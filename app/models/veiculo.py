"""
Model SQLAlchemy para a tabela 'veiculos'.

Relação: Um Cliente tem muitos Veículos (1:N).
  - 'cliente_id' é a FK — equivale ao @relation do Prisma
  - 'relationship()' permite acessar cliente.veiculos e veiculo.cliente
"""
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Veiculo(Base):
    __tablename__ = "veiculos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True)

    placa: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    marca: Mapped[str] = mapped_column(String(60), nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    cor: Mapped[str | None] = mapped_column(String(40))
    km_atual: Mapped[int] = mapped_column(Integer, default=0)
    observacoes: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Lado N da relação: acessa o cliente dono deste veículo
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="veiculos")

    # Lado 1 da relação com ordens de serviço
    ordens: Mapped[list["OrdemServico"]] = relationship("OrdemServico", back_populates="veiculo")


# Importado aqui para evitar circular import — o Python resolve na ordem de execução
from app.models.cliente import Cliente  # noqa: E402
