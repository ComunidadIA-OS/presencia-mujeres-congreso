#!/usr/bin/env python3
"""Evalúa un método de clasificación contra la muestra anotada a mano.

Uso (desde la raíz del repositorio):
    python src/presencia/evaluate.py data/annotated/muestra_anotada.csv
    python src/presencia/evaluate.py data/annotated/muestra_anotada.csv --modelo Qwen3.5-397B-A17B --hibrido
    python src/presencia/evaluate.py data/annotated/muestra_anotada.csv --modelo Qwen3.5-9B --sin-razonamiento --paralelo 4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from presencia import baseline, llm  # noqa: E402
from presencia.annotated import LABELS, is_continuation, load_rows, split_rows, validate  # noqa: E402
from presencia.evaluation import evaluate, format_report  # noqa: E402


def cache_name(model, cfg):
    """Archivo de caché por modelo; las respuestas sin razonamiento se guardan aparte."""
    suffix = "" if cfg.get("thinking", True) else "__sin-razonamiento"
    return f"{model.replace('/', '_')}{suffix}.jsonl"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("muestra", help="CSV anotado, p. ej. data/annotated/muestra_anotada.csv")
    parser.add_argument("--errores", action="store_true", help="Lista las filas donde el método falla")
    parser.add_argument("--modelo", action="append", default=[],
                        help="Modelo de OVHcloud a evaluar (se puede repetir), p. ej. --modelo gpt-oss-120b")
    parser.add_argument("--cache", default="data/processed/llm", help="Carpeta donde se guardan las respuestas del modelo")
    parser.add_argument("--hibrido", action="store_true",
                        help="Añade el método híbrido: réplica por estructura de turnos y el resto con el modelo")
    parser.add_argument("--sin-razonamiento", action="store_true",
                        help="Pide al modelo que responda sin razonar antes (Qwen3.x): mucho más rápido")
    parser.add_argument("--paralelo", type=int, default=1, help="Peticiones simultáneas al modelo (por defecto 1)")
    parser.add_argument("--timeout", type=float, help="Segundos máximos por petición (por defecto 120)")
    args = parser.parse_args(argv)

    rows = load_rows(args.muestra)
    problems = validate(rows)
    if problems:
        print("\n".join(problems))
        return 1
    calibration, evaluation = split_rows(rows)
    print(f"Muestra: {len(rows)} filas | calibración: {len(calibration)} | evaluación: {len(evaluation)}\n")

    gold = [r["etiqueta"].strip() for r in evaluation]
    predicted = [baseline.classify(r) for r in evaluation]
    print("MÉTODO BASE (reglas)")
    print(format_report(evaluate(gold, predicted, LABELS), LABELS))

    methods = {"reglas": predicted}
    examples = [r for r in calibration if r["etiqueta"].strip() in LABELS and not is_continuation(r)]
    for name in args.modelo:
        cfg = llm.settings(name)
        if args.sin_razonamiento:
            cfg["thinking"] = False
        if args.timeout:
            cfg["timeout"] = args.timeout
        cache = Path(args.cache) / cache_name(name, cfg)
        print(f"\nMODELO {name} ({len(examples)} ejemplos de calibración)")
        methods[name] = llm.classify_rows(cfg, evaluation, examples, cache_path=cache, workers=args.paralelo)
        print(format_report(evaluate(gold, methods[name], LABELS), LABELS))
        if args.hibrido:
            hybrid = [baseline.structural_label(r) or p for r, p in zip(evaluation, methods[name])]
            methods[f"{name} + estructura"] = hybrid
            print(f"\nHÍBRIDO {name} + estructura (réplica decidida por la secuencia de turnos)")
            print(format_report(evaluate(gold, hybrid, LABELS), LABELS))

    if len(methods) > 1:
        print("\nRESUMEN")
        for name, pred in methods.items():
            res = evaluate(gold, pred, LABELS)
            print(f"{name:<45} accuracy {res['accuracy']:.3f}  F1 macro {res['macro_f1']:.3f}")

    if args.errores:
        for name, pred in methods.items():
            print(f"\nErrores de {name}:")
            for r, g, p in zip(evaluation, gold, pred):
                if g != p:
                    print(f"{r['ID'].split('_', 1)[-1]:<28} humano={g:<14} método={p:<14} {r['inicio'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
