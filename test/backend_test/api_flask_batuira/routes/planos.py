from __future__ import annotations

from flask import Blueprint, g

from database import fetch_all, fetch_one, get_db
from responses import error, success
from security import auth_required
from utils import audit_log, dynamic_update, get_json, require_fields

bp = Blueprint("planos", __name__)


def resident_exists(resident_id: int) -> bool:
    return fetch_one("SELECT id FROM acolhidos WHERE id=?", (resident_id,)) is not None


def pia_payload(pia_id: int) -> dict | None:
    row = fetch_one(
        """SELECT p.*,u.nome AS criado_por_nome FROM pias p
        JOIN usuarios u ON u.id=p.criado_por WHERE p.id=?""", (pia_id,)
    )
    if row:
        row["metas"] = fetch_all(
            """SELECT m.*,u.nome AS responsavel_nome FROM pia_metas m
            LEFT JOIN usuarios u ON u.id=m.responsavel_id
            WHERE m.pia_id=? ORDER BY m.id""", (pia_id,)
        )
    return row


def pts_payload(pts_id: int) -> dict | None:
    row = fetch_one(
        """SELECT p.*,u.nome AS criado_por_nome FROM pts p
        JOIN usuarios u ON u.id=p.criado_por WHERE p.id=?""", (pts_id,)
    )
    if row:
        row["intervencoes"] = fetch_all(
            """SELECT i.*,u.nome AS responsavel_nome FROM pts_intervencoes i
            LEFT JOIN usuarios u ON u.id=i.responsavel_id
            WHERE i.pts_id=? ORDER BY i.id""", (pts_id,)
        )
    return row


def discharge_payload(plan_id: int) -> dict | None:
    row = fetch_one(
        """SELECT p.*,u.nome AS coordenador_nome FROM planos_alta p
        JOIN usuarios u ON u.id=p.coordenador_id WHERE p.id=?""", (plan_id,)
    )
    if row:
        row["etapas"] = fetch_all(
            "SELECT * FROM plano_alta_etapas WHERE plano_alta_id=? ORDER BY ordem", (plan_id,)
        )
    return row


# PIA
@bp.get("/acolhidos/<int:resident_id>/pias")
@auth_required("admin", "technical")
def list_pias(resident_id: int):
    if not resident_exists(resident_id): return error("Acolhido não encontrado.", status=404)
    return success(fetch_all("SELECT * FROM pias WHERE acolhido_id=? ORDER BY data_elaboracao DESC,id DESC",(resident_id,)))


@bp.get("/pias/<int:pia_id>")
@auth_required("admin", "technical")
def get_pia(pia_id: int):
    row=pia_payload(pia_id)
    if row is None:return error("PIA não encontrado.",status=404)
    return success(row)


@bp.post("/acolhidos/<int:resident_id>/pias")
@auth_required("admin", "technical")
def create_pia(resident_id: int):
    if not resident_exists(resident_id): return error("Acolhido não encontrado.", status=404)
    data=get_json();require_fields(data,["versao","situacao_atual","necessidades","data_elaboracao"])
    db=get_db();cur=db.execute("""INSERT INTO pias
    (acolhido_id,criado_por,versao,situacao_atual,necessidades,potencialidades,
     data_elaboracao,data_revisao,status) VALUES(?,?,?,?,?,?,?,?,?)""",
    (resident_id,g.current_user["id"],data["versao"],data["situacao_atual"],data["necessidades"],
     data.get("potencialidades"),data["data_elaboracao"],data.get("data_revisao"),data.get("status","rascunho")))
    pia_id=int(cur.lastrowid)
    for m in data.get("metas",[]):
        require_fields(m,["area","objetivo","acoes","status"])
        db.execute("""INSERT INTO pia_metas
        (pia_id,responsavel_id,area,objetivo,acoes,prazo,progresso,status)
        VALUES(?,?,?,?,?,?,?,?)""",
        (pia_id,m.get("responsavel_id"),m["area"],m["objetivo"],m["acoes"],m.get("prazo"),m.get("progresso",0),m["status"]))
    audit_log("CRIAR","pias",pia_id);db.commit();return success(pia_payload(pia_id),status=201)


