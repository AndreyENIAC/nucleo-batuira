"""API Flask acadêmica do Núcleo Batuíra.

Versão de MVP: somente as rotas necessárias para o frontend atual.
As consultas SQL aparecem diretamente nas rotas para facilitar o estudo.
"""

from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from database import BASE_DIR, get_connection


app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "chave-academica-batuira-2026-com-mais-de-32-caracteres"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
JWTManager(app)

PASTA_UPLOADS = BASE_DIR / "uploads"
PASTA_UPLOADS.mkdir(exist_ok=True)
EXTENSOES_PERMITIDAS = {"pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def resposta_erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


def calcular_idade(data_nascimento):
    try:
        nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
        hoje = datetime.now().date()
        return hoje.year - nascimento.year - (
            (hoje.month, hoje.day) < (nascimento.month, nascimento.day)
        )
    except (TypeError, ValueError):
        return None


def arquivo_permitido(nome):
    return "." in nome and nome.rsplit(".", 1)[1].lower() in EXTENSOES_PERMITIDAS


def usuario_atual_id():
    return int(get_jwt_identity())


@app.errorhandler(404)
def rota_nao_encontrada(_erro):
    return resposta_erro("Rota não encontrada.", 404)


@app.errorhandler(413)
def upload_muito_grande(_erro):
    return resposta_erro("O arquivo ultrapassa o limite de 10 MB.", 413)


# ============================================================
# INÍCIO E LOGIN
# ============================================================

@app.get("/")
def inicio():
    return jsonify({"mensagem": "API do Núcleo Batuíra funcionando."})


@app.post("/api/login")
def login():
    dados = request.get_json(silent=True) or {}
    username = str(dados.get("username", "")).strip()
    senha = str(dados.get("senha", ""))

    if not username or not senha:
        return resposta_erro("Informe o usuário e a senha.")

    with get_connection() as conn:
        usuario = conn.execute(
            """
            SELECT u.id, u.nome, u.username, u.senha_hash, u.ativo,
                   p.codigo AS perfil, p.nome AS nome_perfil
            FROM usuarios u
            JOIN perfis_acesso p ON p.id = u.perfil_id
            WHERE u.username = ?
            """,
            (username,),
        ).fetchone()

        if usuario is None or not usuario["ativo"]:
            return resposta_erro("Usuário ou senha incorretos.", 401)

        if not check_password_hash(usuario["senha_hash"], senha):
            return resposta_erro("Usuário ou senha incorretos.", 401)

        conn.execute(
            "UPDATE usuarios SET ultimo_login = CURRENT_TIMESTAMP WHERE id = ?",
            (usuario["id"],),
        )
        conn.commit()

    token = create_access_token(identity=str(usuario["id"]))

    return jsonify(
        {
            "mensagem": "Login realizado com sucesso.",
            "access_token": token,
            "usuario": {
                "id": usuario["id"],
                "nome": usuario["nome"],
                "username": usuario["username"],
                "perfil": usuario["perfil"],
                "nome_perfil": usuario["nome_perfil"],
            },
        }
    )


@app.get("/api/me")
@jwt_required()
def meus_dados():
    with get_connection() as conn:
        usuario = conn.execute(
            """
            SELECT u.id, u.nome, u.username, u.email, u.profissao,
                   u.registro_profissional,
                   p.codigo AS perfil, p.nome AS nome_perfil
            FROM usuarios u
            JOIN perfis_acesso p ON p.id = u.perfil_id
            WHERE u.id = ?
            """,
            (usuario_atual_id(),),
        ).fetchone()

    if usuario is None:
        return resposta_erro("Usuário não encontrado.", 404)
    return jsonify(dict(usuario))


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/api/dashboard")
@jwt_required()
def dashboard():
    with get_connection() as conn:
        total_acolhidos = conn.execute(
            "SELECT COUNT(*) FROM acolhidos WHERE status != 'inativo'"
        ).fetchone()[0]

        criticos = conn.execute(
            "SELECT COUNT(*) FROM acolhidos WHERE status = 'critico'"
        ).fetchone()[0]

        usuarios_ativos = conn.execute(
            "SELECT COUNT(*) FROM usuarios WHERE ativo = 1"
        ).fetchone()[0]

        gastos_mes = conn.execute(
            """
            SELECT COALESCE(SUM(valor), 0)
            FROM gastos
            WHERE strftime('%Y-%m', data_gasto) = strftime('%Y-%m', 'now')
            """
        ).fetchone()[0]

        receitas_mes = conn.execute(
            """
            SELECT COALESCE(SUM(valor), 0)
            FROM receitas
            WHERE strftime('%Y-%m', data_recebimento) = strftime('%Y-%m', 'now')
            """
        ).fetchone()[0]

        eventos = conn.execute(
            """
            SELECT e.id, e.titulo, e.tipo, e.inicio, e.local,
                   a.nome AS acolhido
            FROM eventos_agenda e
            LEFT JOIN acolhidos a ON a.id = e.acolhido_id
            ORDER BY datetime(e.inicio)
            LIMIT 5
            """
        ).fetchall()

        alertas = conn.execute(
            """
            SELECT al.id, al.tipo, al.severidade, al.mensagem,
                   a.nome AS acolhido
            FROM alertas al
            LEFT JOIN acolhidos a ON a.id = al.acolhido_id
            WHERE al.status IN ('aberto', 'em_tratamento')
            ORDER BY al.id DESC
            LIMIT 5
            """
        ).fetchall()

    return jsonify(
        {
            "total_acolhidos": total_acolhidos,
            "acolhidos_criticos": criticos,
            "usuarios_ativos": usuarios_ativos,
            "gastos_mes": float(gastos_mes),
            "receitas_mes": float(receitas_mes),
            "saldo_mes": float(receitas_mes) - float(gastos_mes),
            "agenda": [dict(evento) for evento in eventos],
            "alertas": [dict(alerta) for alerta in alertas],
        }
    )


# ============================================================
# ACOLHIDOS
# ============================================================

@app.get("/api/acolhidos")
@jwt_required()
def listar_acolhidos():
    busca = request.args.get("busca", "").strip()
    status = request.args.get("status", "").strip()

    sql = """
        SELECT a.*,
               (SELECT d.descricao
                FROM diagnosticos d
                WHERE d.acolhido_id = a.id
                  AND d.principal = 1
                  AND d.ativo = 1
                LIMIT 1) AS condicao_principal,
               (SELECT e.inicio
                FROM eventos_agenda e
                WHERE e.acolhido_id = a.id
                  AND lower(e.tipo) LIKE '%consulta%'
                ORDER BY datetime(e.inicio) DESC
                LIMIT 1) AS ultima_consulta
        FROM acolhidos a
        WHERE a.status != 'inativo'
    """
    parametros = []

    if busca:
        sql += " AND a.nome LIKE ?"
        parametros.append(f"%{busca}%")

    if status:
        sql += " AND a.status = ?"
        parametros.append(status)

    sql += " ORDER BY a.nome"

    with get_connection() as conn:
        linhas = conn.execute(sql, parametros).fetchall()

    acolhidos = []
    for linha in linhas:
        acolhido = dict(linha)
        acolhido["idade"] = calcular_idade(acolhido["data_nascimento"])
        acolhidos.append(acolhido)

    return jsonify(acolhidos)


@app.get("/api/acolhidos/<int:acolhido_id>")
@jwt_required()
def buscar_acolhido(acolhido_id):
    with get_connection() as conn:
        linha = conn.execute(
            "SELECT * FROM acolhidos WHERE id = ?", (acolhido_id,)
        ).fetchone()

        if linha is None:
            return resposta_erro("Acolhido não encontrado.", 404)

        acolhido = dict(linha)
        acolhido["idade"] = calcular_idade(acolhido["data_nascimento"])

        diagnostico = conn.execute(
            """
            SELECT descricao, cid, data_diagnostico
            FROM diagnosticos
            WHERE acolhido_id = ? AND principal = 1 AND ativo = 1
            LIMIT 1
            """,
            (acolhido_id,),
        ).fetchone()

        contato = conn.execute(
            """
            SELECT id, nome, parentesco, telefone, email,
                   responsavel_legal, contato_principal
            FROM familiares
            WHERE acolhido_id = ? AND ativo = 1
            ORDER BY contato_principal DESC
            LIMIT 1
            """,
            (acolhido_id,),
        ).fetchone()

        alergias = conn.execute(
            """
            SELECT a.nome, aa.gravidade
            FROM acolhido_alergias aa
            JOIN alergias a ON a.id = aa.alergia_id
            WHERE aa.acolhido_id = ?
            ORDER BY a.nome
            """,
            (acolhido_id,),
        ).fetchall()

        sinais = conn.execute(
            """
            SELECT * FROM sinais_vitais
            WHERE acolhido_id = ?
            ORDER BY datetime(medido_em) DESC
            LIMIT 1
            """,
            (acolhido_id,),
        ).fetchone()

    acolhido["diagnostico_principal"] = dict(diagnostico) if diagnostico else None
    acolhido["contato_principal"] = dict(contato) if contato else None
    acolhido["alergias"] = [dict(item) for item in alergias]
    acolhido["sinais_vitais"] = dict(sinais) if sinais else None

    return jsonify(acolhido)


@app.post("/api/acolhidos")
@jwt_required()
def cadastrar_acolhido():
    dados = request.get_json(silent=True) or {}

    campos_obrigatorios = [
        "nome",
        "data_nascimento",
        "modalidade_acolhimento",
        "data_admissao",
    ]

    if any(not dados.get(campo) for campo in campos_obrigatorios):
        return resposta_erro(
            "Preencha nome, data de nascimento, modalidade e data de admissão."
        )

    with get_connection() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO acolhidos (
                    nome, data_nascimento, cpf, rg, sexo,
                    modalidade_acolhimento, data_admissao,
                    ala, quarto, status, tipo_atendimento,
                    convenio, endereco, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dados["nome"],
                    dados["data_nascimento"],
                    dados.get("cpf") or None,
                    dados.get("rg") or None,
                    dados.get("sexo") or None,
                    dados["modalidade_acolhimento"],
                    dados["data_admissao"],
                    dados.get("ala") or None,
                    dados.get("quarto") or None,
                    dados.get("status", "estavel"),
                    dados.get("tipo_atendimento") or None,
                    dados.get("convenio") or None,
                    dados.get("endereco") or None,
                    dados.get("observacoes") or None,
                ),
            )

            acolhido_id = cursor.lastrowid

            if dados.get("condicao_principal"):
                conn.execute(
                    """
                    INSERT INTO diagnosticos (
                        acolhido_id, registrado_por, descricao,
                        data_diagnostico, principal, ativo
                    ) VALUES (?, ?, ?, ?, 1, 1)
                    """,
                    (
                        acolhido_id,
                        usuario_atual_id(),
                        dados["condicao_principal"],
                        dados["data_admissao"],
                    ),
                )

            conn.commit()

        except Exception as erro:
            if "UNIQUE constraint failed: acolhidos.cpf" in str(erro):
                return resposta_erro("Já existe um acolhido com este CPF.", 409)
            return resposta_erro("Não foi possível cadastrar o acolhido.")

    return jsonify({"mensagem": "Acolhido cadastrado.", "id": acolhido_id}), 201


