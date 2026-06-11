from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models.user import User, Role
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    password: str
    role: Role = Role.MECANICO


class UserOut(BaseModel):
    id: int
    nome: str
    email: str
    role: Role
    ativo: bool

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(dados: UserCreate, db: Session = Depends(get_db)):
    """Cria usuário. Em produção, proteja com require_admin."""
    if db.query(User).filter(User.email == dados.email).first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    user = User(
        nome=dados.nome,
        email=dados.email,
        hashed_password=hash_password(dados.password),
        role=dados.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    OAuth2 password flow — o Swagger já gera o formulário de login automaticamente.
    'username' do form é o e-mail (padrão OAuth2).
    """
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    if not user.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    token = create_access_token({"sub": str(user.id)})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
