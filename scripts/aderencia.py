"""JSON da vaga x perfil-mestre -> análise de aderência.

Uso:
    python scripts/aderencia.py vaga.json [-o aderencia.md] [--json aderencia.json]

Para cada requisito, procura no perfil a evidência (ID citável '<seção>#<ordem>' e
trecho literal) e marca cobre / parcial / lacuna. Antes de tudo checa os três
bloqueios: localidade e modelo de trabalho, senioridade e obrigatório sem cobertura.
Requisito sem nenhum conceito reconhecido fica como 'revisar': o Claude julga à mão,
com evidência do perfil, e nunca conta como coberto sem ela.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from _comum import Linha, Perfil, carregar_conceitos, carregar_perfil, conceitos_no_texto, contem_termo, dobrar

GRANDE_RECIFE = [
    "recife", "olinda", "jaboatao", "jaboatao dos guararapes", "paulista", "camaragibe", "cabo de santo agostinho",
    "sao lourenco da mata", "abreu e lima", "igarassu", "ipojuca", "moreno", "itamaraca", "itapissuma", "aracoiaba",
]

# Seções do perfil que valem como evidência, em ordem de preferência.
PRIORIDADE = ["4", "11b", "11", "5", "8", "9", "10", "6", "7", "2", "3"]
VALOR = {"cobre": 1.0, "parcial": 0.5, "lacuna": 0.0}
PESO = {"obrigatorio": 2, "desejavel": 1}


def _ordem_secao(linha: Linha) -> int:
    raiz = linha.secao if linha.secao in PRIORIDADE else linha.secao.split(".")[0]
    return PRIORIDADE.index(raiz) if raiz in PRIORIDADE else len(PRIORIDADE)


def evidencia(perfil: Perfil, termos: list[str]) -> tuple[Linha, str] | None:
    candidatas = []
    for termo in termos:
        for l in perfil.linhas:
            if _ordem_secao(l) < len(PRIORIDADE) and contem_termo(l.dobrado, termo):
                candidatas.append((_ordem_secao(l), l.numero, l, termo))
    if not candidatas:
        return None
    _, _, linha, termo = min(candidatas, key=lambda c: (c[0], c[1]))
    return linha, termo


def avaliar_conceito(perfil: Perfil, conceito: dict) -> dict:
    achado = evidencia(perfil, conceito["cobre"])
    status = "cobre"
    if not achado:
        achado = evidencia(perfil, conceito["parcial"])
        status = "parcial"
    if not achado:
        return {"id": conceito["id"], "rotulo": conceito["rotulo"], "status": "lacuna", "evidencia": None, "trecho": None, "nota": conceito.get("nota")}
    linha, termo = achado
    trecho = linha.texto if len(linha.texto) <= 160 else _janela(linha.texto, termo)
    return {
        "id": conceito["id"], "rotulo": conceito["rotulo"], "status": status,
        "evidencia": linha.id, "trecho": trecho, "nota": conceito.get("nota"),
    }


def _janela(texto: str, termo: str, raio: int = 75) -> str:
    pos = dobrar(texto).find(dobrar(termo.lstrip("=")))
    pos = max(pos, 0)
    ini, fim = max(0, pos - raio), min(len(texto), pos + len(termo) + raio)
    return ("…" if ini else "") + texto[ini:fim].strip() + ("…" if fim < len(texto) else "")


ESPECIFICAS = {"ferramenta", "linguagem", "frontend", "backend", "infra", "dados", "formacao"}


def status_requisito(texto: str, avaliados: list[dict], categorias: dict[str, str]) -> str:
    if not avaliados:
        return "revisar"
    aceita_similar = re.search(r"similar|equivalente|afins|related|or other|ou outra", texto, re.I)
    alternativa = re.search(r"\bou\b|\bor\b|/|similar|equivalente|afins|related", texto, re.I)
    especificos = [a for a in avaliados if categorias[a["id"]] in ESPECIFICAS]
    if especificos and alternativa and not aceita_similar:
        # "Automação com Selenium ou Cypress": vale a ferramenta pedida, não o conceito genérico.
        # Numa lista ("Front-end, APIs, Mobile e Mainframe") todos os conceitos contam.
        avaliados = especificos
    estados = [a["status"] for a in avaliados]
    if alternativa:
        return max(estados, key=lambda s: VALOR[s])
    if all(s == "cobre" for s in estados):
        return "cobre"
    if all(s == "lacuna" for s in estados):
        return "lacuna"
    return "parcial"


def checar_bloqueios(vaga: dict, requisitos: list[dict]) -> tuple[list[str], list[str]]:
    bloqueios, ressalvas = [], []
    modelo = vaga.get("modelo_trabalho")
    local = dobrar(vaga.get("local") or "")
    na_regiao = any(re.search(rf"\b{c}\b", local) for c in GRANDE_RECIFE)
    if modelo in ("presencial", "hibrido", "ambiguo", "nao-informado"):
        if na_regiao:
            pass
        elif not local:
            ressalvas.append("Localidade não informada para vaga não remota: confirmar antes de aplicar.")
        elif vaga.get("relocacao_oferecida"):
            ressalvas.append(f"{modelo.capitalize()} em {vaga['local']}, com menção a relocação: só aplicar se cobrir deslocamento e moradia.")
        else:
            bloqueios.append(f"Localidade: {modelo} em {vaga['local']}, fora da Grande Recife e sem relocação custeada.")

    senioridade = vaga.get("senioridade")
    if senioridade == "senior":
        bloqueios.append("Senioridade: vaga sênior/lead. Alvo é júnior; o escopo das entregas não sustenta o título.")
    elif senioridade == "pleno":
        ressalvas.append("Senioridade: vaga pleno. Pode aplicar se o escopo couber, posicionando como 'QA com entregas de engenharia' (10 meses de QA formal).")
    elif senioridade == "nao-informada":
        ressalvas.append("Senioridade não informada: tratar como possível pleno; não brigar por título.")
    elif senioridade == "estagio":
        ressalvas.append("Vaga de estágio/trainee: confirmar se aceita quem já tem vínculo CLT.")

    obrig = [r for r in requisitos if r["tipo"] == "obrigatorio" and r["status"] != "revisar"]
    sem = [r for r in obrig if r["status"] == "lacuna"]
    if sem:
        lista = "; ".join(r["texto"] for r in sem)
        if len(sem) >= 2 or (obrig and len(sem) / len(obrig) > 0.25):
            bloqueios.append(f"Obrigatórios sem cobertura ({len(sem)} de {len(obrig)}): {lista}")
        else:
            ressalvas.append(f"Obrigatório sem cobertura: {lista}. Vai para lacunas, nunca para o currículo.")
    return bloqueios, ressalvas


POSICIONAMENTOS = {
    "3.2": {"playwright", "cypress", "selenium", "automacao", "e2e", "ci-cd", "github-actions", "page-objects", "typescript", "observabilidade", "maestro", "appium"},
    "3.3": {"react", "nextjs", "tailwind", "css", "ui-libs", "design-system", "figma", "node", "express", "orm", "state", "forms", "vite", "react-native", "responsivo", "acessibilidade"},
    "3.4": {"ia", "mcp"},
    "3.1": {"testes-manuais", "casos-de-teste", "plano-de-testes", "bdd", "gherkin", "bug-tracking", "regressao", "smoke", "homologacao", "requisitos", "testes-api", "sql", "jira", "documentacao", "incidentes", "risco"},
}
NOMES_POS = {
    "3.1": "QA Engineer / Analista de Testes (funcional + estratégia)",
    "3.2": "QA Automation / SDET",
    "3.3": "Engenheiro de Software / Fullstack com foco em qualidade e tooling",
    "3.4": "Engenheiro de IA aplicada / Agentes",
    "3.5": "Perfil júnior generalista / estágio / trainee",
}


def sugerir_posicionamento(vaga: dict) -> str:
    if vaga.get("senioridade") == "estagio":
        return "3.5"
    pontos = {k: 0 for k in POSICIONAMENTOS}
    for kw in vaga.get("palavras_chave", []):
        for pos, ids in POSICIONAMENTOS.items():
            if kw["conceito"] in ids:
                pontos[pos] += kw.get("peso", 1)
    return max(pontos, key=lambda k: (pontos[k], k == "3.1"))


def analisar(vaga: dict, perfil: Perfil | None = None) -> dict:
    perfil = perfil or carregar_perfil()
    conceitos = carregar_conceitos()
    por_id = {c["id"]: c for c in conceitos}
    cache: dict[str, dict] = {}

    def avaliar(cid: str) -> dict:
        if cid not in cache:
            cache[cid] = avaliar_conceito(perfil, por_id[cid])
        return cache[cid]

    requisitos = []
    for tipo, chave in (("obrigatorio", "obrigatorios"), ("desejavel", "desejaveis")):
        for texto in vaga.get(chave, []):
            achados = conceitos_no_texto(texto, conceitos)
            avaliados = [avaliar(c["id"]) | {"forma_na_vaga": forma} for c, forma in achados]
            requisitos.append({
                "texto": texto, "tipo": tipo,
                "status": status_requisito(texto, avaliados, {c["id"]: c["categoria"] for c in conceitos}),
                "conceitos": avaliados,
            })

    contaveis = [r for r in requisitos if r["status"] != "revisar"]
    total = sum(PESO[r["tipo"]] for r in contaveis)
    score = round(100 * sum(PESO[r["tipo"]] * VALOR[r["status"]] for r in contaveis) / total) if total else 0

    bloqueios, ressalvas = checar_bloqueios(vaga, requisitos)
    if bloqueios:
        recomendacao = "não aplicar"
    elif score >= 70 and not any(r.startswith(("Obrigatório", "Senioridade: vaga pleno", "Presencial", "Hibrido", "Híbrido")) for r in ressalvas):
        recomendacao = "aplicar"
    elif score >= 50:
        recomendacao = "aplicar com ressalvas"
    else:
        recomendacao = "não aplicar"

    palavras = []
    for kw in vaga.get("palavras_chave", []):
        c = por_id.get(kw["conceito"])
        if not c:
            continue
        a = avaliar(c["id"])
        usar = a["status"] != "lacuna" and not c.get("no_cv", False)
        palavras.append({
            "conceito": c["id"], "forma_na_vaga": kw["forma_na_vaga"], "forma_cv": c.get("forma_cv"),
            "status": a["status"], "usar_no_cv": usar, "evidencia": a["evidencia"], "peso": kw.get("peso", 1),
            "nota": a["nota"],
        })

    pos = sugerir_posicionamento(vaga)
    return {
        "vaga": {k: vaga.get(k) for k in ("titulo", "empresa", "local", "modelo_trabalho", "senioridade", "idioma")},
        "bloqueios": bloqueios,
        "ressalvas": ressalvas,
        "score": score,
        "recomendacao": recomendacao,
        "posicionamento": {"secao": pos, "nome": NOMES_POS[pos]},
        "requisitos": requisitos,
        "palavras_chave": palavras,
        "revisar": [r["texto"] for r in requisitos if r["status"] == "revisar"],
    }


ICONE = {"cobre": "cobre", "parcial": "parcial", "lacuna": "**lacuna**", "revisar": "revisar"}


def _celula(texto: str | None) -> str:
    return (texto or "").replace("|", "\\|").replace("\n", " ")


def para_markdown(res: dict) -> str:
    v = res["vaga"]
    linhas = [
        f"# Aderência: {v['titulo']} · {v.get('empresa') or 'empresa não identificada'}",
        "",
        f"Local: {v.get('local') or 'não informado'} · Modelo: {v.get('modelo_trabalho')} · Senioridade: {v.get('senioridade')} · Idioma: {v.get('idioma')}",
        "",
        "## 1. Bloqueios",
        "",
    ]
    linhas += [f"- BLOQUEIO: {b}" for b in res["bloqueios"]] or ["- Nenhum bloqueio."]
    linhas += [f"- Ressalva: {r}" for r in res["ressalvas"]]
    linhas += ["", "## 2. Requisitos × perfil", "", "| Requisito | Tipo | Status | Evidência no perfil |", "| --- | --- | --- | --- |"]
    for r in res["requisitos"]:
        ev = "; ".join(
            f"{c['rotulo']}: {c['status']}" + (f" ({c['evidencia']}: \"{c['trecho']}\")" if c["evidencia"] else "")
            for c in r["conceitos"]
        ) or "nenhum conceito reconhecido: julgar à mão"
        linhas.append(f"| {_celula(r['texto'])} | {r['tipo']} | {ICONE[r['status']]} | {_celula(ev)} |")
    usar = [p for p in res["palavras_chave"] if p["usar_no_cv"]]
    fora = [p for p in res["palavras_chave"] if not p["usar_no_cv"]]
    linhas += ["", "## 3. Palavras-chave", ""]
    linhas.append("Para o currículo (cobertura real): " + (", ".join(
        f"{p['forma_cv'] or p['forma_na_vaga']}" + (f" [{p['status']}]" if p["status"] != "cobre" else "") for p in usar
    ) or "nenhuma"))
    linhas.append("")
    linhas.append("Fora do currículo (lacuna ou termo proibido): " + (", ".join(
        f"{p['forma_na_vaga']} ({p['status']})" for p in fora
    ) or "nenhuma"))
    notas = [p for p in res["palavras_chave"] if p["nota"] and p["status"] != "cobre"]
    if notas:
        linhas += [""] + [f"- {p['forma_na_vaga']}: {p['nota']}" for p in notas]
    linhas += [
        "", "## 4. Recomendação", "",
        f"**{res['recomendacao'].upper()}** · score {res['score']}/100 (obrigatório peso 2, desejável peso 1; cobre 1, parcial 0,5).",
        "",
        f"Posicionamento sugerido: {res['posicionamento']['secao']} {res['posicionamento']['nome']}.",
    ]
    if res["revisar"]:
        linhas += ["", "Requisitos para julgar à mão (sem conceito no léxico): " + "; ".join(res["revisar"])]
    return "\n".join(linhas) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("vaga", help="JSON gerado por extrair_vaga.py (revisado)")
    ap.add_argument("-o", "--saida", help="relatório Markdown (padrão: stdout)")
    ap.add_argument("--json", help="grava também o resultado em JSON (usado por verificar_fatos.py)")
    args = ap.parse_args()

    vaga = json.load(open(args.vaga, encoding="utf-8"))
    res = analisar(vaga)
    md = para_markdown(res)
    if args.saida:
        open(args.saida, "w", encoding="utf-8").write(md)
    else:
        print(md)
    if args.json:
        open(args.json, "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
