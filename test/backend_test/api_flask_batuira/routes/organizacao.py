from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, g, request

from database import fetch_all, fetch_one, get_db
from responses import error, success
from security import auth_required
from utils import audit_log, dynamic_update, get_json, pagination, require_fields

bp = Blueprint("organizacao", __name__)


@bp.get("/agenda")
@auth_required("admin", "technical", "financial", "staff")
def list_events():
    conditions=[];params=[]
    for field in ("acolhido_id","responsavel_id","tipo","status"):
        value=request.args.get(field)
        if value not in (None,""):conditions.append(f"e.{field}=?");params.append(value)
    if request.args.get("data_inicio"):conditions.append("datetime(e.inicio)>=datetime(?)");params.append(request.args["data_inicio"])
    if request.args.get("data_fim"):conditions.append("datetime(e.inicio)<=datetime(?)");params.append(request.args["data_fim"])
    where=" WHERE "+" AND ".join(conditions) if conditions else ""
    rows=fetch_all("""SELECT e.*,a.nome AS acolhido_nome,r.nome AS responsavel_nome,c.nome AS criado_por_nome
    FROM eventos_agenda e LEFT JOIN acolhidos a ON a.id=e.acolhido_id
    LEFT JOIN usuarios r ON r.id=e.responsavel_id JOIN usuarios c ON c.id=e.criado_por"""+where+" ORDER BY e.inicio",params)
    return success(rows)


@bp.post("/agenda")
@auth_required("admin", "technical", "staff")
def create_event():
    data=get_json();require_fields(data,["titulo","tipo","inicio"]);db=get_db()
    cur=db.execute("""INSERT INTO eventos_agenda
    (acolhido_id,responsavel_id,criado_por,titulo,tipo,inicio,fim,local,status,observacoes)
    VALUES(?,?,?,?,?,?,?,?,?,?)""",
    (data.get("acolhido_id"),data.get("responsavel_id"),g.current_user["id"],data["titulo"],data["tipo"],
     data["inicio"],data.get("fim"),data.get("local"),data.get("status","agendado"),data.get("observacoes")))
    rid=int(cur.lastrowid);audit_log("CRIAR","eventos_agenda",rid);db.commit();return success(fetch_one("SELECT * FROM eventos_agenda WHERE id=?",(rid,)),status=201)


@bp.put("/agenda/<int:record_id>")
@auth_required("admin", "technical", "staff")
def update_event(record_id:int):
    if fetch_one("SELECT id FROM eventos_agenda WHERE id=?",(record_id,)) is None:return error("Evento não encontrado.",status=404)
    data=get_json();dynamic_update("eventos_agenda",record_id,data,{"acolhido_id","responsavel_id","titulo","tipo","inicio","fim","local","status","observacoes"})
    audit_log("ATUALIZAR","eventos_agenda",record_id);get_db().commit();return success(fetch_one("SELECT * FROM eventos_agenda WHERE id=?",(record_id,)))


@bp.delete("/agenda/<int:record_id>")
@auth_required("admin", "technical")
def delete_event(record_id:int):
    db=get_db();cur=db.execute("DELETE FROM eventos_agenda WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Evento não encontrado.",status=404)
    audit_log("EXCLUIR","eventos_agenda",record_id);db.commit();return success(message="Evento excluído.")


@bp.get("/tarefas")
@auth_required("admin", "technical", "financial", "staff")
def list_tasks():
    limit,offset=pagination();conditions=[];params=[]
    user=g.current_user
    if user["perfil_codigo"]=="staff":conditions.append("t.responsavel_id=?");params.append(user["id"])
    elif request.args.get("responsavel_id"):conditions.append("t.responsavel_id=?");params.append(request.args["responsavel_id"])
    for field in ("acolhido_id","prioridade","status"):
        value=request.args.get(field)
        if value not in (None,""):conditions.append(f"t.{field}=?");params.append(value)
    where=" WHERE "+" AND ".join(conditions) if conditions else ""
    total=fetch_one("SELECT COUNT(*) total FROM tarefas t"+where,params)["total"]
    rows=fetch_all("""SELECT t.*,a.nome AS acolhido_nome,r.nome AS responsavel_nome,c.nome AS criado_por_nome
    FROM tarefas t LEFT JOIN acolhidos a ON a.id=t.acolhido_id
    JOIN usuarios r ON r.id=t.responsavel_id JOIN usuarios c ON c.id=t.criado_por"""+where+" ORDER BY CASE t.prioridade WHEN 'urgente' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 ELSE 4 END,t.prazo LIMIT ? OFFSET ?",[*params,limit,offset])
    return success({"itens":rows,"total":total,"limit":limit,"offset":offset})


