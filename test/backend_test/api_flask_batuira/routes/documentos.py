from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, g, request, send_file
from werkzeug.utils import secure_filename

from database import fetch_all, fetch_one, get_db
from responses import error, success
from security import auth_required
from utils import audit_log, dynamic_update, get_json, pagination, require_fields

bp = Blueprint("documentos", __name__)

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "csv", "txt", "jpg", "jpeg", "png"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def serialize_document(row: dict) -> dict:
    result = dict(row)
    result["url_download"] = f"/api/documentos/{result['id']}/download"
    return result


@bp.get("/documentos")
@auth_required("admin", "technical", "financial")
def list_documents():
    limit, offset = pagination()
    conditions = []
    params: list = []
    for field in ("acolhido_id", "escopo", "categoria", "status"):
        value = request.args.get(field)
        if value not in (None, ""):
            conditions.append(f"d.{field} = ?")
            params.append(value)
    search = request.args.get("busca", "").strip()
    if search:
        conditions.append("(lower(d.titulo) LIKE lower(?) OR lower(d.nome_original) LIKE lower(?))")
        term = f"%{search}%"; params.extend([term, term])
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    total = fetch_one("SELECT COUNT(*) AS total FROM documentos d" + where, params)["total"]
    rows = fetch_all(
        """SELECT d.*,a.nome AS acolhido_nome,u.nome AS enviado_por_nome
        FROM documentos d
        LEFT JOIN acolhidos a ON a.id=d.acolhido_id
        JOIN usuarios u ON u.id=d.enviado_por""" + where + " ORDER BY d.enviado_em DESC LIMIT ? OFFSET ?",
        [*params, limit, offset],
    )
    return success({"itens":[serialize_document(r) for r in rows],"total":total,"limit":limit,"offset":offset})


@bp.get("/acolhidos/<int:resident_id>/documentos")
@auth_required("admin", "technical", "financial")
def list_resident_documents(resident_id:int):
    rows=fetch_all("""SELECT d.*,u.nome AS enviado_por_nome FROM documentos d
    JOIN usuarios u ON u.id=d.enviado_por WHERE d.acolhido_id=? ORDER BY d.enviado_em DESC""",(resident_id,))
    return success([serialize_document(r) for r in rows])


@bp.get("/documentos/<int:document_id>")
@auth_required("admin", "technical", "financial")
def get_document(document_id:int):
    row=fetch_one("SELECT * FROM documentos WHERE id=?",(document_id,))
    if row is None:return error("Documento não encontrado.",status=404)
    return success(serialize_document(row))


