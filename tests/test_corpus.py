import csv

from presencia.corpus import (
    analyze_text,
    continuation_ids,
    index_text_files,
    iter_speeches,
    sequence_context,
)
from presencia.export import main

HEADER = [
    "ID", "Date", "Speaker_role", "Speaker_gender", "Speaker_ID",
    "Speaker_minister", "Speaker_party", "Party_status", "Topic",
]


def write_tsv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(HEADER)
        writer.writerows(rows)


def make_corpus(root):
    year = root / "2022"
    year.mkdir()
    (root / "00README.txt").write_text("Plain-text corpus\nsin tabuladores\n", encoding="utf-8")
    (year / "s1.txt").write_text(
        "S1.u1\tMuy buenas tardes. Se abre la sesión.\n"
        "S1.u2\tGracias, presidenta. [[Aplausos]] Señorías, ñandú [[Rumores.-Aplausos]] fin.\n",
        encoding="utf-8",
    )
    english = [
        ["S1.u1", "2022-01-25", "Chairperson", "-", "-", "-", "-", "-", "Other"],
        ["S1.u2", "2022-01-25", "Regular", "F", "ana", "Minister", "PSOE", "Coalition", "Health"],
        ["S1.u3", "2022-01-25", "Regular", "M", "luis", "notMinister", "PP", "Opposition", "Health"],  # sin texto
    ]
    spanish = [["S1.u1", "2022-01-25", "Presidencia", "-", "-", "-", "-", "-", "Otros"]]
    write_tsv(year / "s1-meta-en.tsv", english)
    write_tsv(year / "s1-meta.tsv", spanish)  # versión en español: debe ignorarse


def test_analyze_text_ignores_comments_in_word_count():
    words, comments = analyze_text("Gracias, presidenta. [[Aplausos]] Señorías, ñandú [[Rumores.-Aplausos]] fin.")
    assert words == 5
    assert comments == ["Aplausos", "Rumores.-Aplausos"]


def _item(number, role, speaker, text):
    return {"ID": f"S1.u{number}", "Speaker_role": role, "Speaker_ID": speaker}, text


def test_continuation_ids():
    long_chair = " ".join(["palabra"] * 13)
    items = [
        _item(1, "Regular", "ana", "Primera parte."),
        _item(2, "Chairperson", "-", "Silencio, por favor."),
        _item(3, "Regular", "ana", "Sigue la misma intervención."),  # continuación
        _item(4, "Chairperson", "-", long_chair),
        _item(5, "Regular", "ana", "Otra intervención."),  # no: la presidencia habló más de 12 palabras
        _item(6, "Chairperson", "-", "Tiene la palabra."),
        _item(7, "Regular", "luis", "Otro orador."),  # no: persona distinta
    ]
    assert continuation_ids(items) == {"S1.u3"}
    assert continuation_ids(list(reversed(items))) == {"S1.u3"}  # no depende del orden de entrada


def test_sequence_context_merges_interruptions_and_labels_people():
    # id, rol, persona, palabras
    turns = [
        ("S1.u1", "Chairperson", "-", 2),
        ("S1.u2", "Regular", "ana", 104),
        ("S1.u3", "Chairperson", "-", 3),  # interrupción breve
        ("S1.u4", "Regular", "ana", 52),  # continuación de u2
        ("S1.u5", "Chairperson", "-", 3),
        ("S1.u6", "Regular", "ana", 98),  # continuación
        ("S1.u7", "Chairperson", "-", 6),
        ("S1.u8", "Regular", "luis", 220),
        ("S1.u9", "Chairperson", "-", 4),
        ("S1.u10", "Regular", "ana", 40),
    ]
    assert sequence_context(turns, 7) == "P(2) A(254) P(6) → B(220)"
    # La misma persona de antes vuelve a hablar: se reconoce por la letra repetida
    assert sequence_context(turns, 9) == "P(2) A(254) P(6) B(220) P(4) → A(40)"
    assert sequence_context(turns, 1) == "P(2) → A(104)"


def test_index_ignores_readme(tmp_path):
    make_corpus(tmp_path)
    assert set(index_text_files(tmp_path)) == {"S1"}


def test_iter_speeches_joins_text_and_ignores_spanish(tmp_path):
    make_corpus(tmp_path)
    speeches = list(iter_speeches(tmp_path))
    assert len(speeches) == 3
    assert speeches[0][1].startswith("Muy buenas tardes")
    assert speeches[2][1] is None


def test_export_writes_tables(tmp_path, capsys):
    make_corpus(tmp_path)
    out = tmp_path / "out"
    assert main([str(tmp_path), "--salida", str(out)]) == 0

    with open(out / "intervenciones.csv", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert [r["words"] for r in rows] == ["7", "5", ""]
    assert rows[1]["n_comments"] == "2"
    assert [r["continuation"] for r in rows] == ["0", "0", "0"]

    with open(out / "comentarios.csv", encoding="utf-8", newline="") as fh:
        comments = {r["comentario"]: r for r in csv.DictReader(fh)}
    assert comments["Aplausos"]["en_oradores"] == "1"
    assert "sin texto asociado: 1" in capsys.readouterr().out
