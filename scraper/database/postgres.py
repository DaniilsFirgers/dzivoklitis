import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine


class PostgresDb:
    def __init__(self) -> None:
        self.host: str = os.getenv("POSTGRES_HOST", "localhost")
        self.port: int = int(os.getenv("POSTGRES_PORT", 5432))
        self.user: str = os.getenv("POSTGRES_USER", "postgres")
        self.password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.database: str = os.getenv("POSTGRES_DB", "flats")

        self.url: str = f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

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

    async def init_db(self) -> None:
        """Initialize the database schema asynchronously."""
        async with self.engine.begin() as conn:
            # Create all tables defined in self.Base metadata
            await conn.run_sync(self.Base.metadata.create_all)


# Create a singleton instance of PostgresDb
postgres_instance = PostgresDb()
