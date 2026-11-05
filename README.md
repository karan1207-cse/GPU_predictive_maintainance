GPU Health & Failure Detection Platform
A machine-learning project for analysing GPU telemetry, detecting
unusual operating behaviour and predicting potential GPU failures.
Accuracy note: This README is based on the project details
available from the resume and previous discussions. Verify exact
dataset sources, feature names, filenames, API routes and run commands
against the current repository before publishing.

Overview
The project explores how historical GPU telemetry can support hardware
health monitoring. It combines:
- Isolation Forest for unsupervised anomaly detection.
- XGBoost for supervised GPU failure prediction.
- MLflow for experiment tracking and model registry.
- SHAP for model explainability.
- FastAPI and React for backend and dashboard components, as
  listed in the project resume. Confirm that both are present in the
  current repository.
Dataset
Previously recorded dataset details:

  Item                          Value
  Total telemetry records      50,259
Total columns                   150
Training records             40,207
Training failure records        241
Testing records              10,052
Testing failure records          54

The dataset is highly imbalanced because failure records are rare. The
telemetry may include utilisation, memory, temperature, power,
performance and hardware-health measurements. Refer to the source
dataset and preprocessing code for the exact feature names and the final
model input columns.
Models
Isolation Forest
Isolation Forest is an unsupervised anomaly-detection algorithm. It
repeatedly uses random feature selections and splits to isolate
observations. Unusual observations are often isolated in fewer splits,
so the algorithm can flag telemetry patterns that differ from normal
behaviour.

An anomaly is not automatically a hardware failure; it is an observation
that may need investigation.
XGBoost
XGBoost is a supervised gradient-boosted decision-tree algorithm. It
learns from labelled historical examples to distinguish failure-related
records from normal records.

Because failures are rare, precision, recall and PR-AUC are important
alongside ROC-AUC.
Explainability
SHAP (SHapley Additive exPlanations) can explain how input features
contribute to model predictions. Confirm which SHAP plots and workflows
are implemented in the repository.
Recorded results
  Model      Metric          Result
  XGBoost    ROC-AUC     0.8665
XGBoost    PR-AUC      0.3211
LightGBM   ROC-AUC     0.8450

ROC-AUC measures ranking discrimination across thresholds. PR-AUC
focuses on the precision-recall trade-off and is especially informative
when the positive class is rare. Reproduce these results using the final
repository code before presenting them as benchmark results.
Technology stack
- Python
- Pandas and NumPy
- Scikit-learn
- XGBoost and LightGBM
- MLflow
- SHAP
- FastAPI
- React
Keep only the tools that are actually present and implemented in the
version you publish.
High-level workflow
GPU telemetry
     |
     v
Data inspection and preprocessing
     |
     v
Feature preparation and train/test split
     |
     +------------------------+
     |                        |
     v                        v
Isolation Forest           XGBoost
Anomaly detection       Failure prediction
     |                        |
     +------------+-----------+
                  |
                  v
           Model evaluation
          ROC-AUC / PR-AUC
                  |
                  v
        Experiment tracking
               MLflow
                  |
                  v
       API and dashboard layer*
* Include the API and dashboard only if these components are
implemented and working in the current repository.
Evaluation metrics
- Precision: Of the records predicted as failures, how many were
  actual failures?
- Recall: Of all actual failures, how many did the model identify?
- F1-score: Harmonic mean of precision and recall.
- ROC-AUC: Ability to rank positive examples above negative
  examples across thresholds.
- PR-AUC: Area under the precision-recall curve.
Review the confusion matrix and choose a decision threshold based on the
cost of missed failures versus false alarms.
Setup
The exact project entry points and run commands were not available when
this README was prepared. Add the verified commands from your repository
instead of guessing filenames.

Create and activate a virtual environment:
python -m venv .venv
Windows PowerShell:
.\.venv\Scripts\Activate.ps1
Linux/macOS:
source .venv/bin/activate
Install dependencies if the repository contains requirements.txt:
pip install -r requirements.txt
Run the training notebook/script, API and frontend using the actual
entry points documented in your repository.
Limitations and future improvements
- Failure labels are highly imbalanced; threshold selection and
  precision-recall analysis are important.
- An anomaly does not necessarily mean a failure.
- A random split can overestimate performance if records from the same
  GPU or nearby time periods appear in both sets. Consider
  GPU-ID-based or time-based validation, depending on the intended
  deployment.
- Monitor data drift and model performance after deployment.
- Validate data quality and model performance before using predictions
  operationally.
Future enhancements
- Evaluate time-based and GPU-group-based validation.
- Tune the decision threshold to operational requirements.
- Add data-drift and model-performance monitoring.
- Improve explanations for high-risk predictions.
- Automate retraining with explicit data-quality and model-acceptance
  checks.
Author
Karan Almad
Computer Science Engineering | Machine Learning | Backend Development
| Cloud Technologies
Before publishing
Verify the dataset source, exact feature columns, preprocessing steps,
model parameters, file names, API endpoints, screenshots and run
commands. Remove any claim or technology that is not actually
implemented in your repository.
