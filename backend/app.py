"""API Flask acadêmica do Núcleo Batuíra.

Versão de MVP: somente as rotas necessárias para o frontend atual.
As consultas SQL aparecem diretamente nas rotas para facilitar o estudo.
"""

from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
import secrets
import sqlite3
import string
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from database import BASE_DIR, get_connection


app = Flask(__name__)
CORS(app, expose_headers=["Content-Disposition"])

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


def buscar_usuario_atual():
    """Retorna o usuário autenticado com o código do perfil."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT u.id, u.nome, u.username, u.email, u.senha_hash,
                   u.primeiro_acesso, u.ativo,
                   p.codigo AS perfil, p.nome AS nome_perfil
            FROM usuarios u
            JOIN perfis_acesso p ON p.id = u.perfil_id
            WHERE u.id = ?
            """,
            (usuario_atual_id(),),
        ).fetchone()


def permitir_perfis(*perfis_permitidos):
    """Protege uma ação para os perfis informados."""
    def decorator(funcao):
        @wraps(funcao)
        def wrapper(*args, **kwargs):
            usuario = buscar_usuario_atual()

            if usuario is None or not usuario["ativo"]:
                return resposta_erro("Usuário inativo ou não encontrado.", 401)

            if usuario["perfil"] not in perfis_permitidos:
                return resposta_erro("Você não tem permissão para realizar esta ação.", 403)

            return funcao(*args, **kwargs)

        return wrapper
    return decorator


def gerar_senha_temporaria():
    """Gera uma senha temporária simples para o MVP acadêmico."""
    caracteres = string.ascii_letters + string.digits
    parte_aleatoria = "".join(secrets.choice(caracteres) for _ in range(8))
    return "Bat@" + parte_aleatoria


def validar_nova_senha(nova_senha):
    if len(nova_senha) < 8:
        return "A nova senha deve possuir pelo menos 8 caracteres."
    if nova_senha.isalpha() or nova_senha.isdigit():
        return "Use letras e números na nova senha."
    return None


def normalizar_cpf(cpf):
    """Mantém somente os 11 números do CPF para evitar duplicidades por formatação."""
    numeros = "".join(caractere for caractere in str(cpf or "") if caractere.isdigit())
    return numeros


def validar_cpf_simples(cpf):
    """Validação acadêmica: exige 11 dígitos, sem validar os dígitos verificadores."""
    return len(normalizar_cpf(cpf)) == 11


STATUS_ACOLHIDO = {"estavel", "monitoramento", "critico", "alta", "inativo"}
STATUS_PRESCRICAO = {"ativa", "suspensa", "encerrada"}
SEVERIDADES_ALERTA = {"baixa", "media", "alta", "critica"}
SETORES_AGENDA = {"saude", "institucional", "geral"}
STATUS_EVENTO = {"agendado", "concluido", "cancelado"}


def normalizar_data_hora(valor):
    """Converte o valor do input datetime-local para o formato aceito pelo SQLite."""
    texto = str(valor or "").strip().replace("T", " ")
    if not texto:
        return None
    if len(texto) == 16:
        texto += ":00"
    try:
        datetime.strptime(texto, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return texto


def setores_visiveis_agenda(perfil):
    """Define quais setores da agenda cada perfil pode consultar."""
    if perfil in {"admin", "staff"}:
        return ("saude", "institucional", "geral")
    if perfil == "technical":
        return ("saude", "geral")
    if perfil == "financial":
        return ("institucional", "geral")
    return ("geral",)


def pode_alterar_setor_agenda(perfil, setor):
    """Funcionário apenas consulta; cada equipe altera somente seu setor."""
    if perfil == "admin":
        return setor in SETORES_AGENDA
    if perfil == "technical":
        return setor == "saude"
    if perfil == "financial":
        return setor == "institucional"
    return False


ROTAS_LIBERADAS_PRIMEIRO_ACESSO = {
    "/api/login",
    "/api/me",
    "/api/trocar-senha",
    "/api/esqueci-senha",
}


@app.before_request
def bloquear_primeiro_acesso_sem_troca():
    """Impede o uso do sistema antes da troca da senha temporária."""
    if request.method == "OPTIONS" or not request.path.startswith("/api/"):
        return None

    if request.path in ROTAS_LIBERADAS_PRIMEIRO_ACESSO:
        return None

    verify_jwt_in_request(optional=True)
    identidade = get_jwt_identity()

    if identidade is None:
        return None

    with get_connection() as conn:
        usuario = conn.execute(
            "SELECT ativo, primeiro_acesso FROM usuarios WHERE id = ?",
            (int(identidade),),
        ).fetchone()

    if usuario is None or not usuario["ativo"]:
        return jsonify({"erro": "Usuário inativo ou não encontrado."}), 401

    if usuario["primeiro_acesso"]:
        return jsonify(
            {
                "erro": "Troque a senha temporária antes de continuar.",
                "troca_senha_obrigatoria": True,
            }
        ), 403

    return None


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
            SELECT u.id, u.nome, u.username, u.email, u.senha_hash, u.ativo,
                   u.primeiro_acesso,
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
                "email": usuario["email"],
                "primeiro_acesso": bool(usuario["primeiro_acesso"]),
            },
        }
    )


@app.get("/api/me")
@jwt_required()
def meus_dados():
    with get_connection() as conn:
        usuario = conn.execute(
            """
            SELECT u.id, u.nome, u.username, u.email, u.telefone, u.profissao,
                   u.conselho_profissional, u.registro_profissional,
                   u.primeiro_acesso, u.ativo,
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


@app.post("/api/trocar-senha")
@jwt_required()
def trocar_senha():
    dados = request.get_json(silent=True) or {}
    senha_atual = str(dados.get("senha_atual", ""))
    nova_senha = str(dados.get("nova_senha", ""))
    confirmacao = str(dados.get("confirmacao", ""))

    if not senha_atual or not nova_senha or not confirmacao:
        return resposta_erro("Preencha a senha atual, a nova senha e a confirmação.")

    if nova_senha != confirmacao:
        return resposta_erro("A confirmação da senha não confere.")

    erro_senha = validar_nova_senha(nova_senha)
    if erro_senha:
        return resposta_erro(erro_senha)

    with get_connection() as conn:
        usuario = conn.execute(
            "SELECT senha_hash FROM usuarios WHERE id = ? AND ativo = 1",
            (usuario_atual_id(),),
        ).fetchone()

        if usuario is None:
            return resposta_erro("Usuário não encontrado.", 404)

        if not check_password_hash(usuario["senha_hash"], senha_atual):
            return resposta_erro("A senha atual está incorreta.", 401)

        if check_password_hash(usuario["senha_hash"], nova_senha):
            return resposta_erro("A nova senha precisa ser diferente da senha atual.")

        conn.execute(
            """
            UPDATE usuarios
            SET senha_hash = ?, primeiro_acesso = 0,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (generate_password_hash(nova_senha), usuario_atual_id()),
        )
        conn.commit()

    return jsonify({"mensagem": "Senha alterada com sucesso."})


