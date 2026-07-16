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

- `admin / admin123`
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
