import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

TAMANHO_CPF = 11
TAMANHO_MAXIMO_EMAIL = 255
CARACTERES_DE_FORMATACAO_DO_CPF = re.compile(r"[.\-\s]")
PADRAO_CPF = re.compile(r"[0-9]{11}")


def _calcular_digito_verificador(base: str) -> str:
    """Módulo 11, com pesos decrescentes de len(base) + 1 até 2."""
    pesos = range(len(base) + 1, 1, -1)
    soma = sum(int(digito) * peso for digito, peso in zip(base, pesos))
    resto = (soma * 10) % 11
    return str(0 if resto == 10 else resto)


def validar_cpf(cpf: str) -> bool:
    """Recebe o CPF somente com dígitos e confere o tamanho e os dois dígitos verificadores."""
    if not PADRAO_CPF.fullmatch(cpf):
        return False
    if cpf == cpf[0] * TAMANHO_CPF:
        return False
    primeiro = _calcular_digito_verificador(cpf[:9])
    segundo = _calcular_digito_verificador(cpf[:9] + primeiro)
    return cpf[9:] == primeiro + segundo


class CompradorCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(min_length=1, max_length=100, examples=["Maria Souza"])
    cpf: str = Field(examples=["529.982.247-25"])
    email: EmailStr = Field(examples=["maria@email.com"])

    @field_validator("cpf")
    @classmethod
    def normalizar_e_validar_cpf(cls, valor: str) -> str:
        cpf = CARACTERES_DE_FORMATACAO_DO_CPF.sub("", valor)
        if not validar_cpf(cpf):
            raise ValueError("CPF inválido.")
        return cpf

    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, valor):
        return valor.strip().lower() if isinstance(valor, str) else valor

    @field_validator("email")
    @classmethod
    def validar_tamanho_do_email(cls, valor: str) -> str:
        if len(valor) > TAMANHO_MAXIMO_EMAIL:
            raise ValueError(f"O e-mail deve ter no máximo {TAMANHO_MAXIMO_EMAIL} caracteres.")
        return valor


class CompradorUpdate(CompradorCreate):
    pass


class CompradorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf: str
    email: str
    criado_em: datetime
