"""
api/schemas/patient.py

Pydantic schemas for Patient and Allergy endpoints.
Strictly separates public API response contract from internal ORM models.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AllergyCreate(BaseModel):
    allergen: str = Field(..., min_length=1, max_length=255)
    severity: str = Field(..., description="MILD, MODERATE, SEVERE, or LIFE_THREATENING")
    reaction: str | None = Field(default=None, max_length=1000)


class AllergyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    allergen: str
    severity: str
    reaction: str | None = None
    recorded_at: datetime


class PatientCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: date
    gender: str = Field(..., description="MALE, FEMALE, or OTHER")
    phone: str = Field(..., min_length=5, max_length=50)
    national_id: str | None = Field(default=None, max_length=50)
    blood_type: str | None = Field(default=None, max_length=10)
    email: EmailStr | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    blood_type: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    date_of_birth: date
    gender: str
    phone: str
    national_id: str | None = None
    blood_type: str | None = None
    created_at: datetime


class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    full_name: str
    date_of_birth: date
    gender: str
    phone: str
    national_id: str | None = None
    blood_type: str | None = None
    email: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    allergies: list[AllergyRead] = []
