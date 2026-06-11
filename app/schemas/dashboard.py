"""
Schemas de resposta para o Dashboard.

Apenas saída — nenhum destes schemas recebe dados do cliente.
"""
from pydantic import BaseModel


class KPIs(BaseModel):
    os_abertas: int
    os_em_andamento: int
    os_concluidas_mes: int
    faturamento_mes: float
    faturamento_total: float
    ticket_medio: float
    pecas_estoque_critico: int


class FaturamentoMensal(BaseModel):
    ano: int
    mes: int
    total_os: int
    faturamento: float


class OSPorStatus(BaseModel):
    status: str
    total: int


class TopCliente(BaseModel):
    cliente_id: int
    nome: str
    total_os: int
    gasto_total: float


class PecaMaisUsada(BaseModel):
    peca_id: int
    codigo: str
    nome: str
    total_usado: int
    receita_gerada: float


class EstoqueCritico(BaseModel):
    peca_id: int
    codigo: str
    nome: str
    estoque_atual: int
    estoque_minimo: int
    diferenca: int
