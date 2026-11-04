"""
drift.py — Evidently-based feature drift monitoring.

Compares incoming prediction batches against a reference baseline
derived from the first seeded data.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from sqlalchemy import func, desc

from app.database import SessionLocal, PredictionRecord

# Target features to monitor for drift
MONITORED_FEATURES = [
    "gpu_energy", "gpu_usage",
    "power_max_1min", "power_range_15min",
    "core_temp_max_15min", "core_temp_max_5min",
    "mem_temp_max_5min",
    "n_NA_power_1h", "n_NA_power_6h",
]

# Lazy import evidently (heavy dependency)
try:
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset
    HAS_EVIDENTLY = True
except ImportError:
    HAS_EVIDENTLY = False


def _load_predictions_df(limit: int = 500) -> pd.DataFrame:
    """Load recent predictions with their feature JSON into a DataFrame."""
    db = SessionLocal()
    try:
        rows = (
            db.query(PredictionRecord)
            .filter(PredictionRecord.features_json.isnot(None))
            .order_by(desc(PredictionRecord.timestamp))
            .limit(limit)
            .all()
        )
        records = []
        for r in rows:
            try:
                feats = json.loads(r.features_json)
                records.append(feats)
            except Exception:
                pass
        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records)
    finally:
        db.close()


def compute_drift() -> Dict[str, Any]:
    """
    Compute feature drift using Evidently.

    Returns a dict with per-feature drift scores and an overall drift flag.
    """
    df = _load_predictions_df(limit=500)
    if df.empty or len(df) < 20:
        return {
            "drift_detected": False,
            "feature_drift": [],
            "message": "Insufficient prediction data for drift analysis",
            "drift_classification": "INSUFFICIENT_DATA",
        }

    # Keep only monitored features that exist in the data
    available = [f for f in MONITORED_FEATURES if f in df.columns]
    if not available:
        return {
            "drift_detected": False,
            "feature_drift": [],
            "message": "No monitored features found in prediction data.",
        }

    df_monitored = df[available].apply(pd.to_numeric, errors="coerce")

    # Split: first half = reference, second half = current
    split = len(df_monitored) // 2
    reference = df_monitored.iloc[:split]
    current   = df_monitored.iloc[split:]

    if not HAS_EVIDENTLY:
        # Fallback: simple statistical comparison
        return _simple_drift(reference, current, available)

    try:
        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=reference, current_data=current)
        result = report.as_dict()

        feature_drift = []
        overall_drifted = False

        metrics = result.get("metrics", [])
        for m in metrics:
            mr = m.get("result", {})
            if "drift_by_columns" in mr:
                for col_name, col_data in mr["drift_by_columns"].items():
                    if col_name in available:
                        drifted = bool(col_data.get("drift_detected", False))
                        score = float(col_data.get("drift_score", 0.0))
                        classification = _classify_drift(score)
                        feature_drift.append({
                            "feature": str(col_name),
                            "drift_score": round(score, 4),
                            "drifted": drifted,
                            "drift_classification": classification,
                        })
                        if drifted:
                            overall_drifted = True

        # Overall classification based on max drift score
        max_score = max((fd["drift_score"] for fd in feature_drift), default=0.0)
        return {
            "drift_detected": bool(overall_drifted),
            "feature_drift": feature_drift,
            "drift_classification": _classify_drift(max_score),
        }
    except Exception as e:
        return _simple_drift(reference, current, available)


def _classify_drift(score: float) -> str:
    """Classify drift score into LOW / MODERATE / HIGH."""
    if score > 0.30:
        return "HIGH"
    elif score >= 0.20:
        return "MODERATE"
    else:
        return "LOW"


def _simple_drift(reference: pd.DataFrame, current: pd.DataFrame, features: List[str]) -> Dict[str, Any]:
    """
    Simple drift detection fallback using KS-like relative mean shift.
    """
    feature_drift = []
    overall_drifted = False

    for feat in features:
        ref_mean = float(reference[feat].mean())
        cur_mean = float(current[feat].mean())
        ref_std  = float(reference[feat].std())

        if ref_std > 0:
            shift = abs(cur_mean - ref_mean) / ref_std
        else:
            shift = 0.0

        drifted = bool(shift > 2.0)  # > 2 std deviations = drift
        classification = _classify_drift(shift)
        feature_drift.append({
            "feature":     str(feat),
            "drift_score": round(float(shift), 4),
            "drifted":     drifted,
            "drift_classification": classification,
        })
        if drifted:
            overall_drifted = True

    max_score = max((fd["drift_score"] for fd in feature_drift), default=0.0)
    return {
        "drift_detected": bool(overall_drifted),
        "feature_drift":  feature_drift,
        "drift_classification": _classify_drift(max_score),
    }
