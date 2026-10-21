"""Lectura de ParlaMint-ES: une los metadatos (TSV) con el texto (.txt) de cada intervención."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from presencia.explore import field, find_metadata_files

# Comentarios del transcriptor entre dobles corchetes: [[Aplausos]], [[Rumores]]...
COMMENT_RE = re.compile(r"\[\[(.*?)\]\]", re.DOTALL)


def session_of(speech_id):
    """'ParlaMint-ES_2022-01-25-CD220125.u3' -> 'ParlaMint-ES_2022-01-25-CD220125'."""
    return speech_id.rsplit(".u", 1)[0]


def read_text_file(path):
    """Genera (id_intervención, texto) de un .txt: dos columnas separadas por tabulador."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if "\t" not in line:
                continue
            speech_id, _, text = line.partition("\t")
            yield speech_id, text


def index_text_files(root):
    """Asocia cada sesión con su .txt leyendo el ID de la primera intervención.

    No depende de cómo se llamen los archivos. Ignora los que no tienen
    el formato de dos columnas (p. ej. 00README.txt).
    """
    index = {}
    for path in sorted(Path(root).rglob("*.txt")):
        first = next(read_text_file(path), None)
        if first is not None:
            index[session_of(first[0])] = path
    return index


def iter_speeches(root):
    """Genera (fila_de_metadatos, texto) para cada intervención.

    Usa solo los TSV en inglés. El texto es None si no se encuentra.
    """
    texts = index_text_files(root)
    for meta_path in find_metadata_files(root):
        with open(meta_path, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        if not rows:
            continue
        txt_path = texts.get(session_of(field(rows[0], "ID")))
        speeches = dict(read_text_file(txt_path)) if txt_path else {}
        for row in rows:
            yield row, speeches.get(row.get("ID"))


def clean_comment(comment):
    """Normaliza espacios dentro de un comentario."""
    return " ".join(comment.split())


def analyze_text(text):
    """Devuelve (nº de palabras sin contar comentarios, lista de comentarios normalizados)."""
    comments = [clean_comment(c) for c in COMMENT_RE.findall(text)]
    words = len(COMMENT_RE.sub(" ", text).split())
    return words, comments


# Un turno de presidencia de esta longitud o menos entre dos turnos de la misma
# persona se considera una interrupción ("Silencio, por favor", "debe ir terminando").
MAX_INTERRUPTION_WORDS = 12


def turn_number(speech_id):
    """'S1.u12' -> 12; None si el ID no tiene ese formato."""
    try:
        return int(speech_id.rsplit(".u", 1)[1])
    except (IndexError, ValueError):
        return None


def word_count(text):
    """Palabras de un texto sin contar los comentarios del transcriptor."""
    return len(COMMENT_RE.sub(" ", text or "").split())


def continuation_ids(items):
    """IDs de las intervenciones que continúan la anterior de la misma persona.

    ``items`` son los pares (fila, texto) de una sesión. En el corpus, cuando la
    presidencia interrumpe con una frase breve, el discurso se parte en dos filas.
    Una intervención es continuación si entre ella y la anterior de la misma
    persona solo hay un turno de presidencia de MAX_INTERRUPTION_WORDS palabras o menos.
    """
    ordered = sorted(items, key=lambda item: turn_number(field(item[0], "ID")) or 0)
    found = set()
    for i in range(2, len(ordered)):
        (prev, _), (mid, mid_text), (row, _) = ordered[i - 2], ordered[i - 1], ordered[i]
        speaker = field(row, "Speaker_ID")
        if (
            field(mid, "Speaker_role") == "Chairperson"
            and word_count(mid_text) <= MAX_INTERRUPTION_WORDS
            and field(prev, "Speaker_role") != "Chairperson"
            and field(row, "Speaker_role") != "Chairperson"
            and speaker not in ("-", "?")
            and field(prev, "Speaker_ID") == speaker
        ):
            found.add(row["ID"])
    return found
