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
OLLAMA_ENABLED = os.environ.get("OLLAMA_EXPLANATIONS", "1").strip().lower() not in {"0", "false", "no"}


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
                "You explain a hypertension risk demo result in plain language. "
                "You do not diagnose, prescribe, change the risk score, or add facts "
                "not present in the provided JSON."
            ),
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 90,
                "top_p": 0.9,
            },
        },
        timeout=OLLAMA_GENERATE_TIMEOUT_SECONDS,
    )

    explanation = clean_llm_text(str(response.get("response", "")))
    if not explanation:
        raise OllamaExplanationError("Ollama returned an empty explanation")

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
    payload = {
        "riskPercent": assessment["riskPercent"],
        "category": assessment["category"],
        "calculated": assessment["calculated"],
        "riskDrivers": assessment["riskDrivers"],
        "breakdown": assessment["breakdown"],
        "recommendations": assessment["recommendations"][:3],
        "disclaimer": assessment["disclaimer"],
    }
    return (
        "Write one concise paragraph, 35 to 55 words, for a patient reading this "
        "hypertension risk demo. Mention the risk category, the main drivers, and "
        "that it is not medical advice. Use only this JSON:\n"
        f"{json.dumps(payload, ensure_ascii=True)}"
    )


def clean_llm_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip().strip("\"'")
    if len(cleaned) > 600:
        cleaned = cleaned[:597].rstrip() + "..."
    return cleaned


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
