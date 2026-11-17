import logging

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.storage import StorageError, StorageNotConfiguredError, SupabaseStorage, get_storage
from app.modules.veiculos import service
from app.modules.veiculos.models import StatusVeiculo, Veiculo
from app.modules.veiculos.schemas import VeiculoCreate, VeiculoResponse, VeiculoUpdate

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/veiculos",
    tags=["Veículos"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Token ausente, inválido ou expirado"},
    },
)

NAO_ENCONTRADO = {status.HTTP_404_NOT_FOUND: {"description": "Veículo não encontrado"}}


def _erro(status_code: int, erro: Exception) -> HTTPException:
    return HTTPException(status_code=status_code, detail=str(erro))


@router.post(
    "",
    response_model=VeiculoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um veículo",
    responses={status.HTTP_400_BAD_REQUEST: {"description": "Placa já cadastrada"}},
)
def criar(dados: VeiculoCreate, db: Session = Depends(get_db)) -> Veiculo:
    try:
        return service.criar(db, dados)
    except service.PlacaJaCadastradaError as erro:
        raise _erro(status.HTTP_400_BAD_REQUEST, erro)


@router.get("", response_model=list[VeiculoResponse], summary="Lista os veículos")
def listar(
    status_veiculo: StatusVeiculo | None = Query(None, alias="status", description="Filtra pelo status"),
    db: Session = Depends(get_db),
) -> list[Veiculo]:
    return service.listar(db, status_veiculo)


@router.get(
    "/{veiculo_id}",
    response_model=VeiculoResponse,
    summary="Busca um veículo pelo ID",
    responses=NAO_ENCONTRADO,
)
def obter(veiculo_id: int, db: Session = Depends(get_db)) -> Veiculo:
    try:
        return service.obter(db, veiculo_id)
    except service.VeiculoNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)


@router.put(
    "/{veiculo_id}",
    response_model=VeiculoResponse,
    summary="Atualiza um veículo",
    responses={**NAO_ENCONTRADO, status.HTTP_400_BAD_REQUEST: {"description": "Placa já cadastrada"}},
)
def atualizar(veiculo_id: int, dados: VeiculoUpdate, db: Session = Depends(get_db)) -> Veiculo:
    try:
        return service.atualizar(db, veiculo_id, dados)
    except service.VeiculoNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
    except service.PlacaJaCadastradaError as erro:
        raise _erro(status.HTTP_400_BAD_REQUEST, erro)


@router.delete(
    "/{veiculo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui um veículo",
    responses={**NAO_ENCONTRADO, status.HTTP_400_BAD_REQUEST: {"description": "Veículo vendido"}},
)
def excluir(
    veiculo_id: int,
    db: Session = Depends(get_db),
    storage: SupabaseStorage = Depends(get_storage),
) -> None:
    try:
        service.excluir(db, veiculo_id, storage)
    except service.VeiculoNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
    except service.VeiculoVendidoError as erro:
        raise _erro(status.HTTP_400_BAD_REQUEST, erro)


@router.put(
    "/{veiculo_id}/imagem",
    response_model=VeiculoResponse,
    summary="Envia ou substitui a imagem do veículo",
    responses={
        **NAO_ENCONTRADO,
        status.HTTP_400_BAD_REQUEST: {"description": "Arquivo vazio, maior que 5 MB ou em formato não suportado"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Serviço de imagens indisponível"},
    },
)
def enviar_imagem(
    veiculo_id: int,
    arquivo: UploadFile = File(description="Imagem JPEG, PNG ou WEBP de até 5 MB"),
    db: Session = Depends(get_db),
    storage: SupabaseStorage = Depends(get_storage),
) -> Veiculo:
    conteudo = arquivo.file.read(service.TAMANHO_MAXIMO_IMAGEM + 1)
    try:
        return service.definir_imagem(db, veiculo_id, conteudo, storage)
    except service.VeiculoNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
    except service.ImagemInvalidaError as erro:
        raise _erro(status.HTTP_400_BAD_REQUEST, erro)
    except (StorageNotConfiguredError, StorageError):
        logger.exception("Falha ao enviar a imagem do veículo %s", veiculo_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de imagens indisponível.",
        )


@router.delete(
    "/{veiculo_id}/imagem",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a imagem do veículo",
    responses=NAO_ENCONTRADO,
)
def remover_imagem(
    veiculo_id: int,
    db: Session = Depends(get_db),
    storage: SupabaseStorage = Depends(get_storage),
) -> None:
    try:
        service.remover_imagem(db, veiculo_id, storage)
    except service.VeiculoNaoEncontradoError as erro:
        raise _erro(status.HTTP_404_NOT_FOUND, erro)
