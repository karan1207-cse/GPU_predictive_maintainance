"""
dashboard.py — Dashboard API routes for the GPU Monitoring frontend.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db, PredictionRecord, SessionLocal
from app.model import predict, FEATURES
from app.explain import explain_prediction
from app.schemas import FactorImpact, ExplainResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

BASE_DIR = Path(__file__).resolve().parent.parent

_SEEDED = False


def seed_initial_data():
    """
    On first startup, seed the database from raw CSV so the dashboard
    shows realistic fleet data with genuine historical telemetry sequences.
    """
    global _SEEDED
    if _SEEDED:
        return
    _SEEDED = True

    db = SessionLocal()
    try:
        count = db.query(func.count(PredictionRecord.prediction_id)).scalar()
        if count > 0:
            return  # Already seeded

        csv_path = BASE_DIR / "data" / "raw" / "points_with_jobs_tele_ult.csv"
        if not csv_path.exists():
            return

        import pandas as pd
        # Load 500 rows to establish a 50-GPU fleet with 10 snapshots per GPU
        df = pd.read_csv(csv_path, nrows=500)

        feature_cols = [c for c in FEATURES if c in df.columns]

        now = datetime.now(timezone.utc)
        records = []

        total_rows = len(df)
        num_gpus = 50

        # We map rows to 50 fleet GPUs.
        # Row 476 is mapped to GPU-0476 so it has genuine historical readings leading up to it.
        for i in range(total_rows):
            row = df.iloc[i]
            gpu_idx = i % num_gpus
            if gpu_idx == 26:  # 476 % 50 == 26
                gpu_id = "GPU-0476"
                hostname = "c04n16"
            else:
                gpu_id = f"GPU-{gpu_idx + 1:04d}"
                hostname = f"node-{((gpu_idx) // 4) + 1:02d}"

            # Step index for this GPU (0 to 9)
            step = i // num_gpus
            # Chronological timestamp: step 9 is now, step 0 is 9 hours ago
            time_offset = timedelta(hours=(9 - step), minutes=(i % 15))
            record_time = now - time_offset

            features = {
                c: float(row[c])
                for c in feature_cols
                if c in row and pd.notna(row[c])
            }

            prob, risk = predict(features)

            serial_val = str(row.get("serial", f"SN-{100000 + gpu_idx}"))

            record = PredictionRecord(
                timestamp=record_time,
                gpu_id=gpu_id,
                hostname=hostname,
                serial=serial_val,
                failure_probability=prob,
                risk_level=risk,
                model_version="1",
                features_json=json.dumps(features),
                acknowledged=False,
            )
            records.append(record)

        db.add_all(records)
        db.commit()
        print(f"[seed] Successfully seeded {len(records)} prediction records for {num_gpus} GPUs.")
    except Exception as e:
        db.rollback()
        print(f"[seed] Warning: could not seed DB — {e}")
    finally:
        db.close()


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/summary")
def fleet_summary(db: Session = Depends(get_db)):
    """Fleet-wide KPI summary based on latest status per GPU."""
    subq = (
        db.query(
            PredictionRecord.gpu_id,
            func.max(PredictionRecord.timestamp).label("latest"),
        )
        .filter(PredictionRecord.gpu_id.isnot(None))
        .group_by(PredictionRecord.gpu_id)
        .subquery()
    )

    latest = (
        db.query(PredictionRecord)
        .join(
            subq,
            (PredictionRecord.gpu_id == subq.c.gpu_id)
            & (PredictionRecord.timestamp == subq.c.latest),
        )
        .all()
    )

    high = sum(1 for r in latest if r.risk_level == "HIGH")
    medium = sum(1 for r in latest if r.risk_level == "MEDIUM")
    healthy = len(latest) - high - medium

    return {
        "total_gpus": len(latest),
        "healthy":    healthy,
        "medium_risk": medium,
        "high_risk":  high,
    }


@router.get("/gpus")
def list_gpus(
    limit: int = 100,
    offset: int = 0,
    risk_level: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List GPUs with their latest prediction status."""
    subq = (
        db.query(
            PredictionRecord.gpu_id,
            func.max(PredictionRecord.timestamp).label("latest"),
        )
        .filter(PredictionRecord.gpu_id.isnot(None))
        .group_by(PredictionRecord.gpu_id)
        .subquery()
    )

    q = (
        db.query(PredictionRecord)
        .join(
            subq,
            (PredictionRecord.gpu_id == subq.c.gpu_id)
            & (PredictionRecord.timestamp == subq.c.latest),
        )
    )

    if risk_level and risk_level.upper() != "ALL":
        q = q.filter(PredictionRecord.risk_level == risk_level.upper())

    rows = q.order_by(desc(PredictionRecord.failure_probability)).offset(offset).limit(limit).all()

    result = []
    for r in rows:
        features = {}
        if r.features_json:
            try:
                features = json.loads(r.features_json)
            except Exception:
                pass
        result.append({
            "gpu_id":              r.gpu_id,
            "hostname":            r.hostname,
            "serial":              r.serial,
            "failure_probability": r.failure_probability,
            "risk_level":          r.risk_level,
            "last_seen":           r.timestamp.isoformat() if r.timestamp else None,
            "gpu_usage":           features.get("gpu_usage"),
            "core_temp_max_15min": features.get("core_temp_max_15min"),
            "power_max_1min":      features.get("power_max_1min"),
            "acknowledged":        bool(r.acknowledged),
        })

    return result


