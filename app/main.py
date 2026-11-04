"""
main.py — FastAPI application for GPU Failure Detection Platform.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.model import predict, FEATURES
from app.explain import explain_prediction
from app.schemas import (
    GPUData, PredictionResponse, ExplainResponse, FactorImpact,
    ModelMonitoringSummary, FeatureDriftItem,
)
from app.database import get_db, init_db, PredictionRecord
from app.dashboard import router as dashboard_router, seed_initial_data

# ── Add project root to sys.path so src/ imports work ──
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="GPU Failure Detection API",
    description="ML-powered GPU Infrastructure Health & Predictive Failure Detection Platform",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Prometheus ───────────────────────────────────────────────────────────────
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    _instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
    )
    _instrumentator.instrument(app).expose(app, endpoint="/metrics")
except ImportError:
    pass  # prometheus not installed — skip silently

# ── Include dashboard sub-routes ─────────────────────────────────────────────
app.include_router(dashboard_router)


# ── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()
    seed_initial_data()


# ── Core Endpoints ───────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "GPU_Failure_XGBoost",
        "version": "1",
    }


@app.get("/model-info")
def model_info():
    return {
        "model_name":       "GPU_Failure_XGBoost",
        "model_version":    "1",
        "algorithm":        "XGBoost (Gradient Boosted Trees)",
        "roc_auc":          0.8665,
        "pr_auc":           0.3211,
        "feature_count_raw": 140,
        "feature_count_numerical": len(FEATURES),
        "risk_thresholds": {
            "HIGH":   ">= 0.50",
            "MEDIUM": ">= 0.20",
            "LOW":    "< 0.20",
        },
    }


@app.post("/predict", response_model=PredictionResponse)
def predict_failure(data: GPUData, db: Session = Depends(get_db)):
    features = data.model_dump(exclude={"gpu_id", "hostname", "serial"})

    probability, risk = predict(features)

    # Persist prediction
    record = PredictionRecord(
        gpu_id=data.gpu_id,
        hostname=data.hostname,
        serial=data.serial,
        failure_probability=probability,
        risk_level=risk,
        model_name="GPU_Failure_XGBoost",
        model_version="1",
        features_json=json.dumps(
            {k: v for k, v in features.items() if v is not None}
        ),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictionResponse(
        failure_probability=probability,
        risk_level=risk,
        prediction_id=record.prediction_id,
        timestamp=record.timestamp.isoformat() if record.timestamp else None,
    )


@app.post("/explain", response_model=ExplainResponse)
def explain_failure(data: GPUData, db: Session = Depends(get_db)):
    features = data.model_dump(exclude={"gpu_id", "hostname", "serial"})
    has_telemetry = any(v is not None for v in features.values())

    if data.gpu_id and not has_telemetry:
        record = (
            db.query(PredictionRecord)
            .filter(PredictionRecord.gpu_id == data.gpu_id)
            .order_by(desc(PredictionRecord.timestamp))
            .first()
        )
        if record and record.features_json:
            stored_features = json.loads(record.features_json)
            factors = explain_prediction(stored_features, top_k=10)
            factor_models = [FactorImpact(**f) for f in factors]
            return ExplainResponse(
                failure_probability=record.failure_probability,
                risk_level=record.risk_level,
                model_name="GPU_Failure_XGBoost",
                model_version="1",
                features=factor_models,
                top_factors=factor_models,
                gpu_id=record.gpu_id,
                hostname=record.hostname,
                timestamp=record.timestamp.isoformat() if record.timestamp else None,
            )

    probability, risk = predict(features)
    factors = explain_prediction(features, top_k=10)
    factor_models = [FactorImpact(**f) for f in factors]

    return ExplainResponse(
        failure_probability=probability,
        risk_level=risk,
        model_name="GPU_Failure_XGBoost",
        model_version="1",
        features=factor_models,
        top_factors=factor_models,
        gpu_id=data.gpu_id,
        hostname=data.hostname,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ── Clean API Route Aliases ─────────────────────────────────────────────────
# These provide cleaner URLs alongside the /dashboard/* routes

@app.get("/fleet/summary")
def fleet_summary_alias(db: Session = Depends(get_db)):
    """Alias for /dashboard/summary."""
    from app.dashboard import fleet_summary
    return fleet_summary(db)


@app.get("/gpus")
def list_gpus_alias(
    limit: int = 100,
    offset: int = 0,
    risk_level: str = Query(None),
    db: Session = Depends(get_db),
):
    """Alias for /dashboard/gpus."""
    from app.dashboard import list_gpus
    return list_gpus(limit=limit, offset=offset, risk_level=risk_level, db=db)


@app.get("/gpus/{gpu_id}")
def gpu_detail_alias(gpu_id: str, db: Session = Depends(get_db)):
    """Alias for /dashboard/gpu/{gpu_id}."""
    from app.dashboard import gpu_detail
    return gpu_detail(gpu_id, db)


@app.get("/gpus/{gpu_id}/history")
def gpu_history_alias(gpu_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Alias for /dashboard/prediction-history/{gpu_id}."""
    from app.dashboard import prediction_history
    return prediction_history(gpu_id, limit=limit, db=db)


