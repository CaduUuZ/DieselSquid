"""
Rotas de Peças (catálogo + estoque) e Itens de OS.

Regras de negócio de estoque:
  - Adicionar peça à OS → debita do estoque
  - Remover peça da OS → devolve ao estoque
  - Cancelar OS (no router de ordens) → devolve tudo ao estoque
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.peca import Peca, ItemOS
from app.models.ordem_servico import OrdemServico, StatusOS
from app.schemas.peca import PecaCreate, PecaUpdate, PecaOut, AjusteEstoque, ItemOSCreate, ItemOSOut

router = APIRouter(tags=["Peças"])


# ── Catálogo de Peças ──────────────────────────────────────────────────────────

@router.post("/pecas", response_model=PecaOut, status_code=status.HTTP_201_CREATED)
def criar_peca(dados: PecaCreate, db: Session = Depends(get_db)):
    peca = Peca(**dados.model_dump())
    db.add(peca)
    try:
        db.commit()
        db.refresh(peca)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Código de peça já cadastrado")
    return peca


@router.get("/pecas", response_model=list[PecaOut])
def listar_pecas(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    busca: str | None = Query(None, description="Filtrar por código, nome ou marca"),
    estoque_baixo: bool | None = Query(None, description="Filtrar apenas peças com estoque baixo"),
    db: Session = Depends(get_db),
):
    query = db.query(Peca)
    if busca:
        termo = f"%{busca}%"
        query = query.filter(
            Peca.codigo.ilike(termo) | Peca.nome.ilike(termo) | Peca.marca.ilike(termo)
        )
    if estoque_baixo:
        # Filtra peças onde estoque_atual <= estoque_minimo
        from sqlalchemy import column
        query = query.filter(Peca.estoque_atual <= Peca.estoque_minimo)
    return query.order_by(Peca.nome).offset(skip).limit(limit).all()


@router.get("/pecas/{peca_id}", response_model=PecaOut)
def buscar_peca(peca_id: int, db: Session = Depends(get_db)):
    peca = db.get(Peca, peca_id)
    if not peca:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    return peca


@router.put("/pecas/{peca_id}", response_model=PecaOut)
def atualizar_peca(peca_id: int, dados: PecaUpdate, db: Session = Depends(get_db)):
    peca = db.get(Peca, peca_id)
    if not peca:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(peca, campo, valor)
    db.commit()
    db.refresh(peca)
    return peca


@router.patch("/pecas/{peca_id}/estoque", response_model=PecaOut)
def ajustar_estoque(peca_id: int, dados: AjusteEstoque, db: Session = Depends(get_db)):
    """
    Entrada (+) ou saída (-) manual de estoque.
    Quantidade positiva = entrada (compra), negativa = saída (perda/ajuste).
    """
    peca = db.get(Peca, peca_id)
    if not peca:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    novo_estoque = peca.estoque_atual + dados.quantidade
    if novo_estoque < 0:
        raise HTTPException(
            status_code=409,
            detail=f"Estoque insuficiente. Atual: {peca.estoque_atual}, solicitado: {abs(dados.quantidade)}"
        )
    peca.estoque_atual = novo_estoque
    db.commit()
    db.refresh(peca)
    return peca


# ── Itens de OS (peças usadas em uma ordem) ───────────────────────────────────

@router.post("/ordens/{os_id}/itens", response_model=ItemOSOut, status_code=status.HTTP_201_CREATED)
def adicionar_item_os(os_id: int, dados: ItemOSCreate, db: Session = Depends(get_db)):
    """
    Adiciona uma peça à OS e debita do estoque automaticamente.
    Só é permitido em OS com status aberta, em_andamento ou aguardando_pecas.
    """
    os = db.get(OrdemServico, os_id)
    if not os:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    if os.status in (StatusOS.CONCLUIDA, StatusOS.CANCELADA):
        raise HTTPException(status_code=409, detail="Não é possível adicionar peças a uma OS finalizada")

    peca = db.get(Peca, dados.peca_id)
    if not peca:
        raise HTTPException(status_code=404, detail="Peça não encontrada")
    if peca.estoque_atual < dados.quantidade:
        raise HTTPException(
            status_code=409,
            detail=f"Estoque insuficiente. Disponível: {peca.estoque_atual}, solicitado: {dados.quantidade}"
        )

    # Snapshot do preço atual — histórico fica correto mesmo se o preço mudar
    item = ItemOS(os_id=os_id, peca_id=dados.peca_id, quantidade=dados.quantidade, preco_unitario=peca.preco_venda)
    peca.estoque_atual -= dados.quantidade

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/ordens/{os_id}/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_item_os(os_id: int, item_id: int, db: Session = Depends(get_db)):
    """Remove peça da OS e devolve ao estoque."""
    item = db.query(ItemOS).filter(ItemOS.id == item_id, ItemOS.os_id == os_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado nesta OS")

    os = db.get(OrdemServico, os_id)
    if os.status in (StatusOS.CONCLUIDA, StatusOS.CANCELADA):
        raise HTTPException(status_code=409, detail="Não é possível remover peças de uma OS finalizada")

    # Devolve ao estoque
    item.peca.estoque_atual += item.quantidade
    db.delete(item)
    db.commit()
