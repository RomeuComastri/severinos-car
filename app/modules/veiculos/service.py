import logging
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.storage import StorageError, StorageNotConfiguredError, SupabaseStorage
from app.modules.veiculos import repository
from app.modules.veiculos.models import StatusVeiculo, Veiculo
from app.modules.veiculos.schemas import VeiculoCreate, VeiculoUpdate

logger = logging.getLogger(__name__)

TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024


class VeiculoNaoEncontradoError(Exception):
    pass


class PlacaJaCadastradaError(Exception):
    pass


class VeiculoVendidoError(Exception):
    pass


class ImagemInvalidaError(Exception):
    pass


def listar(db: Session, status: StatusVeiculo | None = None) -> list[Veiculo]:
    return repository.listar(db, status)


def obter(db: Session, veiculo_id: int) -> Veiculo:
    veiculo = repository.buscar_por_id(db, veiculo_id)
    if veiculo is None:
        raise VeiculoNaoEncontradoError("Veículo não encontrado.")
    return veiculo


def criar(db: Session, dados: VeiculoCreate) -> Veiculo:
    _garantir_placa_disponivel(db, dados.placa)
    veiculo = Veiculo(**dados.model_dump(), status=StatusVeiculo.DISPONIVEL)
    return _salvar(db, veiculo)


def atualizar(db: Session, veiculo_id: int, dados: VeiculoUpdate) -> Veiculo:
    veiculo = obter(db, veiculo_id)
    if dados.placa != veiculo.placa:
        _garantir_placa_disponivel(db, dados.placa)

    for campo, valor in dados.model_dump().items():
        setattr(veiculo, campo, valor)
    return _salvar(db, veiculo)


def excluir(db: Session, veiculo_id: int, storage: SupabaseStorage) -> None:
    veiculo = obter(db, veiculo_id)
    if veiculo.status == StatusVeiculo.VENDIDO:
        raise VeiculoVendidoError("Não é possível excluir um veículo vendido.")

    imagem_url = veiculo.imagem_url
    repository.excluir(db, veiculo)
    if imagem_url:
        _remover_do_storage(storage, imagem_url)


def definir_imagem(db: Session, veiculo_id: int, conteudo: bytes, storage: SupabaseStorage) -> Veiculo:
    veiculo = obter(db, veiculo_id)
    extensao, content_type = validar_imagem(conteudo)

    caminho = f"{veiculo.id}/{uuid4().hex}.{extensao}"
    imagem_anterior = veiculo.imagem_url
    veiculo.imagem_url = storage.enviar(caminho, conteudo, content_type)

    try:
        veiculo = repository.salvar(db, veiculo)
    except Exception:
        db.rollback()
        _remover_do_storage(storage, storage.url_publica(caminho))
        raise

    if imagem_anterior:
        _remover_do_storage(storage, imagem_anterior)
    return veiculo


def remover_imagem(db: Session, veiculo_id: int, storage: SupabaseStorage) -> None:
    veiculo = obter(db, veiculo_id)
    imagem_url = veiculo.imagem_url
    if imagem_url is None:
        return

    veiculo.imagem_url = None
    repository.salvar(db, veiculo)
    _remover_do_storage(storage, imagem_url)


def validar_imagem(conteudo: bytes) -> tuple[str, str]:
    """Identifica o formato pelo conteúdo do arquivo, e não pela extensão informada pelo cliente."""
    if not conteudo:
        raise ImagemInvalidaError("O arquivo está vazio.")
    if len(conteudo) > TAMANHO_MAXIMO_IMAGEM:
        raise ImagemInvalidaError("A imagem deve ter no máximo 5 MB.")

    if conteudo.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "webp", "image/webp"
    raise ImagemInvalidaError("Formato não suportado. Envie uma imagem JPEG, PNG ou WEBP.")


def _garantir_placa_disponivel(db: Session, placa: str) -> None:
    if repository.buscar_por_placa(db, placa) is not None:
        raise PlacaJaCadastradaError(f"Já existe um veículo com a placa {placa}.")


def _salvar(db: Session, veiculo: Veiculo) -> Veiculo:
    placa = veiculo.placa
    try:
        return repository.salvar(db, veiculo)
    except IntegrityError as erro:
        db.rollback()
        raise PlacaJaCadastradaError(f"Já existe um veículo com a placa {placa}.") from erro


def _remover_do_storage(storage: SupabaseStorage, url: str) -> None:
    caminho = storage.caminho_da_url(url)
    if caminho is None:
        return
    try:
        storage.remover(caminho)
    except (StorageError, StorageNotConfiguredError):
        logger.warning("Não foi possível remover a imagem %s do Storage", caminho, exc_info=True)
