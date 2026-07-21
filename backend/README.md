# Backend Flask — Núcleo Batuíra

Backend acadêmico feito com Flask e SQLite.

## Instalação no Windows

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

A API ficará disponível em `http://127.0.0.1:5000`.

## Logins de teste

- `admin / admin123` — exige troca de senha no primeiro acesso
- `tecnico / senha123`
- `financeiro / senha123`
- `func / senha123`

## Arquivos principais

- `app.py`: rotas da API.
- `database.py`: conexão com o SQLite.
- `batuira.db`: banco com dados fictícios.
- `schema_batuira.sql`: criação das tabelas.
- `seed_batuira.sql`: dados iniciais.
- `criar_banco.py`: recria o banco.
- `ROTAS_API.md`: lista de endpoints.

## Atualização de banco existente

O arquivo `configurar_windows.bat` executa as migrações sem apagar os dados:

```bat
python migrar_etapa1_autenticacao.py
python migrar_etapa2_saude.py
python migrar_etapa3_institucional.py
```

A Etapa 3 adiciona os setores da agenda e garante a categoria de gasto `Outros`.

## Permissões

- Administrador: acesso completo e gerenciamento de usuários.
- Equipe técnica: alterações na Gestão de Saúde.
- Equipe institucional: alterações na Gestão Institucional e na agenda institucional.
- Funcionário: consulta dos módulos, sem cadastrar ou modificar.
