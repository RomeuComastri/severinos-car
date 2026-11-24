from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.compradores.models import Comprador
from app.modules.veiculos.models import StatusVeiculo, Veiculo
from app.modules.vendas import repository
from app.modules.vendas.models import Venda
from app.modules.vendas.schemas import VendaCreate, VendaUpdate


class VendaNaoEncontradaError(Exception):
    pass


class VeiculoNaoEncontradoError(Exception):
    pass


class CompradorNaoEncontradoError(Exception):
    pass


class VeiculoNaoDisponivelError(Exception):
    pass


class VeiculoJaVendidoError(Exception):
    pass


def listar(db: Session) -> list[Venda]:
    return repository.listar(db)


def obter(db: Session, venda_id: int) -> Venda:
    venda = repository.buscar_por_id(db, venda_id)
    if venda is None:
        raise VendaNaoEncontradaError("Venda não encontrada.")
    return venda


def criar(db: Session, dados: VendaCreate) -> Venda:
    veiculo = _obter_veiculo(db, dados.veiculo_id)
    _obter_comprador(db, dados.comprador_id)
    if veiculo.status != StatusVeiculo.DISPONIVEL:
        raise VeiculoNaoDisponivelError("Não é possível vender um veículo já vendido.")

    venda = Venda(**dados.model_dump())
    veiculo.status = StatusVeiculo.VENDIDO

    try:
        return repository.salvar(db, venda)
    except IntegrityError as erro:
        db.rollback()
        if repository.buscar_por_veiculo(db, dados.veiculo_id) is not None:
            raise VeiculoJaVendidoError("Não é possível vender um veículo já vendido.") from erro
        raise


def atualizar(db: Session, venda_id: int, dados: VendaUpdate) -> Venda:
    venda = obter(db, venda_id)
    veiculo_anterior = db.get(Veiculo, venda.veiculo_id)

    novo_veiculo = _obter_veiculo(db, dados.veiculo_id)
    _obter_comprador(db, dados.comprador_id)

    if novo_veiculo.id != venda.veiculo_id and novo_veiculo.status != StatusVeiculo.DISPONIVEL:
        raise VeiculoNaoDisponivelError("Não é possível vender um veículo já vendido.")

    if veiculo_anterior is not None and novo_veiculo.id != veiculo_anterior.id:
        veiculo_anterior.status = StatusVeiculo.DISPONIVEL
    novo_veiculo.status = StatusVeiculo.VENDIDO

    for campo, valor in dados.model_dump().items():
        setattr(venda, campo, valor)

    try:
        return repository.salvar(db, venda)
    except IntegrityError as erro:
        db.rollback()
        raise VeiculoJaVendidoError("Não é possível vender um veículo já vendido.") from erro


def excluir(db: Session, venda_id: int) -> None:
    venda = obter(db, venda_id)
    veiculo = db.get(Veiculo, venda.veiculo_id)

    repository.excluir(db, venda)
    if veiculo is not None:
        veiculo.status = StatusVeiculo.DISPONIVEL
        db.commit()
        db.refresh(veiculo)


def _obter_veiculo(db: Session, veiculo_id: int) -> Veiculo:
    veiculo = db.get(Veiculo, veiculo_id)
    if veiculo is None:
        raise VeiculoNaoEncontradoError("Veículo não encontrado.")
    return veiculo


def _obter_comprador(db: Session, comprador_id: int) -> Comprador:
    comprador = db.get(Comprador, comprador_id)
    if comprador is None:
        raise CompradorNaoEncontradoError("Comprador não encontrado.")
    return comprador
