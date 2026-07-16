from __future__ import annotations

from flask import Blueprint, g, request

from database import fetch_all, fetch_one, get_db
from responses import error, success
from security import auth_required
from utils import as_bool_int, audit_log, dynamic_update, get_json, normalize_competence, pagination, require_fields

bp = Blueprint("financeiro", __name__)


@bp.get("/categorias-financeiras")
@auth_required("admin", "financial")
def list_categories():
    return success(fetch_all("SELECT * FROM categorias_financeiras ORDER BY tipo,nome"))


@bp.post("/categorias-financeiras")
@auth_required("admin", "financial")
def create_category():
    data=get_json();require_fields(data,["nome","tipo"]);db=get_db()
    cur=db.execute("INSERT INTO categorias_financeiras(nome,tipo,ativo) VALUES(?,?,?)",
                   (data["nome"],data["tipo"],as_bool_int(data.get("ativo",True))))
    rid=int(cur.lastrowid);audit_log("CRIAR","categorias_financeiras",rid);db.commit()
    return success(fetch_one("SELECT * FROM categorias_financeiras WHERE id=?",(rid,)),status=201)


@bp.put("/categorias-financeiras/<int:record_id>")
@auth_required("admin", "financial")
def update_category(record_id:int):
    if fetch_one("SELECT id FROM categorias_financeiras WHERE id=?",(record_id,)) is None:return error("Categoria não encontrada.",status=404)
    data=get_json()
    if "ativo" in data:data["ativo"]=as_bool_int(data["ativo"])
    dynamic_update("categorias_financeiras",record_id,data,{"nome","tipo","ativo"})
    audit_log("ATUALIZAR","categorias_financeiras",record_id);get_db().commit()
    return success(fetch_one("SELECT * FROM categorias_financeiras WHERE id=?",(record_id,)))


def list_financial(table:str,date_field:str,kind:str):
    limit,offset=pagination();conditions=[];params=[]
    for field in ("acolhido_id","categoria_id","status") if table=="gastos" else ("categoria_id","status"):
        value=request.args.get(field)
        if value not in (None,""):conditions.append(f"f.{field}=?");params.append(value)
    if request.args.get("data_inicio"):conditions.append(f"date(f.{date_field})>=date(?)");params.append(request.args["data_inicio"])
    if request.args.get("data_fim"):conditions.append(f"date(f.{date_field})<=date(?)");params.append(request.args["data_fim"])
    where=" WHERE "+" AND ".join(conditions) if conditions else ""
    total=fetch_one(f"SELECT COUNT(*) total FROM {table} f"+where,params)["total"]
    resident_join="LEFT JOIN acolhidos a ON a.id=f.acolhido_id" if table=="gastos" else ""
    rows=fetch_all(f"""SELECT f.*,c.nome AS categoria_nome,c.tipo AS categoria_tipo,
    u.nome AS registrado_por_nome {',a.nome AS acolhido_nome' if table=='gastos' else ''}
    FROM {table} f JOIN usuarios u ON u.id=f.registrado_por
    LEFT JOIN categorias_financeiras c ON c.id=f.categoria_id {resident_join}
    {where} ORDER BY f.{date_field} DESC,f.id DESC LIMIT ? OFFSET ?""",[*params,limit,offset])
    return success({"itens":rows,"total":total,"limit":limit,"offset":offset,"tipo":kind})


@bp.get("/gastos")
@auth_required("admin", "financial")
def list_expenses():return list_financial("gastos","data_gasto","despesa")


@bp.post("/gastos")
@auth_required("admin", "financial")
def create_expense():
    data=get_json();require_fields(data,["categoria_id","descricao","valor","data_gasto"]);db=get_db()
    cur=db.execute("""INSERT INTO gastos
    (acolhido_id,categoria_id,comprovante_documento_id,registrado_por,descricao,valor,data_gasto,fornecedor,status,observacoes)
    VALUES(?,?,?,?,?,?,?,?,?,?)""",
    (data.get("acolhido_id"),data["categoria_id"],data.get("comprovante_documento_id"),g.current_user["id"],
     data["descricao"],data["valor"],data["data_gasto"],data.get("fornecedor"),data.get("status","registrado"),data.get("observacoes")))
    rid=int(cur.lastrowid);audit_log("CRIAR","gastos",rid);db.commit();return success(fetch_one("SELECT * FROM gastos WHERE id=?",(rid,)),status=201)


