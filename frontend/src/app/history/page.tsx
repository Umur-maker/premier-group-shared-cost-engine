"use client";

import { useEffect, useState } from "react";
import { getHistory, deleteRun, getHistoryExcelUrl } from "@/lib/api";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard } from "@/components";
import type { HistoryEntry } from "@/types";

export default function HistoryPage() {
  const { lang } = useApp();
  const [runs, setRuns] = useState<HistoryEntry[]>([]);
  const [error, setError] = useState("");

  const load = async () => {
    try { setRuns(await getHistory()); } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error"); }
  };
  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string) => {
    try { await deleteRun(id); await load(); } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error"); }
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
        <SectionCard>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700">
                <th className="text-left p-2 border-b dark:border-gray-600">{tr("history.period", lang)}</th>
                <th className="text-left p-2 border-b dark:border-gray-600">{tr("history.generated", lang)}</th>
                <th className="text-right p-2 border-b dark:border-gray-600">{tr("history.companies_col", lang)}</th>
                <th className="text-left p-2 border-b dark:border-gray-600">{tr("history.lang", lang)}</th>
                <th className="p-2 border-b dark:border-gray-600">{tr("history.actions", lang)}</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="p-2 border-b dark:border-gray-700 font-medium">
                    {months[r.month - 1]} {r.year}
                  </td>
                  <td className="p-2 border-b dark:border-gray-700 text-gray-500">
                    {r.generated_at.slice(0, 10)}
                  </td>
                  <td className="p-2 border-b dark:border-gray-700 text-right">{r.company_count}</td>
                  <td className="p-2 border-b dark:border-gray-700 uppercase text-gray-500">{r.language}</td>
                  <td className="p-2 border-b dark:border-gray-700 space-x-2">
                    <a href={getHistoryExcelUrl(r.id)} download
                      className="text-blue-600 hover:underline text-xs">{tr("history.download", lang)}</a>
                    <button onClick={() => handleDelete(r.id)}
                      className="text-red-600 hover:underline text-xs">{tr("history.delete", lang)}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>
      )}
    </PageLayout>
  );
}
