import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, make_url, pool

from app.models import Base

config = context.config
if database_url := os.getenv("WORKBENCH_DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def secure_sqlite_path() -> Path | None:
    url = make_url(config.get_main_option("sqlalchemy.url"))
    if url.drivername != "sqlite" or url.database in {None, "", ":memory:"}:
        return None
    path = Path(url.database).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.parent.exists():
        path.parent.mkdir(parents=True, mode=0o700)
        path.parent.chmod(0o700)
    return path


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    sqlite_path = secure_sqlite_path()
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    if sqlite_path is not None and sqlite_path.exists():
        sqlite_path.chmod(0o600)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
