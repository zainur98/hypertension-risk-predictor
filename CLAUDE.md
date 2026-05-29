# Hypertension Risk Predictor — Claude Context

## What this project is

A single-page clinical decision support demo that estimates a patient's hypertension risk within 5 years. Not a validated medical tool — trained on synthetic data to prove the engineering flow.

- **Frontend:** `index.html` — vanilla HTML/CSS/JS, zero dependencies. The live, model-backed version served by the backend.
- **Backend:** `backend/app.py` — Python standard library HTTP server, no frameworks
- **Model:** `backend/models/model-v1.json` — logistic regression trained on `backend/data/test_patients.csv` (200 synthetic rows)
- **POC frontend:** `index-frontend-poc.html` — older version with browser-side rule-based scoring, no backend call. Has an **"Auto fill" button** (top-right of the Patient details heading) that pre-populates the form with moderate-risk test values for quick testing — this is POC-only and should not be added to `index.html`.

**Important:** Any UI change that applies to `index.html` must also be applied to `index-frontend-poc.html`. Both files share the same layout, components, and JS logic — keep them in sync. Exception: POC-only dev helpers (like Auto fill) stay in `index-frontend-poc.html` only.

## How to run

```powershell
python -m backend.app
# or on Windows without python in PATH:
py -3.9 -m backend.app
```

Opens at `http://127.0.0.1:8000`. The backend serves `index.html` and handles all API calls.

Key API endpoint: `POST /api/risk/estimate`

## Retrain the model

```powershell
python -m backend.model_train
```

Writes to `backend/models/model-v1.json`.

## Model features

The logistic regression uses 18 features:

`age`, `bmi`, `systolic`, `diastolic`, `gender_male`, `diabetes_yes`, `smoking_yes`, `family_history_yes`, `activity_low`, `activity_moderate`, `salt_high`, `salt_moderate`, `alcohol_high`, `alcohol_moderate`, `stress_high`, `stress_moderate`, `sleep_short`, `sleep_long`

These match the 5 core EHR variables from the research proposal (age, sex, BMI, smoking, diabetes) plus blood pressure and extended lifestyle predictors.

## LLM integration

`backend/llm_explain.py` contains a local Ollama explanation helper but it is **disabled** (`OLLAMA_EXPLANATIONS` defaults to `"0"`). The backend does not call it during normal operation. The file is kept for potential future use — re-enable by importing `build_explanation_with_ollama` in `model_predict.py` and setting `OLLAMA_EXPLANATIONS=1`.

## Current language support

English and Georgian (`ka`). Translations live entirely in `index.html` — two objects: `TRANSLATIONS` (UI strings, keyed) and `PHRASE_TRANSLATIONS` (backend-returned phrases, mapped by display string).

## Completed UI work

- Loading state on submit — button disables and shows a spinner + "Calculating…" during fetch
- Progress bar labels positioned at 0%, 30%, 70%
- Replaced Clinical/Lifestyle score cards with **Pulse Pressure** and **Top Risk Driver** metric cards
- Form stays at 2 columns (`col-md-6`) at all breakpoints — 3-column was too crowded, do not re-add
- Font-weight values normalized: `820→800`, `760/750/730/720/680→700`, `650→600`
- Tightened metric card padding; fixed top-driver-item grid to 2-col
- Added hover lift to `.metric-card` and `.info-card`
- Removed orphaned `.driver-score` CSS rule
- Fixed breakdown chart normalization to sum-based shares
- Renamed "Family history" label to "Family history of hypertension"
- Added min/max input guard rails with dynamic unit-switch attribute updates
- Added SVG radar/spider chart for group-level risk breakdown
- Replaced Contributing Factors card and group bar chart with individual feature bar chart (`riskDriversChart`) + radar chart side by side
- Recommendations redesigned: full-width, grouped into Lifestyle / Medical / Monitoring with colour-coded left borders
- Added **Gender** field to the form (Male/Female); wired through model pipeline; model retrained on 200-row synthetic dataset

## Results section layout

The results area uses a two-column Bootstrap grid at `lg` (992px+):
- `col-12 col-lg-5` — Risk Drivers bar chart (narrow left)
- `col-12 col-lg-7` — Radar chart / Risk profile (wide right)
- `col-12` — Recommendations (full width)

The form fields use `col-12 col-md-6` (2 columns at `md`+). Do not re-add `col-lg-4` to form fields.

## Architecture notes

- The `LOCALIZED_SELECTORS` array in `index.html` applies Georgian translations via CSS selectors — brittle if HTML structure changes. Update indices carefully when adding or removing form fields or result cards.
- `APP_CONFIG.backendUrl` switches between absolute and relative URL based on `window.location.protocol`, so the file can be opened directly or served.
- `backend/model_predict.py` sends all feature impacts (`riskDrivers`) to the frontend, not just the top 3. The frontend slices to top 6 for display.
