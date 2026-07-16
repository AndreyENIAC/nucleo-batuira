from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, g
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from database import fetch_one, get_db
from responses import error, success
from security import auth_required
from utils import audit_log, get_json, require_fields

bp = Blueprint("auth", __name__)


def serialize_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "nome": user["nome"],
        "username": user["username"],
        "email": user["email"],
        "telefone": user["telefone"],
        "profissao": user["profissao"],
        "conselho_profissional": user["conselho_profissional"],
        "registro_profissional": user["registro_profissional"],
        "perfil": {
            "codigo": user["perfil_codigo"],
            "nome": user["perfil_nome"],
        },
        "primeiro_acesso": bool(user["primeiro_acesso"]),
        "ativo": bool(user["ativo"]),
        "ultimo_login": user["ultimo_login"],
    }


@bp.post("/auth/login")
def login():
    data = get_json()
    login_value = data.get("login") or data.get("username") or data.get("email")
    password = data.get("senha") or data.get("password")
    if not login_value or not password:
        return error("Informe usuário/e-mail e senha.", status=400)

    user = fetch_one(
        """
        SELECT u.*, p.codigo AS perfil_codigo, p.nome AS perfil_nome
        FROM usuarios u
        JOIN perfis_acesso p ON p.id = u.perfil_id
        WHERE u.username = ? OR lower(u.email) = lower(?)
        LIMIT 1
        """,
        (login_value, login_value),
    )
    if user is None or not check_password_hash(user["senha_hash"], password):
        return error("Usuário ou senha incorretos.", status=401)
    if not user["ativo"]:
        return error("Este usuário está desativado.", status=403)

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    db = get_db()
    db.execute("UPDATE usuarios SET ultimo_login = ? WHERE id = ?", (now, user["id"]))
    audit_log("LOGIN", "usuarios", int(user["id"]), user_id=int(user["id"]))
    db.commit()
    user["ultimo_login"] = now

    token = create_access_token(
        identity=str(user["id"]),
        additional_claims={"perfil": user["perfil_codigo"]},
    )
    return success(
        {
            "access_token": token,
            "tipo_token": "Bearer",
            "troca_senha_obrigatoria": bool(user["primeiro_acesso"]),
            "usuario": serialize_user(user),
        },
        message="Login realizado com sucesso.",
    )


@bp.get("/auth/me")
@auth_required(allow_first_access=True)
def me():
    return success(serialize_user(g.current_user))


@bp.post("/auth/trocar-senha")
@auth_required(allow_first_access=True)
def change_password():
    data = get_json()
    require_fields(data, ["nova_senha"])
    new_password = str(data["nova_senha"])
    confirmation = data.get("confirmacao", new_password)
    if len(new_password) < 6:
        raise ValueError("A nova senha precisa ter pelo menos 6 caracteres.")
    if new_password != confirmation:
        raise ValueError("A confirmação da senha não coincide.")

    user = g.current_user
    if not user["primeiro_acesso"]:
        current_password = data.get("senha_atual")
        if not current_password or not check_password_hash(user["senha_hash"], current_password):
            return error("A senha atual está incorreta.", status=401)

    db = get_db()
    db.execute(
        "UPDATE usuarios SET senha_hash = ?, primeiro_acesso = 0 WHERE id = ?",
        (generate_password_hash(new_password), user["id"]),
    )
    audit_log("TROCA_SENHA", "usuarios", int(user["id"]))
    db.commit()
    return success(message="Senha alterada com sucesso.")


@bp.post("/auth/logout")
@auth_required(allow_first_access=True)
def logout():
    audit_log("LOGOUT", "usuarios", int(g.current_user["id"]))
    get_db().commit()
    return success(message="Sessão encerrada. Remova o token no frontend.")
