from sqlalchemy.orm import Session

from app.core.security import (
    criar_access_token,
    gerar_hash_senha,
    simular_verificacao_de_senha,
    verificar_senha,
)
from app.modules.auth import repository
from app.modules.auth.models import Usuario

SENHA_MIN_CARACTERES = 8


class CredenciaisInvalidasError(Exception):
    """Usado para e-mail inexistente, senha incorreta e usuário inativo, sem revelar qual ocorreu."""


class EmailJaCadastradoError(Exception):
    pass


class SenhaFracaError(ValueError):
    pass


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def autenticar(db: Session, email: str, senha: str) -> str:
    usuario = repository.buscar_por_email(db, normalizar_email(email))

    if usuario is None:
        simular_verificacao_de_senha()
        raise CredenciaisInvalidasError()

    if not verificar_senha(senha, usuario.senha_hash) or not usuario.ativo:
        raise CredenciaisInvalidasError()

    return criar_access_token(subject=str(usuario.id))


def criar_usuario(db: Session, nome: str, email: str, senha: str) -> Usuario:
    email = normalizar_email(email)

    if len(senha) < SENHA_MIN_CARACTERES:
        raise SenhaFracaError(f"A senha deve ter pelo menos {SENHA_MIN_CARACTERES} caracteres.")

    if repository.buscar_por_email(db, email) is not None:
        raise EmailJaCadastradoError(f"Já existe um usuário com o e-mail {email}.")

    usuario = Usuario(nome=nome.strip(), email=email, senha_hash=gerar_hash_senha(senha))
    return repository.criar(db, usuario)
