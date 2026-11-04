import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Cpu, Brain, AlertTriangle, Activity, Zap,
} from "lucide-react";

const links = [
  { to: "/",              icon: LayoutDashboard, label: "Fleet Overview" },
  { to: "/gpu",           icon: Cpu,             label: "GPU Details" },
  { to: "/explainability",icon: Brain,           label: "Explainability" },
  { to: "/alerts",        icon: AlertTriangle,   label: "Alerts" },
  { to: "/monitoring",    icon: Activity,        label: "Model Monitoring" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>
          <span className="logo-icon"><Zap size={18} color="#fff" /></span>
          GPU Health Platform
        </h1>
        <span>Predictive Failure Detection</span>
      </div>

      <nav className="sidebar-nav">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            <l.icon size={18} />
            {l.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 11, color: "var(--text-muted)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span className="status-dot" />
            <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>Telemetry Replay Mode</span>
          </div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", opacity: 0.9 }}>
            Data Source: ORNL Summit GPU Telemetry
          </div>
          <div style={{ fontSize: 10, color: "var(--accent-light)", opacity: 0.9 }}>
            Historical telemetry / prediction replay
          </div>
        </div>
      </div>
    </aside>
  );
}
