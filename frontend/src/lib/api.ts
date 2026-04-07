export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
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
  AllocationResult,
  PaymentStatus,
  OutstandingBalance,
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

export const saveSettings = (data: Partial<Settings>) =>
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
  `${API_BASE}/api/calculate/${runId}/excel`;

// History
export const getHistory = () => request<HistoryEntry[]>("/api/history");

export const deleteRun = (runId: string) =>
  request<{ status: string }>(`/api/history/${runId}`, { method: "DELETE" });

export const getHistoryExcelUrl = (runId: string) =>
  `${API_BASE}/api/history/${runId}/excel`;

export const getRunDetail = (runId: string) =>
  request<HistoryEntry & { results: AllocationResult[]; companies: Company[] }>(
    `/api/history/${runId}`
  );

export const getHistoryStatementPdfUrl = (runId: string, companyId: string) =>
  `${API_BASE}/api/history/${runId}/statement-pdf?company_id=${encodeURIComponent(companyId)}`;

// Payments
export const getPayments = (year: number, month: number) =>
  request<Record<string, PaymentStatus>>(`/api/payments/${year}/${month}`);

export const updatePayment = (year: number, month: number, data: {
  company_id: string; paid: boolean; paid_amount?: number; paid_date?: string;
}) => request<{ status: string }>(`/api/payments/${year}/${month}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const getBalances = (year: number, month: number) =>
  request<Record<string, OutstandingBalance>>(`/api/payments/balances/${year}/${month}`);
