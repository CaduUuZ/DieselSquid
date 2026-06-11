"""
Schemas Pydantic para Veículos.

Novidade aqui: VeiculoOut inclui um objeto aninhado 'ClienteResumo'
para não retornar todos os dados do cliente, só o essencial.
Isso é o equivalente ao 'select' do Prisma ou ao .populate() do Mongoose.
"""
from datetime import datetime
from pydantic import BaseModel, field_validator
import re


class ClienteResumo(BaseModel):
    """Usado dentro de VeiculoOut — evita dados desnecessários na resposta."""
    id: int
    nome: str
    cpf: str
    telefone: str | None

    model_config = {"from_attributes": True}


class VeiculoCreate(BaseModel):
    cliente_id: int
    placa: str
    marca: str
    modelo: str
    ano: int
    cor: str | None = None
    km_atual: int = 0
    observacoes: str | None = None

    @field_validator("placa")
    @classmethod
    def normalizar_placa(cls, v: str) -> str:
        """Aceita formato antigo (ABC-1234) e Mercosul (ABC1D23). Guarda sem hífen."""
        placa = re.sub(r"[-\s]", "", v).upper()
        if not re.match(r"^[A-Z]{3}\d{4}$|^[A-Z]{3}\d[A-Z]\d{2}$", placa):
            raise ValueError("Placa inválida — use ABC1234 ou ABC1D23")
        return placa

    @field_validator("ano")
    @classmethod
    def validar_ano(cls, v: int) -> int:
        if not (1900 <= v <= 2100):
            raise ValueError("Ano inválido")
        return v

    @field_validator("km_atual")
    @classmethod
    def validar_km(cls, v: int) -> int:
        if v < 0:
            raise ValueError("KM não pode ser negativo")
        return v


class VeiculoUpdate(BaseModel):
    cor: str | None = None
    km_atual: int | None = None
    observacoes: str | None = None


class VeiculoOut(BaseModel):
    id: int
    placa: str
    marca: str
    modelo: str
    ano: int
    cor: str | None
    km_atual: int
    observacoes: str | None
    created_at: datetime
    updated_at: datetime
    cliente: ClienteResumo

    model_config = {"from_attributes": True}
