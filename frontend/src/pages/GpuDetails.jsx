import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from "recharts";
import { getGpuList, getGpuDetail, getPredictionHistory } from "../services/api";

function RiskBadge({ level }) {
  return (
    <span className={`badge ${(level || "").toLowerCase()}`}>
      <span className="badge-dot" />
      {level}
    </span>
  );
}

function formatNumber(val) {
  if (val == null || isNaN(val)) return "—";
  if (Math.abs(val) >= 1e9) return (val / 1e9).toFixed(2) + "B";
  if (Math.abs(val) >= 1e6) return (val / 1e6).toFixed(1) + "M";
  if (Math.abs(val) >= 1e3) return (val / 1e3).toFixed(1) + "k";
  return val.toFixed(1);
}

function formatTimestamp(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}, ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

export default function GpuDetails() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [gpuList, setGpuList]       = useState([]);
  const [selectedId, setSelectedId] = useState(searchParams.get("id") || null);
  const [detail, setDetail]         = useState(null);
  const [history, setHistory]       = useState([]);
  const [loading, setLoading]       = useState(true);
  const [search, setSearch]         = useState("");

  useEffect(() => {
    getGpuList({ limit: 200 })
      .then((r) => {
        setGpuList(r.data);
        const urlId = searchParams.get("id");
        if (urlId && r.data.find((g) => g.gpu_id === urlId)) {
          setSelectedId(urlId);
        } else if (!selectedId && r.data.length > 0) {
          const found476 = r.data.find((g) => g.gpu_id === "GPU-0476");
          setSelectedId(found476 ? found476.gpu_id : r.data[0].gpu_id);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Sync selectedId to URL
  useEffect(() => {
    if (selectedId) {
      setSearchParams({ id: selectedId }, { replace: true });
    }
  }, [selectedId]);

  useEffect(() => {
    if (!selectedId) return;
    Promise.all([
      getGpuDetail(selectedId),
      getPredictionHistory(selectedId),
    ]).then(([d, h]) => {
      setDetail(d.data);
      setHistory(
        (h.data || []).map((p) => ({
          ...p,
          time: p.timestamp ? new Date(p.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "",
          prob: +(p.failure_probability * 100).toFixed(1),
        }))
      );
    }).catch(console.error);
  }, [selectedId]);

  const handleSelectGpu = (gpuId) => {
    setSelectedId(gpuId);
  };

  const handleViewExplainability = () => {
    if (selectedId) {
      navigate(`/explainability?id=${selectedId}`);
    }
  };

  if (loading) return <div className="loading-container"><div className="spinner" /></div>;

  const filtered = gpuList.filter(
    (g) => g.gpu_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>GPU Details</h2>
        <p>Deep-dive telemetry and health metrics for individual GPUs</p>
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: "280px 1fr" }}>
        {/* GPU Selector */}
        <div className="card" style={{ maxHeight: "calc(100vh - 160px)", overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div className="card-header">
            <span className="card-title">GPU List</span>
          </div>
          <input
            type="text"
            placeholder="Search GPU..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: "100%",
              padding: "8px 12px",
              marginBottom: 12,
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              background: "var(--bg-secondary)",
              color: "var(--text-primary)",
              fontSize: 12,
              outline: "none",
            }}
          />
          <div style={{ overflowY: "auto", flex: 1 }}>
            {filtered.map((g) => (
              <div
                key={g.gpu_id}
                onClick={() => handleSelectGpu(g.gpu_id)}
                style={{
                  padding: "10px 12px",
                  marginBottom: 4,
                  borderRadius: "var(--radius-sm)",
                  cursor: "pointer",
                  background: selectedId === g.gpu_id ? "var(--accent-glow)" : "transparent",
                  borderLeft: selectedId === g.gpu_id ? "3px solid var(--accent)" : "3px solid transparent",
                  transition: "all 0.15s",
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                  {g.gpu_id}
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 4 }}>
                  <RiskBadge level={g.risk_level} />
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                    {(g.failure_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Detail Panel */}
        <div>
          {detail ? (
            <>
              {/* Header */}
              <div className="card" style={{ marginBottom: 20 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div>
                    <h3 style={{ fontSize: 20, fontWeight: 700 }}>{detail.gpu_id}</h3>
                    <p style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 4 }}>
                      Host: {detail.hostname || "—"} · Serial: {detail.serial || "—"}
                    </p>
                    {detail.last_seen && (
                      <p style={{ color: "var(--text-muted)", fontSize: 11, marginTop: 2 }}>
                        Last Recorded: {formatTimestamp(detail.last_seen)}
                      </p>
                    )}
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <RiskBadge level={detail.risk_level} />
                    <div style={{ fontSize: 24, fontWeight: 800, marginTop: 4, color: "var(--text-primary)" }}>
                      {(detail.failure_probability * 100).toFixed(1)}%
                    </div>
                    <button
                      className="filter-btn"
                      style={{ marginTop: 8, fontSize: 11, padding: "4px 12px" }}
                      onClick={handleViewExplainability}
                    >
                      View SHAP Analysis →
                    </button>
                  </div>
                </div>
              </div>

              {/* Gauges */}
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="card-header">
                  <span className="card-title">Telemetry Gauges</span>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Observed Metrics</span>
                </div>
                <div className="gauge-grid">
                  <div className="gauge">
                    <div className="gauge-value" title={detail.gpu_usage != null ? detail.gpu_usage.toLocaleString() : ""}>
                      {formatNumber(detail.gpu_usage)}
                    </div>
                    <div className="gauge-label">Cumulative Usage</div>
                    <div className="gauge-unit">cycles</div>
                  </div>
                  <div className="gauge">
                    <div className="gauge-value" title={detail.gpu_energy != null ? detail.gpu_energy.toLocaleString() : ""}>
                      {formatNumber(detail.gpu_energy)}
                    </div>
                    <div className="gauge-label">Cumulative Energy</div>
                    <div className="gauge-unit">J</div>
                  </div>
                  <div className="gauge">
                    <div className="gauge-value">
                      {detail.power_max_1min != null ? detail.power_max_1min.toFixed(0) : "—"}
                    </div>
                    <div className="gauge-label">Max Power (1m)</div>
                    <div className="gauge-unit">W</div>
                  </div>
                  <div className="gauge">
                    <div className="gauge-value">
                      {detail.core_temp_max_15min != null ? detail.core_temp_max_15min.toFixed(0) : "—"}
                    </div>
                    <div className="gauge-label">Core Temp (15m)</div>
                    <div className="gauge-unit">°C</div>
                  </div>
                  <div className="gauge">
                    <div className="gauge-value">
                      {detail.mem_temp_max_5min != null ? detail.mem_temp_max_5min.toFixed(0) : "—"}
                    </div>
                    <div className="gauge-label">Mem Temp (5m)</div>
                    <div className="gauge-unit">°C</div>
                  </div>
                </div>
              </div>

              {/* History Chart */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">Failure Probability History</span>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                    {history.length} record{history.length !== 1 ? "s" : ""}
                  </span>
                </div>
                {history.length > 0 ? (
                  <div style={{ width: "100%", height: 280, minHeight: 280 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={history} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(75,85,99,0.2)" />
                        <XAxis dataKey="time" stroke="var(--text-muted)" tick={{ fontSize: 10 }} />
                        <YAxis domain={[0, 100]} stroke="var(--text-muted)" tick={{ fontSize: 10 }} unit="%" />
                        <Tooltip
                          contentStyle={{
                            background: "var(--bg-secondary)",
                            border: "1px solid var(--border)",
                            borderRadius: 8,
                            fontSize: 12,
                          }}
                          formatter={(value) => [`${value}%`, "Failure Probability"]}
                        />
                        <ReferenceLine
                          y={50}
                          stroke="var(--red)"
                          strokeDasharray="4 4"
                          label={{ value: "HIGH (50%)", fill: "var(--red)", fontSize: 10, position: "insideTopRight" }}
                        />
                        <ReferenceLine
                          y={20}
                          stroke="var(--yellow)"
                          strokeDasharray="4 4"
                          label={{ value: "MEDIUM (20%)", fill: "var(--yellow)", fontSize: 10, position: "insideTopRight" }}
                        />
                        <Line
                          type="monotone"
                          dataKey="prob"
                          stroke="var(--accent)"
                          strokeWidth={2}
                          dot={{ r: 4, fill: "var(--accent)" }}
                          activeDot={{ r: 6 }}
                          name="Failure %"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <p style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                    No historical predictions available for this GPU.
                  </p>
                )}
              </div>
            </>
          ) : (
            <div className="card" style={{ textAlign: "center", padding: 60 }}>
              <p style={{ color: "var(--text-muted)" }}>Select a GPU from the list</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