@bp.post("/tarefas")
@auth_required("admin", "technical")
def create_task():
    data=get_json();require_fields(data,["responsavel_id","titulo"]);db=get_db()
    cur=db.execute("""INSERT INTO tarefas
    (acolhido_id,responsavel_id,criado_por,titulo,descricao,prioridade,prazo,status,concluida_em)
    VALUES(?,?,?,?,?,?,?,?,?)""",
    (data.get("acolhido_id"),data["responsavel_id"],g.current_user["id"],data["titulo"],data.get("descricao"),data.get("prioridade","media"),data.get("prazo"),data.get("status","pendente"),data.get("concluida_em")))
    rid=int(cur.lastrowid);audit_log("CRIAR","tarefas",rid);db.commit();return success(fetch_one("SELECT * FROM tarefas WHERE id=?",(rid,)),status=201)


@bp.put("/tarefas/<int:record_id>")
@auth_required("admin", "technical", "staff")
def update_task(record_id:int):
    row=fetch_one("SELECT * FROM tarefas WHERE id=?",(record_id,))
    if row is None:return error("Tarefa não encontrada.",status=404)
    if g.current_user["perfil_codigo"]=="staff" and row["responsavel_id"]!=g.current_user["id"]:
        return error("Você só pode alterar suas próprias tarefas.",status=403)
    data=get_json()
    if data.get("status")=="concluida" and not data.get("concluida_em"):
        data["concluida_em"]=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    allowed={"status","concluida_em","observacoes"} if g.current_user["perfil_codigo"]=="staff" else {"acolhido_id","responsavel_id","titulo","descricao","prioridade","prazo","status","concluida_em"}
    # "observacoes" não existe na tabela; removemos se veio do staff.
    allowed.discard("observacoes")
    dynamic_update("tarefas",record_id,data,allowed)
    audit_log("ATUALIZAR","tarefas",record_id);get_db().commit();return success(fetch_one("SELECT * FROM tarefas WHERE id=?",(record_id,)))


@bp.delete("/tarefas/<int:record_id>")
@auth_required("admin", "technical")
def delete_task(record_id:int):
    db=get_db();cur=db.execute("DELETE FROM tarefas WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Tarefa não encontrada.",status=404)
    audit_log("EXCLUIR","tarefas",record_id);db.commit();return success(message="Tarefa excluída.")


@bp.get("/alertas")
@auth_required("admin", "technical")
def list_alerts():
    conditions=[];params=[]
    for field in ("acolhido_id","severidade","status","tipo"):
        value=request.args.get(field)
        if value not in (None,""):conditions.append(f"a.{field}=?");params.append(value)
    where=" WHERE "+" AND ".join(conditions) if conditions else ""
    return success(fetch_all("""SELECT a.*,ac.nome AS acolhido_nome,c.nome AS criado_por_nome,r.nome AS resolvido_por_nome
    FROM alertas a LEFT JOIN acolhidos ac ON ac.id=a.acolhido_id
    JOIN usuarios c ON c.id=a.criado_por LEFT JOIN usuarios r ON r.id=a.resolvido_por"""+where+" ORDER BY CASE a.severidade WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 ELSE 4 END,a.criado_em DESC",params))


@bp.post("/alertas")
@auth_required("admin", "technical")
def create_alert():
    data=get_json();require_fields(data,["tipo","severidade","mensagem"]);db=get_db()
    cur=db.execute("""INSERT INTO alertas(acolhido_id,criado_por,tipo,severidade,mensagem,status)
    VALUES(?,?,?,?,?,?)""",
    (data.get("acolhido_id"),g.current_user["id"],data["tipo"],data["severidade"],data["mensagem"],data.get("status","aberto")))
    rid=int(cur.lastrowid);audit_log("CRIAR","alertas",rid);db.commit();return success(fetch_one("SELECT * FROM alertas WHERE id=?",(rid,)),status=201)


@bp.put("/alertas/<int:record_id>")
@auth_required("admin", "technical")
def update_alert(record_id:int):
    if fetch_one("SELECT id FROM alertas WHERE id=?",(record_id,)) is None:return error("Alerta não encontrado.",status=404)
    data=get_json()
    if data.get("status")=="resolvido":
        data.setdefault("resolvido_por",g.current_user["id"])
        data.setdefault("resolvido_em",datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    dynamic_update("alertas",record_id,data,{"acolhido_id","tipo","severidade","mensagem","status","resolvido_por","resolvido_em"})
    audit_log("ATUALIZAR","alertas",record_id);get_db().commit();return success(fetch_one("SELECT * FROM alertas WHERE id=?",(record_id,)))


@bp.get("/logs-auditoria")
@auth_required("admin")
def list_logs():
    limit,offset=pagination(default_limit=100,max_limit=500);conditions=[];params=[]
    if request.args.get("usuario_id"):conditions.append("l.usuario_id=?");params.append(request.args["usuario_id"])
    if request.args.get("tabela"):conditions.append("l.tabela=?");params.append(request.args["tabela"])
    where=" WHERE "+" AND ".join(conditions) if conditions else ""
    return success(fetch_all("""SELECT l.*,u.nome AS usuario_nome FROM logs_auditoria l
    LEFT JOIN usuarios u ON u.id=l.usuario_id"""+where+" ORDER BY l.criado_em DESC LIMIT ? OFFSET ?",[*params,limit,offset]))
