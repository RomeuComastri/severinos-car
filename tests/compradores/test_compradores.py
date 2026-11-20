import pytest
from fastapi.testclient import TestClient

from tests.compradores.conftest import OUTRO_CPF_VALIDO, dados_comprador, mensagens_de_erro

CPF_DUPLICADO = {"detail": "Já existe um comprador com este CPF."}


def test_cadastra_comprador_valido(client: TestClient, auth_headers: dict):
    response = client.post("/compradores", json=dados_comprador(), headers=auth_headers)

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["id"] > 0
    assert corpo["nome"] == "Maria Souza"
    assert corpo["cpf"] == "52998224725"
    assert corpo["email"] == "maria@email.com"
    assert corpo["criado_em"]


def test_cadastra_comprador_com_cpf_formatado_e_salva_somente_digitos(client: TestClient, auth_headers: dict):
    response = client.post("/compradores", json=dados_comprador(cpf="529.982.247-25"), headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["cpf"] == "52998224725"


def test_email_e_salvo_em_minusculas_e_sem_espacos(client: TestClient, auth_headers: dict):
    response = client.post("/compradores", json=dados_comprador(email="  Maria@Email.COM "), headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["email"] == "maria@email.com"


@pytest.mark.parametrize(
    "cpf",
    ["", "52998224724", "5299822472", "529982247251", "abcdefghijk", "529.982.247-2x", "11111111111", "00000000000"],
)
def test_rejeita_cpf_invalido(client: TestClient, auth_headers: dict, cpf: str):
    response = client.post("/compradores", json=dados_comprador(cpf=cpf), headers=auth_headers)

    assert response.status_code == 422
    assert "Value error, CPF inválido." in mensagens_de_erro(response)


@pytest.mark.parametrize("email", ["", "maria", "maria@", "@email.com", "maria@@email.com", "maria silva@email.com"])
def test_rejeita_email_invalido(client: TestClient, auth_headers: dict, email: str):
    response = client.post("/compradores", json=dados_comprador(email=email), headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "email"]


@pytest.mark.parametrize("campo", ["nome", "cpf", "email"])
def test_rejeita_cadastro_sem_campo_obrigatorio(client: TestClient, auth_headers: dict, campo: str):
    dados = dados_comprador()
    del dados[campo]

    response = client.post("/compradores", json=dados, headers=auth_headers)

    assert response.status_code == 422


def test_rejeita_nome_vazio(client: TestClient, auth_headers: dict):
    response = client.post("/compradores", json=dados_comprador(nome="   "), headers=auth_headers)

    assert response.status_code == 422


def test_rejeita_cpf_duplicado(client: TestClient, auth_headers: dict, comprador_cadastrado: dict):
    response = client.post("/compradores", json=dados_comprador(nome="Outra Maria"), headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == CPF_DUPLICADO


def test_rejeita_cpf_duplicado_mesmo_com_formatacao_diferente(
    client: TestClient, auth_headers: dict, comprador_cadastrado: dict
):
    response = client.post("/compradores", json=dados_comprador(cpf="529.982.247-25"), headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == CPF_DUPLICADO


def test_lista_compradores(client: TestClient, auth_headers: dict, comprador_cadastrado: dict):
    client.post("/compradores", json=dados_comprador(nome="João Lima", cpf=OUTRO_CPF_VALIDO), headers=auth_headers)

    response = client.get("/compradores", headers=auth_headers)

    assert response.status_code == 200
    assert [comprador["cpf"] for comprador in response.json()] == ["52998224725", OUTRO_CPF_VALIDO]


def test_lista_vazia_quando_nao_ha_compradores(client: TestClient, auth_headers: dict):
    response = client.get("/compradores", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_busca_comprador_por_id(client: TestClient, auth_headers: dict, comprador_cadastrado: dict):
    response = client.get(f"/compradores/{comprador_cadastrado['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == comprador_cadastrado


@pytest.mark.parametrize(
    "metodo, corpo",
    [
        ("GET", None),
        ("PUT", dados_comprador()),
        ("DELETE", None),
    ],
)
def test_comprador_inexistente_retorna_404(client: TestClient, auth_headers: dict, metodo: str, corpo: dict | None):
    response = client.request(metodo, "/compradores/999", json=corpo, headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Comprador não encontrado."}


def test_atualiza_comprador(client: TestClient, auth_headers: dict, comprador_cadastrado: dict):
    novos_dados = dados_comprador(nome="Maria Souza Lima", cpf=OUTRO_CPF_VALIDO, email="maria.lima@email.com")

    response = client.put(f"/compradores/{comprador_cadastrado['id']}", json=novos_dados, headers=auth_headers)

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["id"] == comprador_cadastrado["id"]
    assert corpo["nome"] == "Maria Souza Lima"
    assert corpo["cpf"] == OUTRO_CPF_VALIDO
    assert corpo["email"] == "maria.lima@email.com"


def test_atualizacao_mantendo_o_proprio_cpf_nao_e_duplicidade(
    client: TestClient, auth_headers: dict, comprador_cadastrado: dict
):
    response = client.put(
        f"/compradores/{comprador_cadastrado['id']}",
        json=dados_comprador(nome="Maria S."),
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["nome"] == "Maria S."


def test_atualizacao_rejeita_cpf_de_outro_comprador(client: TestClient, auth_headers: dict, comprador_cadastrado: dict):
    outro = client.post("/compradores", json=dados_comprador(cpf=OUTRO_CPF_VALIDO), headers=auth_headers).json()

    response = client.put(f"/compradores/{outro['id']}", json=dados_comprador(), headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == CPF_DUPLICADO


def test_atualizacao_rejeita_cpf_invalido(client: TestClient, auth_headers: dict, comprador_cadastrado: dict):
    response = client.put(
        f"/compradores/{comprador_cadastrado['id']}",
        json=dados_comprador(cpf="52998224724"),
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert "Value error, CPF inválido." in mensagens_de_erro(response)


def test_exclui_comprador_sem_vendas(client: TestClient, auth_headers: dict, comprador_cadastrado: dict):
    url = f"/compradores/{comprador_cadastrado['id']}"

    response = client.delete(url, headers=auth_headers)

    assert response.status_code == 204
    assert client.get(url, headers=auth_headers).status_code == 404


def test_nao_exclui_comprador_com_venda_registrada(
    client: TestClient, auth_headers: dict, comprador_cadastrado: dict, registrar_venda
):
    url = f"/compradores/{comprador_cadastrado['id']}"
    registrar_venda(comprador_cadastrado["id"])

    response = client.delete(url, headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {"detail": "Não é possível excluir um comprador com vendas registradas."}
    assert client.get(url, headers=auth_headers).status_code == 200


def test_exclui_comprador_sem_vendas_mesmo_que_outro_comprador_tenha(
    client: TestClient, auth_headers: dict, comprador_cadastrado: dict, registrar_venda
):
    outro = client.post("/compradores", json=dados_comprador(cpf=OUTRO_CPF_VALIDO), headers=auth_headers).json()
    registrar_venda(outro["id"])

    response = client.delete(f"/compradores/{comprador_cadastrado['id']}", headers=auth_headers)

    assert response.status_code == 204


@pytest.mark.parametrize(
    "metodo, url",
    [
        ("GET", "/compradores"),
        ("POST", "/compradores"),
        ("GET", "/compradores/1"),
        ("PUT", "/compradores/1"),
        ("DELETE", "/compradores/1"),
    ],
)
def test_rotas_de_compradores_exigem_autenticacao(client: TestClient, metodo: str, url: str):
    response = client.request(metodo, url)

    assert response.status_code == 401
    assert response.json() == {"detail": "Não autenticado."}
