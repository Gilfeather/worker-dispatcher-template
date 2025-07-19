import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .models import Base


class DatabaseConnection:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    def get_session(self) -> AsyncSession:
        return self.async_session()
    
    async def close(self):
        await self.engine.dispose()


def get_database_connection() -> DatabaseConnection:
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost/worker_dispatcher"
    )
    return DatabaseConnection(database_url)