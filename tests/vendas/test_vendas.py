import pytest
from fastapi.testclient import TestClient

from tests.vendas.conftest import dados_venda
from tests.veiculos.conftest import dados_veiculo


def test_venda_valida_marca_veiculo_como_vendido(
    client: TestClient,
    auth_headers: dict,
    veiculo_disponivel: dict,
    comprador_cadastrado_para_venda: dict,
):
    response = client.post(
        "/vendas",
        json=dados_venda(veiculo_disponivel["id"], comprador_cadastrado_para_venda["id"]),
        headers=auth_headers,
    )

    assert response.status_code == 201
    venda = response.json()
    assert venda["veiculo_id"] == veiculo_disponivel["id"]
    assert venda["comprador_id"] == comprador_cadastrado_para_venda["id"]
    assert venda["valor"] == 55000.0

    veiculo = client.get(f"/veiculos/{veiculo_disponivel['id']}", headers=auth_headers)
    assert veiculo.status_code == 200
    assert veiculo.json()["status"] == "vendido"


def test_bloqueia_venda_de_veiculo_ja_vendido(
    client: TestClient,
    auth_headers: dict,
    veiculo_disponivel: dict,
    comprador_cadastrado_para_venda: dict,
):
    dados = dados_venda(veiculo_disponivel["id"], comprador_cadastrado_para_venda["id"])
    primeira = client.post("/vendas", json=dados, headers=auth_headers)
    segunda = client.post("/vendas", json=dados, headers=auth_headers)

    assert primeira.status_code == 201
    assert segunda.status_code == 400
    assert segunda.json() == {"detail": "Não é possível vender um veículo já vendido."}


def test_rejeita_valor_menor_ou_igual_a_zero(
    client: TestClient,
    auth_headers: dict,
    veiculo_disponivel: dict,
    comprador_cadastrado_para_venda: dict,
):
    response = client.post(
        "/vendas",
        json=dados_venda(veiculo_disponivel["id"], comprador_cadastrado_para_venda["id"], valor=0),
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert "O valor deve ser maior que zero." in str(response.json()["detail"])


@pytest.mark.parametrize("veiculo_id,comprador_id", [(999, 1), (1, 999)])
def test_rejeita_veiculo_ou_comprador_inexistente(
    client: TestClient,
    auth_headers: dict,
    veiculo_id: int,
    comprador_id: int,
):
    response = client.post(
        "/vendas",
        json=dados_venda(veiculo_id, comprador_id),
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_crud_e_cancelamento_retorna_veiculo_a_disponivel(
    client: TestClient,
    auth_headers: dict,
    veiculo_disponivel: dict,
    comprador_cadastrado_para_venda: dict,
):
    dados = dados_venda(veiculo_disponivel["id"], comprador_cadastrado_para_venda["id"])
    criada = client.post("/vendas", json=dados, headers=auth_headers)
    assert criada.status_code == 201
    venda_id = criada.json()["id"]

    listada = client.get("/vendas", headers=auth_headers)
    assert listada.status_code == 200
    assert len(listada.json()) == 1

    atualizada = client.put(
        f"/vendas/{venda_id}",
        json=dados_venda(veiculo_disponivel["id"], comprador_cadastrado_para_venda["id"], valor=60000),
        headers=auth_headers,
    )
    assert atualizada.status_code == 200
    assert atualizada.json()["valor"] == 60000.0

    excluida = client.delete(f"/vendas/{venda_id}", headers=auth_headers)
    assert excluida.status_code == 204

    veiculo = client.get(f"/veiculos/{veiculo_disponivel['id']}", headers=auth_headers)
    assert veiculo.json()["status"] == "disponivel"


def test_lista_todas_as_vendas(
    client: TestClient,
    auth_headers: dict,
    veiculo_disponivel: dict,
    comprador_cadastrado_para_venda: dict,
):
    segundo_veiculo = client.post(
        "/veiculos",
        json=dados_veiculo(placa="XYZ9876"),
        headers=auth_headers,
    )
    assert segundo_veiculo.status_code == 201

    primeira_venda = client.post(
        "/vendas",
        json=dados_venda(veiculo_disponivel["id"], comprador_cadastrado_para_venda["id"]),
        headers=auth_headers,
    )
    segunda_venda = client.post(
        "/vendas",
        json=dados_venda(segundo_veiculo.json()["id"], comprador_cadastrado_para_venda["id"]),
        headers=auth_headers,
    )

    response = client.get("/vendas", headers=auth_headers)

    assert primeira_venda.status_code == 201
    assert segunda_venda.status_code == 201
    assert response.status_code == 200
    assert [venda["id"] for venda in response.json()] == [
        primeira_venda.json()["id"],
        segunda_venda.json()["id"],
    ]


def test_venda_inexistente_retorna_404(client: TestClient, auth_headers: dict):
    response = client.get("/vendas/999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Venda não encontrada."}


@pytest.mark.parametrize(
    "metodo,url",
    [
        ("GET", "/vendas"),
        ("POST", "/vendas"),
        ("GET", "/vendas/1"),
        ("PUT", "/vendas/1"),
        ("DELETE", "/vendas/1"),
    ],
)
def test_rotas_de_vendas_exigem_autenticacao(client: TestClient, metodo: str, url: str):
    response = client.request(metodo, url)
    assert response.status_code == 401
