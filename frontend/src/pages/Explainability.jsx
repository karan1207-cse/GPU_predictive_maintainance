import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from "recharts";
import { ArrowUpRight, ArrowDownRight, RefreshCw, AlertCircle, Clock } from "lucide-react";
import { getGpuList, getGpuExplain } from "../services/api";

function RiskBadge({ level }) {
  const cls = (level || "").toLowerCase();
  return (
    <span className={`badge ${cls}`}>
      <span className="badge-dot" />
      {level}
    </span>
  );
}

function formatObservedValue(val) {
  if (val == null || val === "N/A") return "N/A";
  const num = Number(val);
  if (isNaN(num)) return String(val);
  if (Math.abs(num) >= 1e6) return num.toLocaleString();
  return num % 1 !== 0 ? num.toFixed(2) : num.toString();
}

function formatTimestamp(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}, ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

export default function Explainability() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [gpuList, setGpuList] = useState([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("id") || "");
  const [loadingGpus, setLoadingGpus] = useState(true);
  const [explainLoading, setExplainLoading] = useState(false);
  const [explanation, setExplanation] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    getGpuList({ limit: 100 })
      .then((res) => {
        setGpuList(res.data);
        const urlId = searchParams.get("id");
        if (urlId && res.data.find((g) => g.gpu_id === urlId)) {
          setSelectedId(urlId);
        } else if (!selectedId && res.data.length > 0) {
          const found476 = res.data.find((g) => g.gpu_id === "GPU-0476");
          setSelectedId(found476 ? found476.gpu_id : res.data[0].gpu_id);
        }
      })
      .catch((err) => {
        console.error("Failed to load GPU list:", err);
        setErrorMsg("Unable to load GPU fleet list.");
      })
      .finally(() => setLoadingGpus(false));
  }, []);

  // Sync selectedId to URL
  useEffect(() => {
    if (selectedId) {
      setSearchParams({ id: selectedId }, { replace: true });
    }
  }, [selectedId]);

  const runExplanation = (id) => {
    if (!id) return;
    setExplainLoading(true);
    setErrorMsg(null);

    getGpuExplain(id)
      .then((res) => {
        setExplanation(res.data);
      })
      .catch((err) => {
        console.error("SHAP explanation error:", err);
        setErrorMsg("Unable to generate SHAP explanation for this GPU.");
        setExplanation(null);
      })
      .finally(() => setExplainLoading(false));
  };

  useEffect(() => {
    if (selectedId) {
      runExplanation(selectedId);
    }
  }, [selectedId]);

  // Use features list if available, fall back to top_factors
  const factors = explanation?.features?.length > 0
    ? explanation.features
    : (explanation?.top_factors || []);

  const chartData = factors.map((f) => {
    const isIncrease = (f.effect || f.direction || "").toLowerCase().includes("increase");
    const val = f.value != null && f.value !== "N/A" ? f.value : (f.observed_value ?? null);
    return {
      feature: f.feature,
      impact: Math.abs(f.shap_value ?? f.impact),
      rawImpact: f.shap_value ?? f.impact,
      direction: isIncrease ? "Increases Risk" : "Decreases Risk",
      isIncrease,
      observedValue: formatObservedValue(val),
    };
  });

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Explainability (SHAP Analysis)</h2>
        <p>Model interpretability and root cause attribution for GPU telemetry</p>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <div style={{ minWidth: 280, flex: 1 }}>
            <label style={{ fontSize: 12, color: "var(--text-muted)", display: "block", marginBottom: 6 }}>
              SELECT GPU FOR EXPLANATION
            </label>
            <div className="select-wrapper">
              <select
                value={selectedId}
                onChange={(e) => setSelectedId(e.target.value)}
                disabled={loadingGpus}
              >
                {gpuList.map((g) => (
                  <option key={g.gpu_id} value={g.gpu_id}>
                    {g.gpu_id} — {g.risk_level} ({(g.failure_probability * 100).toFixed(1)}%)
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            className="filter-btn"
            style={{ display: "flex", alignItems: "center", gap: 6, alignSelf: "flex-end", height: 40 }}
            onClick={() => runExplanation(selectedId)}
            disabled={explainLoading}
          >
            <RefreshCw size={14} className={explainLoading ? "spinner" : ""} />
            Re-run Analysis
          </button>
        </div>
      </div>

      {explainLoading ? (
        <div className="loading-container">
          <div className="spinner" />
          <span style={{ marginLeft: 12, color: "var(--text-muted)", fontSize: 13 }}>Loading GPU explanation...</span>
        </div>
      ) : errorMsg ? (
        <div className="card" style={{ textAlign: "center", padding: 48, borderColor: "var(--red)" }}>
          <AlertCircle size={36} color="var(--red)" style={{ margin: "0 auto 12px auto" }} />
          <h3 style={{ fontSize: 16, color: "var(--red)", marginBottom: 6 }}>Explanation Unavailable</h3>
          <p style={{ color: "var(--text-muted)", fontSize: 13 }}>{errorMsg}</p>
        </div>
      ) : explanation ? (
        <>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-label">Selected GPU</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{explanation.gpu_id || selectedId}</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                Host: {explanation.hostname || "—"}
              </div>
              {explanation.timestamp && (
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4, display: "flex", alignItems: "center", gap: 4 }}>
                  <Clock size={12} />
                  Prediction timestamp: {formatTimestamp(explanation.timestamp)}
                </div>
              )}
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Calculated Failure Risk</div>
              <div style={{ fontSize: 28, fontWeight: 800, marginTop: 4 }}>
                {(explanation.failure_probability * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                Model: {explanation.model_name || "GPU_Failure_XGBoost"} v{explanation.model_version || "1"}
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Risk Classification</div>
              <div style={{ marginTop: 8 }}>
                <RiskBadge level={explanation.risk_level} />
              </div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
                Threshold: {explanation.risk_level === "HIGH" ? "≥ 0.50" : explanation.risk_level === "MEDIUM" ? "0.20 - 0.49" : "< 0.20"}
              </div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <div className="card-header">
                <span className="card-title">Top Contributing Factors (SHAP Magnitude)</span>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>TreeExplainer (Absolute |SHAP|)</span>
              </div>

              {chartData.length > 0 ? (
                <div style={{ width: "100%", height: 350, minHeight: 350 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 30, top: 10, bottom: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(75,85,99,0.2)" />
                      <XAxis type="number" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                      <YAxis
                        dataKey="feature"
                        type="category"
                        stroke="var(--text-muted)"
                        tick={{ fontSize: 10 }}
                        width={130}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "var(--bg-secondary)",
                          border: "1px solid var(--border)",
                          borderRadius: 8,
                          fontSize: 12,
                        }}
                        formatter={(val, name, item) => [
                          `${item.payload.rawImpact > 0 ? "+" : ""}${item.payload.rawImpact.toFixed(4)} (${item.payload.direction})`,
                          "SHAP Impact"
                        ]}
                      />
                      <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                        {chartData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.isIncrease ? "var(--red)" : "var(--green)"}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                  No factors returned by SHAP explainer.
                </p>
              )}

              <div style={{ display: "flex", gap: 16, justifyContent: "center", marginTop: 8, fontSize: 12 }}>
                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ width: 10, height: 10, background: "var(--red)", borderRadius: 2 }} />
                  Increases Risk (+SHAP)
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ width: 10, height: 10, background: "var(--green)", borderRadius: 2 }} />
                  Decreases Risk (-SHAP)
                </span>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <span className="card-title">Feature Contribution Breakdown</span>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  Top {factors.length} Factors
                </span>
              </div>
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Feature</th>
                      <th>Observed Value</th>
                      <th>Effect</th>
                      <th>SHAP Impact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {factors.map((factor, idx) => {
                      const isIncrease = (factor.effect || factor.direction || "").toLowerCase().includes("increase");
                      const val = factor.value != null && factor.value !== "N/A" ? factor.value : (factor.observed_value ?? null);
                      const shapVal = factor.shap_value ?? factor.impact;
                      return (
                        <tr key={idx}>
                          <td style={{ fontWeight: 500, color: "var(--text-primary)" }}>{factor.feature}</td>
                          <td>{formatObservedValue(val)}</td>
                          <td>
                            {isIncrease ? (
                              <span style={{ color: "var(--red)", display: "flex", alignItems: "center", gap: 4 }}>
                                <ArrowUpRight size={14} /> Increases Risk
                              </span>
                            ) : (
                              <span style={{ color: "var(--green)", display: "flex", alignItems: "center", gap: 4 }}>
                                <ArrowDownRight size={14} /> Decreases Risk
                              </span>
                            )}
                          </td>
                          <td style={{ fontWeight: 600 }}>
                            {shapVal > 0 ? `+${shapVal.toFixed(4)}` : shapVal.toFixed(4)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="card" style={{ textAlign: "center", padding: 60 }}>
          <p style={{ color: "var(--text-muted)" }}>Select a GPU to view its SHAP explanation.</p>
        </div>
      )}
    </div>
  );
}
