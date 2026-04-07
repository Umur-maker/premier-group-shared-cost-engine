"use client";

import { useEffect, useState } from "react";
import { getHistory, getRunDetail, getPayments, updatePayment, getBalances } from "@/lib/api";
import { formatRon } from "@/lib/formatting";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard, Button } from "@/components";
import type { HistoryEntry, AllocationResult, PaymentStatus, OutstandingBalance } from "@/types";

export default function ManagerPage() {
  const { lang } = useApp();
  const [runs, setRuns] = useState<HistoryEntry[]>([]);
  const [selectedRun, setSelectedRun] = useState<string>("");
  const [results, setResults] = useState<AllocationResult[]>([]);
  const [payments, setPayments] = useState<Record<string, PaymentStatus>>({});
  const [balances, setBalances] = useState<Record<string, OutstandingBalance>>({});
  const [error, setError] = useState("");
  const months = monthNames(lang);

  useEffect(() => {
    getHistory().then(setRuns).catch(() => setError(tr("error.backend_down", lang)));
  }, [lang]);

  const loadRun = async (runId: string) => {
    setSelectedRun(runId);
    setError("");
    try {
      const run = runs.find((r) => r.id === runId);
      if (!run) return;
      const detail = await getRunDetail(runId);
      setResults(detail.results || []);
      const payData = await getPayments(run.year, run.month);
      setPayments(payData);
      const balData = await getBalances(run.year, run.month);
      setBalances(balData);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  const togglePayment = async (companyId: string, currentlyPaid: boolean) => {
    const run = runs.find((r) => r.id === selectedRun);
    if (!run) return;
    const result = results.find((r) => r.company_id === companyId);
    try {
      await updatePayment(run.year, run.month, {
        company_id: companyId,
        paid: !currentlyPaid,
        paid_amount: result?.total || 0,
        paid_date: !currentlyPaid ? new Date().toISOString().slice(0, 10) : "",
      });
      const payData = await getPayments(run.year, run.month);
      setPayments(payData);
      const balData = await getBalances(run.year, run.month);
      setBalances(balData);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  const totalBilled = results.reduce((s, r) => s + r.total, 0);
  const totalPaid = results.reduce((s, r) => {
    const p = payments[r.company_id];
    return s + (p?.paid ? (p.paid_amount || r.total) : 0);
  }, 0);
  const totalOutstanding = Object.values(balances).reduce((s, b) => s + b.total_outstanding, 0);

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
          {/* Overview cards */}
          <div className="grid grid-cols-3 gap-4">
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
          </div>

          {/* Payment status table */}
          <SectionCard title={tr("manager.payment_status", lang)}>
            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-navy text-white">
                    <th className="p-2.5 text-left text-xs uppercase">{tr("table.company", lang)}</th>
                    <th className="p-2.5 text-right text-xs uppercase">{tr("manager.total_billed", lang)}</th>
                    <th className="p-2.5 text-center text-xs uppercase">{tr("manager.payment_status", lang)}</th>
                    <th className="p-2.5 text-right text-xs uppercase">{tr("manager.total_outstanding", lang)}</th>
                    <th className="p-2.5 text-center text-xs uppercase"></th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => {
                    const p = payments[r.company_id];
                    const isPaid = p?.paid || false;
                    const bal = balances[r.company_id];
                    return (
                      <tr key={r.company_id}
                        className={`${i % 2 === 0 ? "bg-white dark:bg-card-dark" : "bg-gray-50 dark:bg-gray-800/40"}
                          hover:bg-blue-50/50 dark:hover:bg-navy-light/10`}>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 font-medium">
                          {r.company_name}
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums">
                          {formatRon(r.total)}
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-center">
                          <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium
                            ${isPaid ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                                     : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"}`}>
                            {isPaid ? tr("manager.paid", lang) : tr("manager.unpaid", lang)}
                          </span>
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums">
                          {bal ? formatRon(bal.total_outstanding) : "—"}
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-center">
                          <Button
                            variant={isPaid ? "danger" : "primary"}
                            className="text-xs px-2 py-1"
                            onClick={() => togglePayment(r.company_id, isPaid)}
                          >
                            {isPaid ? tr("manager.mark_unpaid", lang) : tr("manager.mark_paid", lang)}
                          </Button>
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