@app.put("/api/acolhidos/<int:acolhido_id>")
@jwt_required()
def atualizar_acolhido(acolhido_id):
    dados = request.get_json(silent=True) or {}

    campos = {
        "nome": dados.get("nome"),
        "data_nascimento": dados.get("data_nascimento"),
        "cpf": dados.get("cpf"),
        "rg": dados.get("rg"),
        "sexo": dados.get("sexo"),
        "modalidade_acolhimento": dados.get("modalidade_acolhimento"),
        "data_admissao": dados.get("data_admissao"),
        "ala": dados.get("ala"),
        "quarto": dados.get("quarto"),
        "status": dados.get("status"),
        "tipo_atendimento": dados.get("tipo_atendimento"),
        "convenio": dados.get("convenio"),
        "endereco": dados.get("endereco"),
        "observacoes": dados.get("observacoes"),
    }

    campos = {nome: valor for nome, valor in campos.items() if valor is not None}

    if not campos:
        return resposta_erro("Nenhum campo foi enviado para atualização.")

    partes_sql = ", ".join(f"{nome} = ?" for nome in campos)
    valores = list(campos.values()) + [acolhido_id]

    with get_connection() as conn:
        cursor = conn.execute(
            f"""
            UPDATE acolhidos
            SET {partes_sql}, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            valores,
        )

        if cursor.rowcount == 0:
            return resposta_erro("Acolhido não encontrado.", 404)

        if dados.get("condicao_principal"):
            conn.execute(
                "UPDATE diagnosticos SET principal = 0 WHERE acolhido_id = ?",
                (acolhido_id,),
            )
            conn.execute(
                """
                INSERT INTO diagnosticos (
                    acolhido_id, registrado_por, descricao,
                    data_diagnostico, principal, ativo
                ) VALUES (?, ?, ?, date('now'), 1, 1)
                """,
                (acolhido_id, usuario_atual_id(), dados["condicao_principal"]),
            )

        conn.commit()

    return jsonify({"mensagem": "Acolhido atualizado."})


# ============================================================
# FAMILIARES
# ============================================================

@app.get("/api/acolhidos/<int:acolhido_id>/familiares")
@jwt_required()
def listar_familiares(acolhido_id):
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT * FROM familiares
            WHERE acolhido_id = ? AND ativo = 1
            ORDER BY contato_principal DESC, nome
            """,
            (acolhido_id,),
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/acolhidos/<int:acolhido_id>/familiares")
@jwt_required()
def cadastrar_familiar(acolhido_id):
    dados = request.get_json(silent=True) or {}

    if not dados.get("nome") or not dados.get("parentesco"):
        return resposta_erro("Informe o nome e o parentesco.")

    with get_connection() as conn:
        acolhido = conn.execute(
            "SELECT id FROM acolhidos WHERE id = ?", (acolhido_id,)
        ).fetchone()

        if acolhido is None:
            return resposta_erro("Acolhido não encontrado.", 404)

        if dados.get("contato_principal"):
            conn.execute(
                "UPDATE familiares SET contato_principal = 0 WHERE acolhido_id = ?",
                (acolhido_id,),
            )

        cursor = conn.execute(
            """
            INSERT INTO familiares (
                acolhido_id, nome, parentesco, telefone, email,
                contato_principal, responsavel_legal,
                autorizado_visita, frequencia_visita, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                acolhido_id,
                dados["nome"],
                dados["parentesco"],
                dados.get("telefone"),
                dados.get("email"),
                int(bool(dados.get("contato_principal"))),
                int(bool(dados.get("responsavel_legal"))),
                int(dados.get("autorizado_visita", 1)),
                dados.get("frequencia_visita"),
                dados.get("observacoes"),
            ),
        )
        conn.commit()

    return jsonify({"mensagem": "Familiar cadastrado.", "id": cursor.lastrowid}), 201


# ============================================================
# PRESCRIÇÕES E NOTAS CLÍNICAS
# ============================================================

@app.get("/api/acolhidos/<int:acolhido_id>/prescricoes")
@jwt_required()
def listar_prescricoes(acolhido_id):
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT p.*, u.nome AS profissional,
                   u.registro_profissional
            FROM prescricoes p
            JOIN usuarios u ON u.id = p.prescrito_por
            WHERE p.acolhido_id = ?
            ORDER BY date(p.data_inicio) DESC, p.id DESC
            """,
            (acolhido_id,),
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/acolhidos/<int:acolhido_id>/prescricoes")
@jwt_required()
def cadastrar_prescricao(acolhido_id):
    dados = request.get_json(silent=True) or {}

    obrigatorios = ["tipo_prescricao", "medicamento", "posologia", "data_inicio"]
    if any(not dados.get(campo) for campo in obrigatorios):
        return resposta_erro("Preencha tipo, medicamento, posologia e data de início.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO prescricoes (
                acolhido_id, prescrito_por, tipo_prescricao,
                medicamento, dosagem, via_administracao,
                frequencia, posologia, data_inicio,
                data_fim, status, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                acolhido_id,
                usuario_atual_id(),
                dados["tipo_prescricao"],
                dados["medicamento"],
                dados.get("dosagem"),
                dados.get("via_administracao"),
                dados.get("frequencia"),
                dados["posologia"],
                dados["data_inicio"],
                dados.get("data_fim"),
                dados.get("status", "ativa"),
                dados.get("observacoes"),
            ),
        )
        conn.commit()

    return jsonify({"mensagem": "Prescrição cadastrada.", "id": cursor.lastrowid}), 201


@app.get("/api/acolhidos/<int:acolhido_id>/notas")
@jwt_required()
def listar_notas(acolhido_id):
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT n.*, u.nome AS profissional,
                   u.profissao, u.registro_profissional
            FROM notas_clinicas n
            JOIN usuarios u ON u.id = n.profissional_id
            WHERE n.acolhido_id = ?
            ORDER BY datetime(n.registrado_em) DESC
            """,
            (acolhido_id,),
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/acolhidos/<int:acolhido_id>/notas")
@jwt_required()
def cadastrar_nota(acolhido_id):
    dados = request.get_json(silent=True) or {}

    if not dados.get("tipo") or not dados.get("conteudo"):
        return resposta_erro("Informe o tipo e o conteúdo da nota.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO notas_clinicas (
                acolhido_id, profissional_id, tipo, conteudo
            ) VALUES (?, ?, ?, ?)
            """,
            (acolhido_id, usuario_atual_id(), dados["tipo"], dados["conteudo"]),
        )
        conn.commit()

    return jsonify({"mensagem": "Nota clínica cadastrada.", "id": cursor.lastrowid}), 201


