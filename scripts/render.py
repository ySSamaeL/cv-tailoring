"""Markdown canônico -> PDF (Typst), com auditoria de uma página.

Uso:
    python scripts/render.py curriculo.md [-o curriculo.pdf] [--paginas 1]

Passos:
1. Lê o Markdown canônico e monta os dados do template (assets/curriculo.typ).
2. Compila com o pacote Python `typst` (sem binário separado).
3. Se passar de uma página, aperta a densidade numa escada curta (fonte nunca
   abaixo de 9,5 pt). Se ainda assim não couber, falha (código 2) e diz quanto
   sobrou: quem corta bullets é a skill, por ordem de relevância, nunca o script.
4. Audita o PDF: número de páginas, texto extraível (ATS), nome e e-mail presentes,
   e quanto da página foi usado (aviso abaixo de 85%).
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

from _comum import RAIZ, dobrar
from _curriculo import ler

TEMPLATE = RAIZ / "assets" / "curriculo.typ"

# (fonte em pt, margem lateral em cm, margem vertical em cm, respiro entre seções)
ESCADA = [
    (10.5, 1.5, 1.3, 1.0),
    (10.2, 1.4, 1.2, 0.9),
    (10.0, 1.35, 1.1, 0.8),
    (9.8, 1.3, 1.05, 0.7),
    (9.6, 1.25, 1.0, 0.6),
    (9.5, 1.2, 0.95, 0.5),
]


def compilar(dados: dict, degrau: tuple, formato: str = "pdf", ppi: int = 110):
    import typst

    fonte, mx, my, respiro = degrau
    dados = dict(dados, estilo={"fonte": fonte, "margem_x": mx, "margem_y": my, "respiro": respiro})
    extra = {"format": "png", "ppi": ppi} if formato == "png" else {}
    return typst.compile(
        str(TEMPLATE),
        root=str(RAIZ),
        sys_inputs={"dados": json.dumps(dados, ensure_ascii=False)},
        **extra,
    )


def auditar(pdf: bytes) -> dict:
    from pypdf import PdfReader

    leitor = PdfReader(io.BytesIO(pdf))
    pagina = leitor.pages[0]
    altura = float(pagina.mediabox.height)
    ys: list[float] = []

    def visitante(texto, cm, tm, _fonte, _tamanho):
        if texto.strip():
            ys.append(tm[4] * cm[1] + tm[5] * cm[3] + cm[5])

    texto = pagina.extract_text(visitor_text=visitante)
    menor = min(ys) if ys else altura
    return {
        "paginas": len(leitor.pages),
        "texto": "\n".join(p.extract_text() for p in leitor.pages),
        "preenchimento": round(100 * (altura - menor) / altura),
        "primeira_pagina": texto,
    }


def renderizar(md: str, max_paginas: int = 1) -> tuple[bytes | None, dict]:
    dados, unidades = ler(md)
    relatorio: dict = {"degraus": []}
    melhor = None
    for degrau in ESCADA:
        pdf = compilar(dados, degrau)
        aud = auditar(pdf)
        relatorio["degraus"].append({"fonte": degrau[0], "paginas": aud["paginas"], "preenchimento": aud["preenchimento"]})
        melhor = (pdf, aud, degrau)
        if aud["paginas"] <= max_paginas:
            break
    pdf, aud, degrau = melhor
    relatorio.update(
        fonte_final=degrau[0], paginas=aud["paginas"], preenchimento=aud["preenchimento"], avisos=[], erros=[]
    )
    if aud["paginas"] > max_paginas:
        relatorio["erros"].append(
            f"{aud['paginas']} páginas mesmo com fonte {degrau[0]} pt. Corte os bullets menos relevantes para a vaga "
            "(primeiro projetos fora do tema, depois bullets das experiências mais antigas; nunca remova uma experiência inteira)."
        )
    texto = dobrar(aud["texto"])
    if dados["nome"] and dobrar(dados["nome"]).split()[0] not in texto:
        relatorio["erros"].append("O nome não aparece no texto extraído do PDF (problema de ATS).")
    emails = [c[0]["t"] for c in dados["contato"] if c and "@" in c[0]["t"]]
    for e in emails:
        if dobrar(e) not in texto.replace("\n", ""):
            relatorio["erros"].append(f"E-mail {e} não aparece no texto extraído do PDF.")
    itens = [u.texto for u in unidades if u.tipo == "item"]
    perdidos = [i for i in itens if dobrar(i.split()[0]) not in texto] if itens else []
    if perdidos:
        relatorio["avisos"].append(f"{len(perdidos)} bullet(s) não localizados no texto extraído: confira o PDF.")
    if aud["paginas"] <= max_paginas and aud["preenchimento"] < 85 and degrau == ESCADA[0]:
        relatorio["avisos"].append(
            f"Página {aud['preenchimento']}% preenchida: há espaço para mais um bullet relevante (ou um projeto)."
        )
    relatorio["degrau"] = degrau
    relatorio["dados"] = dados
    return pdf, relatorio


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("markdown")
    ap.add_argument("-o", "--saida", help="PDF de saída (padrão: mesmo nome com .pdf)")
    ap.add_argument("--paginas", type=int, default=1, help="máximo de páginas (padrão 1)")
    ap.add_argument("--png", action="store_true", help="grava também uma prévia PNG da primeira página")
    args = ap.parse_args()

    origem = Path(args.markdown)
    destino = Path(args.saida) if args.saida else origem.with_suffix(".pdf")
    pdf, rel = renderizar(origem.read_text(encoding="utf-8"), args.paginas)
    destino.write_bytes(pdf)
    if args.png:
        imagem = compilar(rel["dados"], rel["degrau"], formato="png")
        if isinstance(imagem, list):
            imagem = imagem[0]
        destino.with_suffix(".png").write_bytes(imagem)
    print(f"PDF: {destino} · {rel['paginas']} página(s) · fonte {rel['fonte_final']} pt · página {rel['preenchimento']}% preenchida")
    for a in rel["avisos"]:
        print(f"AVISO: {a}")
    for e in rel["erros"]:
        print(f"ERRO: {e}")
    return 2 if rel["erros"] else 0


if __name__ == "__main__":
    sys.exit(main())
