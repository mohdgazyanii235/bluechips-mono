"""add psp_* columns for provider-agnostic payment tracking

Revision ID: b8c4f2a91d63
Revises: a47c3b8de219
Create Date: 2026-05-13 21:30:00.000000

This migration introduces a provider-agnostic identifier layer so we can
swap payment providers (Stripe → Verotel) without further DB changes.

The legacy stripe_* columns are RETAINED to preserve historic data. They
should not be written to by new code.
"""
from alembic import op
import sqlalchemy as sa

revision = 'b8c4f2a91d63'
down_revision = 'a47c3b8de219'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # escorts
    op.add_column('escorts', sa.Column('psp_provider', sa.String(20), nullable=True))
    op.add_column('escorts', sa.Column('psp_subscription_id', sa.String(100), nullable=True))
    op.add_column('escorts', sa.Column('psp_blue_tick_subscription_id', sa.String(100), nullable=True))
    op.create_index('ix_escorts_psp_subscription_id', 'escorts', ['psp_subscription_id'])

    # subscriptions
    op.add_column('subscriptions', sa.Column('psp_provider', sa.String(20), nullable=True))
    op.add_column('subscriptions', sa.Column('psp_subscription_id', sa.String(100), nullable=True))
    op.add_column('subscriptions', sa.Column('psp_checkout_reference', sa.String(100), nullable=True))
    op.create_index('ix_subscriptions_psp_subscription_id', 'subscriptions', ['psp_subscription_id'])


def downgrade() -> None:
    op.drop_index('ix_subscriptions_psp_subscription_id', table_name='subscriptions')
    op.drop_column('subscriptions', 'psp_checkout_reference')
    op.drop_column('subscriptions', 'psp_subscription_id')
    op.drop_column('subscriptions', 'psp_provider')

    op.drop_index('ix_escorts_psp_subscription_id', table_name='escorts')
    op.drop_column('escorts', 'psp_blue_tick_subscription_id')
    op.drop_column('escorts', 'psp_subscription_id')
    op.drop_column('escorts', 'psp_provider')