@app.get("/explain/{gpu_id}", response_model=ExplainResponse)
def gpu_explain_alias(gpu_id: str, db: Session = Depends(get_db)):
    """Alias for /dashboard/gpu/{gpu_id}/explain."""
    from app.dashboard import gpu_explain
    return gpu_explain(gpu_id, db)


@app.get("/alerts")
def alerts_alias(
    risk_level: str = Query("ALL"),
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Alias for /dashboard/alerts."""
    from app.dashboard import list_alerts
    return list_alerts(risk_level=risk_level, limit=limit, db=db)


@app.post("/alerts/{prediction_id}/acknowledge")
@app.patch("/alerts/{prediction_id}/acknowledge")
def acknowledge_alias(prediction_id: str, db: Session = Depends(get_db)):
    """Alias for /dashboard/alerts/{prediction_id}/acknowledge (POST & PATCH)."""
    from app.dashboard import acknowledge_alert
    return acknowledge_alert(prediction_id, db)


@app.get("/monitoring")
def monitoring_alias(db: Session = Depends(get_db)):
    """Alias for /dashboard/model-monitoring."""
    return model_monitoring(db)


# ── Model Monitoring Endpoint ───────────────────────────────────────────────

@app.get("/dashboard/model-monitoring")
def model_monitoring(db: Session = Depends(get_db)):
    """Model monitoring with drift detection."""
    total = db.query(func.count(PredictionRecord.prediction_id)).scalar() or 0
    high  = db.query(func.count(PredictionRecord.prediction_id)).filter(
        PredictionRecord.risk_level == "HIGH"
    ).scalar() or 0
    medium = db.query(func.count(PredictionRecord.prediction_id)).filter(
        PredictionRecord.risk_level == "MEDIUM"
    ).scalar() or 0
    low = total - high - medium

    # Compute drift
    try:
        from src.monitoring.drift import compute_drift
        drift_result = compute_drift()
    except Exception:
        drift_result = {
            "drift_detected": False,
            "feature_drift": [],
            "message": "Insufficient prediction data for drift analysis",
            "drift_classification": "INSUFFICIENT_DATA",
        }

    return {
        "model_name":           "GPU_Failure_XGBoost",
        "model_version":        "1",
        "roc_auc":              0.8665,
        "pr_auc":               0.3211,
        "total_predictions":    total,
        "high_risk_count":      high,
        "medium_risk_count":    medium,
        "low_risk_count":       low,
        "drift_detected":       drift_result.get("drift_detected", False),
        "drift_classification": drift_result.get("drift_classification", "LOW"),
        "message":              drift_result.get("message"),
        "feature_drift":        drift_result.get("feature_drift", []),
    }