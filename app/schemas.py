"""
schemas.py — Pydantic models for all API endpoints.
"""
from __future__ import annotations

from typing import Optional, List, Any
from pydantic import BaseModel


# ── Input ────────────────────────────────────────────────────────────────────
class GPUData(BaseModel):
    """Full 127-feature GPU telemetry input (all fields optional; NaN-filled at inference)."""
    # Metadata fields (not fed to the model)
    gpu_id:   Optional[str]   = None
    hostname: Optional[str]   = None
    serial:   Optional[str]   = None

    # ── Telemetry features ──
    hours_in_job:            Optional[float] = None
    gpu_energy:              Optional[float] = None
    gpu_usage:               Optional[float] = None
    n_jobs_1h:               Optional[float] = None
    jobhours_1h:             Optional[float] = None
    n_jobs_6h:               Optional[float] = None
    jobhours_6h:             Optional[float] = None
    n_jobs_24h:              Optional[float] = None
    jobhours_24h:            Optional[float] = None
    n_jobs_120h:             Optional[float] = None
    jobhours_120h:           Optional[float] = None
    job_max_power:           Optional[float] = None
    job_range_power:         Optional[float] = None
    job_min_power:           Optional[float] = None
    n_no_tele_6h:            Optional[float] = None
    n_no_tele_1h:            Optional[float] = None
    n_no_tele_15min:         Optional[float] = None
    n_no_tele_5min:          Optional[float] = None
    n_no_tele_1min:          Optional[float] = None
    n_NA_power_6h:           Optional[float] = None
    n_NA_core_temp_6h:       Optional[float] = None
    n_NA_mem_temp_6h:        Optional[float] = None
    n_NA_power_1h:           Optional[float] = None
    n_NA_core_temp_1h:       Optional[float] = None
    n_NA_mem_temp_1h:        Optional[float] = None
    n_NA_power_15min:        Optional[float] = None
    n_NA_core_temp_15min:    Optional[float] = None
    n_NA_mem_temp_15min:     Optional[float] = None
    n_NA_power_5min:         Optional[float] = None
    n_NA_core_temp_5min:     Optional[float] = None
    n_NA_mem_temp_5min:      Optional[float] = None
    n_NA_power_1min:         Optional[float] = None
    n_NA_core_temp_1min:     Optional[float] = None
    n_NA_mem_temp_1min:      Optional[float] = None
    power_fluct_6h:          Optional[float] = None
    core_temp_fluct_6h:      Optional[float] = None
    mem_temp_fluct_6h:       Optional[float] = None
    power_fluct_1h:          Optional[float] = None
    core_temp_fluct_1h:      Optional[float] = None
    mem_temp_fluct_1h:       Optional[float] = None
    power_fluct_15min:       Optional[float] = None
    core_temp_fluct_15min:   Optional[float] = None
    mem_temp_fluct_15min:    Optional[float] = None
    power_fluct_5min:        Optional[float] = None
    core_temp_fluct_5min:    Optional[float] = None
    mem_temp_fluct_5min:     Optional[float] = None
    power_fluct_1min:        Optional[float] = None
    core_temp_fluct_1min:    Optional[float] = None
    mem_temp_fluct_1min:     Optional[float] = None
    power_fluct_lifetime:    Optional[float] = None
    core_temp_fluct_lifetime:Optional[float] = None
    mem_temp_fluct_lifetime: Optional[float] = None
    power_avg_lifetime:      Optional[float] = None
    core_temp_avg_lifetime:  Optional[float] = None
    mem_temp_avg_lifetime:   Optional[float] = None
    power_min_lifetime:      Optional[float] = None
    power_max_lifetime:      Optional[float] = None
    power_range_lifetime:    Optional[float] = None
    core_temp_min_lifetime:  Optional[float] = None
    core_temp_max_lifetime:  Optional[float] = None
    core_temp_range_lifetime:Optional[float] = None
    mem_temp_min_lifetime:   Optional[float] = None
    mem_temp_max_lifetime:   Optional[float] = None
    mem_temp_range_lifetime: Optional[float] = None
    n_zero_power:            Optional[float] = None
    n_zero_core_temp:        Optional[float] = None
    n_zero_mem_temp:         Optional[float] = None
    power_mean_6h:           Optional[float] = None
    power_min_6h:            Optional[float] = None
    power_max_6h:            Optional[float] = None
    power_range_6h:          Optional[float] = None
    core_temp_mean_6h:       Optional[float] = None
    core_temp_min_6h:        Optional[float] = None
    core_temp_max_6h:        Optional[float] = None
    core_temp_range_6h:      Optional[float] = None
    mem_temp_mean_6h:        Optional[float] = None
    mem_temp_min_6h:         Optional[float] = None
    mem_temp_max_6h:         Optional[float] = None
    mem_temp_range_6h:       Optional[float] = None
    power_mean_1h:           Optional[float] = None
    power_min_1h:            Optional[float] = None
    power_max_1h:            Optional[float] = None
    power_range_1h:          Optional[float] = None
    core_temp_mean_1h:       Optional[float] = None
    core_temp_min_1h:        Optional[float] = None
    core_temp_max_1h:        Optional[float] = None
    core_temp_range_1h:      Optional[float] = None
    mem_temp_mean_1h:        Optional[float] = None
    mem_temp_min_1h:         Optional[float] = None
    mem_temp_max_1h:         Optional[float] = None
    mem_temp_range_1h:       Optional[float] = None
    power_mean_15min:        Optional[float] = None
    power_min_15min:         Optional[float] = None
    power_max_15min:         Optional[float] = None
    power_range_15min:       Optional[float] = None
    core_temp_mean_15min:    Optional[float] = None
    core_temp_min_15min:     Optional[float] = None
    core_temp_max_15min:     Optional[float] = None
    core_temp_range_15min:   Optional[float] = None
    mem_temp_mean_15min:     Optional[float] = None
    mem_temp_min_15min:      Optional[float] = None
    mem_temp_max_15min:      Optional[float] = None
    mem_temp_range_15min:    Optional[float] = None
    power_mean_5min:         Optional[float] = None
    power_min_5min:          Optional[float] = None
    power_max_5min:          Optional[float] = None
    power_range_5min:        Optional[float] = None
    core_temp_mean_5min:     Optional[float] = None
    core_temp_min_5min:      Optional[float] = None
    core_temp_max_5min:      Optional[float] = None
    core_temp_range_5min:    Optional[float] = None
    mem_temp_mean_5min:      Optional[float] = None
    mem_temp_min_5min:       Optional[float] = None
    mem_temp_max_5min:       Optional[float] = None
    mem_temp_range_5min:     Optional[float] = None
    power_mean_1min:         Optional[float] = None
    power_min_1min:          Optional[float] = None
    power_max_1min:          Optional[float] = None
    power_range_1min:        Optional[float] = None
    core_temp_mean_1min:     Optional[float] = None
    core_temp_min_1min:      Optional[float] = None
    core_temp_max_1min:      Optional[float] = None
    core_temp_range_1min:    Optional[float] = None
    mem_temp_mean_1min:      Optional[float] = None
    mem_temp_min_1min:       Optional[float] = None
    mem_temp_max_1min:       Optional[float] = None
    mem_temp_range_1min:     Optional[float] = None