@bp.put("/pias/<int:pia_id>")
@auth_required("admin", "technical")
def update_pia(pia_id:int):
    if pia_payload(pia_id) is None:return error("PIA não encontrado.",status=404)
    data=get_json();dynamic_update("pias",pia_id,data,
        {"versao","situacao_atual","necessidades","potencialidades","data_elaboracao","data_revisao","status"})
    audit_log("ATUALIZAR","pias",pia_id);get_db().commit();return success(pia_payload(pia_id))


@bp.post("/pias/<int:pia_id>/metas")
@auth_required("admin", "technical")
def create_pia_goal(pia_id:int):
    if pia_payload(pia_id) is None:return error("PIA não encontrado.",status=404)
    data=get_json();require_fields(data,["area","objetivo","acoes","status"]);db=get_db()
    cur=db.execute("""INSERT INTO pia_metas
    (pia_id,responsavel_id,area,objetivo,acoes,prazo,progresso,status) VALUES(?,?,?,?,?,?,?,?)""",
    (pia_id,data.get("responsavel_id"),data["area"],data["objetivo"],data["acoes"],data.get("prazo"),data.get("progresso",0),data["status"]))
    rid=int(cur.lastrowid);audit_log("CRIAR","pia_metas",rid);db.commit();return success(fetch_one("SELECT * FROM pia_metas WHERE id=?",(rid,)),status=201)


@bp.put("/pia-metas/<int:goal_id>")
@auth_required("admin", "technical")
def update_pia_goal(goal_id:int):
    if fetch_one("SELECT id FROM pia_metas WHERE id=?",(goal_id,)) is None:return error("Meta não encontrada.",status=404)
    data=get_json();dynamic_update("pia_metas",goal_id,data,{"responsavel_id","area","objetivo","acoes","prazo","progresso","status"})
    audit_log("ATUALIZAR","pia_metas",goal_id);get_db().commit();return success(fetch_one("SELECT * FROM pia_metas WHERE id=?",(goal_id,)))


@bp.delete("/pia-metas/<int:goal_id>")
@auth_required("admin", "technical")
def delete_pia_goal(goal_id:int):
    db=get_db();cur=db.execute("DELETE FROM pia_metas WHERE id=?",(goal_id,))
    if cur.rowcount==0:return error("Meta não encontrada.",status=404)
    audit_log("EXCLUIR","pia_metas",goal_id);db.commit();return success(message="Meta excluída.")


# PTS
@bp.get("/acolhidos/<int:resident_id>/pts")
@auth_required("admin", "technical")
def list_pts(resident_id:int):
    if not resident_exists(resident_id):return error("Acolhido não encontrado.",status=404)
    return success(fetch_all("SELECT * FROM pts WHERE acolhido_id=? ORDER BY data_reuniao DESC,id DESC",(resident_id,)))


@bp.get("/pts/<int:pts_id>")
@auth_required("admin", "technical")
def get_pts(pts_id:int):
    row=pts_payload(pts_id)
    if row is None:return error("PTS não encontrado.",status=404)
    return success(row)


