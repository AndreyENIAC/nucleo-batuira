from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "batuira.db"))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "troque-esta-chave-em-producao-nucleo-batuira",
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_HOURS", "8"))
    )
    JWT_ERROR_MESSAGE_KEY = "erro"

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = True


class TestingConfig(Config):
    TESTING = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
