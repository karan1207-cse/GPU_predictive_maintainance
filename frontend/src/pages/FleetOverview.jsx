import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
} from "recharts";
import { Server, ShieldCheck, AlertTriangle, XOctagon } from "lucide-react";
import { getFleetSummary, getRiskDistribution, getAlerts } from "../services/api";

const RISK_COLORS = { low: "#10b981", medium: "#f59e0b", high: "#ef4444" };

function RiskBadge({ level }) {
  const cls = (level || "").toLowerCase();
  return (
    <span className={`badge ${cls}`}>
      <span className="badge-dot" />
      {level}
    </span>
  );
}

export default function FleetOverview() {
  const navigate = useNavigate();
  const [summary, setSummary]     = useState(null);
  const [riskDist, setRiskDist]   = useState(null);
  const [alerts, setAlerts]       = useState([]);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    Promise.all([
      getFleetSummary(),
      getRiskDistribution(),
      getAlerts({ limit: 10 }),
    ]).then(([s, r, a]) => {
      setSummary(s.data);
      setRiskDist(r.data);
      setAlerts(a.data);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-container"><div className="spinner" /></div>;

  const pieData = riskDist
    ? [
        { name: "Healthy", value: riskDist.low,    color: RISK_COLORS.low },
        { name: "Medium Risk", value: riskDist.medium, color: RISK_COLORS.medium },
        { name: "High Risk", value: riskDist.high,   color: RISK_COLORS.high },
      ]
    : [];

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Fleet Overview</h2>
        <p>Real-time GPU infrastructure health monitoring</p>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card total">
          <div className="kpi-icon"><Server size={40} /></div>
          <div className="kpi-label">Total GPUs</div>
          <div className="kpi-value">{summary?.total_gpus?.toLocaleString() || 0}</div>
        </div>
        <div className="kpi-card healthy">
          <div className="kpi-icon"><ShieldCheck size={40} /></div>
          <div className="kpi-label">Healthy</div>
          <div className="kpi-value">{summary?.healthy?.toLocaleString() || 0}</div>
        </div>
        <div className="kpi-card medium">
          <div className="kpi-icon"><AlertTriangle size={40} /></div>
          <div className="kpi-label">Medium Risk</div>
          <div className="kpi-value">{summary?.medium_risk?.toLocaleString() || 0}</div>
        </div>
        <div className="kpi-card high">
          <div className="kpi-icon"><XOctagon size={40} /></div>
          <div className="kpi-label">High Risk</div>
          <div className="kpi-value">{summary?.high_risk?.toLocaleString() || 0}</div>
        </div>
      </div>

      {/* Charts & Alerts Grid */}
      <div className="grid-2">
        {/* Risk Distribution Pie */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Risk Distribution</span>
          </div>
          <div style={{ width: "100%", height: 280, minHeight: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={110}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "var(--bg-secondary)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: "flex", justifyContent: "center", gap: 24, marginTop: 8 }}>
            {pieData.map((d) => (
              <span key={d.name} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text-secondary)" }}>
                <span style={{ width: 10, height: 10, borderRadius: "50%", background: d.color }} />
                {d.name}: {d.value}
              </span>
            ))}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Recent Alerts</span>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{alerts.length} alerts</span>
          </div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>GPU</th>
                  <th>Risk</th>
                  <th>Probability</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {alerts.slice(0, 8).map((a) => (
                    <tr key={a.prediction_id} onClick={() => navigate(`/gpu?id=${a.gpu_id}`)} style={{ cursor: "pointer" }}>
                    <td style={{ color: "var(--text-primary)", fontWeight: 500 }}>{a.gpu_id || "—"}</td>
                    <td><RiskBadge level={a.risk_level} /></td>
                    <td>{(a.failure_probability * 100).toFixed(1)}%</td>
                    <td style={{ fontSize: 11 }}>
                      {a.timestamp ? (() => { const d = new Date(a.timestamp); const pad = (n) => String(n).padStart(2, "0"); return `${pad(d.getDate())}/${pad(d.getMonth()+1)}/${d.getFullYear()}, ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; })() : "—"}
                    </td>
                  </tr>
                ))}
                {alerts.length === 0 && (
                  <tr><td colSpan={4} style={{ textAlign: "center", padding: 32 }}>No alerts</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
