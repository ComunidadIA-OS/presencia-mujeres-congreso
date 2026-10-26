#!/usr/bin/env python3
"""Clasifica el rol de una muestra grande de intervenciones con el método híbrido.

Uso (desde la raíz del repositorio):
    python src/presencia/classify.py data/raw/ParlaMint-ES.txt --estimar
    python src/presencia/classify.py data/raw/ParlaMint-ES.txt --modelo Qwen3.5-397B-A17B --n 1500 --paralelo 4

Método híbrido (el mejor en la evaluación): si la persona ya había hablado en el mismo
intercambio, es ``replica`` (estructura de turnos, sin modelo); el resto lo decide el modelo
con los ejemplos de calibración de la muestra anotada.

Selección: n intervenciones de mujeres y n de hombres (rol Regular, sin continuaciones) al azar,
sin repetir las de la muestra anotada. El modelo NO recibe género, nombre ni grupo: solo el
contexto de la intervención. Los metadatos se unen después por el ID.

Escribe data/processed/roles.csv: una fila por intervención con su rol, cómo se decidió y un
``peso`` (intervenciones de ese género en el corpus / en la muestra) para estimar proporciones
del corpus completo. Las respuestas del modelo quedan en caché: si se corta, se reanuda.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from itertools import groupby
from pathlib import Path

if __package__ in (None, ""):  # ejecución directa: python src/presencia/classify.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from presencia import baseline, llm  # noqa: E402
from presencia.annotated import LABELS, is_continuation, load_rows, split_rows  # noqa: E402
from presencia.corpus import continuation_ids, iter_speeches, sequence_context, turns_of  # noqa: E402
from presencia.explore import field  # noqa: E402
from presencia.sample import build_record, session_key  # noqa: E402

META = ["Date", "Speaker_gender", "Speaker_party", "Party_status", "Speaker_minister", "Topic"]
OUT_FIELDS = ["ID"] + META + ["palabras", "rol", "metodo", "peso"]


def candidates_by_gender(root, exclude=()):
    """{'F': [IDs], 'M': [IDs]} de intervenciones de diputados/as sin continuaciones."""
    found = {"F": [], "M": []}
    for _, group in groupby(iter_speeches(root), key=session_key):
        items = list(group)
        continuations = continuation_ids(items)
        for row, _ in items:
            gender = field(row, "Speaker_gender")
            speech_id = field(row, "ID")
            if (field(row, "Speaker_role") == "Regular" and gender in found
                    and speech_id not in continuations and speech_id not in exclude):
                found[gender].append(speech_id)
    return found


def choose(candidates, n, seed):
    """Muestra estratificada por género. n <= 0: todas."""
    rng = random.Random(seed)
    chosen = set()
    for gender, ids in candidates.items():
        ids = sorted(ids)
        chosen.update(ids if n <= 0 or n >= len(ids) else rng.sample(ids, n))
    return chosen


def build_rows(root, chosen):
    """Filas con el mismo contexto que vio la anotadora (``build_record``) y los metadatos aparte."""
    rows, meta = [], {}
    for _, group in groupby(iter_speeches(root), key=session_key):
        items = list(group)
        turns = turns_of(items)
        position = {turn[0]: i for i, turn in enumerate(turns)}
        by_id = {r.get("ID"): t for r, t in items}
        for row, text in items:
            if row.get("ID") in chosen:
                rows.append(build_record(row, text, by_id, sequence_context(turns, position[row["ID"]])))
                meta[row["ID"]] = {k: field(row, k) for k in META}
    return rows, meta


def weights(candidates, chosen):
    """Peso por género = intervenciones en el corpus / intervenciones en la muestra."""
    out = {}
    for gender, ids in candidates.items():
        in_sample = sum(1 for i in ids if i in chosen)
        out[gender] = len(ids) / in_sample if in_sample else 0.0
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("carpeta", help="Carpeta con los TSV y los .txt, p. ej. data/raw/ParlaMint-ES.txt")
    parser.add_argument("--modelo", default="Qwen3.5-397B-A17B", help="Modelo de OVHcloud (por defecto Qwen3.5-397B-A17B)")
    parser.add_argument("--n", type=int, default=1500, help="Intervenciones por género (0 = todas)")
    parser.add_argument("--semilla", type=int, default=2026)
    parser.add_argument("--anotada", default="data/annotated/muestra_anotada.csv",
                        help="Muestra anotada: aporta los ejemplos y sus filas se excluyen")
    parser.add_argument("--paralelo", type=int, default=4, help="Peticiones simultáneas (por defecto 4)")
    parser.add_argument("--sin-razonamiento", action="store_true", help="Respuesta directa, sin razonar (Qwen3.x)")
    parser.add_argument("--timeout", type=float, help="Segundos máximos por petición")
    parser.add_argument("--estimar", action="store_true", help="Solo cuenta filas y llamadas; no usa el modelo")
    parser.add_argument("--cache", default="data/processed/llm")
    parser.add_argument("--salida", default="data/processed/roles.csv")
    args = parser.parse_args(argv)

    root = Path(args.carpeta)
    if not root.is_dir():
        print(f"La carpeta no existe: {root.resolve()}")
        return 2

    annotated = load_rows(args.anotada) if Path(args.anotada).is_file() else []
    calibration, _ = split_rows(annotated) if annotated else ([], [])
    examples = [r for r in calibration if r["etiqueta"].strip() in LABELS and not is_continuation(r)]
    exclude = {r["ID"] for r in annotated}

    candidates = candidates_by_gender(root, exclude)
    chosen = choose(candidates, args.n, args.semilla)
    rows, meta = build_rows(root, chosen)
    structural = {r["ID"]: baseline.structural_label(r) for r in rows}
    to_model = sum(1 for label in structural.values() if not label)
    print(f"Candidatas: mujeres {len(candidates['F'])}, hombres {len(candidates['M'])}")
    print(f"Muestra: {len(rows)} intervenciones (semilla {args.semilla}); "
          f"réplica por estructura: {len(rows) - to_model}; al modelo: {to_model}")

    cfg = llm.settings(args.modelo) if not args.estimar else {"thinking": not args.sin_razonamiento}
    if args.sin_razonamiento:
        cfg["thinking"] = False
    if args.timeout:
        cfg["timeout"] = args.timeout
    suffix = "" if cfg.get("thinking", True) else "__sin-razonamiento"
    cache = Path(args.cache) / f"{args.modelo.replace('/', '_')}{suffix}.jsonl"
    cached = llm.load_cache(cache)
    missing = sum(1 for r in rows if not structural[r["ID"]] and r["ID"] not in cached)
    print(f"Ya en caché: {to_model - missing}; llamadas pendientes: {missing}")
    if args.estimar:
        print("Con 4 peticiones simultáneas y ~5 s por respuesta: "
              f"~{missing * 5 / 4 / 60:.0f} min (mide tú el tiempo real con --n 20 antes de lanzar todo).")
        return 0

    start = time.time()
    labels = llm.classify_rows(cfg, rows, examples, cache_path=cache, workers=args.paralelo,
                               decide=baseline.structural_label)
    print(f"\nTiempo: {(time.time() - start) / 60:.1f} min")

    cached = llm.load_cache(cache)
    w = weights(candidates, chosen)
    out = Path(args.salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    failed = 0
    with open(out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS)
        writer.writeheader()
        for row, label in zip(rows, labels):
            if structural[row["ID"]]:
                method = "estructura"
            elif row["ID"] in cached:
                method = "modelo"
            else:
                method, label = "sin_respuesta", ""
                failed += 1
            writer.writerow({"ID": row["ID"], **meta[row["ID"]], "palabras": row["palabras"], "rol": label,
                             "metodo": method, "peso": f"{w[meta[row['ID']]['Speaker_gender']]:.4f}"})
    print(f"Escrito en {out.resolve()}")
    if failed:
        print(f"AVISO: {failed} filas sin respuesta. Vuelve a lanzar el mismo comando para completarlas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
