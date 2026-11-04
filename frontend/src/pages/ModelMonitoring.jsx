import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from "recharts";
import { Activity, CheckCircle2, AlertCircle, Database, Award, ShieldAlert, Info } from "lucide-react";
import { getModelMonitoring, getModelInfo } from "../services/api";

export default function ModelMonitoring() {
  const [monitoring, setMonitoring] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getModelMonitoring(),
      getModelInfo()
    ])
      .then(([monRes, infoRes]) => {
        setMonitoring(monRes.data);
        setModelInfo(infoRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-container"><div className="spinner" /></div>;

  const driftData = (monitoring?.feature_drift || []).map((fd) => ({
    feature: fd.feature,
    drift_score: fd.drift_score,
    drifted: fd.drifted,
    classification: fd.drift_classification || (fd.drift_score > 0.30 ? "HIGH" : fd.drift_score >= 0.20 ? "MODERATE" : "LOW")
  }));

  const overallClassification = monitoring?.drift_classification || 
    (monitoring?.drift_detected ? "HIGH" : "LOW");

  const isInsufficient = monitoring?.message && monitoring?.message.toLowerCase().includes("insufficient");

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Model Monitoring & Data Drift</h2>
        <p>Evidently & Prometheus telemetry for serving degradation and distribution drift</p>
      </div>

      {/* Model Spec KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card total">
          <div className="kpi-icon"><Award size={40} /></div>
          <div className="kpi-label">Registered Model</div>
          <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>
            {monitoring?.model_name || "GPU_Failure_XGBoost"}
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
            Version {monitoring?.model_version || "1"} (Production)
          </div>
        </div>

        <div className="kpi-card healthy">
          <div className="kpi-icon"><Activity size={40} /></div>
          <div className="kpi-label">Validation ROC-AUC</div>
          <div className="kpi-value">{modelInfo?.roc_auc?.toFixed(4) || "0.8665"}</div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
            PR-AUC: {modelInfo?.pr_auc?.toFixed(4) || "0.3211"}
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon"><Database size={40} /></div>
          <div className="kpi-label">Total Predictions Evaluated</div>
          <div className="kpi-value">
            {monitoring?.total_predictions?.toLocaleString() || 0}
          </div>
        </div>

        <div className={`kpi-card ${overallClassification === "HIGH" ? "high" : overallClassification === "MODERATE" ? "medium" : "healthy"}`}>
          <div className="kpi-icon"><ShieldAlert size={40} /></div>
          <div className="kpi-label">Data Drift Status</div>
          <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 8 }}>
            {monitoring?.drift_detected ? (
              <span className="drift-status alert">
                <AlertCircle size={16} /> Drift Detected ({overallClassification})
              </span>
            ) : (
              <span className="drift-status ok">
                <CheckCircle2 size={16} /> Baseline Stable ({overallClassification})
              </span>
            )}
          </div>
        </div>
      </div>

      {isInsufficient && (
        <div className="card" style={{ marginBottom: 20, borderColor: "var(--yellow)", background: "rgba(245, 158, 11, 0.08)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Info size={20} color="var(--yellow)" />
            <div>
              <strong style={{ color: "var(--yellow)" }}>Notice:</strong> {monitoring.message}
            </div>
          </div>
        </div>
      )}

      {/* Drift Details and Threshold Specs */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Monitored Feature Drift Scores</span>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Evidently Preset</span>
          </div>

          {driftData.length > 0 ? (
            <div style={{ width: "100%", height: 380, minHeight: 380 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={driftData} margin={{ top: 10, right: 20, left: -10, bottom: 90 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(75,85,99,0.2)" />
                  <XAxis
                    dataKey="feature"
                    stroke="var(--text-muted)"
                    tick={{ fontSize: 10 }}
                    angle={-45}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--bg-secondary)",
                      border: "1px solid var(--border)",
                      borderRadius: 8,
                      fontSize: 12
                    }}
                    formatter={(val, name, item) => [
                      `${val} — ${item.payload.classification} Risk (${item.payload.drifted ? "Drifted" : "Normal"})`,
                      "Drift Score"
                    ]}
                  />
                  <Bar dataKey="drift_score" radius={[4, 4, 0, 0]}>
                    {driftData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.classification === "HIGH" ? "#ef4444" : entry.classification === "MODERATE" ? "#f59e0b" : "#6366f1"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
              {monitoring?.message || "No drift data recorded yet."}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Production Model & Drift Specifications</span>
          </div>

          <div className="stat-row">
            <span className="stat-label">Model Architecture</span>
            <span className="stat-value">{modelInfo?.algorithm || "XGBoost"}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Feature Space</span>
            <span className="stat-value">140 Raw / 127 Numerical Imputed</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">High Risk Threshold</span>
            <span className="stat-value" style={{ color: "var(--red)" }}>&ge; 0.50</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Medium Risk Threshold</span>
            <span className="stat-value" style={{ color: "var(--yellow)" }}>0.20 - 0.49</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Low Risk Threshold</span>
            <span className="stat-value" style={{ color: "var(--green)" }}>&lt; 0.20</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Drift Classification: LOW</span>
            <span className="stat-value" style={{ color: "var(--green)" }}>&lt; 0.20</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Drift Classification: MODERATE</span>
            <span className="stat-value" style={{ color: "var(--yellow)" }}>0.20 - 0.30</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Drift Classification: HIGH</span>
            <span className="stat-value" style={{ color: "var(--red)" }}>&gt; 0.30</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Prometheus Metrics Endpoint</span>
            <span className="stat-value" style={{ fontFamily: "monospace", fontSize: 12 }}>
              /metrics
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
