from __future__ import annotations

from flask import Blueprint, g, request

from database import fetch_all, fetch_one, get_db
from responses import error, success
from security import auth_required
from utils import as_bool_int, audit_log, dynamic_update, get_json, require_fields

bp = Blueprint("clinico", __name__)


def resident_exists(resident_id: int) -> bool:
    return fetch_one("SELECT id FROM acolhidos WHERE id = ?", (resident_id,)) is not None


# Diagnósticos
@bp.get("/acolhidos/<int:resident_id>/diagnosticos")
@auth_required("admin", "technical")
def list_diagnoses(resident_id: int):
    if not resident_exists(resident_id):
        return error("Acolhido não encontrado.", status=404)
    return success(fetch_all(
        """
        SELECT d.*, u.nome AS registrado_por_nome
        FROM diagnosticos d JOIN usuarios u ON u.id=d.registrado_por
        WHERE d.acolhido_id=? ORDER BY d.principal DESC, d.data_diagnostico DESC, d.id DESC
        """, (resident_id,)
    ))


@bp.post("/acolhidos/<int:resident_id>/diagnosticos")
@auth_required("admin", "technical")
def create_diagnosis(resident_id: int):
    if not resident_exists(resident_id):
        return error("Acolhido não encontrado.", status=404)
    data = get_json(); require_fields(data, ["descricao"])
    db = get_db()
    cur = db.execute(
        """INSERT INTO diagnosticos
        (acolhido_id, registrado_por, descricao, cid, data_diagnostico, principal, ativo, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (resident_id, g.current_user["id"], data["descricao"], data.get("cid"),
         data.get("data_diagnostico"), as_bool_int(data.get("principal", False)),
         as_bool_int(data.get("ativo", True)), data.get("observacoes"))
    )
    record_id = int(cur.lastrowid); audit_log("CRIAR", "diagnosticos", record_id); db.commit()
    return success(fetch_one("SELECT * FROM diagnosticos WHERE id=?", (record_id,)), message="Diagnóstico registrado.", status=201)


@bp.put("/diagnosticos/<int:record_id>")
@auth_required("admin", "technical")
def update_diagnosis(record_id: int):
    if fetch_one("SELECT id FROM diagnosticos WHERE id=?", (record_id,)) is None:
        return error("Diagnóstico não encontrado.", status=404)
    data = get_json()
    for f in ("principal", "ativo"):
        if f in data: data[f] = as_bool_int(data[f])
    dynamic_update("diagnosticos", record_id, data,
                   {"descricao", "cid", "data_diagnostico", "principal", "ativo", "observacoes"})
    audit_log("ATUALIZAR", "diagnosticos", record_id); get_db().commit()
    return success(fetch_one("SELECT * FROM diagnosticos WHERE id=?", (record_id,)), message="Diagnóstico atualizado.")


@bp.delete("/diagnosticos/<int:record_id>")
@auth_required("admin", "technical")
def delete_diagnosis(record_id: int):
    db=get_db(); cur=db.execute("UPDATE diagnosticos SET ativo=0, principal=0 WHERE id=?", (record_id,))
    if cur.rowcount == 0: return error("Diagnóstico não encontrado.", status=404)
    audit_log("INATIVAR", "diagnosticos", record_id); db.commit(); return success(message="Diagnóstico inativado.")


# Alergias
@bp.get("/alergias")
@auth_required("admin", "technical")
def list_allergies_catalog():
    return success(fetch_all("SELECT * FROM alergias ORDER BY nome"))


@bp.post("/alergias")
@auth_required("admin", "technical")
def create_allergy_catalog():
    data=get_json(); require_fields(data,["nome"]); db=get_db()
    cur=db.execute("INSERT INTO alergias(nome) VALUES (?)", (data["nome"].strip(),)); rid=int(cur.lastrowid)
    audit_log("CRIAR", "alergias", rid); db.commit(); return success(fetch_one("SELECT * FROM alergias WHERE id=?",(rid,)),status=201)


@bp.get("/acolhidos/<int:resident_id>/alergias")
@auth_required("admin", "technical")
def list_resident_allergies(resident_id: int):
    if not resident_exists(resident_id): return error("Acolhido não encontrado.", status=404)
    return success(fetch_all(
        """SELECT aa.*, a.nome, u.nome AS registrado_por_nome
        FROM acolhido_alergias aa JOIN alergias a ON a.id=aa.alergia_id
        JOIN usuarios u ON u.id=aa.registrado_por
        WHERE aa.acolhido_id=? ORDER BY a.nome""", (resident_id,)
    ))


@bp.post("/acolhidos/<int:resident_id>/alergias")
@auth_required("admin", "technical")
def add_resident_allergy(resident_id: int):
    if not resident_exists(resident_id): return error("Acolhido não encontrado.", status=404)
    data=get_json()
    allergy_id=data.get("alergia_id")
    db=get_db()
    if not allergy_id:
        require_fields(data,["nome"])
        row=fetch_one("SELECT id FROM alergias WHERE lower(nome)=lower(?)",(data["nome"].strip(),))
        if row: allergy_id=row["id"]
        else: allergy_id=int(db.execute("INSERT INTO alergias(nome) VALUES (?)",(data["nome"].strip(),)).lastrowid)
    db.execute("""INSERT INTO acolhido_alergias
        (acolhido_id, alergia_id, registrado_por, gravidade, observacoes)
        VALUES (?, ?, ?, ?, ?)""",
        (resident_id, allergy_id, g.current_user["id"], data.get("gravidade"), data.get("observacoes")))
    audit_log("VINCULAR", "acolhido_alergias", None, {"acolhido_id":resident_id,"alergia_id":allergy_id}); db.commit()
    return success(message="Alergia vinculada ao acolhido.", status=201)


@bp.delete("/acolhidos/<int:resident_id>/alergias/<int:allergy_id>")
@auth_required("admin", "technical")
def remove_resident_allergy(resident_id: int, allergy_id: int):
    db=get_db(); cur=db.execute("DELETE FROM acolhido_alergias WHERE acolhido_id=? AND alergia_id=?",(resident_id,allergy_id))
    if cur.rowcount==0: return error("Vínculo de alergia não encontrado.",status=404)
    audit_log("DESVINCULAR", "acolhido_alergias", None, {"acolhido_id":resident_id,"alergia_id":allergy_id}); db.commit()
    return success(message="Alergia removida do acolhido.")


# Sinais vitais
@bp.get("/acolhidos/<int:resident_id>/sinais-vitais")
@auth_required("admin", "technical")
def list_vitals(resident_id: int):
    if not resident_exists(resident_id): return error("Acolhido não encontrado.", status=404)
    return success(fetch_all(
        """SELECT s.*, u.nome AS registrado_por_nome,
        CASE WHEN s.peso_kg IS NOT NULL AND s.altura_m IS NOT NULL AND s.altura_m > 0
             THEN ROUND(s.peso_kg/(s.altura_m*s.altura_m),2) END AS imc
        FROM sinais_vitais s JOIN usuarios u ON u.id=s.registrado_por
        WHERE s.acolhido_id=? ORDER BY s.medido_em DESC""",(resident_id,)
    ))


@bp.post("/acolhidos/<int:resident_id>/sinais-vitais")
@auth_required("admin", "technical")
def create_vitals(resident_id: int):
    if not resident_exists(resident_id): return error("Acolhido não encontrado.", status=404)
    data=get_json(); require_fields(data,["medido_em"])
    fields=["peso_kg","altura_m","pressao_sistolica","pressao_diastolica","frequencia_cardiaca",
            "saturacao_oxigenio","glicemia","temperatura","observacoes"]
    db=get_db(); cur=db.execute(
        """INSERT INTO sinais_vitais
        (acolhido_id, registrado_por, medido_em, peso_kg, altura_m, pressao_sistolica,
         pressao_diastolica, frequencia_cardiaca, saturacao_oxigenio, glicemia, temperatura, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (resident_id,g.current_user["id"],data["medido_em"],*[data.get(f) for f in fields]))
    rid=int(cur.lastrowid); audit_log("CRIAR","sinais_vitais",rid); db.commit()
    return success(fetch_one("SELECT * FROM sinais_vitais WHERE id=?",(rid,)),status=201)


@bp.put("/sinais-vitais/<int:record_id>")
@auth_required("admin", "technical")
def update_vitals(record_id: int):
    if fetch_one("SELECT id FROM sinais_vitais WHERE id=?",(record_id,)) is None: return error("Registro não encontrado.",status=404)
    data=get_json(); dynamic_update("sinais_vitais",record_id,data,
        {"medido_em","peso_kg","altura_m","pressao_sistolica","pressao_diastolica","frequencia_cardiaca",
         "saturacao_oxigenio","glicemia","temperatura","observacoes"})
    audit_log("ATUALIZAR","sinais_vitais",record_id); get_db().commit()
    return success(fetch_one("SELECT * FROM sinais_vitais WHERE id=?",(record_id,)))


@bp.delete("/sinais-vitais/<int:record_id>")
@auth_required("admin", "technical")
def delete_vitals(record_id: int):
    db=get_db(); cur=db.execute("DELETE FROM sinais_vitais WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Registro não encontrado.",status=404)
    audit_log("EXCLUIR","sinais_vitais",record_id);db.commit();return success(message="Registro excluído.")


# Prescrições
@bp.get("/acolhidos/<int:resident_id>/prescricoes")
@auth_required("admin", "technical")
def list_prescriptions(resident_id: int):
    if not resident_exists(resident_id): return error("Acolhido não encontrado.", status=404)
    status=request.args.get("status")
    sql="""SELECT p.*, u.nome AS prescrito_por_nome, u.registro_profissional
           FROM prescricoes p JOIN usuarios u ON u.id=p.prescrito_por WHERE p.acolhido_id=?"""
    params=[resident_id]
    if status: sql+=" AND p.status=?";params.append(status)
    sql+=" ORDER BY p.data_inicio DESC,p.id DESC"
    rows=fetch_all(sql,params)
    for row in rows:
        row["horarios"]=fetch_all("SELECT * FROM prescricao_horarios WHERE prescricao_id=? ORDER BY horario",(row["id"],))
    return success(rows)


@bp.get("/prescricoes/<int:record_id>")
@auth_required("admin", "technical")
def get_prescription(record_id:int):
    row=fetch_one("SELECT * FROM prescricoes WHERE id=?",(record_id,))
    if row is None:return error("Prescrição não encontrada.",status=404)
    row["horarios"]=fetch_all("SELECT * FROM prescricao_horarios WHERE prescricao_id=? ORDER BY horario",(record_id,))
    return success(row)


@bp.post("/acolhidos/<int:resident_id>/prescricoes")
@auth_required("admin", "technical")
def create_prescription(resident_id:int):
    if not resident_exists(resident_id):return error("Acolhido não encontrado.",status=404)
    data=get_json();require_fields(data,["tipo_prescricao","medicamento","posologia","data_inicio"])
    db=get_db();cur=db.execute("""INSERT INTO prescricoes
      (acolhido_id,prescrito_por,tipo_prescricao,medicamento,dosagem,via_administracao,
       frequencia,posologia,data_inicio,data_fim,status,observacoes)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
      (resident_id,g.current_user["id"],data["tipo_prescricao"],data["medicamento"],data.get("dosagem"),
       data.get("via_administracao"),data.get("frequencia"),data["posologia"],data["data_inicio"],
       data.get("data_fim"),data.get("status","ativa"),data.get("observacoes")))
    rid=int(cur.lastrowid)
    for item in data.get("horarios",[]):
        if isinstance(item,str): item={"horario":item}
        db.execute("INSERT INTO prescricao_horarios(prescricao_id,horario,dose,observacoes) VALUES(?,?,?,?)",
                   (rid,item["horario"],item.get("dose"),item.get("observacoes")))
    audit_log("CRIAR","prescricoes",rid);db.commit();return get_prescription(rid)[0],201


@bp.put("/prescricoes/<int:record_id>")
@auth_required("admin", "technical")
def update_prescription(record_id:int):
    if fetch_one("SELECT id FROM prescricoes WHERE id=?",(record_id,)) is None:return error("Prescrição não encontrada.",status=404)
    data=get_json();dynamic_update("prescricoes",record_id,data,
        {"tipo_prescricao","medicamento","dosagem","via_administracao","frequencia","posologia",
         "data_inicio","data_fim","status","observacoes"})
    audit_log("ATUALIZAR","prescricoes",record_id);get_db().commit();return get_prescription(record_id)


@bp.delete("/prescricoes/<int:record_id>")
@auth_required("admin", "technical")
def close_prescription(record_id:int):
    db=get_db();cur=db.execute("UPDATE prescricoes SET status='encerrada' WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Prescrição não encontrada.",status=404)
    audit_log("ENCERRAR","prescricoes",record_id);db.commit();return success(message="Prescrição encerrada.")


@bp.post("/prescricoes/<int:record_id>/horarios")
@auth_required("admin", "technical")
def add_schedule(record_id:int):
    if fetch_one("SELECT id FROM prescricoes WHERE id=?",(record_id,)) is None:return error("Prescrição não encontrada.",status=404)
    data=get_json();require_fields(data,["horario"]);db=get_db()
    cur=db.execute("INSERT INTO prescricao_horarios(prescricao_id,horario,dose,observacoes) VALUES(?,?,?,?)",
                   (record_id,data["horario"],data.get("dose"),data.get("observacoes")))
    rid=int(cur.lastrowid);audit_log("CRIAR","prescricao_horarios",rid);db.commit()
    return success(fetch_one("SELECT * FROM prescricao_horarios WHERE id=?",(rid,)),status=201)


@bp.delete("/prescricao-horarios/<int:record_id>")
@auth_required("admin", "technical")
def delete_schedule(record_id:int):
    db=get_db();cur=db.execute("DELETE FROM prescricao_horarios WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Horário não encontrado.",status=404)
    audit_log("EXCLUIR","prescricao_horarios",record_id);db.commit();return success(message="Horário removido.")


@bp.get("/acolhidos/<int:resident_id>/administracoes-medicamentos")
@auth_required("admin", "technical")
def list_administrations(resident_id:int):
    date_filter=request.args.get("data")
    sql="""SELECT am.*,ph.horario,ph.dose,p.medicamento,p.posologia,u.nome AS administrado_por_nome
    FROM administracoes_medicamentos am
    JOIN prescricao_horarios ph ON ph.id=am.prescricao_horario_id
    JOIN prescricoes p ON p.id=ph.prescricao_id
    JOIN usuarios u ON u.id=am.administrado_por
    WHERE p.acolhido_id=?""";params=[resident_id]
    if date_filter:sql+=" AND substr(am.previsto_para,1,10)=?";params.append(date_filter)
    sql+=" ORDER BY am.previsto_para DESC"
    return success(fetch_all(sql,params))


@bp.post("/administracoes-medicamentos")
@auth_required("admin", "technical")
def create_administration():
    data=get_json();require_fields(data,["prescricao_horario_id","previsto_para","status"]);db=get_db()
    cur=db.execute("""INSERT INTO administracoes_medicamentos
    (prescricao_horario_id,administrado_por,previsto_para,administrado_em,status,observacoes)
    VALUES(?,?,?,?,?,?)""",
    (data["prescricao_horario_id"],g.current_user["id"],data["previsto_para"],data.get("administrado_em"),data["status"],data.get("observacoes")))
    rid=int(cur.lastrowid);audit_log("CRIAR","administracoes_medicamentos",rid);db.commit()
    return success(fetch_one("SELECT * FROM administracoes_medicamentos WHERE id=?",(rid,)),status=201)


@bp.put("/administracoes-medicamentos/<int:record_id>")
@auth_required("admin", "technical")
def update_administration(record_id:int):
    if fetch_one("SELECT id FROM administracoes_medicamentos WHERE id=?",(record_id,)) is None:return error("Administração não encontrada.",status=404)
    data=get_json();dynamic_update("administracoes_medicamentos",record_id,data,
        {"previsto_para","administrado_em","status","observacoes"})
    audit_log("ATUALIZAR","administracoes_medicamentos",record_id);get_db().commit()
    return success(fetch_one("SELECT * FROM administracoes_medicamentos WHERE id=?",(record_id,)))


# Notas clínicas
@bp.get("/acolhidos/<int:resident_id>/notas-clinicas")
@auth_required("admin", "technical")
def list_notes(resident_id:int):
    return success(fetch_all("""SELECT n.*,u.nome AS profissional_nome,u.profissao,u.registro_profissional
      FROM notas_clinicas n JOIN usuarios u ON u.id=n.profissional_id
      WHERE n.acolhido_id=? ORDER BY n.registrado_em DESC""",(resident_id,)))


@bp.post("/acolhidos/<int:resident_id>/notas-clinicas")
@auth_required("admin", "technical")
def create_note(resident_id:int):
    if not resident_exists(resident_id):return error("Acolhido não encontrado.",status=404)
    data=get_json();require_fields(data,["tipo","conteudo"]);db=get_db()
    cur=db.execute("INSERT INTO notas_clinicas(acolhido_id,profissional_id,tipo,conteudo) VALUES(?,?,?,?)",
                   (resident_id,g.current_user["id"],data["tipo"],data["conteudo"]))
    rid=int(cur.lastrowid);audit_log("CRIAR","notas_clinicas",rid);db.commit()
    return success(fetch_one("SELECT * FROM notas_clinicas WHERE id=?",(rid,)),status=201)


@bp.put("/notas-clinicas/<int:record_id>")
@auth_required("admin", "technical")
def update_note(record_id:int):
    if fetch_one("SELECT id FROM notas_clinicas WHERE id=?",(record_id,)) is None:return error("Nota não encontrada.",status=404)
    data=get_json();data["atualizado_em"]=data.get("atualizado_em") or __import__('datetime').datetime.now().isoformat()
    dynamic_update("notas_clinicas",record_id,data,{"tipo","conteudo","atualizado_em"})
    audit_log("ATUALIZAR","notas_clinicas",record_id);get_db().commit();return success(fetch_one("SELECT * FROM notas_clinicas WHERE id=?",(record_id,)))


@bp.delete("/notas-clinicas/<int:record_id>")
@auth_required("admin", "technical")
def delete_note(record_id:int):
    db=get_db();cur=db.execute("DELETE FROM notas_clinicas WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Nota não encontrada.",status=404)
    audit_log("EXCLUIR","notas_clinicas",record_id);db.commit();return success(message="Nota excluída.")
