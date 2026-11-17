from datetime import date

import pytest
from fastapi.testclient import TestClient

from tests.veiculos.conftest import dados_veiculo, mensagens_de_erro


def test_cadastra_veiculo_valido(client: TestClient, auth_headers: dict):
    response = client.post("/veiculos", json=dados_veiculo(placa="abc-1234"), headers=auth_headers)

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["id"] > 0
    assert corpo["placa"] == "ABC1234"
    assert corpo["modelo"] == "Gol"
    assert corpo["preco"] == 55000.0
    assert corpo["imagem_url"] is None


def test_veiculo_novo_nasce_disponivel_mesmo_com_status_informado(client: TestClient, auth_headers: dict):
    response = client.post("/veiculos", json=dados_veiculo(status="vendido"), headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["status"] == "disponivel"


def test_rejeita_placa_duplicada(client: TestClient, auth_headers: dict, veiculo_cadastrado: dict):
    response = client.post("/veiculos", json=dados_veiculo(placa="abc1d23", modelo="Polo"), headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {"detail": "Já existe um veículo com a placa ABC1D23."}


def test_rejeita_cadastro_sem_placa(client: TestClient, auth_headers: dict):
    dados = dados_veiculo()
    del dados["placa"]

    response = client.post("/veiculos", json=dados, headers=auth_headers)

    assert response.status_code == 422


@pytest.mark.parametrize("placa", ["", "AB12345", "ABCD123", "ABC12345", "1BC1234"])
def test_rejeita_placa_em_formato_invalido(client: TestClient, auth_headers: dict, placa: str):
    response = client.post("/veiculos", json=dados_veiculo(placa=placa), headers=auth_headers)

    assert response.status_code == 422
    assert "Value error, Placa inválida. Use o formato ABC1234 ou ABC1D23." in mensagens_de_erro(response)


@pytest.mark.parametrize("ano", [1899, date.today().year + 2])
def test_rejeita_ano_invalido(client: TestClient, auth_headers: dict, ano: int):
    response = client.post("/veiculos", json=dados_veiculo(ano=ano), headers=auth_headers)

    assert response.status_code == 422
    assert any("O ano deve estar entre 1900 e" in mensagem for mensagem in mensagens_de_erro(response))


@pytest.mark.parametrize("preco", [0, -1500])
def test_rejeita_preco_menor_ou_igual_a_zero(client: TestClient, auth_headers: dict, preco: float):
    response = client.post("/veiculos", json=dados_veiculo(preco=preco), headers=auth_headers)

    assert response.status_code == 422
    assert "Value error, O preço deve ser maior que zero." in mensagens_de_erro(response)


def test_lista_veiculos(client: TestClient, auth_headers: dict, veiculo_cadastrado: dict):
    client.post("/veiculos", json=dados_veiculo(placa="XYZ9876", modelo="Polo"), headers=auth_headers)

    response = client.get("/veiculos", headers=auth_headers)

    assert response.status_code == 200
    assert [veiculo["placa"] for veiculo in response.json()] == ["ABC1D23", "XYZ9876"]


def test_filtra_veiculos_por_status(client: TestClient, auth_headers: dict, veiculo_cadastrado: dict):
    vendido = client.post("/veiculos", json=dados_veiculo(placa="XYZ9876"), headers=auth_headers).json()
    client.put(f"/veiculos/{vendido['id']}", json=dados_veiculo(placa="XYZ9876", status="vendido"), headers=auth_headers)

    response = client.get("/veiculos", params={"status": "vendido"}, headers=auth_headers)

    assert response.status_code == 200
    assert [veiculo["id"] for veiculo in response.json()] == [vendido["id"]]


def test_busca_veiculo_por_id(client: TestClient, auth_headers: dict, veiculo_cadastrado: dict):
    response = client.get(f"/veiculos/{veiculo_cadastrado['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == veiculo_cadastrado


@pytest.mark.parametrize(
    "metodo, corpo",
    [
        ("GET", None),
        ("PUT", dados_veiculo(status="disponivel")),
        ("DELETE", None),
    ],
)
def test_veiculo_inexistente_retorna_404(client: TestClient, auth_headers: dict, metodo: str, corpo: dict | None):
    response = client.request(metodo, "/veiculos/999", json=corpo, headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Veículo não encontrado."}


def test_atualiza_veiculo(client: TestClient, auth_headers: dict, veiculo_cadastrado: dict):
    novos_dados = dados_veiculo(cor="Preto", preco=52990.90, status="vendido")

    response = client.put(f"/veiculos/{veiculo_cadastrado['id']}", json=novos_dados, headers=auth_headers)

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["cor"] == "Preto"
    assert corpo["preco"] == 52990.9
    assert corpo["status"] == "vendido"


def test_atualizacao_rejeita_placa_de_outro_veiculo(client: TestClient, auth_headers: dict, veiculo_cadastrado: dict):
    outro = client.post("/veiculos", json=dados_veiculo(placa="XYZ9876"), headers=auth_headers).json()

    response = client.put(
        f"/veiculos/{outro['id']}",
        json=dados_veiculo(placa="ABC1D23", status="disponivel"),
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Já existe um veículo com a placa ABC1D23."}


def test_exclui_veiculo_disponivel(client: TestClient, auth_headers: dict, veiculo_cadastrado: dict):
    url = f"/veiculos/{veiculo_cadastrado['id']}"

    response = client.delete(url, headers=auth_headers)

    assert response.status_code == 204
    assert client.get(url, headers=auth_headers).status_code == 404


def test_nao_exclui_veiculo_vendido(client: TestClient, auth_headers: dict, veiculo_cadastrado: dict):
    url = f"/veiculos/{veiculo_cadastrado['id']}"
    client.put(url, json=dados_veiculo(status="vendido"), headers=auth_headers)

    response = client.delete(url, headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {"detail": "Não é possível excluir um veículo vendido."}
    assert client.get(url, headers=auth_headers).status_code == 200


@pytest.mark.parametrize(
    "metodo, url",
    [
        ("GET", "/veiculos"),
        ("POST", "/veiculos"),
        ("GET", "/veiculos/1"),
        ("PUT", "/veiculos/1"),
        ("DELETE", "/veiculos/1"),
        ("PUT", "/veiculos/1/imagem"),
        ("DELETE", "/veiculos/1/imagem"),
    ],
)
def test_rotas_de_veiculos_exigem_autenticacao(client: TestClient, metodo: str, url: str):
    response = client.request(metodo, url)

    assert response.status_code == 401
    assert response.json() == {"detail": "Não autenticado."}
