import pytest

from app.core.storage import StorageNotConfiguredError, SupabaseStorage

URL = "https://projeto.supabase.co"


def test_chave_secreta_nova_vai_somente_no_header_apikey():
    storage = SupabaseStorage(URL, "sb_secret_abc123", "veiculos")

    assert storage._headers() == {"apikey": "sb_secret_abc123"}


def test_chave_legada_service_role_vai_tambem_no_header_authorization():
    storage = SupabaseStorage(URL, "eyJhbGciOiJIUzI1NiJ9.payload.assinatura", "veiculos")

    headers = storage._headers()

    assert headers["apikey"] == "eyJhbGciOiJIUzI1NiJ9.payload.assinatura"
    assert headers["Authorization"] == "Bearer eyJhbGciOiJIUzI1NiJ9.payload.assinatura"


def test_converte_caminho_em_url_publica_e_vice_versa():
    storage = SupabaseStorage(URL, "sb_secret_abc123", "veiculos")

    url = storage.url_publica("1/foto.jpg")

    assert url == "https://projeto.supabase.co/storage/v1/object/public/veiculos/1/foto.jpg"
    assert storage.caminho_da_url(url) == "1/foto.jpg"
    assert storage.caminho_da_url("https://outro-site.com/foto.jpg") is None


def test_envio_sem_configuracao_lanca_erro():
    storage = SupabaseStorage(None, None, "veiculos")

    with pytest.raises(StorageNotConfiguredError):
        storage.enviar("1/foto.jpg", b"conteudo", "image/jpeg")
