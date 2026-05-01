# Hypertension Risk Assessment Tool

A single-page clinical decision support demo that estimates hypertension risk using expanded rule-based logic. The project is built with pure HTML, CSS, and vanilla JavaScript, with Bootstrap loaded through a CDN.

This is a prototype UI intended to simulate how a future ML-powered hypertension risk prediction system might behave. It is not a validated medical model.

## Features

- Responsive medical-style dashboard interface
- No backend, database, or build step required
- Expanded rule-based hypertension risk scoring
- Automatic BMI calculation
- Blood pressure stage classification
- Risk percentage and category output
- Clinical score and lifestyle score summaries
- Animated result cards, progress bars, and range markers
- Risk contribution breakdown bar chart
- Clinical vs lifestyle split visualization
- BMI range infographic
- Blood pressure stage infographic
- Ranked top risk drivers panel
- Contributing factor explanation
- Personalized recommendation list
- Input validation and smooth result reveal

## Inputs

The tool asks for:

- Age
- Height, entered in centimeters or feet and inches
- Weight, entered in kilograms or pounds
- Diabetes status
- Smoking status
- Systolic and diastolic blood pressure
- Family history of hypertension
- Physical activity level
- Salt intake
- Alcohol intake
- Stress level
- Average sleep duration

BMI is calculated automatically from height and weight before applying the risk rules.

## Risk Logic

The risk score starts at `0` and increases based on weighted clinical and lifestyle factors. The final score is capped at `100%`.

### Clinical Factors

| Factor | Rule | Score |
| --- | --- | --- |
| Age | 40 to 49 | +7 |
| Age | 50 to 59 | +12 |
| Age | 60 or older | +16 |
| Blood pressure | Systolic 120 to 129 | +6 |
| Blood pressure | Systolic 130+ or diastolic 80+ | +12 |
| Blood pressure | Systolic 140+ or diastolic 90+ | +18 |
| Blood pressure | Systolic 180+ or diastolic 120+ | +24 |
| Diabetes | Yes | +12 |
| Family history | Close relative with hypertension | +8 |

### Body Composition And Lifestyle Factors

| Factor | Rule | Score |
| --- | --- | --- |
| BMI | 25 to 29.9 | +6 |
| BMI | 30 to 34.9 | +11 |
| BMI | 35 or higher | +14 |
| Smoking | Yes | +10 |
| Physical activity | Moderate | +3 |
| Physical activity | Low or sedentary | +8 |
| Salt intake | Moderate | +3 |
| Salt intake | High | +8 |
| Alcohol intake | Moderate | +2 |
| Alcohol intake | Heavy or frequent | +7 |
| Stress | Moderate | +3 |
| Stress | High most days | +6 |
| Sleep | More than 9 hours | +3 |
| Sleep | Less than 6 hours | +6 |

## Risk Categories

| Score | Category |
| --- | --- |
| Less than 30% | Low Risk |
| 30% to 70% | Moderate Risk |
| Greater than 70% | High Risk |

## Result Visualizations

After calculation, the app shows:

- Overall risk percentage
- Risk category badge
- Animated risk progress bar
- BMI value and BMI status
- Blood pressure reading and stage
- Clinical score
- Lifestyle score
- Clinical vs lifestyle split bars
- BMI range marker
- Blood pressure stage marker
- Top risk drivers
- Risk contribution breakdown
- Contributing factors
- Personalized recommendations

## How Recommendations Work

Recommendations are generated from the user's selected risk factors. Examples include:

- Elevated blood pressure: confirm readings with repeated measurements
- Diabetes: discuss blood pressure targets with a clinician
- Smoking: seek smoking cessation support
- High sodium intake: reduce sodium-heavy and highly processed foods
- Low activity: build toward regular moderate activity
- Short sleep duration: aim for consistent 7 to 9 hour sleep when possible
- Elevated BMI: consider weight, nutrition, and activity goals

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

This tool is for educational purposes only and not a substitute for professional medical advice, diagnosis, or treatment. The scoring system is a simplified demonstration and should not be used for real clinical decisions.
