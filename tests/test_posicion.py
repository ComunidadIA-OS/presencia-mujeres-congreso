import math

from presencia.posicion import build_points, categories, point_map, summarize, wilson

TEI_DOC = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>
  <div><u xml:id="S.u1"><seg>Se abre la sesión.</seg></u></div>
  <div><head xml:id="S.head1">PROPOSICIONES NO DE LEY : - DEL GRUPO A, SOBRE X</head>
    <note>Número de expediente 1</note>
    <u xml:id="S.u2"><seg>a</seg></u><u xml:id="S.u3"><seg>b</seg></u><u xml:id="S.u4"><seg>c</seg></u>
  </div>
  <div><head xml:id="S.head2">- DEL GRUPO B, SOBRE Y</head>
    <u xml:id="S.u5"><seg>d</seg></u><u xml:id="S.u6"><seg>e</seg></u>
  </div>
</body></text></TEI>"""


def row(uid, role="Regular", gender="F", minister="notMinister"):
    return {"ID": uid, "Speaker_role": role, "Speaker_gender": gender, "Speaker_minister": minister}


def test_point_map_follows_headers(tmp_path):
    path = tmp_path / "S.xml"
    path.write_text(TEI_DOC, encoding="utf-8")
    m = point_map(path)
    assert m["S.u1"][0] == 0
    assert m["S.u2"] == (1, "PROPOSICIONES NO DE LEY : - DEL GRUPO A, SOBRE X")
    assert m["S.u4"][0] == 1 and m["S.u5"][0] == 2


def test_categories_inherit_section():
    assert categories(["PREGUNTAS : - DE X", "- DE Y", "VOTACIÓN DE CONJUNTO"]) == [
        "PREGUNTAS", "PREGUNTAS", "VOTACIÓN DE CONJUNTO"]


def test_build_points_skips_chair_and_continuations():
    pmap = {f"S.u{i}": (1, "P") for i in range(1, 6)}
    items = [(row("S.u1", role="Chairperson", gender="-"), ""), (row("S.u2", gender="F"), ""),
             (row("S.u3", role="Chairperson", gender="-"), ""), (row("S.u4", gender="F"), ""),
             (row("S.u5", gender="M", minister="minister"), "")]
    points = build_points(items, pmap, continuations={"S.u4"})
    assert [t[0] for t in points[0]["turnos"]] == ["S.u2", "S.u5"]
    assert points[0]["turnos"][1][2] is True  # ministro


def test_summarize_open_close_and_position():
    def point(genders, ministers=None, year="2020", cat="X"):
        ministers = ministers or [False] * len(genders)
        return {"turnos": [(f"id{i}", g, m) for i, (g, m) in enumerate(zip(genders, ministers))],
                "anio": year, "categoria": cat}

    points = [point(["F", "M"]), point(["M", "M", "F"]), point(["F"])]  # el último no cuenta (1 turno)
    rows = {(r["metrica"], r["grupo"]): r for r in summarize(points, min_group=1)}
    r1 = rows[("R1_apertura", "todas")]
    assert r1["n"] == 2 and r1["mujeres"] == 1 and r1["referencia_pct"] == 40.0  # 2 F de 5 turnos
    r2 = rows[("R2_cierre", "todas")]
    assert r2["mujeres"] == 1
    r5f = rows[("R5_posicion_media_mujeres", "todas")]
    assert r5f["n"] == 2 and math.isclose(r5f["pct_mujeres"], 0.5)  # posiciones 0 y 1


def test_summarize_without_ministers():
    points = [{"turnos": [("a", "M", True), ("b", "F", False), ("c", "M", False)], "anio": "2020", "categoria": "X"}]
    rows = {(r["metrica"], r["grupo"]): r for r in summarize(points, min_group=1)}
    assert rows[("R1_apertura", "todas")]["mujeres"] == 0
    assert rows[("R1_apertura", "sin_ministros")]["mujeres"] == 1


def test_wilson_bounds():
    lo, hi = wilson(5, 10)
    assert 0 < lo < 0.5 < hi < 1