@app.post("/api/esqueci-senha")
def esqueci_senha():
    dados = request.get_json(silent=True) or {}
    identificacao = str(dados.get("identificacao", "")).strip()

    if not identificacao:
        return resposta_erro("Informe seu usuário ou e-mail.")

    with get_connection() as conn:
        usuario = conn.execute(
            """
            SELECT id
            FROM usuarios
            WHERE ativo = 1 AND (username = ? OR lower(email) = lower(?))
            """,
            (identificacao, identificacao),
        ).fetchone()

        if usuario is not None:
            pendente = conn.execute(
                """
                SELECT id
                FROM solicitacoes_recuperacao_senha
                WHERE usuario_id = ? AND status = 'pendente'
                """,
                (usuario["id"],),
            ).fetchone()

            if pendente is None:
                conn.execute(
                    """
                    INSERT INTO solicitacoes_recuperacao_senha (usuario_id)
                    VALUES (?)
                    """,
                    (usuario["id"],),
                )
                conn.commit()

    # A resposta é sempre genérica para não revelar quais contas existem.
    return jsonify(
        {
            "mensagem": (
                "Solicitação registrada. Procure um administrador para receber "
                "uma senha temporária."
            )
        }
    )


# ============================================================
# GERENCIAMENTO DE USUÁRIOS — SOMENTE ADMINISTRADOR
# ============================================================

@app.get("/api/perfis")
@jwt_required()
@permitir_perfis("admin")
def listar_perfis():
    with get_connection() as conn:
        perfis = conn.execute(
            "SELECT id, codigo, nome, descricao FROM perfis_acesso ORDER BY id"
        ).fetchall()
    return jsonify([dict(perfil) for perfil in perfis])


@app.get("/api/usuarios")
@jwt_required()
@permitir_perfis("admin")
def listar_usuarios():
    with get_connection() as conn:
        usuarios = conn.execute(
            """
            SELECT u.id, u.nome, u.username, u.email, u.telefone,
                   u.profissao, u.conselho_profissional,
                   u.registro_profissional, u.primeiro_acesso,
                   u.ativo, u.ultimo_login, u.criado_em,
                   p.codigo AS perfil, p.nome AS nome_perfil,
                   EXISTS (
                       SELECT 1 FROM solicitacoes_recuperacao_senha s
                       WHERE s.usuario_id = u.id AND s.status = 'pendente'
                   ) AS recuperacao_pendente
            FROM usuarios u
            JOIN perfis_acesso p ON p.id = u.perfil_id
            ORDER BY u.ativo DESC, u.nome
            """
        ).fetchall()
    return jsonify([dict(usuario) for usuario in usuarios])


