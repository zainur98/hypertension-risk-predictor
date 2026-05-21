# Hypertension Risk Predictor — Claude Context

## What this project is

A single-page clinical decision support demo that estimates a patient's hypertension risk within 5 years. Not a validated medical tool — trained on synthetic data to prove the engineering flow.

- **Frontend:** `index.html` — vanilla HTML/CSS/JS, zero dependencies, ~2100 lines
- **Backend:** `backend/app.py` — Python standard library HTTP server, no frameworks
- **Model:** `backend/models/model-v1.json` — logistic regression trained on `backend/data/test_patients.csv`
- **POC frontend:** `index-frontend-poc.html` — older version with browser-side rule-based scoring

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

These were identified and agreed on — none implemented yet:

1. **Loading state on submit** — the Calculate Risk button gives no feedback while the backend responds. Should disable + show a spinner during the fetch. Highest priority UX fix.

2. ~~**Progress bar label alignment** — "Low / Moderate / High" labels are evenly spaced, implying thresholds at 33%/67%. Actual thresholds are 30%/70%. Labels or tick marks should sit at the correct positions.~~ **Done** — labels now positioned at 0%, 30%, 70% in both `index.html` and `index-frontend-poc.html`.

3. ~~**Clinical/Lifestyle score cards** — the metric cards show raw scores (`+5`) with no maximum, which is meaningless to a user. Either show as `5 / 10` or remove raw numbers and let the split bars carry the story.~~ **Done** — removed raw scores from both `index.html` and `index-frontend-poc.html`; the split bars carry the story. Also removed `+N` scores from the breakdown chart and top risk drivers list for the same reason.

4. **Form layout on large screens** — currently 2-column (6 rows). At 1040px wide there's room for 3 columns, which would cut form height by ~a third.

5. **Font-weight values** — the CSS uses non-standard values (`820`, `760`, `650` etc.) that only work on variable fonts. System UI fonts snap to `700`/`400`. Standardize to `400 / 500 / 600 / 700`.

## Additional fixes done

- Tightened metric card padding after score removal (removed `min-height: 102px`, reduced vertical padding)
- Fixed top-driver-item grid from 3-col to 2-col after score span removal
- Added hover lift to `.metric-card` and `.info-card` to match `.result-card` behaviour
- Removed orphaned `.driver-score` CSS rule

## Architecture notes

- The `LOCALIZED_SELECTORS` array in `index.html` applies Georgian translations via nth-child CSS selectors — brittle if HTML structure changes.
- The Georgian plain-language summary (`getLocalizedExplanation`) is a hard-coded template in JS rather than going through the translation system — inconsistent with how other strings work.
- `APP_CONFIG.backendUrl` switches between absolute and relative URL based on `window.location.protocol`, so the file can be opened directly or served.
