import csv

from presencia import classify, llm, roles
from test_sample import make_corpus


def test_classify_end_to_end_without_api(tmp_path, monkeypatch):
    make_corpus(tmp_path, speakers={6: "p2"})  # u6 la dice la misma persona que u2: réplica por estructura
    monkeypatch.setattr(llm, "settings", lambda model=None: {"model": model, "thinking": True})
    asked = []

    def fake_chat(cfg, messages, **kw):
        asked.append(1)
        return "posicion"

    monkeypatch.setattr(llm, "chat", fake_chat)
    out = tmp_path / "roles.csv"
    assert classify.main([str(tmp_path), "--n", "0", "--anotada", str(tmp_path / "no.csv"), "--paralelo", "1",
                          "--cache", str(tmp_path / "llm"), "--salida", str(out)]) == 0
    with open(out, encoding="utf-8") as fh:
        rows = {r["ID"]: r for r in csv.DictReader(fh)}
    assert set(rows) == {"S1.u2", "S1.u4", "S1.u6", "S1.u8"}
    assert rows["S1.u6"]["rol"] == "replica" and rows["S1.u6"]["metodo"] == "estructura"
    assert rows["S1.u2"]["rol"] == "posicion" and rows["S1.u2"]["metodo"] == "modelo"
    assert "Speaker_ID" not in rows["S1.u2"]  # no guarda la identidad de la persona
    assert len(asked) == 3


def test_roles_summary_and_wilson():
    low, high = roles.wilson(5, 10)
    assert 0.2 < low < 0.5 < high < 0.8
    rows = [{"Speaker_gender": g, "Speaker_minister": "notMinister", "Party_status": "Opposition",
             "rol": rol, "peso": "1"} for g, rol in [("F", "pregunta"), ("F", "posicion"), ("M", "posicion"), ("M", "posicion")]]
    summary = {(s["grupo"], s["rol"]): s for s in roles.summarize(rows)}
    assert summary[("todas", "pregunta")]["cuota_mujeres"] == 100.0
    assert abs(summary[("todas", "posicion")]["razon"] - (1 / 3) / 0.5) < 1e-9
