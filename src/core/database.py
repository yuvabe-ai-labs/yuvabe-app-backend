from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core import *
from src.core.config import settings

load_dotenv()

engine = create_engine(
    settings.DATABASE_URL, echo=True
)  # to false on prod just to chcek for now

async_engine = create_async_engine(
    url=settings.ASYNC_DATABASE_URL, future=True, connect_args={"ssl": True}
)

async_session = async_sessionmaker(
    class_=AsyncSession, bind=async_engine, expire_on_commit=False
)


def init_db():
    SQLModel.metadata.create_all(engine)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


if __name__ == "__main__":
    print("Table creating")
    init_db()
    print("Table Created successfully!")
