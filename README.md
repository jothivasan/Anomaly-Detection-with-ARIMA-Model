# Anomaly Detection with ARIMA Model

An explainable Flask application for detecting unusual patterns in financial transaction time series. It combines ARIMA/SARIMAX forecasting with statistical, machine-learning, and risk-scoring components and presents the results in an interactive dashboard.

## Features

- Forecast-based anomaly detection with SARIMAX/ARIMA models
- Isolation Forest and One-Class SVM comparison
- Adaptive thresholds, risk scores, and feature engineering
- Explainability views and real-time simulation
- CSV dataset upload and dashboard-based result exploration

## Tech stack

Python 3.8+, Flask, Pandas, NumPy, scikit-learn, Statsmodels, TensorFlow/Keras, SHAP, HTML/CSS, and JavaScript.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. The sample transaction series are in `Input/`; do not use the application as a financial decision system without validating the models against your own data.

## Project layout

- `app.py` – Flask entry point and routes
- `modules/` – feature engineering, detectors, scoring, and explanations
- `Input/` – sample time-series inputs
- `templates/` and `static/` – dashboard UI

## License

Released under the MIT License. See [LICENSE](LICENSE).