# ============================================================
# PIA, PTS E PLANO DE ALTA — CONSULTA DO MVP
# ============================================================

@app.get("/api/acolhidos/<int:acolhido_id>/pias")
@jwt_required()
def listar_pias(acolhido_id):
    with get_connection() as conn:
        pias = conn.execute(
            """
            SELECT p.*, u.nome AS criado_por_nome
            FROM pias p
            JOIN usuarios u ON u.id = p.criado_por
            WHERE p.acolhido_id = ?
            ORDER BY date(p.data_elaboracao) DESC
            """,
            (acolhido_id,),
        ).fetchall()

        resultado = []
        for pia in pias:
            item = dict(pia)
            metas = conn.execute(
                """
                SELECT m.*, u.nome AS responsavel_nome
                FROM pia_metas m
                LEFT JOIN usuarios u ON u.id = m.responsavel_id
                WHERE m.pia_id = ?
                ORDER BY m.id
                """,
                (pia["id"],),
            ).fetchall()
            item["metas"] = [dict(meta) for meta in metas]
            resultado.append(item)

    return jsonify(resultado)


@app.get("/api/acolhidos/<int:acolhido_id>/pts")
@jwt_required()
def listar_pts(acolhido_id):
    with get_connection() as conn:
        lista_pts = conn.execute(
            """
            SELECT p.*, u.nome AS criado_por_nome
            FROM pts p
            JOIN usuarios u ON u.id = p.criado_por
            WHERE p.acolhido_id = ?
            ORDER BY date(p.data_reuniao) DESC
            """,
            (acolhido_id,),
        ).fetchall()

        resultado = []
        for pts in lista_pts:
            item = dict(pts)
            intervencoes = conn.execute(
                """
                SELECT i.*, u.nome AS responsavel_nome
                FROM pts_intervencoes i
                LEFT JOIN usuarios u ON u.id = i.responsavel_id
                WHERE i.pts_id = ?
                ORDER BY i.id
                """,
                (pts["id"],),
            ).fetchall()
            item["intervencoes"] = [dict(intervencao) for intervencao in intervencoes]
            resultado.append(item)

    return jsonify(resultado)


