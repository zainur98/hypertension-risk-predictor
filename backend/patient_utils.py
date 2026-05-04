"""Shared patient input parsing and clinical display helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PatientInput:
    age: float
    height: float
    height_unit: str
    weight: float
    weight_unit: str
    diabetes: str
    smoking: str
    systolic: float
    diastolic: float
    family_history: str
    activity: str
    salt_intake: str
    alcohol: str
    stress: str
    sleep: str
    height_inches: float = 0


def parse_patient_input(payload: dict[str, Any]) -> PatientInput:
    patient = PatientInput(
        age=to_float(payload.get("age"), "age"),
        height=to_float(payload.get("height"), "height"),
        height_inches=to_float(payload.get("heightInches", payload.get("height_inches", 0)), "heightInches"),
        height_unit=str(payload.get("heightUnit", payload.get("height_unit", "cm"))),
        weight=to_float(payload.get("weight"), "weight"),
        weight_unit=str(payload.get("weightUnit", payload.get("weight_unit", "kg"))),
        diabetes=normalize_choice(payload.get("diabetes"), "diabetes", {"yes", "no"}),
        smoking=normalize_choice(payload.get("smoking"), "smoking", {"yes", "no"}),
        systolic=to_float(payload.get("systolic"), "systolic"),
        diastolic=to_float(payload.get("diastolic"), "diastolic"),
        family_history=normalize_choice(
            payload.get("familyHistory", payload.get("family_history")),
            "familyHistory",
            {"yes", "no"},
        ),
        activity=normalize_choice(payload.get("activity"), "activity", {"high", "moderate", "low"}),
        salt_intake=normalize_choice(
            payload.get("saltIntake", payload.get("salt_intake")),
            "saltIntake",
            {"low", "moderate", "high"},
        ),
        alcohol=normalize_choice(payload.get("alcohol"), "alcohol", {"none", "moderate", "high"}),
        stress=normalize_choice(payload.get("stress"), "stress", {"low", "moderate", "high"}),
        sleep=normalize_choice(payload.get("sleep"), "sleep", {"normal", "short", "long"}),
    )

    validate_patient_input(patient)
    return patient


def validate_patient_input(patient: PatientInput) -> None:
    if patient.age <= 0 or patient.age > 120:
        raise ValueError("age must be between 1 and 120")
    if patient.height <= 0:
        raise ValueError("height must be greater than 0")
    if patient.height_unit not in {"cm", "ft-in"}:
        raise ValueError("heightUnit must be either 'cm' or 'ft-in'")
    if patient.height_inches < 0 or patient.height_inches >= 12:
        raise ValueError("heightInches must be between 0 and 11.9")
    if patient.weight <= 0:
        raise ValueError("weight must be greater than 0")
    if patient.weight_unit not in {"kg", "lbs"}:
        raise ValueError("weightUnit must be either 'kg' or 'lbs'")
    if patient.systolic < 70 or patient.systolic > 260:
        raise ValueError("systolic must be between 70 and 260")
    if patient.diastolic < 40 or patient.diastolic > 160:
        raise ValueError("diastolic must be between 40 and 160")
    if patient.systolic <= patient.diastolic:
        raise ValueError("systolic must be greater than diastolic")


def calculate_bmi(
    height: float,
    height_unit: str,
    height_inches: float,
    weight: float,
    weight_unit: str,
) -> float:
    total_inches = (height * 12) + height_inches
    height_meters = total_inches * 0.0254 if height_unit == "ft-in" else height / 100
    weight_kg = weight * 0.45359237 if weight_unit == "lbs" else weight
    return weight_kg / (height_meters * height_meters)


def get_bmi_status(bmi: float) -> str:
    if bmi >= 30:
        return "Obesity range"
    if bmi >= 25:
        return "Overweight range"
    if bmi < 18.5:
        return "Below normal range"
    return "Normal range"


def get_blood_pressure_status(systolic: float, diastolic: float) -> str:
    if systolic >= 180 or diastolic >= 120:
        return "Hypertensive crisis range"
    if systolic >= 140 or diastolic >= 90:
        return "Stage 2 hypertension range"
    if systolic >= 130 or diastolic >= 80:
        return "Stage 1 hypertension range"
    if systolic >= 120:
        return "Elevated blood pressure range"
    return "Normal blood pressure range"


def get_risk_category(risk: int) -> str:
    if risk < 30:
        return "Low Risk"
    if risk <= 70:
        return "Moderate Risk"
    return "High Risk"


def to_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc


def normalize_choice(value: Any, field_name: str, allowed: set[str]) -> str:
    normalized = str(value).strip().lower()
    if normalized not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {allowed_values}")
    return normalized
