import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Navbar from "./components/Navbar";
import FleetOverview from "./pages/FleetOverview";
import GpuDetails from "./pages/GpuDetails";
import Explainability from "./pages/Explainability";
import Alerts from "./pages/Alerts";
import ModelMonitoring from "./pages/ModelMonitoring";

export default function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<FleetOverview />} />
          <Route path="/gpu" element={<GpuDetails />} />
          <Route path="/explainability" element={<Explainability />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/monitoring" element={<ModelMonitoring />} />
        </Routes>
      </main>
    </div>
  );
}
