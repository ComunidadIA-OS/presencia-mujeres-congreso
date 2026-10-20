#!/usr/bin/env python3
"""Genera tablas derivadas de ParlaMint-ES (metadatos + texto).

Uso (desde la raíz del repositorio):
    python src/presencia/export.py data/raw/ParlaMint-ES.txt

Escribe en data/processed/ (cambiable con --salida):
  intervenciones.csv  una fila por intervención: metadatos básicos, nº de palabras y nº de comentarios
  comentarios.csv     comentarios del transcriptor ([[...]]) únicos, con su frecuencia
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):  # ejecución directa: python src/presencia/export.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from presencia.corpus import analyze_text, iter_speeches  # noqa: E402
from presencia.explore import CHAIR, field  # noqa: E402

META_FIELDS = [
    "ID", "Date", "Speaker_role", "Speaker_gender", "Speaker_ID",
    "Speaker_minister", "Speaker_party", "Party_status", "Topic",
]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("carpeta", help="Carpeta con los TSV y los .txt, p. ej. data/raw/ParlaMint-ES.txt")
    parser.add_argument("--salida", default="data/processed", help="Carpeta de salida (por defecto data/processed)")
    args = parser.parse_args(argv)

    root = Path(args.carpeta)
    if not root.is_dir():
        print(f"La carpeta no existe: {root.resolve()}")
        return 2
    out_dir = Path(args.salida)
    out_dir.mkdir(parents=True, exist_ok=True)

    total_comments, speaker_comments = Counter(), Counter()
    n = missing = words_all = words_speakers = 0

    with open(out_dir / "intervenciones.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(META_FIELDS + ["words", "n_comments"])
        for row, text in iter_speeches(root):
            n += 1
            is_chair = field(row, "Speaker_role") == CHAIR
            if text is None:
                missing += 1
                words, comments = "", []
            else:
                words, comments = analyze_text(text)
                words_all += words
                if not is_chair:
                    words_speakers += words
            total_comments.update(comments)
            if not is_chair:
                speaker_comments.update(comments)
            writer.writerow([field(row, f) for f in META_FIELDS] + [words, len(comments)])

    if n == 0:
        print(f"No se encontraron metadatos en {root.resolve()}. Ejecuta primero explore.py para diagnosticar.")
        return 1

    with open(out_dir / "comentarios.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["comentario", "total", "en_oradores"])
        for comment, total in total_comments.most_common():
            writer.writerow([comment, total, speaker_comments.get(comment, 0)])

    print(f"Intervenciones: {n}   sin texto asociado: {missing}")
    print(f"Palabras: {words_all} (oradores: {words_speakers})")
    print(
        f"Comentarios del transcriptor: {sum(total_comments.values())} en total, "
        f"{len(total_comments)} distintos, {sum(speaker_comments.values())} en intervenciones de oradores"
    )
    print(f"Archivos escritos en {out_dir.resolve()}: intervenciones.csv, comentarios.csv")
    if missing:
        print("AVISO: hay intervenciones sin texto; revisar la asociación de archivos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
