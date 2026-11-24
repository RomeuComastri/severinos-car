from sqlalchemy import column, exists, inspect, select, table
from sqlalchemy.orm import Session

from app.modules.compradores.models import Comprador

# Contrato com o módulo de vendas (veja "Integração com o módulo de vendas" no README):
# a tabela de vendas deve se chamar "vendas" e ter a coluna "comprador_id", chave estrangeira
# para compradores.id. Se o módulo de vendas usar outros nomes, ajuste somente estas constantes.
TABELA_VENDAS = "vendas"
COLUNA_COMPRADOR_NA_VENDA = "comprador_id"


def listar(db: Session) -> list[Comprador]:
    return list(db.scalars(select(Comprador).order_by(Comprador.id)))


def buscar_por_id(db: Session, comprador_id: int) -> Comprador | None:
    return db.get(Comprador, comprador_id)


def buscar_por_cpf(db: Session, cpf: str) -> Comprador | None:
    return db.scalar(select(Comprador).where(Comprador.cpf == cpf))


def possui_vendas(db: Session, comprador_id: int) -> bool:
    """Informa se existe alguma venda registrada para o comprador.

    Não importa nada do módulo de vendas: consulta a tabela pelo nome, e só se ela existir. Assim
    este módulo funciona antes de vendas ser integrado (sem tabela, não há vendas) e passa a
    bloquear a exclusão assim que a tabela for criada.
    """
    if not inspect(db.connection()).has_table(TABELA_VENDAS):
        return False

    vendas = table(TABELA_VENDAS, column(COLUNA_COMPRADOR_NA_VENDA))
    consulta = select(exists().where(vendas.c[COLUNA_COMPRADOR_NA_VENDA] == comprador_id))
    return bool(db.scalar(consulta))


def salvar(db: Session, comprador: Comprador) -> Comprador:
    db.add(comprador)
    db.commit()
    db.refresh(comprador)
    return comprador


def excluir(db: Session, comprador: Comprador) -> None:
    db.delete(comprador)
    db.commit()
