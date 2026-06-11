"""
Configurações da aplicação lidas do .env.

Node.js equivalente: process.env.DATABASE_URL com dotenv.
Pydantic BaseSettings já valida e tipifica as variáveis — se faltar alguma, erro na inicialização.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
