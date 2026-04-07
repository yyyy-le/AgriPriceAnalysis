"""add spec_info and unit_info to price_records

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE price_records
        ADD COLUMN IF NOT EXISTS spec_info VARCHAR(100),
        ADD COLUMN IF NOT EXISTS unit_info VARCHAR(20)
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE price_records
        DROP COLUMN IF EXISTS spec_info,
        DROP COLUMN IF EXISTS unit_info
    """)
