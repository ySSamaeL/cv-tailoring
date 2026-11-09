"""Gera dist/cv-tailoring.zip para enviar como skill pessoal no claude.ai / Cowork.

Uso:
    python scripts/empacotar.py

O zip tem uma pasta raiz 'cv-tailoring/' com SKILL.md, references/, scripts/,
assets/ e requirements.txt. Ficam de fora: historico/ (suas candidaturas),
evals/, tests/, docs/ e qualquer arquivo ignorado pelo git.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INCLUIR = ["SKILL.md", "requirements.txt", "references", "scripts", "assets"]
IGNORAR = {"__pycache__", ".pytest_cache"}


def arquivos() -> list[Path]:
    saida = []
    for item in INCLUIR:
        caminho = RAIZ / item
        if caminho.is_file():
            saida.append(caminho)
            continue
        for p in sorted(caminho.rglob("*")):
            if p.is_file() and not (IGNORAR & set(p.parts)) and p.suffix != ".pyc":
                saida.append(p)
    return saida


def main() -> int:
    destino = RAIZ / "dist" / "cv-tailoring.zip"
    destino.parent.mkdir(exist_ok=True)
    lista = arquivos()
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for p in lista:
            z.write(p, Path("cv-tailoring") / p.relative_to(RAIZ))
    print(f"{destino} · {len(lista)} arquivos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
