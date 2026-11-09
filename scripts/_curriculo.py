"""Leitura do currículo em Markdown canônico (formato em references/modelos/formato-canonico.md).

Devolve uma estrutura usada tanto pelo render.py (desenho) quanto pelo
verificar_fatos.py (cada unidade com texto puro e as fontes citadas).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_FONTE = re.compile(r"<!--\s*fonte\s*:\s*(.*?)-->", re.I)
_COMENTARIO = re.compile(r"<!--.*?-->", re.S)
_INLINE = re.compile(r"\*\*(.+?)\*\*|(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|\[(.+?)\]\((.+?)\)")


@dataclass
class Unidade:
    tipo: str  # contato | paragrafo | entrada | item | rotulado
    secao: str
    texto: str  # texto puro, sem marcação
    fontes: list[str] = field(default_factory=list)
    linha: int = 0
    rotulo: str | None = None  # para itens rotulados (Habilidades)


def corridas(texto: str) -> list[dict]:
    """'**a** b [c](u)' -> [{'t':'a','b':True},{'t':' b'},{'t':'c','u':'u'}]"""
    saida, pos = [], 0
    for m in _INLINE.finditer(texto):
        if m.start() > pos:
            saida.append({"t": texto[pos : m.start()]})
        if m.group(1) is not None:
            saida.append({"t": m.group(1), "b": True})
        elif m.group(2) is not None:
            saida.append({"t": m.group(2), "i": True})
        else:
            saida.append({"t": m.group(3), "u": m.group(4)})
        pos = m.end()
    if pos < len(texto):
        saida.append({"t": texto[pos:]})
    return saida or [{"t": ""}]


def texto_puro(texto: str) -> str:
    return "".join(r["t"] for r in corridas(_COMENTARIO.sub("", texto))).strip()


def _fontes(linha: str) -> tuple[str, list[str]]:
    ids: list[str] = []
    for m in _FONTE.finditer(linha):
        ids += [i.strip() for i in re.split(r"[,;]", m.group(1)) if i.strip()]
    return _COMENTARIO.sub("", linha).rstrip(), ids


def _contato_corridas(item: str) -> list[dict]:
    item = item.strip()
    if _INLINE.search(item):
        return corridas(item)
    if re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", item):
        return [{"t": item, "u": f"mailto:{item}"}]
    if re.match(r"(https?://)?(www\.)?(linkedin|github|gitlab)\.com/", item):
        url = item if item.startswith("http") else f"https://{item}"
        return [{"t": re.sub(r"^https?://(www\.)?", "", item), "u": url}]
    return [{"t": item}]


def ler(md: str) -> tuple[dict, list[Unidade]]:
    """Devolve (dados para o template, unidades para verificação)."""
    dados: dict = {"nome": "", "headline": None, "contato": [], "secoes": [], "idioma": "pt", "titulo_doc": "Currículo"}
    unidades: list[Unidade] = []
    meta = re.search(r"<!--\s*cv-tailoring(.*?)-->", md, re.S)
    if meta:
        idioma = re.search(r"idioma\s*:\s*(\w+)", meta.group(1))
        if idioma:
            dados["idioma"] = idioma.group(1)
        if dados["idioma"] == "en":
            dados["titulo_doc"] = "Resume"
        vaga = re.search(r"vaga\s*:\s*(.+?)\s*$", meta.group(1).strip(), re.S)
        if vaga:
            dados["vaga"] = vaga.group(1).strip()

    secao = None
    lista = None
    entrada_aberta = None
    paragrafo: list[str] = []
    linhas = md.splitlines()

    def fechar_paragrafo():
        nonlocal paragrafo
        if paragrafo and secao is not None:
            juntos = " ".join(p for p, _ in paragrafo)
            fontes = sum((f for _, f in paragrafo), [])
            secao["blocos"].append({"tipo": "paragrafo", "corridas": corridas(juntos)})
            unidades.append(Unidade("paragrafo", secao["titulo"], texto_puro(juntos), fontes, paragrafo_inicio))
        paragrafo = []

    paragrafo_inicio = 0
    for n, bruta in enumerate(linhas, start=1):
        if bruta.strip().startswith("<!--") and bruta.strip().endswith("-->") and not _FONTE.search(bruta):
            continue
        linha, fontes = _fontes(bruta)
        s = linha.strip()
        if not s:
            fechar_paragrafo()
            lista = None
            continue
        if s.startswith("# "):
            dados["nome"] = s[2:].strip()
            continue
        if s.startswith("## "):
            fechar_paragrafo()
            secao = {"titulo": s[3:].strip(), "blocos": []}
            dados["secoes"].append(secao)
            lista = entrada_aberta = None
            continue
        if secao is None and s.startswith("> "):
            # headline: cargo + stack, a linha que o recrutador lê primeiro
            dados["headline"] = corridas(s[2:].strip())
            unidades.append(Unidade("headline", "Cabeçalho", texto_puro(s[2:]), fontes, n))
            continue
        if secao is None:
            # linha(s) de contato logo abaixo do nome
            for item in s.split(" | "):
                dados["contato"].append(_contato_corridas(item))
                unidades.append(Unidade("contato", "Cabeçalho", texto_puro(item), fontes, n))
            continue
        if s.startswith("### "):
            fechar_paragrafo()
            lista = None
            titulo, _, data = s[4:].rpartition(" | ") if " | " in s else (s[4:], "", "")
            entrada_aberta = {"tipo": "entrada", "titulo": corridas(titulo.strip()), "data": corridas(data.strip()), "org": None, "local": [{"t": ""}]}
            secao["blocos"].append(entrada_aberta)
            unidades.append(Unidade("entrada", secao["titulo"], texto_puro(s[4:]), fontes, n))
            continue
        if s.startswith("- "):
            fechar_paragrafo()
            entrada_aberta = None
            corpo = s[2:].strip()
            rot = re.match(r"^\*\*(.+?)\*\*\s*:\s*(.*)$", corpo)
            tipo = "rotulado" if rot else "lista"
            if lista is None or lista["tipo"] != tipo:
                lista = {"tipo": tipo, "itens": []}
                secao["blocos"].append(lista)
            if rot:
                lista["itens"].append({"rotulo": rot.group(1), "texto": corridas(rot.group(2))})
                unidades.append(Unidade("rotulado", secao["titulo"], texto_puro(rot.group(2)), fontes, n, rotulo=rot.group(1)))
            else:
                lista["itens"].append(corridas(corpo))
                unidades.append(Unidade("item", secao["titulo"], texto_puro(corpo), fontes, n))
            continue
        if entrada_aberta is not None and entrada_aberta["org"] is None:
            org, _, local = s.rpartition(" | ") if " | " in s else (s, "", "")
            entrada_aberta["org"] = corridas(org.strip())
            entrada_aberta["local"] = corridas(local.strip())
            unidades.append(Unidade("entrada", secao["titulo"], texto_puro(s), fontes, n))
            continue
        if not paragrafo:
            paragrafo_inicio = n
        paragrafo.append((s, fontes))
    fechar_paragrafo()
    return dados, unidades
