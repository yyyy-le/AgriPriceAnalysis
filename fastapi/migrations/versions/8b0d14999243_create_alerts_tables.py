"""create alerts tables

Revision ID: 8b0d14999243
Revises: c3d4e5f6g7h8
Create Date: 2026-04-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8b0d14999243'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建预警规则表
    op.execute("""
        CREATE TABLE price_alerts (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            alert_type VARCHAR(10) NOT NULL CHECK (alert_type IN ('above', 'below')),
            threshold DECIMAL(10, 2) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # 创建索引
    op.create_index('idx_price_alerts_user_id', 'price_alerts', ['user_id'])
    op.create_index('idx_price_alerts_product_id', 'price_alerts', ['product_id'])
    op.create_index('idx_price_alerts_is_active', 'price_alerts', ['is_active'])

    # 创建预警历史记录表
    op.execute("""
        CREATE TABLE alert_logs (
            id SERIAL PRIMARY KEY,
            alert_id INT NOT NULL REFERENCES price_alerts(id) ON DELETE CASCADE,
            triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            price_value DECIMAL(10, 2) NOT NULL,
            threshold_value DECIMAL(10, 2) NOT NULL,
            alert_type VARCHAR(10) NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE
        );
    """)

    # 创建索引
    op.create_index('idx_alert_logs_alert_id', 'alert_logs', ['alert_id'])
    op.create_index('idx_alert_logs_triggered_at', 'alert_logs', ['triggered_at'])


def downgrade() -> None:
    op.drop_table('alert_logs')
    op.drop_table('price_alerts')