@app.post("/api/usuarios")
@jwt_required()
@permitir_perfis("admin")
def cadastrar_usuario():
    dados = request.get_json(silent=True) or {}
    obrigatorios = ["nome", "username", "perfil"]

    if any(not str(dados.get(campo, "")).strip() for campo in obrigatorios):
        return resposta_erro("Preencha nome, usuário e perfil.")

    senha_temporaria = str(dados.get("senha_temporaria", "")).strip()
    if not senha_temporaria:
        senha_temporaria = gerar_senha_temporaria()

    erro_senha = validar_nova_senha(senha_temporaria)
    if erro_senha:
        return resposta_erro(erro_senha)

    with get_connection() as conn:
        perfil = conn.execute(
            "SELECT id FROM perfis_acesso WHERE codigo = ?",
            (dados["perfil"],),
        ).fetchone()
        if perfil is None:
            return resposta_erro("Perfil inválido.")

        try:
            cursor = conn.execute(
                """
                INSERT INTO usuarios (
                    perfil_id, nome, username, email, senha_hash,
                    telefone, profissao, conselho_profissional,
                    registro_profissional, primeiro_acesso, ativo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
                """,
                (
                    perfil["id"],
                    str(dados["nome"]).strip(),
                    str(dados["username"]).strip(),
                    str(dados.get("email", "")).strip() or None,
                    generate_password_hash(senha_temporaria),
                    str(dados.get("telefone", "")).strip() or None,
                    str(dados.get("profissao", "")).strip() or None,
                    str(dados.get("conselho_profissional", "")).strip() or None,
                    str(dados.get("registro_profissional", "")).strip() or None,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as erro:
            if "usuarios.username" in str(erro):
                return resposta_erro("Este nome de usuário já está em uso.", 409)
            if "usuarios.email" in str(erro):
                return resposta_erro("Este e-mail já está em uso.", 409)
            return resposta_erro("Não foi possível cadastrar o usuário.")

    return jsonify(
        {
            "mensagem": "Usuário cadastrado com senha temporária.",
            "id": cursor.lastrowid,
            "senha_temporaria": senha_temporaria,
        }
    ), 201


@app.put("/api/usuarios/<int:usuario_id>")
@jwt_required()
@permitir_perfis("admin")
def atualizar_usuario(usuario_id):
    dados = request.get_json(silent=True) or {}
    obrigatorios = ["nome", "username", "perfil"]

    if any(not str(dados.get(campo, "")).strip() for campo in obrigatorios):
        return resposta_erro("Preencha nome, usuário e perfil.")

    with get_connection() as conn:
        perfil = conn.execute(
            "SELECT id FROM perfis_acesso WHERE codigo = ?",
            (dados["perfil"],),
        ).fetchone()
        if perfil is None:
            return resposta_erro("Perfil inválido.")

        if usuario_id == usuario_atual_id() and dados["perfil"] != "admin":
            return resposta_erro("Você não pode remover o próprio perfil de administrador.")

        try:
            cursor = conn.execute(
                """
                UPDATE usuarios
                SET perfil_id = ?, nome = ?, username = ?, email = ?,
                    telefone = ?, profissao = ?, conselho_profissional = ?,
                    registro_profissional = ?, atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    perfil["id"],
                    str(dados["nome"]).strip(),
                    str(dados["username"]).strip(),
                    str(dados.get("email", "")).strip() or None,
                    str(dados.get("telefone", "")).strip() or None,
                    str(dados.get("profissao", "")).strip() or None,
                    str(dados.get("conselho_profissional", "")).strip() or None,
                    str(dados.get("registro_profissional", "")).strip() or None,
                    usuario_id,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as erro:
            if "usuarios.username" in str(erro):
                return resposta_erro("Este nome de usuário já está em uso.", 409)
            if "usuarios.email" in str(erro):
                return resposta_erro("Este e-mail já está em uso.", 409)
            return resposta_erro("Não foi possível atualizar o usuário.")

    if cursor.rowcount == 0:
        return resposta_erro("Usuário não encontrado.", 404)

    return jsonify({"mensagem": "Usuário atualizado."})


@app.patch("/api/usuarios/<int:usuario_id>/status")
@jwt_required()
@permitir_perfis("admin")
def alterar_status_usuario(usuario_id):
    dados = request.get_json(silent=True) or {}
    ativo = dados.get("ativo")

    if ativo not in (True, False, 0, 1):
        return resposta_erro("Informe se o usuário ficará ativo ou inativo.")

    if usuario_id == usuario_atual_id() and not bool(ativo):
        return resposta_erro("Você não pode inativar o próprio usuário.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE usuarios
            SET ativo = ?, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (int(bool(ativo)), usuario_id),
        )
        conn.commit()

    if cursor.rowcount == 0:
        return resposta_erro("Usuário não encontrado.", 404)

    return jsonify({"mensagem": "Situação do usuário atualizada."})


@app.post("/api/usuarios/<int:usuario_id>/senha-temporaria")
@jwt_required()
@permitir_perfis("admin")
def redefinir_senha_usuario(usuario_id):
    senha_temporaria = gerar_senha_temporaria()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE usuarios
            SET senha_hash = ?, primeiro_acesso = 1,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ? AND ativo = 1
            """,
            (generate_password_hash(senha_temporaria), usuario_id),
        )
        conn.commit()

    if cursor.rowcount == 0:
        return resposta_erro("Usuário ativo não encontrado.", 404)

    return jsonify(
        {
            "mensagem": "Senha temporária gerada.",
            "senha_temporaria": senha_temporaria,
        }
    )


@app.get("/api/recuperacoes-senha")
@jwt_required()
@permitir_perfis("admin")
def listar_recuperacoes_senha():
    with get_connection() as conn:
        solicitacoes = conn.execute(
            """
            SELECT s.id, s.status, s.solicitado_em, s.resolvido_em,
                   u.id AS usuario_id, u.nome, u.username, u.email
            FROM solicitacoes_recuperacao_senha s
            JOIN usuarios u ON u.id = s.usuario_id
            WHERE s.status = 'pendente'
            ORDER BY datetime(s.solicitado_em)
            """
        ).fetchall()
    return jsonify([dict(item) for item in solicitacoes])


@app.post("/api/recuperacoes-senha/<int:solicitacao_id>/resolver")
@jwt_required()
@permitir_perfis("admin")
def resolver_recuperacao_senha(solicitacao_id):
    senha_temporaria = gerar_senha_temporaria()

    with get_connection() as conn:
        solicitacao = conn.execute(
            """
            SELECT id, usuario_id
            FROM solicitacoes_recuperacao_senha
            WHERE id = ? AND status = 'pendente'
            """,
            (solicitacao_id,),
        ).fetchone()

        if solicitacao is None:
            return resposta_erro("Solicitação pendente não encontrada.", 404)

        conn.execute(
            """
            UPDATE usuarios
            SET senha_hash = ?, primeiro_acesso = 1, ativo = 1,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (generate_password_hash(senha_temporaria), solicitacao["usuario_id"]),
        )
        conn.execute(
            """
            UPDATE solicitacoes_recuperacao_senha
            SET status = 'resolvida', resolvido_por = ?,
                resolvido_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (usuario_atual_id(), solicitacao_id),
        )
        conn.commit()

    return jsonify(
        {
            "mensagem": "Solicitação resolvida com uma senha temporária.",
            "senha_temporaria": senha_temporaria,
        }
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/api/dashboard")
@jwt_required()
def dashboard():
    usuario = buscar_usuario_atual()
    setores = setores_visiveis_agenda(usuario["perfil"])
    marcadores_setores = ", ".join("?" for _ in setores)

    with get_connection() as conn:
        situacao_linhas = conn.execute(
            """
            SELECT status, COUNT(*) AS total
            FROM acolhidos
            GROUP BY status
            """
        ).fetchall()
        situacao = {status: 0 for status in STATUS_ACOLHIDO}
        for linha in situacao_linhas:
            situacao[linha["status"]] = linha["total"]

        total_acolhidos = sum(situacao.values())
        usuarios_ativos = conn.execute(
            "SELECT COUNT(*) FROM usuarios WHERE ativo = 1"
        ).fetchone()[0]

        gastos_mes = conn.execute(
            """
            SELECT COALESCE(SUM(valor), 0)
            FROM gastos
            WHERE strftime('%Y-%m', data_gasto) = strftime('%Y-%m', 'now', 'localtime')
              AND status != 'cancelado'
            """
        ).fetchone()[0]

        receitas_mes = conn.execute(
            """
            SELECT COALESCE(SUM(valor), 0)
            FROM receitas
            WHERE strftime('%Y-%m', data_recebimento) = strftime('%Y-%m', 'now', 'localtime')
              AND status != 'cancelada'
            """
        ).fetchone()[0]

        eventos = conn.execute(
            f"""
            SELECT e.id, e.titulo, e.tipo, e.setor, e.inicio, e.fim,
                   e.local, e.status, a.nome AS acolhido
            FROM eventos_agenda e
            LEFT JOIN acolhidos a ON a.id = e.acolhido_id
            WHERE e.status = 'agendado'
              AND date(e.inicio) >= date('now', 'localtime')
              AND e.setor IN ({marcadores_setores})
            ORDER BY datetime(e.inicio), e.id
            """,
            setores,
        ).fetchall()

        alertas = conn.execute(
            """
            SELECT al.id, al.tipo, al.severidade, al.mensagem, al.criado_em,
                   a.nome AS acolhido
            FROM alertas al
            LEFT JOIN acolhidos a ON a.id = al.acolhido_id
            WHERE al.status IN ('aberto', 'em_tratamento')
              AND (al.acolhido_id IS NULL OR a.status != 'inativo')
            ORDER BY datetime(al.criado_em) DESC, al.id DESC
            """
        ).fetchall()
        total_alertas = conn.execute(
            """
            SELECT COUNT(*)
            FROM alertas al
            LEFT JOIN acolhidos a ON a.id = al.acolhido_id
            WHERE al.status IN ('aberto', 'em_tratamento')
              AND (al.acolhido_id IS NULL OR a.status != 'inativo')
            """
        ).fetchone()[0]

    return jsonify(
        {
            "total_acolhidos": total_acolhidos,
            "usuarios_ativos": usuarios_ativos,
            "gastos_mes": float(gastos_mes),
            "receitas_mes": float(receitas_mes),
            "saldo_mes": float(receitas_mes) - float(gastos_mes),
            "situacao_acolhidos": situacao,
            "agenda": [dict(evento) for evento in eventos],
            "alertas": [dict(alerta) for alerta in alertas],
            "total_alertas_abertos": total_alertas,
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
        WHERE 1 = 1
    """
    parametros = []

    if busca:
        sql += " AND (a.nome LIKE ? OR a.cpf LIKE ?)"
        parametros.extend([f"%{busca}%", f"%{normalizar_cpf(busca)}%"])

    if status:
        if status not in STATUS_ACOLHIDO:
            return resposta_erro("Status de acolhido inválido.")
        sql += " AND a.status = ?"
        parametros.append(status)
    else:
        sql += " AND a.status != 'inativo'"

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
            SELECT a.id, a.nome, aa.gravidade, aa.observacoes, aa.registrado_em
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
@permitir_perfis("admin", "technical")
def cadastrar_acolhido():
    dados = request.get_json(silent=True) or {}

    campos_obrigatorios = [
        "nome",
        "data_nascimento",
        "cpf",
        "data_admissao",
        "status",
    ]

    if any(not str(dados.get(campo, "")).strip() for campo in campos_obrigatorios):
        return resposta_erro(
            "Preencha nome, data de nascimento, CPF, data de admissão e status."
        )

    cpf = normalizar_cpf(dados.get("cpf"))
    if not validar_cpf_simples(cpf):
        return resposta_erro("Informe um CPF com 11 números.")

    status = dados.get("status")
    if status not in STATUS_ACOLHIDO:
        return resposta_erro("Status de acolhido inválido.")

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
                    dados["nome"].strip(),
                    dados["data_nascimento"],
                    cpf,
                    dados.get("rg") or None,
                    dados.get("sexo") or None,
                    "idoso",
                    dados["data_admissao"],
                    dados.get("ala") or None,
                    dados.get("quarto") or None,
                    status,
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
                        dados["condicao_principal"].strip(),
                        dados["data_admissao"],
                    ),
                )

            conn.commit()

        except sqlite3.IntegrityError as erro:
            if "acolhidos.cpf" in str(erro):
                return resposta_erro("Já existe um acolhido com este CPF.", 409)
            return resposta_erro("Não foi possível cadastrar o acolhido.")

    return jsonify({"mensagem": "Acolhido cadastrado.", "id": acolhido_id}), 201


@app.put("/api/acolhidos/<int:acolhido_id>")
@jwt_required()
@permitir_perfis("admin", "technical")
def atualizar_acolhido(acolhido_id):
    dados = request.get_json(silent=True) or {}

    if "cpf" in dados:
        cpf = normalizar_cpf(dados.get("cpf"))
        if not validar_cpf_simples(cpf):
            return resposta_erro("Informe um CPF com 11 números.")
        dados["cpf"] = cpf

    if "status" in dados and dados.get("status") not in STATUS_ACOLHIDO:
        return resposta_erro("Status de acolhido inválido.")

    campos = {
        "nome": dados.get("nome"),
        "data_nascimento": dados.get("data_nascimento"),
        "cpf": dados.get("cpf"),
        "rg": dados.get("rg"),
        "sexo": dados.get("sexo"),
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

    if not campos and not dados.get("condicao_principal"):
        return resposta_erro("Nenhum campo foi enviado para atualização.")

    with get_connection() as conn:
        existente = conn.execute(
            "SELECT id FROM acolhidos WHERE id = ?", (acolhido_id,)
        ).fetchone()
        if existente is None:
            return resposta_erro("Acolhido não encontrado.", 404)

        try:
            if campos:
                partes_sql = ", ".join(f"{nome} = ?" for nome in campos)
                valores = list(campos.values()) + [acolhido_id]
                conn.execute(
                    f"""
                    UPDATE acolhidos
                    SET {partes_sql}, atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    valores,
                )

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
                    (
                        acolhido_id,
                        usuario_atual_id(),
                        dados["condicao_principal"].strip(),
                    ),
                )

            conn.commit()
        except sqlite3.IntegrityError as erro:
            if "acolhidos.cpf" in str(erro):
                return resposta_erro("Já existe um acolhido com este CPF.", 409)
            return resposta_erro("Não foi possível atualizar o acolhido.")

    return jsonify({"mensagem": "Dados do acolhido atualizados."})


@app.patch("/api/acolhidos/<int:acolhido_id>/status")
@jwt_required()
@permitir_perfis("admin", "technical")
def alterar_status_acolhido(acolhido_id):
    dados = request.get_json(silent=True) or {}
    status = dados.get("status")

    if status not in STATUS_ACOLHIDO:
        return resposta_erro("Status de acolhido inválido.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE acolhidos
            SET status = ?,
                data_saida = CASE
                    WHEN ? IN ('alta', 'inativo') THEN COALESCE(data_saida, date('now'))
                    ELSE NULL
                END,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, status, acolhido_id),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Acolhido não encontrado.", 404)
        conn.commit()

    return jsonify({"mensagem": "Status do acolhido atualizado.", "status": status})


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
@permitir_perfis("admin", "technical")
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


@app.delete("/api/familiares/<int:familiar_id>")
@jwt_required()
@permitir_perfis("admin", "technical")
def remover_familiar(familiar_id):
    """Oculta o vínculo familiar sem apagar o histórico do banco."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE familiares SET ativo = 0, contato_principal = 0 WHERE id = ? AND ativo = 1",
            (familiar_id,),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Familiar não encontrado ou já removido.", 404)
        conn.commit()
    return jsonify({"mensagem": "Familiar removido do perfil."})


# ============================================================
# GESTÃO DE SAÚDE: ALERGIAS, PRESCRIÇÕES, NOTAS, PIA, PTS E ALTA
# ============================================================

@app.get("/api/alergias")
@jwt_required()
def listar_catalogo_alergias():
    with get_connection() as conn:
        linhas = conn.execute("SELECT id, nome FROM alergias ORDER BY nome").fetchall()
    return jsonify([dict(linha) for linha in linhas])


@app.get("/api/acolhidos/<int:acolhido_id>/alergias")
@jwt_required()
def listar_alergias_acolhido(acolhido_id):
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT a.id, a.nome, aa.gravidade, aa.observacoes,
                   aa.registrado_em, u.nome AS registrado_por_nome
            FROM acolhido_alergias aa
            JOIN alergias a ON a.id = aa.alergia_id
            JOIN usuarios u ON u.id = aa.registrado_por
            WHERE aa.acolhido_id = ?
            ORDER BY a.nome
            """,
            (acolhido_id,),
        ).fetchall()
    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/acolhidos/<int:acolhido_id>/alergias")
@jwt_required()
@permitir_perfis("admin", "technical")
def cadastrar_alergia_acolhido(acolhido_id):
    dados = request.get_json(silent=True) or {}
    nome = str(dados.get("nome", "")).strip()
    alergia_id = dados.get("alergia_id")

    if not alergia_id and not nome:
        return resposta_erro("Selecione ou informe uma alergia.")

    with get_connection() as conn:
        if conn.execute("SELECT id FROM acolhidos WHERE id = ?", (acolhido_id,)).fetchone() is None:
            return resposta_erro("Acolhido não encontrado.", 404)

        if not alergia_id:
            conn.execute("INSERT OR IGNORE INTO alergias (nome) VALUES (?)", (nome,))
            alergia = conn.execute(
                "SELECT id FROM alergias WHERE lower(nome) = lower(?)", (nome,)
            ).fetchone()
            alergia_id = alergia["id"]

        try:
            conn.execute(
                """
                INSERT INTO acolhido_alergias (
                    acolhido_id, alergia_id, registrado_por, gravidade, observacoes
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    acolhido_id,
                    int(alergia_id),
                    usuario_atual_id(),
                    dados.get("gravidade") or None,
                    dados.get("observacoes") or None,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return resposta_erro("Esta alergia já está vinculada ao acolhido.", 409)

    return jsonify({"mensagem": "Alergia adicionada ao perfil."}), 201


@app.delete("/api/acolhidos/<int:acolhido_id>/alergias/<int:alergia_id>")
@jwt_required()
@permitir_perfis("admin", "technical")
def remover_alergia_acolhido(acolhido_id, alergia_id):
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM acolhido_alergias WHERE acolhido_id = ? AND alergia_id = ?",
            (acolhido_id, alergia_id),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Alergia não encontrada no perfil.", 404)
        conn.commit()
    return jsonify({"mensagem": "Alergia removida do perfil."})


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
            WHERE p.acolhido_id = ? AND p.removida = 0
            ORDER BY CASE p.status WHEN 'ativa' THEN 0 ELSE 1 END,
                     date(p.data_inicio) DESC, p.id DESC
            """,
            (acolhido_id,),
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/acolhidos/<int:acolhido_id>/prescricoes")
@jwt_required()
@permitir_perfis("admin", "technical")
def cadastrar_prescricao(acolhido_id):
    dados = request.get_json(silent=True) or {}

    obrigatorios = ["tipo_prescricao", "medicamento", "posologia", "data_inicio"]
    if any(not dados.get(campo) for campo in obrigatorios):
        return resposta_erro("Preencha tipo, medicamento, posologia e data de início.")

    status = dados.get("status", "ativa")
    if status not in STATUS_PRESCRICAO:
        return resposta_erro("Status de prescrição inválido.")

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
                status,
                dados.get("observacoes"),
            ),
        )
        conn.commit()

    return jsonify({"mensagem": "Prescrição cadastrada.", "id": cursor.lastrowid}), 201


@app.patch("/api/prescricoes/<int:prescricao_id>/status")
@jwt_required()
@permitir_perfis("admin", "technical")
def alterar_status_prescricao(prescricao_id):
    dados = request.get_json(silent=True) or {}
    status = dados.get("status")
    if status not in STATUS_PRESCRICAO:
        return resposta_erro("Status de prescrição inválido.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE prescricoes
            SET status = ?, atualizado_em = CURRENT_TIMESTAMP,
                data_fim = CASE
                    WHEN ? IN ('suspensa', 'encerrada') THEN COALESCE(data_fim, date('now'))
                    ELSE data_fim
                END
            WHERE id = ?
            """,
            (status, status, prescricao_id),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Prescrição não encontrada.", 404)
        conn.commit()

    return jsonify({"mensagem": "Status da prescrição atualizado."})


@app.delete("/api/prescricoes/<int:prescricao_id>")
@jwt_required()
@permitir_perfis("admin", "technical")
def remover_prescricao(prescricao_id):
    """Remove a prescrição da tela, preservando o registro como removido."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE prescricoes
            SET removida = 1, status = 'encerrada',
                data_fim = COALESCE(data_fim, date('now')),
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ? AND removida = 0
            """,
            (prescricao_id,),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Prescrição não encontrada ou já removida.", 404)
        conn.commit()
    return jsonify({"mensagem": "Prescrição removida da visualização."})


@app.get("/api/acolhidos/<int:acolhido_id>/notas")
@jwt_required()
def listar_notas(acolhido_id):
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT n.*, u.nome AS profissional,
                   u.profissao, u.registro_profissional,
                   al.id AS alerta_id, al.status AS alerta_status,
                   al.severidade AS alerta_severidade
            FROM notas_clinicas n
            JOIN usuarios u ON u.id = n.profissional_id
            LEFT JOIN alertas al
              ON al.origem_tipo = 'nota_clinica' AND al.origem_id = n.id
            WHERE n.acolhido_id = ?
            ORDER BY datetime(n.registrado_em) DESC
            """,
            (acolhido_id,),
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/acolhidos/<int:acolhido_id>/notas")
@jwt_required()
@permitir_perfis("admin", "technical")
def cadastrar_nota(acolhido_id):
    dados = request.get_json(silent=True) or {}

    if not dados.get("tipo") or not dados.get("conteudo"):
        return resposta_erro("Informe o tipo e o conteúdo da nota.")

    gerar_alerta = bool(dados.get("gerar_alerta"))
    severidade = dados.get("severidade", "media")
    if gerar_alerta and severidade not in SEVERIDADES_ALERTA:
        return resposta_erro("Severidade de alerta inválida.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO notas_clinicas (
                acolhido_id, profissional_id, tipo, conteudo
            ) VALUES (?, ?, ?, ?)
            """,
            (acolhido_id, usuario_atual_id(), dados["tipo"], dados["conteudo"]),
        )
        nota_id = cursor.lastrowid
        alerta_id = None

        if gerar_alerta:
            resumo = dados["conteudo"].strip()
            if len(resumo) > 180:
                resumo = resumo[:177] + "..."
            alerta_cursor = conn.execute(
                """
                INSERT INTO alertas (
                    acolhido_id, criado_por, tipo, severidade,
                    mensagem, status, origem_tipo, origem_id
                ) VALUES (?, ?, 'nota_clinica', ?, ?, 'aberto', 'nota_clinica', ?)
                """,
                (acolhido_id, usuario_atual_id(), severidade, resumo, nota_id),
            )
            alerta_id = alerta_cursor.lastrowid

        conn.commit()

    return jsonify(
        {"mensagem": "Nota clínica cadastrada.", "id": nota_id, "alerta_id": alerta_id}
    ), 201


@app.patch("/api/alertas/<int:alerta_id>/resolver")
@jwt_required()
@permitir_perfis("admin", "technical")
def resolver_alerta(alerta_id):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE alertas
            SET status = 'resolvido', resolvido_por = ?, resolvido_em = CURRENT_TIMESTAMP
            WHERE id = ? AND status != 'resolvido'
            """,
            (usuario_atual_id(), alerta_id),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Alerta não encontrado ou já resolvido.", 404)
        conn.commit()
    return jsonify({"mensagem": "Alerta marcado como resolvido."})


# ------------------------------------------------------------
# PIA
# ------------------------------------------------------------

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


@app.post("/api/acolhidos/<int:acolhido_id>/pias")
@jwt_required()
@permitir_perfis("admin", "technical")
def cadastrar_pia(acolhido_id):
    dados = request.get_json(silent=True) or {}
    obrigatorios = ["versao", "situacao_atual", "necessidades", "data_elaboracao"]
    if any(not dados.get(campo) for campo in obrigatorios):
        return resposta_erro("Preencha versão, situação, necessidades e data de elaboração.")

    with get_connection() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO pias (
                    acolhido_id, criado_por, versao, situacao_atual,
                    necessidades, potencialidades, data_elaboracao,
                    data_revisao, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    acolhido_id, usuario_atual_id(), dados["versao"],
                    dados["situacao_atual"], dados["necessidades"],
                    dados.get("potencialidades"), dados["data_elaboracao"],
                    dados.get("data_revisao"), dados.get("status", "ativo"),
                ),
            )
            pia_id = cursor.lastrowid
            meta = dados.get("meta_inicial") or {}
            if meta.get("area") and meta.get("objetivo") and meta.get("acoes"):
                conn.execute(
                    """
                    INSERT INTO pia_metas (
                        pia_id, responsavel_id, area, objetivo, acoes,
                        prazo, progresso, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pia_id, usuario_atual_id(), meta["area"], meta["objetivo"],
                        meta["acoes"], meta.get("prazo"), int(meta.get("progresso", 0)),
                        meta.get("status", "em_andamento"),
                    ),
                )
            conn.commit()
        except sqlite3.IntegrityError:
            return resposta_erro("Já existe um PIA com esta versão para o acolhido.", 409)

    return jsonify({"mensagem": "PIA cadastrado.", "id": pia_id}), 201


@app.post("/api/pias/<int:pia_id>/metas")
@jwt_required()
@permitir_perfis("admin", "technical")
def cadastrar_meta_pia(pia_id):
    dados = request.get_json(silent=True) or {}
    if any(not dados.get(campo) for campo in ["area", "objetivo", "acoes"]):
        return resposta_erro("Preencha área, objetivo e ações da meta.")

    progresso = int(dados.get("progresso", 0))
    if progresso < 0 or progresso > 100:
        return resposta_erro("O progresso deve ficar entre 0 e 100.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pia_metas (
                pia_id, responsavel_id, area, objetivo, acoes,
                prazo, progresso, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pia_id, usuario_atual_id(), dados["area"], dados["objetivo"],
                dados["acoes"], dados.get("prazo"), progresso,
                dados.get("status", "em_andamento"),
            ),
        )
        conn.commit()
    return jsonify({"mensagem": "Meta adicionada ao PIA.", "id": cursor.lastrowid}), 201


# ------------------------------------------------------------
# PTS
# ------------------------------------------------------------

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


@app.post("/api/acolhidos/<int:acolhido_id>/pts")
@jwt_required()
@permitir_perfis("admin", "technical")
def cadastrar_pts(acolhido_id):
    dados = request.get_json(silent=True) or {}
    obrigatorios = ["diagnostico_situacao", "objetivos_terapeuticos", "data_reuniao", "status"]
    if any(not dados.get(campo) for campo in obrigatorios):
        return resposta_erro("Preencha diagnóstico, objetivos, data da reunião e status.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pts (
                acolhido_id, criado_por, diagnostico_situacao,
                objetivos_terapeuticos, avaliacao_equipe,
                observacoes_gerais, data_reuniao, data_revisao, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                acolhido_id, usuario_atual_id(), dados["diagnostico_situacao"],
                dados["objetivos_terapeuticos"], dados.get("avaliacao_equipe"),
                dados.get("observacoes_gerais"), dados["data_reuniao"],
                dados.get("data_revisao"), dados["status"],
            ),
        )
        pts_id = cursor.lastrowid
        intervencao = dados.get("intervencao_inicial") or {}
        if intervencao.get("especialidade") and intervencao.get("intervencao"):
            conn.execute(
                """
                INSERT INTO pts_intervencoes (
                    pts_id, responsavel_id, especialidade,
                    responsavel_externo, intervencao, frequencia, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pts_id, usuario_atual_id(), intervencao["especialidade"],
                    None, intervencao["intervencao"], intervencao.get("frequencia"),
                    intervencao.get("status", "ativa"),
                ),
            )
        conn.commit()

    return jsonify({"mensagem": "PTS cadastrado.", "id": pts_id}), 201


@app.post("/api/pts/<int:pts_id>/intervencoes")
@jwt_required()
@permitir_perfis("admin", "technical")
def cadastrar_intervencao_pts(pts_id):
    dados = request.get_json(silent=True) or {}
    if not dados.get("especialidade") or not dados.get("intervencao"):
        return resposta_erro("Preencha especialidade e intervenção.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pts_intervencoes (
                pts_id, responsavel_id, especialidade,
                responsavel_externo, intervencao, frequencia, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pts_id, usuario_atual_id(), dados["especialidade"],
                None, dados["intervencao"], dados.get("frequencia"),
                dados.get("status", "ativa"),
            ),
        )
        conn.commit()
    return jsonify({"mensagem": "Intervenção adicionada ao PTS.", "id": cursor.lastrowid}), 201


