#!/usr/bin/env python3
"""Métricas de posición en el debate: apertura (R1), cierre (R2) y posición temprana (R5).

Uso (desde la raíz del repositorio):
    python src/presencia/posicion.py data/raw/ParlaMint-ES.txt --tei data/raw/ParlaMint-ES.TEI

Los metadatos TSV no traen el punto del orden del día (la columna ``Agenda`` está vacía), así que
los puntos se toman de los encabezados ``<head>`` de la versión TEI (XML): cada encabezado abre un
punto nuevo y las intervenciones que le siguen pertenecen a él.

En cada punto se cuentan solo los turnos de oradores (sin presidencia) y sin continuaciones
(discursos partidos por una interrupción breve de la presidencia). Se usan los puntos con al menos
2 turnos.

- R1 Apertura: género de quien hace el primer turno del punto.
- R2 Cierre: género de quien hace el último turno del punto.
- R5 Posición: posición media de los turnos de cada género, de 0 (primero) a 1 (último).

La referencia de R1 y R2 es la proporción de mujeres entre todos los turnos de esos mismos puntos.
La razón de representación es (cuota de mujeres en apertura o cierre) / (referencia): 1 es
proporcional, menos de 1 indica que abren o cierran menos de lo que les correspondería.

Escribe (sin nombres ni identificadores de persona):
  data/processed/posicion_resumen.csv  métricas agregadas con intervalo de Wilson del 95 %
  data/processed/puntos.csv            una fila por punto: tipo de sección, nº de turnos y género de apertura y cierre

Nota: el XML pone un encabezado por sección del orden del día (p. ej. «PREGUNTAS»), no por cada
pregunta o iniciativa, así que R1 y R2 miden la apertura y el cierre de cada sección.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from itertools import groupby
from pathlib import Path

if __package__ in (None, ""):  # ejecución directa: python src/presencia/posicion.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from presencia.corpus import continuation_ids, iter_speeches, session_of, turn_number  # noqa: E402
from presencia.explore import CHAIR, field  # noqa: E402

TEI = "{http://www.tei-c.org/ns/1.0}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
MIN_TURNS = 2
MIN_GROUP = 30  # categorías y años con menos puntos no se informan por separado
MIN_PARTY = 200  # turnos mínimos de cada género para informar R5 de un grupo parlamentario


# ----------------------------------------------------------------- TEI -> puntos

def point_map(tei_path):
    """{ID de intervención: (nº de punto, título)} siguiendo el orden del documento TEI."""
    mapping, index, title = {}, 0, "(inicio de la sesión)"
    for _, elem in ET.iterparse(str(tei_path), events=("end",)):
        if elem.tag == TEI + "head":
            index += 1
            title = " ".join("".join(elem.itertext()).split())
        elif elem.tag == TEI + "u":
            uid = elem.get(XML_ID)
            if uid:
                mapping[uid] = (index, title)
            elem.clear()
    return mapping


SECTION_SPLIT = re.compile(r"\s*:\s*|\s+-\s+")


def categories(titles):
    """Tipo de sección de cada punto: el texto del encabezado antes de ':' o de ' - ' (así no se
    arrastran nombres de personas, que van detrás). Los que empiezan por '-' heredan la anterior."""
    out, current = [], "(sin categoría)"
    for t in titles:
        t = " ".join(t.split())
        if t.startswith("("):
            current = t
        elif not t.startswith("-"):
            current = SECTION_SPLIT.split(t, maxsplit=1)[0].strip(" -.") or "(sin categoría)"
        out.append(current)
    return out


def tei_index(tei_root):
    return {p.stem: p for p in Path(tei_root).rglob("*.xml")}


# ------------------------------------------------------------ corpus -> turnos

def is_minister(row):
    return field(row, "Speaker_minister").lower() == "minister"


def build_points(items, pmap, continuations):
    """Agrupa los turnos de oradores de una sesión por punto del orden del día.

    items: lista de (fila de metadatos, texto) de una sesión. Devuelve una lista de puntos:
    {"punto", "titulo", "turnos": [(ID, género, es_ministro, grupo), ...]} en orden.
    """
    rows = sorted((r for r, _ in items), key=lambda r: turn_number(field(r, "ID")) or 0)
    points = {}
    for row in rows:
        uid = field(row, "ID")
        if field(row, "Speaker_role") == CHAIR or uid in continuations or uid not in pmap:
            continue
        index, title = pmap[uid]
        point = points.setdefault(index, {"punto": index, "titulo": title, "turnos": []})
        point["turnos"].append((uid, field(row, "Speaker_gender"), is_minister(row), field(row, "Speaker_party")))
    return [points[k] for k in sorted(points)]


# --------------------------------------------------------------- estadística

def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def share_row(metric, group, women, total, ref_women, ref_total):
    lo, hi = wilson(women, total)
    pct = women / total if total else float("nan")
    ref = ref_women / ref_total if ref_total else float("nan")
    return {
        "metrica": metric, "grupo": group, "n": total, "mujeres": women,
        "pct_mujeres": round(100 * pct, 1), "ic95_inf": round(100 * lo, 1), "ic95_sup": round(100 * hi, 1),
        "referencia_pct": round(100 * ref, 1),
        "razon": round(pct / ref, 2) if ref and not math.isnan(pct) else "",
    }


def mean_ci(values):
    n = len(values)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    m = sum(values) / n
    if n < 2:
        return m, float("nan"), float("nan")
    sd = math.sqrt(sum((v - m) ** 2 for v in values) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    return m, m - half, m + half


def summarize(points, min_group=MIN_GROUP, min_party=MIN_PARTY):
    """points: lista de dicts con 'turnos', 'anio' y 'categoria'. Devuelve las filas del resumen."""
    rows = []

    def open_close(subset, group, ministers):
        k_open = k_close = n_open = n_close = ref_w = ref_n = 0
        for p in subset:
            turns = [t for t in p["turnos"] if ministers or not t[2]]
            if len(turns) < MIN_TURNS:
                continue
            first, last = turns[0][1], turns[-1][1]
            if first in ("F", "M"):
                n_open += 1
                k_open += first == "F"
            if last in ("F", "M"):
                n_close += 1
                k_close += last == "F"
            genders = [t[1] for t in turns if t[1] in ("F", "M")]
            ref_w += genders.count("F")
            ref_n += len(genders)
        rows.append(share_row("R1_apertura", group, k_open, n_open, ref_w, ref_n))
        rows.append(share_row("R2_cierre", group, k_close, n_close, ref_w, ref_n))

    open_close(points, "todas", ministers=True)
    open_close(points, "sin_ministros", ministers=False)

    by_cat = defaultdict(list)
    for p in points:
        by_cat[p["categoria"]].append(p)
    for cat, subset in sorted(by_cat.items(), key=lambda kv: -len(kv[1])):
        if sum(len(p["turnos"]) >= MIN_TURNS for p in subset) >= min_group:
            open_close(subset, f"categoria: {cat[:60]}", ministers=True)

    by_year = defaultdict(list)
    for p in points:
        by_year[p["anio"]].append(p)
    for year in sorted(by_year):
        open_close(by_year[year], f"anio: {year}", ministers=True)

    # R5: posición normalizada de cada turno dentro de su punto
    for label, ministers in (("todas", True), ("sin_ministros", False)):
        pos = {"F": [], "M": []}
        for p in points:
            turns = [t for t in p["turnos"] if ministers or not t[2]]
            n = len(turns)
            if n < MIN_TURNS:
                continue
            for i, t in enumerate(turns):
                if t[1] in pos:
                    pos[t[1]].append(i / (n - 1))
        for g, name in (("F", "mujeres"), ("M", "hombres")):
            m, lo, hi = mean_ci(pos[g])
            rows.append({
                "metrica": f"R5_posicion_media_{name}", "grupo": label, "n": len(pos[g]), "mujeres": "",
                "pct_mujeres": round(m, 3), "ic95_inf": round(lo, 3), "ic95_sup": round(hi, 3),
                "referencia_pct": 0.5, "razon": "",
            })

    # R5 dentro de cada grupo parlamentario: controla que el orden de intervención depende del grupo
    by_party = defaultdict(lambda: {"F": [], "M": []})
    for p in points:
        turns = [t for t in p["turnos"] if not t[2]]
        n = len(turns)
        if n < MIN_TURNS:
            continue
        for i, t in enumerate(turns):
            if t[1] in ("F", "M") and len(t) > 3 and t[3] not in ("?", "-", ""):
                by_party[t[3]][t[1]].append(i / (n - 1))
    for party, pos in sorted(by_party.items(), key=lambda kv: -(len(kv[1]["F"]) + len(kv[1]["M"]))):
        if min(len(pos["F"]), len(pos["M"])) < min_party:
            continue
        for g, name in (("F", "mujeres"), ("M", "hombres")):
            m, lo, hi = mean_ci(pos[g])
            rows.append({
                "metrica": f"R5_posicion_media_{name}", "grupo": f"grupo: {party[:40]}", "n": len(pos[g]),
                "mujeres": "", "pct_mujeres": round(m, 3), "ic95_inf": round(lo, 3), "ic95_sup": round(hi, 3),
                "referencia_pct": 0.5, "razon": "",
            })
    return rows


FIELDS = ["metrica", "grupo", "n", "mujeres", "pct_mujeres", "ic95_inf", "ic95_sup", "referencia_pct", "razon"]
POINT_FIELDS = ["Text_ID", "punto", "anio", "categoria", "turnos", "turnos_mujeres",
                "apertura_genero", "cierre_genero", "apertura_ID", "cierre_ID"]


def format_report(rows):
    lines = []
    for r in rows:
        if r["metrica"].startswith("R5"):
            lines.append(f"  {r['metrica']:<30} {r['grupo'][:30]:<30} n={r['n']:>6}  media {r['pct_mujeres']:.3f} "
                         f"[{r['ic95_inf']:.3f}, {r['ic95_sup']:.3f}]  (0 = primero, 1 = último)")
        else:
            lines.append(f"  {r['metrica']:<12} {r['grupo'][:48]:<48} n={r['n']:>5}  mujeres {r['pct_mujeres']:>5.1f} % "
                         f"[{r['ic95_inf']:.1f}–{r['ic95_sup']:.1f}]  ref {r['referencia_pct']:.1f} %  razón {r['razon']}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("carpeta", help="Carpeta con los TSV y los .txt, p. ej. data/raw/ParlaMint-ES.txt")
    parser.add_argument("--tei", default="data/raw/ParlaMint-ES.TEI", help="Carpeta con los XML TEI")
    parser.add_argument("--salida", default="data/processed/posicion_resumen.csv")
    parser.add_argument("--puntos", default="data/processed/puntos.csv")
    args = parser.parse_args(argv)

    index = tei_index(args.tei)
    if not index:
        print(f"No se encontraron XML en {Path(args.tei).resolve()}")
        return 2

    all_points, missing, sessions = [], 0, 0
    for text_id, group in groupby(iter_speeches(Path(args.carpeta)), key=lambda it: session_of(field(it[0], "ID"))):
        items = list(group)
        tei_path = index.get(text_id)
        if tei_path is None:
            missing += 1
            continue
        sessions += 1
        pmap = point_map(tei_path)
        points = build_points(items, pmap, continuation_ids(items))
        cats = categories([p["titulo"] for p in points])
        year = text_id.split("_", 1)[-1][:4]
        for p, cat in zip(points, cats):
            p.update(Text_ID=text_id, anio=year, categoria=cat)
        all_points.extend(points)

    usable = [p for p in all_points if len(p["turnos"]) >= MIN_TURNS]
    print(f"Sesiones: {sessions} (sin XML: {missing}) | puntos: {len(all_points)} | "
          f"puntos con {MIN_TURNS} o más turnos de oradores: {len(usable)}\n")

    rows = summarize(all_points)
    print(format_report(rows))

    out = Path(args.salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    with open(args.puntos, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=POINT_FIELDS)
        writer.writeheader()
        for p in all_points:
            t = p["turnos"]
            writer.writerow({
                "Text_ID": p["Text_ID"], "punto": p["punto"], "anio": p["anio"], "categoria": p["categoria"],
                "turnos": len(t),
                "turnos_mujeres": sum(x[1] == "F" for x in t),
                "apertura_genero": t[0][1] if t else "", "cierre_genero": t[-1][1] if t else "",
                "apertura_ID": t[0][0] if t else "", "cierre_ID": t[-1][0] if t else "",
            })
    print(f"\nEscrito {out} y {args.puntos}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
