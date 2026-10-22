#!/usr/bin/env python3
"""Prepara la muestra para anotar a mano el rol de las intervenciones.

Uso (desde la raíz del repositorio):
    python src/presencia/sample.py data/raw/ParlaMint-ES.txt
    python src/presencia/sample.py data/raw/ParlaMint-ES.txt --n 60 --semilla 42

Elige n intervenciones de mujeres y n de hombres (rol Regular) al azar y escribe
data/processed/muestra_anotacion.csv. Excluye las continuaciones (discursos partidos
por una interrupción breve de la presidencia). El archivo NO incluye género, nombre
ni grupo, para anotar a ciegas; el género se une después por el ID. Incluye la
estructura de los turnos anteriores (columna ``secuencia``), que no identifica a nadie.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from itertools import groupby
from pathlib import Path

if __package__ in (None, ""):  # ejecución directa: python src/presencia/sample.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from presencia.corpus import (  # noqa: E402
    COMMENT_RE,
    continuation_ids,
    iter_speeches,
    sequence_context,
    session_of,
    turn_number,
    turns_of,
    word_count,
)
from presencia.explore import field  # noqa: E402

FIELDS = ["ID", "previo_2", "previo_1", "secuencia", "inicio", "final", "palabras", "etiqueta", "notas"]


def excerpt(text, limit, tail=False):
    """Primeras (o últimas, si tail) ``limit`` palabras, sin comentarios del transcriptor."""
    words = COMMENT_RE.sub(" ", text or "").split()
    if len(words) <= limit:
        return " ".join(words)
    if tail:
        return "… " + " ".join(words[-limit:])
    return " ".join(words[:limit]) + " …"


def session_key(item):
    return session_of(field(item[0], "ID"))


def build_record(row, text, by_id, sequence):
    """Arma la fila de anotación con el contexto de los dos turnos anteriores."""
    speech_id = row["ID"]
    base, number = session_of(speech_id), turn_number(speech_id)
    prev1 = by_id.get(f"{base}.u{number - 1}", "") if number else ""
    prev2 = by_id.get(f"{base}.u{number - 2}", "") if number else ""
    words = word_count(text)
    return {
        "ID": speech_id,
        "previo_2": excerpt(prev2, 50, tail=True),
        "previo_1": excerpt(prev1, 80),
        "secuencia": sequence,
        "inicio": excerpt(text, 120),
        "final": excerpt(text, 40, tail=True) if words > 160 else "",
        "palabras": words,
        "etiqueta": "",
        "notas": "",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("carpeta", help="Carpeta con los TSV y los .txt, p. ej. data/raw/ParlaMint-ES.txt")
    parser.add_argument("--n", type=int, default=60, help="Intervenciones por género (por defecto 60)")
    parser.add_argument("--semilla", type=int, default=42, help="Semilla del azar, para repetir la muestra")
    parser.add_argument("--salida", default="data/processed/muestra_anotacion.csv")
    args = parser.parse_args(argv)

    root = Path(args.carpeta)
    if not root.is_dir():
        print(f"La carpeta no existe: {root.resolve()}")
        return 2

    # Pasada 1: candidatos (intervenciones de diputados/as con género M o F, sin continuaciones)
    candidates = {"F": [], "M": []}
    excluded = 0
    for _, group in groupby(iter_speeches(root), key=session_key):
        items = list(group)
        continuations = continuation_ids(items)
        for row, _ in items:
            gender = field(row, "Speaker_gender")
            if field(row, "Speaker_role") != "Regular" or gender not in candidates:
                continue
            if row.get("ID") in continuations:
                excluded += 1
            else:
                candidates[gender].append(field(row, "ID"))

    rng = random.Random(args.semilla)
    chosen = set()
    for gender in ("F", "M"):
        k = min(args.n, len(candidates[gender]))
        chosen.update(rng.sample(sorted(candidates[gender]), k))
    if not chosen:
        print("No hay candidatos: ejecuta explore.py para diagnosticar.")
        return 1

    # Pasada 2: texto, contexto y estructura de las elegidas
    records = []
    for _, group in groupby(iter_speeches(root), key=session_key):
        items = list(group)
        turns = turns_of(items)
        position = {turn[0]: i for i, turn in enumerate(turns)}
        by_id = {r.get("ID"): t for r, t in items}
        for row, text in items:
            if row.get("ID") in chosen:
                records.append(build_record(row, text, by_id, sequence_context(turns, position[row["ID"]])))

    rng.shuffle(records)  # que no salgan agrupadas por género
    out = Path(args.salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:  # utf-8-sig: Excel muestra bien las tildes
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)

    print(f"Candidatos: mujeres {len(candidates['F'])}, hombres {len(candidates['M'])}")
    print(f"Continuaciones excluidas: {excluded}")
    print(f"Muestra: {len(records)} intervenciones (semilla {args.semilla})")
    print(f"Escrito en {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
