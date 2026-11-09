"""Funções compartilhadas pelos scripts da skill cv-tailoring.

Tudo aqui é determinístico e só usa a biblioteca padrão: normalização de texto,
leitura do perfil-mestre em linhas rastreáveis e do léxico de conceitos.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PERFIL = RAIZ / "references" / "perfil-mestre.md"
CONCEITOS = RAIZ / "references" / "conceitos.json"

# Saída UTF-8 também no console do Windows.
for _fluxo in (sys.stdout, sys.stderr):
    if hasattr(_fluxo, "reconfigure"):
        _fluxo.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------- texto

def sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )


def dobrar(texto: str) -> str:
    """Minúsculas e sem acento: base de toda comparação."""
    return sem_acento(texto).lower()


STOPWORDS = set(
    """
    a o as os um uma uns umas de da do das dos em na no nas nos por para pra com sem
    e ou que se ao aos à às como mais menos muito pelo pela pelos pelas entre sobre
    sob até após antes depois desde cada seu sua seus suas meu minha este esta isso
    esse essa ele ela eles elas ja nao sim tambem foi ser sao era ter tem
    the an and or of to in on for with without by at from as into over per via
    is are was were be been being this that these those its their our my your
    than then also more most all any each both such using used use
    """.split()
)

_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#./-]*[a-z0-9+#]|[a-z0-9]")


def tokens(texto: str) -> list[str]:
    return [t for t in _TOKEN.findall(dobrar(texto)) if t not in STOPWORDS]


def radicais(texto: str, tamanho: int = 5) -> set[str]:
    """Radicais por prefixo: aproxima PT e EN (automação/automation -> autom)."""
    saida = set()
    for t in tokens(texto):
        if any(ch.isdigit() for ch in t):
            continue
        if len(t) < 3:
            continue
        saida.add(t[:tamanho])
    return saida


_NUMERO = re.compile(r"(?<![\w.,])(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)(?![\w])")


def numeros(texto: str) -> set[str]:
    """Números normalizados: 1.990 e 1,990 viram 1990; 5,1 e 5.1 viram 5.1."""
    saida = set()
    limpo = re.sub(r"<!--.*?-->", " ", texto)
    limpo = re.sub(r"\bL\d+\b", " ", limpo)  # citações de linha
    limpo = re.sub(r"(\d+)(º|ª|st|nd|rd|th)\b", r"\1", limpo)  # ordinais: 1º, 83rd
    # "27 mil", "27k" e "27 thousand" valem 27000, como "27,000"
    limpo = re.sub(
        r"\b(\d{1,3})\s*(?:mil|k|thousand)\b", lambda m: str(int(m.group(1)) * 1000), limpo, flags=re.I
    )
    for bruto in _NUMERO.findall(limpo):
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", bruto):
            valor = re.sub(r"[.,]", "", bruto)
        else:
            valor = bruto.replace(",", ".")
        saida.add(valor.lstrip("0") or "0")
    return saida


def contem_termo(texto_dobrado: str, termo: str) -> bool:
    """Busca de termo com fronteira de palavra.

    Termo prefixado com '=' é sensível a maiúsculas (ex.: '=AI', para não casar com 'aí').
    """
    if termo.startswith("="):
        alvo = re.escape(termo[1:])
        return re.search(rf"(?<![\w]){alvo}(?![\w])", texto_dobrado) is not None
    alvo = re.escape(dobrar(termo))
    return re.search(rf"(?<![\w]){alvo}(?![\w])", texto_dobrado) is not None


def achar_termo(texto_original: str, termo: str) -> str | None:
    """Devolve a forma exata como o termo aparece no texto original (ou None)."""
    if termo.startswith("="):
        m = re.search(rf"(?<![\w]){re.escape(termo[1:])}(?![\w])", texto_original)
        return m.group(0) if m else None
    dob = dobrar(texto_original)
    m = re.search(rf"(?<![\w]){re.escape(dobrar(termo))}(?![\w])", dob)
    if not m:
        return None
    # NFKD pode mudar o comprimento; mapeia caractere a caractere quando possível.
    if len(dob) == len(texto_original):
        return texto_original[m.start() : m.end()]
    return termo


# ---------------------------------------------------------------- perfil

@dataclass
class Linha:
    numero: int
    texto: str
    secao: str  # ex.: "4.1", "11b", "8"
    titulo: str  # título do cabeçalho mais próximo
    ordem: int = 0  # posição da linha dentro da seção

    @property
    def id(self) -> str:
        """ID citável: '<seção>#<ordem>', ex.: '4.1#5'. Estável enquanto a seção não mudar."""
        return f"{self.secao}#{self.ordem}"

    @property
    def dobrado(self) -> str:
        return dobrar(self.texto)


@dataclass
class Perfil:
    linhas: list[Linha] = field(default_factory=list)

    @property
    def texto_dobrado(self) -> str:
        return "\n".join(l.dobrado for l in self.linhas)

    def linha(self, numero: int) -> Linha | None:
        for l in self.linhas:
            if l.numero == numero:
                return l
        return None

    def por_id(self, ref: str) -> Linha | None:
        """Aceita '4.1#5' ou 'L85'."""
        ref = ref.strip()
        if re.fullmatch(r"L\d+", ref):
            return self.linha(int(ref[1:]))
        for l in self.linhas:
            if l.id == ref:
                return l
        return None

    def da_secao(self, *prefixos: str) -> list[Linha]:
        return [l for l in self.linhas if any(l.secao == p or l.secao.startswith(p + ".") for p in prefixos)]


_CAB = re.compile(r"^(#{2,4})\s+(?:(\d+[a-z]?(?:\.\d+)*)\.?\s+)?(.*)$")


def carregar_perfil(caminho: Path = PERFIL) -> Perfil:
    perfil = Perfil()
    secao, titulo = "0", ""
    contagem: dict[str, int] = {}
    for i, bruto in enumerate(caminho.read_text(encoding="utf-8").splitlines(), start=1):
        texto = bruto.strip()
        m = _CAB.match(texto)
        if m:
            titulo = m.group(3)
            if m.group(2):
                secao = m.group(2)
            elif m.group(1) == "###" and secao:
                # subseções sem número (ex.: "### Domínio") herdam a seção pai
                secao = secao.split(".")[0]
            continue
        if not texto or texto == "---" or re.fullmatch(r"\|[\s|:-]+\|", texto):
            continue
        contagem[secao] = contagem.get(secao, 0) + 1
        perfil.linhas.append(Linha(i, texto, secao, titulo, contagem[secao]))
    return perfil


# ---------------------------------------------------------------- conceitos

_CACHE_CONCEITOS: dict[Path, list[dict]] = {}


def carregar_conceitos(caminho: Path = CONCEITOS) -> list[dict]:
    if caminho not in _CACHE_CONCEITOS:
        _CACHE_CONCEITOS[caminho] = json.loads(caminho.read_text(encoding="utf-8"))["conceitos"]
    return _CACHE_CONCEITOS[caminho]


def conceitos_no_texto(texto: str, conceitos: list[dict] | None = None) -> list[tuple[dict, str]]:
    """Conceitos citados no texto, com a forma exata usada.

    Variantes mais longas casam primeiro e "consomem" o trecho, para que
    'Tailwind CSS' não conte também como 'CSS'.
    """
    conceitos = conceitos or carregar_conceitos()
    pares = sorted(
        ((v, c) for c in conceitos for v in c["variantes"]),
        key=lambda p: -len(p[0].lstrip("=")),
    )
    restante = texto
    vistos: dict[str, tuple[dict, str]] = {}
    for var, c in pares:
        forma = achar_termo(restante, var)
        if not forma:
            continue
        if c["id"] not in vistos:
            vistos[c["id"]] = (c, forma)
        restante = restante.replace(forma, " " * len(forma), 1)
    return list(vistos.values())


def ler_entrada(caminho: str | None) -> str:
    if caminho in (None, "-"):
        return sys.stdin.read()
    return Path(caminho).read_text(encoding="utf-8")
