import csv

import pytest

from presencia.agreement import cohen_kappa, interpret, main

FIELDS = ["ID", "previo_2", "previo_1", "secuencia", "inicio", "final", "palabras", "etiqueta", "notas"]


def write(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({f: r.get(f, "") for f in FIELDS})


def test_kappa_perfect_and_known_value():
    assert cohen_kappa(["a", "b", "a"], ["a", "b", "a"]) == pytest.approx(1.0)
    # po = 0.75; pe = 0.5*0.25 + 0.5*0.75 = 0.5; kappa = 0.5
    assert cohen_kappa(["a", "a", "b", "b"], ["a", "b", "b", "b"]) == pytest.approx(0.5)


def test_kappa_rejects_bad_input():
    with pytest.raises(ValueError):
        cohen_kappa([], [])
    with pytest.raises(ValueError):
        cohen_kappa(["a"], ["a", "b"])


def test_interpret_scale():
    assert interpret(0.85) == "casi perfecto"
    assert interpret(0.65) == "sustancial"
    assert interpret(-0.1) == "pobre"


def test_solo_kappa_joins_by_id_and_skips_continuations(tmp_path, capsys):
    reference = [{"ID": f"S.u{i}", "etiqueta": "posicion"} for i in range(1, 6)]
    reference.append({"ID": "S.u6", "etiqueta": "otra", "notas": "continuación"})
    second = [
        {"ID": "S.u1", "etiqueta": "posicion"},
        {"ID": "S.u2", "etiqueta": "replica"},
        {"ID": "S.u6", "etiqueta": "posicion"},          # continuación en la referencia: fuera
        {"ID": "N.u1", "etiqueta": "pregunta"},          # nueva
    ]
    ref_path, second_path = tmp_path / "ref.csv", tmp_path / "a2.csv"
    write(ref_path, reference)
    write(second_path, second)

    assert main([str(second_path), "--referencia", str(ref_path), "--solo-kappa"]) == 0
    out = capsys.readouterr().out
    assert "comunes con la referencia: 2 | nuevas: 1" in out
    assert "Acuerdo observado: 1/2" in out
    assert "S.u2" in out  # aparece en la lista de desacuerdos


def test_rejects_empty_labels(tmp_path):
    ref_path, second_path = tmp_path / "ref.csv", tmp_path / "a2.csv"
    write(ref_path, [{"ID": "S.u1", "etiqueta": "posicion"}])
    write(second_path, [{"ID": "S.u1", "etiqueta": ""}])
    assert main([str(second_path), "--referencia", str(ref_path), "--solo-kappa"]) == 1
