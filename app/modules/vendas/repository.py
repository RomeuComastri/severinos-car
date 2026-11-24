from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.vendas.models import Venda


def listar(db: Session) -> list[Venda]:
    return list(db.scalars(select(Venda).order_by(Venda.id)))


def buscar_por_id(db: Session, venda_id: int) -> Venda | None:
    return db.get(Venda, venda_id)


def buscar_por_veiculo(db: Session, veiculo_id: int) -> Venda | None:
    return db.scalar(select(Venda).where(Venda.veiculo_id == veiculo_id))


def salvar(db: Session, venda: Venda) -> Venda:
    db.add(venda)
    db.commit()
    db.refresh(venda)
    return venda


def excluir(db: Session, venda: Venda) -> None:
    db.delete(venda)
    db.commit()
