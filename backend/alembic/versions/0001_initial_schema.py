"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "boroughs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("seo_title", sa.String(70)),
        sa.Column("seo_description", sa.String(160)),
        sa.Column("is_premium_area", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="99"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_boroughs_slug", "boroughs", ["slug"])

    op.create_table(
        "escorts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("stage_name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("age", sa.Integer()),
        sa.Column("nationality", sa.String(80)),
        sa.Column("ethnicity", sa.String(80)),
        sa.Column("height_cm", sa.Integer()),
        sa.Column("build", sa.String(20)),
        sa.Column("hair_colour", sa.String(50)),
        sa.Column("eye_colour", sa.String(50)),
        sa.Column("dress_size", sa.String(20)),
        sa.Column("chest", sa.String(30)),
        sa.Column("borough_id", postgresql.UUID(as_uuid=True)),
        sa.Column("availability_type", sa.String(10)),
        sa.Column("rate_30min", sa.Integer()),
        sa.Column("rate_1hour", sa.Integer()),
        sa.Column("rate_2hours", sa.Integer()),
        sa.Column("rate_overnight", sa.Integer()),
        sa.Column("about_me", sa.String(600)),
        sa.Column("languages", postgresql.ARRAY(sa.String())),
        sa.Column("booking_notice", sa.String(100)),
        sa.Column("std_tested", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("std_tested_date", sa.String(20)),
        sa.Column("verification_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_verification_token", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("available_now", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("profile_complete", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("subscription_tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("subscription_expires_at", sa.DateTime()),
        sa.Column("stripe_customer_id", sa.String(100)),
        sa.Column("stripe_subscription_id", sa.String(100)),
        sa.Column("profile_views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("contact_clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["borough_id"], ["boroughs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_escorts_email", "escorts", ["email"])
    op.create_index("ix_escorts_slug", "escorts", ["slug"])
    op.create_index("ix_escorts_borough_id", "escorts", ["borough_id"])

    op.create_table(
        "escort_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("escort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("thumbnail_url", sa.String(500)),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["escort_id"], ["escorts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_escort_photos_escort_id", "escort_photos", ["escort_id"])

    op.create_table(
        "escort_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("escort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["escort_id"], ["escorts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_escort_services_escort_id", "escort_services", ["escort_id"])

    op.create_table(
        "verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("escort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("id_document_url", sa.String(500)),
        sa.Column("selfie_url", sa.String(500)),
        sa.Column("match_selfie_url", sa.String(500)),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("admin_notes", sa.Text()),
        sa.Column("reviewed_by", sa.String(100)),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["escort_id"], ["escorts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("escort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tier", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("stripe_subscription_id", sa.String(100)),
        sa.Column("stripe_price_id", sa.String(100)),
        sa.Column("amount_gbp", sa.Integer()),
        sa.Column("current_period_start", sa.DateTime()),
        sa.Column("current_period_end", sa.DateTime()),
        sa.Column("cancelled_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["escort_id"], ["escorts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "boosts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("escort_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("boost_type", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("stripe_payment_intent_id", sa.String(100)),
        sa.Column("amount_gbp", sa.Integer()),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["escort_id"], ["escorts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("boosts")
    op.drop_table("subscriptions")
    op.drop_table("verifications")
    op.drop_table("escort_services")
    op.drop_table("escort_photos")
    op.drop_table("escorts")
    op.drop_table("boroughs")
