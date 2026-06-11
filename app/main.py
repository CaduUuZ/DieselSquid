"""
Ponto de entrada da aplicação.

Node.js equivalente:
  const app = express()
  app.use(express.json())
  app.use('/clientes', clientesRouter)
  app.listen(8000)

Aqui o uvicorn faz o papel do 'app.listen()' — chamado via CLI ou pelo run.py.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import clientes, veiculos, ordens_servico, pecas

# Cria as tabelas no banco se não existirem
# Em produção, substitua por migrations Alembic (como o 'prisma migrate deploy')
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DieselSquid — Sistema de Oficina",
    description="API de gerenciamento de garagem/oficina mecânica",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clientes.router, prefix="/api")
app.include_router(veiculos.router, prefix="/api")
app.include_router(ordens_servico.router, prefix="/api")
app.include_router(pecas.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "ok", "app": "DieselSquid"}
