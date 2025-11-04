from sqlmodel import Session
from datetime import date
import uuid

from src.core.database import engine 
from src.core.models import Users, Roles, Teams 


role = Roles(
    id=uuid.uuid4(),
    name="User"
)

team = Teams(
    id=uuid.uuid4(),
    name="Health Squad"
)

user = Users(
    id=uuid.uuid4(),
    email_id="test@example.com",
    password="hashed_password_here",
    user_name="tilak",
    dob=date(2000, 5, 20),
    address="Bangalore, India",
    role_id=role.id,
    emotion_trend={"happy": 10, "sad": 2},
    habit_trend={"exercise": 5, "sleep": 8},
    profile_picture="https://example.com/image.jpg",
    post_id=uuid.uuid4()
)


with Session(engine) as session:
    session.add(role)
    session.add(team)
    session.add(user)
    session.commit()

print("Sample data inserted successfully!")
