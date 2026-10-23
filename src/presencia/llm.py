"""Cliente mínimo para un modelo de lenguaje abierto vía OVHcloud AI Endpoints.

Usa la API compatible con OpenAI (``/v1/chat/completions``), así que el modelo y la URL son
configurables: cambiar de proveedor o de modelo no requiere tocar el código. Solo biblioteca estándar.

Configuración (variables de entorno o archivo ``.env`` en la raíz, que NO se sube a Git):
    OVH_AI_TOKEN      clave de acceso (obligatoria)
    OVH_AI_BASE_URL   por defecto https://oai.endpoints.kepler.ai.cloud.ovh.net/v1
    OVH_AI_MODEL      nombre del modelo, p. ej. gpt-oss-120b
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
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
    }


def _request(url, token, payload=None, timeout=120):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def list_models(cfg):
    return sorted(m["id"] for m in _request(f"{cfg['base_url']}/models", cfg["token"]).get("data", []))


def chat(cfg, messages, max_tokens=3000, retries=3):
    """Una llamada a chat/completions; devuelve el texto de la respuesta."""
    payload = {"model": cfg["model"], "messages": messages, "temperature": 0, "max_tokens": max_tokens}
    for attempt in range(retries):
        try:
            data = _request(f"{cfg['base_url']}/chat/completions", cfg["token"], payload)
            message = data["choices"][0]["message"]
            return message.get("content") or message.get("reasoning_content") or ""
        except (urllib.error.URLError, TimeoutError, KeyError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt * 2)


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
    found = re.findall(r"\b(" + "|".join(LABELS) + r")\b", (text or "").lower().replace("réplica", "replica")
                       .replace("posición", "posicion"))
    return found[-1] if found else "otra"


def classify_rows(cfg, rows, examples, cache_path=None, ask=chat, progress=True):
    """Clasifica filas con el modelo. Guarda cada respuesta en caché (JSONL) para poder reanudar."""
    cache = {}
    if cache_path and Path(cache_path).is_file():
        for line in Path(cache_path).read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item["raw"].strip():  # una respuesta vacía no vale: se vuelve a pedir
                cache[item["ID"]] = item["raw"]
    out = []
    for i, row in enumerate(rows, 1):
        if row["ID"] not in cache:
            cache[row["ID"]] = ask(cfg, build_messages(row, examples))
            if cache_path and cache[row["ID"]].strip():
                Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
                with open(cache_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"ID": row["ID"], "raw": cache[row["ID"]]}, ensure_ascii=False) + "\n")
            if progress:
                print(f"  {i}/{len(rows)}", end="\r", flush=True)
        out.append(parse_label(cache[row["ID"]]))
    return out
