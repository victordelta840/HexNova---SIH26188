"""Add case and audit lifecycle fields.

Revision ID: 0002_audit_case_fields
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_audit_case_fields"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("screening_sessions", sa.Column("case_id", sa.String(length=64), nullable=True))
    op.add_column("screening_sessions", sa.Column("document_type", sa.String(length=32)))
    op.add_column("screening_sessions", sa.Column("document_hash", sa.String(length=128)))
    op.add_column("screening_sessions", sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.add_column("screening_sessions", sa.Column("risk_score", sa.Float()))
    op.add_column("screening_sessions", sa.Column("risk_level", sa.String(length=16)))
    op.add_column("screening_sessions", sa.Column("mode", sa.String(length=32), nullable=True))
    op.add_column("audit_events", sa.Column("module_name", sa.String(length=64)))
    op.add_column("audit_events", sa.Column("status", sa.String(length=32)))
    op.add_column("audit_events", sa.Column("details", sa.Text()))
    op.execute("UPDATE screening_sessions SET case_id = 'LEGACY-' || id::text WHERE case_id IS NULL")
    op.execute("UPDATE screening_sessions SET mode = 'DEMONSTRATION' WHERE mode IS NULL")
    op.alter_column("screening_sessions", "case_id", nullable=False)
    op.alter_column("screening_sessions", "mode", nullable=False)
    op.create_unique_constraint("uq_screening_sessions_case_id", "screening_sessions", ["case_id"])


def downgrade() -> None:
    op.drop_constraint("uq_screening_sessions_case_id", "screening_sessions", type_="unique")
    op.drop_column("audit_events", "details")
    op.drop_column("audit_events", "status")
    op.drop_column("audit_events", "module_name")
    op.drop_column("screening_sessions", "mode")
    op.drop_column("screening_sessions", "risk_level")
    op.drop_column("screening_sessions", "risk_score")
    op.drop_column("screening_sessions", "completed_at")
    op.drop_column("screening_sessions", "document_hash")
    op.drop_column("screening_sessions", "document_type")
    op.drop_column("screening_sessions", "case_id")