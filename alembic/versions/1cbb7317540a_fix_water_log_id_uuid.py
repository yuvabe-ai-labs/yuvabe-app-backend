from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision: str = '1cbb7317540a'
down_revision: Union[str, Sequence[str], None] = '9176b44b89ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old id column (this will remove the INTEGER id column)
    op.drop_column('water_logs', 'id')
    
    # Add the new UUID id column
    op.add_column('water_logs', sa.Column('id', sa.UUID(), nullable=False, primary_key=True, default=uuid.uuid4))
    
    # Optional: If you had any foreign key constraints or other indexes on the old id, you might need to add them back.

def downgrade() -> None:
    """Downgrade schema."""
    # Drop the UUID id column
    op.drop_column('water_logs', 'id')
    
    # Add the original INTEGER id column back
    op.add_column('water_logs', sa.Column('id', sa.Integer(), nullable=False, primary_key=True))
    
    # Optional: Restore any other changes you might have made during the downgrade