# ------------------------------------------------------------
# PLANO DE ALTA
# ------------------------------------------------------------

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


@app.post("/api/acolhidos/<int:acolhido_id>/planos-alta")
@jwt_required()
@permitir_perfis("admin", "technical")
def cadastrar_plano_alta(acolhido_id):
    dados = request.get_json(silent=True) or {}
    if not dados.get("previsao_alta") and not dados.get("orientacoes"):
        return resposta_erro("Informe a previsão ou as orientações do plano de alta.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO planos_alta (
                acolhido_id, coordenador_id, previsao_alta,
                tipo_alta, status, orientacoes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                acolhido_id, usuario_atual_id(), dados.get("previsao_alta"),
                dados.get("tipo_alta"), dados.get("status", "planejamento"),
                dados.get("orientacoes"),
            ),
        )
        plano_id = cursor.lastrowid
        etapas = dados.get("etapas") or []
        for ordem, etapa in enumerate(etapas, start=1):
            descricao = str(etapa).strip()
            if descricao:
                conn.execute(
                    """
                    INSERT INTO plano_alta_etapas (plano_alta_id, descricao, ordem)
                    VALUES (?, ?, ?)
                    """,
                    (plano_id, descricao, ordem),
                )
        conn.commit()

    return jsonify({"mensagem": "Plano de alta cadastrado.", "id": plano_id}), 201


