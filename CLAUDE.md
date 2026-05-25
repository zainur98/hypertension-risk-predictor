# Hypertension Risk Predictor — Claude Context

## What this project is

A single-page clinical decision support demo that estimates a patient's hypertension risk within 5 years. Not a validated medical tool — trained on synthetic data to prove the engineering flow.

- **Frontend:** `index.html` — vanilla HTML/CSS/JS, zero dependencies, ~2100 lines. The live, model-backed version served by the backend.
- **Backend:** `backend/app.py` — Python standard library HTTP server, no frameworks
- **Model:** `backend/models/model-v1.json` — logistic regression trained on `backend/data/test_patients.csv`
- **POC frontend:** `index-frontend-poc.html` — older version with browser-side rule-based scoring, no backend call

**Important:** Any UI change that applies to `index.html` must also be applied to `index-frontend-poc.html`. Both files share the same layout, components, and JS logic — keep them in sync.

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

## Current language support

English and Georgian (`ka`). Translations live entirely in `index.html` — two objects: `TRANSLATIONS` (UI strings, keyed) and `PHRASE_TRANSLATIONS` (backend-returned phrases, mapped by display string).

## Pending UI improvements (from design review session)

All items resolved.

1. ~~**Loading state on submit**~~ **Done** — button disables and shows a spinner + "Calculating…" during the fetch; restores in a `finally` block on both success and error.

2. ~~**Progress bar label alignment**~~ **Done** — labels now positioned at 0%, 30%, 70%.

3. ~~**Clinical/Lifestyle score cards**~~ **Done** — removed raw scores; split bars carry the story. Cards replaced with Pulse Pressure and Top Risk Driver (see below).

4. ~~**Form layout on large screens**~~ **Done** — 3-column layout (`col-lg-4`) at 992px+, cutting form from 6 rows to 4.

5. ~~**Font-weight values**~~ **Done** — all non-standard values normalized: `820→800`, `760/750/730/720/680→700`, `650→600`.

## Additional fixes done

- Tightened metric card padding after score removal (removed `min-height: 102px`, reduced vertical padding)
- Fixed top-driver-item grid from 3-col to 2-col after score span removal
- Added hover lift to `.metric-card` and `.info-card` to match `.result-card` behaviour
- Removed orphaned `.driver-score` CSS rule
- Replaced Clinical Risk Load and Lifestyle Risk Load metric cards with **Pulse Pressure** (systolic − diastolic, with Normal/Elevated/Wide status) and **Top Risk Driver** (highest-scoring group from the breakdown)
- Fixed breakdown chart normalization: bars now show each group's share of total attributed risk (sum-based) instead of being pinned relative to the max scorer
- Renamed "Family history" form label to "Family history of hypertension"
- Added min/max input guard rails: age 18–100, height 100–250 cm / 3–8 ft, weight 20–300 kg / 44–660 lbs; HTML attributes and JS validation kept in sync; unit-switch handlers update attributes dynamically

## Architecture notes

- The `LOCALIZED_SELECTORS` array in `index.html` applies Georgian translations via nth-child CSS selectors — brittle if HTML structure changes.
- The Georgian plain-language summary (`getLocalizedExplanation`) is a hard-coded template in JS rather than going through the translation system — inconsistent with how other strings work.
- `APP_CONFIG.backendUrl` switches between absolute and relative URL based on `window.location.protocol`, so the file can be opened directly or served.