@app.get("/api/acolhidos/<int:acolhido_id>/planos-alta")
@jwt_required()
def listar_planos_alta(acolhido_id):
    with get_connection() as conn:
        planos = conn.execute(
            """
            SELECT p.*, u.nome AS coordenador_nome
            FROM planos_alta p
            JOIN usuarios u ON u.id = p.coordenador_id
            WHERE p.acolhido_id = ?
            ORDER BY p.id DESC
            """,
            (acolhido_id,),
        ).fetchall()

        resultado = []
        for plano in planos:
            item = dict(plano)
            etapas = conn.execute(
                """
                SELECT * FROM plano_alta_etapas
                WHERE plano_alta_id = ?
                ORDER BY ordem
                """,
                (plano["id"],),
            ).fetchall()
            item["etapas"] = [dict(etapa) for etapa in etapas]
            resultado.append(item)

    return jsonify(resultado)


# ============================================================
# DOCUMENTOS
# ============================================================

@app.get("/api/documentos")
@jwt_required()
def listar_documentos():
    acolhido_id = request.args.get("acolhido_id", type=int)
    escopo = request.args.get("escopo", "").strip()

    sql = """
        SELECT d.*, a.nome AS acolhido, u.nome AS enviado_por_nome
        FROM documentos d
        LEFT JOIN acolhidos a ON a.id = d.acolhido_id
        JOIN usuarios u ON u.id = d.enviado_por
        WHERE 1 = 1
    """
    parametros = []

    if acolhido_id:
        sql += " AND d.acolhido_id = ?"
        parametros.append(acolhido_id)

    if escopo:
        sql += " AND d.escopo = ?"
        parametros.append(escopo)

    sql += " ORDER BY datetime(d.enviado_em) DESC"

    with get_connection() as conn:
        linhas = conn.execute(sql, parametros).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/documentos")