@app.patch("/api/planos-alta/<int:plano_id>/concluir")
@jwt_required()
@permitir_perfis("admin", "technical")
def concluir_plano_alta(plano_id):
    with get_connection() as conn:
        plano = conn.execute(
            "SELECT acolhido_id FROM planos_alta WHERE id = ?", (plano_id,)
        ).fetchone()
        if plano is None:
            return resposta_erro("Plano de alta não encontrado.", 404)

        conn.execute(
            """
            UPDATE planos_alta
            SET status = 'concluido', atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (plano_id,),
        )
        conn.execute(
            """
            UPDATE acolhidos
            SET status = 'alta', data_saida = COALESCE(data_saida, date('now')),
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (plano["acolhido_id"],),
        )
        conn.commit()

    return jsonify({"mensagem": "Plano concluído e acolhido marcado como alta."})


@app.patch("/api/planos-alta/<int:plano_id>/cancelar")
@jwt_required()
@permitir_perfis("admin", "technical")
def cancelar_plano_alta(plano_id):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE planos_alta
            SET status = 'cancelado', atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ? AND status NOT IN ('concluido', 'cancelado')
            """,
            (plano_id,),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Plano não encontrado, concluído ou já cancelado.", 404)
        conn.commit()
    return jsonify({"mensagem": "Plano de alta cancelado."})


# ------------------------------------------------------------
# BENEFÍCIOS E AUXÍLIOS
# ------------------------------------------------------------

@app.get("/api/acolhidos/<int:acolhido_id>/beneficios")
@jwt_required()
def listar_beneficios_acolhido(acolhido_id):
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT * FROM beneficios
            WHERE acolhido_id = ? AND status != 'removido'
            ORDER BY CASE status WHEN 'ativo' THEN 0 ELSE 1 END, id DESC
            """,
            (acolhido_id,),
        ).fetchall()
    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/acolhidos/<int:acolhido_id>/beneficios")
