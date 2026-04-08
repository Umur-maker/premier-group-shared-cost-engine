"use client";

import { useEffect, useState } from "react";
import { getHistory, deleteRun, getHistoryExcelUrl, getRunDetail, getHistoryStatementPdfUrl } from "@/lib/api";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { formatRon } from "@/lib/formatting";
import { PageLayout, SectionCard, Button, DataTable } from "@/components";
import type { HistoryEntry, AllocationResult, Company } from "@/types";

export default function HistoryPage() {
  const { lang } = useApp();
  const [runs, setRuns] = useState<HistoryEntry[]>([]);
  const [error, setError] = useState("");
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [runDetail, setRunDetail] = useState<{
    results: AllocationResult[];
    companies: Company[];
  } | null>(null);
  const [selectedCompany, setSelectedCompany] = useState("");
  const [previewTab, setPreviewTab] = useState("summary");

  const load = async () => {
    try { setRuns(await getHistory()); } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error"); }
  };
  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string) => {
    if (!confirm(tr("history.confirm_delete", lang))) return;
    try { await deleteRun(id); setExpandedRun(null); await load(); } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error"); }
  };

  const toggleExpand = async (id: string) => {
    if (expandedRun === id) {
      setExpandedRun(null); setRunDetail(null); setSelectedCompany(""); return;
    }
    try {
      const detail = await getRunDetail(id);
      setRunDetail({ results: detail.results, companies: detail.companies });
      setExpandedRun(id); setSelectedCompany(""); setPreviewTab("summary");
    } catch {
      setRunDetail(null); setExpandedRun(id);
    }
  };

  const months = monthNames(lang);

  const detailCols = [
    { key: "company_name", header: tr("table.company", lang) },
    { key: "electricity", header: tr("table.elec", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.electricity) },
    { key: "water", header: tr("table.water", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.water) },
    { key: "garbage", header: tr("table.garb", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.garbage) },
    { key: "gas_hotel", header: tr("table.gas_h", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.gas_hotel) },
    { key: "gas_ground_floor", header: tr("table.gas_gf", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.gas_ground_floor) },
    { key: "gas_first_floor", header: tr("table.gas_ff", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.gas_first_floor) },
    { key: "consumables", header: tr("table.consum", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.consumables) },
    { key: "printer", header: tr("table.printer", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.printer) },
    { key: "internet", header: tr("table.internet", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.internet) },
    { key: "maintenance", header: tr("table.maint", lang), align: "right" as const, render: (r: AllocationResult) => formatRon((r.maintenance || 0) + (r.maintenance_vat || 0)) },
    { key: "rent", header: tr("table.rent", lang), align: "right" as const, render: (r: AllocationResult) => formatRon((r.rent || 0) + (r.rent_vat || 0)) },
    { key: "total", header: tr("table.total", lang), align: "right" as const, bold: true, render: (r: AllocationResult) => formatRon(r.total) },
  ];

  return (
    <PageLayout title={tr("history.title", lang)}>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {runs.length === 0 ? (
        <SectionCard>
          <p className="text-gray-500 text-sm">{tr("history.empty", lang)}</p>
        </SectionCard>
      ) : (
        <div className="space-y-2">
          {runs.map((r) => (
            <SectionCard key={r.id}>
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium">
                    {(r.month >= 1 && r.month <= 12 ? months[r.month - 1] : `?${r.month}`)} {r.year}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400 text-xs ml-3">
                    {tr("history.generated", lang)}: {r.generated_at.slice(0, 10)}
                  </span>
                  <span className="text-gray-400 text-xs ml-3">
                    {r.company_count} {tr("history.companies_col", lang).toLowerCase()}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <a href={getHistoryExcelUrl(r.id)} download>
                    <Button variant="secondary" className="text-xs px-3 py-1">
                      Excel
                    </Button>
                  </a>
                  <Button variant={expandedRun === r.id ? "primary" : "secondary"} className="text-xs px-3 py-1"
                    onClick={() => toggleExpand(r.id)}>
                    {expandedRun === r.id ? "▲ Close" : "▼ Details"}
                  </Button>
                  <button onClick={() => handleDelete(r.id)}
                    className="text-red-500 hover:text-red-700 text-xs px-2">
                    {tr("history.delete", lang)}
                  </button>
                </div>
              </div>

              {/* Expanded detail view */}
              {expandedRun === r.id && runDetail && runDetail.results && (
                <div className="mt-4 pt-4 border-t dark:border-gray-700 space-y-4">
                  {/* Preview tabs */}
                  <div className="flex gap-2">
                    {["summary", "detailed", "totals"].map((tab) => (
                      <button key={tab} onClick={() => setPreviewTab(tab)}
                        className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                          previewTab === tab
                            ? "bg-navy text-white"
                            : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                        }`}>
                        {tab === "summary" ? tr("monthly.tab_summary", lang)
                          : tab === "detailed" ? tr("monthly.tab_detailed", lang)
                          : tr("monthly.tab_totals", lang)}
                      </button>
                    ))}
                  </div>

                  {previewTab === "summary" && (
                    <DataTable
                      columns={[
                        { key: "company_name", header: tr("table.company", lang) },
                        { key: "total", header: tr("table.total", lang), align: "right", bold: true,
                          render: (r: AllocationResult) => formatRon(r.total) },
                      ]}
                      data={runDetail.results} keyField="company_id"
                    />
                  )}

                  {previewTab === "detailed" && (
                    <DataTable columns={detailCols} data={runDetail.results} keyField="company_id" />
                  )}

                  {previewTab === "totals" && (
                    <div className="space-y-2">
                      {[
                        ["electricity", tr("field.electricity", lang)],
                        ["water", tr("field.water", lang)],
                        ["garbage", tr("field.garbage", lang)],
                        ["gas_hotel", "Gas (Hotel)"],
                        ["gas_ground_floor", "Gas (GF)"],
                        ["gas_first_floor", "Gas (1F)"],
                        ["consumables", tr("field.consumables", lang)],
                        ["printer", tr("field.printer", lang)],
                        ["internet", tr("field.internet", lang)],
                        ["maintenance", tr("table.maint", lang)],
                        ["rent", tr("table.rent", lang)],
                      ].map(([key, label]) => {
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        let total = runDetail.results.reduce((s, r) => s + ((r as any)[key] || 0), 0);
                        // Include VAT for maintenance and rent
                        if (key === "maintenance") total += runDetail.results.reduce((s, r) => s + (r.maintenance_vat || 0), 0);
                        if (key === "rent") total += runDetail.results.reduce((s, r) => s + (r.rent_vat || 0), 0);
                        if (total === 0) return null;
                        return (
                          <div key={key} className="flex justify-between items-center py-1 border-b border-gray-100 dark:border-gray-700">
                            <span className="text-sm">{label}</span>
                            <span className="text-sm font-medium tabular-nums">{formatRon(total)}</span>
                          </div>
                        );
                      })}
                      <div className="flex justify-between items-center py-2 border-t-2 border-navy dark:border-blue-400">
                        <span className="text-sm font-bold text-navy dark:text-white">{tr("table.total", lang)}</span>
                        <span className="text-lg font-bold text-navy dark:text-white tabular-nums">
                          {formatRon(runDetail.results.reduce((s, r) => s + r.total, 0))}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* PDF statement section */}
                  <div className="pt-3 border-t dark:border-gray-700">
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {tr("export.statement", lang)}:
                      </span>
                      <select value={selectedCompany}
                        onChange={(e) => setSelectedCompany(e.target.value)}
                        className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm
                                   bg-white dark:bg-gray-700 min-w-[220px]">
                        <option value="">{tr("export.select_company", lang)}</option>
                        {runDetail.results.filter(x => x.total > 0).map((x) => (
                          <option key={x.company_id} value={x.company_id}>
                            {x.company_name} — {formatRon(x.total)}
                          </option>
                        ))}
                      </select>
                      {selectedCompany && (
                        <a href={getHistoryStatementPdfUrl(r.id, selectedCompany)} download>
                          <Button className="text-xs px-3 py-1">
                            {tr("export.download_pdf", lang)}
                          </Button>
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {expandedRun === r.id && (!runDetail || !runDetail.results) && (
                <div className="mt-3 pt-3 border-t dark:border-gray-700">
                  <p className="text-xs text-gray-400">{tr("history.snapshot_unavailable", lang)}</p>
                </div>
              )}
            </SectionCard>
          ))}
        </div>
      )}
    </PageLayout>
  );
}
