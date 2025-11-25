"""add is_read to leave table

Revision ID: d9bb355538fd
Revises: e95f62f91348
Create Date: 2025-11-25 16:43:45.584602

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'd9bb355538fd'
down_revision: Union[str, Sequence[str], None] = 'e95f62f91348'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "leave",
        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )

def downgrade():
    op.drop_column("leave", "is_read")
