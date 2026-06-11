"""
Schemas para Ordens de Serviço.

Novidade: campo 'status' tipado com o Enum — o Pydantic valida
automaticamente que o valor enviado é um dos permitidos.
"""
from datetime import datetime
from pydantic import BaseModel
from app.models.ordem_servico import StatusOS


class VeiculoResumo(BaseModel):
    id: int
    placa: str
    marca: str
    modelo: str
    ano: int

    model_config = {"from_attributes": True}


class ClienteResumo(BaseModel):
    id: int
    nome: str
    telefone: str | None

    model_config = {"from_attributes": True}


class OSCreate(BaseModel):
    veiculo_id: int
    descricao_problema: str
    km_entrada: int
    data_previsao: datetime | None = None


class OSUpdate(BaseModel):
    diagnostico: str | None = None
    valor_mao_obra: float | None = None
    data_previsao: datetime | None = None


class OSAtualizarStatus(BaseModel):
    """Schema dedicado só para mudança de status — deixa a intenção explícita."""
    status: StatusOS
    data_conclusao: datetime | None = None


class OSOut(BaseModel):
    id: int
    status: StatusOS
    descricao_problema: str
    diagnostico: str | None
    km_entrada: int
    valor_mao_obra: float
    data_previsao: datetime | None
    data_conclusao: datetime | None
    created_at: datetime
    updated_at: datetime
    veiculo: VeiculoResumo
    cliente: ClienteResumo

    model_config = {"from_attributes": True}
