import csv

from presencia.corpus import analyze_text, index_text_files, iter_speeches
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

    with open(out / "comentarios.csv", encoding="utf-8", newline="") as fh:
        comments = {r["comentario"]: r for r in csv.DictReader(fh)}
    assert comments["Aplausos"]["en_oradores"] == "1"
    assert "sin texto asociado: 1" in capsys.readouterr().out
