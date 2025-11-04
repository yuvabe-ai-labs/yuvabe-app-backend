from sqlmodel import SQLModel, Field
from datetime import date
from sqlalchemy.dialects.postgresql import JSONB
import uuid

class Users(SQLModel, table=True):
    id: uuid.UUID | None = Field(default=None, primary_key=True)
    email_id : str = Field(unique=True)
    password : str 
    user_name : str
    dob : date 
    address : str
    role_id : uuid.UUID
    emotion_trend : dict = Field(sa_type=JSONB)
    habit_trend : dict = Field(sa_type=JSONB)
    profile_picture : str
    post_id : uuid.UUID

class Teams(SQLModel, table = True):
    id: uuid.UUID | None = Field(default=None, primary_key=True)
    name : str

class Roles(SQLModel, table = True):
    id : uuid.UUID | None = Field(default=None , primary_key=True)
    name : str