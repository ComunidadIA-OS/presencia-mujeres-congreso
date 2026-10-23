#!/usr/bin/env python3
"""Lista los modelos disponibles en tu cuenta de OVHcloud AI Endpoints.

Uso: python src/presencia/models.py
"""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from presencia.llm import list_models, settings  # noqa: E402

if __name__ == "__main__":
    cfg = settings()
    print(f"Consultando {cfg['base_url']}/models ...")
    for name in list_models(cfg):
        print(" ", name)
