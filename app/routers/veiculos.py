"""
Rotas de Veículos.

Novidade: rota aninhada GET /clientes/{id}/veiculos
para buscar os veículos de um cliente específico.
Isso é um padrão REST para relações — equivale ao include do Prisma.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.veiculo import Veiculo
from app.models.cliente import Cliente
from app.schemas.veiculo import VeiculoCreate, VeiculoUpdate, VeiculoOut

router = APIRouter(tags=["Veículos"])


@router.post("/veiculos", response_model=VeiculoOut, status_code=status.HTTP_201_CREATED)
def criar_veiculo(dados: VeiculoCreate, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, dados.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    veiculo = Veiculo(**dados.model_dump())
    db.add(veiculo)
    try:
        db.commit()
        db.refresh(veiculo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Placa já cadastrada")
    return veiculo


@router.get("/veiculos", response_model=list[VeiculoOut])
def listar_veiculos(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    busca: str | None = Query(None, description="Filtrar por placa, marca ou modelo"),
    db: Session = Depends(get_db),
):
    query = db.query(Veiculo)
    if busca:
        termo = f"%{busca}%"
        query = query.filter(
            Veiculo.placa.ilike(termo)
            | Veiculo.marca.ilike(termo)
            | Veiculo.modelo.ilike(termo)
        )
    return query.order_by(Veiculo.marca, Veiculo.modelo).offset(skip).limit(limit).all()


@router.get("/veiculos/{veiculo_id}", response_model=VeiculoOut)
def buscar_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    veiculo = db.get(Veiculo, veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    return veiculo


@router.get("/clientes/{cliente_id}/veiculos", response_model=list[VeiculoOut])
def veiculos_do_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Rota aninhada — todos os veículos de um cliente específico."""
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente.veiculos


@router.put("/veiculos/{veiculo_id}", response_model=VeiculoOut)
def atualizar_veiculo(veiculo_id: int, dados: VeiculoUpdate, db: Session = Depends(get_db)):
    veiculo = db.get(Veiculo, veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(veiculo, campo, valor)

    db.commit()
    db.refresh(veiculo)
    return veiculo


@router.delete("/veiculos/{veiculo_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    veiculo = db.get(Veiculo, veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    db.delete(veiculo)
    db.commit()
