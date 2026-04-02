"use client";

import { useEffect, useState } from "react";
import { getHistory, deleteRun, getHistoryExcelUrl, getRunDetail, getHistoryStatementPdfUrl } from "@/lib/api";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { formatRon } from "@/lib/formatting";
import { PageLayout, SectionCard, Button } from "@/components";
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

  const load = async () => {
    try { setRuns(await getHistory()); } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error"); }
  };
  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string) => {
    try { await deleteRun(id); setExpandedRun(null); await load(); } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error"); }
  };

  const toggleExpand = async (id: string) => {
    if (expandedRun === id) {
      setExpandedRun(null);
      setRunDetail(null);
      setSelectedCompany("");
      return;
    }
    try {
      const detail = await getRunDetail(id);
      setRunDetail({ results: detail.results, companies: detail.companies });
      setExpandedRun(id);
      setSelectedCompany("");
    } catch {
      setRunDetail(null);
      setExpandedRun(id);
    }
  };

  const months = monthNames(lang);

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
                  <span className="font-medium">{months[r.month - 1]} {r.year}</span>
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
                      {tr("history.download", lang)} Excel
                    </Button>
                  </a>
                  <Button variant="secondary" className="text-xs px-3 py-1"
                    onClick={() => toggleExpand(r.id)}>
                    {expandedRun === r.id ? "▲" : "PDF ▼"}
                  </Button>
                  <button onClick={() => handleDelete(r.id)}
                    className="text-red-500 hover:text-red-700 text-xs px-2">
                    {tr("history.delete", lang)}
                  </button>
                </div>
              </div>

              {expandedRun === r.id && (
                <div className="mt-3 pt-3 border-t dark:border-gray-700">
                  {runDetail && runDetail.companies ? (
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {tr("export.statement", lang)}:
                      </span>
                      <select value={selectedCompany}
                        onChange={(e) => setSelectedCompany(e.target.value)}
                        className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm
                                   bg-white dark:bg-gray-700 min-w-[220px]">
                        <option value="">{tr("export.select_company", lang)}</option>
                        {runDetail.companies.map((c) => {
                          const res = runDetail.results?.find((x) => x.company_id === c.id);
                          return (
                            <option key={c.id} value={c.id}>
                              {c.name} — {res ? formatRon(res.total) : ""}
                            </option>
                          );
                        })}
                      </select>
                      {selectedCompany && (
                        <a href={getHistoryStatementPdfUrl(r.id, selectedCompany)} download>
                          <Button variant="primary" className="text-xs px-3 py-1">
                            {tr("export.download_pdf", lang)}
                          </Button>
                        </a>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400">
                      Snapshot data not available for this run. Only new runs support company statements.
                    </p>
                  )}
                </div>
              )}
            </SectionCard>
          ))}
        </div>
      )}
    </PageLayout>
  );
}
