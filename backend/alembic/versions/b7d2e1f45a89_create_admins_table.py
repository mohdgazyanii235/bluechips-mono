"""create admins table

Revision ID: b7d2e1f45a89
Revises: a3f1c8e29d74
Create Date: 2026-05-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b7d2e1f45a89'
down_revision = 'a3f1c8e29d74'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'admins',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_admins_email'), 'admins', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_admins_email'), table_name='admins')
    op.drop_table('admins')
