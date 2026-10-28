#!/usr/bin/env python3
"""Gráficos de la evaluación y de las métricas de rol por género (PNG para la presentación).

Uso (desde la raíz del repositorio, después de evaluate.py, classify.py y roles.py):
    python src/presencia/figures.py

No llama a ningún modelo: usa la caché de data/processed/llm/, la muestra anotada,
data/processed/intervenciones.csv (para unir el género por ID) y el resumen de roles:
roles_resumen_completo.csv (corpus completo) si existe; si no, roles_resumen.csv (muestra de 3.000).
Escribe docs/figuras/*.png.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401

from presencia import baseline, llm  # noqa: E402
from presencia.annotated import LABELS, load_rows, split_rows  # noqa: E402
from presencia.evaluation import evaluate  # noqa: E402

# Paleta validada (dataviz): violeta = mujeres, aqua = hombres; gris para lo secundario.
WOMEN, MEN = "#6250d6", "#1baf7a"
ACCENT, MUTED = "#6250d6", "#c3c2b7"
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e0", "#ffffff"
ROLE_NAMES = {"defensa": "Defensa de iniciativa", "pregunta": "Pregunta / interpelación",
              "respuesta": "Respuesta", "replica": "Réplica", "posicion": "Fijación de posición",
              "procedimental": "Procedimental"}


def style(ax, title, subtitle=None):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_2, length=0, labelsize=10)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.figure.text(0.02, 0.96, title, fontsize=14, fontweight="bold", color=INK, va="top")
    if subtitle:
        ax.figure.text(0.02, 0.905, subtitle, fontsize=10, color=INK_2, va="top")


def eval_predictions(annotated, cache_dir, model):
    rows = load_rows(annotated)
    _, ev = split_rows(rows)
    cache = llm.load_cache(Path(cache_dir) / f"{model}.jsonl")
    preds = {"Reglas (sin IA)": [baseline.classify(r) for r in ev]}
    for name in ("gpt-oss-120b", model):
        c = llm.load_cache(Path(cache_dir) / f"{name}.jsonl")
        if c:
            preds[name] = [llm.parse_label(c.get(r["ID"], "")) for r in ev]
    preds[f"Híbrido: estructura + {model}"] = [baseline.structural_label(r) or llm.parse_label(cache.get(r["ID"], ""))
                                              for r in ev]
    return ev, [r["etiqueta"].strip() for r in ev], preds


def fig_evaluation(gold, preds, out):
    names = list(preds)
    f1 = [evaluate(gold, preds[n], LABELS)["macro_f1"] for n in names]
    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    y = range(len(names))[::-1]
    colors = [ACCENT if i == len(names) - 1 else MUTED for i in range(len(names))]
    ax.barh(list(y), f1, height=0.55, color=colors)
    for yi, v in zip(y, f1):
        ax.text(v + 0.01, yi, f"{v:.2f}".replace(".", ","), va="center", fontsize=11, color=INK, fontweight="bold")
    ax.set_yticks(list(y), names, color=INK)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
    ax.set_xlabel("F1 macro (1 = acierto perfecto en todas las clases)", color=INK_2)
    style(ax, "El método híbrido es el que mejor identifica el rol",
          f"F1 macro sobre {len(gold)} intervenciones anotadas a mano")
    fig.subplots_adjust(left=0.36, right=0.95, top=0.80, bottom=0.17)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def fig_error_gender(ev, gold, preds, genders, out):
    names = [n for n in preds if n.startswith(("Reglas", "Híbrido"))]
    data = {}
    for n in names:
        for g in ("F", "M"):
            idx = [i for i, r in enumerate(ev) if genders.get(r["ID"]) == g]
            errors = sum(gold[i] != preds[n][i] for i in idx)
            data[(n, g)] = (100 * errors / len(idx), errors, len(idx))
    fig, ax = plt.subplots(figsize=(9, 3.8), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    h = 0.34
    for i, n in enumerate(names[::-1]):
        for j, (g, color, label) in enumerate((("M", MEN, "Hombres"), ("F", WOMEN, "Mujeres"))):
            pct, k, total = data[(n, g)]
            yy = i + (j - 0.5) * (h + 0.04)
            ax.barh(yy, pct, height=h, color=color, label=label if i == 0 else None)
            ax.text(pct + 0.4, yy, f"{pct:.0f} %  ({k} de {total})", va="center", fontsize=10, color=INK)
    ax.set_yticks(range(len(names)), [n.split(":")[0] for n in names[::-1]], color=INK)
    ax.set_xlim(0, max(v[0] for v in data.values()) * 1.45)
    ax.set_xlabel("% de intervenciones mal clasificadas", color=INK_2)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], frameon=False, loc="lower right", fontsize=10)
    style(ax, "Sin IA, el error con las mujeres es más del doble",
          "Las reglas no detectan bien preguntas e iniciativas, más frecuentes en sus intervenciones")
    fig.subplots_adjust(left=0.14, right=0.97, top=0.78, bottom=0.17)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def read_summary(path, group):
    with open(path, encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh) if r["grupo"] == group and r["rol"] in ROLE_NAMES]


def fig_roles(summary, out, source):
    rows = sorted(summary, key=lambda r: float(r["pct_F"]) + float(r["pct_M"]))
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    for i, r in enumerate(rows):
        for g, color, dy in (("F", WOMEN, 0.15), ("M", MEN, -0.15)):
            pct = float(r[f"pct_{g}"])
            low, high = (float(x) for x in r[f"ic_{g}"].split("-"))
            ax.plot([low, high], [i + dy, i + dy], color=color, linewidth=2, solid_capstyle="round")
            ax.plot(pct, i + dy, "o", color=color, markersize=8, markeredgecolor=SURFACE, markeredgewidth=2,
                    label=("Mujeres" if g == "F" else "Hombres") if i == len(rows) - 1 else None)
        ax.text(max(float(r["pct_F"]), float(r["pct_M"])) + 5, i,
                f"{float(r['pct_F']):.1f} % / {float(r['pct_M']):.1f} %".replace(".", ","),
                va="center", fontsize=9, color=INK_2)
    labels = [ROLE_NAMES[r["rol"]] for r in rows]
    ax.set_yticks(range(len(rows)), labels, color=INK)
    ax.set_xlim(0, 75)
    ax.set_xlabel("% de las intervenciones de cada género (punto) e intervalo de confianza del 95 % (línea)",
                  color=INK_2, fontsize=9)
    ax.legend(frameon=False, loc="lower right", fontsize=10)
    n_f, n_m = rows[0]["n_F"], rows[0]["n_M"]
    style(ax, "Las diputadas presentan más iniciativas y preguntan más al Gobierno",
          f"Rol de cada intervención, sin ministros/as (mujeres n = {n_f}, hombres n = {n_m}); mujeres / hombres")
    fig.text(0.02, 0.055, f"Fuente: {source}.", fontsize=8, color=INK_2)
    fig.text(0.02, 0.02, "Rol clasificado con el método híbrido (regla estructural + Qwen3.5-397B-A17B), "
             "con error similar para mujeres y hombres.", fontsize=8, color=INK_2)
    fig.subplots_adjust(left=0.27, right=0.97, top=0.80, bottom=0.2)
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anotada", default="data/annotated/muestra_anotada.csv")
    parser.add_argument("--cache", default="data/processed/llm")
    parser.add_argument("--modelo", default="Qwen3.5-397B-A17B")
    parser.add_argument("--intervenciones", default="data/processed/intervenciones.csv")
    parser.add_argument("--resumen", default=None,
                        help="Resumen de roles; por defecto, el del corpus completo si existe, si no el de la muestra")
    parser.add_argument("--salida", default="docs/figuras")
    args = parser.parse_args(argv)

    out = Path(args.salida)
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "DejaVu Sans"
    ev, gold, preds = eval_predictions(args.anotada, args.cache, args.modelo)
    fig_evaluation(gold, preds, out / "1_evaluacion_metodos.png")
    with open(args.intervenciones, encoding="utf-8", newline="") as fh:
        genders = {r["ID"]: r["Speaker_gender"] for r in csv.DictReader(fh)}
    fig_error_gender(ev, gold, preds, genders, out / "2_error_por_genero.png")
    resumen = args.resumen
    if resumen is None:
        full = Path("data/processed/roles_resumen_completo.csv")
        resumen = str(full) if full.is_file() else "data/processed/roles_resumen.csv"
    if Path(resumen).is_file():
        source = ("corpus completo de diputadas y diputados, 2015–2023" if "completo" in resumen
                  else "muestra estratificada de 3.000 intervenciones")
        fig_roles(read_summary(resumen, "sin_ministros"), out / "3_roles_por_genero.png", source)
        print(f"Rol por género a partir de {resumen}")
    print(f"Gráficos escritos en {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
