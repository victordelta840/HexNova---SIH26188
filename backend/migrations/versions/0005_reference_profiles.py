"""Add locked reference profile support.

Revision ID: 0005_reference_profiles
Revises: 0004_users
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_reference_profiles"
down_revision = "0004_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_reference_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("profile_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="LOCKED"),
        sa.Column("document_hash", sa.String(length=128), nullable=False),
        sa.Column("profile_summary", sa.JSON(), nullable=True),
        sa.Column("characteristics", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_action", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_reference_profiles_document_type", "document_reference_profiles", ["document_type"])
    op.create_index("ix_reference_profiles_status", "document_reference_profiles", ["status"])
    op.create_index("ix_reference_profiles_created_at", "document_reference_profiles", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_reference_profiles_created_at", table_name="document_reference_profiles")
    op.drop_index("ix_reference_profiles_status", table_name="document_reference_profiles")
    op.drop_index("ix_reference_profiles_document_type", table_name="document_reference_profiles")
    op.drop_table("document_reference_profiles")
