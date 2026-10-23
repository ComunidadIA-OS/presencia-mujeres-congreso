"""Carga de la muestra anotada a mano (verdad de referencia).

Tolera lo que hace Excel: separador ``;`` o ``,`` y codificación UTF-8 o ANSI (cp1252).
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

LABELS = ("defensa", "pregunta", "respuesta", "replica", "posicion", "procedimental", "otra")
CALIBRATION_ROWS = 15  # las primeras filas sirven para afinar la guía y como ejemplos; no se evalúan


def read_text(path):
    data = Path(path).read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def load_rows(path):
    raw = read_text(path)
    delimiter = max([",", ";", "\t"], key=raw.split("\n", 1)[0].count)
    return list(csv.DictReader(io.StringIO(raw), delimiter=delimiter))


def is_continuation(row):
    return row["etiqueta"].strip() == "otra" and "continuaci" in row.get("notas", "").lower()


def split_rows(rows):
    """Devuelve (calibración, evaluación). Evaluación excluye las continuaciones que se colaron."""
    calibration = rows[:CALIBRATION_ROWS]
    evaluation = [r for r in rows[CALIBRATION_ROWS:] if not is_continuation(r)]
    return calibration, evaluation


def validate(rows):
    """Lista de problemas: etiquetas vacías o fuera de la lista."""
    problems = []
    for i, r in enumerate(rows, 1):
        label = r["etiqueta"].strip()
        if label not in LABELS:
            problems.append(f"fila {i} ({r['ID']}): etiqueta no válida «{label}»")
    return problems
