import os
from collections.abc import Generator

# Precisa vir ANTES de importar o app: get_settings() é chamada (e fica em cache) no import de
# app.main. Variáveis de ambiente têm prioridade sobre o .env, então os testes nunca usam a
# chave real. Na CI não existe .env, e é este valor que permite os testes rodarem.
CHAVE_JWT_DE_TESTE = "chave-secreta-usada-somente-nos-testes-automatizados"
os.environ["JWT_SECRET_KEY"] = CHAVE_JWT_DE_TESTE

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.modules.auth import service as auth_service
from app.modules.auth.models import Usuario

SENHA_DE_TESTE = "senhaDeTeste123"


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
def client(db_session: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def usuario_cadastrado(db_session: Session) -> Usuario:
    """Usuário ativo, com e-mail joao@loja.com e senha SENHA_DE_TESTE."""
    return auth_service.criar_usuario(db_session, nome="João", email="joao@loja.com", senha=SENHA_DE_TESTE)
