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
