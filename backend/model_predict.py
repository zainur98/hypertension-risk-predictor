"""Prediction helpers for the synthetic-data logistic regression model."""

from __future__ import annotations

import json
import math
from typing import Any

from .llm_explain import OLLAMA_MODEL, build_explanation_with_ollama
from .model_features import FEATURE_NAMES, features_from_payload
from .patient_utils import (
    get_blood_pressure_status,
    get_bmi_status,
    get_risk_category,
)
from .resources import resource_path


MODEL_PATH = resource_path("backend/models/model-v1.json")


def assess_with_model(payload: dict[str, Any]) -> dict[str, Any]:
    model = load_model()
    features, patient, bmi = features_from_payload(payload)
    scaled_features = scale_features(features, model["means"], model["scales"])
    probability = sigmoid(dot(model["weights"], scaled_features) + model["bias"])
    risk = min(round(probability * 100), 100)
    feature_impacts = get_feature_impacts(model, scaled_features, risk)
    breakdown = get_group_breakdown(feature_impacts)
    clinical_total = sum(item["score"] for item in breakdown if item["label"] in {"Age", "Blood pressure", "Medical history"})
    lifestyle_total = sum(item["score"] for item in breakdown if item["label"] in {"BMI", "Lifestyle"})
    fallback_explanation = get_plain_language_explanation(risk, feature_impacts, breakdown)
    assessment = {
        "riskPercent": risk,
        "category": get_risk_category(risk),
        "modelVersion": model["modelVersion"],
        "calculated": {
            "bmi": round(bmi, 1),
            "bmiStatus": get_bmi_status(bmi),
            "bloodPressure": f"{round(patient.systolic)}/{round(patient.diastolic)}",
            "bloodPressureStage": get_blood_pressure_status(patient.systolic, patient.diastolic),
            "clinicalRiskLoad": clinical_total,
            "lifestyleRiskLoad": lifestyle_total,
            "modelProbability": round(probability, 4),
        },
        "breakdown": breakdown,
        "riskDrivers": feature_impacts[:3],
        "factors": [impact["factor"] for impact in feature_impacts[:5]] or ["No major model drivers detected"],
        "recommendations": get_recommendations(feature_impacts),
        "disclaimer": "Synthetic-data demo model. Not a substitute for professional medical advice.",
    }
    explanation, source = get_assessment_explanation(assessment, fallback_explanation)
    assessment["explanation"] = explanation
    assessment["explanationSource"] = source
    assessment["explanationModel"] = OLLAMA_MODEL if source == "ollama" else "deterministic-fallback"

    return assessment


def load_model() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise ValueError("model-v1 is not trained yet. Run: python -m backend.model_train")

    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def scale_features(features: list[float], means: list[float], scales: list[float]) -> list[float]:
    return [
        (value - means[index]) / scales[index]
        for index, value in enumerate(features)
    ]


def get_feature_impacts(model: dict[str, Any], scaled_features: list[float], risk: int) -> list[dict[str, Any]]:
    raw_impacts = []

    for name, weight, value in zip(FEATURE_NAMES, model["weights"], scaled_features):
        contribution = weight * value
        if contribution > 0:
            raw_impacts.append({
                "feature": name,
                "factor": format_feature_name(name),
                "rawContribution": contribution,
            })

    total = sum(item["rawContribution"] for item in raw_impacts) or 1
    impacts = []

    for item in raw_impacts:
        impacts.append({
            "feature": item["feature"],
            "factor": item["factor"],
            "riskContribution": max(1, round(item["rawContribution"] / total * risk)),
        })

    impacts.sort(key=lambda item: item["riskContribution"], reverse=True)
    return impacts


