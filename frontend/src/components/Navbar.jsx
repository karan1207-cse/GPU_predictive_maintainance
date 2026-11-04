import { useLocation } from "react-router-dom";
import { Bell, RefreshCw } from "lucide-react";

const titles = {
  "/":               "Fleet Overview",
  "/gpu":            "GPU Details",
  "/explainability": "Explainability — SHAP Analysis",
  "/alerts":         "Alerts & Notifications",
  "/monitoring":     "Model Monitoring",
};

export default function Navbar() {
  const { pathname } = useLocation();
  const title = titles[pathname] || "Dashboard";

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <header className="navbar">
      <h2 className="navbar-title">{title}</h2>
      <div className="navbar-actions">
        <span className="navbar-badge" style={{ background: "rgba(99, 102, 241, 0.15)", color: "var(--accent-light)", fontSize: 11 }}>
          ORNL Summit Replay
        </span>
        <span className="navbar-badge" style={{ background: "var(--accent-glow)", color: "var(--accent-light)", fontSize: 11 }}>
          XGBoost v1
        </span>
        <button
          onClick={handleRefresh}
          className="filter-btn"
          title="Refresh dashboard data from backend"
          style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, padding: "4px 10px", height: 28 }}
        >
          <RefreshCw size={12} /> Refresh
        </button>
        <Bell size={18} color="var(--text-muted)" style={{ cursor: "pointer" }} />
      </div>
    </header>
  );
}