# ── Prediction Output ─────────────────────────────────────────────────────────
class PredictionResponse(BaseModel):
    failure_probability: float
    risk_level:          str            # HIGH / MEDIUM / LOW
    prediction_id:       Optional[str] = None
    timestamp:           Optional[str] = None


# ── Explainability ────────────────────────────────────────────────────────────
class FactorImpact(BaseModel):
    feature:        str
    value:          Optional[Any] = None      # float or "N/A"
    shap_value:     float
    effect:         str                       # "increases risk" | "decreases risk"
    # Backward compatibility fields
    impact:         float
    direction:      str                       # "Increases Risk" | "Decreases Risk"
    observed_value: Optional[Any] = None


class ExplainResponse(BaseModel):
    gpu_id:              Optional[str] = None
    hostname:            Optional[str] = None
    failure_probability: float
    risk_level:          str
    model:               str = "GPU_Failure_XGBoost"
    model_name:          str = "GPU_Failure_XGBoost"
    model_version:       str = "1"
    features:            List[FactorImpact] = []
    top_factors:         List[FactorImpact] = []
    timestamp:           Optional[str] = None



# ── Dashboard ─────────────────────────────────────────────────────────────────
class FleetSummary(BaseModel):
    total_gpus:   int
    healthy:      int
    medium_risk:  int
    high_risk:    int


class GPUListItem(BaseModel):
    gpu_id:              str
    hostname:            Optional[str] = None
    serial:              Optional[str] = None
    failure_probability: float
    risk_level:          str
    last_seen:           Optional[str] = None
    # Key telemetry snapshot
    gpu_usage:           Optional[float] = None
    core_temp_max_15min: Optional[float] = None
    power_max_1min:      Optional[float] = None


class GPUDetail(GPUListItem):
    gpu_energy:              Optional[float] = None
    mem_temp_max_5min:       Optional[float] = None
    n_NA_power_6h:           Optional[float] = None
    power_range_15min:       Optional[float] = None


class AlertItem(BaseModel):
    prediction_id:       str
    gpu_id:              Optional[str] = None
    hostname:            Optional[str] = None
    failure_probability: float
    risk_level:          str
    timestamp:           str
    acknowledged:        bool = False


class RiskDistribution(BaseModel):
    low:    int
    medium: int
    high:   int


class FeatureDriftItem(BaseModel):
    feature:     str
    drift_score: float
    drifted:     bool


class ModelMonitoringSummary(BaseModel):
    model_name:          str
    model_version:       str
    roc_auc:             float
    pr_auc:              float
    total_predictions:   int
    high_risk_count:     int
    medium_risk_count:   int
    low_risk_count:      int
    feature_drift:       List[FeatureDriftItem]
    drift_detected:      bool