"""
Model para o catálogo de peças com controle de estoque.

Relação com OS: M:N com dados extras — não é uma relação pura,
pois a tabela intermediária (itens_os) tem colunas próprias
(quantidade, preco_unitario). Por isso usamos um model explícito
em vez do 'secondary' do SQLAlchemy.

Prisma equivalente:
  model Peca {
    id             Int      @id @default(autoincrement())
    codigo         String   @unique
    nome           String
    preco_venda    Decimal
    estoque_atual  Int
    itens          ItemOS[]
  }
"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, ForeignKey, DateTime, func, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UnidadeMedida(str, enum.Enum):
    UNIDADE = "un"
    LITRO = "litro"
    KG = "kg"
    METRO = "metro"
    PAR = "par"
    JOGO = "jogo"


class Peca(Base):
    __tablename__ = "pecas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    marca: Mapped[str | None] = mapped_column(String(80))
    unidade: Mapped[UnidadeMedida] = mapped_column(SAEnum(UnidadeMedida), default=UnidadeMedida.UNIDADE)

    preco_custo: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    preco_venda: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    estoque_atual: Mapped[int] = mapped_column(Integer, default=0)
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    itens: Mapped[list["ItemOS"]] = relationship("ItemOS", back_populates="peca")

    @property
    def estoque_baixo(self) -> bool:
        """True se o estoque está abaixo do mínimo — usado no dashboard."""
        return self.estoque_atual <= self.estoque_minimo


class ItemOS(Base):
    """
    Tabela junction entre OrdemServico e Peca com dados extras.

    'preco_unitario' é um snapshot — guarda o preço no momento do uso.
    Assim, se o preço da peça mudar depois, o histórico fica correto.
    Equivale ao padrão de 'price snapshot' em e-commerce.
    """
    __tablename__ = "itens_os"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    os_id: Mapped[int] = mapped_column(ForeignKey("ordens_servico.id", ondelete="CASCADE"), nullable=False, index=True)
    peca_id: Mapped[int] = mapped_column(ForeignKey("pecas.id", ondelete="RESTRICT"), nullable=False)

    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    preco_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    os: Mapped["OrdemServico"] = relationship("OrdemServico", back_populates="itens")
    peca: Mapped["Peca"] = relationship("Peca", back_populates="itens")

    @property
    def subtotal(self) -> float:
        return self.quantidade * float(self.preco_unitario)


from app.models.ordem_servico import OrdemServico  # noqa: E402
