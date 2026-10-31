#!/usr/bin/env python3
"""Turns compat/resultados.csv into compat/TABELA.md, sorted by RAM and then by game.

Add one line to the CSV per report received (the issue forms ask for exactly these fields).
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "compat" / "resultados.csv"
OUT_PATH = ROOT / "compat" / "TABELA.md"
COLUMNS = ["aparelho", "chip", "ram", "android", "apk", "build", "jogo", "api", "fps", "observacoes"]
TITLES = ["Celular", "Chip", "RAM", "Android", "APK", "Build", "Jogo", "API", "FPS", "Observações"]


def ram_key(value: str) -> int:
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else 0


def cell(value: str) -> str:
    return (value or "").replace("|", "/").replace("\n", " ").strip()


def main() -> int:
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            print(f"error: columns missing in the CSV: {', '.join(missing)}", file=sys.stderr)
            return 1
        rows = list(reader)

    rows.sort(key=lambda r: (ram_key(r["ram"]), r["jogo"].lower(), r["aparelho"].lower()))
    lines = [
        "# Tabela de desempenho",
        "",
        "Gerada de `compat/resultados.csv` por `tools/compat_table.py`. Cada linha é um relato de usuário.",
        "",
    ]
    if not rows:
        lines.append("Ainda não há relatos.")
    else:
        lines.append("| " + " | ".join(TITLES) + " |")
        lines.append("|" + "|".join(["---"] * len(TITLES)) + "|")
        for row in rows:
            lines.append("| " + " | ".join(cell(row[c]) for c in COLUMNS) + " |")
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"== wrote {OUT_PATH.relative_to(ROOT)} with {len(rows)} reports")
    return 0


if __name__ == "__main__":
    sys.exit(main())
