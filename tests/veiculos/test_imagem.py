import pytest
from fastapi.testclient import TestClient

from app.core.storage import SupabaseStorage, get_storage
from app.main import app
from app.modules.veiculos.service import TAMANHO_MAXIMO_IMAGEM
from tests.conftest import StorageFake
from tests.veiculos.conftest import IMAGEM_JPEG, IMAGEM_PNG, IMAGEM_WEBP

URL_PUBLICA_DO_BUCKET = "https://storage.teste/storage/v1/object/public/veiculos/"


def enviar_imagem(client: TestClient, veiculo_id: int, conteudo: bytes, headers: dict, nome: str = "foto.jpg"):
    return client.put(
        f"/veiculos/{veiculo_id}/imagem",
        files={"arquivo": (nome, conteudo, "image/jpeg")},
        headers=headers,
    )


@pytest.mark.parametrize(
    "conteudo, extensao",
    [(IMAGEM_JPEG, "jpg"), (IMAGEM_PNG, "png"), (IMAGEM_WEBP, "webp")],
)
def test_envia_imagem_e_salva_a_url_no_veiculo(
    client: TestClient,
    auth_headers: dict,
    veiculo_cadastrado: dict,
    storage_fake: StorageFake,
    conteudo: bytes,
    extensao: str,
):
    response = enviar_imagem(client, veiculo_cadastrado["id"], conteudo, auth_headers)

    assert response.status_code == 200
    imagem_url = response.json()["imagem_url"]
    assert imagem_url.startswith(f"{URL_PUBLICA_DO_BUCKET}{veiculo_cadastrado['id']}/")
    assert imagem_url.endswith(f".{extensao}")
    assert len(storage_fake.enviados) == 1


def test_rejeita_arquivo_que_nao_e_imagem(
    client: TestClient, auth_headers: dict, veiculo_cadastrado: dict, storage_fake: StorageFake
):
    response = enviar_imagem(client, veiculo_cadastrado["id"], b"%PDF-1.7 documento", auth_headers, nome="foto.jpg")

    assert response.status_code == 400
    assert response.json() == {"detail": "Formato não suportado. Envie uma imagem JPEG, PNG ou WEBP."}
    assert storage_fake.enviados == []


def test_rejeita_imagem_maior_que_5_mb(
    client: TestClient, auth_headers: dict, veiculo_cadastrado: dict, storage_fake: StorageFake
):
    imagem_grande = IMAGEM_JPEG + b"\x00" * TAMANHO_MAXIMO_IMAGEM

    response = enviar_imagem(client, veiculo_cadastrado["id"], imagem_grande, auth_headers)

    assert response.status_code == 400
    assert response.json() == {"detail": "A imagem deve ter no máximo 5 MB."}
    assert storage_fake.enviados == []


def test_envio_de_imagem_para_veiculo_inexistente_retorna_404(client: TestClient, auth_headers: dict):
    response = enviar_imagem(client, 999, IMAGEM_JPEG, auth_headers)

    assert response.status_code == 404


def test_substituir_imagem_remove_a_anterior_do_storage(
    client: TestClient, auth_headers: dict, veiculo_cadastrado: dict, storage_fake: StorageFake
):
    enviar_imagem(client, veiculo_cadastrado["id"], IMAGEM_JPEG, auth_headers)
    enviar_imagem(client, veiculo_cadastrado["id"], IMAGEM_PNG, auth_headers)

    assert len(storage_fake.enviados) == 2
    assert storage_fake.removidos == [storage_fake.enviados[0]]


def test_remove_imagem_do_veiculo(
    client: TestClient, auth_headers: dict, veiculo_cadastrado: dict, storage_fake: StorageFake
):
    url = f"/veiculos/{veiculo_cadastrado['id']}"
    enviar_imagem(client, veiculo_cadastrado["id"], IMAGEM_JPEG, auth_headers)

    response = client.delete(f"{url}/imagem", headers=auth_headers)

    assert response.status_code == 204
    assert client.get(url, headers=auth_headers).json()["imagem_url"] is None
    assert storage_fake.removidos == storage_fake.enviados


def test_excluir_veiculo_remove_a_imagem_do_storage(
    client: TestClient, auth_headers: dict, veiculo_cadastrado: dict, storage_fake: StorageFake
):
    enviar_imagem(client, veiculo_cadastrado["id"], IMAGEM_JPEG, auth_headers)

    response = client.delete(f"/veiculos/{veiculo_cadastrado['id']}", headers=auth_headers)

    assert response.status_code == 204
    assert storage_fake.removidos == storage_fake.enviados


def test_envio_de_imagem_sem_storage_configurado_retorna_503(
    client: TestClient, auth_headers: dict, veiculo_cadastrado: dict
):
    app.dependency_overrides[get_storage] = lambda: SupabaseStorage(None, None, "veiculos")

    response = enviar_imagem(client, veiculo_cadastrado["id"], IMAGEM_JPEG, auth_headers)

    assert response.status_code == 503
    assert response.json() == {"detail": "Serviço de imagens indisponível."}
