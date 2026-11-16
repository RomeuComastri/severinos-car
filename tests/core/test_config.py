import pytest

from app.core import database
from app.core.config import Settings
from app.core.database import DatabaseNotConfiguredError


@pytest.mark.parametrize(
    "url_entrada, url_esperada",
    [
        ("postgresql://u:s@host:5432/db", "postgresql+psycopg://u:s@host:5432/db"),
        ("postgres://u:s@host:5432/db", "postgresql+psycopg://u:s@host:5432/db"),
        ("postgresql+psycopg://u:s@host:5432/db", "postgresql+psycopg://u:s@host:5432/db"),
    ],
)
def test_url_do_supabase_e_convertida_para_driver_psycopg(url_entrada, url_esperada):
    settings = Settings(_env_file=None, database_url=url_entrada)

    assert settings.sqlalchemy_database_url == url_esperada


def test_url_do_banco_e_none_quando_nao_configurada():
    settings = Settings(_env_file=None, database_url=None)

    assert settings.sqlalchemy_database_url is None


def test_get_engine_lanca_erro_quando_database_url_nao_configurada(monkeypatch):
    monkeypatch.setattr(database, "get_settings", lambda: Settings(_env_file=None, database_url=None))
    database.get_engine.cache_clear()
    try:
        with pytest.raises(DatabaseNotConfiguredError):
            database.get_engine()
    finally:
        database.get_engine.cache_clear()
