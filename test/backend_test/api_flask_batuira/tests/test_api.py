from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app import create_app
from config import TestingConfig


@pytest.fixture()
def client(tmp_path: Path):
    source = Path(__file__).resolve().parents[1] / "batuira.db"
    database = tmp_path / "test.db"
    shutil.copy2(source, database)
    app = create_app(
        TestingConfig,
        {
            "DATABASE_PATH": str(database),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
            "JWT_SECRET_KEY": "test-secret-key-with-at-least-thirty-two-bytes",
        },
    )
    with app.test_client() as client:
        yield client


def login(client, password="admin123"):
    response = client.post("/api/auth/login", json={"login":"admin","senha":password})
    assert response.status_code == 200, response.get_json()
    return response.get_json()["dados"]["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    response=client.get("/api/health")
    assert response.status_code==200
    assert response.get_json()["dados"]["status"]=="ok"


def test_login_change_password_and_dashboard(client):
    token=login(client)
    blocked=client.get("/api/dashboard",headers=auth(token))
    assert blocked.status_code==403

    changed=client.post("/api/auth/trocar-senha",headers=auth(token),json={"nova_senha":"NovaSenha123","confirmacao":"NovaSenha123"})
    assert changed.status_code==200

    token=login(client,"NovaSenha123")
    dashboard=client.get("/api/dashboard",headers=auth(token))
    assert dashboard.status_code==200
    assert dashboard.get_json()["dados"]["perfil"]=="admin"


def test_create_resident_and_family(client):
    token=login(client)
    client.post("/api/auth/trocar-senha",headers=auth(token),json={"nova_senha":"NovaSenha123","confirmacao":"NovaSenha123"})
    token=login(client,"NovaSenha123")

    response=client.post("/api/acolhidos",headers=auth(token),json={
        "nome":"Pessoa de Teste",
        "data_nascimento":"1950-01-15",
        "modalidade_acolhimento":"idoso",
        "data_admissao":"2026-07-15",
        "status":"estavel"
    })
    assert response.status_code==201,response.get_json()
    resident_id=response.get_json()["dados"]["id"]

    family=client.post(f"/api/acolhidos/{resident_id}/familiares",headers=auth(token),json={
        "nome":"Contato Teste","parentesco":"Filho","contato_principal":True
    })
    assert family.status_code==201,family.get_json()

    listing=client.get("/api/acolhidos?busca=Pessoa",headers=auth(token))
    assert listing.status_code==200
    assert listing.get_json()["dados"]["total"]>=1
