"""add parent_id to categories

Revision ID: a3f8b2c1d4e5
Revises: 92fff32c2eb5
Create Date: 2026-04-08

"""
from alembic import op
import sqlalchemy as sa

revision = 'a3f8b2c1d4e5'
down_revision = 'd24005c6b70a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('categories', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_categories_parent_id', 'categories', 'categories',
        ['parent_id'], ['id'], ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_categories_parent_id', 'categories', type_='foreignkey')
    op.drop_column('categories', 'parent_id')
