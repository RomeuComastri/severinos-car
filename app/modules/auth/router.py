import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import JwtNotConfiguredError
from app.modules.auth import service
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import Usuario
from app.modules.auth.schemas import LoginRequest, TokenResponse, UsuarioResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autentica o usuário e devolve um token JWT",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "E-mail ou senha inválidos"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Autenticação não configurada no servidor"},
    },
)
def login(dados: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        token = service.autenticar(db, dados.email, dados.senha)
    except service.CredenciaisInvalidasError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JwtNotConfiguredError:
        logger.exception("JWT_SECRET_KEY não configurada: não é possível emitir tokens")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticação indisponível.",
        )

    return TokenResponse(access_token=token, expires_in=get_settings().jwt_expire_minutes * 60)


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Retorna os dados do usuário logado",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Token ausente, inválido ou expirado"}},
)
def me(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    return usuario
