"""Método base: reglas de palabras clave y estructura (sin IA).

Es el listón que debe superar el modelo de lenguaje. Usa solo lo que ve la persona
que anota: el turno anterior (``previo_1``), la ``secuencia`` y el inicio del texto.
"""
from __future__ import annotations

import re

PROCEDURAL_RE = re.compile(
    r"art[ií]culo\s+\d+|alusion|cuesti[oó]n de orden|\bjuro\b|\bprometo\b|"
    r"resultado de la votaci[oó]n|votos emitidos|escrutinio|turno de palabra",
    re.I,
)
QUESTION_RE = re.compile(r"\bpregunta\b|interpelaci[oó]n", re.I)
INITIATIVE_RE = re.compile(
    r"proposici[oó]n|moci[oó]n|proyecto de ley|real decreto|enmienda|comisi[oó]n de investigaci[oó]n|"
    r"convalidaci[oó]n|dictamen",
    re.I,
)
GROUP_TURN_RE = re.compile(r"por el grupo|grupo parlamentario|tiene la palabra|a continuaci[oó]n", re.I)
GOVERNMENT_RE = re.compile(r"ministr[oa]|vicepresident[ea]|presidente del gobierno|secretari[oa] de estado", re.I)
SHORT_PROCEDURAL_WORDS = 15


def people(secuencia):
    """Separa ``secuencia`` en (letras de personas anteriores, letra del turno actual).

    Acepta la flecha ``→`` o el ``?`` en que la convierte Excel al guardar en ANSI.
    """
    tokens = re.findall(r"([A-Z])\((\d+)\)", secuencia)
    if not tokens:
        return [], None
    *previous, current = tokens
    return [t[0] for t in previous if t[0] != "P"], current[0]


def classify(row):
    """Etiqueta una fila de la muestra (diccionario con previo_1, secuencia, inicio, palabras)."""
    previous, current = people(row["secuencia"])
    context = row["previo_1"]
    start = row["inicio"]
    words = int(row["palabras"] or 0)

    if current is not None and current in previous:
        return "replica"
    if PROCEDURAL_RE.search(start[:300]) or words <= SHORT_PROCEDURAL_WORDS:
        return "procedimental"
    if QUESTION_RE.search(context) and "diputad" in context.lower():
        return "pregunta"
    if INITIATIVE_RE.search(context) and not GROUP_TURN_RE.search(context[-120:]):
        return "defensa"
    if GOVERNMENT_RE.search(context[-160:]) and not GROUP_TURN_RE.search(context[-160:]):
        return "respuesta"
    return "posicion"
