"""Add case management query indexes.

Revision ID: 0003_case_management_indexes
Revises: 0002_audit_case_fields
"""
from alembic import op


revision = "0003_case_management_indexes"
down_revision = "0002_audit_case_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_screening_sessions_created_at", "screening_sessions", ["created_at"])
    op.create_index("ix_screening_sessions_risk_level", "screening_sessions", ["risk_level"])
    op.create_index("ix_screening_sessions_status", "screening_sessions", ["status"])
    op.create_index("ix_screening_sessions_document_type", "screening_sessions", ["document_type"])


def downgrade() -> None:
    op.drop_index("ix_screening_sessions_document_type", table_name="screening_sessions")
    op.drop_index("ix_screening_sessions_status", table_name="screening_sessions")
    op.drop_index("ix_screening_sessions_risk_level", table_name="screening_sessions")
    op.drop_index("ix_screening_sessions_created_at", table_name="screening_sessions")