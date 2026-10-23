"""Métricas para comparar un clasificador con las etiquetas humanas."""
from __future__ import annotations

from collections import Counter


def evaluate(gold, predicted, labels):
    """Accuracy, precisión/recall/F1 por clase, macro-F1 y matriz de confusión."""
    pairs = list(zip(gold, predicted))
    total = len(pairs)
    correct = sum(g == p for g, p in pairs)
    confusion = Counter(pairs)
    per_class = {}
    for label in labels:
        tp = confusion[(label, label)]
        fp = sum(confusion[(g, label)] for g in labels if g != label)
        fn = sum(confusion[(label, p)] for p in labels if p != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1, "n": tp + fn}
    present = [lab for lab in labels if per_class[lab]["n"] > 0]
    macro_f1 = sum(per_class[lab]["f1"] for lab in present) / len(present) if present else 0.0
    return {
        "n": total,
        "accuracy": correct / total if total else 0.0,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion": confusion,
    }


def format_report(result, labels):
    lines = [f"Filas evaluadas: {result['n']}", f"Accuracy: {result['accuracy']:.3f}", f"F1 macro: {result['macro_f1']:.3f}", ""]
    lines.append(f"{'clase':<15}{'n':>4}{'prec':>7}{'recall':>8}{'f1':>6}")
    for label in labels:
        c = result["per_class"][label]
        if c["n"] or any(result["confusion"][(g, label)] for g in labels):
            lines.append(f"{label:<15}{c['n']:>4}{c['precision']:>7.2f}{c['recall']:>8.2f}{c['f1']:>6.2f}")
    lines += ["", "Matriz de confusión (filas = humano, columnas = método):"]
    short = [lab[:5] for lab in labels]
    lines.append(" " * 15 + "".join(f"{s:>7}" for s in short))
    for g in labels:
        if any(result["confusion"][(g, p)] for p in labels):
            lines.append(f"{g:<15}" + "".join(f"{result['confusion'][(g, p)]:>7}" for p in labels))
    return "\n".join(lines)
