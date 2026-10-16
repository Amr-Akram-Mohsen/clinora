"""
tests/test_clinical_ranges.py

Unit tests for domain clinical physiological boundaries, abnormal observation detection,
and BMI calculation rules. Pure domain logic tests (no database required).
"""

import pytest

from domain.clinical.ranges import (
    ObservationType,
    calculate_bmi,
    is_observation_abnormal,
)


def test_blood_pressure_abnormality():
    # Normal BP: Sys 90-120, Dia 60-80
    assert not is_observation_abnormal(ObservationType.BLOOD_PRESSURE_SYS, 115.0)
    assert not is_observation_abnormal(ObservationType.BLOOD_PRESSURE_DIA, 75.0)

    # Hypertensive / Elevated
    assert is_observation_abnormal(ObservationType.BLOOD_PRESSURE_SYS, 145.0)
    assert is_observation_abnormal(ObservationType.BLOOD_PRESSURE_DIA, 95.0)

    # Hypotensive
    assert is_observation_abnormal(ObservationType.BLOOD_PRESSURE_SYS, 80.0)
    assert is_observation_abnormal(ObservationType.BLOOD_PRESSURE_DIA, 50.0)


def test_heart_rate_abnormality():
    # Normal: 60 - 100 bpm
    assert not is_observation_abnormal(ObservationType.HEART_RATE, 72.0)
    assert not is_observation_abnormal(ObservationType.HEART_RATE, 60.0)
    assert not is_observation_abnormal(ObservationType.HEART_RATE, 100.0)

    # Bradycardia (<60) & Tachycardia (>100)
    assert is_observation_abnormal(ObservationType.HEART_RATE, 48.0)
    assert is_observation_abnormal(ObservationType.HEART_RATE, 125.0)


def test_body_temperature_abnormality():
    # Normal: 36.1 - 37.2 °C
    assert not is_observation_abnormal(ObservationType.BODY_TEMPERATURE, 36.6)
    # Fever
    assert is_observation_abnormal(ObservationType.BODY_TEMPERATURE, 38.9)
    # Hypothermia
    assert is_observation_abnormal(ObservationType.BODY_TEMPERATURE, 35.0)


def test_oxygen_saturation_abnormality():
    # Normal: 95 - 100 %
    assert not is_observation_abnormal(ObservationType.OXYGEN_SATURATION, 98.0)
    # Hypoxemia
    assert is_observation_abnormal(ObservationType.OXYGEN_SATURATION, 89.0)


def test_calculate_bmi():
    # 70 kg, 175 cm -> 70 / (1.75 * 1.75) = 22.86 -> 22.9
    bmi = calculate_bmi(weight_kg=70.0, height_cm=175.0)
    assert bmi == 22.9
    assert not is_observation_abnormal(ObservationType.BMI, bmi)

    # Obese: 110 kg, 170 cm -> 110 / 2.89 = 38.1
    obese_bmi = calculate_bmi(weight_kg=110.0, height_cm=170.0)
    assert obese_bmi == 38.1
    assert is_observation_abnormal(ObservationType.BMI, obese_bmi)


def test_calculate_bmi_invalid_inputs():
    with pytest.raises(ValueError, match="Weight and height must be positive values."):
        calculate_bmi(weight_kg=0, height_cm=170)

    with pytest.raises(ValueError, match="Weight and height must be positive values."):
        calculate_bmi(weight_kg=70, height_cm=-10)