@jwt_required()
def enviar_documento():
    arquivo = request.files.get("arquivo")
    titulo = request.form.get("titulo", "").strip()
    categoria = request.form.get("categoria", "").strip()
    escopo = request.form.get("escopo", "acolhido").strip()
    acolhido_id = request.form.get("acolhido_id", type=int)

    if arquivo is None or not arquivo.filename:
        return resposta_erro("Selecione um arquivo.")

    if not titulo or not categoria:
        return resposta_erro("Informe o título e a categoria.")

    if escopo == "acolhido" and not acolhido_id:
        return resposta_erro("Informe o acolhido relacionado.")

    if escopo not in {"acolhido", "institucional"}:
        return resposta_erro("Escopo inválido.")

    if not arquivo_permitido(arquivo.filename):
        return resposta_erro("Tipo de arquivo não permitido.")

    nome_original = secure_filename(arquivo.filename)
    nome_salvo = f"{uuid4().hex}_{nome_original}"
    caminho = PASTA_UPLOADS / nome_salvo
    arquivo.save(caminho)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO documentos (
                acolhido_id, enviado_por, escopo, titulo,
                categoria, nome_original, caminho_arquivo,
                mime_type, tamanho_bytes, data_validade, descricao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                acolhido_id if escopo == "acolhido" else None,
                usuario_atual_id(),
                escopo,
                titulo,
                categoria,
                nome_original,
                nome_salvo,
                arquivo.mimetype,
                caminho.stat().st_size,
                request.form.get("data_validade") or None,
                request.form.get("descricao") or None,
            ),
        )
        conn.commit()

    return jsonify({"mensagem": "Documento enviado.", "id": cursor.lastrowid}), 201


