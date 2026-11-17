from fastapi.testclient import TestClient

from app.modules.auth.models import Usuario
from tests.conftest import SENHA_DE_TESTE


def test_login_valido_retorna_token(client: TestClient, usuario_cadastrado: Usuario):
    response = client.post("/auth/login", json={"email": "joao@loja.com", "senha": SENHA_DE_TESTE})

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"


def test_senha_incorreta_retorna_401(client: TestClient, usuario_cadastrado: Usuario):
    response = client.post("/auth/login", json={"email": "joao@loja.com", "senha": "senhaErrada"})

    assert response.status_code == 401
    assert response.json() == {"detail": "E-mail ou senha inválidos."}
