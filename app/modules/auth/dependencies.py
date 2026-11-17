import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import JwtNotConfiguredError, TokenInvalidoError, decodificar_access_token
from app.modules.auth import repository
from app.modules.auth.models import Usuario

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False, description="Token obtido em POST /auth/login")


def _nao_autorizado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credenciais: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    if credenciais is None:
        raise _nao_autorizado()

    try:
        payload = decodificar_access_token(credenciais.credentials)
        usuario_id = int(payload["sub"])
    except (TokenInvalidoError, ValueError):
        raise _nao_autorizado()
    except JwtNotConfiguredError:
        logger.exception("JWT_SECRET_KEY não configurada: não é possível validar tokens")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticação indisponível.",
        )

    usuario = repository.buscar_por_id(db, usuario_id)
    if usuario is None or not usuario.ativo:
        raise _nao_autorizado()

    return usuario
