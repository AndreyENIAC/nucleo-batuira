# Sistema Núcleo Batuíra — Frontend e Backend integrados

Projeto acadêmico usando:

- Frontend: HTML, CSS, Bootstrap e JavaScript puro.
- Backend: Python, Flask e JWT.
- Banco: SQLite.

## Como executar no Windows

### Opção rápida

Execute `iniciar_projeto.bat`. Serão abertas duas janelas: uma para o Flask e outra para o Frontend.

Depois acesse:

```text
http://127.0.0.1:5500/login.html
```

### Execução manual

No primeiro terminal:

```bat
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

No segundo terminal:

```bat
cd frontend
python -m http.server 5500
```

## Como a integração funciona

1. O usuário preenche o formulário no HTML.
2. O JavaScript usa `fetch()` para chamar a API Flask.
3. O Flask valida a requisição e executa um comando SQL.
4. O SQLite salva ou consulta os dados.
5. O Flask devolve JSON.
6. O JavaScript mostra a resposta na página.

O endereço da API está no arquivo `frontend/js/api.js`.
