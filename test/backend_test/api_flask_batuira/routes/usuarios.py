from __future__ import annotations

from flask import Blueprint, g, request
from werkzeug.security import generate_password_hash

from database import fetch_all, fetch_one, get_db
from responses import error, success
from security import auth_required
from utils import as_bool_int, audit_log, dynamic_update, get_json, pagination, require_fields

bp = Blueprint("usuarios", __name__)


USER_SELECT = """
SELECT
    u.id, u.nome, u.username, u.email, u.telefone, u.profissao,
    u.conselho_profissional, u.registro_profissional,
    u.primeiro_acesso, u.ativo, u.ultimo_login, u.criado_em, u.atualizado_em,
    p.id AS perfil_id, p.codigo AS perfil_codigo, p.nome AS perfil_nome
FROM usuarios u
JOIN perfis_acesso p ON p.id = u.perfil_id
"""


def serialize_user(row: dict) -> dict:
    row = dict(row)
    row["primeiro_acesso"] = bool(row["primeiro_acesso"])
    row["ativo"] = bool(row["ativo"])
    return row


def resolve_profile(data: dict, required: bool = False) -> int | None:
    if data.get("perfil_id") not in (None, ""):
        profile = fetch_one("SELECT id FROM perfis_acesso WHERE id = ?", (data["perfil_id"],))
    elif data.get("perfil") not in (None, ""):
        profile = fetch_one("SELECT id FROM perfis_acesso WHERE codigo = ?", (data["perfil"],))
    else:
        if required:
            raise ValueError("Informe perfil_id ou perfil.")
        return None
    if profile is None:
        raise ValueError("Perfil de acesso inválido.")
    return int(profile["id"])


@bp.get("/perfis")
@auth_required("admin")
def list_profiles():
    return success(fetch_all("SELECT * FROM perfis_acesso ORDER BY id"))


@bp.get("/usuarios")
@auth_required("admin")
def list_users():
    limit, offset = pagination()
    conditions = []
    params: list = []

    search = request.args.get("busca", "").strip()
    if search:
        conditions.append("(lower(u.nome) LIKE lower(?) OR lower(u.username) LIKE lower(?) OR lower(coalesce(u.email,'')) LIKE lower(?))")
        term = f"%{search}%"
        params.extend([term, term, term])
    if request.args.get("perfil"):
        conditions.append("p.codigo = ?")
        params.append(request.args["perfil"])
    if request.args.get("ativo") in {"0", "1"}:
        conditions.append("u.ativo = ?")
        params.append(int(request.args["ativo"]))

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    count = fetch_one(
        "SELECT COUNT(*) AS total FROM usuarios u JOIN perfis_acesso p ON p.id=u.perfil_id" + where,
        params,
    )["total"]
    rows = fetch_all(
        USER_SELECT + where + " ORDER BY u.nome LIMIT ? OFFSET ?",
        [*params, limit, offset],
    )
    return success({"itens": [serialize_user(r) for r in rows], "total": count, "limit": limit, "offset": offset})


@bp.get("/usuarios/<int:user_id>")
@auth_required("admin")
def get_user(user_id: int):
    row = fetch_one(USER_SELECT + " WHERE u.id = ?", (user_id,))
    if row is None:
        return error("Usuário não encontrado.", status=404)
    return success(serialize_user(row))


@bp.post("/usuarios")
@auth_required("admin")
def create_user():
    data = get_json()
    require_fields(data, ["nome", "username", "senha"])
    if len(str(data["senha"])) < 6:
        raise ValueError("A senha inicial precisa ter pelo menos 6 caracteres.")
    profile_id = resolve_profile(data, required=True)

    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO usuarios (
            perfil_id, nome, username, email, senha_hash, telefone,
            profissao, conselho_profissional, registro_profissional,
            primeiro_acesso, ativo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            profile_id,
            data["nome"].strip(),
            data["username"].strip(),
            data.get("email") or None,
            generate_password_hash(str(data["senha"])),
            data.get("telefone") or None,
            data.get("profissao") or None,
            data.get("conselho_profissional") or None,
            data.get("registro_profissional") or None,
            as_bool_int(data.get("primeiro_acesso", True)),
            as_bool_int(data.get("ativo", True)),
        ),
    )
    user_id = int(cursor.lastrowid)
    audit_log("CRIAR", "usuarios", user_id, {"username": data["username"]})
    db.commit()
    return success(serialize_user(fetch_one(USER_SELECT + " WHERE u.id = ?", (user_id,))), message="Usuário criado.", status=201)


@bp.put("/usuarios/<int:user_id>")
@auth_required("admin")
def update_user(user_id: int):
    if fetch_one("SELECT id FROM usuarios WHERE id = ?", (user_id,)) is None:
        return error("Usuário não encontrado.", status=404)
    data = get_json()
    if "perfil" in data or "perfil_id" in data:
        data["perfil_id"] = resolve_profile(data, required=True)
    if "ativo" in data:
        data["ativo"] = as_bool_int(data["ativo"])
    if "primeiro_acesso" in data:
        data["primeiro_acesso"] = as_bool_int(data["primeiro_acesso"])
    if "senha" in data:
        if len(str(data["senha"])) < 6:
            raise ValueError("A senha precisa ter pelo menos 6 caracteres.")
        data["senha_hash"] = generate_password_hash(str(data.pop("senha")))

    allowed = {
        "perfil_id", "nome", "username", "email", "telefone", "profissao",
        "conselho_profissional", "registro_profissional", "primeiro_acesso",
        "ativo", "senha_hash",
    }
    dynamic_update("usuarios", user_id, data, allowed)
    audit_log("ATUALIZAR", "usuarios", user_id)
    get_db().commit()
    return success(serialize_user(fetch_one(USER_SELECT + " WHERE u.id = ?", (user_id,))), message="Usuário atualizado.")


@bp.post("/usuarios/<int:user_id>/redefinir-senha")
@auth_required("admin")
def reset_password(user_id: int):
    if fetch_one("SELECT id FROM usuarios WHERE id = ?", (user_id,)) is None:
        return error("Usuário não encontrado.", status=404)
    data = get_json()
    require_fields(data, ["nova_senha"])
    if len(str(data["nova_senha"])) < 6:
        raise ValueError("A nova senha precisa ter pelo menos 6 caracteres.")
    db = get_db()
    db.execute(
        "UPDATE usuarios SET senha_hash = ?, primeiro_acesso = 1 WHERE id = ?",
        (generate_password_hash(str(data["nova_senha"])), user_id),
    )
    audit_log("REDEFINIR_SENHA", "usuarios", user_id)
    db.commit()
    return success(message="Senha redefinida. A troca será exigida no próximo acesso.")


@bp.delete("/usuarios/<int:user_id>")
@auth_required("admin")
def deactivate_user(user_id: int):
    if user_id == int(g.current_user["id"]):
        return error("Você não pode desativar o próprio usuário.", status=400)
    db = get_db()
    cursor = db.execute("UPDATE usuarios SET ativo = 0 WHERE id = ?", (user_id,))
    if cursor.rowcount == 0:
        return error("Usuário não encontrado.", status=404)
    audit_log("DESATIVAR", "usuarios", user_id)
    db.commit()
    return success(message="Usuário desativado.")