@bp.post("/acolhidos/<int:resident_id>/pts")
@auth_required("admin", "technical")
def create_pts(resident_id:int):
    if not resident_exists(resident_id):return error("Acolhido não encontrado.",status=404)
    data=get_json();require_fields(data,["diagnostico_situacao","objetivos_terapeuticos","data_reuniao","status"])
    db=get_db();cur=db.execute("""INSERT INTO pts
    (acolhido_id,criado_por,diagnostico_situacao,objetivos_terapeuticos,avaliacao_equipe,
     observacoes_gerais,data_reuniao,data_revisao,status) VALUES(?,?,?,?,?,?,?,?,?)""",
    (resident_id,g.current_user["id"],data["diagnostico_situacao"],data["objetivos_terapeuticos"],
     data.get("avaliacao_equipe"),data.get("observacoes_gerais"),data["data_reuniao"],data.get("data_revisao"),data["status"]))
    pts_id=int(cur.lastrowid)
    for item in data.get("intervencoes",[]):
        require_fields(item,["especialidade","intervencao"])
        db.execute("""INSERT INTO pts_intervencoes
        (pts_id,responsavel_id,especialidade,responsavel_externo,intervencao,frequencia,status)
        VALUES(?,?,?,?,?,?,?)""",
        (pts_id,item.get("responsavel_id"),item["especialidade"],item.get("responsavel_externo"),item["intervencao"],item.get("frequencia"),item.get("status","ativa")))
    audit_log("CRIAR","pts",pts_id);db.commit();return success(pts_payload(pts_id),status=201)


@bp.put("/pts/<int:pts_id>")
@auth_required("admin", "technical")
def update_pts(pts_id:int):
    if pts_payload(pts_id) is None:return error("PTS não encontrado.",status=404)
    data=get_json();dynamic_update("pts",pts_id,data,
        {"diagnostico_situacao","objetivos_terapeuticos","avaliacao_equipe","observacoes_gerais","data_reuniao","data_revisao","status"})
    audit_log("ATUALIZAR","pts",pts_id);get_db().commit();return success(pts_payload(pts_id))


@bp.post("/pts/<int:pts_id>/intervencoes")
@auth_required("admin", "technical")
def create_intervention(pts_id:int):
    if pts_payload(pts_id) is None:return error("PTS não encontrado.",status=404)
    data=get_json();require_fields(data,["especialidade","intervencao"]);db=get_db()
    cur=db.execute("""INSERT INTO pts_intervencoes
    (pts_id,responsavel_id,especialidade,responsavel_externo,intervencao,frequencia,status)
    VALUES(?,?,?,?,?,?,?)""",
    (pts_id,data.get("responsavel_id"),data["especialidade"],data.get("responsavel_externo"),data["intervencao"],data.get("frequencia"),data.get("status","ativa")))
    rid=int(cur.lastrowid);audit_log("CRIAR","pts_intervencoes",rid);db.commit();return success(fetch_one("SELECT * FROM pts_intervencoes WHERE id=?",(rid,)),status=201)


@bp.put("/pts-intervencoes/<int:item_id>")
@auth_required("admin", "technical")
def update_intervention(item_id:int):
    if fetch_one("SELECT id FROM pts_intervencoes WHERE id=?",(item_id,)) is None:return error("Intervenção não encontrada.",status=404)
    data=get_json();dynamic_update("pts_intervencoes",item_id,data,
        {"responsavel_id","especialidade","responsavel_externo","intervencao","frequencia","status"})
    audit_log("ATUALIZAR","pts_intervencoes",item_id);get_db().commit();return success(fetch_one("SELECT * FROM pts_intervencoes WHERE id=?",(item_id,)))


@bp.delete("/pts-intervencoes/<int:item_id>")
@auth_required("admin", "technical")
def delete_intervention(item_id:int):
    db=get_db();cur=db.execute("DELETE FROM pts_intervencoes WHERE id=?",(item_id,))
    if cur.rowcount==0:return error("Intervenção não encontrada.",status=404)
    audit_log("EXCLUIR","pts_intervencoes",item_id);db.commit();return success(message="Intervenção excluída.")


# Plano de alta
@bp.get("/acolhidos/<int:resident_id>/planos-alta")
@auth_required("admin", "technical")
def list_discharge_plans(resident_id:int):
    if not resident_exists(resident_id):return error("Acolhido não encontrado.",status=404)
    return success(fetch_all("SELECT * FROM planos_alta WHERE acolhido_id=? ORDER BY criado_em DESC",(resident_id,)))