def get_group_breakdown(feature_impacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = {
        "Age": 0,
        "Blood pressure": 0,
        "BMI": 0,
        "Medical history": 0,
        "Lifestyle": 0,
    }

    for impact in feature_impacts:
        groups[group_for_feature(impact["feature"])] += impact["riskContribution"]

    return [
        {"label": label, "score": score}
        for label, score in groups.items()
    ]


def group_for_feature(feature: str) -> str:
    if feature == "age":
        return "Age"
    if feature in {"systolic", "diastolic"}:
        return "Blood pressure"
    if feature == "bmi":
        return "BMI"
    if feature in {"diabetes_yes", "family_history_yes"}:
        return "Medical history"
    return "Lifestyle"


def get_recommendations(feature_impacts: list[dict[str, Any]]) -> list[str]:
    recommendations = []
    recommendation_map = {
        "bmi": "Review weight, nutrition, and activity goals",
        "systolic": "Confirm blood pressure readings with repeated measurements",
        "diastolic": "Confirm blood pressure readings with repeated measurements",
        "diabetes_yes": "Discuss blood pressure targets with a clinician",
        "smoking_yes": "Smoking cessation support is strongly recommended",
        "activity_low": "Build toward regular moderate activity",
        "salt_high": "Reduce sodium-heavy and highly processed foods",
        "alcohol_high": "Consider reducing alcohol intake",
        "stress_high": "Add stress-management habits and recovery time",
        "sleep_short": "Aim for a consistent 7 to 9 hours of sleep when possible",
    }

    for impact in feature_impacts:
        recommendation = recommendation_map.get(impact["feature"])
        if recommendation and recommendation not in recommendations:
            recommendations.append(recommendation)

    return recommendations or ["Maintain healthy lifestyle habits and routine checkups"]


def get_plain_language_explanation(
    risk: int,
    feature_impacts: list[dict[str, Any]],
    breakdown: list[dict[str, Any]],
) -> str:
    """Summarize the structured model output without changing the risk score."""
    category = get_risk_category(risk).lower()
    drivers = [impact["factor"] for impact in feature_impacts[:3]]
    driver_text = format_driver_text(drivers)
    clinical_score = sum(
        item["score"]
        for item in breakdown
        if item["label"] in {"Age", "Blood pressure", "Medical history"}
    )
    lifestyle_score = sum(
        item["score"]
        for item in breakdown
        if item["label"] in {"BMI", "Lifestyle"}
    )
    stronger_area = "clinical factors" if clinical_score >= lifestyle_score else "lifestyle factors"

    if risk < 10:
        return (
            "Low risk estimate, with no major risk driver standing out in this screening. "
            "Keep routine checkups in mind and review any health concerns with a clinician."
        )

    if risk < 30:
        return (
            f"Low risk estimate, with {driver_text} contributing most in this screening. "
            "Keep routine checkups in mind and review any health concerns with a clinician."
        )

    if risk <= 70 and driver_text:
        return (
            f"Moderate risk estimate, with {driver_text} as the clearest contributors. "
            f"The pattern leans toward {stronger_area}; review this screening result "
            "with a clinician."
        )

    if driver_text:
        return (
            f"{category.capitalize()} estimate, with {driver_text} as the clearest "
            f"contributors. The pattern leans toward {stronger_area}; review this "
            "screening result with a clinician."
        )

    return (
        f"{category.capitalize()} estimate, with no single dominant driver in the "
        "submitted values. Keep monitoring routine readings and use this as a screening "
        "aid, not medical advice."
    )


def get_assessment_explanation(assessment: dict[str, Any], fallback: str) -> tuple[str, str]:
    try:
        return build_explanation_with_ollama(assessment), "ollama"
    except Exception as exc:
        print(f"Ollama explanation unavailable; using fallback: {exc}")
        return fallback, "fallback"


def format_driver_text(drivers: list[str]) -> str:
    if not drivers:
        return ""
    if len(drivers) == 1:
        return drivers[0]
    if len(drivers) == 2:
        return f"{drivers[0]} and {drivers[1]}"
    return f"{drivers[0]}, {drivers[1]}, and {drivers[2]}"


def format_feature_name(name: str) -> str:
    label_map = {
        "bmi": "BMI",
        "diabetes_yes": "Diabetes",
        "smoking_yes": "Smoking",
        "family_history_yes": "Family history",
        "activity_low": "Low physical activity",
        "activity_moderate": "Moderate physical activity",
        "salt_high": "High salt intake",
        "salt_moderate": "Moderate salt intake",
        "alcohol_high": "High alcohol intake",
        "alcohol_moderate": "Moderate alcohol intake",
        "stress_high": "High stress",
        "stress_moderate": "Moderate stress",
        "sleep_short": "Short sleep",
        "sleep_long": "Long sleep",
    }
    if name in label_map:
        return label_map[name]

    return name.replace("_", " ").title()


def dot(weights: list[float], features: list[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, features))


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)

    z = math.exp(value)
    return z / (1 + z)
