
# GPU Health & Failure Detection Platform

A machine learning-based platform designed to analyse GPU telemetry, detect unusual operating behaviour, and predict potential GPU failures.

## Project Overview

GPU infrastructure generates large amounts of telemetry data. Analysing this data can help identify abnormal hardware behaviour and potential failures.

This project uses machine learning techniques to detect anomalies and predict GPU failures using historical telemetry data.

### Key Features

- GPU telemetry data analysis
- Anomaly detection using Isolation Forest
- Failure prediction using XGBoost
- Model performance evaluation
- Model explainability using SHAP
- Experiment tracking using MLflow
- GPU health monitoring concepts

## Dataset Information

The dataset contains approximately:

| Description | Value |
|---|---:|
| Total Records | 50,259 |
| Total Columns | 150 |
| Training Records | 40,207 |
| Testing Records | 10,052 |
| Training Failures | 241 |
| Testing Failures | 54 |

The dataset contains highly imbalanced failure records, making precision and recall important evaluation metrics.

## Technology Stack

- Python
- Pandas
- NumPy
- Scikit-learn
- XGBoost
- LightGBM
- Isolation Forest
- SHAP
- MLflow
- FastAPI
- React

## Machine Learning Models

### 1. Isolation Forest

Isolation Forest is an unsupervised machine learning algorithm used for anomaly detection.

It identifies unusual observations by randomly selecting features and splitting data. Anomalies generally require fewer splits to become isolated.

In this project, it is used to identify unusual GPU telemetry patterns.

### 2. XGBoost

XGBoost is a supervised machine learning algorithm based on gradient-boosted decision trees.

It learns from labelled historical telemetry data to predict potential GPU failures.

### 3. SHAP Explainability

SHAP helps explain machine learning predictions by showing how individual features contribute to model outputs.

It helps understand which telemetry features influence failure predictions.

## Model Performance

Recorded experimental results:

| Model | Metric | Score |
|---|---|---:|
| XGBoost | ROC-AUC | 0.8665 |
| XGBoost | PR-AUC | 0.3211 |
| LightGBM | ROC-AUC | 0.8450 |

### Evaluation Metrics

- **ROC-AUC:** Measures how well the model distinguishes positive and negative classes.
- **PR-AUC:** Measures the precision-recall trade-off, especially useful for imbalanced datasets.
- **Precision:** Percentage of predicted failures that are actual failures.
- **Recall:** Percentage of actual failures correctly identified.

## Project Workflow

1. Collect GPU telemetry data.
2. Inspect and preprocess the dataset.
3. Prepare features for machine learning.
4. Split the dataset into training and testing sets.
5. Apply Isolation Forest for anomaly detection.
6. Train XGBoost for failure prediction.
7. Evaluate models using ROC-AUC and PR-AUC.
8. Track experiments using MLflow.
9. Analyse feature contributions using SHAP.

## Why This Project?

GPU failures can affect infrastructure availability and performance.

Predictive maintenance helps identify unusual operating conditions and potential hardware risks before they become critical problems.

This project explores how machine learning can support proactive GPU health monitoring.

## Future Improvements

- Improve failure prediction performance.
- Evaluate time-based and GPU-based train/test splitting.
- Implement real-time telemetry monitoring.
- Add data drift detection.
- Improve model explainability.
- Develop automated model retraining workflows.

## Author

**Karan Almad**

Computer Science Engineering Student

Interested in Machine Learning, Software Development and Cloud Technologies.
