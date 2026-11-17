import pytest
from fastapi.testclient import TestClient

DADOS_VEICULO = {
    "placa": "ABC1D23",
    "marca": "Volkswagen",
    "modelo": "Gol",
    "ano": 2022,
    "cor": "Prata",
    "preco": 55000.00,
}

IMAGEM_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 100
IMAGEM_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
IMAGEM_WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 100


def dados_veiculo(**alteracoes) -> dict:
    return {**DADOS_VEICULO, **alteracoes}


def mensagens_de_erro(response) -> list[str]:
    return [erro["msg"] for erro in response.json()["detail"]]


@pytest.fixture
def veiculo_cadastrado(client: TestClient, auth_headers: dict) -> dict:
    """Veículo disponível, com os dados de DADOS_VEICULO."""
    response = client.post("/veiculos", json=DADOS_VEICULO, headers=auth_headers)
    assert response.status_code == 201
    return response.json()
