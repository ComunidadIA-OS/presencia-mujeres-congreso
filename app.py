#!/usr/bin/env python3
"""Demo: presencia y protagonismo de las mujeres en el Congreso (ParlaMint-ES).

Uso (desde la raíz del repositorio):
    python app.py                 # en el Jupyter de OVHcloud: puerto 7860
    python app.py --compartir     # además, enlace público temporal de Gradio

Tres pantallas:
  1. ¿Quién protagoniza el debate?  Rol en el debate (IA) y posición (apertura, cierre) por género.
  2. Así decide el sistema.         Ejemplos reales de la muestra anotada: la secuencia de turnos,
                                     el rol, si lo decidió la regla o el modelo, y la etiqueta humana.
  3. ¿El sistema es justo?          Error por género de las reglas frente al método híbrido y
                                     acuerdo con las anotadoras.

Funciona sin conexión con el modelo: los resultados y los ejemplos salen de archivos ya calculados
(data/processed/ y la caché del modelo). Clasificar en directo es opcional y necesita OVH_AI_TOKEN.
Los nombres de personas se ocultan en los textos que se muestran.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sys
from pathlib import Path

import gradio as gr
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from presencia import baseline  # noqa: E402
from presencia.annotated import LABELS, is_continuation, load_rows, split_rows  # noqa: E402
from presencia.llm import parse_label  # noqa: E402

PROC = ROOT / "data" / "processed"
MODEL = "Qwen3.5-397B-A17B"

# Paleta de referencia validada (categórica, modo claro): ranuras 1 y 2. Sin rosa/azul por género.
COLOR_F, COLOR_M = "#2a78d6", "#eb6834"
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"

ROLES = {
    "defensa": "Defiende una iniciativa",
    "pregunta": "Pregunta al Gobierno",
    "respuesta": "Responde",
    "replica": "Réplica",
    "posicion": "Fija la posición del grupo",
    "procedimental": "Trámite",
    "otra": "Otra",
}
GRUPOS = {
    "todas": "Todas las intervenciones",
    "sin_ministros": "Diputadas y diputados (sin ministros)",
    "oposicion": "Oposición",
    "gobierno_y_socios": "Gobierno y socios",
    "ministros": "Miembros del Gobierno",
}


# ------------------------------------------------------------------ datos

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def roles_source():
    """Usa el resumen del corpus completo si existe; si no, el de la muestra estratificada."""
    full = PROC / "roles_resumen_completo.csv"
    if full.is_file():
        return full, "corpus completo de diputadas y diputados"
    return PROC / "roles_resumen.csv", "muestra estratificada de 3.000 intervenciones (1.500 por género, con pesos)"


def interval(text):
    try:
        lo, hi = (float(x) for x in str(text).split("-"))
        return lo, hi
    except ValueError:
        return None


NAME_RE = re.compile(
    r"\b((?i:señora|señor|señoría|don|doña|ministra|ministro|diputada|diputado|vicepresidenta|vicepresidente|"
    r"presidenta|presidente))(\s+(?:(?:de|del|la|las|los|y|i)\s+)*[A-ZÁÉÍÓÚÑ][\wáéíóúñü\-]+)+",
)


def anonimizar(texto):
    """Oculta nombres propios tras tratamientos y cargos («señora García» -> «señora [nombre]»)."""
    return NAME_RE.sub(lambda m: f"{m.group(1)} [nombre]", texto or "")


def load_model_cache():
    cache = {}
    path = PROC / "llm" / f"{MODEL}.jsonl"
    if path.is_file():
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.endswith("\n"):
                    d = json.loads(line)
                    cache[d["ID"]] = d["raw"]
    return cache


ANNOTATED = ROOT / "data" / "annotated" / "muestra_anotada.csv"
CALIBRATION, EVALUATION = split_rows(load_rows(ANNOTATED)) if ANNOTATED.is_file() else ([], [])
EVALUATION = [r for r in EVALUATION if not is_continuation(r)]
CACHE = load_model_cache()


# ------------------------------------------------------------ pantalla 1

def style(ax, fig):
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=10, length=0)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def legend(ax):
    handles = [Patch(color=COLOR_F, label="Mujeres"), Patch(color=COLOR_M, label="Hombres")]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False,
              fontsize=10, labelcolor=INK, borderaxespad=0.2)


def roles_figure(grupo):
    path, _ = roles_source()
    rows = [r for r in read_csv(path) if r["grupo"] == grupo and r["rol"] in ROLES]
    order = [k for k in ROLES if any(r["rol"] == k for r in rows)]
    rows = sorted(rows, key=lambda r: order.index(r["rol"]))[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.6 * len(rows) + 1.4))
    style(ax, fig)
    h = 0.36
    for i, r in enumerate(rows):
        for offset, sex, color in ((h / 2 + 0.02, "F", COLOR_F), (-h / 2 - 0.02, "M", COLOR_M)):
            value = float(r[f"pct_{sex}"])
            ax.barh(i + offset, value, height=h, color=color, label=None)
            ci = interval(r[f"ic_{sex}"])
            if ci:
                ax.plot(ci, [i + offset] * 2, color=INK, linewidth=1)
            ax.text(value + 0.6 if not ci else ci[1] + 0.6, i + offset, f"{value:.1f} %",
                    va="center", fontsize=9, color=INK_2)
    ax.set_yticks(range(len(rows)), [ROLES[r["rol"]] for r in rows], color=INK)
    ax.set_xlabel("% de las intervenciones de cada género (con intervalo del 95 %)", color=INK_2, fontsize=9)
    legend(ax)
    fig.tight_layout()
    return fig


def roles_table(grupo):
    path, _ = roles_source()
    out = []
    for r in read_csv(path):
        if r["grupo"] == grupo and r["rol"] in ROLES:
            out.append([ROLES[r["rol"]], f"{float(r['pct_F']):.1f} %", f"{float(r['pct_M']):.1f} %",
                        f"{float(r['cuota_mujeres']):.1f} %", f"{float(r['razon']):.2f}"])
    return out


def posicion_rows():
    path = PROC / "posicion_resumen.csv"
    if not path.is_file():
        return []
    out = []
    names = {"R1_apertura": "Abre la sección", "R2_cierre": "Cierra la sección"}
    for r in read_csv(path):
        if r["metrica"] in names and r["grupo"] in ("todas", "sin_ministros"):
            out.append([names[r["metrica"]], GRUPOS.get(r["grupo"], r["grupo"]),
                        f"{float(r['pct_mujeres']):.1f} % [{float(r['ic95_inf']):.1f}–{float(r['ic95_sup']):.1f}]",
                        f"{float(r['referencia_pct']):.1f} %", r["razon"]])
    return out


def update_roles(grupo_label):
    grupo = {v: k for k, v in GRUPOS.items()}[grupo_label]
    return roles_figure(grupo), roles_table(grupo)


# ------------------------------------------------------------ pantalla 2

def decide(row):
    """Devuelve (rol, quién decide, motivo) con el método híbrido, sin llamar a la API."""
    structural = baseline.structural_label(row)
    if structural:
        return structural, "Regla estructural (sin modelo)", "La persona ya había hablado en este intercambio: su letra se repite en la secuencia."
    raw = CACHE.get(row["ID"])
    if raw is None:
        return None, "Modelo de lenguaje", "Esta intervención no está en la caché del modelo."
    return parse_label(raw), f"Modelo de lenguaje abierto ({MODEL})", "El modelo ha leído el turno anterior de la presidencia, la secuencia y el inicio del texto. No ha recibido nombre, grupo ni género."


def show_example(index):
    if not EVALUATION:
        return "No se encuentra la muestra anotada.", "", "", "", 0
    index = int(index) % len(EVALUATION)
    row = EVALUATION[index]
    rol, quien, motivo = decide(row)
    humano = row["etiqueta"].strip()
    acierto = "✅ Coincide con la etiqueta humana" if rol == humano else "⚠️ No coincide con la etiqueta humana"
    contexto = (f"**Turno anterior de la presidencia:** {anonimizar(row['previo_1'])}\n\n"
                f"**Secuencia de turnos:** `{row['secuencia']}`  \n"
                "*(P = presidencia; cada letra es una persona distinta; la flecha marca el turno a clasificar; "
                "los números son palabras)*")
    texto = anonimizar(row["inicio"])
    resultado = (f"### {ROLES.get(rol, rol or '—')}\n\n**Quién lo decide:** {quien}  \n**Por qué:** {motivo}\n\n"
                 f"**Etiqueta de la anotadora (a ciegas):** {ROLES.get(humano, humano)}  \n{acierto}")
    return contexto, texto, resultado, f"Ejemplo {index + 1} de {len(EVALUATION)}", index


def random_example():
    return show_example(random.randrange(max(len(EVALUATION), 1)))


def next_example(index):
    return show_example(int(index) + 1)


def live_classify(index):
    """Opcional: pide la etiqueta al modelo en directo (necesita OVH_AI_TOKEN y conexión)."""
    try:
        from presencia import llm
        row = EVALUATION[int(index) % len(EVALUATION)]
        if baseline.structural_label(row):
            return "Este turno lo decide la regla estructural: no hace falta llamar al modelo."
        cfg = llm.settings(MODEL)
        examples = [r for r in CALIBRATION if r["etiqueta"].strip() in LABELS and not is_continuation(r)]
        label = parse_label(llm.chat(cfg, llm.build_messages(row, examples)))
        return f"Respuesta del modelo en directo: **{ROLES.get(label, label)}**"
    except SystemExit as exc:
        return f"No se puede llamar al modelo: {exc}"
    except Exception as exc:  # la demo no debe caerse si la API no responde
        return f"El modelo no responde ahora mismo ({type(exc).__name__}). La demo sigue funcionando con los resultados guardados."


# ------------------------------------------------------------ pantalla 3

# Cifras de docs/05-evaluacion.md y docs/06-acuerdo-y-confirmacion.md
EVALUACION = [
    ["Evaluación (102 filas, anotadora 1)", "Reglas (sin IA)", "0,873", "0,683", "9 errores (acc. 0,83)", "4 errores (acc. 0,92)"],
    ["Evaluación (102 filas, anotadora 1)", "Híbrido (regla + modelo)", "0,922", "0,888", "5 errores (acc. 0,90)", "3 errores (acc. 0,94)"],
    ["Confirmación (30 filas nuevas, anotadora 2)", "Reglas (sin IA)", "0,867", "0,550", "3 errores (acc. 0,80)", "1 error (acc. 0,93)"],
    ["Confirmación (30 filas nuevas, anotadora 2)", "Híbrido (regla + modelo)", "0,867", "0,694", "2 errores (acc. 0,87)", "2 errores (acc. 0,87)"],
]
ACUERDO = [
    ["Anotadora 1 frente a anotadora 2", "26/34", "0,765"],
    ["Híbrido frente a anotadora 1", "29/34", "0,853"],
    ["Híbrido frente a anotadora 2", "27/34", "0,794"],
]


def fairness_figure():
    fig, ax = plt.subplots(figsize=(7, 2.8))
    style(ax, fig)
    labels = ["Reglas (sin IA)", "Híbrido (regla + modelo)"]
    women, men = [0.83, 0.90], [0.92, 0.94]
    y = [1, 0]
    h = 0.34
    for yy, w, m in zip(y, women, men):
        ax.barh(yy + h / 2 + 0.02, w * 100, height=h, color=COLOR_F)
        ax.barh(yy - h / 2 - 0.02, m * 100, height=h, color=COLOR_M)
        ax.text(w * 100 + 1, yy + h / 2 + 0.02, f"{w * 100:.0f} %", va="center", fontsize=9, color=INK_2)
        ax.text(m * 100 + 1, yy - h / 2 - 0.02, f"{m * 100:.0f} %", va="center", fontsize=9, color=INK_2)
    ax.set_yticks(y, labels, color=INK)
    ax.set_xlim(0, 105)
    ax.set_xlabel("Acierto con intervenciones de cada género (evaluación, 102 filas)", color=INK_2, fontsize=9)
    legend(ax)
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------ interfaz

def build():
    _, source_label = roles_source()
    with gr.Blocks(title="Presencia y protagonismo de las mujeres en el Congreso") as demo:
        gr.Markdown(
            "# Presencia y protagonismo de las mujeres en el Congreso\n"
            "Debates del Pleno del Congreso de los Diputados, 2015–2023 (ParlaMint-ES 5.0, CC BY 4.0). "
            "Resultados **agregados**: el sistema no evalúa a personas concretas."
        )
        with gr.Tab("1. ¿Quién protagoniza el debate?"):
            gr.Markdown(
                "Las mujeres hacen el **37 %** de las intervenciones. Cuando intervienen, "
                "**¿qué papel cumplen?** El rol de cada intervención lo clasifica el sistema de IA.  \n"
                f"*Datos: {source_label}.*"
            )
            grupo = gr.Dropdown(list(GRUPOS.values()), value=GRUPOS["sin_ministros"], label="Grupo")
            plot = gr.Plot(roles_figure("sin_ministros"))
            table = gr.Dataframe(
                roles_table("sin_ministros"),
                headers=["Rol", "Mujeres", "Hombres", "Cuota de mujeres en el rol", "Razón (1 = proporcional)"],
                interactive=False,
            )
            grupo.change(update_roles, grupo, [plot, table])
            gr.Markdown(
                "### ¿Abren y cierran los debates?\n"
                "Proporción de secciones del orden del día que abre o cierra una mujer, frente a su peso en esas "
                "secciones (todo el corpus, sin IA)."
            )
            gr.Dataframe(
                posicion_rows(),
                headers=["Métrica", "Grupo", "Mujeres [IC 95 %]", "Referencia", "Razón"],
                interactive=False,
            )
            gr.Markdown(
                "**Lectura:** la brecha está en **cuánto** intervienen las mujeres, no en qué papel cumplen ni en "
                "qué momento hablan. *Más tiempo de palabra no implica más influencia.*"
            )

        with gr.Tab("2. Así decide el sistema"):
            gr.Markdown(
                "Intervenciones reales de la muestra anotada a mano y a ciegas. El **método híbrido** decide las "
                "réplicas con una regla explicable y el resto con un modelo de lenguaje **abierto**. "
                "Los nombres de personas se ocultan."
            )
            index = gr.Number(value=0, visible=False, precision=0)
            counter = gr.Markdown()
            with gr.Row():
                with gr.Column(scale=3):
                    contexto = gr.Markdown()
                    texto = gr.Textbox(label="Inicio de la intervención", lines=8, interactive=False)
                with gr.Column(scale=2):
                    resultado = gr.Markdown()
            with gr.Row():
                btn_next = gr.Button("Siguiente ejemplo")
                btn_rand = gr.Button("Ejemplo al azar")
                btn_live = gr.Button("Preguntar al modelo en directo (opcional)")
            live = gr.Markdown()
            outputs = [contexto, texto, resultado, counter, index]
            btn_next.click(next_example, index, outputs)
            btn_rand.click(random_example, None, outputs)
            btn_live.click(live_classify, index, live)
            demo.load(lambda: show_example(0), None, outputs)

        with gr.Tab("3. ¿El sistema es justo?"):
            gr.Markdown(
                "No basta con acertar en general: medimos **cuánto se equivoca el sistema con las intervenciones "
                "de mujeres y de hombres**. Un sistema solo de reglas habría infravalorado el protagonismo de las "
                "mujeres."
            )
            gr.Plot(fairness_figure())
            gr.Dataframe(
                EVALUACION,
                headers=["Conjunto", "Método", "Accuracy", "F1 macro", "Mujeres", "Hombres"],
                interactive=False,
            )
            gr.Markdown("### ¿Está al nivel de una persona experta?")
            gr.Dataframe(ACUERDO, headers=["Comparación (34 filas comunes)", "Coincidencias", "Acuerdo"],
                         interactive=False)
            gr.Markdown(
                "El sistema coincide con cada anotadora tanto o más de lo que ellas coinciden entre sí. "
                "Detalles y cautelas: `docs/05-evaluacion.md` y `docs/06-acuerdo-y-confirmacion.md`."
            )
    return demo


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--puerto", type=int, default=7860)
    parser.add_argument("--compartir", action="store_true", help="Crea un enlace público temporal de Gradio")
    args = parser.parse_args(argv)
    if "NOTEBOOK_ID" in os.environ and "NOTEBOOK_HOST" in os.environ:
        print(f"URL de la demo: https://{os.environ['NOTEBOOK_ID']}-{args.puerto}.{os.environ['NOTEBOOK_HOST']}")
    build().launch(server_name="0.0.0.0", server_port=args.puerto, share=args.compartir)


if __name__ == "__main__":
    main()
