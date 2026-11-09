"""Roda os evals da skill e atualiza a tabela de resultados em evals/checks.md.

Uso:
    python evals/rodar_evals.py

Para cada vaga em evals/vagas/: extrai, analisa a aderência e, se existir
evals/resultados/<vaga>/curriculo.md (escrito pela skill), verifica os fatos e
renderiza o PDF. Os currículos não são gerados aqui: são a saída da skill
(o modelo), e este script só julga, de forma determinística.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from _comum import dobrar  # noqa: E402
from aderencia import analisar, para_markdown  # noqa: E402
from extrair_vaga import extrair  # noqa: E402
from render import renderizar  # noqa: E402
from verificar_fatos import PROIBIDOS, verificar  # noqa: E402

VAGAS = RAIZ / "evals" / "vagas"
RESULTADOS = RAIZ / "evals" / "resultados"
CHECKS = RAIZ / "evals" / "checks.md"
ESPERADO = {  # recomendação esperada por vaga
    "a-qa-analyst-jr-recife": {"aplicar", "aplicar com ressalvas"},
    "b-qa-automation-en-remote": {"aplicar", "aplicar com ressalvas"},
    "c-frontend-jr-remoto": {"aplicar", "aplicar com ressalvas"},
    "d-qa-presencial-sao-paulo": {"não aplicar"},
}
TERMOS_PROIBIDOS = [p for p, _ in PROIBIDOS] + [r"ufrpe[^\n]{0,40}(andamento|previs|cursando)"]


def ok(valor: bool) -> str:
    return "✅" if valor else "❌"


def avaliar(nome: str) -> dict:
    pasta = RESULTADOS / nome
    pasta.mkdir(parents=True, exist_ok=True)
    texto = (VAGAS / f"{nome}.txt").read_text(encoding="utf-8")
    vaga = extrair(texto)
    (pasta / "vaga.json").write_text(json.dumps(vaga, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ad = analisar(vaga)
    (pasta / "aderencia.md").write_text(para_markdown(ad), encoding="utf-8")
    (pasta / "aderencia.json").write_text(json.dumps(ad, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    linha = {
        "vaga": nome, "idioma_vaga": vaga["idioma"], "recomendacao": ad["recomendacao"], "score": ad["score"],
        "recomendacao_ok": ad["recomendacao"] in ESPERADO.get(nome, {ad["recomendacao"]}),
        "analise": all(s in para_markdown(ad) for s in ("Bloqueios", "Requisitos × perfil", "Recomendação")),
    }
    cv = pasta / "curriculo.md"
    if not cv.exists():
        linha["curriculo"] = False
        return linha

    md = cv.read_text(encoding="utf-8")
    rel = verificar(md, ad)
    (pasta / "verificacao.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    texto_cv = re.sub(r"<!--.*?-->", "", md)
    proibidos = sum(len(re.findall(p, texto_cv, re.I)) for p in TERMOS_PROIBIDOS)
    unidades = [u for u in rel["unidades"] if u["tipo"] in ("item", "paragrafo")]
    com_origem = [u for u in unidades if u["origem"] and not u["falhas"]]
    tecnicas = [p for p in rel["palavras_chave"] if p["usar_no_cv"] and p["tecnica"]]
    indevidas = [p for p in rel["palavras_chave"] if not p["usar_no_cv"]]
    pdf, rend = renderizar(md)
    (pasta / "curriculo.pdf").write_bytes(pdf)
    linha.update(
        curriculo=True,
        proibidos=proibidos,
        bullets=len(unidades),
        bullets_com_origem=len(com_origem),
        palavras=len(tecnicas),
        palavras_indevidas=len(indevidas),
        paginas=rend["paginas"],
        preenchimento=rend["preenchimento"],
        idioma_cv=rel["idioma"],
        verificador=rel["aprovado"],
    )
    return linha


def tabela(linhas: list[dict]) -> str:
    cab = (
        "| Vaga | Análise antes do CV | Recomendação | Termos proibidos | Bullets com origem | "
        "Palavras-chave (8–15, todas cobertas) | Uma página | Idioma | Verificador |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    )
    corpo = []
    for l in linhas:
        rec = f"{ok(l['recomendacao_ok'])} {l['recomendacao']} ({l['score']})"
        if not l.get("curriculo"):
            corpo.append(f"| {l['vaga']} | {ok(l['analise'])} | {rec} | n/a (sem currículo) | n/a | n/a | n/a | n/a | n/a |")
            continue
        pal_ok = 8 <= l["palavras"] <= 15 and l["palavras_indevidas"] == 0
        corpo.append(
            f"| {l['vaga']} | {ok(l['analise'])} | {rec} | {ok(l['proibidos'] == 0)} {l['proibidos']} | "
            f"{ok(l['bullets_com_origem'] == l['bullets'])} {l['bullets_com_origem']}/{l['bullets']} | "
            f"{ok(pal_ok)} {l['palavras']} | {ok(l['paginas'] == 1)} {l['paginas']} ({l['preenchimento']}%) | "
            f"{ok(l['idioma_cv'] == l['idioma_vaga'])} {l['idioma_cv']} | {ok(l['verificador'])} |"
        )
    return cab + "\n".join(corpo) + "\n"


def aprovado(l: dict) -> bool:
    if not l["recomendacao_ok"] or not l["analise"]:
        return False
    if not l.get("curriculo"):
        return l["recomendacao"] == "não aplicar"
    return (
        l["proibidos"] == 0 and l["bullets_com_origem"] == l["bullets"] and 8 <= l["palavras"] <= 15
        and l["palavras_indevidas"] == 0 and l["paginas"] == 1 and l["idioma_cv"] == l["idioma_vaga"] and l["verificador"]
    )


def main() -> int:
    nomes = sorted(p.stem for p in VAGAS.glob("*.txt"))
    linhas = [avaliar(n) for n in nomes]
    resultado = tabela(linhas)
    total = sum(aprovado(l) for l in linhas)
    resultado += f"\n**{total} de {len(linhas)} evals aprovados.**\n"
    print(resultado)
    conteudo = CHECKS.read_text(encoding="utf-8")
    novo = re.sub(r"(<!-- resultados:inicio -->\n).*?(<!-- resultados:fim -->)", lambda m: m.group(1) + resultado + m.group(2), conteudo, flags=re.S)
    CHECKS.write_text(novo, encoding="utf-8")
    (RESULTADOS / "resumo.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if total == len(linhas) else 1


if __name__ == "__main__":
    sys.exit(main())
