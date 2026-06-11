"""
Schemas Pydantic para validação e serialização de Clientes.

Node.js equivalente: express-validator + response shaping manual.
Aqui o Pydantic faz as duas coisas: valida a entrada e serializa a saída.

Três schemas por recurso é o padrão:
  - ClienteCreate  → body do POST (sem id/timestamps)
  - ClienteUpdate  → body do PUT/PATCH (todos opcionais)
  - ClienteOut     → o que a API retorna (inclui id/timestamps)
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
import re


class ClienteCreate(BaseModel):
    nome: str
    cpf: str
    telefone: str | None = None
    email: EmailStr | None = None
    endereco: str | None = None

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        """Remove formatação e valida que tem 11 dígitos."""
        digits = re.sub(r"\D", "", v)
        if len(digits) != 11:
            raise ValueError("CPF deve ter 11 dígitos")
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome deve ter ao menos 2 caracteres")
        return v


class ClienteUpdate(BaseModel):
    """Todos os campos opcionais — equivale ao PATCH."""
    nome: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    endereco: str | None = None


class ClienteOut(BaseModel):
    """Schema de resposta. 'from_attributes=True' permite ler de objetos SQLAlchemy."""
    id: int
    nome: str
    cpf: str
    telefone: str | None
    email: str | None
    endereco: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
