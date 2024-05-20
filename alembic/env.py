import os
from logging.config import fileConfig

from alembic_utils.replaceable_entity import register_entities
from sqlalchemy import engine_from_config, pool

from alembic import context
from kyotsu.config import get_settings
from kyotsu.db import *
from kyotsu.db.base import Base
from kyotsu.db.triggers import onupdate_function, prefix_onupdate_trigger, event_code_onupdate_trigger, event_code_auto_increment, event_code_auto_increment_trigger

CI_MODE = context.get_x_argument(as_dictionary=True).get("ci_mode") == "true"

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

if CI_MODE:
    postgres_url = os.environ.get("POSTGRES_MIGRATION_URL")
else:
    postgres_url = str(get_settings().POSTGRES.CONN_STR).replace("postgresql", "postgresql+psycopg2")

if not postgres_url:
    msg = "'POSTGRES_MIGRATION_URL' is not configured." if CI_MODE else "Pydantic CONN_URL assemble error."
    raise OSError(msg)

config.set_main_option("sqlalchemy.url", postgres_url)

replaceable_entities = [
    onupdate_function,
    prefix_onupdate_trigger,
    event_code_onupdate_trigger,
    event_code_auto_increment,
    event_code_auto_increment_trigger,
]


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


if context.get_x_argument(as_dictionary=True).get("run_replaceable") == "true":
    register_entities(replaceable_entities)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
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
