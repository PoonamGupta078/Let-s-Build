/**
 * Read-only client for the SecureTrace FastAPI backend.
 *
 * The backend serves the synthetic demo case (data/make_case.py). All
 * fund-flow amounts are estimates; the backend disclaimers are echoed in the
 * responses and rendered by the UI.
 */
import type {
  CutData,
  GraphData,
  OverviewData,
  SeeAlert,
  TraceData,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export interface HealthData {
  status: string;
  service: string;
  version: string;
  demo_mode: boolean;
  data_source: string;
}

export const api = {
  health: () => get<HealthData>("/api/health"),
  overview: () => get<OverviewData>("/api/overview"),
  alerts: () => get<SeeAlert[]>("/api/alerts"),
  graph: () => get<GraphData>("/api/graph"),
  trace: (seedAccount = "S") =>
    get<TraceData>(`/api/trace?seed_account=${encodeURIComponent(seedAccount)}`),
  cut: (seedAccount = "S", tAlert = "2026-01-01T10:20:00") =>
    get<CutData>(
      `/api/cut?seed_account=${encodeURIComponent(seedAccount)}&t_alert=${encodeURIComponent(tAlert)}`,
    ),
};
