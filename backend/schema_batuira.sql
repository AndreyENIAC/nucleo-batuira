PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA user_version = 1;

BEGIN TRANSACTION;

CREATE TABLE perfis_acesso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE
        CHECK (codigo IN ('admin', 'technical', 'financial', 'staff')),
    nome TEXT NOT NULL,
    descricao TEXT
);

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    perfil_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    senha_hash TEXT NOT NULL,
    telefone TEXT,
    profissao TEXT,
    conselho_profissional TEXT,
    registro_profissional TEXT,
    primeiro_acesso INTEGER NOT NULL DEFAULT 1
        CHECK (primeiro_acesso IN (0, 1)),
    ativo INTEGER NOT NULL DEFAULT 1
        CHECK (ativo IN (0, 1)),
    ultimo_login TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (perfil_id) REFERENCES perfis_acesso(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE tokens_recuperacao_senha (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expira_em TEXT NOT NULL,
    utilizado_em TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE solicitacoes_recuperacao_senha (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendente'
        CHECK (status IN ('pendente', 'resolvida', 'cancelada')),
    solicitado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolvido_por INTEGER,
    resolvido_em TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (resolvido_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE acolhidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    cpf TEXT UNIQUE,
    rg TEXT,
    sexo TEXT,
    modalidade_acolhimento TEXT NOT NULL DEFAULT 'idoso'
        CHECK (modalidade_acolhimento IN ('idoso', 'infantil')),
    data_admissao TEXT NOT NULL,
    data_saida TEXT,
    ala TEXT,
    quarto TEXT,
    status TEXT NOT NULL DEFAULT 'estavel'
        CHECK (status IN ('estavel', 'monitoramento', 'critico', 'alta', 'inativo')),
    tipo_atendimento TEXT,
    convenio TEXT,
    endereco TEXT,
    foto_url TEXT,
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (data_saida IS NULL OR date(data_saida) >= date(data_admissao))
);

CREATE TABLE familiares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    parentesco TEXT NOT NULL,
    telefone TEXT,
    email TEXT,
    endereco TEXT,
    contato_principal INTEGER NOT NULL DEFAULT 0
        CHECK (contato_principal IN (0, 1)),
    responsavel_legal INTEGER NOT NULL DEFAULT 0
        CHECK (responsavel_legal IN (0, 1)),
    autorizado_visita INTEGER NOT NULL DEFAULT 1
        CHECK (autorizado_visita IN (0, 1)),
    frequencia_visita TEXT,
    ativo INTEGER NOT NULL DEFAULT 1
        CHECK (ativo IN (0, 1)),
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE visitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER NOT NULL,
    familiar_id INTEGER,
    registrado_por INTEGER NOT NULL,
    tipo TEXT,
    inicio TEXT NOT NULL,
    fim TEXT,
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (familiar_id) REFERENCES familiares(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (fim IS NULL OR datetime(fim) >= datetime(inicio))
);

CREATE TABLE diagnosticos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER NOT NULL,
    registrado_por INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    cid TEXT,
    data_diagnostico TEXT,
    principal INTEGER NOT NULL DEFAULT 0
        CHECK (principal IN (0, 1)),
    ativo INTEGER NOT NULL DEFAULT 1
        CHECK (ativo IN (0, 1)),
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE alergias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE acolhido_alergias (
    acolhido_id INTEGER NOT NULL,
    alergia_id INTEGER NOT NULL,
    registrado_por INTEGER NOT NULL,
    gravidade TEXT,
    observacoes TEXT,
    registrado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (acolhido_id, alergia_id),
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (alergia_id) REFERENCES alergias(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE sinais_vitais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER NOT NULL,
    registrado_por INTEGER NOT NULL,
    medido_em TEXT NOT NULL,
    peso_kg NUMERIC,
    altura_m NUMERIC,
    pressao_sistolica INTEGER,
    pressao_diastolica INTEGER,
    frequencia_cardiaca INTEGER,
    saturacao_oxigenio NUMERIC,
    glicemia NUMERIC,
    temperatura NUMERIC,
    observacoes TEXT,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (peso_kg IS NULL OR peso_kg > 0),
    CHECK (altura_m IS NULL OR altura_m > 0),
    CHECK (pressao_sistolica IS NULL OR pressao_sistolica > 0),
    CHECK (pressao_diastolica IS NULL OR pressao_diastolica > 0),
    CHECK (frequencia_cardiaca IS NULL OR frequencia_cardiaca > 0),
    CHECK (saturacao_oxigenio IS NULL OR (saturacao_oxigenio >= 0 AND saturacao_oxigenio <= 100)),
    CHECK (glicemia IS NULL OR glicemia >= 0)
);

CREATE TABLE prescricoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER NOT NULL,
    prescrito_por INTEGER NOT NULL,
    tipo_prescricao TEXT NOT NULL
        CHECK (tipo_prescricao IN ('medica', 'enfermagem', 'nutricional', 'outra')),
    medicamento TEXT NOT NULL,
    dosagem TEXT,
    via_administracao TEXT,
    frequencia TEXT,
    posologia TEXT NOT NULL,
    data_inicio TEXT NOT NULL,
    data_fim TEXT,
    status TEXT NOT NULL DEFAULT 'ativa'
        CHECK (status IN ('ativa', 'suspensa', 'encerrada')),
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (prescrito_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (data_fim IS NULL OR date(data_fim) >= date(data_inicio))
);

CREATE TABLE prescricao_horarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescricao_id INTEGER NOT NULL,
    horario TEXT NOT NULL,
    dose TEXT,
    observacoes TEXT,
    FOREIGN KEY (prescricao_id) REFERENCES prescricoes(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    UNIQUE (prescricao_id, horario)
);

CREATE TABLE administracoes_medicamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescricao_horario_id INTEGER NOT NULL,
    administrado_por INTEGER NOT NULL,
    previsto_para TEXT NOT NULL,
    administrado_em TEXT,
    status TEXT NOT NULL DEFAULT 'pendente'
        CHECK (status IN ('pendente', 'administrado', 'recusado', 'omitido')),
    observacoes TEXT,
    FOREIGN KEY (prescricao_horario_id) REFERENCES prescricao_horarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (administrado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (prescricao_horario_id, previsto_para)
);

CREATE TABLE notas_clinicas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER NOT NULL,
    profissional_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    registrado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (profissional_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE pias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER NOT NULL,
    criado_por INTEGER NOT NULL,
    versao TEXT NOT NULL,
    situacao_atual TEXT NOT NULL,
    necessidades TEXT NOT NULL,
    potencialidades TEXT,
    data_elaboracao TEXT NOT NULL,
    data_revisao TEXT,
    status TEXT NOT NULL DEFAULT 'rascunho'
        CHECK (status IN ('rascunho', 'ativo', 'revisado', 'encerrado')),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (acolhido_id, versao)
);

CREATE TABLE pia_metas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pia_id INTEGER NOT NULL,
    responsavel_id INTEGER,
    area TEXT NOT NULL,
    objetivo TEXT NOT NULL,
    acoes TEXT NOT NULL,
    prazo TEXT,
    progresso INTEGER NOT NULL DEFAULT 0
        CHECK (progresso BETWEEN 0 AND 100),
    status TEXT NOT NULL,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pia_id) REFERENCES pias(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE pts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER NOT NULL,
    criado_por INTEGER NOT NULL,
    diagnostico_situacao TEXT NOT NULL,
    objetivos_terapeuticos TEXT NOT NULL,
    avaliacao_equipe TEXT,
    observacoes_gerais TEXT,
    data_reuniao TEXT NOT NULL,
    data_revisao TEXT,
    status TEXT NOT NULL,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE pts_intervencoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pts_id INTEGER NOT NULL,
    responsavel_id INTEGER,
    especialidade TEXT NOT NULL,
    responsavel_externo TEXT,
    intervencao TEXT NOT NULL,
    frequencia TEXT,
    status TEXT NOT NULL DEFAULT 'ativa',
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pts_id) REFERENCES pts(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK (responsavel_id IS NOT NULL OR responsavel_externo IS NOT NULL)
);

CREATE TABLE planos_alta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER NOT NULL,
    coordenador_id INTEGER NOT NULL,
    previsao_alta TEXT,
    tipo_alta TEXT,
    status TEXT NOT NULL DEFAULT 'planejamento'
        CHECK (status IN ('planejamento', 'em_andamento', 'concluido', 'cancelado')),
    orientacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (coordenador_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE plano_alta_etapas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plano_alta_id INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    ordem INTEGER NOT NULL CHECK (ordem > 0),
    status TEXT NOT NULL DEFAULT 'pendente'
        CHECK (status IN ('pendente', 'em_andamento', 'concluido')),
    concluido_em TEXT,
    observacoes TEXT,
    FOREIGN KEY (plano_alta_id) REFERENCES planos_alta(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    UNIQUE (plano_alta_id, ordem)
);

CREATE TABLE documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER,
    enviado_por INTEGER NOT NULL,
    escopo TEXT NOT NULL
        CHECK (escopo IN ('acolhido', 'institucional')),
    titulo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    nome_original TEXT NOT NULL,
    caminho_arquivo TEXT NOT NULL,
    mime_type TEXT,
    tamanho_bytes INTEGER,
    data_validade TEXT,
    status TEXT NOT NULL DEFAULT 'ativo',
    descricao TEXT,
    enviado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (enviado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (
        (escopo = 'acolhido' AND acolhido_id IS NOT NULL)
        OR
        (escopo = 'institucional' AND acolhido_id IS NULL)
    ),
    CHECK (tamanho_bytes IS NULL OR tamanho_bytes >= 0)
);

CREATE TABLE recursos_administrativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER,
    criado_por INTEGER NOT NULL,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,
    numero_documento TEXT,
    orgao_emissor TEXT,
    data_emissao TEXT,
    data_validade TEXT,
    status TEXT NOT NULL
        CHECK (status IN ('ativo', 'atencao', 'vencido', 'inativo')),
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (documento_id) REFERENCES documentos(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (data_validade IS NULL OR data_emissao IS NULL OR date(data_validade) >= date(data_emissao))
);

CREATE TABLE categorias_financeiras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL
        CHECK (tipo IN ('despesa', 'receita')),
    ativo INTEGER NOT NULL DEFAULT 1
        CHECK (ativo IN (0, 1)),
    UNIQUE (nome, tipo)
);

CREATE TABLE gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER,
    categoria_id INTEGER NOT NULL,
    comprovante_documento_id INTEGER,
    registrado_por INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    valor NUMERIC NOT NULL CHECK (valor >= 0),
    data_gasto TEXT NOT NULL,
    fornecedor TEXT,
    status TEXT NOT NULL DEFAULT 'registrado',
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (categoria_id) REFERENCES categorias_financeiras(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (comprovante_documento_id) REFERENCES documentos(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id INTEGER,
    comprovante_documento_id INTEGER,
    registrado_por INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    fonte TEXT,
    valor NUMERIC NOT NULL CHECK (valor >= 0),
    data_recebimento TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'recebida',
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias_financeiras(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (comprovante_documento_id) REFERENCES documentos(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE prestacoes_contas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gerado_por INTEGER NOT NULL,
    aprovado_por INTEGER,
    relatorio_documento_id INTEGER,
    competencia TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL
        CHECK (status IN ('rascunho', 'em_analise', 'aprovado', 'rejeitado')),
    gerado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    aprovado_em TEXT,
    observacoes TEXT,
    FOREIGN KEY (gerado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (aprovado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (relatorio_documento_id) REFERENCES documentos(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE beneficios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER NOT NULL,
    tipo_beneficio TEXT NOT NULL,
    numero_beneficio TEXT,
    orgao_pagador TEXT,
    valor_mensal NUMERIC NOT NULL CHECK (valor_mensal >= 0),
    data_inicio TEXT,
    data_fim TEXT,
    status TEXT NOT NULL,
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (data_fim IS NULL OR data_inicio IS NULL OR date(data_fim) >= date(data_inicio))
);

CREATE TABLE eventos_agenda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER,
    responsavel_id INTEGER,
    criado_por INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    tipo TEXT NOT NULL,
    setor TEXT NOT NULL DEFAULT 'geral'
        CHECK (setor IN ('saude', 'institucional', 'geral')),
    inicio TEXT NOT NULL,
    fim TEXT,
    local TEXT,
    status TEXT NOT NULL DEFAULT 'agendado',
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CHECK (fim IS NULL OR datetime(fim) >= datetime(inicio))
);

CREATE TABLE tarefas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER,
    responsavel_id INTEGER NOT NULL,
    criado_por INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descricao TEXT,
    prioridade TEXT NOT NULL DEFAULT 'media'
        CHECK (prioridade IN ('baixa', 'media', 'alta', 'urgente')),
    prazo TEXT,
    status TEXT NOT NULL DEFAULT 'pendente'
        CHECK (status IN ('pendente', 'em_andamento', 'concluida', 'cancelada')),
    concluida_em TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acolhido_id INTEGER,
    criado_por INTEGER NOT NULL,
    resolvido_por INTEGER,
    tipo TEXT NOT NULL,
    severidade TEXT NOT NULL
        CHECK (severidade IN ('baixa', 'media', 'alta', 'critica')),
    mensagem TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'aberto'
        CHECK (status IN ('aberto', 'em_tratamento', 'resolvido', 'cancelado')),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolvido_em TEXT,
    origem_tipo TEXT,
    origem_id INTEGER,
    FOREIGN KEY (acolhido_id) REFERENCES acolhidos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (resolvido_por) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE logs_auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    acao TEXT NOT NULL,
    tabela TEXT NOT NULL,
    registro_id INTEGER,
    detalhes_json TEXT,
    endereco_ip TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

-- Índices de busca e relacionamento
CREATE INDEX idx_usuarios_perfil ON usuarios(perfil_id);
CREATE INDEX idx_solicitacoes_recuperacao_usuario
    ON solicitacoes_recuperacao_senha(usuario_id, status);
CREATE INDEX idx_usuarios_ativo ON usuarios(ativo);
CREATE INDEX idx_tokens_usuario ON tokens_recuperacao_senha(usuario_id);
CREATE INDEX idx_tokens_expiracao ON tokens_recuperacao_senha(expira_em);

CREATE INDEX idx_acolhidos_nome ON acolhidos(nome);
CREATE INDEX idx_acolhidos_status ON acolhidos(status);
CREATE INDEX idx_acolhidos_modalidade ON acolhidos(modalidade_acolhimento);
CREATE INDEX idx_familiares_acolhido ON familiares(acolhido_id);
CREATE UNIQUE INDEX ux_familiar_contato_principal
    ON familiares(acolhido_id)
    WHERE contato_principal = 1 AND ativo = 1;
CREATE INDEX idx_visitas_acolhido_inicio ON visitas(acolhido_id, inicio);

CREATE INDEX idx_diagnosticos_acolhido ON diagnosticos(acolhido_id);
CREATE UNIQUE INDEX ux_diagnostico_principal_ativo
    ON diagnosticos(acolhido_id)
    WHERE principal = 1 AND ativo = 1;
CREATE INDEX idx_sinais_acolhido_data ON sinais_vitais(acolhido_id, medido_em);

CREATE INDEX idx_prescricoes_acolhido_status ON prescricoes(acolhido_id, status);
CREATE INDEX idx_horarios_prescricao ON prescricao_horarios(prescricao_id);
CREATE INDEX idx_administracoes_previsto ON administracoes_medicamentos(previsto_para, status);
CREATE INDEX idx_notas_acolhido_data ON notas_clinicas(acolhido_id, registrado_em);

CREATE INDEX idx_pias_acolhido ON pias(acolhido_id);
CREATE UNIQUE INDEX ux_pia_ativa_por_acolhido
    ON pias(acolhido_id)
    WHERE status = 'ativo';
CREATE INDEX idx_pia_metas_pia ON pia_metas(pia_id);
CREATE INDEX idx_pts_acolhido ON pts(acolhido_id);
CREATE INDEX idx_pts_intervencoes_pts ON pts_intervencoes(pts_id);
CREATE INDEX idx_planos_alta_acolhido ON planos_alta(acolhido_id);
CREATE INDEX idx_etapas_plano_alta ON plano_alta_etapas(plano_alta_id, ordem);

CREATE INDEX idx_documentos_acolhido ON documentos(acolhido_id);
CREATE INDEX idx_eventos_setor_inicio ON eventos_agenda(setor, inicio);
CREATE INDEX idx_documentos_categoria ON documentos(categoria);
CREATE INDEX idx_documentos_validade ON documentos(data_validade);
CREATE INDEX idx_recursos_validade ON recursos_administrativos(data_validade, status);

CREATE INDEX idx_gastos_data ON gastos(data_gasto);
CREATE INDEX idx_gastos_acolhido ON gastos(acolhido_id);
CREATE INDEX idx_gastos_categoria ON gastos(categoria_id);
CREATE INDEX idx_receitas_data ON receitas(data_recebimento);
CREATE INDEX idx_receitas_categoria ON receitas(categoria_id);
CREATE INDEX idx_beneficios_acolhido ON beneficios(acolhido_id);

CREATE INDEX idx_eventos_inicio ON eventos_agenda(inicio);
CREATE INDEX idx_eventos_acolhido ON eventos_agenda(acolhido_id);
CREATE INDEX idx_tarefas_responsavel_status ON tarefas(responsavel_id, status);
CREATE INDEX idx_tarefas_prazo ON tarefas(prazo);
CREATE INDEX idx_alertas_status_severidade ON alertas(status, severidade);
CREATE INDEX idx_alertas_acolhido ON alertas(acolhido_id);
CREATE INDEX idx_alertas_origem ON alertas(origem_tipo, origem_id);
CREATE INDEX idx_logs_tabela_registro ON logs_auditoria(tabela, registro_id);
CREATE INDEX idx_logs_usuario_data ON logs_auditoria(usuario_id, criado_em);

-- Atualização automática do campo atualizado_em
CREATE TRIGGER trg_usuarios_atualizado_em
AFTER UPDATE ON usuarios
FOR EACH ROW
WHEN NEW.atualizado_em = OLD.atualizado_em
BEGIN
    UPDATE usuarios SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_acolhidos_atualizado_em
AFTER UPDATE ON acolhidos
FOR EACH ROW
WHEN NEW.atualizado_em = OLD.atualizado_em
BEGIN
    UPDATE acolhidos SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_prescricoes_atualizado_em
AFTER UPDATE ON prescricoes
FOR EACH ROW
WHEN NEW.atualizado_em = OLD.atualizado_em
BEGIN
    UPDATE prescricoes SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_pias_atualizado_em
AFTER UPDATE ON pias
FOR EACH ROW
WHEN NEW.atualizado_em = OLD.atualizado_em
BEGIN
    UPDATE pias SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_pts_atualizado_em
AFTER UPDATE ON pts
FOR EACH ROW
WHEN NEW.atualizado_em = OLD.atualizado_em
BEGIN
    UPDATE pts SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_planos_alta_atualizado_em
AFTER UPDATE ON planos_alta
FOR EACH ROW
WHEN NEW.atualizado_em = OLD.atualizado_em
BEGIN
    UPDATE planos_alta SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_recursos_administrativos_atualizado_em
AFTER UPDATE ON recursos_administrativos
FOR EACH ROW
WHEN NEW.atualizado_em = OLD.atualizado_em
BEGIN
    UPDATE recursos_administrativos SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

COMMIT;
