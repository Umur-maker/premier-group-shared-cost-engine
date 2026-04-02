"use client";

import { useState } from "react";
import { Button } from "./Button";
import { SectionCard } from "./SectionCard";
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
  const [selectedCompany, setSelectedCompany] = useState("");
  const [stmtLoading, setStmtLoading] = useState(false);

  const activeCompanies = companies.filter((c) => c.active);

  const downloadStatement = async () => {
    if (!selectedCompany) return;
    setStmtLoading(true);
    try {
      const res = await fetch(`${API}/api/calculate/statement`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_id: selectedCompany,
          month, year, language,
          monthly_input: monthlyInput,
        }),
      });
      if (!res.ok) throw new Error("Failed to generate statement");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const company = activeCompanies.find((c) => c.id === selectedCompany);
      a.href = url;
      a.download = `Statement_${company?.name.replace(/\s/g, "_")}_${year}_${String(month).padStart(2, "0")}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setStmtLoading(false);
    }
  };

  return (
    <SectionCard title="Export">
      <div className="space-y-4">
        {/* Internal report */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600">Internal Report (all companies):</span>
          <a href={`${API}/api/calculate/${runId}/excel`} download={filename}>
            <Button variant="primary">Download {filename}</Button>
          </a>
        </div>

        {/* Company statement */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600">Company Statement:</span>
          <select
            value={selectedCompany}
            onChange={(e) => setSelectedCompany(e.target.value)}
            className="border border-gray-300 rounded px-2 py-1.5 text-sm"
          >
            <option value="">Select company...</option>
            {activeCompanies.map((c) => {
              const r = results.find((r) => r.company_id === c.id);
              return (
                <option key={c.id} value={c.id}>
                  {c.name} — {r?.total.toFixed(2)} RON
                </option>
              );
            })}
          </select>
          <Button
            onClick={downloadStatement}
            disabled={!selectedCompany || stmtLoading}
            variant="secondary"
          >
            {stmtLoading ? "Generating..." : "Download Statement"}
          </Button>
        </div>
      </div>
    </SectionCard>
  );
}
