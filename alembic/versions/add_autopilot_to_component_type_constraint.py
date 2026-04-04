"""Add AUTOPILOT to component type constraint

Revision ID: 4e679dfb11f5
Revises: e8fd0ae2ee85  # Changed to point to the existing migration
Create Date: 2026-04-04 11:04:42.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '4e679dfb11f5'
down_revision: Union[str, Sequence[str], None] = 'e8fd0ae2ee85'  # Updated to reference the existing migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update the check constraint to include AUTOPILOT value
    # First drop the existing constraint
    op.execute("ALTER TABLE components DROP CONSTRAINT IF EXISTS check_component_type")
    
    # Then create the new constraint with AUTOPILOT included
    op.execute("ALTER TABLE components ADD CONSTRAINT check_component_type CHECK (type IN ('DVS', 'KPP', 'RK', 'HR', 'BK', 'AUTOPILOT'))")


def downgrade() -> None:
    # Revert to the previous constraint without AUTOPILOT
    # Drop the current constraint
    op.execute("ALTER TABLE components DROP CONSTRAINT IF EXISTS check_component_type")
    
    # Recreate the old constraint without AUTOPILOT
    op.execute("ALTER TABLE components ADD CONSTRAINT check_component_type CHECK (type IN ('DVS', 'KPP', 'RK', 'HR', 'BK'))")