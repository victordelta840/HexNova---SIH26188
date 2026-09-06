from app.db.base import Base
from app.db import models


def test_screening_schema_contains_required_tables() -> None:
    expected_tables = {
        "screening_sessions",
        "document_records",
        "extracted_fields",
        "validation_results",
        "tampering_analyses",
        "face_verifications",
        "risk_assessments",
        "audit_events",
    }

    assert expected_tables.issubset(Base.metadata.tables)


def test_audit_fields_are_registered_on_existing_models() -> None:
    assert {"case_id", "document_hash", "completed_at", "risk_level", "mode"}.issubset(
        Base.metadata.tables["screening_sessions"].c.keys()
    )
    assert {"module_name", "status", "details"}.issubset(Base.metadata.tables["audit_events"].c.keys())