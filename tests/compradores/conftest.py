from collections.abc import Callable
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Column, Date, Integer, MetaData, Numeric, String, Table, insert
from sqlalchemy.orm import Session

DADOS_COMPRADOR = {
    "nome": "Maria Souza",
    "cpf": "52998224725",
    "email": "maria@email.com",
    "telefone": "(35) 99999-1234",
}

# Outro CPF válido, para cenários com dois compradores.
OUTRO_CPF_VALIDO = "11144477735"


def dados_comprador(**alteracoes) -> dict:
    return {**DADOS_COMPRADOR, **alteracoes}


def mensagens_de_erro(response) -> list[str]:
    return [erro["msg"] for erro in response.json()["detail"]]


@pytest.fixture
def comprador_cadastrado(client: TestClient, auth_headers: dict) -> dict:
    """Comprador com os dados de DADOS_COMPRADOR."""
    response = client.post("/compradores", json=DADOS_COMPRADOR, headers=auth_headers)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def registrar_venda(db_session: Session) -> Callable[[int], None]:
    """Registra uma venda para o comprador informado.

    O módulo de vendas pertence a outro integrante e ainda não existe. Esta fixture cria uma tabela
    "vendas" mínima (somente id e comprador_id), fora do Base.metadata, apenas para exercitar a regra
    de exclusão. Quando o model Venda for integrado, substitua a tabela abaixo por ele.
    """
    tabela_vendas = Table(
        "vendas",
        MetaData(),
        Column("id", Integer, primary_key=True),
        Column("veiculo_id", Integer, nullable=False),
        Column("comprador_id", Integer, nullable=False),
        Column("data", Date, nullable=False),
        Column("valor", Numeric(12, 2), nullable=False),
        Column("forma_pagamento", String(50), nullable=False),
    )
    tabela_vendas.create(bind=db_session.connection(), checkfirst=True)

    def registrar(comprador_id: int) -> None:
        db_session.execute(
            insert(tabela_vendas).values(
                veiculo_id=comprador_id,
                comprador_id=comprador_id,
                data=date(2026, 11, 23),
                valor=55000,
                forma_pagamento="Pix",
            )
        )
        db_session.commit()

    return registrar
