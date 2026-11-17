"""Comandos de terminal do módulo de autenticação.

Criar um usuário (a senha é pedida de forma oculta, sem ficar no histórico do terminal):
    python -m app.modules.auth.cli criar-usuario --nome "João Silva" --email joao@loja.com

O comando grava no banco configurado em DATABASE_URL (arquivo .env).
"""

import argparse
import getpass
import sys
from collections.abc import Callable

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.core.database import DatabaseNotConfiguredError, get_session_factory
from app.core.security import SenhaMuitoLongaError
from app.modules.auth import service

_validador_email = TypeAdapter(EmailStr)


def _erro(mensagem: str) -> int:
    print(f"Erro: {mensagem}", file=sys.stderr)
    return 1


def criar_usuario(
    db: Session,
    nome: str,
    email: str,
    ler_senha: Callable[[str], str] = getpass.getpass,
) -> int:
    """Pede a senha duas vezes e cria o usuário. Devolve 0 em caso de sucesso e 1 em caso de erro."""
    try:
        _validador_email.validate_python(email)
    except ValidationError:
        return _erro(f"e-mail inválido: {email}")

    senha = ler_senha("Senha: ")
    if senha != ler_senha("Confirme a senha: "):
        return _erro("as senhas não conferem.")

    try:
        usuario = service.criar_usuario(db, nome=nome, email=email, senha=senha)
    except (service.SenhaFracaError, SenhaMuitoLongaError, service.EmailJaCadastradoError) as erro:
        return _erro(str(erro))

    print(f"Usuário criado: id={usuario.id}, nome={usuario.nome}, email={usuario.email}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.modules.auth.cli")
    comandos = parser.add_subparsers(dest="comando", required=True)

    criar = comandos.add_parser("criar-usuario", help="Cria um usuário que pode fazer login na API")
    criar.add_argument("--nome", required=True)
    criar.add_argument("--email", required=True)

    args = parser.parse_args(argv)

    try:
        db = get_session_factory()()
    except DatabaseNotConfiguredError as erro:
        return _erro(f"{erro} Configure o arquivo .env antes de executar o comando.")

    try:
        return criar_usuario(db, nome=args.nome, email=args.email)
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
