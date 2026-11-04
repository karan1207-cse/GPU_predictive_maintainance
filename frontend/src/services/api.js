import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// ── Core endpoints ──
export const getHealth       = () => api.get("/health");
export const getModelInfo    = () => api.get("/model-info");
export const postPredict     = (data) => api.post("/predict", data);
export const postExplain     = (data) => api.post("/explain", data);

// ── Dashboard endpoints ──
export const getFleetSummary      = () => api.get("/dashboard/summary");
export const getGpuList           = (params) => api.get("/dashboard/gpus", { params });
export const getAlerts            = (params) => api.get("/dashboard/alerts", { params });
export const postAcknowledge      = (predictionId) => api.post(`/dashboard/alerts/${predictionId}/acknowledge`);
export const getGpuDetail         = (gpuId) => api.get(`/dashboard/gpu/${gpuId}`);
export const getGpuExplain        = (gpuId) => api.get(`/dashboard/gpu/${gpuId}/explain`);
export const getRiskDistribution  = () => api.get("/dashboard/risk-distribution");
export const getPredictionHistory = (gpuId) => api.get(`/dashboard/prediction-history/${gpuId}`);
export const getModelMonitoring   = () => api.get("/dashboard/model-monitoring");

export default api;
