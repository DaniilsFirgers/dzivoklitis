import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import your Base and models
from scraper.database.postgres import postgres_instance
from scraper.database.models.flat import Flat
from scraper.database.models.price import Price
from scraper.database.models.favorite import Favourite
from scraper.database.models.user import User
from scraper.database.models.filter import Filter

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Read environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "default_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "default_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "default_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
# Default to 5432 if not set
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Construct the database URL
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
# Override sqlalchemy.url in config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = postgres_instance.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# Exclude PostGIS system tables from comparison
def include_object(object, name, type_, reflected, compare_to):
    if name in ['topology', 'spatial_ref_sys', 'layer']:
        return False
    return True


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
        include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()


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
        context.configure(
            connection=connection, target_metadata=target_metadata, include_object=include_object, version_table="alembic_version"
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
