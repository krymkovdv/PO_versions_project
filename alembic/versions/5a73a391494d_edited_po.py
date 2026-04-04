"""edited_po

Revision ID: 5a73a391494d
Revises: 4e679dfb11f5
Create Date: 2026-04-04 11:44:14.759654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a73a391494d'
down_revision: Union[str, Sequence[str], None] = '4e679dfb11f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # First, add the column as nullable
    op.add_column('softwares', sa.Column('name', sa.Text(), nullable=True))
    
    # Update existing rows with a default value (you can use a meaningful default)
    # For example, use the path column as the initial value for name, or use a placeholder
    op.execute("UPDATE softwares SET name = 'Unnamed Software' WHERE name IS NULL")
    
    # Now make the column non-nullable
    op.alter_column('softwares', 'name', nullable=False)
    
    # Handle other column changes
    op.alter_column('softwares', 'path',
               existing_type=sa.TEXT(),
               nullable=True)
    op.drop_index(op.f('idx_tractors_id'), table_name='tractors')
    op.drop_index(op.f('idx_tractors_last_activity'), table_name='tractors')
    op.drop_index(op.f('idx_tractors_vin'), table_name='tractors')


def downgrade() -> None:
    """Downgrade schema."""
    # Handle other column changes first
    op.create_index(op.f('idx_tractors_vin'), 'tractors', ['vin'], unique=False)
    op.create_index(op.f('idx_tractors_last_activity'), 'tractors', ['last_activity'], unique=False)
    op.create_index(op.f('idx_tractors_id'), 'tractors', ['id'], unique=False)
    op.alter_column('softwares', 'path',
               existing_type=sa.TEXT(),
               nullable=False)
    
    # Remove the name column
    op.drop_column('softwares', 'name')