"""Local Ollama explanation helper for model assessment output."""

from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
OLLAMA_PULL_TIMEOUT_SECONDS = int(os.environ.get("OLLAMA_PULL_TIMEOUT_SECONDS", "900"))
OLLAMA_GENERATE_TIMEOUT_SECONDS = int(os.environ.get("OLLAMA_GENERATE_TIMEOUT_SECONDS", "60"))
OLLAMA_ENABLED = os.environ.get("OLLAMA_EXPLANATIONS", "0").strip().lower() in {"1", "true", "yes"}


class OllamaExplanationError(RuntimeError):
    """Raised when a local LLM explanation cannot be generated."""


def build_explanation_with_ollama(assessment: dict[str, Any]) -> str:
    if not OLLAMA_ENABLED:
        raise OllamaExplanationError("Ollama explanations are disabled")

    ensure_model_available(OLLAMA_MODEL)

    prompt = build_prompt(assessment)
    response = ollama_request(
        "POST",
        "/api/generate",
        {
            "model": OLLAMA_MODEL,
            "system": (
                "You write calm patient-facing summaries for a hypertension risk demo. "
                "Use only the supplied facts. Do not diagnose, prescribe, add medical "
                "conditions, or mention that you are an AI."
            ),
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.25,
                "num_predict": 65,
                "top_p": 0.9,
                "repeat_penalty": 1.15,
            },
        },
        timeout=OLLAMA_GENERATE_TIMEOUT_SECONDS,
    )

    explanation = clean_llm_text(str(response.get("response", "")))
    if not explanation:
        raise OllamaExplanationError("Ollama returned an empty explanation")
    explanation = repair_explanation(explanation, assessment)
    validate_explanation(explanation, assessment)

    return explanation


def ensure_model_available(model_name: str) -> None:
    if model_is_available(model_name):
        return

    ollama_request(
        "POST",
        "/api/pull",
        {
            "model": model_name,
            "stream": False,
        },
        timeout=OLLAMA_PULL_TIMEOUT_SECONDS,
    )

    if not model_is_available(model_name):
        raise OllamaExplanationError(f"Ollama model '{model_name}' was not found after pull")


def model_is_available(model_name: str) -> bool:
    response = ollama_request("GET", "/api/tags", timeout=3)
    names = {
        model.get("name")
        for model in response.get("models", [])
        if isinstance(model, dict)
    }
    return model_name in names


def build_prompt(assessment: dict[str, Any]) -> str:
    drivers = [
        driver["factor"]
        for driver in assessment["riskDrivers"][:3]
    ]
    has_drivers = bool(drivers)
    payload = {
        "category": assessment["category"],
        "driverText": format_driver_text(drivers),
        "hasDrivers": has_drivers,
        "strongerRiskArea": get_stronger_risk_area(assessment["breakdown"]),
    }
    if has_drivers:
        instruction = (
            "Write two short sentences, 24 to 38 words total. Mention the category "
            "and these drivers without renaming them. You may vary the sentence shape. "
            "End with a brief reminder to review the result with a clinician, doctor, "
            "or healthcare professional."
        )
    else:
        instruction = (
            "Write two short sentences, 20 to 32 words total. Mention the category "
            "and say no dominant risk driver stands out. Do not say 'submitted values'. "
            "End with a brief reminder to review the result with a clinician, doctor, "
            "or healthcare professional."
        )

    return (
        "Return only the final summary. "
        f"{instruction} Avoid percentages, labels, bullets, headings, diagnosis, "
        "treatment, prescriptions, and action steps. JSON:\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def get_stronger_risk_area(breakdown: list[dict[str, Any]]) -> str:
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
    return "clinical factors" if clinical_score >= lifestyle_score else "lifestyle factors"


def format_driver_text(drivers: list[str]) -> str:
    if not drivers:
        return "the submitted values"
    if len(drivers) == 1:
        return drivers[0]
    if len(drivers) == 2:
        return f"{drivers[0]} and {drivers[1]}"
    return f"{drivers[0]}, {drivers[1]}, and {drivers[2]}"


def clean_llm_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip().strip("\"'")
    cleaned = re.sub(r"^(summary|plain-language summary)\s*[:\-]\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b[Ss]ignificantly\b", "may", cleaned)
    cleaned = re.sub(r"\b[Ss]ignificant\b", "notable", cleaned)
    cleaned = re.sub(r"\s*for personalized advice\.?", ".", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*for personalized guidance\.?", ".", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+immediately\.?", ".", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+to ensure (it is|it's) accurate and appropriate for you\.?", ".", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+to ensure accuracy\.?", ".", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"Please review this result with your healthcare provider\.?",
        "Review this screening result with a clinician.",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"Review this with your healthcare provider\.?",
        "Review this screening result with a clinician.",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = remove_overreaching_sentences(cleaned)
    if len(cleaned) > 360:
        cleaned = cleaned[:357].rstrip() + "..."
    return cleaned


def remove_overreaching_sentences(text: str) -> str:
    blocked_sentence_terms = {
        "optimal health",
        "monitoring or management",
        "manage your",
    }
    sentences = re.findall(r"[^.!?]+[.!?]", text)
    if not sentences:
        return text

    kept = [
        sentence.strip()
        for sentence in sentences
        if not any(term in sentence.lower() for term in blocked_sentence_terms)
    ]
    return " ".join(kept) or text


def repair_explanation(explanation: str, assessment: dict[str, Any]) -> str:
    repaired = explanation.strip()
    lowered = repaired.lower()
    category = assessment["category"]

    if category.lower() not in lowered:
        repaired = f"{category} estimate. {repaired}"
        lowered = repaired.lower()

    if not any(term in lowered for term in {"clinician", "doctor", "healthcare professional", "healthcare provider"}):
        if not repaired.endswith("."):
            repaired = repaired.rstrip(".") + "."
        repaired = f"{repaired} Review this screening result with a clinician."

    return repaired


def validate_explanation(explanation: str, assessment: dict[str, Any]) -> None:
    lowered = explanation.lower()
    blocked_terms = {
        "heart disease",
        "diagnosis",
        "diagnose",
        "treatment",
        "prescription",
        "medication",
        "personalized advice",
        "personalized guidance",
        "immediately",
        "severe",
        "you are obese",
    }

    if any(term in lowered for term in blocked_terms):
        raise OllamaExplanationError("Ollama explanation included blocked medical wording")
    if len(explanation.split()) > 60:
        raise OllamaExplanationError("Ollama explanation was too long")
    if not explanation.endswith("."):
        raise OllamaExplanationError("Ollama explanation appeared incomplete")
    if not any(term in lowered for term in {"clinician", "doctor", "healthcare professional", "healthcare provider"}):
        raise OllamaExplanationError("Ollama explanation missed clinician reminder")
    if assessment["category"].lower() not in lowered:
        raise OllamaExplanationError("Ollama explanation missed risk category")


def ollama_request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    data = None
    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        f"{OLLAMA_BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise OllamaExplanationError(str(exc)) from exc
