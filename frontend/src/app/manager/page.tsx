"use client";

import { useEffect, useState } from "react";
import { getHistory, getRunDetail, getRunPayments, getAllBalances } from "@/lib/api";
import { formatRon } from "@/lib/formatting";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard } from "@/components";
import type { HistoryEntry, AllocationResult, PaymentEntry } from "@/types";

export default function ManagerPage() {
  const { lang } = useApp();
  const [runs, setRuns] = useState<HistoryEntry[]>([]);
  const [selectedRun, setSelectedRun] = useState("");
  const [results, setResults] = useState<AllocationResult[]>([]);
  const [payments, setPayments] = useState<PaymentEntry[]>([]);
  const [balances, setBalances] = useState<Record<string, number>>({});
  const [error, setError] = useState("");
  const months = monthNames(lang);

  useEffect(() => {
    getHistory().then(setRuns).catch(() => setError(tr("error.backend_down", lang)));
  }, [lang]);

  const loadRun = async (runId: string) => {
    setSelectedRun(runId);
    setError("");
    try {
      const detail = await getRunDetail(runId);
      setResults(detail.results || []);
      const [payData, balData] = await Promise.all([
        getRunPayments(runId),
        getAllBalances(),
      ]);
      setPayments(payData);
      setBalances(balData);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  const totalBilled = results.reduce((s, r) => s + r.total, 0);
  const totalPaid = payments.reduce((s, p) => s + p.amount, 0);
  const totalOutstanding = Object.values(balances).reduce((s, b) => s + Math.max(0, b), 0);
  const totalCredit = Object.values(balances).reduce((s, b) => s + Math.min(0, b), 0);

  return (
    <PageLayout title={tr("manager.title", lang)}>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      <SectionCard title={tr("manager.select_month", lang)}>
        <select value={selectedRun} onChange={(e) => loadRun(e.target.value)}
          className="border dark:border-gray-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-gray-700 min-w-[250px]">
          <option value="">{tr("manager.select_month", lang)}...</option>
          {runs.map((r) => (
            <option key={r.id} value={r.id}>
              {months[r.month - 1]} {r.year} ({r.generated_at.slice(0, 10)})
            </option>
          ))}
        </select>
      </SectionCard>

      {selectedRun && results.length > 0 && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <SectionCard>
              <p className="text-xs text-gray-500 uppercase">{tr("manager.total_billed", lang)}</p>
              <p className="text-2xl font-bold text-navy dark:text-white mt-1">{formatRon(totalBilled)}</p>
            </SectionCard>
            <SectionCard>
              <p className="text-xs text-gray-500 uppercase">{tr("manager.total_paid", lang)}</p>
              <p className="text-2xl font-bold text-green-600 mt-1">{formatRon(totalPaid)}</p>
            </SectionCard>
            <SectionCard>
              <p className="text-xs text-gray-500 uppercase">{tr("manager.total_outstanding", lang)}</p>
              <p className="text-2xl font-bold text-red-600 mt-1">{formatRon(totalOutstanding)}</p>
            </SectionCard>
            <SectionCard>
              <p className="text-xs text-gray-500 uppercase">{tr("monthly.credit", lang)}</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">{formatRon(Math.abs(totalCredit))}</p>
            </SectionCard>
          </div>

          <SectionCard title={tr("manager.payment_status", lang)}>
            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-navy text-white">
                    <th className="p-2.5 text-left text-xs uppercase">{tr("table.company", lang)}</th>
                    <th className="p-2.5 text-right text-xs uppercase">{tr("monthly.amount_due", lang)}</th>
                    <th className="p-2.5 text-right text-xs uppercase">{tr("manager.total_paid", lang)}</th>
                    <th className="p-2.5 text-right text-xs uppercase">{tr("monthly.net_balance", lang)}</th>
                    <th className="p-2.5 text-left text-xs uppercase">{tr("monthly.payments", lang)}</th>
                  </tr>
                </thead>
                <tbody>
                  {results.filter(r => r.total > 0).map((r, i) => {
                    const companyPayments = payments.filter(p => p.company_id === r.company_id);
                    const paid = companyPayments.reduce((s, p) => s + p.amount, 0);
                    const bal = balances[r.company_id] || 0;

                    return (
                      <tr key={r.company_id}
                        className={`${i % 2 === 0 ? "bg-white dark:bg-card-dark" : "bg-gray-50/60 dark:bg-gray-800/40"}`}>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 font-medium">{r.company_name}</td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums">{formatRon(r.total)}</td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums text-green-600">{formatRon(paid)}</td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums">
                          <span className={bal > 0 ? "text-red-600 font-semibold" : bal < 0 ? "text-blue-600" : "text-green-600"}>
                            {bal > 0 ? formatRon(bal) : bal < 0 ? `${tr("monthly.credit", lang)}: ${formatRon(Math.abs(bal))}` : tr("manager.paid", lang)}
                          </span>
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-xs text-gray-500">
                          {companyPayments.length > 0
                            ? companyPayments.map(p => `${p.date}: ${formatRon(p.amount)}`).join(" | ")
                            : "—"
                          }
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </SectionCard>
        </>
      )}

      {selectedRun && results.length === 0 && (
        <SectionCard>
          <p className="text-gray-500 text-sm">{tr("manager.no_runs", lang)}</p>
        </SectionCard>
      )}
    </PageLayout>
  );
}
