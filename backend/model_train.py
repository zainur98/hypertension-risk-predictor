"""Train a small logistic regression model from synthetic test data.

This is a dependency-free training script for the POC. The resulting model is
for engineering demonstration only and is not clinically meaningful.

Run from the repository root:
    python -m backend.model_train
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from .model_features import FEATURE_NAMES, features_from_payload


DATA_PATH = Path(__file__).parent / "data" / "test_patients.csv"
MODEL_PATH = Path(__file__).parent / "models" / "model-v1.json"


def main() -> None:
    rows = load_training_rows(DATA_PATH)
    feature_matrix = [row["features"] for row in rows]
    labels = [row["label"] for row in rows]
    means, scales = fit_scaler(feature_matrix)
    scaled_features = [scale_features(features, means, scales) for features in feature_matrix]
    weights, bias = train_logistic_regression(scaled_features, labels)
    metrics = evaluate(scaled_features, labels, weights, bias)

    model = {
        "modelVersion": "model-v1",
        "modelType": "standard-library-logistic-regression",
        "trainingData": "backend/data/test_patients.csv",
        "target": "hypertension_within_5_years",
        "disclaimer": "Synthetic-data demo model. Not clinically validated.",
        "featureNames": FEATURE_NAMES,
        "means": means,
        "scales": scales,
        "weights": weights,
        "bias": bias,
        "metrics": metrics,
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(model, indent=2), encoding="utf-8")

    print(f"Saved {model['modelVersion']} to {MODEL_PATH}")
    print(f"Training rows: {len(rows)}")
    print(f"Training accuracy: {metrics['accuracy']:.2f}")


def load_training_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        rows = []
        for row in csv.DictReader(csv_file):
            payload = csv_row_to_payload(row)
            features, _, _ = features_from_payload(payload)
            rows.append({
                "features": features,
                "label": parse_bool(row["hypertension_within_5_years"]),
            })
        return rows


def csv_row_to_payload(row: dict[str, str]) -> dict:
    return {
        "age": row["age"],
        "height": row["height"],
        "heightUnit": row["height_unit"],
        "heightInches": row["height_inches"],
        "weight": row["weight"],
        "weightUnit": row["weight_unit"],
        "systolic": row["systolic"],
        "diastolic": row["diastolic"],
        "diabetes": row["diabetes"],
        "smoking": row["smoking"],
        "familyHistory": row["family_history"],
        "activity": row["activity"],
        "saltIntake": row["salt_intake"],
        "alcohol": row["alcohol"],
        "stress": row["stress"],
        "sleep": row["sleep"],
    }


def fit_scaler(feature_matrix: list[list[float]]) -> tuple[list[float], list[float]]:
    columns = list(zip(*feature_matrix))
    means = [sum(column) / len(column) for column in columns]
    scales = []

    for index, column in enumerate(columns):
        variance = sum((value - means[index]) ** 2 for value in column) / len(column)
        scale = math.sqrt(variance)
        scales.append(scale if scale > 0 else 1.0)

    return means, scales


def scale_features(features: list[float], means: list[float], scales: list[float]) -> list[float]:
    return [
        (value - means[index]) / scales[index]
        for index, value in enumerate(features)
    ]


def train_logistic_regression(
    feature_matrix: list[list[float]],
    labels: list[int],
    epochs: int = 2200,
    learning_rate: float = 0.08,
    l2_penalty: float = 0.02,
) -> tuple[list[float], float]:
    feature_count = len(feature_matrix[0])
    weights = [0.0] * feature_count
    bias = 0.0
    row_count = len(feature_matrix)

    for _ in range(epochs):
        weight_gradients = [0.0] * feature_count
        bias_gradient = 0.0

        for features, label in zip(feature_matrix, labels):
            prediction = sigmoid(dot(weights, features) + bias)
            error = prediction - label
            bias_gradient += error

            for index, value in enumerate(features):
                weight_gradients[index] += error * value

        for index in range(feature_count):
            regularization = l2_penalty * weights[index]
            weights[index] -= learning_rate * ((weight_gradients[index] / row_count) + regularization)

        bias -= learning_rate * (bias_gradient / row_count)

    return weights, bias


def evaluate(
    feature_matrix: list[list[float]],
    labels: list[int],
    weights: list[float],
    bias: float,
) -> dict[str, float]:
    probabilities = [sigmoid(dot(weights, features) + bias) for features in feature_matrix]
    predictions = [1 if probability >= 0.5 else 0 for probability in probabilities]
    correct = sum(1 for prediction, label in zip(predictions, labels) if prediction == label)
    return {
        "accuracy": correct / len(labels),
        "positiveRate": sum(labels) / len(labels),
    }


def parse_bool(value: str) -> int:
    return 1 if value.strip().lower() == "true" else 0


def dot(weights: list[float], features: list[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, features))


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)

    z = math.exp(value)
    return z / (1 + z)


if __name__ == "__main__":
    main()