@bp.put("/gastos/<int:record_id>")
@auth_required("admin", "financial")
def update_expense(record_id:int):
    if fetch_one("SELECT id FROM gastos WHERE id=?",(record_id,)) is None:return error("Gasto não encontrado.",status=404)
    data=get_json();dynamic_update("gastos",record_id,data,{"acolhido_id","categoria_id","comprovante_documento_id","descricao","valor","data_gasto","fornecedor","status","observacoes"})
    audit_log("ATUALIZAR","gastos",record_id);get_db().commit();return success(fetch_one("SELECT * FROM gastos WHERE id=?",(record_id,)))


@bp.delete("/gastos/<int:record_id>")
@auth_required("admin", "financial")
def delete_expense(record_id:int):
    db=get_db();cur=db.execute("DELETE FROM gastos WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Gasto não encontrado.",status=404)
    audit_log("EXCLUIR","gastos",record_id);db.commit();return success(message="Gasto excluído.")


@bp.get("/receitas")
@auth_required("admin", "financial")
def list_revenues():return list_financial("receitas","data_recebimento","receita")


@bp.post("/receitas")
@auth_required("admin", "financial")
def create_revenue():
    data=get_json();require_fields(data,["descricao","valor","data_recebimento"]);db=get_db()
    cur=db.execute("""INSERT INTO receitas
    (categoria_id,comprovante_documento_id,registrado_por,descricao,fonte,valor,data_recebimento,status,observacoes)
    VALUES(?,?,?,?,?,?,?,?,?)""",
    (data.get("categoria_id"),data.get("comprovante_documento_id"),g.current_user["id"],data["descricao"],data.get("fonte"),data["valor"],data["data_recebimento"],data.get("status","recebida"),data.get("observacoes")))
    rid=int(cur.lastrowid);audit_log("CRIAR","receitas",rid);db.commit();return success(fetch_one("SELECT * FROM receitas WHERE id=?",(rid,)),status=201)


@bp.put("/receitas/<int:record_id>")
@auth_required("admin", "financial")
def update_revenue(record_id:int):
    if fetch_one("SELECT id FROM receitas WHERE id=?",(record_id,)) is None:return error("Receita não encontrada.",status=404)
    data=get_json();dynamic_update("receitas",record_id,data,{"categoria_id","comprovante_documento_id","descricao","fonte","valor","data_recebimento","status","observacoes"})
    audit_log("ATUALIZAR","receitas",record_id);get_db().commit();return success(fetch_one("SELECT * FROM receitas WHERE id=?",(record_id,)))


@bp.delete("/receitas/<int:record_id>")
@auth_required("admin", "financial")
def delete_revenue(record_id:int):
    db=get_db();cur=db.execute("DELETE FROM receitas WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Receita não encontrada.",status=404)
    audit_log("EXCLUIR","receitas",record_id);db.commit();return success(message="Receita excluída.")


def prestation_payload(record:dict)->dict:
    comp=record["competencia"]
    expense=fetch_one("SELECT COALESCE(SUM(valor),0) total FROM gastos WHERE substr(data_gasto,1,7)=?",(comp,))["total"]
    revenue=fetch_one("SELECT COALESCE(SUM(valor),0) total FROM receitas WHERE substr(data_recebimento,1,7)=?",(comp,))["total"]
    record=dict(record);record.update({"total_gastos":expense,"recursos_recebidos":revenue,"saldo":revenue-expense});return record


@bp.get("/prestacoes-contas")
@auth_required("admin", "financial")
def list_prestations():
    rows=fetch_all("""SELECT p.*,u.nome AS gerado_por_nome,a.nome AS aprovado_por_nome
    FROM prestacoes_contas p JOIN usuarios u ON u.id=p.gerado_por
    LEFT JOIN usuarios a ON a.id=p.aprovado_por ORDER BY p.competencia DESC""")
    return success([prestation_payload(r) for r in rows])


