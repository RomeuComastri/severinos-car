from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.compradores import service
from app.modules.compradores.models import Comprador
from app.modules.compradores.schemas import CompradorCreate, CompradorResponse, CompradorUpdate

router = APIRouter(
    prefix="/compradores",
    tags=["Compradores"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Token ausente, inválido ou expirado"},
    },
)

NAO_ENCONTRADO = {status.HTTP_404_NOT_FOUND: {"description": "Comprador não encontrado"}}
CPF_DUPLICADO = {status.HTTP_400_BAD_REQUEST: {"description": "CPF já cadastrado"}}


def _erro(status_code: int, erro: Exception) -> HTTPException:
    return HTTPException(status_code=status_code, detail=str(erro))


@router.post(
    "",
    response_model=CompradorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um comprador",
    responses=CPF_DUPLICADO,
)
def criar(dados: CompradorCreate, db: Session = Depends(get_db)) -> Comprador:
    try:
        return service.criar(db, dados)
    except service.CpfJaCadastradoError as erro:
        raise _erro(status.HTTP_400_BAD_REQUEST, erro)


@router.get("", response_model=list[CompradorResponse], summary="Lista os compradores")
def listar(db: Session = Depends(get_db)) -> list[Comprador]:
    return service.listar(db)


@router.get(
    "/{comprador_id}",
    response_model=CompradorResponse,
    summary="Busca um comprador pelo ID",
    responses=NAO_ENCONTRADO,
)
def obter(comprador_id: int, db: Session = Depends(get_db)) -> Comprador:
    try:
        return service.obter(db, comprador_id)
    except service.CompradorNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)


@router.put(
    "/{comprador_id}",
    response_model=CompradorResponse,
    summary="Atualiza um comprador",
    responses={**NAO_ENCONTRADO, **CPF_DUPLICADO},
)
def atualizar(comprador_id: int, dados: CompradorUpdate, db: Session = Depends(get_db)) -> Comprador:
    try:
        return service.atualizar(db, comprador_id, dados)
    except service.CompradorNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
    except service.CpfJaCadastradoError as erro:
        raise _erro(status.HTTP_400_BAD_REQUEST, erro)


@router.delete(
    "/{comprador_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui um comprador",
    responses={
        **NAO_ENCONTRADO,
        status.HTTP_400_BAD_REQUEST: {"description": "Comprador com vendas registradas"},
    },
)
def excluir(comprador_id: int, db: Session = Depends(get_db)) -> None:
    try:
        service.excluir(db, comprador_id)
    except service.CompradorNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
    except service.CompradorComVendasError as erro:
        raise _erro(status.HTTP_400_BAD_REQUEST, erro)
