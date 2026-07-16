from __future__ import annotations

import sqlite3

from flask import current_app
from werkzeug.exceptions import HTTPException

from database import get_db
from responses import error


def register_error_handlers(app) -> None:
    @app.errorhandler(ValueError)
    def handle_value_error(exc: ValueError):
        get_db().rollback()
        return error(str(exc), status=400)

    @app.errorhandler(sqlite3.IntegrityError)
    def handle_integrity_error(exc: sqlite3.IntegrityError):
        get_db().rollback()
        text = str(exc)
        if "UNIQUE constraint failed" in text:
            message = "Já existe um registro com um valor que precisa ser único."
        elif "FOREIGN KEY constraint failed" in text:
            message = "O registro informado possui relacionamento inválido ou ainda está em uso."
        elif "CHECK constraint failed" in text:
            message = "Um dos valores enviados não atende às regras do banco."
        elif "NOT NULL constraint failed" in text:
            message = "Um campo obrigatório não foi informado."
        else:
            message = "Não foi possível salvar os dados por uma regra de integridade."
        return error(message, status=409, details=text if current_app.debug else None)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return error(exc.description, status=exc.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        try:
            get_db().rollback()
        except Exception:
            pass
        current_app.logger.exception("Erro inesperado", exc_info=exc)
        return error(
            "Ocorreu um erro interno no servidor.",
            status=500,
            details=str(exc) if current_app.debug else None,
        )
