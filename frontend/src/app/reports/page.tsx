"use client";

import { useEffect, useState } from "react";
import { getHistory, getRunDetail } from "@/lib/api";
import { formatRon } from "@/lib/formatting";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard, Button, DataTable } from "@/components";
import type { HistoryEntry, AllocationResult } from "@/types";

const EXPENSE_KEYS = [
  "electricity", "water", "garbage", "gas_hotel", "gas_ground_floor", "gas_first_floor",
  "consumables", "printer", "internet", "maintenance", "maintenance_vat", "rent", "rent_vat",
] as const;

export default function ReportsPage() {
  const { lang } = useApp();
  const [runs, setRuns] = useState<HistoryEntry[]>([]);
  const [selectedCompany, setSelectedCompany] = useState("all");
  const [fromMonth, setFromMonth] = useState(1);
  const [fromYear, setFromYear] = useState(new Date().getFullYear());
  const [toMonth, setToMonth] = useState(new Date().getMonth() + 1);
  const [toYear, setToYear] = useState(new Date().getFullYear());
  const [reportData, setReportData] = useState<AllocationResult[] | null>(null);
  const [companyNames, setCompanyNames] = useState<{ id: string; name: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const months = monthNames(lang);

  useEffect(() => {
    getHistory().then(setRuns).catch(() => setError(tr("error.backend_down", lang)));
  }, [lang]);

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setReportData(null);
    try {
      const filtered = runs.filter((r) => {
        const from = fromYear * 100 + fromMonth;
        const to = toYear * 100 + toMonth;
        const current = r.year * 100 + r.month;
        return current >= from && current <= to;
      });

      if (filtered.length === 0) {
        setError(tr("reports.no_data", lang));
        setLoading(false);
        return;
      }

      // Load full details for each run
      const details = await Promise.all(filtered.map((r) => getRunDetail(r.id)));

      // Collect unique companies
      const compMap = new Map<string, string>();
      details.forEach((d) => {
        (d.results || []).forEach((r) => compMap.set(r.company_id, r.company_name));
      });
      setCompanyNames(Array.from(compMap, ([id, name]) => ({ id, name })));

      // Aggregate results
      const aggregated = new Map<string, AllocationResult>();
      for (const detail of details) {
        for (const r of (detail.results || [])) {
          if (selectedCompany !== "all" && r.company_id !== selectedCompany) continue;
          const existing = aggregated.get(r.company_id);
          if (existing) {
            for (const key of EXPENSE_KEYS) {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              (existing as any)[key] += (r as any)[key] || 0;
            }
            existing.total += r.total;
          } else {
            aggregated.set(r.company_id, { ...r });
          }
        }
      }

      // Round
      const result = Array.from(aggregated.values()).map((r) => {
        for (const key of EXPENSE_KEYS) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (r as any)[key] = Math.round(((r as any)[key] || 0) * 100) / 100;
        }
        r.total = Math.round(r.total * 100) / 100;
        return r;
      });

      setReportData(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  const cols = [
    { key: "company_name", header: tr("table.company", lang) },
    ...EXPENSE_KEYS.map((k) => {
      const headerMap: Record<string, string> = {
        electricity: tr("table.elec", lang), water: tr("table.water", lang),
        garbage: tr("table.garb", lang), gas_hotel: tr("table.gas_h", lang),
        gas_ground_floor: tr("table.gas_gf", lang), gas_first_floor: tr("table.gas_ff", lang),
        consumables: tr("table.consum", lang), printer: tr("table.printer", lang),
        internet: tr("table.internet", lang), maintenance: tr("table.maint", lang),
        maintenance_vat: tr("table.maint_vat", lang), rent: tr("table.rent", lang),
        rent_vat: tr("table.rent_vat", lang),
      };
      return {
        key: k,
        header: headerMap[k] || k,
        align: "right" as const,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        render: (r: AllocationResult) => formatRon((r as any)[k] || 0),
      };
    }),
    { key: "total", header: tr("table.total", lang), align: "right" as const, bold: true,
      render: (r: AllocationResult) => formatRon(r.total) },
  ];

  return (
    <PageLayout title={tr("reports.title", lang)}>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      <SectionCard title={tr("reports.select_period", lang)}>
        <div className="flex items-end gap-4 flex-wrap">
          <div>
            <label className="block text-xs text-gray-500 mb-1">{tr("reports.from", lang)}</label>
            <div className="flex gap-2">
              <select value={fromMonth} onChange={(e) => setFromMonth(+e.target.value)}
                className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700">
                {months.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
              </select>
              <input type="number" value={fromYear} onChange={(e) => setFromYear(+e.target.value)}
                className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm w-20 bg-white dark:bg-gray-700" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">{tr("reports.to", lang)}</label>
            <div className="flex gap-2">
              <select value={toMonth} onChange={(e) => setToMonth(+e.target.value)}
                className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700">
                {months.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
              </select>
              <input type="number" value={toYear} onChange={(e) => setToYear(+e.target.value)}
                className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm w-20 bg-white dark:bg-gray-700" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">{tr("reports.company_filter", lang)}</label>
            <select value={selectedCompany} onChange={(e) => setSelectedCompany(e.target.value)}
              className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700 min-w-[180px]">
              <option value="all">{tr("reports.all_companies", lang)}</option>
              {companyNames.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? "..." : tr("reports.generate", lang)}
          </Button>
        </div>
      </SectionCard>

      {reportData && (
        <SectionCard title={tr("reports.period_total", lang)}>
          <DataTable columns={cols} data={reportData} keyField="company_id" />
          {reportData.length > 1 && (
            <div className="mt-3 text-right text-sm font-bold text-navy dark:text-blue-300">
              {tr("table.total", lang)}: {formatRon(reportData.reduce((s, r) => s + r.total, 0))}
            </div>
          )}
        </SectionCard>
      )}
    </PageLayout>
  );
}
