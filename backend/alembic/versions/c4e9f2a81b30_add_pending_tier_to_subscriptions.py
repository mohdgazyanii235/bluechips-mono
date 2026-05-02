"""add pending_tier to subscriptions

Revision ID: c4e9f2a81b30
Revises: b7d2e1f45a89
Create Date: 2026-05-02 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c4e9f2a81b30'
down_revision = 'b7d2e1f45a89'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('subscriptions', sa.Column('pending_tier', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('subscriptions', 'pending_tier')
