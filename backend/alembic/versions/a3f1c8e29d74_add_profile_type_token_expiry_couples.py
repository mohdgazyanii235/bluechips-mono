"""add_profile_type_token_expiry_couples

Revision ID: a3f1c8e29d74
Revises: 5252eaf02a13
Create Date: 2026-05-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f1c8e29d74'
down_revision: Union[str, None] = '5252eaf02a13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'escorts',
        sa.Column('profile_type', sa.String(length=20), nullable=False, server_default='individual'),
    )
    op.add_column(
        'escorts',
        sa.Column('email_verification_token_expires_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('escorts', 'email_verification_token_expires_at')
    op.drop_column('escorts', 'profile_type')
