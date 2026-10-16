"""
infrastructure/database/models/clinical.py

ORM models for core clinical workflows:
- Appointment: Clinical scheduling and visit queue
- Visit: Encounter record with structured SOAP notes and physician signature
- Observation: Discrete quantitative/qualitative vitals and metrics
- Prescription: Prescribed medications, dosage, frequency, and instructions
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from infrastructure.database.models.organization import Organization
    from infrastructure.database.models.patient import Patient
    from infrastructure.database.models.user import User


class Appointment(UUIDPKMixin, TimestampMixin, Base):
    """
    Scheduled consultation appointment between a patient and provider.
    """

    __tablename__ = "appointments"

    __table_args__ = (
        Index("ix_appointments_org_doctor_time", "organization_id", "doctor_id", "scheduled_time"),
        Index("ix_appointments_org_patient", "organization_id", "patient_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="SCHEDULED",
        nullable=False,
    )  # SCHEDULED, CONFIRMED, CHECKED_IN, IN_CONSULTATION, COMPLETED, CANCELLED, NO_SHOW
    reason_for_visit: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped[Patient] = relationship("Patient", back_populates="appointments")
    doctor: Mapped[User] = relationship("User")
    visit: Mapped[Visit | None] = relationship("Visit", back_populates="appointment", uselist=False)

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} patient_id={self.patient_id} status={self.status!r}>"


class Visit(UUIDPKMixin, TimestampMixin, Base):
    """
    Clinical consultation encounter.
    Contains structured SOAP documentation (Subjective, Objective, Assessment, Plan).
    Once status is SIGNED, the record is locked from modification.
    """

    __tablename__ = "visits"

    __table_args__ = (
        Index("ix_visits_org_patient_date", "organization_id", "patient_id", "visit_date"),
        Index("ix_visits_org_doctor", "organization_id", "doctor_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
    )

    visit_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="IN_PROGRESS",
        nullable=False,
    )  # IN_PROGRESS, COMPLETED, SIGNED

    chief_complaint: Mapped[str] = mapped_column(Text, nullable=False)
    subjective_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    patient: Mapped[Patient] = relationship("Patient", back_populates="visits")
    doctor: Mapped[User] = relationship("User")
    appointment: Mapped[Appointment | None] = relationship("Appointment", back_populates="visit")

    observations: Mapped[list[Observation]] = relationship(
        "Observation",
        back_populates="visit",
        order_by="Observation.recorded_at.asc()",
    )
    prescriptions: Mapped[list[Prescription]] = relationship(
        "Prescription",
        back_populates="visit",
        order_by="Prescription.issued_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<Visit id={self.id} patient_id={self.patient_id} status={self.status!r}>"


class Observation(UUIDPKMixin, Base):
    """
    Discrete quantitative or qualitative clinical measurement (vital signs, labs, biometric).
    """

    __tablename__ = "observations"

    __table_args__ = (
        Index("ix_observations_org_patient_type_date", "organization_id", "patient_id", "type", "recorded_at"),
        Index("ix_observations_visit_id", "visit_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    visit_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="SET NULL"),
        nullable=True,
    )
    recorded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # BLOOD_PRESSURE_SYS, BLOOD_PRESSURE_DIA, HEART_RATE, RESPIRATORY_RATE, BODY_TEMPERATURE, OXYGEN_SATURATION, WEIGHT, HEIGHT, BMI, BLOOD_GLUCOSE
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)  # mmHg, bpm, celsius, %, kg, cm, mg/dL
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    patient: Mapped[Patient] = relationship("Patient", back_populates="observations")
    visit: Mapped[Visit | None] = relationship("Visit", back_populates="observations")
    recorded_by: Mapped[User | None] = relationship("User")

    def __repr__(self) -> str:
        return f"<Observation type={self.type!r} value={self.value} {self.unit} abnormal={self.is_abnormal}>"


class Prescription(UUIDPKMixin, Base):
    """
    Direct pharmacotherapy prescription issued by a physician during or linked to an encounter.
    """

    __tablename__ = "prescriptions"

    __table_args__ = (
        Index("ix_prescriptions_org_patient_active", "organization_id", "patient_id", "is_active"),
        Index("ix_prescriptions_visit_id", "visit_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    visit_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="RESTRICT"),
        nullable=False,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    medication_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. 500mg
    route: Mapped[str] = mapped_column(String(50), default="ORAL", nullable=False)  # ORAL, INTRAVENOUS, etc.
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. Once daily, Twice daily
    duration: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. 7 days
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    patient: Mapped[Patient] = relationship("Patient", back_populates="prescriptions")
    visit: Mapped[Visit] = relationship("Visit", back_populates="prescriptions")
    doctor: Mapped[User] = relationship("User")

    def __repr__(self) -> str:
        return f"<Prescription medication={self.medication_name!r} dosage={self.dosage!r} active={self.is_active}>"