@jwt_required()
@permitir_perfis("admin", "technical")
def cadastrar_beneficio(acolhido_id):
    dados = request.get_json(silent=True) or {}
    if not dados.get("tipo_beneficio") or dados.get("valor_mensal") in (None, ""):
        return resposta_erro("Informe o tipo e o valor mensal do benefício.")

    try:
        valor = float(dados["valor_mensal"])
    except (TypeError, ValueError):
        return resposta_erro("Valor mensal inválido.")
    if valor < 0:
        return resposta_erro("O valor mensal não pode ser negativo.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO beneficios (
                acolhido_id, tipo_beneficio, numero_beneficio,
                orgao_pagador, valor_mensal, data_inicio,
                data_fim, status, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                acolhido_id, dados["tipo_beneficio"], dados.get("numero_beneficio"),
                dados.get("orgao_pagador"), valor, dados.get("data_inicio"),
                dados.get("data_fim"), dados.get("status", "ativo"),
                dados.get("observacoes"),
            ),
        )
        conn.commit()
    return jsonify({"mensagem": "Benefício cadastrado.", "id": cursor.lastrowid}), 201


@app.patch("/api/beneficios/<int:beneficio_id>/status")
@jwt_required()
@permitir_perfis("admin", "technical")
def alterar_status_beneficio(beneficio_id):
    dados = request.get_json(silent=True) or {}
    status = str(dados.get("status", "")).strip()
    if not status:
        return resposta_erro("Informe o status do benefício.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE beneficios
            SET status = ?, data_fim = CASE
                WHEN ? = 'ativo' THEN NULL
                ELSE COALESCE(data_fim, date('now'))
            END
            WHERE id = ?
            """,
            (status, status, beneficio_id),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Benefício não encontrado.", 404)
        conn.commit()
    return jsonify({"mensagem": "Status do benefício atualizado."})


@app.delete("/api/beneficios/<int:beneficio_id>")
@jwt_required()
@permitir_perfis("admin", "technical")
def remover_beneficio(beneficio_id):
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE beneficios SET status = 'removido', data_fim = COALESCE(data_fim, date('now')) WHERE id = ? AND status != 'removido'",
            (beneficio_id,),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Benefício não encontrado ou já removido.", 404)
        conn.commit()
    return jsonify({"mensagem": "Benefício removido da visualização."})


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
        WHERE d.status != 'removido'
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
    usuario = buscar_usuario_atual()
    escopo_informado = request.form.get("escopo", "acolhido").strip()
    perfis_permitidos = (
        {"admin", "technical"}
        if escopo_informado == "acolhido"
        else {"admin", "financial"}
    )
    if usuario is None or usuario["perfil"] not in perfis_permitidos:
        return resposta_erro("Você não tem permissão para enviar este documento.", 403)

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
            """
            SELECT nome_original, caminho_arquivo, mime_type
            FROM documentos WHERE id = ? AND status != 'removido'
            """,
            (documento_id,),
        ).fetchone()

    if documento is None:
        return resposta_erro("Documento não encontrado.", 404)

    caminho = PASTA_UPLOADS / documento["caminho_arquivo"]
    if not caminho.is_file():
        return resposta_erro(
            "O cadastro do documento existe, mas o arquivo físico não foi encontrado. "
            "Envie o documento novamente.",
            404,
        )

    return send_from_directory(
        PASTA_UPLOADS,
        documento["caminho_arquivo"],
        as_attachment=True,
        download_name=documento["nome_original"],
        mimetype=documento["mime_type"] or None,
        conditional=True,
    )


@app.delete("/api/documentos/<int:documento_id>")
@jwt_required()
def remover_documento(documento_id):
    usuario = buscar_usuario_atual()
    with get_connection() as conn:
        documento = conn.execute(
            "SELECT escopo, caminho_arquivo, status FROM documentos WHERE id = ?",
            (documento_id,),
        ).fetchone()
        if documento is None or documento["status"] == "removido":
            return resposta_erro("Documento não encontrado ou já removido.", 404)

        permitidos = {"admin", "technical"} if documento["escopo"] == "acolhido" else {"admin", "financial"}
        if usuario is None or usuario["perfil"] not in permitidos:
            return resposta_erro("Você não tem permissão para remover este documento.", 403)

        conn.execute("UPDATE documentos SET status = 'removido' WHERE id = ?", (documento_id,))
        conn.commit()

    caminho = PASTA_UPLOADS / documento["caminho_arquivo"]
    if caminho.is_file():
        try:
            caminho.unlink()
        except OSError:
            pass

    return jsonify({"mensagem": "Documento removido."})


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


@app.get("/api/receitas")
@jwt_required()
def listar_receitas():
    with get_connection() as conn:
        linhas = conn.execute(
            """
            SELECT r.*, c.nome AS categoria,
                   u.nome AS registrado_por_nome
            FROM receitas r
            LEFT JOIN categorias_financeiras c ON c.id = r.categoria_id
            JOIN usuarios u ON u.id = r.registrado_por
            WHERE r.status != 'cancelada'
            ORDER BY date(r.data_recebimento) DESC, r.id DESC
            """
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/receitas")
@jwt_required()
@permitir_perfis("admin", "financial")
def cadastrar_receita():
    dados = request.get_json(silent=True) or {}
    obrigatorios = ["categoria_id", "descricao", "valor", "data_recebimento"]

    if any(dados.get(campo) in (None, "") for campo in obrigatorios):
        return resposta_erro("Preencha categoria, descrição, valor e data de recebimento.")

    try:
        valor = float(dados["valor"])
    except (TypeError, ValueError):
        return resposta_erro("Informe um valor válido.")

    if valor < 0:
        return resposta_erro("O valor não pode ser negativo.")

    with get_connection() as conn:
        categoria = conn.execute(
            "SELECT id FROM categorias_financeiras WHERE id = ? AND tipo = 'receita' AND ativo = 1",
            (dados["categoria_id"],),
        ).fetchone()
        if categoria is None:
            return resposta_erro("Categoria de receita inválida.")

        cursor = conn.execute(
            """
            INSERT INTO receitas (
                categoria_id, registrado_por, descricao, fonte, valor,
                data_recebimento, status, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dados["categoria_id"],
                usuario_atual_id(),
                str(dados["descricao"]).strip(),
                str(dados.get("fonte") or "").strip() or None,
                valor,
                dados["data_recebimento"],
                dados.get("status", "recebida"),
                str(dados.get("observacoes") or "").strip() or None,
            ),
        )
        conn.commit()

    return jsonify({"mensagem": "Receita cadastrada.", "id": cursor.lastrowid}), 201


