# Hypertension Risk Assessment Tool

A single-page clinical decision support demo that estimates hypertension risk within 5 years using a logistic regression model. The project uses a vanilla HTML/CSS/JS frontend and a Python standard-library backend with no external dependencies.

This is a prototype intended to demonstrate how an ML-powered hypertension risk prediction system might behave in a clinical setting. It is not a validated medical model.

## Features

- Responsive medical-style dashboard interface
- Logistic regression model trained on 200 synthetic patients
- Automatic BMI calculation from height and weight
- Blood pressure stage classification
- Risk percentage and category output (Low / Moderate / High)
- Pulse pressure calculation with clinical status
- Individual risk driver bar chart (top 6 features)
- Group-level radar chart (Age, Blood pressure, BMI, Medical history, Lifestyle)
- BMI range and blood pressure stage infographics
- Recommendations grouped by Lifestyle, Medical, and Monitoring
- Input validation with unit-aware min/max guard rails
- Bilingual interface: English and Georgian

## Inputs

| Field | Values |
| --- | --- |
| Age | 18–100 |
| Height | cm or feet/inches |
| Weight | kg or lbs |
| Gender | Male / Female |
| Diabetes | Yes / No |
| Smoking | Yes / No |
| Systolic / Diastolic BP | mmHg |
| Family history of hypertension | Yes / No |
| Physical activity | High / Moderate / Low |
| Salt intake | Low / Moderate / High |
| Alcohol intake | None / Moderate / High |
| Stress level | Low / Moderate / High |
| Average sleep | Normal / Short / Long |

BMI is calculated by the backend from height and weight.

## Risk Model

The active app uses `model-v1`, a logistic regression model trained on `backend/data/test_patients.csv` (200 synthetic rows). It predicts the synthetic target `hypertension_within_5_years` and returns a risk percentage, category, feature-level contribution breakdown, and recommendations.

Model features match the 5 core EHR variables from the associated research proposal (age, sex, BMI, smoking, diabetes) plus blood pressure and extended lifestyle predictors.

`index-frontend-poc.html` preserves a browser-side rule-based version for offline use.

## Risk Categories

| Score | Category |
| --- | --- |
| Less than 30% | Low Risk |
| 30% to 70% | Moderate Risk |
| Greater than 70% | High Risk |

## How to Run

```bash
python -m backend.app
```

On Windows without `python` in PATH:

```powershell
py -3.9 -m backend.app
```

Opens at `http://127.0.0.1:8000/`. The backend serves `index.html` and handles all API calls.

## Training the Model

```bash
python -m backend.model_train
```

Reads `backend/data/test_patients.csv`, writes `backend/models/model-v1.json`.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Check API status |
| GET | `/api/test-patients` | Return synthetic patient rows |
| POST | `/api/risk/estimate` | Estimate hypertension risk |

Example request:

```json
{
  "age": 57,
  "height": 5,
  "heightUnit": "ft-in",
  "heightInches": 4,
  "weight": 192,
  "weightUnit": "lbs",
  "systolic": 138,
  "diastolic": 86,
  "gender": "female",
  "diabetes": "yes",
  "smoking": "no",
  "familyHistory": "yes",
  "activity": "low",
  "saltIntake": "high",
  "alcohol": "none",
  "stress": "high",
  "sleep": "short"
}
```

Example response (abbreviated):

```json
{
  "riskPercent": 95,
  "category": "High Risk",
  "modelVersion": "model-v1",
  "calculated": {
    "bmi": 33.0,
    "bmiStatus": "Obesity range",
    "bloodPressure": "138/86",
    "bloodPressureStage": "Stage 1 hypertension range"
  },
  "breakdown": [
    { "label": "Age", "score": 18 },
    { "label": "Blood pressure", "score": 14 },
    { "label": "BMI", "score": 20 },
    { "label": "Medical history", "score": 22 },
    { "label": "Lifestyle", "score": 21 }
  ],
  "riskDrivers": [
    { "factor": "Diabetes", "riskContribution": 18 },
    { "factor": "Low physical activity", "riskContribution": 16 }
  ],
  "recommendations": [
    "Discuss blood pressure targets with a clinician",
    "Build toward regular moderate activity"
  ]
}
```

## Project Structure

```text
hypertension-risk-predictor/
├── backend/
│   ├── app.py
│   ├── llm_explain.py
│   ├── model_features.py
│   ├── model_predict.py
│   ├── model_train.py
│   ├── patient_utils.py
│   ├── resources.py
│   ├── models/
│   │   └── model-v1.json
│   └── data/
│       └── test_patients.csv
├── index.html
├── index-frontend-poc.html
└── README.md
```

## Disclaimer

This tool is for educational purposes only and not a substitute for professional medical advice, diagnosis, or treatment. The model is trained on synthetic data and should not be used for real clinical decisions.
