"""add discount codes and referral system

Revision ID: d5f3b2c91e47
Revises: c4e9f2a81b30
Create Date: 2026-05-04 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import random
import string

revision = 'd5f3b2c91e47'
down_revision = 'c4e9f2a81b30'
branch_labels = None
depends_on = None


def _random_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


def upgrade() -> None:
    # ── discount_codes table ──────────────────────────────────────────────────
    op.create_table(
        'discount_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('percent_off', sa.Integer(), nullable=False),
        sa.Column('applicable_tiers', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('duration_months', sa.Integer(), nullable=False),
        sa.Column('max_redemptions', sa.Integer(), nullable=True),
        sa.Column('current_redemptions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_unique_constraint('uq_discount_codes_code', 'discount_codes', ['code'])
    op.create_index('ix_discount_codes_code', 'discount_codes', ['code'])

    # ── referral fields on escorts ────────────────────────────────────────────
    op.add_column('escorts', sa.Column('referral_code', sa.String(10), nullable=True))
    op.add_column('escorts', sa.Column('referred_by_code', sa.String(10), nullable=True))
    op.add_column('escorts', sa.Column('referral_reward_claimed', sa.Boolean(), nullable=False, server_default='false'))

    # Backfill unique referral codes for all existing escorts
    conn = op.get_bind()
    escort_ids = conn.execute(sa.text("SELECT id FROM escorts WHERE referral_code IS NULL")).fetchall()
    used_codes: set[str] = set()
    for row in escort_ids:
        for _ in range(50):
            code = _random_code()
            if code not in used_codes:
                used_codes.add(code)
                break
        conn.execute(
            sa.text("UPDATE escorts SET referral_code = :code WHERE id = :id"),
            {"code": code, "id": row[0]},
        )

    # Now safe to add unique constraint
    op.create_unique_constraint('uq_escorts_referral_code', 'escorts', ['referral_code'])
    op.create_index('ix_escorts_referral_code', 'escorts', ['referral_code'])


def downgrade() -> None:
    op.drop_index('ix_escorts_referral_code', table_name='escorts')
    op.drop_constraint('uq_escorts_referral_code', 'escorts', type_='unique')
    op.drop_column('escorts', 'referral_reward_claimed')
    op.drop_column('escorts', 'referred_by_code')
    op.drop_column('escorts', 'referral_code')
    op.drop_index('ix_discount_codes_code', table_name='discount_codes')
    op.drop_table('discount_codes')