@app.delete("/api/receitas/<int:receita_id>")
@jwt_required()
@permitir_perfis("admin", "financial")
def remover_receita(receita_id):
    """Cancela a receita para corrigir lançamentos sem apagar o histórico."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE receitas SET status = 'cancelada' WHERE id = ? AND status != 'cancelada'",
            (receita_id,),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Receita não encontrada ou já removida.", 404)
        conn.commit()
    return jsonify({"mensagem": "Receita removida dos totais e da lista."})


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
            WHERE g.status != 'cancelado'
            ORDER BY date(g.data_gasto) DESC, g.id DESC
            """
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/gastos")
@jwt_required()
@permitir_perfis("admin", "financial")
def cadastrar_gasto():
    dados = request.get_json(silent=True) or {}
    obrigatorios = ["categoria_id", "descricao", "valor", "data_gasto"]

    if any(dados.get(campo) in (None, "") for campo in obrigatorios):
        return resposta_erro("Preencha categoria, descrição, valor e data.")

    try:
        valor = float(dados["valor"])
    except (TypeError, ValueError):
        return resposta_erro("Informe um valor válido.")

    if valor < 0:
        return resposta_erro("O valor não pode ser negativo.")

    with get_connection() as conn:
        categoria = conn.execute(
            "SELECT id FROM categorias_financeiras WHERE id = ? AND tipo = 'despesa' AND ativo = 1",
            (dados["categoria_id"],),
        ).fetchone()
        if categoria is None:
            return resposta_erro("Categoria de gasto inválida.")

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
                str(dados["descricao"]).strip(),
                valor,
                dados["data_gasto"],
                str(dados.get("fornecedor") or "").strip() or None,
                dados.get("status", "registrado"),
                str(dados.get("observacoes") or "").strip() or None,
            ),
        )
        conn.commit()

    return jsonify({"mensagem": "Gasto cadastrado.", "id": cursor.lastrowid}), 201


