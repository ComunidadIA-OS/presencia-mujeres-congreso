import json
import os

from presencia.llm import build_messages, classify_rows, has_label, load_env, parse_label

ROW = {"ID": "x.u1", "previo_2": "", "previo_1": "Pregunta de la diputada X.", "secuencia": "P(5) → A(60)",
       "inicio": "Señor ministro, ...", "final": "", "palabras": 60, "etiqueta": ""}


def test_parse_label():
    assert parse_label("pregunta") == "pregunta"
    assert parse_label("Razonando... podría ser posicion, pero es replica") == "replica"
    assert parse_label("Réplica") == "replica"
    assert parse_label("") == "otra" and parse_label(None) == "otra"
    assert parse_label("no sé") == "otra"


def test_build_messages_uses_examples_as_few_shot():
    example = dict(ROW, etiqueta="pregunta")
    messages = build_messages(ROW, [example])
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "user"]
    assert messages[2]["content"] == "pregunta"
    assert "secuencia: P(5) → A(60)" in messages[3]["content"]


def test_load_env_does_not_override(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('# comentario\nOVH_AI_TOKEN="abc"\nOVH_AI_MODEL=m1\n', encoding="utf-8")
    monkeypatch.setenv("OVH_AI_MODEL", "ya-definido")
    monkeypatch.delenv("OVH_AI_TOKEN", raising=False)
    load_env(env)
    assert os.environ["OVH_AI_TOKEN"] == "abc" and os.environ["OVH_AI_MODEL"] == "ya-definido"


def test_classify_rows_uses_cache(tmp_path):
    calls = []

    def fake_ask(cfg, messages):
        calls.append(1)
        return "pregunta"

    cache = tmp_path / "c.jsonl"
    assert classify_rows({}, [ROW], [], cache_path=cache, ask=fake_ask, progress=False) == ["pregunta"]
    assert classify_rows({}, [ROW], [], cache_path=cache, ask=fake_ask, progress=False) == ["pregunta"]
    assert len(calls) == 1  # la segunda vez sale de la caché
    assert json.loads(cache.read_text(encoding="utf-8").splitlines()[0])["ID"] == "x.u1"


def test_empty_answers_are_not_cached(tmp_path):
    answers = iter(["", "pregunta"])  # vacía, luego válida
    cache = tmp_path / "c.jsonl"
    ask = lambda cfg, messages: next(answers)  # noqa: E731
    assert classify_rows({}, [ROW], [], cache_path=cache, ask=ask, progress=False) == ["otra"]
    assert not cache.exists() or cache.read_text(encoding="utf-8") == ""
    assert classify_rows({}, [ROW], [], cache_path=cache, ask=ask, progress=False) == ["pregunta"]


def test_has_label_and_failures_do_not_crash(tmp_path):
    assert has_label("Réplica") and not has_label("") and not has_label("no estoy seguro")

    def broken(cfg, messages):
        raise TimeoutError("lento")

    cache = tmp_path / "c.jsonl"
    assert classify_rows({}, [ROW], [], cache_path=cache, ask=broken, progress=False) == ["otra"]
    assert not cache.exists()  # nada que reutilizar: se reintentará
