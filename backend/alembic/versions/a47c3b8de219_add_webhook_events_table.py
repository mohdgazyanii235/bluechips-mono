"""add webhook events table for idempotency

Revision ID: a47c3b8de219
Revises: f9e2d4b71c83
Create Date: 2026-05-11 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a47c3b8de219'
down_revision = 'f9e2d4b71c83'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_webhook_events_received_at', 'webhook_events', ['received_at'])


def downgrade() -> None:
    op.drop_index('ix_webhook_events_received_at', table_name='webhook_events')
    op.drop_table('webhook_events')
