/**
 * Lightweight typed API client for the admin workspace.
 * All requests automatically attach the stored JWT token.
 */
import type { AdminSnapshot } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

const TOKEN_KEY = "admin_token";

export function storeToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export async function adminLogin(
  email: string,
  password: string,
): Promise<{ access_token: string; role: string }> {
  return apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export interface BehaviourResponse {
  data_available_through: string;
  date_from: string;
  date_to: string;
  kpis: {
    active_customers: number;
    avg_session_seconds: number;
    most_interested_product: string | null;
    avg_engagement_pct: number;
  };
  segmentation: { segment: string; count: number }[];
  spending_patterns: { category: string; amount: number }[];
  income_patterns: { band: string; count: number }[];
  product_affinity: {
    product: string;
    views: number;
    clicks: number;
    interested_customers: number;
    engagement_pct: number;
  }[];
  session_analytics: {
    total_sessions: number;
    pages_per_session: number;
    returning_customers: number;
    avg_duration_seconds: number;
    sessions_by_month: { month: string; count: number }[];
  };
  page_visits: {
    page: string;
    visits: number;
    unique_customers: number;
    avg_time_seconds: number;
  }[];
  navigation_journeys: { path: string[]; sessions: number }[];
  customer_behaviour: {
    total: number;
    page: number;
    page_size: number;
    items: {
      customer_id: string;
      customer_code: string;
      name: string;
      segment: string;
      product_interest: string | null;
      avg_session_seconds: number;
      engagement_pct: number;
      top_spending_category: string | null;
      risk: string | null;
    }[];
  };
}

export interface FiltersResponse {
  segments: string[];
  products: string[];
  customers: { id: string; code: string; name: string }[];
}

export function fetchBehaviour(
  params: URLSearchParams,
): Promise<BehaviourResponse> {
  return apiFetch(`/analytics/behaviour?${params.toString()}`);
}

export function fetchFilters(search?: string): Promise<FiltersResponse> {
  const qs = search ? `?search=${encodeURIComponent(search)}` : "";
  return apiFetch(`/analytics/behaviour/filters${qs}`);
}

export interface OverviewResponse extends AdminSnapshot {
  summary: {
    totalCustomers: number;
    activeFraudAlerts: number;
    highRiskCustomers: number;
    openInvestigations: number;
    complianceAlerts: number;
    engagementPct: number;
  };
}

export function fetchAdminOverview(asOf?: string): Promise<OverviewResponse> {
  const qs = asOf ? `?as_of=${encodeURIComponent(asOf)}` : "";
  return apiFetch(`/analytics/overview${qs}`);
}
