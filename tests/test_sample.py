import csv

from presencia.corpus import turn_number
from presencia.sample import excerpt, main

HEADER = [
    "ID", "Date", "Speaker_role", "Speaker_gender", "Speaker_ID",
    "Speaker_minister", "Speaker_party", "Party_status", "Topic",
]
EXPECTED = {f"S1.u{i}": f"Texto del turno {i}. fin {i}." for i in range(1, 9)}


def make_corpus(root, speakers=None):
    """Sesión de 8 turnos: impares = presidencia, pares = oradores (u2 y u6 mujeres, u4 y u8 hombres).

    ``speakers`` permite forzar el ID de orador de un turno, p. ej. {4: "p2"}.
    """
    speakers = speakers or {}
    year = root / "2022"
    year.mkdir()
    lines, rows = [], []
    for i in range(1, 9):
        is_chair = i % 2 == 1
        role = "Chairperson" if is_chair else "Regular"
        gender = "-" if is_chair else ("F" if i in (2, 6) else "M")
        speaker = "-" if is_chair else speakers.get(i, f"p{i}")
        lines.append(f"S1.u{i}\tTexto del turno {i}. [[Aplausos]] fin {i}.")
        rows.append([f"S1.u{i}", "2022-01-25", role, gender, speaker, "notMinister", "PP", "Opposition", "Health"])
    (year / "s1.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with open(year / "s1-meta-en.tsv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(HEADER)
        writer.writerows(rows)


def read_sample(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def test_excerpt_truncates_and_strips_comments():
    assert excerpt("uno [[Aplausos]] dos tres", 10) == "uno dos tres"
    assert excerpt("uno dos tres cuatro", 2) == "uno dos …"
    assert excerpt("uno dos tres cuatro", 2, tail=True) == "… tres cuatro"
    assert excerpt(None, 5) == ""


def test_turn_number():
    assert turn_number("S1.u12") == 12
    assert turn_number("sin-formato") is None


def test_sample_is_blind_balanced_and_has_context(tmp_path):
    make_corpus(tmp_path)
    out = tmp_path / "muestra.csv"
    assert main([str(tmp_path), "--n", "1", "--salida", str(out)]) == 0

    rows = read_sample(out)
    assert len(rows) == 2  # una mujer y un hombre
    assert "Speaker_gender" not in rows[0] and "Speaker_ID" not in rows[0]  # anotación a ciegas
    genders = set()
    for r in rows:
        number = int(r["ID"].rsplit(".u", 1)[1])
        genders.add("F" if number in (2, 6) else "M")
        assert r["inicio"] == EXPECTED[r["ID"]]
        assert r["previo_1"] == EXPECTED[f"S1.u{number - 1}"]
        assert r["etiqueta"] == ""
    assert genders == {"F", "M"}


def test_sample_is_reproducible(tmp_path):
    make_corpus(tmp_path)
    for name in ("a.csv", "b.csv"):
        assert main([str(tmp_path), "--n", "1", "--semilla", "7", "--salida", str(tmp_path / name)]) == 0
    assert [r["ID"] for r in read_sample(tmp_path / "a.csv")] == [r["ID"] for r in read_sample(tmp_path / "b.csv")]


def test_sample_excludes_continuations(tmp_path):
    # u4 lo dice la misma persona que u2, con un turno breve de presidencia (u3) en medio: es continuación
    make_corpus(tmp_path, speakers={4: "p2"})
    out = tmp_path / "muestra.csv"
    assert main([str(tmp_path), "--n", "10", "--salida", str(out)]) == 0
    assert {r["ID"] for r in read_sample(out)} == {"S1.u2", "S1.u6", "S1.u8"}
