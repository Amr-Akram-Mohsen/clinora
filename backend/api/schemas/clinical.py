"""
api/schemas/clinical.py

Pydantic schemas for clinical visits (SOAP notes), observations (vitals), and prescriptions.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ObservationItemCreate(BaseModel):
    type: str = Field(..., description="Measurement type, e.g. BLOOD_PRESSURE_SYS, HEART_RATE, etc.")
    value: float
    unit: str = Field(..., max_length=30)


class ObservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    visit_id: uuid.UUID | None = None
    type: str
    value: float
    unit: str
    is_abnormal: bool
    recorded_at: datetime


class PrescriptionItemCreate(BaseModel):
    medication_name: str = Field(..., min_length=1, max_length=255)
    dosage: str = Field(..., min_length=1, max_length=100)
    route: str = Field(default="ORAL", max_length=50)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., min_length=1, max_length=100)
    instructions: str | None = None


class PrescriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    visit_id: uuid.UUID
    doctor_id: uuid.UUID
    medication_name: str
    dosage: str
    route: str
    frequency: str
    duration: str
    instructions: str | None = None
    is_active: bool
    issued_at: datetime


class VisitCreate(BaseModel):
    patient_id: uuid.UUID
    chief_complaint: str = Field(..., min_length=1)
    appointment_id: uuid.UUID | None = None
    subjective_notes: str | None = None
    objective_notes: str | None = None
    assessment_notes: str | None = None
    plan_notes: str | None = None


class VisitUpdate(BaseModel):
    chief_complaint: str | None = None
    subjective_notes: str | None = None
    objective_notes: str | None = None
    assessment_notes: str | None = None
    plan_notes: str | None = None


class VisitListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    visit_date: datetime
    status: str
    chief_complaint: str
    signed_at: datetime | None = None


class VisitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_id: uuid.UUID | None = None
    visit_date: datetime
    status: str
    chief_complaint: str
    subjective_notes: str | None = None
    objective_notes: str | None = None
    assessment_notes: str | None = None
    plan_notes: str | None = None
    signed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    observations: list[ObservationRead] = []
    prescriptions: list[PrescriptionRead] = []
