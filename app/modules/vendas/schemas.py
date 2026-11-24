from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator


class VendaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    veiculo_id: int = Field(gt=0)
    comprador_id: int = Field(gt=0)
    data: date
    valor: Decimal = Field(max_digits=12, decimal_places=2)
    forma_pagamento: str = Field(min_length=1, max_length=50)

    @field_validator("valor")
    @classmethod
    def validar_valor(cls, valor: Decimal) -> Decimal:
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")
        return valor


class VendaUpdate(VendaCreate):
    pass


class VendaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    veiculo_id: int
    comprador_id: int
    data: date
    valor: Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
    forma_pagamento: str
    criado_em: datetime
