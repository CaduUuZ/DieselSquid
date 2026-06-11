"""
Dashboard financeiro — queries de agregação.

Node.js equivalente: seria uma série de pool.query() com SQL puro ou
queries encadeadas. Aqui o SQLAlchemy monta o SQL com funções Python,
mas o resultado é idêntico.

Conceitos novos:
  - func.sum / func.count / func.avg  →  SUM(), COUNT(), AVG() no SQL
  - .label("alias")                   →  AS alias no SQL
  - func.date_trunc                   →  TRUNCATE de data para mês/ano
  - .scalar() / .all()                →  busca um valor único ou lista
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from fastapi import APIRouter, Depends

from app.database import get_db
from app.models.ordem_servico import OrdemServico, StatusOS
from app.models.peca import Peca, ItemOS
from app.models.cliente import Cliente
from app.schemas.dashboard import (
    KPIs, FaturamentoMensal, OSPorStatus, TopCliente, PecaMaisUsada, EstoqueCritico,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=KPIs)
def kpis(db: Session = Depends(get_db)):
    """
    Indicadores principais — equivale a rodar várias queries separadas
    e juntar o resultado num objeto.
    """
    agora = datetime.now(timezone.utc)

    os_abertas = db.query(func.count(OrdemServico.id)).filter(
        OrdemServico.status == StatusOS.ABERTA
    ).scalar() or 0

    os_em_andamento = db.query(func.count(OrdemServico.id)).filter(
        OrdemServico.status == StatusOS.EM_ANDAMENTO
    ).scalar() or 0

    # OS concluídas no mês atual
    os_concluidas_mes = db.query(func.count(OrdemServico.id)).filter(
        OrdemServico.status == StatusOS.CONCLUIDA,
        extract("month", OrdemServico.data_conclusao) == agora.month,
        extract("year", OrdemServico.data_conclusao) == agora.year,
    ).scalar() or 0

    # Faturamento = mão de obra + valor das peças das OS concluídas
    # Subquery que soma peças por OS
    pecas_por_os = (
        db.query(
            ItemOS.os_id,
            func.sum(ItemOS.quantidade * ItemOS.preco_unitario).label("total_pecas"),
        )
        .group_by(ItemOS.os_id)
        .subquery()
    )

    fat_mes_row = (
        db.query(
            func.sum(OrdemServico.valor_mao_obra + func.coalesce(pecas_por_os.c.total_pecas, 0))
        )
        .outerjoin(pecas_por_os, OrdemServico.id == pecas_por_os.c.os_id)
        .filter(
            OrdemServico.status == StatusOS.CONCLUIDA,
            extract("month", OrdemServico.data_conclusao) == agora.month,
            extract("year", OrdemServico.data_conclusao) == agora.year,
        )
        .scalar()
    )
    faturamento_mes = float(fat_mes_row or 0)

    fat_total_row = (
        db.query(
            func.sum(OrdemServico.valor_mao_obra + func.coalesce(pecas_por_os.c.total_pecas, 0))
        )
        .outerjoin(pecas_por_os, OrdemServico.id == pecas_por_os.c.os_id)
        .filter(OrdemServico.status == StatusOS.CONCLUIDA)
        .scalar()
    )
    faturamento_total = float(fat_total_row or 0)

    total_concluidas = db.query(func.count(OrdemServico.id)).filter(
        OrdemServico.status == StatusOS.CONCLUIDA
    ).scalar() or 0
    ticket_medio = faturamento_total / total_concluidas if total_concluidas > 0 else 0

    estoque_critico = db.query(func.count(Peca.id)).filter(
        Peca.estoque_atual <= Peca.estoque_minimo
    ).scalar() or 0

    return KPIs(
        os_abertas=os_abertas,
        os_em_andamento=os_em_andamento,
        os_concluidas_mes=os_concluidas_mes,
        faturamento_mes=round(faturamento_mes, 2),
        faturamento_total=round(faturamento_total, 2),
        ticket_medio=round(ticket_medio, 2),
        pecas_estoque_critico=estoque_critico,
    )


@router.get("/faturamento-mensal", response_model=list[FaturamentoMensal])
def faturamento_mensal(meses: int = 12, db: Session = Depends(get_db)):
    """
    Faturamento agrupado por mês — últimos N meses.

    GROUP BY com extract() — o SQLAlchemy monta:
      SELECT EXTRACT(year ...), EXTRACT(month ...), COUNT(*), SUM(...)
      FROM ordens_servico
      WHERE status = 'concluida'
      GROUP BY ano, mes
      ORDER BY ano, mes
    """
    pecas_por_os = (
        db.query(
            ItemOS.os_id,
            func.sum(ItemOS.quantidade * ItemOS.preco_unitario).label("total_pecas"),
        )
        .group_by(ItemOS.os_id)
        .subquery()
    )

    rows = (
        db.query(
            extract("year", OrdemServico.data_conclusao).label("ano"),
            extract("month", OrdemServico.data_conclusao).label("mes"),
            func.count(OrdemServico.id).label("total_os"),
            func.sum(
                OrdemServico.valor_mao_obra + func.coalesce(pecas_por_os.c.total_pecas, 0)
            ).label("faturamento"),
        )
        .outerjoin(pecas_por_os, OrdemServico.id == pecas_por_os.c.os_id)
        .filter(OrdemServico.status == StatusOS.CONCLUIDA)
        .group_by("ano", "mes")
        .order_by("ano", "mes")
        .limit(meses)
        .all()
    )

    return [
        FaturamentoMensal(
            ano=int(r.ano), mes=int(r.mes),
            total_os=r.total_os, faturamento=round(float(r.faturamento or 0), 2)
        )
        for r in rows
    ]


@router.get("/os-por-status", response_model=list[OSPorStatus])
def os_por_status(db: Session = Depends(get_db)):
    """Contagem de OS agrupada por status — para gráfico de pizza."""
    rows = (
        db.query(OrdemServico.status, func.count(OrdemServico.id).label("total"))
        .group_by(OrdemServico.status)
        .all()
    )
    return [OSPorStatus(status=r.status.value, total=r.total) for r in rows]


@router.get("/top-clientes", response_model=list[TopCliente])
def top_clientes(limit: int = 10, db: Session = Depends(get_db)):
    """
    Clientes com maior gasto total em OS concluídas.

    JOIN entre 3 tabelas: clientes → ordens_servico → itens_os.
    """
    pecas_por_os = (
        db.query(
            ItemOS.os_id,
            func.sum(ItemOS.quantidade * ItemOS.preco_unitario).label("total_pecas"),
        )
        .group_by(ItemOS.os_id)
        .subquery()
    )

    rows = (
        db.query(
            Cliente.id.label("cliente_id"),
            Cliente.nome,
            func.count(OrdemServico.id).label("total_os"),
            func.sum(
                OrdemServico.valor_mao_obra + func.coalesce(pecas_por_os.c.total_pecas, 0)
            ).label("gasto_total"),
        )
        .join(OrdemServico, OrdemServico.cliente_id == Cliente.id)
        .outerjoin(pecas_por_os, OrdemServico.id == pecas_por_os.c.os_id)
        .filter(OrdemServico.status == StatusOS.CONCLUIDA)
        .group_by(Cliente.id, Cliente.nome)
        .order_by(func.sum(
            OrdemServico.valor_mao_obra + func.coalesce(pecas_por_os.c.total_pecas, 0)
        ).desc())
        .limit(limit)
        .all()
    )

    return [
        TopCliente(
            cliente_id=r.cliente_id, nome=r.nome,
            total_os=r.total_os, gasto_total=round(float(r.gasto_total or 0), 2)
        )
        for r in rows
    ]


@router.get("/pecas-mais-usadas", response_model=list[PecaMaisUsada])
def pecas_mais_usadas(limit: int = 10, db: Session = Depends(get_db)):
    """Peças mais utilizadas em OS — para decisão de compra de estoque."""
    rows = (
        db.query(
            Peca.id.label("peca_id"),
            Peca.codigo,
            Peca.nome,
            func.sum(ItemOS.quantidade).label("total_usado"),
            func.sum(ItemOS.quantidade * ItemOS.preco_unitario).label("receita_gerada"),
        )
        .join(ItemOS, ItemOS.peca_id == Peca.id)
        .group_by(Peca.id, Peca.codigo, Peca.nome)
        .order_by(func.sum(ItemOS.quantidade).desc())
        .limit(limit)
        .all()
    )

    return [
        PecaMaisUsada(
            peca_id=r.peca_id, codigo=r.codigo, nome=r.nome,
            total_usado=r.total_usado,
            receita_gerada=round(float(r.receita_gerada or 0), 2)
        )
        for r in rows
    ]


@router.get("/estoque-critico", response_model=list[EstoqueCritico])
def estoque_critico(db: Session = Depends(get_db)):
    """Peças abaixo do estoque mínimo — para alerta de reposição."""
    rows = (
        db.query(Peca)
        .filter(Peca.estoque_atual <= Peca.estoque_minimo)
        .order_by((Peca.estoque_atual - Peca.estoque_minimo))
        .all()
    )

    return [
        EstoqueCritico(
            peca_id=p.id, codigo=p.codigo, nome=p.nome,
            estoque_atual=p.estoque_atual, estoque_minimo=p.estoque_minimo,
            diferenca=p.estoque_atual - p.estoque_minimo,
        )
        for p in rows
    ]
