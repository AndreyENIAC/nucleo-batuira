from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Iterable

from flask import request

from database import get_db


def get_json() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Envie um objeto JSON válido.")
    return data


def require_fields(data: dict[str, Any], fields: Iterable[str]) -> None:
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValueError(f"Campos obrigatórios: {', '.join(missing)}.")


def as_bool_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value in (1, "1", "true", "True", "sim", "Sim"):
        return 1
    if value in (0, "0", "false", "False", "nao", "não", "Não", None, ""):
        return 0
    raise ValueError(f"Valor booleano inválido: {value!r}.")


def calculate_age(date_of_birth: str | None) -> int | None:
    if not date_of_birth:
        return None
    try:
        born = date.fromisoformat(date_of_birth[:10])
    except ValueError:
        return None
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def normalize_competence(value: str) -> str:
    value = value.strip()
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise ValueError("A competência deve estar no formato AAAA-MM.") from exc
    return value


def pagination(default_limit: int = 50, max_limit: int = 200) -> tuple[int, int]:
    try:
        limit = int(request.args.get("limit", default_limit))
        offset = int(request.args.get("offset", 0))
    except ValueError as exc:
        raise ValueError("limit e offset precisam ser números inteiros.") from exc
    limit = max(1, min(limit, max_limit))
    offset = max(0, offset)
    return limit, offset


def dynamic_update(
    table: str,
    record_id: int,
    data: dict[str, Any],
    allowed_fields: Iterable[str],
    *,
    id_field: str = "id",
) -> bool:
    allowed = set(allowed_fields)
    fields = [key for key in data if key in allowed]
    if not fields:
        raise ValueError("Nenhum campo válido foi enviado para atualização.")

    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [data[field] for field in fields]
    values.append(record_id)

    cursor = get_db().execute(
        f"UPDATE {table} SET {assignments} WHERE {id_field} = ?", values
    )
    return cursor.rowcount > 0


def audit_log(
    action: str,
    table: str,
    record_id: int | None = None,
    details: dict[str, Any] | None = None,
    user_id: int | None = None,
) -> None:
    from flask import g

    if user_id is None:
        current_user = getattr(g, "current_user", None)
        if current_user:
            user_id = int(current_user["id"])

    get_db().execute(
        """
        INSERT INTO logs_auditoria (
            usuario_id, acao, tabela, registro_id, detalhes_json, endereco_ip
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            action,
            table,
            record_id,
            json.dumps(details, ensure_ascii=False, default=str) if details else None,
            request.remote_addr,
        ),
    )
