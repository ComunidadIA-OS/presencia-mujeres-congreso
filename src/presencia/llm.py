"""Cliente mínimo para un modelo de lenguaje abierto vía OVHcloud AI Endpoints.

Usa la API compatible con OpenAI (``/v1/chat/completions``), así que el modelo y la URL son
configurables: cambiar de proveedor o de modelo no requiere tocar el código. Solo biblioteca estándar.

Configuración (variables de entorno o archivo ``.env`` en la raíz, que NO se sube a Git):
    OVH_AI_TOKEN      clave de acceso (obligatoria)
    OVH_AI_BASE_URL   por defecto https://oai.endpoints.kepler.ai.cloud.ovh.net/v1
    OVH_AI_MODEL      nombre del modelo, p. ej. gpt-oss-120b
    OVH_AI_TIMEOUT    segundos de espera por petición (por defecto 120)
    OVH_AI_THINKING   0 para pedir al modelo que no razone antes de responder (Qwen3.x); más rápido
"""
from __future__ import annotations

import http.client
import json
import os
import re
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
from pathlib import Path

from presencia.annotated import LABELS

DEFAULT_BASE_URL = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"

SYSTEM_PROMPT = """Eres un analista de debates del Congreso de los Diputados de España.
Tu tarea: decidir qué FUNCIÓN cumple una intervención en el debate. Responde SOLO con una etiqueta:

- defensa: ABRE un punto presentando una iniciativa (proposición, moción, enmienda, proyecto de ley, decreto-ley). Solo el turno de presentación.
- pregunta: formula una pregunta oral o una interpelación al Gobierno (aunque suene a reproche).
- respuesta: PRIMERA contestación a una pregunta o interpelación, o contestación del Gobierno a lo planteado por los grupos.
- replica: segundo turno o posterior de la MISMA persona dentro de un intercambio (réplica o dúplica).
- posicion: fija la posición de su grupo, turno a favor o en contra, o explica el voto.
- procedimental: cuestión de orden, alusiones, juramento, resultado de votaciones, trámite.
- otra: no encaja o no se puede decidir.

Datos que recibes: el turno anterior de la presidencia (previo_1), un turno previo (previo_2), la
`secuencia` de turnos (P = presidencia; letras = personas distintas, la misma letra es la misma
persona; la flecha o el signo ? marca el turno a clasificar; los números son palabras), el inicio del
texto y su longitud. Si en `secuencia` la letra del turno a clasificar ya había hablado antes en el
intercambio, es una replica. Decide por la función, no por el tema ni el tono."""


def load_env(path=".env"):
    """Carga KEY=VALUE de un .env en os.environ sin pisar lo que ya esté definido."""
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def settings(model=None):
    load_env()
    token = os.environ.get("OVH_AI_TOKEN")
    if not token:
        raise SystemExit("Falta OVH_AI_TOKEN: defínelo en el archivo .env (ver README).")
    return {
        "token": token,
        "base_url": os.environ.get("OVH_AI_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        "model": model or os.environ.get("OVH_AI_MODEL", ""),
        "timeout": float(os.environ.get("OVH_AI_TIMEOUT", "120")),
        "thinking": os.environ.get("OVH_AI_THINKING", "1") != "0",
    }


def _request(url, token, payload=None, timeout=120):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def list_models(cfg):
    return sorted(m["id"] for m in _request(f"{cfg['base_url']}/models", cfg["token"]).get("data", []))


def chat(cfg, messages, max_tokens=None, retries=3):
    """Una llamada a chat/completions; devuelve el texto de la respuesta.

    Reintenta los errores pasajeros (429, 5xx). Un *timeout* se reintenta solo una vez: si el modelo
    tarda más que ``cfg['timeout']`` es mejor pasar a la siguiente fila y volver en otra ejecución.
    """
    max_tokens = max_tokens or int(os.environ.get("OVH_AI_MAX_TOKENS", "8000"))  # los modelos que razonan gastan muchos
    payload = {"model": cfg["model"], "messages": messages, "temperature": 0, "max_tokens": max_tokens}
    if not cfg.get("thinking", True):
        # Plantillas de Qwen3.x servidas con vLLM: desactiva el razonamiento previo. Si el servidor
        # no lo acepta (error 400), se repite la petición sin este campo.
        payload["chat_template_kwargs"] = {"enable_thinking": False}
        payload["max_tokens"] = min(max_tokens, 50)
    timeout = cfg.get("timeout", 120)
    timeouts = 0
    for attempt in range(retries):
        try:
            data = _request(f"{cfg['base_url']}/chat/completions", cfg["token"], payload, timeout=timeout)
            # Solo vale la respuesta final. El razonamiento (reasoning_content) menciona varias etiquetas
            # y no es una respuesta; si el modelo se queda sin tokens razonando, content llega vacío.
            return data["choices"][0]["message"].get("content") or ""
        except urllib.error.HTTPError as exc:
            if exc.code == 400 and "chat_template_kwargs" in payload:
                payload.pop("chat_template_kwargs")
                payload["max_tokens"] = max_tokens
                continue
            if exc.code not in (429, 500, 502, 503, 504) or attempt == retries - 1:
                raise
            time.sleep(2 ** attempt * 2)
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException, KeyError) as exc:
            # ConnectionError incluye RemoteDisconnected: el servidor cerró la conexión (saturado). Se reintenta.
            timed_out = isinstance(exc, TimeoutError) or "timed out" in str(exc).lower()
            timeouts += timed_out
            if attempt == retries - 1 or timeouts > 1:
                raise TimeoutError(str(exc)) if timed_out else exc
            time.sleep(2 ** attempt * 2)
    return ""