@bp.post("/prestacoes-contas")
@auth_required("admin", "financial")
def create_prestation():
    data=get_json();require_fields(data,["competencia","status"]);comp=normalize_competence(data["competencia"]);db=get_db()
    cur=db.execute("""INSERT INTO prestacoes_contas
    (gerado_por,aprovado_por,relatorio_documento_id,competencia,status,aprovado_em,observacoes)
    VALUES(?,?,?,?,?,?,?)""",
    (g.current_user["id"],data.get("aprovado_por"),data.get("relatorio_documento_id"),comp,data["status"],data.get("aprovado_em"),data.get("observacoes")))
    rid=int(cur.lastrowid);audit_log("CRIAR","prestacoes_contas",rid);db.commit();return success(prestation_payload(fetch_one("SELECT * FROM prestacoes_contas WHERE id=?",(rid,))),status=201)


@bp.put("/prestacoes-contas/<int:record_id>")
@auth_required("admin", "financial")
def update_prestation(record_id:int):
    row=fetch_one("SELECT * FROM prestacoes_contas WHERE id=?",(record_id,))
    if row is None:return error("Prestação não encontrada.",status=404)
    data=get_json()
    if "competencia" in data:data["competencia"]=normalize_competence(data["competencia"])
    dynamic_update("prestacoes_contas",record_id,data,{"aprovado_por","relatorio_documento_id","competencia","status","aprovado_em","observacoes"})
    audit_log("ATUALIZAR","prestacoes_contas",record_id);get_db().commit();return success(prestation_payload(fetch_one("SELECT * FROM prestacoes_contas WHERE id=?",(record_id,))))


@bp.delete("/prestacoes-contas/<int:record_id>")
@auth_required("admin", "financial")
def delete_prestation(record_id:int):
    db=get_db();cur=db.execute("DELETE FROM prestacoes_contas WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Prestação não encontrada.",status=404)
    audit_log("EXCLUIR","prestacoes_contas",record_id);db.commit();return success(message="Prestação excluída.")


@bp.get("/beneficios")
@auth_required("admin", "financial")
def list_benefits():
    resident_id=request.args.get("acolhido_id")
    sql="""SELECT b.*,a.nome AS acolhido_nome FROM beneficios b JOIN acolhidos a ON a.id=b.acolhido_id""";params=[]
    if resident_id:sql+=" WHERE b.acolhido_id=?";params.append(resident_id)
    sql+=" ORDER BY a.nome,b.tipo_beneficio"
    return success(fetch_all(sql,params))


@bp.post("/beneficios")
@auth_required("admin", "financial")
def create_benefit():
    data=get_json();require_fields(data,["acolhido_id","tipo_beneficio","valor_mensal","status"]);db=get_db()
    cur=db.execute("""INSERT INTO beneficios
    (acolhido_id,tipo_beneficio,numero_beneficio,orgao_pagador,valor_mensal,data_inicio,data_fim,status,observacoes)
    VALUES(?,?,?,?,?,?,?,?,?)""",
    (data["acolhido_id"],data["tipo_beneficio"],data.get("numero_beneficio"),data.get("orgao_pagador"),data["valor_mensal"],data.get("data_inicio"),data.get("data_fim"),data["status"],data.get("observacoes")))
    rid=int(cur.lastrowid);audit_log("CRIAR","beneficios",rid);db.commit();return success(fetch_one("SELECT * FROM beneficios WHERE id=?",(rid,)),status=201)


@bp.put("/beneficios/<int:record_id>")
@auth_required("admin", "financial")
def update_benefit(record_id:int):
    if fetch_one("SELECT id FROM beneficios WHERE id=?",(record_id,)) is None:return error("Benefício não encontrado.",status=404)
    data=get_json();dynamic_update("beneficios",record_id,data,{"acolhido_id","tipo_beneficio","numero_beneficio","orgao_pagador","valor_mensal","data_inicio","data_fim","status","observacoes"})
    audit_log("ATUALIZAR","beneficios",record_id);get_db().commit();return success(fetch_one("SELECT * FROM beneficios WHERE id=?",(record_id,)))


@bp.delete("/beneficios/<int:record_id>")
@auth_required("admin", "financial")
def delete_benefit(record_id:int):
    db=get_db();cur=db.execute("DELETE FROM beneficios WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Benefício não encontrado.",status=404)
    audit_log("EXCLUIR","beneficios",record_id);db.commit();return success(message="Benefício excluído.")
