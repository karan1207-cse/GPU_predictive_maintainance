import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model"] == "GPU_Failure_XGBoost"
    assert data["version"] == "1"


def test_model_info():
    response = client.get("/model-info")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "GPU_Failure_XGBoost"
    assert data["roc_auc"] == 0.8665
    assert data["pr_auc"] == 0.3211
    assert "risk_thresholds" in data


def test_predict_endpoint():
    payload = {
        "gpu_id": "GPU-TEST-01",
        "hostname": "test-node-01",
        "gpu_energy": 240.5,
        "gpu_usage": 98.2,
        "power_max_1min": 350.0,
        "core_temp_max_15min": 85.0,
        "n_NA_power_6h": 0.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "failure_probability" in data
    assert "risk_level" in data
    assert data["risk_level"] in ["HIGH", "MEDIUM", "LOW"]
    assert 0.0 <= data["failure_probability"] <= 1.0


def test_explain_endpoint():
    payload = {
        "gpu_id": "GPU-TEST-02",
        "hostname": "test-node-02",
        "gpu_energy": 310.0,
        "gpu_usage": 99.0,
        "power_max_1min": 380.0,
        "core_temp_max_15min": 88.0,
        "n_NA_power_6h": 12.0
    }
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "failure_probability" in data
    assert "risk_level" in data
    assert "top_factors" in data
    assert len(data["top_factors"]) > 0
    factor = data["top_factors"][0]
    assert "feature" in factor
    assert "impact" in factor
    assert "direction" in factor
    assert factor["direction"] in ["Increases Risk", "Decreases Risk"]


def test_explain_data_consistency_gpu0476():
    # 1. Fetch GPU-0476 detail
    gpu_res = client.get("/dashboard/gpu/GPU-0476")
    assert gpu_res.status_code == 200
    gpu_data = gpu_res.json()
    assert gpu_data["gpu_id"] == "GPU-0476"
    assert gpu_data["risk_level"] == "HIGH"
    expected_prob = gpu_data["failure_probability"]
    assert expected_prob >= 0.90

    # 2. Fetch explain for GPU-0476
    explain_res = client.get("/dashboard/gpu/GPU-0476/explain")
    assert explain_res.status_code == 200
    exp_data = explain_res.json()

    # Probability and risk MUST match 100% identically
    assert exp_data["failure_probability"] == expected_prob
    assert exp_data["risk_level"] == "HIGH"
    assert exp_data["timestamp"] is not None
    assert len(exp_data["top_factors"]) > 0

    # Top factors must contain feature, impact, direction, observed_value
    top1 = exp_data["top_factors"][0]
    assert "feature" in top1
    assert "impact" in top1
    assert "direction" in top1
    assert top1["direction"] in ["Increases Risk", "Decreases Risk"]
    assert "observed_value" in top1


def test_dashboard_prediction_history_multipoint():
    response = client.get("/dashboard/prediction-history/GPU-0476")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Must have multiple historical records (10 seeded points)
    assert len(data) >= 5
    for record in data:
        assert "timestamp" in record
        assert "failure_probability" in record
        assert "risk_level" in record


def test_dashboard_summary():
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_gpus" in data
    assert data["total_gpus"] >= 50
    assert "healthy" in data
    assert "medium_risk" in data
    assert "high_risk" in data


def test_dashboard_gpus():
    response = client.get("/dashboard/gpus?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    gpu = data[0]
    assert "gpu_id" in gpu
    assert "failure_probability" in gpu
    assert "risk_level" in gpu


def test_dashboard_alerts_filters():
    # Test ALL
    res_all = client.get("/dashboard/alerts?risk_level=ALL")
    assert res_all.status_code == 200
    assert isinstance(res_all.json(), list)

    # Test HIGH
    res_high = client.get("/dashboard/alerts?risk_level=HIGH")
    assert res_high.status_code == 200
    for a in res_high.json():
        assert a["risk_level"] == "HIGH"

    # Test LOW
    res_low = client.get("/dashboard/alerts?risk_level=LOW")
    assert res_low.status_code == 200
    for a in res_low.json():
        assert a["risk_level"] == "LOW"


def test_alert_acknowledge_persistence():
    alerts = client.get("/dashboard/alerts?limit=1").json()
    assert len(alerts) > 0
    target_id = alerts[0]["prediction_id"]
    initial_status = alerts[0].get("acknowledged", False)

    # Acknowledge
    ack_res = client.post(f"/dashboard/alerts/{target_id}/acknowledge")
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert ack_data["acknowledged"] == (not initial_status)

    # Re-fetch alerts to verify persistence in database
    alerts_after = client.get("/dashboard/alerts?limit=100").json()
    matched = [a for a in alerts_after if a["prediction_id"] == target_id]
    assert len(matched) == 1
    assert matched[0]["acknowledged"] == (not initial_status)


def test_dashboard_risk_distribution():
    response = client.get("/dashboard/risk-distribution")
    assert response.status_code == 200
    data = response.json()
    assert "low" in data
    assert "medium" in data
    assert "high" in data


def test_dashboard_model_monitoring():
    response = client.get("/dashboard/model-monitoring")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "GPU_Failure_XGBoost"
    assert "total_predictions" in data
    assert "drift_detected" in data
    assert "feature_drift" in data


def test_metrics_prometheus():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests" in response.text or "process_cpu_seconds" in response.text
