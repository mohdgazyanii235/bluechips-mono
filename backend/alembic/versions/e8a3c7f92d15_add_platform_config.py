"""add platform_config table

Revision ID: e8a3c7f92d15
Revises: d5f3b2c91e47
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa

revision = 'e8a3c7f92d15'
down_revision = 'd5f3b2c91e47'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'platform_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('essential_monthly_pence', sa.Integer(), nullable=False, server_default='1199'),
        sa.Column('essential_annual_pence', sa.Integer(), nullable=False, server_default='11990'),
        sa.Column('premium_monthly_pence', sa.Integer(), nullable=False, server_default='1899'),
        sa.Column('premium_annual_pence', sa.Integer(), nullable=False, server_default='18990'),
        sa.Column('elite_monthly_pence', sa.Integer(), nullable=False, server_default='2399'),
        sa.Column('elite_annual_pence', sa.Integer(), nullable=False, server_default='23990'),
        sa.Column('blue_tick_setup_pence', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('blue_tick_monthly_pence', sa.Integer(), nullable=False, server_default='399'),
        sa.Column('stripe_essential_monthly_id', sa.String(200), nullable=False, server_default=''),
        sa.Column('stripe_essential_annual_id', sa.String(200), nullable=False, server_default=''),
        sa.Column('stripe_premium_monthly_id', sa.String(200), nullable=False, server_default=''),
        sa.Column('stripe_premium_annual_id', sa.String(200), nullable=False, server_default=''),
        sa.Column('stripe_elite_monthly_id', sa.String(200), nullable=False, server_default=''),
        sa.Column('stripe_elite_annual_id', sa.String(200), nullable=False, server_default=''),
        sa.Column('stripe_blue_tick_setup_id', sa.String(200), nullable=False, server_default=''),
        sa.Column('stripe_blue_tick_monthly_id', sa.String(200), nullable=False, server_default=''),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    # Seed the singleton row — Stripe IDs populated at runtime from config on first boot
    op.execute("INSERT INTO platform_config (id) VALUES (1)")


def downgrade() -> None:
    op.drop_table('platform_config')
