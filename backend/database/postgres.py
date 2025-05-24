import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared_models.base import Base
from shared_models import User, Price, Favourite, Flat, Filter


def _get_db_url():
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", 5432))
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    database: str = os.getenv("POSTGRES_DB", "flats")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


engine = create_engine(_get_db_url(), pool_pre_ping=True, echo=False, pool_use_lifo=True,
                       pool_size=10, max_overflow=20)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to create all tables from Base's metadata


def init_db():
    """Creates all tables based on Base metadata (models)"""
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
