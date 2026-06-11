"""
Rotas de Ordens de Serviço.

Novidade: endpoint dedicado para mudança de status com validação
de transições — regra de negócio aplicada na camada de rota.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ordem_servico import OrdemServico, StatusOS, TRANSICOES_VALIDAS
from app.models.veiculo import Veiculo
from app.schemas.ordem_servico import OSCreate, OSUpdate, OSAtualizarStatus, OSOut

router = APIRouter(prefix="/ordens", tags=["Ordens de Serviço"])


@router.post("/", response_model=OSOut, status_code=status.HTTP_201_CREATED)
def abrir_os(dados: OSCreate, db: Session = Depends(get_db)):
    veiculo = db.get(Veiculo, dados.veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    os = OrdemServico(
        **dados.model_dump(),
        cliente_id=veiculo.cliente_id,
        status=StatusOS.ABERTA,
    )
    db.add(os)
    db.commit()
    db.refresh(os)
    return os


@router.get("/", response_model=list[OSOut])
def listar_ordens(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filtro: StatusOS | None = Query(None, alias="status"),
    cliente_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(OrdemServico)
    if status_filtro:
        query = query.filter(OrdemServico.status == status_filtro)
    if cliente_id:
        query = query.filter(OrdemServico.cliente_id == cliente_id)
    return query.order_by(OrdemServico.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{os_id}", response_model=OSOut)
def buscar_os(os_id: int, db: Session = Depends(get_db)):
    os = db.get(OrdemServico, os_id)
    if not os:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    return os


@router.put("/{os_id}", response_model=OSOut)
def atualizar_os(os_id: int, dados: OSUpdate, db: Session = Depends(get_db)):
    os = db.get(OrdemServico, os_id)
    if not os:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    if os.status in (StatusOS.CONCLUIDA, StatusOS.CANCELADA):
        raise HTTPException(status_code=409, detail=f"OS {os.status.value} não pode ser editada")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(os, campo, valor)

    db.commit()
    db.refresh(os)
    return os


@router.patch("/{os_id}/status", response_model=OSOut)
def mudar_status(os_id: int, dados: OSAtualizarStatus, db: Session = Depends(get_db)):
    """
    PATCH /ordens/{id}/status

    Endpoint dedicado para transições de status.
    Valida se a transição é permitida antes de salvar.
    """
    os = db.get(OrdemServico, os_id)
    if not os:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")

    transicoes = TRANSICOES_VALIDAS[os.status]
    if dados.status not in transicoes:
        permitidas = [s.value for s in transicoes]
        raise HTTPException(
            status_code=409,
            detail=f"Não é possível ir de '{os.status.value}' para '{dados.status.value}'. "
                   f"Transições permitidas: {permitidas or 'nenhuma'}",
        )

    os.status = dados.status

    if dados.status == StatusOS.CONCLUIDA:
        os.data_conclusao = dados.data_conclusao or datetime.now(timezone.utc)

    if dados.status == StatusOS.CANCELADA:
        # Devolve todas as peças ao estoque ao cancelar
        for item in os.itens:
            item.peca.estoque_atual += item.quantidade

    db.commit()
    db.refresh(os)
    return os


@router.get("/veiculo/{veiculo_id}", response_model=list[OSOut])
def historico_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    """Todas as OSs de um veículo — base do histórico de manutenção."""
    veiculo = db.get(Veiculo, veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    return (
        db.query(OrdemServico)
        .filter(OrdemServico.veiculo_id == veiculo_id)
        .order_by(OrdemServico.created_at.desc())
        .all()
    )
