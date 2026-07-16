PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

INSERT INTO perfis_acesso (codigo, nome, descricao) VALUES
    ('admin', 'Administrador', 'Acesso completo ao sistema.'),
    ('technical', 'Equipe Técnica', 'Acesso clínico, assistencial, PIA, PTS e acolhidos.'),
    ('financial', 'Financeiro', 'Acesso ao módulo financeiro, documentos e prestações de contas.'),
    ('staff', 'Funcionário', 'Acesso operacional, agenda, tarefas e consulta de acolhidos.');

INSERT INTO categorias_financeiras (nome, tipo) VALUES
    ('Saúde - Medicamentos', 'despesa'),
    ('Saúde - Nutrição', 'despesa'),
    ('Higiene', 'despesa'),
    ('Equipamentos', 'despesa'),
    ('Alimentação', 'despesa'),
    ('Manutenção', 'despesa'),
    ('Transporte', 'despesa'),
    ('Outras despesas', 'despesa'),
    ('Verba municipal', 'receita'),
    ('Convênio público', 'receita'),
    ('Doações', 'receita'),
    ('Benefícios de acolhidos', 'receita'),
    ('Outras receitas', 'receita');

INSERT INTO alergias (nome) VALUES
    ('Penicilina'),
    ('Dipirona'),
    ('Látex'),
    ('Amendoim'),
    ('Frutos do mar');

COMMIT;
