from datetime import datetime, timedelta, timezone
from functools import lru_cache

import bcrypt
import jwt

from app.core.config import get_settings

# O bcrypt só considera os primeiros 72 bytes da senha (e a versão 5.x lança erro acima disso).
BCRYPT_MAX_BYTES = 72


class JwtNotConfiguredError(RuntimeError):
    pass


class SenhaMuitoLongaError(ValueError):
    pass


class TokenInvalidoError(Exception):
    """Token ausente de campos obrigatórios, com assinatura inválida, expirado ou mal formado."""


def gerar_hash_senha(senha: str) -> str:
    senha_bytes = senha.encode("utf-8")
    if len(senha_bytes) > BCRYPT_MAX_BYTES:
        raise SenhaMuitoLongaError(f"A senha deve ter no máximo {BCRYPT_MAX_BYTES} bytes.")
    return bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    senha_bytes = senha.encode("utf-8")
    if len(senha_bytes) > BCRYPT_MAX_BYTES:
        return False
    return bcrypt.checkpw(senha_bytes, senha_hash.encode("utf-8"))


@lru_cache
def _hash_ficticio() -> str:
    return gerar_hash_senha("senha-ficticia-para-equalizar-o-tempo")


def simular_verificacao_de_senha() -> None:
    """Gasta o mesmo tempo de uma verificação real.

    Usado quando o e-mail não existe, para que o tempo de resposta não revele
    quais e-mails estão cadastrados (timing attack).
    """
    verificar_senha("senha-qualquer", _hash_ficticio())


def _chave_secreta() -> str:
    chave = get_settings().jwt_secret_key
    if not chave:
        raise JwtNotConfiguredError("JWT_SECRET_KEY não configurada.")
    return chave


def criar_access_token(subject: str) -> str:
    settings = get_settings()
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, _chave_secreta(), algorithm=settings.jwt_algorithm)


def decodificar_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            _chave_secreta(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]},
        )
    except jwt.PyJWTError as erro:
        raise TokenInvalidoError(str(erro)) from erro
