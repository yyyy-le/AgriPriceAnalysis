"""restore_cellphone_unique

Revision ID: d24005c6b70a
Revises: 92fff32c2eb5
Create Date: 2026-04-08 18:55:44.132496

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd24005c6b70a'
down_revision: Union[str, None] = '92fff32c2eb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
