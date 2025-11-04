from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv
from . import models
import os

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'),echo=True)

SQLModel.metadata.create_all(engine)