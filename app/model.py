import os
from pathlib import Path
import urllib.request
import joblib
import pandas as pd

# Safe import for mlflow
try:
    import mlflow
    import mlflow.xgboost
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False

# Resolve project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
MODEL_URI = "models:/GPU_Failure_XGBoost/1"

# Find imputer path reliably
IMPUTER_PATH = BASE_DIR / "models" / "median_imputer.pkl"
if not IMPUTER_PATH.exists():
    IMPUTER_PATH = Path("models/median_imputer.pkl")


def _is_mlflow_server_running(url: str, timeout: float = 1.0) -> bool:
    """Check if MLflow tracking server is reachable."""
    if not HAS_MLFLOW:
        return False
    try:
        urllib.request.urlopen(f"{url.rstrip('/')}/health", timeout=timeout)
        return True
    except Exception:
        return False


def _load_model():
    """Load model from MLflow if running, otherwise fallback to local saved model."""
    if HAS_MLFLOW and _is_mlflow_server_running(MLFLOW_TRACKING_URI):
        try:
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            return mlflow.xgboost.load_model(MODEL_URI)
        except Exception:
            pass

    # Local fallback paths
    local_pkl = BASE_DIR / "models" / "xgb_gpu_failure_model.pkl"
    if local_pkl.exists():
        return joblib.load(local_pkl)

    if HAS_MLFLOW:
        mlartifact_dir = BASE_DIR.parent / "mlartifacts" / "1" / "models" / "m-fb524e00d5c84e37a1d522362e1f562a" / "artifacts"
        if mlartifact_dir.exists():
            return mlflow.xgboost.load_model(str(mlartifact_dir))

    raise FileNotFoundError(f"Could not load XGBoost model from local paths ({local_pkl}).")


# Load preprocessing object
imputer = joblib.load(IMPUTER_PATH)

# Load trained model
model = _load_model()

# Exact features expected by the fitted imputer and XGBoost model
if hasattr(imputer, "feature_names_in_"):
    FEATURES = list(imputer.feature_names_in_)
else:
    FEATURES = [
        "hours_in_job", "gpu_energy", "gpu_usage", "n_jobs_1h", "jobhours_1h",
        "n_jobs_6h", "jobhours_6h", "n_jobs_24h", "jobhours_24h", "n_jobs_120h",
        "jobhours_120h", "job_max_power", "job_range_power", "job_min_power",
        "n_no_tele_6h", "n_no_tele_1h", "n_no_tele_15min", "n_no_tele_5min",
        "n_no_tele_1min", "n_NA_power_6h", "n_NA_core_temp_6h", "n_NA_mem_temp_6h",
        "n_NA_power_1h", "n_NA_core_temp_1h", "n_NA_mem_temp_1h", "n_NA_power_15min",
        "n_NA_core_temp_15min", "n_NA_mem_temp_15min", "n_NA_power_5min", "n_NA_core_temp_5min",
        "n_NA_mem_temp_5min", "n_NA_power_1min", "n_NA_core_temp_1min", "n_NA_mem_temp_1min",
        "power_fluct_6h", "core_temp_fluct_6h", "mem_temp_fluct_6h", "power_fluct_1h",
        "core_temp_fluct_1h", "mem_temp_fluct_1h", "power_fluct_15min", "core_temp_fluct_15min",
        "mem_temp_fluct_15min", "power_fluct_5min", "core_temp_fluct_5min", "mem_temp_fluct_5min",
        "power_fluct_1min", "core_temp_fluct_1min", "mem_temp_fluct_1min", "power_fluct_lifetime",
        "core_temp_fluct_lifetime", "mem_temp_fluct_lifetime", "power_avg_lifetime",
        "core_temp_avg_lifetime", "mem_temp_avg_lifetime", "power_min_lifetime",
        "power_max_lifetime", "power_range_lifetime", "core_temp_min_lifetime",
        "core_temp_max_lifetime", "core_temp_range_lifetime", "mem_temp_min_lifetime",
        "mem_temp_max_lifetime", "mem_temp_range_lifetime", "n_zero_power",
        "n_zero_core_temp", "n_zero_mem_temp", "power_mean_6h", "power_min_6h",
        "power_max_6h", "power_range_6h", "core_temp_mean_6h", "core_temp_min_6h",
        "core_temp_max_6h", "core_temp_range_6h", "mem_temp_mean_6h", "mem_temp_min_6h",
        "mem_temp_max_6h", "mem_temp_range_6h", "power_mean_1h", "power_min_1h",
        "power_max_1h", "power_range_1h", "core_temp_mean_1h", "core_temp_min_1h",
        "core_temp_max_1h", "core_temp_range_1h", "mem_temp_mean_1h", "mem_temp_min_1h",
        "mem_temp_max_1h", "mem_temp_range_1h", "power_mean_15min", "power_min_15min",
        "power_max_15min", "power_range_15min", "core_temp_mean_15min", "core_temp_min_15min",
        "core_temp_max_15min", "core_temp_range_15min", "mem_temp_mean_15min",
        "mem_temp_min_15min", "mem_temp_max_15min", "mem_temp_range_15min",
        "power_mean_5min", "power_min_5min", "power_max_5min", "power_range_5min",
        "core_temp_mean_5min", "core_temp_min_5min", "core_temp_max_5min",
        "core_temp_range_5min", "mem_temp_mean_5min", "mem_temp_min_5min",
        "mem_temp_max_5min", "mem_temp_range_5min", "power_mean_1min", "power_min_1min",
        "power_max_1min", "power_range_1min", "core_temp_mean_1min", "core_temp_min_1min",
        "core_temp_max_1min", "core_temp_range_1min", "mem_temp_mean_1min",
        "mem_temp_min_1min", "mem_temp_max_1min", "mem_temp_range_1min"
    ]


def predict(features: dict):
    # Create dataframe with exact training columns
    df = pd.DataFrame([features])

    # Missing API fields become NaN
    df = df.reindex(columns=FEATURES)

    # Apply training-time preprocessing
    X = imputer.transform(df)

    # Prediction
    probability = float(model.predict_proba(X)[0][1])

    if probability >= 0.5:
        risk = "HIGH"
    elif probability >= 0.2:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return probability, risk