def describe(row):
    return (f"previo_2: {row['previo_2']}\nprevio_1: {row['previo_1']}\nsecuencia: {row['secuencia']}\n"
            f"inicio: {row['inicio']}\nfinal: {row.get('final', '')}\npalabras: {row['palabras']}")


def build_messages(row, examples):
    """Prompt con ejemplos (few-shot) tomados SOLO del conjunto de calibración."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for ex in examples:
        messages.append({"role": "user", "content": describe(ex)})
        messages.append({"role": "assistant", "content": ex["etiqueta"].strip()})
    messages.append({"role": "user", "content": describe(row)})
    return messages


def parse_label(text):
    """Última etiqueta válida mencionada en la respuesta; 'otra' si no hay ninguna."""
    found = re.findall(r"\b(" + "|".join(LABELS) + r")\b", _normalize(text))
    return found[-1] if found else "otra"


def has_label(text):
    return bool(re.search(r"\b(" + "|".join(LABELS) + r")\b", _normalize(text)))


def _normalize(text):
    return (text or "").lower().replace("réplica", "replica").replace("posición", "posicion")


def load_cache(cache_path):
    """Respuestas guardadas {ID: texto}. Las vacías o sin etiqueta no valen: se vuelven a pedir."""
    cache = {}
    if cache_path and Path(cache_path).is_file():
        for line in Path(cache_path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if has_label(item["raw"]):
                cache[item["ID"]] = item["raw"]
    return cache


def classify_rows(cfg, rows, examples, cache_path=None, ask=None, progress=True, workers=1, decide=None):
    """Clasifica filas con el modelo. Guarda cada respuesta en caché (JSONL) para poder reanudar.

    ``workers`` > 1 lanza varias peticiones a la vez (respeta los límites del proveedor: 2 a 4 basta).
    ``decide(row)`` puede devolver una etiqueta sin llamar al modelo (método híbrido) o None.
    """
    ask = ask or chat
    cache = load_cache(cache_path)
    fixed = {}
    if decide is not None:
        for row in rows:
            label = decide(row)
            if label:
                fixed[row["ID"]] = label
    pending = [r for r in rows if r["ID"] not in fixed and r["ID"] not in cache]
    total, done, failed = len(pending), 0, 0

    def ask_one(row):
        try:
            return row, ask(cfg, build_messages(row, examples))
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as exc:
            detail = f" {exc.code}" if isinstance(exc, urllib.error.HTTPError) else ""
            print(f"\n  AVISO fila {row['ID']}: {type(exc).__name__}{detail}; se reintentará en la próxima ejecución")
            return row, ""

    def store(row, answer):
        nonlocal done, failed
        done += 1
        if not has_label(answer):
            failed += 1
            return
        cache[row["ID"]] = answer
        if cache_path:
            Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ID": row["ID"], "raw": answer}, ensure_ascii=False) + "\n")
        if progress:
            print(f"  {done}/{total}", end="\r", flush=True)

    if workers <= 1:
        for row in pending:
            store(*ask_one(row))
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for future in as_completed([pool.submit(ask_one, row) for row in pending]):
                store(*future.result())  # se escribe en el hilo principal: la caché no se corrompe

    if failed:
        print(f"\n  AVISO: {failed} filas sin respuesta válida (contadas como 'otra'). Vuelve a ejecutar para reintentarlas.")
    out = []
    for row in rows:
        if row["ID"] in fixed:
            out.append(fixed[row["ID"]])
        else:
            out.append(parse_label(cache.get(row["ID"], "")))
    return out
