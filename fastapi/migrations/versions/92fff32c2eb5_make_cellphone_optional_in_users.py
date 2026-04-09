"""make_cellphone_optional_in_users

Revision ID: 92fff32c2eb5
Revises: 8b0d14999243
Create Date: 2026-04-07 22:20:57.911602

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '92fff32c2eb5'
down_revision: Union[str, None] = '8b0d14999243'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 将 cellphone 字段改为可空，保留唯一约束
    op.alter_column('users', 'cellphone',
                    existing_type=sa.String(length=45),
                    nullable=True)
    # 确保唯一约束存在（之前可能被删除）
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'users_cellphone_key'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT users_cellphone_key UNIQUE (cellphone);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.alter_column('users', 'cellphone',
                    existing_type=sa.String(length=45),
                    nullable=False)

