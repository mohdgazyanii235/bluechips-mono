"""add outreach prospects table and founding offer fields

Revision ID: f9e2d4b71c83
Revises: e8a3c7f92d15
Create Date: 2026-05-11 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'f9e2d4b71c83'
down_revision = 'e8a3c7f92d15'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Founding offer fields on platform_config (singleton) ──────────────────
    op.add_column('platform_config', sa.Column('founding_offer_active', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('platform_config', sa.Column('founding_offer_limit', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('platform_config', sa.Column('founding_offer_signups', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('platform_config', sa.Column('founding_offer_percent_off', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('platform_config', sa.Column('founding_offer_duration_months', sa.Integer(), nullable=False, server_default='6'))
    op.add_column('platform_config', sa.Column('founding_offer_tier', sa.String(20), nullable=False, server_default='premium'))
    op.add_column('platform_config', sa.Column('founding_offer_includes_blue_tick', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('platform_config', sa.Column('founding_offer_lifetime_discount_percent', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('platform_config', sa.Column('founding_offer_badge_label', sa.String(50), nullable=False, server_default='Founding Member'))

    # ── Founding member tracking on escorts ───────────────────────────────────
    op.add_column('escorts', sa.Column('is_founding_member', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('escorts', sa.Column('founding_member_since', sa.DateTime(), nullable=True))
    op.add_column('escorts', sa.Column('signup_discount_code_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('escorts', sa.Column('profile_reminder_sent_at', sa.DateTime(), nullable=True))
    op.create_foreign_key(
        'fk_escorts_signup_discount_code',
        'escorts',
        'discount_codes',
        ['signup_discount_code_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # ── outreach_prospects table ──────────────────────────────────────────────
    op.create_table(
        'outreach_prospects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('x_handle', sa.String(100), nullable=False),
        sa.Column('stage_name', sa.String(100), nullable=False),
        sa.Column('area', sa.String(100), nullable=True),
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='not_contacted'),
        sa.Column('generated_message', sa.Text(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('discount_code_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('converted_escort_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contacted_at', sa.DateTime(), nullable=True),
        sa.Column('replied_at', sa.DateTime(), nullable=True),
        sa.Column('signed_up_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['discount_code_id'], ['discount_codes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['converted_escort_id'], ['escorts.id'], ondelete='SET NULL'),
    )
    op.create_unique_constraint('uq_outreach_x_handle', 'outreach_prospects', ['x_handle'])
    op.create_index('ix_outreach_status', 'outreach_prospects', ['status'])


def downgrade() -> None:
    op.drop_index('ix_outreach_status', table_name='outreach_prospects')
    op.drop_constraint('uq_outreach_x_handle', 'outreach_prospects', type_='unique')
    op.drop_table('outreach_prospects')

    op.drop_constraint('fk_escorts_signup_discount_code', 'escorts', type_='foreignkey')
    op.drop_column('escorts', 'profile_reminder_sent_at')
    op.drop_column('escorts', 'signup_discount_code_id')
    op.drop_column('escorts', 'founding_member_since')
    op.drop_column('escorts', 'is_founding_member')

    for col in [
        'founding_offer_badge_label',
        'founding_offer_lifetime_discount_percent',
        'founding_offer_includes_blue_tick',
        'founding_offer_tier',
        'founding_offer_duration_months',
        'founding_offer_percent_off',
        'founding_offer_signups',
        'founding_offer_limit',
        'founding_offer_active',
    ]:
        op.drop_column('platform_config', col)
