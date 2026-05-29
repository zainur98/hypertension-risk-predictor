"""Feature encoding shared by model training and prediction."""

from __future__ import annotations

from typing import Any

from .patient_utils import PatientInput, calculate_bmi, parse_patient_input


FEATURE_NAMES = [
    "age",
    "bmi",
    "systolic",
    "diastolic",
    "gender_male",
    "diabetes_yes",
    "smoking_yes",
    "family_history_yes",
    "activity_low",
    "activity_moderate",
    "salt_high",
    "salt_moderate",
    "alcohol_high",
    "alcohol_moderate",
    "stress_high",
    "stress_moderate",
    "sleep_short",
    "sleep_long",
]


def features_from_payload(payload: dict[str, Any]) -> tuple[list[float], PatientInput, float]:
    patient = parse_patient_input(payload)
    bmi = calculate_bmi(
        patient.height,
        patient.height_unit,
        patient.height_inches,
        patient.weight,
        patient.weight_unit,
    )
    return features_from_patient(patient, bmi), patient, bmi


def features_from_patient(patient: PatientInput, bmi: float) -> list[float]:
    return [
        patient.age,
        bmi,
        patient.systolic,
        patient.diastolic,
        equals(patient.gender, "male"),
        yes(patient.diabetes),
        yes(patient.smoking),
        yes(patient.family_history),
        equals(patient.activity, "low"),
        equals(patient.activity, "moderate"),
        equals(patient.salt_intake, "high"),
        equals(patient.salt_intake, "moderate"),
        equals(patient.alcohol, "high"),
        equals(patient.alcohol, "moderate"),
        equals(patient.stress, "high"),
        equals(patient.stress, "moderate"),
        equals(patient.sleep, "short"),
        equals(patient.sleep, "long"),
    ]


def yes(value: str) -> float:
    return 1.0 if value == "yes" else 0.0


def equals(value: str, expected: str) -> float:
    return 1.0 if value == expected else 0.0
