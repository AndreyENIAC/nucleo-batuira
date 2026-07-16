from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from database import fetch_one
from responses import error


def load_current_user() -> dict | None:
    identity = get_jwt_identity()
    if identity is None:
        return None
    return fetch_one(
        """
        SELECT u.*, p.codigo AS perfil_codigo, p.nome AS perfil_nome
        FROM usuarios u
        JOIN perfis_acesso p ON p.id = u.perfil_id
        WHERE u.id = ?
        """,
        (int(identity),),
    )


def auth_required(
    *roles: str,
    allow_first_access: bool = False,
) -> Callable:
    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = load_current_user()
            if user is None or not user["ativo"]:
                return error("Usuário inexistente ou desativado.", status=401)
            if user["primeiro_acesso"] and not allow_first_access:
                return error(
                    "Troque a senha inicial antes de acessar o sistema.",
                    status=403,
                    details={"troca_senha_obrigatoria": True},
                )
            if roles and user["perfil_codigo"] not in roles:
                return error("Você não possui permissão para esta operação.", status=403)
            g.current_user = user
            return function(*args, **kwargs)

        return wrapper

    return decorator
