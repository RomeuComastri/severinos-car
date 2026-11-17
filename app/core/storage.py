from functools import lru_cache

import httpx

from app.core.config import get_settings


class StorageNotConfiguredError(RuntimeError):
    pass


class StorageError(RuntimeError):
    pass


class SupabaseStorage:
    def __init__(self, url: str | None, chave: str | None, bucket: str, timeout: float = 15.0):
        self._url = url.rstrip("/") if url else None
        self._chave = chave
        self._bucket = bucket
        self._timeout = timeout

    def enviar(self, caminho: str, conteudo: bytes, content_type: str) -> str:
        self._requisitar(
            "POST",
            f"{self._api()}/object/{self._bucket}/{caminho}",
            headers={**self._headers(), "Content-Type": content_type},
            content=conteudo,
        )
        return self.url_publica(caminho)

    def remover(self, caminho: str) -> None:
        self._requisitar(
            "DELETE",
            f"{self._api()}/object/{self._bucket}",
            headers=self._headers(),
            json={"prefixes": [caminho]},
        )

    def url_publica(self, caminho: str) -> str:
        return f"{self._prefixo_publico()}{caminho}"

    def caminho_da_url(self, url: str) -> str | None:
        if not self._url:
            return None
        prefixo = self._prefixo_publico()
        return url.removeprefix(prefixo) if url.startswith(prefixo) else None

    def _api(self) -> str:
        if not self._url or not self._chave:
            raise StorageNotConfiguredError("SUPABASE_URL e SUPABASE_SECRET_KEY não configuradas.")
        return f"{self._url}/storage/v1"

    def _prefixo_publico(self) -> str:
        return f"{self._url}/storage/v1/object/public/{self._bucket}/"

    def _headers(self) -> dict[str, str]:
        headers = {"apikey": self._chave}
        # A chave legada (service_role) é um JWT e também vai no Authorization; a nova (sb_secret_) não.
        if self._chave.startswith("eyJ"):
            headers["Authorization"] = f"Bearer {self._chave}"
        return headers

    def _requisitar(self, metodo: str, endpoint: str, **kwargs) -> None:
        try:
            resposta = httpx.request(metodo, endpoint, timeout=self._timeout, **kwargs)
            resposta.raise_for_status()
        except httpx.HTTPError as erro:
            raise StorageError(f"Falha na comunicação com o Supabase Storage: {erro}") from erro


@lru_cache
def get_storage() -> SupabaseStorage:
    settings = get_settings()
    return SupabaseStorage(
        settings.supabase_url,
        settings.supabase_secret_key,
        settings.supabase_storage_bucket,
    )
