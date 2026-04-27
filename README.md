# Hypertension Risk Assessment Tool

A single-page clinical decision support demo that estimates hypertension risk using simple rule-based logic. The project is built with pure HTML, CSS, and vanilla JavaScript, with Bootstrap loaded through a CDN.

This is a prototype UI intended to simulate how a future ML-powered hypertension risk prediction system might behave.

## Features

- Responsive medical-style interface
- No backend or database required
- Rule-based hypertension risk scoring
- Dynamic result display without page reload
- Risk percentage and category output
- Color-coded risk categories:
  - Low Risk
  - Moderate Risk
  - High Risk
- Contributing factor explanation
- Personalized recommendation list
- Input validation
- Smooth scroll and result highlighting
- Progress bar visualization

## Inputs

The tool asks for:

- Age
- Height, entered in centimeters or feet and inches
- Weight, entered in kilograms or pounds
- Diabetes status
- Smoking status

BMI is calculated automatically from height and weight before applying the risk rules.

## Risk Logic

The risk score starts at `0` and increases based on the following rules:

| Factor | Rule | Score |
| --- | --- | --- |
| Age | Age > 50 | +25 |
| Age | Age > 40 | +15 |
| Calculated BMI | BMI > 30 | +25 |
| Calculated BMI | BMI > 25 | +15 |
| Diabetes | Yes | +20 |
| Smoking | Yes | +15 |

The final score is capped at `100%`.

## Risk Categories

| Score | Category |
| --- | --- |
| Less than 30% | Low Risk |
| 30% to 70% | Moderate Risk |
| Greater than 70% | High Risk |

## Recommendations

The tool displays recommendations based on the user's inputs:

- Calculated BMI greater than 25: `Consider weight reduction`
- Smoking status is Yes: `Smoking cessation advised`
- Age greater than 40: `Regular blood pressure monitoring recommended`

## How to Run

Clone the repository and open `index.html` in any modern web browser.

```bash
git clone <repository-url>
cd hypertension-risk-predictor
```

Then open:

```text
index.html
```

No installation, build step, or server is required.

## Project Structure

```text
hypertension-risk-predictor/
├── index.html
└── README.md
```

## Technologies Used

- HTML5
- CSS3
- Vanilla JavaScript
- Bootstrap CDN

## Disclaimer

This tool is for educational purposes only and not a substitute for professional medical advice.
