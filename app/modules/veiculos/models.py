import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StatusVeiculo(str, enum.Enum):
    DISPONIVEL = "disponivel"
    VENDIDO = "vendido"


class Veiculo(Base):
    __tablename__ = "veiculos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    placa: Mapped[str] = mapped_column(String(7), unique=True, index=True)
    marca: Mapped[str] = mapped_column(String(50))
    modelo: Mapped[str] = mapped_column(String(50))
    ano: Mapped[int] = mapped_column(Integer)
    cor: Mapped[str] = mapped_column(String(30))
    preco: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[StatusVeiculo] = mapped_column(
        Enum(
            StatusVeiculo,
            native_enum=False,
            length=10,
            values_callable=lambda status: [item.value for item in status],
        ),
        default=StatusVeiculo.DISPONIVEL,
    )
    imagem_url: Mapped[str | None] = mapped_column(String(500))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
