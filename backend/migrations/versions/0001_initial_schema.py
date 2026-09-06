"""Create the initial screening schema.

Revision ID: 0001_initial_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=True)

    op.create_table(
        "screening_sessions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("officer_id", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "document_records",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("screening_session_id", uuid_type, nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("storage_reference", sa.String(length=512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["screening_session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "extracted_fields",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("field_value", sa.Text()),
        sa.Column("confidence", sa.Float()),
        sa.ForeignKeyConstraint(["document_id"], ["document_records.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "validation_results",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("check_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document_records.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "tampering_analyses",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("document_id", uuid_type, nullable=False, unique=True),
        sa.Column("assessment", sa.String(length=32), nullable=False),
        sa.Column("indicators", sa.JSON()),
        sa.Column("evidence", sa.JSON()),
        sa.ForeignKeyConstraint(["document_id"], ["document_records.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "face_verifications",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("similarity", sa.Float()),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document_records.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "risk_assessments",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("screening_session_id", uuid_type, nullable=False, unique=True),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Float()),
        sa.Column("reasons", sa.JSON()),
        sa.ForeignKeyConstraint(["screening_session_id"], ["screening_sessions.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("screening_session_id", uuid_type),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("record_hash", sa.String(length=128)),
        sa.Column("actor_id", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["screening_session_id"], ["screening_sessions.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("risk_assessments")
    op.drop_table("face_verifications")
    op.drop_table("tampering_analyses")
    op.drop_table("validation_results")
    op.drop_table("extracted_fields")
    op.drop_table("document_records")
    op.drop_table("screening_sessions")