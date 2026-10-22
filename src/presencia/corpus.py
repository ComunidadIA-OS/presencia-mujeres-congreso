"""Lectura de ParlaMint-ES: une los metadatos (TSV) con el texto (.txt) de cada intervención."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from presencia.explore import field, find_metadata_files

# Comentarios del transcriptor entre dobles corchetes: [[Aplausos]], [[Rumores]]...
COMMENT_RE = re.compile(r"\[\[(.*?)\]\]", re.DOTALL)

# Un turno de presidencia de esta longitud o menos entre dos turnos de la misma
# persona se considera una interrupción ("Silencio, por favor", "debe ir terminando").
MAX_INTERRUPTION_WORDS = 12


def session_of(speech_id):
    """'ParlaMint-ES_2022-01-25-CD220125.u3' -> 'ParlaMint-ES_2022-01-25-CD220125'."""
    return speech_id.rsplit(".u", 1)[0]


def turn_number(speech_id):
    """'S1.u12' -> 12; None si el ID no tiene ese formato."""
    try:
        return int(speech_id.rsplit(".u", 1)[1])
    except (IndexError, ValueError):
        return None


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


def word_count(text):
    """Palabras de un texto sin contar los comentarios del transcriptor."""
    return len(COMMENT_RE.sub(" ", text or "").split())


def analyze_text(text):
    """Devuelve (nº de palabras sin contar comentarios, lista de comentarios normalizados)."""
    comments = [clean_comment(c) for c in COMMENT_RE.findall(text)]
    return word_count(text), comments


def turns_of(items):
    """Convierte los pares (fila, texto) de una sesión en turnos ordenados.

    Cada turno es una tupla (id, rol, persona, palabras).
    """
    ordered = sorted(items, key=lambda item: turn_number(field(item[0], "ID")) or 0)
    return [
        (row["ID"], field(row, "Speaker_role"), field(row, "Speaker_ID"), word_count(text))
        for row, text in ordered
    ]


def continuations_from_turns(turns):
    """IDs de los turnos que continúan el anterior de la misma persona.

    En el corpus, cuando la presidencia interrumpe con una frase breve, el discurso
    se parte en dos filas. Un turno es continuación si entre él y el anterior de la
    misma persona solo hay un turno de presidencia de MAX_INTERRUPTION_WORDS palabras o menos.
    """
    found = set()
    for i in range(2, len(turns)):
        (_, prev_role, prev_speaker, _), (_, mid_role, _, mid_words), (turn_id, role, speaker, _) = (
            turns[i - 2], turns[i - 1], turns[i],
        )
        if (
            mid_role == "Chairperson"
            and mid_words <= MAX_INTERRUPTION_WORDS
            and prev_role != "Chairperson"
            and role != "Chairperson"
            and speaker not in ("-", "?")
            and prev_speaker == speaker
        ):
            found.add(turn_id)
    return found


def continuation_ids(items):
    """IDs de las intervenciones que continúan la anterior de la misma persona (ver arriba)."""
    return continuations_from_turns(turns_of(items))


def sequence_context(turns, index, before=12):
    """Resume la estructura de los turnos anteriores a ``turns[index]``.

    Devuelve algo como ``P(2) A(18) P(2) B(68) → A(350)``: P es la presidencia, las
    letras son personas distintas dentro de esta ventana (no identifican a nadie) y el
    número son las palabras. Las interrupciones breves de la presidencia se omiten y
    las partes de una misma intervención se suman. Sirve para saber, por ejemplo, si
    una persona ya había intervenido antes en el mismo intercambio.
    """
    continuations = continuations_from_turns(turns)
    letters, tokens = {}, []
    for turn_id, role, speaker, words in turns[max(0, index - before): index + 1]:
        if role == "Chairperson":
            tokens.append(["P", words])
            continue
        label = "?" if speaker in ("-", "?") else letters.setdefault(speaker, chr(65 + len(letters)))
        if turn_id in continuations:
            if tokens and tokens[-1][0] == "P":
                tokens.pop()
            if tokens and tokens[-1][0] == label:
                tokens[-1][1] += words
                continue
        tokens.append([label, words])
    *previous, current = tokens
    parts = [f"{label}({words})" for label, words in previous]
    parts.append(f"→ {current[0]}({current[1]})")
    return " ".join(parts)
