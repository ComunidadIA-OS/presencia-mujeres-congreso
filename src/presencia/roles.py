#!/usr/bin/env python3
"""Métricas de protagonismo por género a partir de los roles clasificados (roles.csv).

Uso (desde la raíz del repositorio):
    python src/presencia/roles.py data/processed/roles.csv

Para cada grupo (todas, sin ministros/as, oposición, Gobierno y socios) calcula:
  - reparto de roles dentro de cada género: % de las intervenciones de mujeres que son
    ``defensa``, ``pregunta``... con intervalo de confianza del 95 % (Wilson);
  - cuota de mujeres en cada rol, ponderada con ``peso`` para estimar el corpus completo;
  - razón de representación: cuota de mujeres en el rol / cuota de mujeres en el grupo
    (1 = proporcional; < 1 = las mujeres ocupan ese rol menos de lo que les tocaría).
Escribe también data/processed/roles_resumen.csv.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

ROLES = ("defensa", "pregunta", "respuesta", "replica", "posicion", "procedimental", "otra")
GROUPS = {
    "todas": lambda r: True,
    "sin_ministros": lambda r: r["Speaker_minister"] != "Minister",
    "oposicion": lambda r: r["Party_status"] == "Opposition" and r["Speaker_minister"] != "Minister",
    "gobierno_y_socios": lambda r: r["Party_status"] == "Coalition" and r["Speaker_minister"] != "Minister",
    "ministros": lambda r: r["Speaker_minister"] == "Minister",
}


def wilson(k, n, z=1.96):
    """Intervalo de confianza del 95 % para una proporción (Wilson)."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def summarize(rows):
    """Filas de resumen: una por (grupo, rol)."""
    out = []
    for group, keep in GROUPS.items():
        sub = [r for r in rows if r["rol"] and keep(r)]
        by_gender = {g: [r for r in sub if r["Speaker_gender"] == g] for g in ("F", "M")}
        if not by_gender["F"] or not by_gender["M"]:
            continue
        weight = {g: sum(float(r["peso"]) for r in by_gender[g]) for g in ("F", "M")}
        share_group = weight["F"] / (weight["F"] + weight["M"])
        for role in ROLES:
            line = {"grupo": group, "rol": role}
            for g in ("F", "M"):
                n = len(by_gender[g])
                k = sum(1 for r in by_gender[g] if r["rol"] == role)
                low, high = wilson(k, n)
                line.update({f"n_{g}": n, f"k_{g}": k, f"pct_{g}": 100 * k / n,
                             f"ic_{g}": f"{100 * low:.1f}-{100 * high:.1f}"})
            wf = sum(float(r["peso"]) for r in by_gender["F"] if r["rol"] == role)
            wm = sum(float(r["peso"]) for r in by_gender["M"] if r["rol"] == role)
            if wf + wm == 0:
                continue
            line["cuota_mujeres"] = 100 * wf / (wf + wm)
            line["cuota_mujeres_grupo"] = 100 * share_group
            line["razon"] = (wf / (wf + wm)) / share_group if share_group else 0.0
            out.append(line)
    return out


def format_summary(summary):
    lines = []
    for group in GROUPS:
        part = [s for s in summary if s["grupo"] == group]
        if not part:
            continue
        lines.append(f"\n== {group}  (mujeres n={part[0]['n_F']}, hombres n={part[0]['n_M']}; "
                     f"cuota de mujeres en el grupo {part[0]['cuota_mujeres_grupo']:.1f} %) ==")
        lines.append(f"{'rol':<15}{'% en mujeres':>20}{'% en hombres':>20}{'cuota mujeres':>15}{'razón':>8}")
        for s in part:
            lines.append(f"{s['rol']:<15}{s['pct_F']:>6.1f} ({s['ic_F']:>11}){s['pct_M']:>6.1f} ({s['ic_M']:>11})"
                         f"{s['cuota_mujeres']:>13.1f} %{s['razon']:>8.2f}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("roles", help="CSV de classify.py, p. ej. data/processed/roles.csv")
    parser.add_argument("--salida", default="data/processed/roles_resumen.csv")
    args = parser.parse_args(argv)

    with open(args.roles, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    missing = sum(1 for r in rows if not r["rol"])
    by_method = {}
    for r in rows:
        by_method[r["metodo"]] = by_method.get(r["metodo"], 0) + 1
    print(f"Intervenciones: {len(rows)}  por método: {by_method}")
    if missing:
        print(f"AVISO: {missing} sin rol (se excluyen). Completa la clasificación antes de dar cifras finales.")

    summary = summarize(rows)
    print(format_summary(summary))
    print("\nrazón = cuota de mujeres en el rol / cuota de mujeres en el grupo (1 = proporcional).")
    print("Cifras de un clasificador automático (F1 macro ~0,89 en evaluación): leer con su margen de error.")

    out = Path(args.salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0].keys()) if summary else ["grupo"])
        writer.writeheader()
        for s in summary:
            writer.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in s.items()})
    print(f"\nEscrito en {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
