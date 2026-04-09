"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-04-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0001_init'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.run_ddl_script('2025_10_24_1438_ext-hstore_883992f5b42f.sql')
    op.run_ddl_script('2025_10_24_1438_ext-pg_trgm_883992f5b42f.sql')
    op.run_ddl_script('2025_10_24_1438_ext-unaccent_883992f5b42f.sql')
    op.run_ddl_script('2025_10_24_1438_ext-uuid-ossp_883992f5b42f.sql')
    op.run_ddl_script('2025_10_24_1438_ext-btree_gin_883992f5b42f.sql')
    op.run_ddl_script('2025_10_24_1438_ext-btree_gist_883992f5b42f.sql')
    op.run_ddl_script('2025_10_24_1438_ext-fuzzystrmatch_883992f5b42f.sql')
    op.run_ddl_script('2025_10_24_1438_tgr_func-update_updated_at_column_883992f5b42f.sql')

    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('cellphone', sa.String(length=45), nullable=True),
        sa.Column('state', postgresql.ENUM('disabled', 'enabled', name='user_state_type'), server_default='enabled', nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('cellphone'),
    )
    op.run_ddl_script('2025_10_24_1438_tgr-update_updated_at_column_users_883992f5b42f.sql')

    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], name='fk_categories_parent_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'markets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('province', sa.String(length=50), nullable=True),
        sa.Column('city', sa.String(length=50), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('unit', sa.String(length=20), server_default=sa.text("'公斤'::character varying"), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name='products_category_id_fkey'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'price_records',
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('market_id', sa.Integer(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('min_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('max_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('avg_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('source', sa.String(length=20), nullable=True),
        sa.Column('spec_info', sa.String(length=100), nullable=True),
        sa.Column('unit_info', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
    )
    op.create_index('price_records_time_idx', 'price_records', ['time'])
    op.create_index('price_records_product_id_time_idx', 'price_records', ['product_id', 'time'])
    op.create_index('price_records_market_id_time_idx', 'price_records', ['market_id', 'time'])
    op.create_index('price_records_time_product_id_market_id_idx', 'price_records', ['time', 'product_id', 'market_id'], unique=True)
    op.create_index('idx_price_records_product_time', 'price_records', ['product_id', 'time'])

    op.create_table(
        'price_alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(length=10), nullable=False),
        sa.Column('threshold', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("alert_type IN ('above', 'below')"),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_price_alerts_user_id', 'price_alerts', ['user_id'])
    op.create_index('idx_price_alerts_product_id', 'price_alerts', ['product_id'])
    op.create_index('idx_price_alerts_is_active', 'price_alerts', ['is_active'])

    op.create_table(
        'alert_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('triggered_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('price_value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('threshold_value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('alert_type', sa.String(length=10), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.ForeignKeyConstraint(['alert_id'], ['price_alerts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_alert_logs_alert_id', 'alert_logs', ['alert_id'])
    op.create_index('idx_alert_logs_triggered_at', 'alert_logs', ['triggered_at'])


def downgrade() -> None:
    op.drop_table('alert_logs')
    op.drop_table('price_alerts')
    op.drop_table('price_records')
    op.drop_table('products')
    op.drop_table('markets')
    op.drop_table('categories')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS user_state_type')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column CASCADE')
