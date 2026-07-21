"""Teste simples da autenticação e das consultas principais."""

from app import app

cliente = app.test_client()

# O administrador inicial deve ser obrigado a trocar admin123.
resposta = cliente.post(
    "/api/login",
    json={"username": "admin", "senha": "admin123"},
)
print("Login do administrador:", resposta.status_code, resposta.get_json())

if resposta.status_code == 200:
    token_admin = resposta.get_json()["access_token"]
    cabecalho_admin = {"Authorization": f"Bearer {token_admin}"}
    resposta = cliente.get("/api/dashboard", headers=cabecalho_admin)
    print("Bloqueio do primeiro acesso:", resposta.status_code, resposta.get_json())

# Um usuário já configurado continua conseguindo consultar o sistema.
resposta = cliente.post(
    "/api/login",
    json={"username": "tecnico", "senha": "senha123"},
)
print("Login técnico:", resposta.status_code)

if resposta.status_code == 200:
    token = resposta.get_json()["access_token"]
    cabecalho = {"Authorization": f"Bearer {token}"}

    resposta = cliente.get("/api/dashboard", headers=cabecalho)
    print("Dashboard:", resposta.status_code)

    resposta = cliente.get("/api/acolhidos", headers=cabecalho)
    dados = resposta.get_json() if resposta.status_code == 200 else []
    print("Quantidade de acolhidos:", len(dados))