@router.get("/alerts")
def list_alerts(
    risk_level: Optional[str] = Query("ALL"),
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Alerts list with filtering by ALL, HIGH, MEDIUM, or LOW."""
    q = db.query(PredictionRecord)

    if risk_level and risk_level.upper() in ("HIGH", "MEDIUM", "LOW"):
        q = q.filter(PredictionRecord.risk_level == risk_level.upper())
    else:
        # ALL alerts: return all predictions ordered by risk and timestamp
        q = q.filter(PredictionRecord.risk_level.in_(["HIGH", "MEDIUM", "LOW"]))

    rows = q.order_by(desc(PredictionRecord.timestamp)).limit(limit).all()

    return [
        {
            "prediction_id":       r.prediction_id,
            "gpu_id":              r.gpu_id,
            "hostname":            r.hostname,
            "failure_probability": r.failure_probability,
            "risk_level":          r.risk_level,
            "timestamp":           r.timestamp.isoformat() if r.timestamp else None,
            "acknowledged":        bool(r.acknowledged),
        }
        for r in rows
    ]


@router.post("/alerts/{prediction_id}/acknowledge")
def acknowledge_alert(prediction_id: str, db: Session = Depends(get_db)):
    """Persist acknowledgement status for an alert in the database."""
    record = (
        db.query(PredictionRecord)
        .filter(PredictionRecord.prediction_id == prediction_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Alert record not found")

    record.acknowledged = not record.acknowledged
    db.commit()
    db.refresh(record)

    return {
        "status": "success",
        "prediction_id": record.prediction_id,
        "acknowledged": bool(record.acknowledged),
    }


@router.get("/gpu/{gpu_id}")
def gpu_detail(gpu_id: str, db: Session = Depends(get_db)):
    """Deep-dive telemetry for a single GPU (latest state)."""
    record = (
        db.query(PredictionRecord)
        .filter(PredictionRecord.gpu_id == gpu_id)
        .order_by(desc(PredictionRecord.timestamp))
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="GPU not found")

    features = {}
    if record.features_json:
        try:
            features = json.loads(record.features_json)
        except Exception:
            pass

    return {
        "gpu_id":              record.gpu_id,
        "hostname":            record.hostname,
        "serial":              record.serial,
        "failure_probability": record.failure_probability,
        "risk_level":          record.risk_level,
        "last_seen":           record.timestamp.isoformat() if record.timestamp else None,
        "gpu_usage":           features.get("gpu_usage"),
        "gpu_energy":          features.get("gpu_energy"),
        "core_temp_max_15min": features.get("core_temp_max_15min"),
        "power_max_1min":      features.get("power_max_1min"),
        "mem_temp_max_5min":   features.get("mem_temp_max_5min"),
        "n_NA_power_6h":       features.get("n_NA_power_6h"),
        "power_range_15min":   features.get("power_range_15min"),
        "acknowledged":        bool(record.acknowledged),
    }


@router.get("/gpu/{gpu_id}/explain", response_model=ExplainResponse)
def gpu_explain(gpu_id: str, db: Session = Depends(get_db)):
    """
    Explain the latest prediction of a specific GPU using its EXACT
    underlying feature vector from the database.
    """
    record = (
        db.query(PredictionRecord)
        .filter(PredictionRecord.gpu_id == gpu_id)
        .order_by(desc(PredictionRecord.timestamp))
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="GPU not found")

    features = {}
    if record.features_json:
        try:
            features = json.loads(record.features_json)
        except Exception:
            pass

    factors = explain_prediction(features, top_k=10)
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


@router.get("/risk-distribution")
def risk_distribution(db: Session = Depends(get_db)):
    """Aggregated risk counts from latest predictions per GPU."""
    subq = (
        db.query(
            PredictionRecord.gpu_id,
            func.max(PredictionRecord.timestamp).label("latest"),
        )
        .filter(PredictionRecord.gpu_id.isnot(None))
        .group_by(PredictionRecord.gpu_id)
        .subquery()
    )

    latest = (
        db.query(PredictionRecord)
        .join(
            subq,
            (PredictionRecord.gpu_id == subq.c.gpu_id)
            & (PredictionRecord.timestamp == subq.c.latest),
        )
        .all()
    )

    low = sum(1 for r in latest if r.risk_level == "LOW")
    medium = sum(1 for r in latest if r.risk_level == "MEDIUM")
    high = sum(1 for r in latest if r.risk_level == "HIGH")

    return {"low": low, "medium": medium, "high": high}


@router.get("/prediction-history/{gpu_id}")
def prediction_history(
    gpu_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Time series of failure probabilities for a GPU, ordered chronologically.
    """
    rows = (
        db.query(PredictionRecord)
        .filter(PredictionRecord.gpu_id == gpu_id)
        .order_by(PredictionRecord.timestamp.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "timestamp":           r.timestamp.isoformat() if r.timestamp else None,
            "failure_probability": r.failure_probability,
            "risk_level":          r.risk_level,
        }
        for r in rows
    ]