@bp.get("/planos-alta/<int:plan_id>")
@auth_required("admin", "technical")
def get_discharge_plan(plan_id:int):
    row=discharge_payload(plan_id)
    if row is None:return error("Plano de alta não encontrado.",status=404)
    return success(row)


@bp.post("/acolhidos/<int:resident_id>/planos-alta")
@auth_required("admin", "technical")
def create_discharge_plan(resident_id:int):
    if not resident_exists(resident_id):return error("Acolhido não encontrado.",status=404)
    data=get_json();db=get_db();cur=db.execute("""INSERT INTO planos_alta
    (acolhido_id,coordenador_id,previsao_alta,tipo_alta,status,orientacoes)
    VALUES(?,?,?,?,?,?)""",
    (resident_id,data.get("coordenador_id",g.current_user["id"]),data.get("previsao_alta"),data.get("tipo_alta"),data.get("status","planejamento"),data.get("orientacoes")))
    plan_id=int(cur.lastrowid)
    for index,item in enumerate(data.get("etapas",[]),start=1):
        require_fields(item,["descricao"])
        db.execute("""INSERT INTO plano_alta_etapas
        (plano_alta_id,descricao,ordem,status,concluido_em,observacoes) VALUES(?,?,?,?,?,?)""",
        (plan_id,item["descricao"],item.get("ordem",index),item.get("status","pendente"),item.get("concluido_em"),item.get("observacoes")))
    audit_log("CRIAR","planos_alta",plan_id);db.commit();return success(discharge_payload(plan_id),status=201)


@bp.put("/planos-alta/<int:plan_id>")
@auth_required("admin", "technical")
def update_discharge_plan(plan_id:int):
    if discharge_payload(plan_id) is None:return error("Plano de alta não encontrado.",status=404)
    data=get_json();dynamic_update("planos_alta",plan_id,data,{"coordenador_id","previsao_alta","tipo_alta","status","orientacoes"})
    audit_log("ATUALIZAR","planos_alta",plan_id);get_db().commit();return success(discharge_payload(plan_id))


@bp.post("/planos-alta/<int:plan_id>/etapas")
@auth_required("admin", "technical")
def create_discharge_step(plan_id:int):
    if discharge_payload(plan_id) is None:return error("Plano de alta não encontrado.",status=404)
    data=get_json();require_fields(data,["descricao","ordem"]);db=get_db()
    cur=db.execute("""INSERT INTO plano_alta_etapas
    (plano_alta_id,descricao,ordem,status,concluido_em,observacoes) VALUES(?,?,?,?,?,?)""",
    (plan_id,data["descricao"],data["ordem"],data.get("status","pendente"),data.get("concluido_em"),data.get("observacoes")))
    rid=int(cur.lastrowid);audit_log("CRIAR","plano_alta_etapas",rid);db.commit();return success(fetch_one("SELECT * FROM plano_alta_etapas WHERE id=?",(rid,)),status=201)


@bp.put("/plano-alta-etapas/<int:step_id>")
@auth_required("admin", "technical")
def update_discharge_step(step_id:int):
    if fetch_one("SELECT id FROM plano_alta_etapas WHERE id=?",(step_id,)) is None:return error("Etapa não encontrada.",status=404)
    data=get_json();dynamic_update("plano_alta_etapas",step_id,data,{"descricao","ordem","status","concluido_em","observacoes"})
    audit_log("ATUALIZAR","plano_alta_etapas",step_id);get_db().commit();return success(fetch_one("SELECT * FROM plano_alta_etapas WHERE id=?",(step_id,)))


@bp.delete("/plano-alta-etapas/<int:step_id>")
@auth_required("admin", "technical")
def delete_discharge_step(step_id:int):
    db=get_db();cur=db.execute("DELETE FROM plano_alta_etapas WHERE id=?",(step_id,))
    if cur.rowcount==0:return error("Etapa não encontrada.",status=404)
    audit_log("EXCLUIR","plano_alta_etapas",step_id);db.commit();return success(message="Etapa excluída.")
