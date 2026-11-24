import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.vendas import service
from app.modules.vendas.models import Venda
from app.modules.vendas.schemas import VendaCreate, VendaResponse, VendaUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendas", tags=["Vendas"])

NAO_ENCONTRADA = {status.HTTP_404_NOT_FOUND: {"description": "Venda não encontrada"}}


def _erro(status_code: int, erro: Exception) -> HTTPException:
    return HTTPException(status_code=status_code, detail=str(erro))


@router.post("", response_model=VendaResponse, status_code=status.HTTP_201_CREATED)
def criar(dados: VendaCreate, db: Session = Depends(get_db)) -> Venda:
    try:
        return service.criar(db, dados)
    except service.VeiculoNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
    except service.CompradorNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
    except (service.VeiculoNaoDisponivelError, service.VeiculoJaVendidoError) as erro:
        raise _erro(status.HTTP_400_BAD_REQUEST, erro)


@router.get("", response_model=list[VendaResponse])
def listar(db: Session = Depends(get_db)) -> list[Venda]:
    return service.listar(db)


@router.get("/{venda_id}", response_model=VendaResponse, responses=NAO_ENCONTRADA)
def obter(venda_id: int, db: Session = Depends(get_db)) -> Venda:
    try:
        return service.obter(db, venda_id)
    except service.VendaNaoEncontradaError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)


@router.put("/{venda_id}", response_model=VendaResponse, responses=NAO_ENCONTRADA)
def atualizar(venda_id: int, dados: VendaUpdate, db: Session = Depends(get_db)) -> Venda:
    try:
        return service.atualizar(db, venda_id, dados)
    except service.VendaNaoEncontradaError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
    except service.VeiculoNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
    except service.CompradorNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
    except (service.VeiculoNaoDisponivelError, service.VeiculoJaVendidoError) as erro:
        raise _erro(status.HTTP_400_BAD_REQUEST, erro)


@router.delete("/{venda_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NAO_ENCONTRADA)
def excluir(venda_id: int, db: Session = Depends(get_db)) -> None:
    try:
        service.excluir(db, venda_id)
    except service.VendaNaoEncontradaError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
