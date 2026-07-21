"""Recria o banco e insere dados de demonstração.

Execute:
    python criar_banco.py

Atenção: o arquivo batuira.db existente será apagado.
"""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "batuira.db"
SCHEMA_PATH = BASE_DIR / "schema_batuira.sql"
SEED_PATH = BASE_DIR / "seed_batuira.sql"


def inserir_usuario(
    conn, perfil, nome, username, senha, profissao=None, registro=None, primeiro_acesso=0
):
    perfil_id = conn.execute(
        "SELECT id FROM perfis_acesso WHERE codigo = ?", (perfil,)
    ).fetchone()[0]
    cursor = conn.execute(
        """
        INSERT INTO usuarios (
            perfil_id, nome, username, email, senha_hash,
            profissao, registro_profissional, primeiro_acesso, ativo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            perfil_id,
            nome,
            username,
            f"{username}@nucleobatuira.local",
            generate_password_hash(senha),
            profissao,
            registro,
            primeiro_acesso,
        ),
    )
    return cursor.lastrowid


def criar_banco():
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.executescript(SEED_PATH.read_text(encoding="utf-8"))

        # Usuários para teste, iguais aos exibidos no frontend.
        admin_id = inserir_usuario(
            conn,
            "admin",
            "Ana Administradora",
            "admin",
            "admin123",
            "Administradora",
            primeiro_acesso=1,
        )
        tecnico_id = inserir_usuario(
            conn,
            "technical",
            "Dr. Carlos Técnico",
            "tecnico",
            "senha123",
            "Médico",
            "CRM-SP 12345",
        )
        financeiro_id = inserir_usuario(
            conn,
            "financial",
            "Maria Financeiro",
            "financeiro",
            "senha123",
            "Assistente Financeira",
        )
        funcionario_id = inserir_usuario(
            conn, "staff", "João Funcionário", "func", "senha123", "Cuidador"
        )

        # Acolhidos de demonstração.
        acolhidos = [
            ("Maria Silva", "1948-03-15", "F", "idoso", "2024-02-01", "A", "101-A", "estavel", "Plano Privado", "Bradesco Saúde", "Demência Moderada"),
            ("José Santos", "1944-05-20", "M", "idoso", "2023-11-10", "A", "102-B", "estavel", "Convênio SUS", "SUS", "Hipertensão"),
            ("Ana Costa", "1951-08-08", "F", "idoso", "2025-01-12", "A", "103-A", "estavel", "Particular", None, "Diabetes Tipo 2"),
            ("Pedro Oliveira", "1938-01-30", "M", "idoso", "2022-06-15", "B", "201-B", "critico", "Plano Privado", "Unimed", "Insuficiência Cardíaca"),
            ("Luiza Ferreira", "1955-04-11", "F", "idoso", "2025-03-02", "B", "202-A", "estavel", "Convênio SUS", "SUS", "Parkinson Leve"),
            ("Carlos Mendes", "1942-09-18", "M", "idoso", "2024-08-22", "B", "203-B", "monitoramento", "Particular", None, "Pós-AVC"),
            ("Regina Almeida", "1947-12-02", "F", "idoso", "2023-03-19", "C", "301-A", "alta", "Plano Privado", "Amil", "Osteoporose"),
        ]

        ids_acolhidos = []
        for nome, nascimento, sexo, modalidade, admissao, ala, quarto, status, tipo, convenio, diagnostico in acolhidos:
            cursor = conn.execute(
                """
                INSERT INTO acolhidos (
                    nome, data_nascimento, sexo, modalidade_acolhimento,
                    data_admissao, ala, quarto, status,
                    tipo_atendimento, convenio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (nome, nascimento, sexo, modalidade, admissao, ala, quarto, status, tipo, convenio),
            )
            acolhido_id = cursor.lastrowid
            ids_acolhidos.append(acolhido_id)
            conn.execute(
                """
                INSERT INTO diagnosticos (
                    acolhido_id, registrado_por, descricao,
                    data_diagnostico, principal, ativo
                ) VALUES (?, ?, ?, ?, 1, 1)
                """,
                (acolhido_id, tecnico_id, diagnostico, admissao),
            )

        maria_id = ids_acolhidos[0]

        # Contato familiar e visitas da Maria.
        familiar_id = conn.execute(
            """
            INSERT INTO familiares (
                acolhido_id, nome, parentesco, telefone, email,
                contato_principal, responsavel_legal,
                autorizado_visita, frequencia_visita
            ) VALUES (?, ?, ?, ?, ?, 1, 1, 1, ?)
            """,
            (
                maria_id,
                "João Silva",
                "Filho",
                "(11) 98765-4321",
                "joao.silva@email.com",
                "Semanal",
            ),
        ).lastrowid

        hoje = date.today()
        conn.execute(
            """
            INSERT INTO visitas (
                acolhido_id, familiar_id, registrado_por,
                tipo, inicio, fim, observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                maria_id,
                familiar_id,
                funcionario_id,
                "Visita familiar",
                f"{hoje.isoformat()} 14:00:00",
                f"{hoje.isoformat()} 16:00:00",
                "Visita tranquila. Trouxe álbum de fotos.",
            ),
        )

        # Alergias e sinais vitais.
        for alergia_nome in ("Penicilina", "Dipirona"):
            alergia_id = conn.execute(
                "SELECT id FROM alergias WHERE nome = ?", (alergia_nome,)
            ).fetchone()[0]
            conn.execute(
                """
                INSERT INTO acolhido_alergias (
                    acolhido_id, alergia_id, registrado_por, gravidade
                ) VALUES (?, ?, ?, ?)
                """,
                (maria_id, alergia_id, tecnico_id, "moderada"),
            )

        conn.execute(
            """
            INSERT INTO sinais_vitais (
                acolhido_id, registrado_por, medido_em,
                peso_kg, altura_m, pressao_sistolica,
                pressao_diastolica, frequencia_cardiaca,
                saturacao_oxigenio
            ) VALUES (?, ?, ?, 62, 1.58, 130, 80, 72, 97)
            """,
            (maria_id, tecnico_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )

        # Prescrições e notas clínicas.
        prescricoes = [
            ("Donepezila 10mg", "1 comprimido ao dia (à noite)", "ativa"),
            ("Metformina 500mg", "2 comprimidos ao dia (após refeição)", "ativa"),
            ("Atenolol 25mg", "1 comprimido ao dia (pela manhã)", "encerrada"),
        ]
        for medicamento, posologia, status in prescricoes:
            conn.execute(
                """
                INSERT INTO prescricoes (
                    acolhido_id, prescrito_por, tipo_prescricao,
                    medicamento, posologia, data_inicio, status
                ) VALUES (?, ?, 'medica', ?, ?, ?, ?)
                """,
                (maria_id, tecnico_id, medicamento, posologia, hoje.isoformat(), status),
            )

        conn.execute(
            """
            INSERT INTO notas_clinicas (
                acolhido_id, profissional_id, tipo, conteudo
            ) VALUES (?, ?, ?, ?)
            """,
            (
                maria_id,
                tecnico_id,
                "Evolução Médica",
                "Paciente apresenta melhora cognitiva após ajuste de dose. PA controlada.",
            ),
        )

        # PIA com metas.
        pia_id = conn.execute(
            """
            INSERT INTO pias (
                acolhido_id, criado_por, versao, situacao_atual,
                necessidades, potencialidades, data_elaboracao,
                data_revisao, status
            ) VALUES (?, ?, 'v1.0', ?, ?, ?, ?, ?, 'ativo')
            """,
            (
                maria_id,
                tecnico_id,
                "Demência moderada com necessidade de apoio diário.",
                "Estimulação cognitiva, cuidado clínico e fortalecimento familiar.",
                "Boa resposta à música e às atividades em grupo.",
                hoje.isoformat(),
                (hoje + timedelta(days=90)).isoformat(),
            ),
        ).lastrowid
        conn.execute(
            """
            INSERT INTO pia_metas (
                pia_id, responsavel_id, area, objetivo,
                acoes, prazo, progresso, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pia_id,
                tecnico_id,
                "Cognitivo",
                "Melhorar a orientação e a memória recente.",
                "Realizar estimulação cognitiva três vezes por semana.",
                (hoje + timedelta(days=60)).isoformat(),
                60,
                "Em andamento",
            ),
        )

        # PTS e intervenção.
        pts_id = conn.execute(
            """
            INSERT INTO pts (
                acolhido_id, criado_por, diagnostico_situacao,
                objetivos_terapeuticos, avaliacao_equipe,
                data_reuniao, data_revisao, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ativo')
            """,
            (
                maria_id,
                tecnico_id,
                "Demência moderada e diabetes controlada.",
                "Manter autonomia, segurança e qualidade de vida.",
                "Acompanhamento multiprofissional contínuo.",
                hoje.isoformat(),
                (hoje + timedelta(days=90)).isoformat(),
            ),
        ).lastrowid
        conn.execute(
            """
            INSERT INTO pts_intervencoes (
                pts_id, responsavel_id, especialidade,
                intervencao, frequencia, status
            ) VALUES (?, ?, ?, ?, ?, 'ativa')
            """,
            (
                pts_id,
                tecnico_id,
                "Medicina",
                "Acompanhar medicações e condições clínicas.",
                "Mensal",
            ),
        )

        # Plano de alta.
        plano_id = conn.execute(
            """
            INSERT INTO planos_alta (
                acolhido_id, coordenador_id, previsao_alta,
                tipo_alta, status, orientacoes
            ) VALUES (?, ?, ?, ?, 'em_andamento', ?)
            """,
            (
                maria_id,
                tecnico_id,
                (hoje + timedelta(days=120)).isoformat(),
                "Alta para domicílio com suporte familiar",
                "Manter as medicações e realizar retorno médico em 30 dias.",
            ),
        ).lastrowid
        etapas = [
            (1, "Estabilização da pressão arterial", "concluido"),
            (2, "Treinamento familiar", "em_andamento"),
            (3, "Adaptação do domicílio", "pendente"),
        ]
        for ordem, descricao, status in etapas:
            conn.execute(
                """
                INSERT INTO plano_alta_etapas (
                    plano_alta_id, descricao, ordem, status
                ) VALUES (?, ?, ?, ?)
                """,
                (plano_id, descricao, ordem, status),
            )

        # Gastos e receitas.
        cat_medicamento = conn.execute(
            "SELECT id FROM categorias_financeiras WHERE nome = 'Saúde - Medicamentos'"
        ).fetchone()[0]
        cat_higiene = conn.execute(
            "SELECT id FROM categorias_financeiras WHERE nome = 'Higiene'"
        ).fetchone()[0]
        cat_verba = conn.execute(
            "SELECT id FROM categorias_financeiras WHERE nome = 'Verba municipal'"
        ).fetchone()[0]

        conn.execute(
            """
            INSERT INTO gastos (
                acolhido_id, categoria_id, registrado_por,
                descricao, valor, data_gasto, fornecedor
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (maria_id, cat_medicamento, financeiro_id, "Medicamentos do mês", 485.50, hoje.isoformat(), "Farmácia Popular"),
        )
        conn.execute(
            """
            INSERT INTO gastos (
                acolhido_id, categoria_id, registrado_por,
                descricao, valor, data_gasto, fornecedor
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ids_acolhidos[1], cat_higiene, financeiro_id, "Fraldas geriátricas", 189.90, hoje.isoformat(), "Distribuidor ABC"),
        )
        conn.execute(
            """
            INSERT INTO receitas (
                categoria_id, registrado_por, descricao,
                fonte, valor, data_recebimento
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (cat_verba, financeiro_id, "Repasse mensal", "Prefeitura de Guarulhos", 15000.00, hoje.isoformat()),
        )
        conn.execute(
            """
            INSERT INTO prestacoes_contas (
                gerado_por, competencia, status, observacoes
            ) VALUES (?, ?, 'em_analise', ?)
            """,
            (financeiro_id, hoje.strftime("%Y-%m"), "Prestação de contas do mês atual."),
        )

        # Agenda e alerta próximos da data de criação do banco.
        amanha = datetime.now() + timedelta(days=1)
        conn.execute(
            """
            INSERT INTO eventos_agenda (
                acolhido_id, responsavel_id, criado_por,
                titulo, tipo, setor, inicio, fim, local
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                maria_id,
                tecnico_id,
                admin_id,
                "Consulta - Maria Silva",
                "Consulta Médica",
                "saude",
                amanha.replace(hour=9, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S"),
                amanha.replace(hour=10, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S"),
                "Consultório 1",
            ),
        )
        depois_de_amanha = datetime.now() + timedelta(days=2)
        conn.execute(
            """
            INSERT INTO eventos_agenda (
                acolhido_id, responsavel_id, criado_por,
                titulo, tipo, setor, inicio, fim, local
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                None,
                financeiro_id,
                admin_id,
                "Reunião de prestação de contas",
                "Reunião",
                "institucional",
                depois_de_amanha.replace(hour=14, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S"),
                depois_de_amanha.replace(hour=15, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S"),
                "Sala administrativa",
            ),
        )

        conn.execute(
            """
            INSERT INTO alertas (
                acolhido_id, criado_por, tipo, severidade, mensagem
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                ids_acolhidos[3],
                tecnico_id,
                "Clínico",
                "critica",
                "Acolhido necessita de acompanhamento da pressão arterial.",
            ),
        )

        conn.commit()

        integridade = conn.execute("PRAGMA integrity_check").fetchone()[0]
        chaves_invalidas = conn.execute("PRAGMA foreign_key_check").fetchall()

    if integridade != "ok" or chaves_invalidas:
        raise RuntimeError(
            f"Banco inválido: integrity_check={integridade}; foreign_keys={chaves_invalidas}"
        )

    print(f"Banco criado: {DB_PATH}")
    print("Logins de teste:")
    print("  admin / admin123")
    print("  tecnico / senha123")
    print("  financeiro / senha123")
    print("  func / senha123")


if __name__ == "__main__":
    criar_banco()
