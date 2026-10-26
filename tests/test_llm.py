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


def test_parallel_and_hybrid_decide(tmp_path):
    rows = [dict(ROW, ID=f"x.u{i}") for i in range(1, 7)]
    asked = []

    def fake_ask(cfg, messages):
        asked.append(messages[-1]["content"])
        return "posicion"

    decide = lambda row: "replica" if row["ID"] == "x.u3" else None  # noqa: E731
    cache = tmp_path / "c.jsonl"
    out = classify_rows({}, rows, [], cache_path=cache, ask=fake_ask, progress=False, workers=3, decide=decide)
    assert out == ["posicion", "posicion", "replica", "posicion", "posicion", "posicion"]
    assert len(asked) == 5  # la fila decidida por estructura no llama al modelo
    assert len(cache.read_text(encoding="utf-8").splitlines()) == 5


def test_chat_disables_thinking_and_falls_back_on_400(monkeypatch):
    import io
    import urllib.error

    from presencia import llm

    payloads = []

    def fake_request(url, token, payload=None, timeout=120):
        payloads.append(dict(payload))
        if "chat_template_kwargs" in payload:
            raise urllib.error.HTTPError(url, 400, "bad", {}, io.BytesIO(b""))
        return {"choices": [{"message": {"content": "pregunta"}}]}

    monkeypatch.setattr(llm, "_request", fake_request)
    cfg = {"base_url": "u", "token": "t", "model": "m", "thinking": False, "timeout": 5}
    assert llm.chat(cfg, [{"role": "user", "content": "x"}]) == "pregunta"
    assert payloads[0]["chat_template_kwargs"] == {"enable_thinking": False}
    assert "chat_template_kwargs" not in payloads[1]


def test_chat_gives_up_quickly_on_timeouts(monkeypatch):
    from presencia import llm

    calls = []

    def slow(url, token, payload=None, timeout=120):
        calls.append(1)
        raise TimeoutError("timed out")

    monkeypatch.setattr(llm, "_request", slow)
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    try:
        llm.chat({"base_url": "u", "token": "t", "model": "m"}, [])
    except TimeoutError:
        pass
    assert len(calls) == 2  # un reintento y a la siguiente fila


def test_chat_retries_remote_disconnected(monkeypatch):
    import http.client

    from presencia import llm

    calls = []

    def flaky(url, token, payload=None, timeout=120):
        calls.append(1)
        if len(calls) == 1:
            raise http.client.RemoteDisconnected("cerrada")
        return {"choices": [{"message": {"content": "posicion"}}]}

    monkeypatch.setattr(llm, "_request", flaky)
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    assert llm.chat({"base_url": "u", "token": "t", "model": "m"}, []) == "posicion"
    assert len(calls) == 2
