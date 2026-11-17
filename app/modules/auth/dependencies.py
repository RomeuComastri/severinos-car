import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import JwtNotConfiguredError, TokenInvalidoError, decodificar_access_token
from app.modules.auth import repository
from app.modules.auth.models import Usuario

logger = logging.getLogger(__name__)

# auto_error=False: quando o header falta (ou não é "Bearer"), o FastAPI devolve None em vez de
# responder sozinho. Assim garantimos o status 401 com a nossa mensagem.
bearer_scheme = HTTPBearer(auto_error=False, description="Token obtido em POST /auth/login")


def _nao_autorizado() -> HTTPException:
    """Resposta padrão para qualquer falha de autenticação (sem token, token inválido ou expirado,
    usuário inexistente ou desativado)."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credenciais: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Exige um token válido e devolve o usuário logado.

    Uso em um módulo inteiro (em app/main.py):
        app.include_router(veiculos_router, dependencies=[Depends(get_current_user)])

    Uso em uma rota que precisa saber quem está logado:
        def minha_rota(usuario: Usuario = Depends(get_current_user)): ...
    """
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
