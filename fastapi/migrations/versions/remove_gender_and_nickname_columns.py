"""remove gender and nickname columns

Revision ID: a1b2c3d4e5f6
Revises: 883992f5b42f
Create Date: 2026-04-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '883992f5b42f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('users', 'nickname')
    op.drop_column('users', 'gender')
    op.execute('DROP TYPE IF EXISTS gender_type')


def downgrade() -> None:
    postgresql.ENUM('male', 'female', 'unknown', name='gender_type').create(op.get_bind())
    op.add_column('users', sa.Column('gender', postgresql.ENUM('male', 'female', 'unknown', name='gender_type'),
                                      nullable=False, server_default='unknown'))
    op.add_column('users', sa.Column('nickname', sa.String(length=255, collation='zh-x-icu'),
                                     nullable=False, server_default=''))
