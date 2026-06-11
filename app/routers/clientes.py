"""
Rotas de Clientes.

Node.js equivalente:
  const router = express.Router()
  router.get('/', async (req, res) => { ... })
  router.post('/', async (req, res) => { ... })

FastAPI usa decorators diretamente na função — mais limpo, sem req/res explícito.
O 'db: Session = Depends(get_db)' é injeção de dependência automática do FastAPI.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteOut

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("/", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def criar_cliente(dados: ClienteCreate, db: Session = Depends(get_db)):
    """
    POST /clientes
    'dados' já vem validado pelo Pydantic — equivale ao body do req.body após express-validator.
    """
    cliente = Cliente(**dados.model_dump())
    db.add(cliente)
    try:
        db.commit()
        db.refresh(cliente)  # recarrega do banco para pegar id e timestamps
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF ou e-mail já cadastrado"
        )
    return cliente


@router.get("/", response_model=list[ClienteOut])
def listar_clientes(
    skip: int = Query(0, ge=0, description="Registros para pular (paginação)"),
    limit: int = Query(20, ge=1, le=100, description="Máximo de registros"),
    busca: str | None = Query(None, description="Filtrar por nome ou CPF"),
    db: Session = Depends(get_db),
):
    """GET /clientes?skip=0&limit=20&busca=joao"""
    query = db.query(Cliente)
    if busca:
        termo = f"%{busca}%"
        query = query.filter(
            Cliente.nome.ilike(termo) | Cliente.cpf.ilike(termo)
        )
    return query.order_by(Cliente.nome).offset(skip).limit(limit).all()


@router.get("/{cliente_id}", response_model=ClienteOut)
def buscar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """GET /clientes/:id"""
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.put("/{cliente_id}", response_model=ClienteOut)
def atualizar_cliente(
    cliente_id: int,
    dados: ClienteUpdate,
    db: Session = Depends(get_db),
):
    """PUT /clientes/:id — atualiza apenas os campos enviados."""
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # model_dump(exclude_unset=True) = só os campos que vieram no body (PATCH behavior)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)

    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """DELETE /clientes/:id"""
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(cliente)
    db.commit()
