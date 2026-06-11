from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Importa todos os models para que o Alembic detecte as tabelas
# Equivale ao prisma migrate — ele compara o schema atual com o banco
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.database import Base
import app.models  # noqa: F401 — garante que todos os models são registrados

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Aponta para os metadados dos nossos models — necessário para autogenerate
target_metadata = Base.metadata

# Sobrescreve a URL do alembic.ini com a do .env
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