@bp.post("/documentos")
@auth_required("admin", "technical", "financial")
def upload_document():
    if "arquivo" not in request.files:
        return error("Envie o arquivo no campo 'arquivo'.",status=400)
    file=request.files["arquivo"]
    if not file.filename:return error("Nenhum arquivo selecionado.",status=400)
    if not allowed_file(file.filename):return error("Tipo de arquivo não permitido.",status=400)

    title=request.form.get("titulo") or Path(file.filename).stem
    category=request.form.get("categoria")
    scope=request.form.get("escopo")
    if not category or scope not in {"acolhido","institucional"}:
        return error("Informe categoria e escopo válido.",status=400)
    resident_id=request.form.get("acolhido_id") or None
    if scope=="acolhido" and not resident_id:return error("Documento de acolhido exige acolhido_id.",status=400)
    if scope=="institucional":resident_id=None

    original=secure_filename(file.filename)
    ext=Path(original).suffix.lower()
    stored=f"{uuid4().hex}{ext}"
    target=Path(current_app.config["UPLOAD_FOLDER"])/stored
    file.save(target)
    size=target.stat().st_size
    mime=file.mimetype or mimetypes.guess_type(original)[0]

    db=get_db()
    try:
        cur=db.execute("""INSERT INTO documentos
        (acolhido_id,enviado_por,escopo,titulo,categoria,nome_original,caminho_arquivo,
         mime_type,tamanho_bytes,data_validade,status,descricao)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (resident_id,g.current_user["id"],scope,title,category,original,stored,mime,size,
         request.form.get("data_validade") or None,request.form.get("status","ativo"),request.form.get("descricao") or None))
        document_id=int(cur.lastrowid);audit_log("CRIAR","documentos",document_id,{"arquivo":original});db.commit()
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return success(serialize_document(fetch_one("SELECT * FROM documentos WHERE id=?",(document_id,))),message="Documento enviado.",status=201)


@bp.get("/documentos/<int:document_id>/download")
@auth_required("admin", "technical", "financial")
def download_document(document_id:int):
    row=fetch_one("SELECT * FROM documentos WHERE id=?",(document_id,))
    if row is None:return error("Documento não encontrado.",status=404)
    path=Path(current_app.config["UPLOAD_FOLDER"])/row["caminho_arquivo"]
    if not path.exists():return error("Arquivo físico não encontrado no servidor.",status=404)
    return send_file(path,as_attachment=True,download_name=row["nome_original"],mimetype=row["mime_type"])


@bp.put("/documentos/<int:document_id>")
@auth_required("admin", "technical", "financial")
def update_document(document_id:int):
    if fetch_one("SELECT id FROM documentos WHERE id=?",(document_id,)) is None:return error("Documento não encontrado.",status=404)
    data=get_json();dynamic_update("documentos",document_id,data,{"titulo","categoria","data_validade","status","descricao"})
    audit_log("ATUALIZAR","documentos",document_id);get_db().commit()
    return success(serialize_document(fetch_one("SELECT * FROM documentos WHERE id=?",(document_id,))))


@bp.delete("/documentos/<int:document_id>")
@auth_required("admin")
def delete_document(document_id:int):
    row=fetch_one("SELECT * FROM documentos WHERE id=?",(document_id,))
    if row is None:return error("Documento não encontrado.",status=404)
    db=get_db();db.execute("DELETE FROM documentos WHERE id=?",(document_id,));audit_log("EXCLUIR","documentos",document_id);db.commit()
    (Path(current_app.config["UPLOAD_FOLDER"])/row["caminho_arquivo"]).unlink(missing_ok=True)
    return success(message="Documento excluído.")


# Recursos administrativos
@bp.get("/recursos-administrativos")
@auth_required("admin", "financial")
def list_admin_resources():
    return success(fetch_all("""SELECT r.*,d.titulo AS documento_titulo,u.nome AS criado_por_nome
    FROM recursos_administrativos r LEFT JOIN documentos d ON d.id=r.documento_id
    JOIN usuarios u ON u.id=r.criado_por ORDER BY r.data_validade,r.nome"""))


@bp.post("/recursos-administrativos")
@auth_required("admin", "financial")
def create_admin_resource():
    data=get_json();require_fields(data,["nome","tipo","status"]);db=get_db()
    cur=db.execute("""INSERT INTO recursos_administrativos
    (documento_id,criado_por,nome,tipo,numero_documento,orgao_emissor,data_emissao,data_validade,status,observacoes)
    VALUES(?,?,?,?,?,?,?,?,?,?)""",
    (data.get("documento_id"),g.current_user["id"],data["nome"],data["tipo"],data.get("numero_documento"),
     data.get("orgao_emissor"),data.get("data_emissao"),data.get("data_validade"),data["status"],data.get("observacoes")))
    rid=int(cur.lastrowid);audit_log("CRIAR","recursos_administrativos",rid);db.commit()
    return success(fetch_one("SELECT * FROM recursos_administrativos WHERE id=?",(rid,)),status=201)


@bp.put("/recursos-administrativos/<int:record_id>")
@auth_required("admin", "financial")
def update_admin_resource(record_id:int):
    if fetch_one("SELECT id FROM recursos_administrativos WHERE id=?",(record_id,)) is None:return error("Recurso não encontrado.",status=404)
    data=get_json();dynamic_update("recursos_administrativos",record_id,data,
        {"documento_id","nome","tipo","numero_documento","orgao_emissor","data_emissao","data_validade","status","observacoes"})
    audit_log("ATUALIZAR","recursos_administrativos",record_id);get_db().commit()
    return success(fetch_one("SELECT * FROM recursos_administrativos WHERE id=?",(record_id,)))


@bp.delete("/recursos-administrativos/<int:record_id>")
@auth_required("admin", "financial")
def delete_admin_resource(record_id:int):
    db=get_db();cur=db.execute("DELETE FROM recursos_administrativos WHERE id=?",(record_id,))
    if cur.rowcount==0:return error("Recurso não encontrado.",status=404)
    audit_log("EXCLUIR","recursos_administrativos",record_id);db.commit();return success(message="Recurso excluído.")
