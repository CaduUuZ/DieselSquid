"""
Conexão com o banco de dados.

Node.js equivalente:
  const { Pool } = require('pg')
  const pool = new Pool({ connectionString: process.env.DATABASE_URL })

Aqui o SQLAlchemy gerencia um pool de conexões automaticamente.
A 'SessionLocal' é o que você usaria para fazer queries — equivale ao pool.query().
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


# create_engine = new Pool() do node-postgres, mas com ORM por baixo
# psycopg3 usa o prefixo "postgresql+psycopg" na connection string
_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
engine = create_engine(_url)

# Cada requisição abre uma Session e fecha no finally — igual ao padrão try/finally do Express
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe base que todos os models herdam. Equivale ao Model do Sequelize/Prisma."""
    pass


def get_db():
    """
    Dependency injection do FastAPI — equivale ao middleware de conexão no Express.
    O 'yield' garante que a session sempre fecha, mesmo se der erro.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
