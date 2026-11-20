from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.compradores import repository
from app.modules.compradores.models import Comprador
from app.modules.compradores.schemas import CompradorCreate, CompradorUpdate

MENSAGEM_CPF_DUPLICADO = "Já existe um comprador com este CPF."
MENSAGEM_COMPRADOR_COM_VENDAS = "Não é possível excluir um comprador com vendas registradas."


class CompradorNaoEncontradoError(Exception):
    pass


class CpfJaCadastradoError(Exception):
    pass


class CompradorComVendasError(Exception):
    pass


def listar(db: Session) -> list[Comprador]:
    return repository.listar(db)


def obter(db: Session, comprador_id: int) -> Comprador:
    comprador = repository.buscar_por_id(db, comprador_id)
    if comprador is None:
        raise CompradorNaoEncontradoError("Comprador não encontrado.")
    return comprador


def criar(db: Session, dados: CompradorCreate) -> Comprador:
    _garantir_cpf_disponivel(db, dados.cpf)
    comprador = Comprador(**dados.model_dump())
    return _salvar(db, comprador)


def atualizar(db: Session, comprador_id: int, dados: CompradorUpdate) -> Comprador:
    comprador = obter(db, comprador_id)
    if dados.cpf != comprador.cpf:
        _garantir_cpf_disponivel(db, dados.cpf)

    for campo, valor in dados.model_dump().items():
        setattr(comprador, campo, valor)
    return _salvar(db, comprador)


def excluir(db: Session, comprador_id: int) -> None:
    comprador = obter(db, comprador_id)
    if repository.possui_vendas(db, comprador.id):
        raise CompradorComVendasError(MENSAGEM_COMPRADOR_COM_VENDAS)

    try:
        repository.excluir(db, comprador)
    except IntegrityError as erro:
        # Rede de segurança: a chave estrangeira de vendas barrou uma venda criada após a checagem.
        db.rollback()
        raise CompradorComVendasError(MENSAGEM_COMPRADOR_COM_VENDAS) from erro


def _garantir_cpf_disponivel(db: Session, cpf: str) -> None:
    if repository.buscar_por_cpf(db, cpf) is not None:
        raise CpfJaCadastradoError(MENSAGEM_CPF_DUPLICADO)


def _salvar(db: Session, comprador: Comprador) -> Comprador:
    try:
        return repository.salvar(db, comprador)
    except IntegrityError as erro:
        db.rollback()
        raise CpfJaCadastradoError(MENSAGEM_CPF_DUPLICADO) from erro
