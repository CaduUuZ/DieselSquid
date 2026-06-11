from datetime import datetime
from pydantic import BaseModel, field_validator
from app.models.peca import UnidadeMedida


class PecaCreate(BaseModel):
    codigo: str
    nome: str
    descricao: str | None = None
    marca: str | None = None
    unidade: UnidadeMedida = UnidadeMedida.UNIDADE
    preco_custo: float = 0
    preco_venda: float
    estoque_atual: int = 0
    estoque_minimo: int = 1

    @field_validator("preco_venda", "preco_custo")
    @classmethod
    def preco_positivo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Preço não pode ser negativo")
        return v

    @field_validator("estoque_atual", "estoque_minimo")
    @classmethod
    def estoque_positivo(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Estoque não pode ser negativo")
        return v


class PecaUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    marca: str | None = None
    preco_custo: float | None = None
    preco_venda: float | None = None
    estoque_minimo: int | None = None


class AjusteEstoque(BaseModel):
    """Entrada ou saída manual de estoque (compra, perda, inventário)."""
    quantidade: int
    motivo: str | None = None


class PecaOut(BaseModel):
    id: int
    codigo: str
    nome: str
    descricao: str | None
    marca: str | None
    unidade: UnidadeMedida
    preco_custo: float
    preco_venda: float
    estoque_atual: int
    estoque_minimo: int
    estoque_baixo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ItemOSCreate(BaseModel):
    peca_id: int
    quantidade: int

    @field_validator("quantidade")
    @classmethod
    def qtd_positiva(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v


class ItemOSOut(BaseModel):
    id: int
    peca_id: int
    quantidade: int
    preco_unitario: float
    subtotal: float
    peca: "PecaOut"

    model_config = {"from_attributes": True}
