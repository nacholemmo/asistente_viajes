"""Configuración leída desde .env. Nada de claves ni modelos hardcodeados."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

load_dotenv(ROOT / ".env")


def get_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("Falta ANTHROPIC_API_KEY en .env (ver .env.example)")
    return key


def get_model() -> str:
    model = os.getenv("ANTHROPIC_MODEL")
    if not model:
        raise RuntimeError("Falta ANTHROPIC_MODEL en .env (ver .env.example)")
    return model
