import pytest
from fastapi.testclient import TestClient

from tests.compradores.conftest import dados_comprador
from tests.veiculos.conftest import dados_veiculo


@pytest.fixture
def veiculo_disponivel(client: TestClient, auth_headers: dict) -> dict:
    response = client.post("/veiculos", json=dados_veiculo(), headers=auth_headers)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def comprador_cadastrado_para_venda(client: TestClient, auth_headers: dict) -> dict:
    response = client.post("/compradores", json=dados_comprador(), headers=auth_headers)
    assert response.status_code == 201
    return response.json()


def dados_venda(veiculo_id: int, comprador_id: int, **alteracoes) -> dict:
    dados = {
        "veiculo_id": veiculo_id,
        "comprador_id": comprador_id,
        "data": "2026-11-23",
        "valor": 55000.00,
        "forma_pagamento": "Pix",
    }
    dados.update(alteracoes)
    return dados
