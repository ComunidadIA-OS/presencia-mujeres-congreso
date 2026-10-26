#!/usr/bin/env python3
"""Acuerdo entre anotadoras (kappa de Cohen) y confirmación del método híbrido.

Uso (desde la raíz del repositorio):
    # 1) Solo el acuerdo entre anotadoras (no usa la API ni recorre el corpus)
    python src/presencia/agreement.py data/annotated/anotadora2.csv --solo-kappa

    # 2) Acuerdo + confirmación del híbrido en las filas nuevas, con error por género
    python src/presencia/agreement.py data/annotated/anotadora2.csv --modelo Qwen3.5-397B-A17B

El archivo de la segunda anotadora mezcla, sin saber cuáles son cuáles:
  - filas que ya anotó la primera anotadora (``--referencia``): sirven para el kappa;
  - filas nuevas: sirven para confirmar el método en datos que no se vieron al diseñarlo.

Las filas marcadas como continuación (``otra`` + «continuación» en notas) se excluyen.
El modelo nunca recibe género, nombre ni grupo: el género se une después por el ID,
solo para medir el error por género.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):  # ejecución directa: python src/presencia/agreement.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from presencia.annotated import LABELS, is_continuation, load_rows, split_rows, validate  # noqa: E402


# --------------------------------------------------------------------------- kappa

def cohen_kappa(a, b):
    """Kappa de Cohen entre dos listas de etiquetas de la misma longitud."""
    if len(a) != len(b) or not a:
        raise ValueError("Las dos listas deben tener la misma longitud y no estar vacías")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if expected == 1:  # las dos usan una sola etiqueta y la misma: acuerdo trivial
        return 1.0
    return (observed - expected) / (1 - expected)


def interpret(kappa):
    """Escala orientativa de Landis y Koch (1977)."""
    for limit, text in ((0.0, "pobre"), (0.20, "leve"), (0.40, "aceptable"),
                        (0.60, "moderado"), (0.80, "sustancial")):
        if kappa <= limit:
            return text
    return "casi perfecto"


def agreement_report(pairs):
    """pairs: lista de (fila_ref, fila_nueva). Devuelve el texto del informe."""
    a = [r["etiqueta"].strip() for r, _ in pairs]
    b = [r["etiqueta"].strip() for _, r in pairs]
    n = len(pairs)
    kappa = cohen_kappa(a, b)
    lines = [
        f"Filas comunes: {n}",
        f"Acuerdo observado: {sum(x == y for x, y in zip(a, b))}/{n} ({sum(x == y for x, y in zip(a, b)) / n:.3f})",
        f"Kappa de Cohen: {kappa:.3f} ({interpret(kappa)}, escala de Landis y Koch)",
        "",
        "Por etiqueta (veces que la usa cada anotadora | coincidencias | kappa de esa etiqueta frente al resto):",
    ]
    for label in LABELS:
        na, nb = a.count(label), b.count(label)
        if na == nb == 0:
            continue
        both = sum(x == y == label for x, y in zip(a, b))
        binary_kappa = cohen_kappa([x == label for x in a], [y == label for y in b])
        lines.append(f"  {label:<14} anotadora1 {na:>2} | anotadora2 {nb:>2} | coinciden {both:>2} | kappa {binary_kappa:.2f}")
    disagreements = [(r, x, y) for (r, _), x, y in zip(pairs, a, b) if x != y]
    lines.append("")
    lines.append(f"Desacuerdos ({len(disagreements)}):")
    for r, x, y in disagreements:
        lines.append(f"  {r['ID'].split('_', 1)[-1]:<28} anotadora1={x:<14} anotadora2={y:<14} {r.get('inicio', '')[:60]}")
    if n < 50:
        lines.append("")
        lines.append(f"Cautela: con {n} filas el kappa tiene mucha incertidumbre; una fila lo mueve varias centésimas.")
    return "\n".join(lines)


# ------------------------------------------------------------- confirmación

def genders_for(ids, corpus):
    """Une el género por ID recorriendo los metadatos del corpus (solo para medir error por género)."""
    from presencia.corpus import iter_speeches
    from presencia.explore import field

    wanted, found = set(ids), {}
    for row, _ in iter_speeches(Path(corpus)):
        speech_id = field(row, "ID")
        if speech_id in wanted:
            found[speech_id] = field(row, "Speaker_gender")
            if len(found) == len(wanted):
                break
    return found


def errors_by_gender(gold, predicted, genders):
    lines = []
    for g, name in (("F", "Mujeres"), ("M", "Hombres")):
        idx = [i for i, x in enumerate(genders) if x == g]
        if not idx:
            continue
        errors = sum(gold[i] != predicted[i] for i in idx)
        lines.append(f"  {name:<8} n={len(idx):>2}  errores {errors:>2}  accuracy {1 - errors / len(idx):.3f}")
    return lines


def confirm(new_rows, reference_rows, args):
    from presencia import baseline, llm
    from presencia.evaluation import evaluate, format_report

    if not hasattr(baseline, "structural_label"):
        print("Falta el código del método híbrido (baseline.structural_label).")
        print("Trae los últimos cambios de GitHub (git pull) y vuelve a lanzarlo. El kappa de arriba es válido.")
        return 1

    gold = [r["etiqueta"].strip() for r in new_rows]
    rows = [{**r, "etiqueta": "", "notas": ""} for r in new_rows]  # el modelo no ve la etiqueta humana
    calibration, _ = split_rows(reference_rows)
    examples = [r for r in calibration if r["etiqueta"].strip() in LABELS and not is_continuation(r)]

    print(f"Uniendo el género por ID desde {args.corpus} ...")
    gender_of = genders_for([r["ID"] for r in rows], args.corpus)
    genders = [gender_of.get(r["ID"], "?") for r in rows]
    missing = genders.count("?")
    if missing:
        print(f"Aviso: {missing} filas sin género encontrado en el corpus.")

    methods = {"reglas": [baseline.classify(r) for r in rows]}
    for name in args.modelo:
        cfg = llm.settings(name)
        cache = Path(args.cache) / f"{name.replace('/', '_')}.jsonl"
        cache.parent.mkdir(parents=True, exist_ok=True)
        print(f"\nHÍBRIDO estructura + {name} ({len(examples)} ejemplos de calibración, caché {cache})")
        methods[f"{name} + estructura"] = llm.classify_rows(
            cfg, rows, examples, cache_path=cache,
            decide=baseline.structural_label, workers=args.paralelo,
        )

    for name, predicted in methods.items():
        print(f"\nMÉTODO {name}")
        print(format_report(evaluate(gold, predicted, LABELS), LABELS))

    print("\nRESUMEN DE LA CONFIRMACIÓN (filas nuevas, etiquetas de la anotadora 2)")
    for name, predicted in methods.items():
        res = evaluate(gold, predicted, LABELS)
        print(f"{name:<40} accuracy {res['accuracy']:.3f}  F1 macro {res['macro_f1']:.3f}")
        for line in errors_by_gender(gold, predicted, genders):
            print(line)

    if args.errores:
        for name, predicted in methods.items():
            print(f"\nErrores de {name}:")
            for r, g, p, sex in zip(rows, gold, predicted, genders):
                if g != p:
                    print(f"  {r['ID'].split('_', 1)[-1]:<28} humana={g:<14} método={p:<14} {r.get('inicio', '')[:60]}")
    print(f"\nCautela: {len(rows)} filas; por género, unas {len(rows) // 2}. Los resultados son orientativos.")
    return 0


# ------------------------------------------------------------------- main

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("anotadora2", help="CSV anotado por la segunda persona, p. ej. data/annotated/anotadora2.csv")
    parser.add_argument("--referencia", default="data/annotated/muestra_anotada.csv",
                        help="CSV de la primera anotadora (por defecto la muestra de 120)")
    parser.add_argument("--solo-kappa", action="store_true", help="Calcula solo el acuerdo, sin modelo ni corpus")
    parser.add_argument("--modelo", action="append", default=[],
                        help="Modelo para el híbrido (se puede repetir); por defecto Qwen3.5-397B-A17B")
    parser.add_argument("--corpus", default="data/raw/ParlaMint-ES.txt", help="Carpeta del corpus, para unir el género")
    parser.add_argument("--cache", default="data/processed/llm/confirmacion",
                        help="Caché propia de la confirmación (separada de la de la evaluación)")
    parser.add_argument("--paralelo", type=int, default=1, help="Peticiones simultáneas a la API")
    parser.add_argument("--errores", action="store_true", help="Lista las filas donde falla cada método")
    args = parser.parse_args(argv)

    second = load_rows(args.anotadora2)
    reference = load_rows(args.referencia)
    problems = validate(second)
    if problems:
        print("Hay etiquetas vacías o mal escritas en el archivo de la anotadora 2:")
        print("\n".join(problems))
        return 1

    ref_by_id = {r["ID"]: r for r in reference}
    second = [r for r in second if not is_continuation(r)]
    common = [(ref_by_id[r["ID"]], r) for r in second if r["ID"] in ref_by_id and not is_continuation(ref_by_id[r["ID"]])]
    new_rows = [r for r in second if r["ID"] not in ref_by_id]
    print(f"Anotadora 2: {len(second)} filas válidas | comunes con la referencia: {len(common)} | nuevas: {len(new_rows)}\n")

    print("=" * 70)
    print("ACUERDO ENTRE ANOTADORAS")
    print("=" * 70)
    if common:
        print(agreement_report(common))
    else:
        print("No hay filas comunes con la referencia: no se puede calcular el kappa.")

    if args.solo_kappa:
        return 0
    if not new_rows:
        print("\nNo hay filas nuevas: no hay nada que confirmar.")
        return 0
    args.modelo = args.modelo or ["Qwen3.5-397B-A17B"]
    print("\n" + "=" * 70)
    print("CONFIRMACIÓN DEL MÉTODO EN FILAS NUEVAS")
    print("=" * 70)
    return confirm(new_rows, reference, args)


if __name__ == "__main__":
    sys.exit(main())
