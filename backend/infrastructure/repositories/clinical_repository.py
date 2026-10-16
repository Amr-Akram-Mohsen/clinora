"""
infrastructure/repositories/clinical_repository.py

Repository for clinical entities: Visits, Observations, and Prescriptions.
Strictly scoped to organization_id tenant boundary.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from infrastructure.database.models.clinical import Observation, Prescription, Visit


class ClinicalRepository:
    """
    Data access for Visits, Observations, and Prescriptions within an organization tenant boundary.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---------------------------------------------------------------------------
    # Visits (Encounters)
    # ---------------------------------------------------------------------------

    async def create_visit(
        self,
        organization_id: uuid.UUID,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        chief_complaint: str,
        appointment_id: uuid.UUID | None = None,
        subjective_notes: str | None = None,
        objective_notes: str | None = None,
        assessment_notes: str | None = None,
        plan_notes: str | None = None,
    ) -> Visit:
        """Create and persist a new clinical encounter draft."""
        visit = Visit(
            organization_id=organization_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_id=appointment_id,
            chief_complaint=chief_complaint.strip(),
            subjective_notes=subjective_notes.strip() if subjective_notes else None,
            objective_notes=objective_notes.strip() if objective_notes else None,
            assessment_notes=assessment_notes.strip() if assessment_notes else None,
            plan_notes=plan_notes.strip() if plan_notes else None,
            status="IN_PROGRESS",
        )
        self._session.add(visit)
        await self._session.flush()
        return visit

    async def find_visit_by_id(
        self,
        organization_id: uuid.UUID,
        visit_id: uuid.UUID,
    ) -> Visit | None:
        """Find a visit by ID, eagerly loading observations and prescriptions."""
        stmt = (
            select(Visit)
            .where(
                Visit.id == visit_id,
                Visit.organization_id == organization_id,
            )
            .options(
                selectinload(Visit.observations),
                selectinload(Visit.prescriptions),
                selectinload(Visit.doctor),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_patient_visits(
        self,
        organization_id: uuid.UUID,
        patient_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Visit], int]:
        """Fetch chronological list of visits for a patient."""
        base_filter = [
            Visit.organization_id == organization_id,
            Visit.patient_id == patient_id,
        ]

        count_stmt = select(func.count(Visit.id)).where(*base_filter)
        total_count = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(Visit)
            .where(*base_filter)
            .options(selectinload(Visit.doctor))
            .order_by(Visit.visit_date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total_count

    async def update_visit_draft(
        self,
        visit: Visit,
        chief_complaint: str | None = None,
        subjective_notes: str | None = None,
        objective_notes: str | None = None,
        assessment_notes: str | None = None,
        plan_notes: str | None = None,
    ) -> Visit:
        """Update draft notes for an open visit."""
        if chief_complaint is not None:
            visit.chief_complaint = chief_complaint.strip()
        if subjective_notes is not None:
            visit.subjective_notes = subjective_notes.strip() if subjective_notes else None
        if objective_notes is not None:
            visit.objective_notes = objective_notes.strip() if objective_notes else None
        if assessment_notes is not None:
            visit.assessment_notes = assessment_notes.strip() if assessment_notes else None
        if plan_notes is not None:
            visit.plan_notes = plan_notes.strip() if plan_notes else None

        await self._session.flush()
        return visit

    async def sign_visit(self, visit: Visit) -> Visit:
        """Lock and sign an encounter."""
        visit.status = "SIGNED"
        visit.signed_at = datetime.now(UTC)
        await self._session.flush()
        return visit

    # ---------------------------------------------------------------------------
    # Observations (Vitals)
    # ---------------------------------------------------------------------------

    async def record_observation(
        self,
        organization_id: uuid.UUID,
        patient_id: uuid.UUID,
        obs_type: str,
        value: float,
        unit: str,
        is_abnormal: bool,
        visit_id: uuid.UUID | None = None,
        recorded_by_id: uuid.UUID | None = None,
    ) -> Observation:
        """Record a discrete clinical measurement."""
        obs = Observation(
            organization_id=organization_id,
            patient_id=patient_id,
            visit_id=visit_id,
            recorded_by_id=recorded_by_id,
            type=obs_type.upper().strip(),
            value=value,
            unit=unit.strip(),
            is_abnormal=is_abnormal,
        )
        self._session.add(obs)
        await self._session.flush()
        return obs

    async def list_patient_observations(
        self,
        organization_id: uuid.UUID,
        patient_id: uuid.UUID,
        limit: int = 50,
    ) -> list[Observation]:
        """Fetch recent observations for a patient."""
        stmt = (
            select(Observation)
            .where(
                Observation.organization_id == organization_id,
                Observation.patient_id == patient_id,
            )
            .order_by(Observation.recorded_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------------------------
    # Prescriptions
    # ---------------------------------------------------------------------------

    async def create_prescription(
        self,
        organization_id: uuid.UUID,
        patient_id: uuid.UUID,
        visit_id: uuid.UUID,
        doctor_id: uuid.UUID,
        medication_name: str,
        dosage: str,
        frequency: str,
        duration: str,
        instructions: str | None = None,
        route: str = "ORAL",
    ) -> Prescription:
        """Issue and record a prescription."""
        rx = Prescription(
            organization_id=organization_id,
            patient_id=patient_id,
            visit_id=visit_id,
            doctor_id=doctor_id,
            medication_name=medication_name.strip(),
            dosage=dosage.strip(),
            route=route.upper().strip(),
            frequency=frequency.strip(),
            duration=duration.strip(),
            instructions=instructions.strip() if instructions else None,
            is_active=True,
        )
        self._session.add(rx)
        await self._session.flush()
        return rx

    async def list_patient_prescriptions(
        self,
        organization_id: uuid.UUID,
        patient_id: uuid.UUID,
        active_only: bool = False,
    ) -> list[Prescription]:
        """Fetch prescriptions for a patient."""
        stmt = (
            select(Prescription)
            .where(
                Prescription.organization_id == organization_id,
                Prescription.patient_id == patient_id,
            )
        )
        if active_only:
            stmt = stmt.where(Prescription.is_active.is_(True))

        stmt = stmt.options(selectinload(Prescription.doctor)).order_by(Prescription.issued_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
