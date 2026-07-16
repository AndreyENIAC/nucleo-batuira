from __future__ import annotations

from typing import Any

from flask import jsonify


def success(
    data: Any = None,
    *,
    message: str | None = None,
    status: int = 200,
):
    payload: dict[str, Any] = {"sucesso": True}
    if message is not None:
        payload["mensagem"] = message
    if data is not None:
        payload["dados"] = data
    return jsonify(payload), status


def error(
    message: str,
    *,
    status: int = 400,
    details: Any = None,
):
    payload: dict[str, Any] = {"sucesso": False, "erro": message}
    if details is not None:
        payload["detalhes"] = details
    return jsonify(payload), status
