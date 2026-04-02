const API = "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

import type {
  Company,
  Settings,
  MonthlyInput,
  CalculateResponse,
  HistoryEntry,
} from "@/types";

// Companies
export const getCompanies = () => request<Company[]>("/api/companies");

export const createCompany = (data: Partial<Company>) =>
  request<Company>("/api/companies", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateCompany = (id: string, data: Partial<Company>) =>
  request<{ status: string }>(`/api/companies/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const deactivateCompany = (id: string) =>
  request<{ status: string }>(`/api/companies/${id}`, { method: "DELETE" });

// Settings
export const getSettings = () => request<Settings>("/api/settings");

export const saveSettings = (data: Settings) =>
  request<{ status: string }>("/api/settings", {
    method: "PUT",
    body: JSON.stringify(data),
  });

// Calculate
export const calculate = (data: {
  month: number;
  year: number;
  language: string;
  monthly_input: MonthlyInput;
}) => request<CalculateResponse>("/api/calculate", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const getExcelUrl = (runId: string) =>
  `${API}/api/calculate/${runId}/excel`;

// History
export const getHistory = () => request<HistoryEntry[]>("/api/history");

export const deleteRun = (runId: string) =>
  request<{ status: string }>(`/api/history/${runId}`, { method: "DELETE" });

export const getHistoryExcelUrl = (runId: string) =>
  `${API}/api/history/${runId}/excel`;
