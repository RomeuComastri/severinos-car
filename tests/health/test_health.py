from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.database import get_db
from app.main import app


class SessaoComFalha:
    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("conexão recusada"))


def test_health_retorna_status_ok(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_db_retorna_conectado_quando_banco_responde(client: TestClient):
    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_health_db_retorna_503_quando_banco_indisponivel():
    app.dependency_overrides[get_db] = lambda: SessaoComFalha()
    try:
        with TestClient(app) as client:
            response = client.get("/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
