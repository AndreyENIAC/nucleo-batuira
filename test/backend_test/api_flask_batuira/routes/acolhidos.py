from __future__ import annotations

from datetime import date

from flask import Blueprint, request

from database import fetch_all, fetch_one, get_db
from responses import error, success
from security import auth_required
from utils import (
    as_bool_int,
    audit_log,
    calculate_age,
    dynamic_update,
    get_json,
    pagination,
    require_fields,
)

bp = Blueprint("acolhidos", __name__)


ACOLHIDO_FIELDS = {
    "nome", "data_nascimento", "cpf", "rg", "sexo", "modalidade_acolhimento",
    "data_admissao", "data_saida", "ala", "quarto", "status", "tipo_atendimento",
    "convenio", "endereco", "foto_url", "observacoes",
}


def serialize_resident(row: dict) -> dict:
    result = dict(row)
    result["idade"] = calculate_age(result.get("data_nascimento"))
    return result


def ensure_resident(resident_id: int) -> dict | None:
    return fetch_one("SELECT * FROM acolhidos WHERE id = ?", (resident_id,))


@bp.get("/acolhidos")
@auth_required("admin", "technical", "financial", "staff")
def list_residents():
    limit, offset = pagination()
    conditions: list[str] = []
    params: list = []

    search = request.args.get("busca", "").strip()
    if search:
        conditions.append("lower(a.nome) LIKE lower(?)")
        params.append(f"%{search}%")
    for field in ("status", "modalidade_acolhimento", "tipo_atendimento"):
        if request.args.get(field):
            conditions.append(f"a.{field} = ?")
            params.append(request.args[field])

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    total = fetch_one("SELECT COUNT(*) AS total FROM acolhidos a" + where, params)["total"]
    rows = fetch_all(
        """
        SELECT
            a.*,
            d.descricao AS diagnostico_principal,
            f.nome AS contato_principal_nome,
            f.telefone AS contato_principal_telefone,
            (
                SELECT MAX(e.inicio)
                FROM eventos_agenda e
                WHERE e.acolhido_id = a.id
                  AND lower(e.tipo) IN ('médica', 'medica', 'consulta', 'consulta médica')
            ) AS ultima_consulta
        FROM acolhidos a
        LEFT JOIN diagnosticos d
               ON d.acolhido_id = a.id AND d.principal = 1 AND d.ativo = 1
        LEFT JOIN familiares f
               ON f.acolhido_id = a.id AND f.contato_principal = 1 AND f.ativo = 1
        """
        + where
        + " ORDER BY a.nome LIMIT ? OFFSET ?",
        [*params, limit, offset],
    )
    return success(
        {
            "itens": [serialize_resident(row) for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )


@bp.get("/acolhidos/<int:resident_id>")
@auth_required("admin", "technical", "financial", "staff")
def get_resident(resident_id: int):
    row = fetch_one(
        """
        SELECT
            a.*,
            d.descricao AS diagnostico_principal,
            d.cid AS diagnostico_cid,
            f.id AS contato_principal_id,
            f.nome AS contato_principal_nome,
            f.parentesco AS contato_principal_parentesco,
            f.telefone AS contato_principal_telefone,
            f.email AS contato_principal_email
        FROM acolhidos a
        LEFT JOIN diagnosticos d
               ON d.acolhido_id = a.id AND d.principal = 1 AND d.ativo = 1
        LEFT JOIN familiares f
               ON f.acolhido_id = a.id AND f.contato_principal = 1 AND f.ativo = 1
        WHERE a.id = ?
        """,
        (resident_id,),
    )
    if row is None:
        return error("Acolhido não encontrado.", status=404)
    return success(serialize_resident(row))


@bp.post("/acolhidos")
@auth_required("admin", "technical")
def create_resident():
    data = get_json()
    require_fields(data, ["nome", "data_nascimento", "modalidade_acolhimento", "data_admissao"])
    fields = [field for field in ACOLHIDO_FIELDS if field in data]
    values = [data[field] for field in fields]
    placeholders = ", ".join("?" for _ in fields)

    db = get_db()
    cursor = db.execute(
        f"INSERT INTO acolhidos ({', '.join(fields)}) VALUES ({placeholders})",
        values,
    )
    resident_id = int(cursor.lastrowid)
    audit_log("CRIAR", "acolhidos", resident_id, {"nome": data["nome"]})
    db.commit()
    return success(serialize_resident(ensure_resident(resident_id)), message="Acolhido cadastrado.", status=201)


@bp.put("/acolhidos/<int:resident_id>")
@auth_required("admin", "technical")
def update_resident(resident_id: int):
    if ensure_resident(resident_id) is None:
        return error("Acolhido não encontrado.", status=404)
    data = get_json()
    dynamic_update("acolhidos", resident_id, data, ACOLHIDO_FIELDS)
    audit_log("ATUALIZAR", "acolhidos", resident_id)
    get_db().commit()
    return success(serialize_resident(ensure_resident(resident_id)), message="Acolhido atualizado.")


@bp.delete("/acolhidos/<int:resident_id>")
@auth_required("admin")
def deactivate_resident(resident_id: int):
    if ensure_resident(resident_id) is None:
        return error("Acolhido não encontrado.", status=404)
    db = get_db()
    db.execute(
        "UPDATE acolhidos SET status = 'inativo', data_saida = COALESCE(data_saida, ?) WHERE id = ?",
        (date.today().isoformat(), resident_id),
    )
    audit_log("INATIVAR", "acolhidos", resident_id)
    db.commit()
    return success(message="Acolhido marcado como inativo.")


# Familiares
@bp.get("/acolhidos/<int:resident_id>/familiares")
@auth_required("admin", "technical", "financial", "staff")
def list_family(resident_id: int):
    if ensure_resident(resident_id) is None:
        return error("Acolhido não encontrado.", status=404)
    rows = fetch_all(
        "SELECT * FROM familiares WHERE acolhido_id = ? ORDER BY contato_principal DESC, nome",
        (resident_id,),
    )
    for row in rows:
        for field in ("contato_principal", "responsavel_legal", "autorizado_visita", "ativo"):
            row[field] = bool(row[field])
    return success(rows)


@bp.post("/acolhidos/<int:resident_id>/familiares")
@auth_required("admin", "technical")
def create_family(resident_id: int):
    if ensure_resident(resident_id) is None:
        return error("Acolhido não encontrado.", status=404)
    data = get_json()
    require_fields(data, ["nome", "parentesco"])
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO familiares (
            acolhido_id, nome, parentesco, telefone, email, endereco,
            contato_principal, responsavel_legal, autorizado_visita,
            frequencia_visita, ativo, observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resident_id, data["nome"], data["parentesco"], data.get("telefone"),
            data.get("email"), data.get("endereco"),
            as_bool_int(data.get("contato_principal", False)),
            as_bool_int(data.get("responsavel_legal", False)),
            as_bool_int(data.get("autorizado_visita", True)),
            data.get("frequencia_visita"), as_bool_int(data.get("ativo", True)),
            data.get("observacoes"),
        ),
    )
    family_id = int(cursor.lastrowid)
    audit_log("CRIAR", "familiares", family_id, {"acolhido_id": resident_id})
    db.commit()
    return success(fetch_one("SELECT * FROM familiares WHERE id = ?", (family_id,)), message="Familiar cadastrado.", status=201)


@bp.put("/familiares/<int:family_id>")
@auth_required("admin", "technical")
def update_family(family_id: int):
    if fetch_one("SELECT id FROM familiares WHERE id = ?", (family_id,)) is None:
        return error("Familiar não encontrado.", status=404)
    data = get_json()
    for field in ("contato_principal", "responsavel_legal", "autorizado_visita", "ativo"):
        if field in data:
            data[field] = as_bool_int(data[field])
    dynamic_update(
        "familiares",
        family_id,
        data,
        {
            "nome", "parentesco", "telefone", "email", "endereco", "contato_principal",
            "responsavel_legal", "autorizado_visita", "frequencia_visita", "ativo", "observacoes",
        },
    )
    audit_log("ATUALIZAR", "familiares", family_id)
    get_db().commit()
    return success(fetch_one("SELECT * FROM familiares WHERE id = ?", (family_id,)), message="Familiar atualizado.")


@bp.delete("/familiares/<int:family_id>")
@auth_required("admin", "technical")
def deactivate_family(family_id: int):
    db = get_db()
    cursor = db.execute("UPDATE familiares SET ativo = 0, contato_principal = 0 WHERE id = ?", (family_id,))
    if cursor.rowcount == 0:
        return error("Familiar não encontrado.", status=404)
    audit_log("INATIVAR", "familiares", family_id)
    db.commit()
    return success(message="Familiar desativado.")


# Visitas
@bp.get("/acolhidos/<int:resident_id>/visitas")
@auth_required("admin", "technical", "staff")
def list_visits(resident_id: int):
    if ensure_resident(resident_id) is None:
        return error("Acolhido não encontrado.", status=404)
    return success(
        fetch_all(
            """
            SELECT v.*, f.nome AS familiar_nome, u.nome AS registrado_por_nome
            FROM visitas v
            LEFT JOIN familiares f ON f.id = v.familiar_id
            JOIN usuarios u ON u.id = v.registrado_por
            WHERE v.acolhido_id = ?
            ORDER BY v.inicio DESC
            """,
            (resident_id,),
        )
    )


@bp.post("/acolhidos/<int:resident_id>/visitas")
@auth_required("admin", "technical", "staff")
def create_visit(resident_id: int):
    if ensure_resident(resident_id) is None:
        return error("Acolhido não encontrado.", status=404)
    data = get_json()
    require_fields(data, ["inicio"])
    db = get_db()
    from flask import g

    cursor = db.execute(
        """
        INSERT INTO visitas (
            acolhido_id, familiar_id, registrado_por, tipo, inicio, fim, observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resident_id, data.get("familiar_id"), g.current_user["id"], data.get("tipo"),
            data["inicio"], data.get("fim"), data.get("observacoes"),
        ),
    )
    visit_id = int(cursor.lastrowid)
    audit_log("CRIAR", "visitas", visit_id, {"acolhido_id": resident_id})
    db.commit()
    return success(fetch_one("SELECT * FROM visitas WHERE id = ?", (visit_id,)), message="Visita registrada.", status=201)


@bp.put("/visitas/<int:visit_id>")
@auth_required("admin", "technical", "staff")
def update_visit(visit_id: int):
    if fetch_one("SELECT id FROM visitas WHERE id = ?", (visit_id,)) is None:
        return error("Visita não encontrada.", status=404)
    data = get_json()
    dynamic_update("visitas", visit_id, data, {"familiar_id", "tipo", "inicio", "fim", "observacoes"})
    audit_log("ATUALIZAR", "visitas", visit_id)
    get_db().commit()
    return success(fetch_one("SELECT * FROM visitas WHERE id = ?", (visit_id,)), message="Visita atualizada.")


@bp.delete("/visitas/<int:visit_id>")
@auth_required("admin", "technical")
def delete_visit(visit_id: int):
    db = get_db()
    cursor = db.execute("DELETE FROM visitas WHERE id = ?", (visit_id,))
    if cursor.rowcount == 0:
        return error("Visita não encontrada.", status=404)
    audit_log("EXCLUIR", "visitas", visit_id)
    db.commit()
    return success(message="Visita excluída.")
