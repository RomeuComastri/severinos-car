from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Severinos Car API"
    database_url: str | None = None

    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_storage_bucket: str = "veiculos"

    @property
    def sqlalchemy_database_url(self) -> str | None:
        """Converte a URL do Supabase para o driver psycopg 3 usado pelo SQLAlchemy."""
        if not self.database_url:
            return None
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
