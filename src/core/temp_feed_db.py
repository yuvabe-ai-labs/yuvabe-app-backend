from datetime import date

from sqlmodel import Session

from src.core.database import engine
from src.core.models import Assets, EmotionLogs, Roles, Teams, Users, UserTeamsRole
from src.feed.models import Comments, Likes, Posts


def seed_users(session: Session):
    users = [
        Users(
            email_id="tilak@example.com",
            password="hashed_pass1",
            user_name="Tilak",
            dob=date(2001, 5, 21),
            address="Chennai",
            profile_picture="tilak.png",
        ),
        Users(
            email_id="arun@example.com",
            password="hashed_pass2",
            user_name="Arun",
            dob=date(2000, 8, 15),
            address="Bangalore",
            profile_picture="arun.png",
        ),
    ]
    session.add_all(users)
    session.commit()
    print("Users added.")
    return users


def seed_teams(session: Session):
    teams = [
        Teams(name="Development"),
        Teams(name="Marketing"),
        Teams(name="Design"),
    ]
    session.add_all(teams)
    session.commit()
    print("Teams added.")
    return teams


def seed_roles(session: Session):
    roles = [
        Roles(name="Admin"),
        Roles(name="Member"),
        Roles(name="Lead"),
    ]
    session.add_all(roles)
    session.commit()
    print("Roles added.")
    return roles


def seed_user_teams_roles(session: Session, users, teams, roles):
    mappings = [
        UserTeamsRole(user_id=users[0].id, team_id=teams[0].id, role_id=roles[0].id),
        UserTeamsRole(user_id=users[1].id, team_id=teams[1].id, role_id=roles[1].id),
    ]
    session.add_all(mappings)
    session.commit()
    print("User-Team-Role mappings added.")


def seed_assets(session: Session, users):
    assets = [
        Assets(user_id=users[0].id, name="MacBook Pro", type="Laptop"),
        Assets(user_id=users[1].id, name="Dell Monitor", type="Monitor"),
    ]
    session.add_all(assets)
    session.commit()
    print("Assets added.")
    return assets


def seed_emotion_logs(session: Session, users):
    logs = [
        EmotionLogs(user_id=users[0].id, morning_emotion=8, evening_emotion=6),
        EmotionLogs(user_id=users[1].id, morning_emotion=7, evening_emotion=8),
    ]
    session.add_all(logs)
    session.commit()
    print("Emotion logs added.")


def seed_posts(session: Session, users):
    posts = [
        Posts(
            user_id=users[0].id,
            caption="New sprint kickoff!",
            image="sprint.png",
        ),
        Posts(
            user_id=users[1].id,
            caption="Design updates rolling out soon!",
            image="design.png",
        ),
    ]
    session.add_all(posts)
    session.commit()
    print("Posts added.")
    return posts


def seed_likes(session: Session, users, posts):
    likes = [
        Likes(user_id=users[0].id, post_id=posts[1].id),
        Likes(user_id=users[1].id, post_id=posts[0].id),
    ]
    session.add_all(likes)
    session.commit()
    print("Likes added.")


def seed_comments(session: Session, users, posts):
    comments = [
        Comments(user_id=users[0].id, post_id=posts[1].id, comment="Looks great!"),
        Comments(user_id=users[1].id, post_id=posts[0].id, comment="Can’t wait!"),
    ]
    session.add_all(comments)
    session.commit()
    print("Comments added.")


def run_all_seeds():
    with Session(engine) as session:
        users = seed_users(session)
        teams = seed_teams(session)
        roles = seed_roles(session)
        seed_user_teams_roles(session, users, teams, roles)
        seed_assets(session, users)
        seed_emotion_logs(session, users)
        posts = seed_posts(session, users)
        seed_likes(session, users, posts)
        seed_comments(session, users, posts)
        print("All data seeded successfully!")


if __name__ == "__main__":
    run_all_seeds()
