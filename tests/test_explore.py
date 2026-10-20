import csv

from presencia.explore import build_report, find_metadata_files, main, summarize

COLUMNS = ["Date", "Speaker_role", "Speaker_ID", "Speaker_gender", "Speaker_minister", "Topic"]


def write_tsv(path, rows, columns):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(columns)
        writer.writerows(rows)


def test_summarize_excludes_chair_and_counts_gender(tmp_path):
    write_tsv(
        tmp_path / "a-meta-en.tsv",
        [
            ["2015-10-14", "Chairperson", "-", "-", "-", "Other"],
            ["2015-10-14", "Regular", "ana", "F", "notMinister", "Civil Rights"],
            ["2015-10-14", "Chairperson", "-", "-", "-", "Other"],
            ["2016-01-01", "Regular", "luis", "M", "notMinister", "Macroeconomics"],
            ["2016-01-01", "Regular", "luis", "M", "notMinister", "Macroeconomics"],
        ],
        COLUMNS,
    )
    # TSV en español: no tiene la columna Speaker_gender y debe ignorarse
    write_tsv(tmp_path / "a-meta.tsv", [["2015-10-14", "Regular"]], ["Fecha", "Rol"])
    # TSV en español: mismas columnas pero valores traducidos; debe ignorarse (si no, todo se cuenta doble)
    write_tsv(tmp_path / "a-meta-es.tsv", [["2015-10-14", "Presidencia", "-", "-", "-", "Otros"]], COLUMNS)

    files = find_metadata_files(tmp_path)
    assert [f.name for f in files] == ["a-meta-en.tsv"]

    s = summarize(files)
    assert s["rows"] == 5
    assert s["role"]["Chairperson"] == 2
    assert s["role_gender"][("Regular", "F")] == 1
    assert s["speakers"]["F"] == {"ana"}
    assert s["speakers"]["M"] == {"luis"}
    assert s["year_gender"]["2016"]["M"] == 2
    assert "Other" not in s["topic_gender"]  # la presidencia no cuenta
    assert s["chair_year"]["2015"]["-"] == 2  # pero sus turnos se cuentan aparte
    assert "Presidencia (turnos" in build_report(s)


def test_main_reports_missing_folder(tmp_path, capsys):
    assert main([str(tmp_path / "no-existe")]) == 2
    assert "no existe" in capsys.readouterr().out


def test_short_rows_do_not_crash(tmp_path):
    # Fila más corta que la cabecera: faltan Speaker_minister y Topic
    path = tmp_path / "b-meta-en.tsv"
    path.write_text("\t".join(COLUMNS) + "\n2015-10-14\tRegular\tana\tF\n", encoding="utf-8")
    s = summarize([path])
    assert s["minister"]["?"] == 1
    assert "?" in s["topic_gender"]
    assert "Condición de ministro" in build_report(s)
