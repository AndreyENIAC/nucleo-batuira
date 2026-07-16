"""Teste simples sem precisar abrir o navegador."""

from app import app

cliente = app.test_client()

resposta = cliente.post(
    "/api/login",
    json={"username": "admin", "senha": "admin123"},
)

print("Login:", resposta.status_code, resposta.get_json())

if resposta.status_code == 200:
    token = resposta.get_json()["access_token"]
    cabecalho = {"Authorization": f"Bearer {token}"}

    resposta = cliente.get("/api/dashboard", headers=cabecalho)
    print("Dashboard:", resposta.status_code, resposta.get_json())

    resposta = cliente.get("/api/acolhidos", headers=cabecalho)
    print("Quantidade de acolhidos:", len(resposta.get_json()))
