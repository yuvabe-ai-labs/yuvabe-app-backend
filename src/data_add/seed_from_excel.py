import pandas as pd
import asyncio
import math
import json
from datetime import datetime, date
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from passlib.context import CryptContext

from src.core.database import async_session
from src.core.models import Users, Teams, Roles, UserTeamsRole, Assets, AssetStatus


# ---------------------------------------------
# PASSWORD HASHER
# ---------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# ---------------------------------------------
# CLEAN NaN / EMPTY VALUES
# ---------------------------------------------
def clean(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


# ---------------------------------------------
# NORMALIZE ASSET ID (NEW)
# ---------------------------------------------
def normalize_asset_id(value: str) -> str:
    """Convert messy input to clean format YB-73-M or YB-77-MS"""
    if not value:
        return None

    value = value.strip().replace(" ", "")
    value = value.upper()

    # Fix repeated hyphens
    while "--" in value:
        value = value.replace("--", "-")

    # If looks like YB73M (missing hyphens)
    if "-" not in value:
        prefix = value[:2]  # YB
        number = "".join(filter(str.isdigit, value))
        suffix = value[len(prefix) + len(number) :]
        return f"{prefix}-{number}-{suffix}"

    return value


# ---------------------------------------------
# ASSET TYPE MAP (fallback)
# ---------------------------------------------
ASSET_TYPE_MAP = {
    "M": "Monitor",
    "L": "Laptop",
    "H": "Headphone",
    "MS": "Mouse",
}


# ---------------------------------------------
# get_or_create
# ---------------------------------------------
async def get_or_create(session: AsyncSession, model, name: str):
    result = await session.exec(select(model).where(model.name == name))
    row = result.first()
    if row:
        return row

    row = model(name=name)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


# ---------------------------------------------
# PARSE ASSETS JSON
# ---------------------------------------------
def parse_assets_from_excel(raw_value):
    if raw_value is None:
        return []

    raw = str(raw_value).strip()
    raw = raw.replace('""', '"')

    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        return []
    except:
        return []


# ---------------------------------------------
# MAIN IMPORT
# ---------------------------------------------
async def seed_from_excel(session: AsyncSession, excel_path="src/data_add/users.xlsx"):
    df = pd.read_excel(excel_path)
    print("\n📌 Importing users from Excel...\n")

    for _, row in df.iterrows():

        # --- DOB ---
        raw_dob = clean(row["dob"])
        dob = None
        if isinstance(raw_dob, str):
            try:
                dob = datetime.strptime(raw_dob, "%d.%m.%Y").date()
            except:
                dob = None
        elif isinstance(raw_dob, datetime):
            dob = raw_dob.date()
        else:
            dob = raw_dob

        # --- CREATE USER (is_verified = True) ---
        user = Users(
            email_id=row["email"],
            password=hash_password(row["password"]),
            user_name=row["User_name"],
            dob=dob,
            address=clean(row["address"]),
            join_date=str(clean(row["join_date"])),
            is_verified=True,  # <--- Added here
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        # --- TEAM / ROLE ---
        team = await get_or_create(session, Teams, row["team"])
        role = await get_or_create(session, Roles, row["role"])

        mapping = UserTeamsRole(
            user_id=user.id,
            team_id=team.id,
            role_id=role.id,
        )
        session.add(mapping)

        # --- ASSETS JSON ---
        assets_list = parse_assets_from_excel(clean(row["assets"]))

        for asset in assets_list:
            asset_id = normalize_asset_id(asset.get("id"))
            asset_type = asset.get("type", "Unknown")

            if not asset_id:
                continue

            asset_obj = Assets(
                id=asset_id,  # cleaned ID like YB-73-M
                user_id=user.id,
                name=asset_type,  # Monitor
                type=asset_type,  # Monitor
                status=AssetStatus.ACTIVE,
            )

            session.add(asset_obj)

        await session.commit()

    print("\n🎉 Excel Import Completed Successfully!\n")


# ---------------------------------------------
# RUN SEEDS
# ---------------------------------------------
async def run_all_seeds():

    async with async_session() as session:

        print("\n🟦 Seeding TEAMS...")
        for t in [
            "AI/Tech",
            "Shared services",
            "Digital Marketing",
            "Bevolve",
            "Bridge",
            "HR",
        ]:
            await get_or_create(session, Teams, t)

        print("\n🟦 Seeding ROLES...")
        for r in ["Mentor", "Team Lead", "HR", "Member"]:
            await get_or_create(session, Roles, r)

        print("\n🟦 Importing USERS from Excel...")
        await seed_from_excel(session, "src/data_add/users.xlsx")

        print("\n✔ All seeding complete!\n")


if __name__ == "__main__":
    asyncio.run(run_all_seeds())
