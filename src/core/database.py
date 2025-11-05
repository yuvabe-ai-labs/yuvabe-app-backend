import os

from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine

from src.core import models as core_models
from src.feed import models as feed_models

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"), echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    print("Table creating")
    init_db()
    print("Table Created successfully!")
