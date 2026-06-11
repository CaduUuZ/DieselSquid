"""
Model SQLAlchemy para a tabela 'clientes'.

Node.js equivalente (Prisma schema):
  model Cliente {
    id        Int      @id @default(autoincrement())
    nome      String
    cpf       String   @unique
    telefone  String?
    email     String?  @unique
    endereco  String?
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
    veiculos  Veiculo[]
  }

Mapped[] é o equivalente ao tipo das colunas com type hints Python.
"""
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    telefone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(150), unique=True, index=True)
    endereco: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Lado 1 da relação: lista de veículos deste cliente
    veiculos: Mapped[list["Veiculo"]] = relationship("Veiculo", back_populates="cliente", cascade="all, delete-orphan")

    # Lado 1 da relação com ordens de serviço
    ordens: Mapped[list["OrdemServico"]] = relationship("OrdemServico", back_populates="cliente")
