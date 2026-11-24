import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Venda(Base):
    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    veiculo_id: Mapped[int] = mapped_column(Integer, ForeignKey("veiculos.id"), unique=True, index=True)
    comprador_id: Mapped[int] = mapped_column(Integer, ForeignKey("compradores.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    forma_pagamento: Mapped[str] = mapped_column(String(50))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
