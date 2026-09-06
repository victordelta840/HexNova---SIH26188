import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class ScreeningSession(Base):
    __tablename__ = "screening_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    document_type: Mapped[str | None] = mapped_column(String(32))
    document_hash: Mapped[str | None] = mapped_column(String(128))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    risk_score: Mapped[float | None]
    risk_level: Mapped[str | None] = mapped_column(String(16))
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="DEMONSTRATION")
    officer_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    documents: Mapped[list["DocumentRecord"]] = relationship(back_populates="session")
    risk_assessment: Mapped["RiskAssessment | None"] = relationship(
        back_populates="session", uselist=False
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="session")

    __table_args__ = (
        Index("ix_screening_sessions_created_at", "created_at"),
        Index("ix_screening_sessions_risk_level", "risk_level"),
        Index("ix_screening_sessions_status", "status"),
        Index("ix_screening_sessions_document_type", "document_type"),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_is_active", "is_active"),
    )


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    screening_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("screening_sessions.id", ondelete="CASCADE"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_reference: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[ScreeningSession] = relationship(back_populates="documents")
    extracted_fields: Mapped[list["ExtractedField"]] = relationship(back_populates="document")
    validation_results: Mapped[list["ValidationResult"]] = relationship(back_populates="document")
    tampering_analysis: Mapped["TamperingAnalysis | None"] = relationship(
        back_populates="document", uselist=False
    )
    face_verifications: Mapped[list["FaceVerification"]] = relationship(back_populates="document")


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    field_value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None]

    document: Mapped[DocumentRecord] = relationship(back_populates="extracted_fields")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False
    )
    check_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    document: Mapped[DocumentRecord] = relationship(back_populates="validation_results")


class TamperingAnalysis(Base):
    __tablename__ = "tampering_analyses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    assessment: Mapped[str] = mapped_column(String(32), nullable=False)
    indicators: Mapped[list | None] = mapped_column(JSON)
    evidence: Mapped[dict | None] = mapped_column(JSON)

    document: Mapped[DocumentRecord] = relationship(back_populates="tampering_analysis")


class FaceVerification(Base):
    __tablename__ = "face_verifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False
    )
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    similarity: Mapped[float | None]
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    document: Mapped[DocumentRecord] = relationship(back_populates="face_verifications")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    screening_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("screening_sessions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[float | None]
    reasons: Mapped[list | None] = mapped_column(JSON)

    session: Mapped[ScreeningSession] = relationship(back_populates="risk_assessment")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    screening_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("screening_sessions.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    module_name: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str | None] = mapped_column(String(32))
    details: Mapped[str | None] = mapped_column(Text)
    record_hash: Mapped[str | None] = mapped_column(String(128))
    actor_id: Mapped[str | None] = mapped_column(String(128))
    actor_role: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[ScreeningSession | None] = relationship(back_populates="audit_events")