"""Fix duplicate check constraint names and add is_closed column

Revision ID: c93d55a5b266
Revises: 
Create Date: 2026-03-24 11:07:53.217561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = 'c93d55a5b266'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add is_closed (if not exists) + fix constraint names"""
    
    # ========================================================================
    # 1. Добавляем колонку is_closed ТОЛЬКО если её нет
    # ========================================================================
    # Используем raw SQL с IF NOT EXISTS для безопасности
    op.execute("""
        ALTER TABLE support_message 
        ADD COLUMN IF NOT EXISTS is_closed BOOLEAN DEFAULT false NOT NULL
    """)
    
    # ========================================================================
    # 2. Переименовываем CheckConstraint: users
    # ========================================================================
    op.execute("""
        ALTER TABLE users 
        DROP CONSTRAINT IF EXISTS check_valid_role
    """)
    op.execute("""
        ALTER TABLE users 
        ADD CONSTRAINT check_user_role 
        CHECK (role IN ('engineer', 'dealer', 'moderator'))
    """)
    
    # ========================================================================
    # 3. Переименовываем CheckConstraint: components
    # ========================================================================
    op.execute("""
        ALTER TABLE components 
        DROP CONSTRAINT IF EXISTS check_valid_role
    """)
    op.execute("""
        ALTER TABLE components 
        ADD CONSTRAINT check_component_type 
        CHECK (type IN ('DVS', 'KPP', 'RK', 'HR', 'BK'))
    """)
    
    # ========================================================================
    # 4. Переименовываем CheckConstraint: softwares
    # ========================================================================
    op.execute("""
        ALTER TABLE softwares 
        DROP CONSTRAINT IF EXISTS check_valid_role
    """)
    op.execute("""
        ALTER TABLE softwares 
        ADD CONSTRAINT check_software_status 
        CHECK (status IN ('serial', 'in operation', 'experienced'))
    """)


def downgrade() -> None:
    """Downgrade schema: revert constraints + keep is_closed (safe)"""
    
    # ========================================================================
    # 1. Возвращаем старые имена CheckConstraint
    # ========================================================================
    # users
    op.execute("""
        ALTER TABLE users 
        DROP CONSTRAINT IF EXISTS check_user_role
    """)
    op.execute("""
        ALTER TABLE users 
        ADD CONSTRAINT check_valid_role 
        CHECK (role IN ('engineer', 'dealer', 'moderator'))
    """)
    
    # components
    op.execute("""
        ALTER TABLE components 
        DROP CONSTRAINT IF EXISTS check_component_type
    """)
    op.execute("""
        ALTER TABLE components 
        ADD CONSTRAINT check_valid_role 
        CHECK (type IN ('DVS', 'KPP', 'RK', 'HR', 'BK'))
    """)
    
    # softwares
    op.execute("""
        ALTER TABLE softwares 
        DROP CONSTRAINT IF EXISTS check_software_status
    """)
    op.execute("""
        ALTER TABLE softwares 
        ADD CONSTRAINT check_valid_role 
        CHECK (status IN ('serial', 'in operation', 'experienced'))
    """)
    
    # ========================================================================
    # 2. НЕ удаляем is_closed при откате (чтобы не потерять данные)
    # Если очень нужно — раскомментируйте строку ниже:
    # op.drop_column('support_message', 'is_closed')
    # ========================================================================