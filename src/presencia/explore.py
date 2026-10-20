#!/usr/bin/env python3
"""Exploración inicial de los metadatos TSV de ParlaMint-ES.

Recorre una carpeta, lee los TSV de metadatos en inglés (los que tienen la
columna ``Speaker_gender``) y cuenta intervenciones por rol, género, año,
condición de ministro y tema. Solo usa la biblioteca estándar.

Uso (desde la raíz del repositorio):
    python src/presencia/explore.py data/raw/ParlaMint-ES.txt
    python src/presencia/explore.py data/raw/ParlaMint-ES.txt --salida data/processed/informe.txt
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

REQUIRED_COLUMN = "Speaker_gender"
CHAIR = "Chairperson"
ENGLISH_ROLES = {"Chairperson", "Regular", "Guest"}


def field(row, name):
    """Valor de una columna; '?' si falta o si la fila es más corta que la cabecera."""
    value = row.get(name)
    return value if value else "?"


def is_english_metadata(path):
    """True si el TSV tiene las columnas esperadas y sus valores están en inglés.

    Las versiones en español y en inglés comparten los nombres de columna y solo
    cambian los valores (p. ej. 'Presidencia' frente a 'Chairperson'), así que se
    distinguen por el rol de la primera fila.
    """
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if REQUIRED_COLUMN not in (reader.fieldnames or []):
            return False
        first = next(reader, None)
    return first is not None and first.get("Speaker_role") in ENGLISH_ROLES


def find_metadata_files(root):
    """Devuelve los TSV de metadatos en inglés que hay bajo ``root``."""
    return [p for p in sorted(Path(root).rglob("*.tsv")) if is_english_metadata(p)]


def summarize(files):
    """Cuenta intervenciones por rol, género, año, ministro y tema."""
    summary = {
        "files": len(files),
        "rows": 0,
        "role": Counter(),
        "role_gender": Counter(),
        "chair_year": defaultdict(Counter),  # año -> género de la presidencia
        "gender": Counter(),  # género de las intervenciones de oradores (sin presidencia)
        "speakers": defaultdict(set),  # género -> ids de orador (sin presidencia)
        "year_gender": defaultdict(Counter),  # año -> género (sin presidencia)
        "minister": Counter(),
        "topic_gender": defaultdict(Counter),  # tema -> género (sin presidencia)
    }
    for path in files:
        with open(path, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                summary["rows"] += 1
                role = field(row, "Speaker_role")
                gender = field(row, "Speaker_gender")
                summary["role"][role] += 1
                summary["role_gender"][(role, gender)] += 1
                if role == CHAIR:
                    summary["chair_year"][field(row, "Date")[:4]][gender] += 1
                    continue
                summary["gender"][gender] += 1
                if gender in ("F", "M"):
                    summary["speakers"][gender].add(field(row, "Speaker_ID"))
                summary["year_gender"][field(row, "Date")[:4]][gender] += 1
                summary["minister"][field(row, "Speaker_minister")] += 1
                summary["topic_gender"][field(row, "Topic")][gender] += 1
    return summary


def share_women(counter):
    """% de mujeres entre las intervenciones con género M o F."""
    women, men = counter.get("F", 0), counter.get("M", 0)
    total = women + men
    return 100 * women / total if total else float("nan")


def build_report(s):
    """Devuelve el informe como texto."""
    out = [f"Archivos de metadatos: {s['files']}   Filas (intervenciones): {s['rows']}", ""]

    out.append("== Intervenciones por rol ==")
    out += [f"  {role:<14}{n:>9}" for role, n in s["role"].most_common()]

    out += ["", "== Rol x género =="]
    out += [f"  {role:<14}{gender:<4}{n:>9}" for (role, gender), n in sorted(s["role_gender"].items())]

    out += ["", "== Resumen sin presidencia (intervenciones de oradores) =="]
    g = s["gender"]
    out.append(f"  Total: {sum(g.values())}   F={g.get('F', 0)}   M={g.get('M', 0)}   otros/desconocido={sum(g.values()) - g.get('F', 0) - g.get('M', 0)}")
    out.append(f"  % de mujeres (entre F y M): {share_women(g):.1f}")

    women, men = len(s["speakers"]["F"]), len(s["speakers"]["M"])
    total = women + men
    pct = 100 * women / total if total else float("nan")
    out.append(f"  Oradores distintos: mujeres={women}  hombres={men}  % mujeres={pct:.1f}")

    out += ["", "== % de mujeres en las intervenciones, por año =="]
    for year in sorted(s["year_gender"]):
        c = s["year_gender"][year]
        out.append(f"  {year}  {share_women(c):5.1f} %   (F={c.get('F', 0)}, M={c.get('M', 0)}, otros={sum(c.values()) - c.get('F', 0) - c.get('M', 0)})")

    out += ["", "== Presidencia (turnos con rol Chairperson) =="]
    out.append("  año    turnos  género conocido  % mujeres entre conocidos")
    chair_total = Counter()
    for year in sorted(s["chair_year"]):
        c = s["chair_year"][year]
        chair_total.update(c)
        known = c.get("F", 0) + c.get("M", 0)
        out.append(f"  {year}  {sum(c.values()):7}  {100 * known / sum(c.values()):12.1f} %  {share_women(c):14.1f} %")
    turns = sum(chair_total.values())
    if turns:
        known = chair_total.get("F", 0) + chair_total.get("M", 0)
        out.append(f"  Total {turns:7}  {100 * known / turns:12.1f} %  {share_women(chair_total):14.1f} %")

    out += ["", "== Condición de ministro =="]
    out += [f"  {value:<14}{n:>9}" for value, n in s["minister"].most_common()]

    out += ["", "== % de mujeres por tema =="]
    for topic, c in sorted(s["topic_gender"].items(), key=lambda kv: -sum(kv[1].values())):
        out.append(f"  {topic:<32}{share_women(c):5.1f} %   (n={sum(c.values())})")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("carpeta", help="Carpeta con los TSV, p. ej. data/raw/ParlaMint-ES.txt")
    parser.add_argument("--salida", help="Guarda además el informe en este archivo (UTF-8)")
    args = parser.parse_args(argv)

    root = Path(args.carpeta)
    if not root.is_dir():
        print(f"La carpeta no existe: {root.resolve()}")
        print("Comprueba la ruta. 'dir data\\raw' (Windows) o 'ls data/raw' (Mac/Linux) muestra lo que hay.")
        return 2

    files = find_metadata_files(root)
    if not files:
        extensions = Counter(p.suffix or "(sin extensión)" for p in root.rglob("*") if p.is_file())
        print(f"No se encontraron TSV con la columna '{REQUIRED_COLUMN}' en {root.resolve()}.")
        print(f"Extensiones encontradas: {dict(extensions)}")
        return 1

    report = build_report(summarize(files))
    print(report)
    if args.salida:
        target = Path(args.salida)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report + "\n", encoding="utf-8")
        print(f"\nInforme guardado en {target.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
