from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import clientes, veiculos, ordens_servico, pecas, dashboard, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DieselSquid — Sistema de Oficina",
    description="API de gerenciamento de garagem/oficina mecânica",
    version="2.0.0",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(clientes.router, prefix="/api")
app.include_router(veiculos.router, prefix="/api")
app.include_router(ordens_servico.router, prefix="/api")
app.include_router(pecas.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/")
def health_check():
    return {"status": "ok", "app": "DieselSquid", "version": "2.0.0"}