@app.delete("/api/gastos/<int:gasto_id>")
@jwt_required()
@permitir_perfis("admin", "financial")
def remover_gasto(gasto_id):
    """Cancela o gasto para corrigir lançamentos sem apagar o histórico."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE gastos SET status = 'cancelado' WHERE id = ? AND status != 'cancelado'",
            (gasto_id,),
        )
        if cursor.rowcount == 0:
            return resposta_erro("Gasto não encontrado ou já removido.", 404)
        conn.commit()
    return jsonify({"mensagem": "Gasto removido dos totais e da lista."})


@app.get("/api/prestacoes-contas")
@jwt_required()
def listar_prestacoes():
    with get_connection() as conn:
        competencias = conn.execute(
            """
            SELECT competencia FROM prestacoes_contas
            UNION
            SELECT strftime('%Y-%m', data_gasto) FROM gastos
            WHERE status != 'cancelado'
            UNION
            SELECT strftime('%Y-%m', data_recebimento) FROM receitas
            WHERE status != 'cancelada'
            UNION
            SELECT strftime('%Y-%m', 'now', 'localtime')
            ORDER BY competencia DESC
            """
        ).fetchall()

        resultado = []
        for competencia_linha in competencias:
            competencia = competencia_linha[0]
            if not competencia:
                continue

            prestacao = conn.execute(
                "SELECT id, status, gerado_em, observacoes FROM prestacoes_contas WHERE competencia = ?",
                (competencia,),
            ).fetchone()
            total_gastos = conn.execute(
                """
                SELECT COALESCE(SUM(valor), 0) FROM gastos
                WHERE strftime('%Y-%m', data_gasto) = ? AND status != 'cancelado'
                """,
                (competencia,),
            ).fetchone()[0]
            total_receitas = conn.execute(
                """
                SELECT COALESCE(SUM(valor), 0) FROM receitas
                WHERE strftime('%Y-%m', data_recebimento) = ? AND status != 'cancelada'
                """,
                (competencia,),
            ).fetchone()[0]

            resultado.append(
                {
                    "id": prestacao["id"] if prestacao else None,
                    "competencia": competencia,
                    "status": prestacao["status"] if prestacao else "resumo",
                    "gerado_em": prestacao["gerado_em"] if prestacao else None,
                    "observacoes": prestacao["observacoes"] if prestacao else None,
                    "total_gastos": float(total_gastos),
                    "total_receitas": float(total_receitas),
                    "saldo": float(total_receitas) - float(total_gastos),
                }
            )

    return jsonify(resultado)



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
            WHERE b.status != 'removido'
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
    usuario = buscar_usuario_atual()
    setores_permitidos = setores_visiveis_agenda(usuario["perfil"])
    setor_solicitado = str(request.args.get("setor", "")).strip().lower()
    status_solicitado = str(request.args.get("status", "")).strip().lower()

    setores_consulta = setores_permitidos
    if setor_solicitado:
        if setor_solicitado not in setores_permitidos:
            return resposta_erro("Você não possui acesso a esse setor da agenda.", 403)
        setores_consulta = (setor_solicitado,)

    marcadores = ", ".join("?" for _ in setores_consulta)
    parametros = list(setores_consulta)
    filtro_status = ""
    if status_solicitado:
        if status_solicitado not in STATUS_EVENTO:
            return resposta_erro("Status de evento inválido.")
        filtro_status = " AND e.status = ?"
        parametros.append(status_solicitado)

    with get_connection() as conn:
        linhas = conn.execute(
            f"""
            SELECT e.*, a.nome AS acolhido,
                   u.nome AS responsavel_nome,
                   c.nome AS criado_por_nome
            FROM eventos_agenda e
            LEFT JOIN acolhidos a ON a.id = e.acolhido_id
            LEFT JOIN usuarios u ON u.id = e.responsavel_id
            JOIN usuarios c ON c.id = e.criado_por
            WHERE e.setor IN ({marcadores})
            {filtro_status}
            ORDER BY datetime(e.inicio), e.id
            """,
            parametros,
        ).fetchall()

    return jsonify([dict(linha) for linha in linhas])


@app.post("/api/agenda")
@jwt_required()
@permitir_perfis("admin", "technical", "financial")
def cadastrar_evento():
    dados = request.get_json(silent=True) or {}
    usuario = buscar_usuario_atual()
    setor = str(dados.get("setor", "")).strip().lower()
    inicio = normalizar_data_hora(dados.get("inicio"))
    fim = normalizar_data_hora(dados.get("fim")) if dados.get("fim") else None
    status = str(dados.get("status", "agendado")).strip().lower()

    if not str(dados.get("titulo", "")).strip() or not str(dados.get("tipo", "")).strip():
        return resposta_erro("Informe o título e o tipo do evento.")
    if not inicio:
        return resposta_erro("Informe uma data e horário inicial válidos.")
    if setor not in SETORES_AGENDA:
        return resposta_erro("Setor de agenda inválido.")
    if not pode_alterar_setor_agenda(usuario["perfil"], setor):
        return resposta_erro("Seu perfil não pode cadastrar eventos nesse setor.", 403)
    if status not in STATUS_EVENTO:
        return resposta_erro("Status de evento inválido.")
    if fim and datetime.strptime(fim, "%Y-%m-%d %H:%M:%S") < datetime.strptime(inicio, "%Y-%m-%d %H:%M:%S"):
        return resposta_erro("O término não pode ser anterior ao início.")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO eventos_agenda (
                acolhido_id, responsavel_id, criado_por, titulo, tipo, setor,
                inicio, fim, local, status, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dados.get("acolhido_id"),
                dados.get("responsavel_id") or usuario_atual_id(),
                usuario_atual_id(),
                str(dados["titulo"]).strip(),
                str(dados["tipo"]).strip(),
                setor,
                inicio,
                fim,
                str(dados.get("local") or "").strip() or None,
                status,
                str(dados.get("observacoes") or "").strip() or None,
            ),
        )
        conn.commit()

    return jsonify({"mensagem": "Evento cadastrado.", "id": cursor.lastrowid}), 201


@app.put("/api/agenda/<int:evento_id>")
@jwt_required()
@permitir_perfis("admin", "technical", "financial")
def atualizar_evento(evento_id):
    dados = request.get_json(silent=True) or {}
    usuario = buscar_usuario_atual()

    with get_connection() as conn:
        evento = conn.execute(
            "SELECT * FROM eventos_agenda WHERE id = ?", (evento_id,)
        ).fetchone()
        if evento is None:
            return resposta_erro("Evento não encontrado.", 404)
        if not pode_alterar_setor_agenda(usuario["perfil"], evento["setor"]):
            return resposta_erro("Seu perfil não pode alterar este evento.", 403)

        setor = str(dados.get("setor", evento["setor"])).strip().lower()
        if setor not in SETORES_AGENDA or not pode_alterar_setor_agenda(usuario["perfil"], setor):
            return resposta_erro("Seu perfil não pode mover o evento para esse setor.", 403)

        inicio = normalizar_data_hora(dados.get("inicio", evento["inicio"]))
        fim_bruto = dados.get("fim", evento["fim"])
        fim = normalizar_data_hora(fim_bruto) if fim_bruto else None
        status = str(dados.get("status", evento["status"])).strip().lower()
        titulo = str(dados.get("titulo", evento["titulo"])).strip()
        tipo = str(dados.get("tipo", evento["tipo"])).strip()

        if not titulo or not tipo or not inicio:
            return resposta_erro("Título, tipo e início são obrigatórios.")
        if status not in STATUS_EVENTO:
            return resposta_erro("Status de evento inválido.")
        if fim and datetime.strptime(fim, "%Y-%m-%d %H:%M:%S") < datetime.strptime(inicio, "%Y-%m-%d %H:%M:%S"):
            return resposta_erro("O término não pode ser anterior ao início.")

        conn.execute(
            """
            UPDATE eventos_agenda
            SET acolhido_id = ?, responsavel_id = ?, titulo = ?, tipo = ?,
                setor = ?, inicio = ?, fim = ?, local = ?, status = ?, observacoes = ?
            WHERE id = ?
            """,
            (
                dados.get("acolhido_id", evento["acolhido_id"]),
                dados.get("responsavel_id", evento["responsavel_id"]),
                titulo,
                tipo,
                setor,
                inicio,
                fim,
                str(dados.get("local", evento["local"]) or "").strip() or None,
                status,
                str(dados.get("observacoes", evento["observacoes"]) or "").strip() or None,
                evento_id,
            ),
        )
        conn.commit()

    return jsonify({"mensagem": "Evento atualizado."})


@app.delete("/api/agenda/<int:evento_id>")
@jwt_required()
@permitir_perfis("admin", "technical", "financial")
def excluir_evento(evento_id):
    usuario = buscar_usuario_atual()
    with get_connection() as conn:
        evento = conn.execute(
            "SELECT setor FROM eventos_agenda WHERE id = ?", (evento_id,)
        ).fetchone()
        if evento is None:
            return resposta_erro("Evento não encontrado.", 404)
        if not pode_alterar_setor_agenda(usuario["perfil"], evento["setor"]):
            return resposta_erro("Seu perfil não pode excluir este evento.", 403)
        conn.execute("DELETE FROM eventos_agenda WHERE id = ?", (evento_id,))
        conn.commit()

    return jsonify({"mensagem": "Evento excluído."})


if __name__ == "__main__":
    app.run(debug=True)