@app.get("/api/documentos/<int:documento_id>/download")
@jwt_required()
def baixar_documento(documento_id):
    with get_connection() as conn:
        documento = conn.execute(
            "SELECT nome_original, caminho_arquivo FROM documentos WHERE id = ?",
            (documento_id,),
        ).fetchone()

    if documento is None:
        return resposta_erro("Documento não encontrado.", 404)

    return send_from_directory(
        PASTA_UPLOADS,
        documento["caminho_arquivo"],
        as_attachment=True,
        download_name=documento["nome_original"],
    )


# ============================================================
# FINANCEIRO
# ============================================================

@app.get("/api/categorias-financeiras")
@jwt_required()
def listar_categorias_financeiras():
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT * FROM categorias_financeiras
            WHERE ativo = 1
            ORDER BY tipo, nome
            """
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.get("/api/gastos")
@jwt_required()
def listar_gastos():
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT g.*, c.nome AS categoria,
                   a.nome AS acolhido,
                   u.nome AS registrado_por_nome
            FROM gastos g
            JOIN categorias_financeiras c ON c.id = g.categoria_id
            LEFT JOIN acolhidos a ON a.id = g.acolhido_id
            JOIN usuarios u ON u.id = g.registrado_por
            ORDER BY date(g.data_gasto) DESC, g.id DESC
            """
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/gastos")
@jwt_required()
def cadastrar_gasto():
    dados = request.get_json(silent=True) or {}
    obrigatorios = ["categoria_id", "descricao", "valor", "data_gasto"]

    if any(dados.get(campo) in (None, "") for campo in obrigatorios):
        return resposta_erro("Preencha categoria, descrição, valor e data.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO gastos (
                acolhido_id, categoria_id, registrado_por,
                descricao, valor, data_gasto,
                fornecedor, status, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dados.get("acolhido_id"),
                dados["categoria_id"],
                usuario_atual_id(),
                dados["descricao"],
                dados["valor"],
                dados["data_gasto"],
                dados.get("fornecedor"),
                dados.get("status", "registrado"),
                dados.get("observacoes"),
            ),
        )
        conn.commit()

    return jsonify({"mensagem": "Gasto cadastrado.", "id": cursor.lastrowid}), 201


