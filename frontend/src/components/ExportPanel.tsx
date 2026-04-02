"use client";

import { useState } from "react";
import { Button } from "./Button";
import { SectionCard } from "./SectionCard";
import { useApp } from "@/lib/AppContext";
import { tr } from "@/lib/i18n";
import { formatRon } from "@/lib/formatting";
import type { AllocationResult, Company, MonthlyInput } from "@/types";

const API = "http://localhost:8000";

interface ExportPanelProps {
  results: AllocationResult[];
  companies: Company[];
  runId: string;
  filename: string;
  month: number;
  year: number;
  language: string;
  monthlyInput: MonthlyInput;
}

export function ExportPanel({
  results, companies, runId, filename, month, year, language, monthlyInput,
}: ExportPanelProps) {
  const { lang } = useApp();
  const [selectedCompany, setSelectedCompany] = useState("");
  const [loading, setLoading] = useState("");

  const activeCompanies = companies.filter((c) => c.active);

  const downloadFile = async (endpoint: string, ext: string) => {
    if (!selectedCompany) return;
    setLoading(ext);
    try {
      const res = await fetch(`${API}/api/calculate/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_id: selectedCompany, month, year, language,
          monthly_input: monthlyInput,
        }),
      });
      if (!res.ok) throw new Error("Failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const company = activeCompanies.find((c) => c.id === selectedCompany);
      a.href = url;
      a.download = `Statement_${company?.name.replace(/\s/g, "_")}_${year}_${String(month).padStart(2, "0")}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally { setLoading(""); }
  };

  return (
    <SectionCard title={tr("export.title", lang)}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {tr("export.internal", lang)}:
          </span>
          <a href={`${API}/api/calculate/${runId}/excel`} download={filename}>
            <Button>{tr("export.download_report", lang)}</Button>
          </a>
        </div>

        <div className="border-t dark:border-gray-700 pt-4">
          <span className="text-sm text-gray-600 dark:text-gray-400 block mb-2">
            {tr("export.statement", lang)}:
          </span>
          <div className="flex items-center gap-3 flex-wrap">
            <select value={selectedCompany} onChange={(e) => setSelectedCompany(e.target.value)}
              className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700 min-w-[200px]">
              <option value="">{tr("export.select_company", lang)}</option>
              {activeCompanies.map((c) => {
                const r = results.find((r) => r.company_id === c.id);
                return (
                  <option key={c.id} value={c.id}>
                    {c.name} — {r ? formatRon(r.total) : ""}
                  </option>
                );
              })}
            </select>
            <Button variant="secondary" disabled={!selectedCompany || loading === "xlsx"}
              onClick={() => downloadFile("statement", "xlsx")}>
              {loading === "xlsx" ? "..." : tr("export.download_excel", lang)}
            </Button>
            <Button variant="secondary" disabled={!selectedCompany || loading === "pdf"}
              onClick={() => downloadFile("statement-pdf", "pdf")}>
              {loading === "pdf" ? "..." : tr("export.download_pdf", lang)}
            </Button>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}
