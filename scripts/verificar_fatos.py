"""Verifica se cada linha do currículo gerado tem origem no perfil-mestre.

Uso:
    python scripts/verificar_fatos.py curriculo.md [--aderencia aderencia.json] [--json relatorio.json]

Sai com código 1 se houver qualquer FALHA. Camadas, todas determinísticas:

1. Origem: cada bullet cita '<!-- fonte: 4.1#6, 11b#8 -->'. O ID tem de existir e o
   bullet tem de se parecer com as linhas citadas (radicais PT/EN + conceitos do léxico).
   Sem citação, o script procura a melhor linha do perfil e exige semelhança maior.
2. Números: todo número do bullet precisa estar nas linhas citadas (1.990 = 1,990).
3. Nomes próprios e siglas: palavras com maiúscula no meio da frase, siglas, termos
   com dígitos ou CamelCase precisam existir no perfil ou no léxico com cobertura.
4. Termos proibidos (regras fixas do perfil) e conceitos sem cobertura ou marcados
   'no_cv' no léxico (Jira, Cypress, Java, ISTQB, Docker...).
5. CI/CD só com qualificador (planejado, proposto, roadmap).
6. Com --aderencia: idioma igual ao da vaga e 8 a 15 palavras-chave da vaga presentes,
   todas com cobertura real.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

from _comum import (
    Perfil, carregar_conceitos, carregar_perfil, conceitos_no_texto, contem_termo,
    dobrar, numeros, radicais, tokens,
)
from _curriculo import Unidade, ler
from aderencia import avaliar_conceito

PONTE = Path(__file__).resolve().parent.parent / "references" / "dicionario-en-pt.txt"

# ---------------------------------------------------------------- regras fixas

PROIBIDOS = [
    (r"\bapostas?\b|\bbetting\b|\bbets?\b|casas? de apostas?|bookmaker", "Use 'iGaming', nunca 'apostas'/'betting'."),
    (r"certifica[cç][aã]o|certifica[cç][oõ]es|\bcertificad[oa]s?\b|\bcertification|\bcertified\b|\bcertificate", "Não há certificação formal: participação em evento não é certificação."),
    (r"(lider|liderei|liderou|lideran[cç]a|\bled\b|\blead\b|leading|gerenci|managed|coordenei).{0,30}(equipe|time|team|squad).{0,20}(\bqa\b|qualidade|testes|quality|testing)",
     "Não dizer que liderou equipe de QA: é QA solo ('responsável pela qualidade de')."),
    (r"\bINC-\d+", "Nome de incidente interno fora do currículo."),
    (r"\bfatias?\s+[ab]\b|\bslices?\s+[ab]\b", "Jargão interno (fatia a/b)."),
    (r"\b(s[eê]nior|senior)\b", "Não inflar senioridade."),
]
# Escalada de alegação: verbo forte no bullet exige o mesmo papel na linha citada.
ESCALADA = [
    (r"mentor", r"mentor", "mentoria"),
    # 'led to' (levou a) e 'Tech Lead' (cargo de outra pessoa) não são alegação de liderança
    (r"\blider(ei|ou|ando|ar)\b|\blideranca\b|\bled\b(?! to)|\bleading\b|\bleadership\b|(?<!tech )\blead (a|the|an)\b",
     r"lider|coorden|lalider", "liderança"),
    (r"gerenci|\bmanaged\b|\bmanager\b|\bchefi", r"gerenc|gest[aã]o", "gestão de pessoas/projetos"),
    (r"coorden|coordinat|supervis", r"coorden|supervis", "coordenação"),
    (r"\bfund(ei|ou|ador|adora)|\bfounded|founder", r"fundador", "fundação"),
    (r"sozinh|\bsolo\b|\bsole\b|\bsingle-handed|\bunico qa|\bunic[oa] respons", r"sozinho|\bsolo\b|unico qa|\bunico\b", "atuação solo"),
    (r"arquitet|architect", r"arquitet", "arquitetura"),
    (r"1[ºo°] lugar|first place|1st place|vencedor|winner|\bvenci\b", r"1[ºo°] lugar", "1º lugar"),
    (r"\b100\s*%|zero downtime|sem falhas|100% uptime", r"\b100\s*%", "100%"),
]
UFRPE_STATUS = r"andamento|previs[aã]o|cursando|trancad|matr[ií]cula|in progress|expected|ongoing|current|\d{4}\s*[–-]"
DOMINIOS_OK = ["linkedin.com", "github.com", "gmail.com"]
QUALIFICADOR_CI = r"planejad|propost|roadmap|planned|proposed|previst"
JARGAO_AVISO = [(r"\bOnda [12]\b|\bWave [12]\b", "Jargão interno 'Onda 1/2': traduza para o leitor (ex.: 'primeira etapa')."),
                (r"\bcasas?\b(?! de)", "Jargão interno 'casa': prefira 'marca' ou 'operadora'.")]

NUM_EXTENSO = {
    "dois": "2", "duas": "2", "três": "3", "tres": "3", "quatro": "4", "cinco": "5", "seis": "6", "sete": "7",
    "oito": "8", "nove": "9", "dez": "10", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "dozen": "12",
}

# Palavras comuns que podem aparecer com maiúscula em cabeçalhos e listas.
LIVRES = set(dobrar(p) for p in """
jan fev mar abr mai jun jul ago set out nov dez feb apr may aug sep sept oct dec
janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro
january february march april june july august september october november december
atual present presente remoto remote hibrido híbrido hybrid presencial on-site onsite
pe brasil brazil english portuguese spanish french native fluent advanced basic intermediate
nativo avançado básico intermediário fluente
analyst engineer developer tester intern student researcher volunteer founder co-founder cofounder
assistant member scholar fellow freelance freelancer contractor web full-time part-time
experience education skills projects awards languages summary profile leadership
""".split())

LIMIAR = {"pt": 0.40, "en": 0.25}
NAO_TECNICAS = {"soft", "formacao", "idioma"}
LIMIAR_SEM_CITACAO = {"pt": 0.55, "en": 0.40}


def numeros_unidade(texto: str) -> set[str]:
    nums = numeros(texto)
    for palavra in re.findall(r"[a-zà-ú]+", texto.lower()):
        if palavra in NUM_EXTENSO:
            nums.add(NUM_EXTENSO[palavra])
    return nums


@lru_cache(maxsize=4096)
def _conceitos_de(texto: str) -> frozenset[str]:
    conceitos = carregar_conceitos()
    achados = {c["id"] for c, _ in conceitos_no_texto(texto, conceitos)}
    dob = dobrar(texto)
    for c in conceitos:
        if any(contem_termo(dob, t) for t in c["cobre"] + c["parcial"]):
            achados.add(c["id"])
    return frozenset(achados)


def conceitos_de(texto: str, _conceitos: list[dict] | None = None) -> set[str]:
    return set(_conceitos_de(texto))


def carregar_ponte() -> dict[str, set[str]]:
    ponte: dict[str, set[str]] = {}
    for linha in PONTE.read_text(encoding="utf-8").splitlines():
        if ":" in linha and not linha.startswith("#"):
            en, pt = linha.split(":", 1)
            ponte[en.strip()] = radicais(pt)
    return ponte


_PONTE = carregar_ponte()


def radicais_ponte(texto: str) -> set[str]:
    """Radicais do texto mais os radicais PT das palavras EN conhecidas."""
    saida = radicais(texto)
    for t in tokens(texto):
        saida |= _PONTE.get(t, set())
    return saida


def semelhanca(texto: str, fonte: str, conceitos: list[dict]) -> float:
    """Fração do bullet sustentada pela fonte: radicais (com ponte EN->PT), conceitos e números."""
    r_txt, r_fonte = radicais(texto), radicais_ponte(fonte) | radicais(fonte)
    traduzidos = {t: radicais(t) | _PONTE.get(t, set()) for t in tokens(texto) if len(t) >= 3 and not any(ch.isdigit() for ch in t)}
    c_txt, c_fonte = conceitos_de(texto, conceitos), conceitos_de(fonte, conceitos)
    n_txt, n_fonte = numeros_unidade(texto), numeros_unidade(fonte)
    total = len(traduzidos) + len(c_txt) + len(n_txt)
    if not total:
        return 1.0
    casados = sum(1 for rads in traduzidos.values() if rads & r_fonte)
    return (casados + len(c_txt & c_fonte) + len(n_txt & n_fonte)) / total


class Verificador:
    def __init__(self, perfil: Perfil, idioma: str):
        self.perfil = perfil
        self.idioma = idioma if idioma in LIMIAR else "pt"
        self.conceitos = carregar_conceitos()
        self.status = {c["id"]: avaliar_conceito(perfil, c)["status"] for c in self.conceitos}
        # títulos de seção também valem como vocabulário ("Analista de QA", "Função Sistemas")
        titulos = sorted({dobrar(l.titulo) for l in perfil.linhas})
        self.texto_perfil = perfil.texto_dobrado + "\n" + "\n".join(titulos)
        self.nums_perfil = set().union(*(numeros_unidade(l.texto) for l in perfil.linhas))
        vocab = set(tokens(self.texto_perfil))
        for c in self.conceitos:
            if self.status[c["id"]] != "lacuna" and not c.get("no_cv"):
                for v in c["variantes"] + [c.get("forma_cv") or "", c["rotulo"]]:
                    vocab |= set(tokens(v.lstrip("=")))
        self.vocab = vocab | LIVRES
        self.radicais_perfil = radicais(self.texto_perfil)
        self.candidatas = [l for l in perfil.linhas if l.secao.split(".")[0] not in ("0", "12", "13", "14")]

    # ------------------------------------------------------------ camadas

    def guarda_nomes(self, texto: str, titulo: bool = False) -> list[str]:
        problemas = []
        frases = re.split(r"(?<=[.!?:;])\s+|\s+[|·]\s+", texto)
        for frase in frases:
            palavras = re.findall(r"[\wÀ-ÿ][\wÀ-ÿ+#./'-]*[\wÀ-ÿ+#]|[\wÀ-ÿ]", frase)
            for i, p in enumerate(palavras):
                limpa = p.strip(".'")
                tem_digito = any(ch.isdigit() for ch in limpa)
                sigla = re.fullmatch(r"[A-Z0-9][A-Z0-9+#./-]+", limpa) is not None and len(limpa) >= 2
                camel = re.search(r"[a-z][A-Z]", limpa) is not None
                maiuscula = limpa[:1].isupper() and i > 0 and not titulo
                if not (sigla or camel or maiuscula or (tem_digito and re.search(r"[A-Za-z]", limpa))):
                    continue
                if tem_digito and not re.search(r"[A-Za-z]{2}", limpa):
                    continue  # números puros são da camada de números
                if tem_digito and not re.search(r"[A-Z]", limpa):
                    continue  # '4-phase', '83rd', '27k', 'v2': o número já passa pela camada de números
                t = dobrar(limpa)
                partes = [x for x in re.split(r"[./'-]", t) if x]
                if t in self.vocab or contem_termo(self.texto_perfil, limpa) or all(x in self.vocab for x in partes):
                    continue
                problemas.append(f"termo sem lastro no perfil: '{limpa}'")
        return sorted(set(problemas))

    def regras_globais(self, texto: str, secao: str) -> tuple[list[str], list[str]]:
        falhas, avisos = [], []
        for padrao, motivo in PROIBIDOS:
            if re.search(padrao, texto, re.I):
                falhas.append(motivo)
        if "ufrpe" in dobrar(texto) and re.search(UFRPE_STATUS, texto, re.I):
            falhas.append("UFRPE: não citar situação da matrícula nem período em andamento.")
        for dom in re.findall(r"\b(?:[\w-]+\.)+(?:com|br|io|app|net|org|dev|bet|cloud)\b(?:/\S*)?", texto, re.I):
            # "ASP.NET" termina em ".net" mas é tecnologia do perfil, não host
            if not any(ok in dom.lower() for ok in DOMINIOS_OK) and not contem_termo(self.texto_perfil, dom):
                falhas.append(f"Host/domínio fora do currículo: {dom}")
        achados = conceitos_no_texto(texto, self.conceitos)
        for c, forma in achados:
            if c.get("no_cv"):
                falhas.append(f"'{forma}' não pode ir para o currículo ({c['rotulo']}: {c.get('nota') or 'sem evidência'}).")
            elif self.status[c["id"]] == "lacuna":
                falhas.append(f"'{forma}' é lacuna no perfil.")
            if c["id"] in ("ci-cd", "github-actions") and not re.search(QUALIFICADOR_CI, texto, re.I):
                falhas.append(f"'{forma}' sem qualificador: CI/CD é planejado, não está rodando.")
        if self.idioma == "pt":
            for padrao, motivo in JARGAO_AVISO:
                if re.search(padrao, texto):
                    avisos.append(motivo)
        else:
            if re.search(JARGAO_AVISO[0][0], texto):
                avisos.append(JARGAO_AVISO[0][1])
        return falhas, avisos

    def origem(self, u: Unidade) -> dict:
        r = {"linha": u.linha, "tipo": u.tipo, "secao": u.secao, "texto": u.texto, "fontes": u.fontes,
             "falhas": [], "avisos": [], "origem": None, "semelhanca": None}
        falhas, avisos = self.regras_globais(u.texto, u.secao)
        r["falhas"] += falhas
        r["avisos"] += avisos
        nums = numeros_unidade(u.texto)

        if u.tipo == "contato":
            if not (contem_termo(self.texto_perfil, u.texto) or dobrar(u.texto) in self.texto_perfil
                    or all(t in self.vocab for t in tokens(u.texto))):
                r["falhas"].append("contato não consta no perfil")
            return r

        if u.tipo in ("entrada", "rotulado", "headline"):
            r["falhas"] += self.guarda_nomes(u.texto, titulo=(u.tipo in ("entrada", "headline")))
            extras = nums - self.nums_perfil
            if extras:
                r["falhas"].append(f"número(s) sem origem: {', '.join(sorted(extras))}")
            if u.tipo in ("rotulado", "headline"):
                r["falhas"] += self.itens_habilidade(u.texto)
            return r

        # item e parágrafo
        r["falhas"] += self.guarda_nomes(u.texto)
        linhas_fonte = []
        for ref in u.fontes:
            l = self.perfil.por_id(ref)
            if l is None:
                r["falhas"].append(f"fonte inexistente no perfil: {ref}")
            else:
                linhas_fonte.append(l)
        if linhas_fonte:
            base = " ".join(l.texto for l in linhas_fonte)
            sem = semelhanca(u.texto, base, self.conceitos)
            r["origem"] = ", ".join(l.id for l in linhas_fonte)
            r["semelhanca"] = round(sem, 2)
            if sem < LIMIAR[self.idioma]:
                r["falhas"].append(f"pouco parecido com a fonte citada ({sem:.2f} < {LIMIAR[self.idioma]})")
            permitidos = set().union(*(numeros_unidade(l.texto) for l in linhas_fonte))
            if u.tipo == "paragrafo":
                permitidos |= set().union(*(numeros_unidade(l.texto) for l in self.perfil.da_secao("11", "11b", "2")))
        elif not u.fontes:
            melhor = max(self.candidatas, key=lambda l: semelhanca(u.texto, l.texto, self.conceitos))
            sem = semelhanca(u.texto, melhor.texto, self.conceitos)
            r["origem"], r["semelhanca"] = melhor.id, round(sem, 2)
            permitidos = numeros_unidade(melhor.texto)
            if u.tipo == "paragrafo":
                permitidos = self.nums_perfil
            if sem < LIMIAR_SEM_CITACAO[self.idioma]:
                r["falhas"].append(
                    f"sem origem: nenhuma linha do perfil sustenta este texto (melhor: {melhor.id}, {sem:.2f}). Cite a fonte ou remova."
                )
            else:
                r["avisos"].append(f"sem citação; origem provável {melhor.id}. Cite com <!-- fonte: {melhor.id} -->.")
        else:
            permitidos = set()
        extras = nums - permitidos
        if extras:
            r["falhas"].append(f"número(s) que não estão na fonte: {', '.join(sorted(extras))}")
        if u.tipo == "item" and (linhas_fonte or r["origem"]):
            base = dobrar(" ".join(l.texto for l in linhas_fonte)) if linhas_fonte else dobrar(self.perfil.por_id(r["origem"]).texto)
            for padrao, exigido, nome in ESCALADA:
                if re.search(padrao, dobrar(u.texto)) and not re.search(exigido, base):
                    r["falhas"].append(f"escalada de alegação ({nome}): a fonte citada não sustenta esse papel.")
        return r

    def itens_habilidade(self, texto: str) -> list[str]:
        falhas = []
        for item in re.split(r",|;|\s+·\s+", re.sub(r"\(.*?\)", "", texto)):
            base = item.strip(" .")
            if not base:
                continue
            if contem_termo(self.texto_perfil, base):
                continue
            achados = conceitos_no_texto(base, self.conceitos)
            if achados and all(self.status[c["id"]] != "lacuna" and not c.get("no_cv") for c, _ in achados):
                continue
            if all(t in self.vocab or _PONTE.get(t, set()) & self.radicais_perfil for t in tokens(base)):
                continue
            falhas.append(f"habilidade sem lastro: '{base}'")
        return falhas


def detectar_idioma(texto: str) -> str:
    from extrair_vaga import detectar_idioma as det
    return det(texto)


def verificar(md: str, aderencia: dict | None = None, perfil: Perfil | None = None) -> dict:
    perfil = perfil or carregar_perfil()
    dados, unidades = ler(md)
    idioma = dados.get("idioma", "pt")
    v = Verificador(perfil, idioma)
    # cargo e empresa dos metadados ("vaga: <cargo> · <empresa>") podem ser nomeados no texto
    # (a carta cita a vaga e a empresa); não são fatos sobre o Samuel.
    v.vocab |= set(tokens(dados.get("vaga", "")))
    resultados = [v.origem(u) for u in unidades]
    texto_total = "\n".join(u.texto for u in unidades)
    gerais: list[str] = []
    avisos_gerais: list[str] = []

    # UFRPE: título e instituição ficam em linhas separadas; checa o bloco da entrada inteiro.
    blocos = re.split(r"\n(?=###? )", md)
    for bloco in blocos:
        cabeca = " ".join(bloco.strip().splitlines()[:2])
        if "ufrpe" in dobrar(cabeca) and re.search(UFRPE_STATUS, cabeca, re.I):
            gerais.append("UFRPE: não citar situação da matrícula nem período em andamento (use só '2024').")

    idioma_texto = detectar_idioma(texto_total)
    if idioma_texto != idioma:
        gerais.append(f"idioma declarado '{idioma}' mas o texto parece '{idioma_texto}'")
    palavras = []
    if aderencia:
        alvo = aderencia["vaga"].get("idioma")
        if alvo and alvo != idioma:
            gerais.append(f"idioma do currículo ({idioma}) diferente do idioma da vaga ({alvo})")
        conceitos = {c["id"]: c for c in v.conceitos}
        presentes = {c["id"] for c, _ in conceitos_no_texto(texto_total, v.conceitos)}
        for kw in aderencia["palavras_chave"]:
            c = conceitos.get(kw["conceito"])
            formas = [kw["forma_na_vaga"], kw.get("forma_cv") or ""] + (c["variantes"] if c else [])
            achou = kw["conceito"] in presentes or any(f and contem_termo(dobrar(texto_total), f) for f in formas)
            if achou:
                palavras.append({"palavra": kw["forma_na_vaga"], "status": kw["status"], "usar_no_cv": kw["usar_no_cv"],
                                 "tecnica": (c or {}).get("categoria") not in NAO_TECNICAS})
        # O limite de 8 a 15 vale para termos técnicos; soft skills, formação e idioma não contam.
        reais = [p for p in palavras if p["usar_no_cv"] and p["tecnica"]]
        indevidas = [p for p in palavras if not p["usar_no_cv"]]
        if len(reais) < 8:
            gerais.append(f"só {len(reais)} palavras-chave da vaga com cobertura real no currículo (mínimo 8)")
        elif len(reais) > 15:
            avisos_gerais.append(f"{len(reais)} palavras-chave da vaga: acima de 15, confira se não virou keyword stuffing")
        if indevidas:
            gerais.append("palavras-chave sem cobertura presentes: " + ", ".join(p["palavra"] for p in indevidas))

    falhas = sum(len(r["falhas"]) for r in resultados) + len(gerais)
    return {
        "aprovado": falhas == 0,
        "falhas": falhas,
        "idioma": idioma,
        "unidades": resultados,
        "gerais": gerais,
        "avisos_gerais": avisos_gerais,
        "palavras_chave": palavras,
    }


def imprimir(rel: dict) -> None:
    for r in rel["unidades"]:
        marca = "FALHA" if r["falhas"] else "ok   "
        origem = f"[{r['origem']} · {r['semelhanca']}]" if r["origem"] else ""
        print(f"{marca} L{r['linha']:<3} {r['tipo']:<9} {origem} {r['texto'][:90]}")
        for f in r["falhas"]:
            print(f"        x {f}")
        for a in r["avisos"]:
            print(f"        ! {a}")
    for g in rel["gerais"]:
        print(f"FALHA geral: {g}")
    for a in rel["avisos_gerais"]:
        print(f"AVISO geral: {a}")
    if rel["palavras_chave"]:
        reais = [p["palavra"] for p in rel["palavras_chave"] if p["usar_no_cv"] and p["tecnica"]]
        print(f"Palavras-chave técnicas da vaga no currículo ({len(reais)}): {', '.join(reais)}")
    print(("APROVADO" if rel["aprovado"] else f"REPROVADO: {rel['falhas']} falha(s)") + f" · idioma {rel['idioma']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("curriculo", help="currículo em Markdown canônico")
    ap.add_argument("--aderencia", help="JSON gerado por aderencia.py --json")
    ap.add_argument("--json", help="grava o relatório em JSON")
    args = ap.parse_args()
    md = Path(args.curriculo).read_text(encoding="utf-8")
    ad = json.load(open(args.aderencia, encoding="utf-8")) if args.aderencia else None
    rel = verificar(md, ad)
    imprimir(rel)
    if args.json:
        Path(args.json).write_text(json.dumps(rel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if rel["aprovado"] else 1


if __name__ == "__main__":
    sys.exit(main())