@app.get("/api/prestacoes-contas")
@jwt_required()
def listar_prestacoes():
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT p.*,
                   (SELECT COALESCE(SUM(g.valor), 0)
                    FROM gastos g
                    WHERE strftime('%Y-%m', g.data_gasto) = p.competencia) AS total_gastos,
                   (SELECT COALESCE(SUM(r.valor), 0)
                    FROM receitas r
                    WHERE strftime('%Y-%m', r.data_recebimento) = p.competencia) AS total_receitas
            FROM prestacoes_contas p
            ORDER BY p.competencia DESC
            """
        ).fetchall()

    resultado = []
    for linha in linhas:
        item = dict(linha)
        item["saldo"] = float(item["total_receitas"]) - float(item["total_gastos"])
        resultado.append(item)

    return jsonify(resultado)


@app.get("/api/recursos-administrativos")
@jwt_required()
def listar_recursos_administrativos():
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT r.*, u.nome AS criado_por_nome
            FROM recursos_administrativos r
            JOIN usuarios u ON u.id = r.criado_por
            ORDER BY r.nome
            """
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


# ============================================================
# BENEFÍCIOS — CONSULTA DO MÓDULO FINANCEIRO
# ============================================================

@app.get("/api/beneficios")
@jwt_required()
def listar_beneficios():
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT b.*, a.nome AS acolhido
            FROM beneficios b
            JOIN acolhidos a ON a.id = b.acolhido_id
            ORDER BY a.nome, b.tipo_beneficio
            """
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


# ============================================================
# AGENDA
# ============================================================

@app.get("/api/agenda")
@jwt_required()
def listar_agenda():
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT e.*, a.nome AS acolhido,
                   u.nome AS responsavel_nome
            FROM eventos_agenda e
            LEFT JOIN acolhidos a ON a.id = e.acolhido_id
            LEFT JOIN usuarios u ON u.id = e.responsavel_id
            ORDER BY datetime(e.inicio)
            """
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


if __name__ == "__main__":
    app.run(debug=True)
