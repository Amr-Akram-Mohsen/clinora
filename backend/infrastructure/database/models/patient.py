"""
infrastructure/database/models/patient.py

ORM models for Patient and Allergy records.

Design:
- Patient represents the Master Patient Index (MPI) within an organization.
- Every patient belongs to exactly one organization (tenancy boundary).
- Soft active status via `is_active`.
- Allergies represent documented clinical adverse drug/substance reactions.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from infrastructure.database.models.clinical import (
        Appointment,
        Observation,
        Prescription,
        Visit,
    )
    from infrastructure.database.models.organization import Organization


class Patient(UUIDPKMixin, TimestampMixin, Base):
    """
    Patient master demographic and medical identity.
    Multi-tenant scoped by organization_id.
    """

    __tablename__ = "patients"

    __table_args__ = (
        Index("ix_patients_organization_id", "organization_id"),
        Index("ix_patients_org_full_name", "organization_id", "full_name"),
        Index("ix_patients_org_phone", "organization_id", "phone"),
        Index("ix_patients_org_national_id", "organization_id", "national_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    national_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)  # MALE, FEMALE, OTHER
    blood_type: Mapped[str | None] = mapped_column(String(10), nullable=True)  # A+, B+, O-, etc.
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped[Organization] = relationship("Organization")
    allergies: Mapped[list[Allergy]] = relationship(
        "Allergy",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="Allergy.recorded_at.desc()",
    )
    visits: Mapped[list[Visit]] = relationship(
        "Visit",
        back_populates="patient",
        order_by="Visit.visit_date.desc()",
    )
    observations: Mapped[list[Observation]] = relationship(
        "Observation",
        back_populates="patient",
        order_by="Observation.recorded_at.desc()",
    )
    prescriptions: Mapped[list[Prescription]] = relationship(
        "Prescription",
        back_populates="patient",
        order_by="Prescription.issued_at.desc()",
    )
    appointments: Mapped[list[Appointment]] = relationship(
        "Appointment",
        back_populates="patient",
        order_by="Appointment.scheduled_time.desc()",
    )

    def __repr__(self) -> str:
        return f"<Patient id={self.id} name={self.full_name!r}>"


class Allergy(UUIDPKMixin, Base):
    """
    Documented drug or substance allergy for a patient.
    """

    __tablename__ = "allergies"

    __table_args__ = (
        Index("ix_allergies_organization_id", "organization_id"),
        Index("ix_allergies_patient_id", "patient_id"),
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

    allergen: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # MILD, MODERATE, SEVERE, LIFE_THREATENING
    reaction: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    patient: Mapped[Patient] = relationship("Patient", back_populates="allergies")

    def __repr__(self) -> str:
        return f"<Allergy patient_id={self.patient_id} allergen={self.allergen!r} severity={self.severity!r}>"
