import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine


class PostgresDb:
    def __init__(self) -> None:
        self.url: str = self._get_db_url()

        # echo=True will print all SQL queries
        self.engine: Engine = create_async_engine(
            self.url, pool_pre_ping=True, echo=False, pool_use_lifo=True)

        self.SessionLocal: sessionmaker[AsyncSession] = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )

        self.Base = declarative_base()

    def _get_db_url(self):
        host: str = os.getenv("POSTGRES_HOST", "localhost")
        port: int = int(os.getenv("POSTGRES_PORT", 5432))
        user: str = os.getenv("POSTGRES_USER", "postgres")
        password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
        database: str = os.getenv("POSTGRES_DB", "flats")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

    async def init_db(self) -> None:
        """Initialize the database schema asynchronously."""
        async with self.engine.begin() as conn:
            # Create all tables defined in self.Base metadata
            await conn.run_sync(self.Base.metadata.create_all)


# Create a singleton instance of PostgresDb
postgres_instance = PostgresDb()
