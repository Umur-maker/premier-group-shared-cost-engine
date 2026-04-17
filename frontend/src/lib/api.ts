export const API_BASE = "http://localhost:8000";

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
  SaveResponse,
  MonthCheck,
  HistoryEntry,
  AllocationResult,
  PaymentEntry,
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

export const importCompanies = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/companies/import`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json() as Promise<{ status: string; count: number }>;
};

export const exportCompaniesUrl = () => `${API_BASE}/api/companies`;

export const deactivateCompany = (id: string) =>
  request<{ status: string }>(`/api/companies/${id}`, { method: "DELETE" });

// Settings
export const getSettings = () => request<Settings>("/api/settings");

export const saveSettings = (data: Partial<Settings>) =>
  request<{ status: string }>("/api/settings", {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const saveMeetingRoom = (data: { active: boolean; area_m2: number; floor: string }) =>
  request<{ status: string }>("/api/settings/meeting-room", {
    method: "PUT",
    body: JSON.stringify(data),
  });

// Calculate — preview only (no save)
export const calculatePreview = (data: {
  month: number; year: number; language: string; monthly_input: MonthlyInput;
}) => request<CalculateResponse>("/api/calculate", {
    method: "POST",
    body: JSON.stringify(data),
  });

// Save as official report
export const saveOfficial = (data: {
  month: number; year: number; language: string; monthly_input: MonthlyInput;
}) => request<SaveResponse>("/api/calculate/save", {
    method: "POST",
    body: JSON.stringify(data),
  });

// Check if month has official report
export const checkMonth = (year: number, month: number) =>
  request<MonthCheck>(`/api/calculate/check/${year}/${month}`);

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

export const recalculateRun = (runId: string) =>
  request<{ run_id: string; replaced: string | null; results: AllocationResult[] }>(
    `/api/history/${runId}/recalculate`, { method: "POST" }
  );

export const getStatementsZipUrl = (runId: string) =>
  `${API_BASE}/api/history/${runId}/statements-zip`;

export const getBackupUrl = () => `${API_BASE}/api/backup`;

export const listBackups = () =>
  request<{ backups: { id: string; timestamp: string; companies_count: number }[] }>("/api/backups");

export const restoreBackup = (backupId: string) =>
  request<{ status: string; backup_id: string }>(`/api/backups/${encodeURIComponent(backupId)}/restore`, {
    method: "POST",
  });

// Payments (ledger)
export const getRunPayments = (runId: string) =>
  request<PaymentEntry[]>(`/api/payments/run/${runId}`);

export const addPaymentEntry = (runId: string, data: {
  company_id: string; amount: number; date: string; note?: string;
}) => request<PaymentEntry>(`/api/payments/run/${runId}`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const deletePaymentEntry = (paymentId: string) =>
  request<{ status: string }>(`/api/payments/entry/${paymentId}`, { method: "DELETE" });

export const getCompanyBalance = (companyId: string) =>
  request<{ company_id: string; running_balance: number }>(`/api/payments/balance/${companyId}`);

export const getAllBalances = () =>
  request<Record<string, number>>("/api/payments/balances");
