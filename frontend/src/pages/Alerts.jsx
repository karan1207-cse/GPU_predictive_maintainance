import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, CheckCircle, Search } from "lucide-react";
import { getAlerts, postAcknowledge } from "../services/api";

function RiskBadge({ level }) {
  const cls = (level || "").toLowerCase();
  return (
    <span className={`badge ${cls}`}>
      <span className="badge-dot" />
      {level}
    </span>
  );
}

export default function Alerts() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = (selectedFilter) => {
    setLoading(true);
    getAlerts({ risk_level: selectedFilter, limit: 100 })
      .then((res) => {
        setAlerts(res.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAlerts(filter);
  }, [filter]);

  const handleToggleAcknowledge = (predictionId) => {
    postAcknowledge(predictionId)
      .then((res) => {
        const newAck = res.data.acknowledged;
        setAlerts((prev) =>
          prev.map((a) =>
            a.prediction_id === predictionId ? { ...a, acknowledged: newAck } : a
          )
        );
      })
      .catch((err) => {
        console.error("Failed to acknowledge alert:", err);
      });
  };

  const filteredAlerts = alerts.filter((a) => {
    const term = search.toLowerCase();
    const gpu = (a.gpu_id || "").toLowerCase();
    const host = (a.hostname || "").toLowerCase();
    return gpu.includes(term) || host.includes(term);
  });

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Alerts & Notifications</h2>
        <p>Active anomaly and risk alerts across the GPU fleet</p>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div className="filter-bar" style={{ marginBottom: 0 }}>
            {["ALL", "HIGH", "MEDIUM", "LOW"].map((lvl) => (
              <button
                key={lvl}
                className={`filter-btn ${filter === lvl ? "active" : ""}`}
                onClick={() => setFilter(lvl)}
              >
                {lvl === "ALL" ? "All Alerts" : `${lvl} Risk`}
              </button>
            ))}
          </div>

          <div style={{ position: "relative", minWidth: 240 }}>
            <input
              type="text"
              placeholder="Search by GPU ID or host..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 12px 8px 32px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border)",
                background: "var(--bg-secondary)",
                color: "var(--text-primary)",
                fontSize: 12,
                outline: "none",
              }}
            />
            <Search
              size={14}
              color="var(--text-muted)"
              style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)" }}
            />
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Fleet Alert Records</span>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Showing {filteredAlerts.length} items
          </span>
        </div>

        {loading ? (
          <div className="loading-container"><div className="spinner" /></div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Prediction ID</th>
                  <th>GPU Identifier</th>
                  <th>Host Node</th>
                  <th>Failure Risk</th>
                  <th>Level</th>
                  <th>Timestamp</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredAlerts.map((a) => {
                  const isAck = !!a.acknowledged;
                  return (
                    <tr key={a.prediction_id}>
                      <td style={{ fontFamily: "monospace", fontSize: 11, color: "var(--text-muted)" }}>
                        {a.prediction_id.slice(0, 8)}...
                      </td>
                      <td style={{ fontWeight: 600, color: "var(--text-primary)", cursor: "pointer" }}
                        onClick={() => navigate(`/gpu?id=${a.gpu_id}`)}
                      >{a.gpu_id || "—"}</td>
                      <td>{a.hostname || "—"}</td>
                      <td style={{ fontWeight: 600 }}>
                        {(a.failure_probability * 100).toFixed(1)}%
                      </td>
                      <td><RiskBadge level={a.risk_level} /></td>
                      <td style={{ fontSize: 12 }}>
                        {a.timestamp ? (() => { const d = new Date(a.timestamp); const pad = (n) => String(n).padStart(2, "0"); return `${pad(d.getDate())}/${pad(d.getMonth()+1)}/${d.getFullYear()}, ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; })() : "—"}
                      </td>
                      <td>
                        {isAck ? (
                          <span style={{ color: "var(--green)", fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
                            <CheckCircle size={14} /> Acknowledged
                          </span>
                        ) : (
                          <span style={{ color: "var(--yellow)", fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
                            <AlertTriangle size={14} /> Unresolved
                          </span>
                        )}
                      </td>
                      <td>
                        <button
                          className="filter-btn"
                          style={{
                            fontSize: 11,
                            padding: "4px 10px",
                            background: isAck ? "transparent" : "var(--accent-glow)",
                            borderColor: isAck ? "var(--border)" : "var(--accent)",
                            color: isAck ? "var(--text-secondary)" : "var(--accent-light)",
                          }}
                          onClick={() => handleToggleAcknowledge(a.prediction_id)}
                        >
                          {isAck ? "Mark Unresolved" : "Acknowledge"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {filteredAlerts.length === 0 && (
                  <tr>
                    <td colSpan={8} style={{ textAlign: "center", padding: 32, color: "var(--text-muted)" }}>
                      No alerts match the current filter criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
