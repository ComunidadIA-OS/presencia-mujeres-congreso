import csv

from presencia.annotated import is_continuation, load_rows, split_rows, validate
from presencia.baseline import classify, people
from presencia.evaluation import evaluate


def row(previo="", secuencia="P(5) → A(100)", inicio="Texto largo " * 10, palabras=100):
    return {"previo_1": previo, "secuencia": secuencia, "inicio": inicio, "palabras": palabras}


def test_people_accepts_arrow_or_excel_question_mark():
    assert people("P(2) A(10) P(3) → B(20)") == (["A"], "B")
    assert people("P(2) A(10) P(3) ? B(20)") == (["A"], "B")  # Excel ANSI convierte → en ?
    assert people("") == ([], None)


def test_repeated_person_is_replica():
    assert classify(row(secuencia="P(2) A(10) P(3) B(20) P(3) → A(50)")) == "replica"


def test_rules_by_context():
    assert classify(row(previo="Pregunta de la diputada doña Ana, del Grupo X.")) == "pregunta"
    assert classify(row(previo="Proposición no de ley relativa a la sanidad. Tiene la palabra la señora Pérez.")) == "posicion"
    assert classify(row(previo="Señora ministra de Sanidad.")) == "respuesta"
    assert classify(row(inicio="Sí, juro.", palabras=2)) == "procedimental"
    assert classify(row(previo="Por el Grupo Popular, tiene la palabra el señor Gil.")) == "posicion"


def test_evaluate_metrics():
    labels = ("a", "b")
    result = evaluate(["a", "a", "b", "b"], ["a", "b", "b", "b"], labels)
    assert result["accuracy"] == 0.75
    assert round(result["per_class"]["b"]["recall"], 2) == 1.0
    assert round(result["per_class"]["a"]["recall"], 2) == 0.5
    assert result["confusion"][("a", "b")] == 1


def test_loader_handles_ansi_semicolon_and_splits(tmp_path):
    fields = ["ID", "previo_1", "secuencia", "inicio", "palabras", "etiqueta", "notas"]
    rows = [{"ID": f"x.u{i}", "previo_1": "", "secuencia": "P(1) ? A(9)", "inicio": "ñandú", "palabras": 9,
             "etiqueta": "posicion", "notas": ""} for i in range(17)]
    rows[16].update(etiqueta="otra", notas="Continuación")
    path = tmp_path / "m.csv"
    with open(path, "w", encoding="cp1252", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    loaded = load_rows(path)
    assert loaded[0]["inicio"] == "ñandú"
    assert validate(loaded) == []
    calibration, evaluation = split_rows(loaded)
    assert (len(calibration), len(evaluation)) == (15, 1)  # la continuación se excluye
    assert is_continuation(loaded[16])
    loaded[0]["etiqueta"] = "inventada"
    assert len(validate(loaded)) == 1
