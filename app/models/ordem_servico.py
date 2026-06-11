"""
Model para Ordens de Serviço.

Novidade: Enum de status com transições controladas.
Python tem enum nativo — aqui usamos com SQLAlchemy para guardar
o valor como string no banco (mais legível que inteiros).

Relações:
  Veiculo 1:N OrdemServico
  Cliente 1:N OrdemServico (denormalizado para facilitar queries)
"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, ForeignKey, DateTime, Enum as SAEnum, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class StatusOS(str, enum.Enum):
    """
    'str' como base permite comparar com strings diretamente.
    Ex: ordem.status == "aberta"  →  True
    """
    ABERTA = "aberta"
    EM_ANDAMENTO = "em_andamento"
    AGUARDANDO_PECAS = "aguardando_pecas"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


# Mapa de transições válidas — regra de negócio centralizada
TRANSICOES_VALIDAS: dict[StatusOS, list[StatusOS]] = {
    StatusOS.ABERTA:           [StatusOS.EM_ANDAMENTO, StatusOS.CANCELADA],
    StatusOS.EM_ANDAMENTO:     [StatusOS.AGUARDANDO_PECAS, StatusOS.CONCLUIDA, StatusOS.CANCELADA],
    StatusOS.AGUARDANDO_PECAS: [StatusOS.EM_ANDAMENTO, StatusOS.CANCELADA],
    StatusOS.CONCLUIDA:        [],
    StatusOS.CANCELADA:        [],
}


class OrdemServico(Base):
    __tablename__ = "ordens_servico"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    veiculo_id: Mapped[int] = mapped_column(ForeignKey("veiculos.id", ondelete="RESTRICT"), nullable=False, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id", ondelete="RESTRICT"), nullable=False, index=True)

    status: Mapped[StatusOS] = mapped_column(SAEnum(StatusOS), default=StatusOS.ABERTA, nullable=False)

    descricao_problema: Mapped[str] = mapped_column(Text, nullable=False)
    diagnostico: Mapped[str | None] = mapped_column(Text)

    km_entrada: Mapped[int] = mapped_column(Integer, nullable=False)
    valor_mao_obra: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    data_previsao: Mapped[datetime | None] = mapped_column(DateTime)
    data_conclusao: Mapped[datetime | None] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    veiculo: Mapped["Veiculo"] = relationship("Veiculo", back_populates="ordens")
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="ordens")


from app.models.veiculo import Veiculo  # noqa: E402
from app.models.cliente import Cliente  # noqa: E402
