"""
domain/clinical/ranges.py

Clinical observation physiological reference boundaries and validation rules.
Pure Python domain logic — zero infrastructure dependencies.
"""

from dataclasses import dataclass
from enum import StrEnum


class ObservationType(StrEnum):
    BLOOD_PRESSURE_SYS = "BLOOD_PRESSURE_SYS"
    BLOOD_PRESSURE_DIA = "BLOOD_PRESSURE_DIA"
    HEART_RATE = "HEART_RATE"
    RESPIRATORY_RATE = "RESPIRATORY_RATE"
    BODY_TEMPERATURE = "BODY_TEMPERATURE"
    OXYGEN_SATURATION = "OXYGEN_SATURATION"
    WEIGHT = "WEIGHT"
    HEIGHT = "HEIGHT"
    BMI = "BMI"
    BLOOD_GLUCOSE = "BLOOD_GLUCOSE"


@dataclass(frozen=True)
class ReferenceRange:
    min_normal: float
    max_normal: float
    unit: str


# Standard adult physiological boundaries
REFERENCE_RANGES: dict[str, ReferenceRange] = {
    ObservationType.BLOOD_PRESSURE_SYS: ReferenceRange(min_normal=90.0, max_normal=120.0, unit="mmHg"),
    ObservationType.BLOOD_PRESSURE_DIA: ReferenceRange(min_normal=60.0, max_normal=80.0, unit="mmHg"),
    ObservationType.HEART_RATE: ReferenceRange(min_normal=60.0, max_normal=100.0, unit="bpm"),
    ObservationType.RESPIRATORY_RATE: ReferenceRange(min_normal=12.0, max_normal=20.0, unit="breaths/min"),
    ObservationType.BODY_TEMPERATURE: ReferenceRange(min_normal=36.1, max_normal=37.2, unit="celsius"),
    ObservationType.OXYGEN_SATURATION: ReferenceRange(min_normal=95.0, max_normal=100.0, unit="%"),
    ObservationType.BMI: ReferenceRange(min_normal=18.5, max_normal=24.9, unit="kg/m2"),
    ObservationType.BLOOD_GLUCOSE: ReferenceRange(min_normal=70.0, max_normal=99.0, unit="mg/dL"),  # Fasting
}


def is_observation_abnormal(obs_type: str, value: float) -> bool:
    """
    Evaluates whether a clinical observation value falls outside normal adult reference ranges.
    Returns False if no reference boundary is registered (e.g. raw weight/height).
    """
    ref = REFERENCE_RANGES.get(obs_type)
    if not ref:
        return False
    return value < ref.min_normal or value > ref.max_normal


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """
    Computes Body Mass Index (BMI) = weight (kg) / [height (m)]^2.
    """
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Weight and height must be positive values.")
    height_m = height_cm / 100.0
    return round(weight_kg / (height_m * height_m), 1)
