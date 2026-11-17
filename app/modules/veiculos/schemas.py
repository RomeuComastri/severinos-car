import re
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

from app.modules.veiculos.models import StatusVeiculo

PADRAO_PLACA = re.compile(r"[A-Z]{3}[0-9][A-Z0-9][0-9]{2}")
ANO_MINIMO = 1900


class VeiculoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    placa: str = Field(examples=["ABC1D23"])
    marca: str = Field(min_length=1, max_length=50, examples=["Volkswagen"])
    modelo: str = Field(min_length=1, max_length=50, examples=["Gol"])
    ano: int = Field(examples=[2022])
    cor: str = Field(min_length=1, max_length=30, examples=["Prata"])
    preco: Decimal = Field(max_digits=12, decimal_places=2, examples=[55000.00])

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, valor: str) -> str:
        placa = valor.upper().replace("-", "").replace(" ", "")
        if not PADRAO_PLACA.fullmatch(placa):
            raise ValueError("Placa inválida. Use o formato ABC1234 ou ABC1D23.")
        return placa

    @field_validator("ano")
    @classmethod
    def validar_ano(cls, valor: int) -> int:
        ano_maximo = date.today().year + 1
        if not ANO_MINIMO <= valor <= ano_maximo:
            raise ValueError(f"O ano deve estar entre {ANO_MINIMO} e {ano_maximo}.")
        return valor

    @field_validator("preco")
    @classmethod
    def validar_preco(cls, valor: Decimal) -> Decimal:
        if valor <= 0:
            raise ValueError("O preço deve ser maior que zero.")
        return valor


class VeiculoUpdate(VeiculoCreate):
    status: StatusVeiculo


class VeiculoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    placa: str
    marca: str
    modelo: str
    ano: int
    cor: str
    preco: Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
    status: StatusVeiculo
    imagem_url: str | None
    criado_em: datetime
