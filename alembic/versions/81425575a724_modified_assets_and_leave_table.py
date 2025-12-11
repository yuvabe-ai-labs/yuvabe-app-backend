"""modified assets and leave table

Revision ID: 711b27b4aefb
Revises: c5bdab52a98c
Create Date: 2025-12-11 09:57:04.269110
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "81425575a724"
down_revision: Union[str, Sequence[str], None] = "c5bdab52a98c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # 1️⃣ Add asset_id as NULLABLE first (to avoid NOT NULL error)
    op.add_column("assets", sa.Column("asset_id", sa.String(), nullable=True))

    # 2️⃣ Populate asset_id for existing rows (if any)
    op.execute("UPDATE assets SET asset_id = 'TEMP-' || id::text")

    # 3️⃣ Make asset_id NOT NULL
    op.alter_column("assets", "asset_id", nullable=False)

    # 4️⃣ Add unique constraint
    op.create_unique_constraint("unique_assetid_type", "assets", ["asset_id", "type"])

    # 5️⃣ Drop old 'name' column safely
    op.drop_column("assets", "name")

    # 6️⃣ Leave the `id` column alone — DO NOT convert VARCHAR → UUID
    # (This fixes the UUID casting error)

    # 7️⃣ Convert leave timestamps
    op.alter_column(
        "leave",
        "requested_at",
        existing_type=sa.DATE(),
        type_=sa.DateTime(),
        existing_nullable=False,
    )

    op.alter_column(
        "leave",
        "updated_at",
        existing_type=sa.DATE(),
        type_=sa.DateTime(),
        existing_nullable=False,
    )


def downgrade() -> None:

    # Reverse leave changes
    op.alter_column(
        "leave",
        "updated_at",
        existing_type=sa.DateTime(),
        type_=sa.DATE(),
        existing_nullable=False,
    )

    op.alter_column(
        "leave",
        "requested_at",
        existing_type=sa.DateTime(),
        type_=sa.DATE(),
        existing_nullable=False,
    )

    # Restore name field
    op.add_column("assets", sa.Column("name", sa.String(), nullable=False))

    # Drop unique constraint
    op.drop_constraint("unique_assetid_type", "assets", type_="unique")

    # Remove asset_id
    op.drop_column("assets", "asset_id")
