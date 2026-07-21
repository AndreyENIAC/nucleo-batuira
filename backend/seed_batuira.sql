PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

INSERT INTO perfis_acesso (codigo, nome, descricao) VALUES
    ('admin', 'Administrador', 'Acesso completo ao sistema.'),
    ('technical', 'Equipe Técnica', 'Acesso de edição à Gestão de Saúde e aos acolhidos.'),
    ('financial', 'Equipe Institucional', 'Acesso de edição à Gestão Institucional.'),
    ('staff', 'Funcionário', 'Acesso somente para leitura a todos os módulos, exceto usuários.');

INSERT INTO categorias_financeiras (nome, tipo) VALUES
    ('Saúde - Medicamentos', 'despesa'),
    ('Saúde - Nutrição', 'despesa'),
    ('Higiene', 'despesa'),
    ('Equipamentos', 'despesa'),
    ('Alimentação', 'despesa'),
    ('Manutenção', 'despesa'),
    ('Transporte', 'despesa'),
    ('Outros', 'despesa'),
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
