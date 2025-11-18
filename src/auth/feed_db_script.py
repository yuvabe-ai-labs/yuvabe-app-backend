from src.auth.utils import hash_password
from datetime import date
from sqlmodel import Session

from src.core.database import engine
from src.core.models import Users, Teams, Roles, UserTeamsRole


# ------------------------
# 1. Seed Users
# ------------------------
def seed_users(session: Session):
    users = [
        Users(
            email_id="ragul@yuvabe.com",
            password=hash_password("Yuvabe"),
            user_name="ragul",
            dob=date(2001, 5, 21),
            address="Chennai",
            profile_picture="ragul.png",
        ),
        Users(
            email_id="shri@yuvabe.com",
            password=hash_password("Yuvabe"),
            user_name="Shri",
            dob=date(1999, 3, 14),
            address="Chennai",
            profile_picture="shri.png",
        ),
        Users(
            email_id="hryuva@yuvabe.com",
            password=hash_password("Yuvabe"),
            user_name="Sathish",
            dob=date(1998, 7, 10),
            address="Chennai",
            profile_picture="Sathish.png",
        ),
        Users(
            email_id="hr2@yuvabe.com",
            password=hash_password("Yuvabe"),
            user_name="Deepika",
            dob=date(1997, 2, 5),
            address="Chennai",
            profile_picture="deepika.png",
        ),
    ]

    session.add_all(users)
    session.commit()
    print("Users added.")
    return users


# ------------------------
# 2. Seed Teams
# ------------------------
def seed_teams(session: Session):
    teams = [
        Teams(name="Tech Team"),
        Teams(name="HR Team"),
    ]
    session.add_all(teams)
    session.commit()
    print("Teams added.")
    return teams


# ------------------------
# 3. Seed Roles
# ------------------------
def seed_roles(session: Session):
    roles = [
        Roles(name="Developer"),
        Roles(name="Team Lead"),
        Roles(name="HR Manager"),
    ]
    session.add_all(roles)
    session.commit()
    print("Roles added.")
    return roles


# ------------------------
# 4. Map Users → Teams → Roles
# ------------------------
def seed_user_teams_roles(session: Session, users, teams, roles):
    mappings = [
        # Hari → Tech Team → Developer
        UserTeamsRole(
            user_id=users[0].id,  # Hari
            team_id=teams[0].id,  # Tech Team
            role_id=roles[0].id,  # Developer
        ),
        # Shri → Tech Team → Team Lead
        UserTeamsRole(
            user_id=users[1].id,  # Shri
            team_id=teams[0].id,  # Tech Team
            role_id=roles[1].id,  # Team Lead
        ),
        # HR Keerthana
        UserTeamsRole(
            user_id=users[2].id,  # Keerthana
            team_id=teams[1].id,  # HR Team
            role_id=roles[2].id,  # HR Manager
        ),
        # HR Deepika
        UserTeamsRole(
            user_id=users[3].id,  # Deepika
            team_id=teams[1].id,  # HR Team
            role_id=roles[2].id,  # HR Manager
        ),
    ]

    session.add_all(mappings)
    session.commit()
    print("User-Team-Role mappings added.")


# ------------------------
# 5. Master Runner
# ------------------------
def run_all_seeds():
    with Session(engine) as session:
        users = seed_users(session)
        teams = seed_teams(session)
        roles = seed_roles(session)
        seed_user_teams_roles(session, users, teams, roles)
        print("All data seeded successfully!")


if __name__ == "__main__":
    run_all_seeds()
