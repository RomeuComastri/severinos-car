from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.veiculos.models import StatusVeiculo, Veiculo


def listar(db: Session, status: StatusVeiculo | None = None) -> list[Veiculo]:
    consulta = select(Veiculo).order_by(Veiculo.id)
    if status is not None:
        consulta = consulta.where(Veiculo.status == status)
    return list(db.scalars(consulta))


def buscar_por_id(db: Session, veiculo_id: int) -> Veiculo | None:
    return db.get(Veiculo, veiculo_id)


def buscar_por_placa(db: Session, placa: str) -> Veiculo | None:
    return db.scalar(select(Veiculo).where(Veiculo.placa == placa))


def salvar(db: Session, veiculo: Veiculo) -> Veiculo:
    db.add(veiculo)
    db.commit()
    db.refresh(veiculo)
    return veiculo


def excluir(db: Session, veiculo: Veiculo) -> None:
    db.delete(veiculo)
    db.commit()
