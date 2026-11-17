import os
from collections.abc import Generator

# Definida antes de importar o app, que lê as configurações no import. Os testes nunca usam a chave real.
os.environ["JWT_SECRET_KEY"] = "chave-secreta-usada-somente-nos-testes-automatizados"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import criar_access_token
from app.core.storage import SupabaseStorage, get_storage
from app.main import app
from app.modules.auth import service as auth_service
from app.modules.auth.models import Usuario

SENHA_DE_TESTE = "senhaDeTeste123"


class StorageFake(SupabaseStorage):
    """Registra os envios e remoções em memória, sem acessar o Supabase."""

    def __init__(self):
        super().__init__("https://storage.teste", "chave-de-teste", "veiculos")
        self.enviados: list[str] = []
        self.removidos: list[str] = []

    def enviar(self, caminho: str, conteudo: bytes, content_type: str) -> str:
        self.enviados.append(caminho)
        return self.url_publica(caminho)

    def remover(self, caminho: str) -> None:
        self.removidos.append(caminho)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Banco SQLite em memória, recriado a cada teste. Os testes nunca acessam o Supabase."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def storage_fake() -> StorageFake:
    return StorageFake()


@pytest.fixture
def client(db_session: Session, storage_fake: StorageFake) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_storage] = lambda: storage_fake
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def usuario_cadastrado(db_session: Session) -> Usuario:
    """Usuário ativo, com e-mail joao@loja.com e senha SENHA_DE_TESTE."""
    return auth_service.criar_usuario(db_session, nome="João", email="joao@loja.com", senha=SENHA_DE_TESTE)


@pytest.fixture
def auth_headers(usuario_cadastrado: Usuario) -> dict[str, str]:
    """Header Authorization com um token válido do usuario_cadastrado."""
    token = criar_access_token(subject=str(usuario_cadastrado.id))
    return {"Authorization": f"Bearer {token}"}
