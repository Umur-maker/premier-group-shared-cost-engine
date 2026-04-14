"use client";

import { useEffect, useState } from "react";
import { getHistory, getRunDetail, getRunPayments, addPaymentEntry, deletePaymentEntry, getAllBalances } from "@/lib/api";
import { formatRon, parseRonInput } from "@/lib/formatting";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard, Button } from "@/components";
import type { HistoryEntry, AllocationResult, PaymentEntry } from "@/types";

export default function PaymentsPage() {
  const { lang } = useApp();
  const [runs, setRuns] = useState<HistoryEntry[]>([]);
  const [selectedRun, setSelectedRun] = useState("");
  const [results, setResults] = useState<AllocationResult[]>([]);
  const [payments, setPayments] = useState<PaymentEntry[]>([]);
  const [balances, setBalances] = useState<Record<string, number>>({});
  const [error, setError] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);
  const [newPayment, setNewPayment] = useState({
    companyId: "", amount: "", date: new Date().toISOString().slice(0, 10), note: "",
  });
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
      const [payData, balData] = await Promise.all([getRunPayments(runId), getAllBalances()]);
      setPayments(payData);
      setBalances(balData);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
  };

  const handleAddPayment = async () => {
    if (!selectedRun || !newPayment.companyId || !newPayment.amount) return;
    try {
      const amount = parseRonInput(newPayment.amount);
      await addPaymentEntry(selectedRun, {
        company_id: newPayment.companyId, amount, date: newPayment.date, note: newPayment.note,
      });
      setNewPayment({ companyId: "", amount: "", date: new Date().toISOString().slice(0, 10), note: "" });
      setShowConfirm(false);
      const [payData, balData] = await Promise.all([getRunPayments(selectedRun), getAllBalances()]);
      setPayments(payData);
      setBalances(balData);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
  };

  const handleDeletePayment = async (paymentId: string) => {
    if (!confirm(tr("monthly.delete_payment_confirm", lang))) return;
    try {
      await deletePaymentEntry(paymentId);
      const [payData, balData] = await Promise.all([getRunPayments(selectedRun), getAllBalances()]);
      setPayments(payData);
      setBalances(balData);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
  };

  const activeWithDue = results.filter(r => r.total > 0);

  return (
    <PageLayout title={tr("payments.title", lang)}>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {/* Month selector */}
      <SectionCard title={tr("payments.select_month", lang)}>
        {runs.length === 0 ? (
          <p className="text-gray-500 text-sm">{tr("payments.no_reports", lang)}</p>
        ) : (
          <select value={selectedRun} onChange={(e) => loadRun(e.target.value)}
            className="border dark:border-gray-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-gray-700 min-w-[280px]">
            <option value="">{tr("payments.select_month", lang)}...</option>
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                {months[r.month - 1]} {r.year} — {r.company_count} {tr("history.companies_col", lang).toLowerCase()}
              </option>
            ))}
          </select>
        )}
      </SectionCard>

      {selectedRun && results.length > 0 && (
        <>
          {/* Balance overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {activeWithDue.map(r => {
              // Payments for THIS run only
              const companyPayments = payments.filter(p => p.company_id === r.company_id);
              const paidThisMonth = companyPayments.reduce((s, p) => s + p.amount, 0);
              const thisMonthBal = r.total - paidThisMonth;
              // Running balance across ALL months (from backend)
              const runningBal = balances[r.company_id] || 0;
              return (
                <SectionCard key={r.company_id} className="!p-3">
                  <div className="text-xs font-medium truncate mb-1">{r.company_name}</div>
                  <div className="text-xs text-gray-500">{tr("monthly.amount_due", lang)}: {formatRon(r.total)}</div>
                  <div className="text-xs text-green-600">{tr("manager.paid", lang)}: {formatRon(paidThisMonth)}</div>
                  <div className={`text-xs font-medium mt-1 ${thisMonthBal > 0 ? "text-orange-600" : thisMonthBal < 0 ? "text-blue-600" : "text-green-600"}`}>
                    {tr("payments.this_month", lang)}: {thisMonthBal > 0 ? formatRon(thisMonthBal) : thisMonthBal < 0 ? `-${formatRon(Math.abs(thisMonthBal))}` : formatRon(0)}
                  </div>
                  <div className={`text-sm font-bold mt-1 pt-1 border-t border-gray-200 dark:border-gray-700 ${runningBal > 0 ? "text-red-600" : runningBal < 0 ? "text-blue-600" : "text-green-600"}`}>
                    {tr("payments.running_total", lang)}: {runningBal > 0 ? formatRon(runningBal) : runningBal < 0 ? `${tr("monthly.credit", lang)}: ${formatRon(Math.abs(runningBal))}` : tr("manager.paid", lang)}
                  </div>
                </SectionCard>
              );
            })}
          </div>

          {/* Payment history table */}
          {payments.length > 0 && (
            <SectionCard title={tr("monthly.payments", lang)}>
              <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-navy text-white">
                      <th className="p-2.5 text-left text-xs uppercase">{tr("table.company", lang)}</th>
                      <th className="p-2.5 text-right text-xs uppercase">{tr("monthly.paid_amount", lang)}</th>
                      <th className="p-2.5 text-left text-xs uppercase">{tr("monthly.pay_date", lang)}</th>
                      <th className="p-2.5 text-left text-xs uppercase">{tr("monthly.pay_note", lang)}</th>
                      <th className="p-2.5 text-xs uppercase"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.map((p, i) => {
                      const name = results.find(r => r.company_id === p.company_id)?.company_name || p.company_id;
                      return (
                        <tr key={p.id} className={i % 2 === 0 ? "bg-white dark:bg-card-dark" : "bg-gray-50/60 dark:bg-gray-800/40"}>
                          <td className="p-2.5 border-b border-gray-100 dark:border-gray-700">{name}</td>
                          <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums font-medium text-green-600">{formatRon(p.amount)}</td>
                          <td className="p-2.5 border-b border-gray-100 dark:border-gray-700">{p.date}</td>
                          <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-gray-500">{p.note || "—"}</td>
                          <td className="p-2.5 border-b border-gray-100 dark:border-gray-700">
                            <button onClick={() => handleDeletePayment(p.id)}
                              className="text-xs text-red-600 hover:underline">✕</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </SectionCard>
          )}

          {/* Add payment form */}
          <SectionCard title={tr("payments.add_payment", lang)}>
            {!showConfirm ? (
              <div className="flex items-end gap-3 flex-wrap">
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">{tr("table.company", lang)}</label>
                  <select value={newPayment.companyId} onChange={(e) => setNewPayment(p => ({ ...p, companyId: e.target.value }))}
                    className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700 min-w-[200px]">
                    <option value="">...</option>
                    {activeWithDue.map(r => (
                      <option key={r.company_id} value={r.company_id}>
                        {r.company_name} — {tr("monthly.amount_due", lang)}: {formatRon(r.total)}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">{tr("monthly.paid_amount", lang)} (RON)</label>
                  <input value={newPayment.amount} onChange={(e) => setNewPayment(p => ({ ...p, amount: e.target.value }))}
                    placeholder="0" className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm w-32 bg-white dark:bg-gray-700" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">{tr("monthly.pay_date", lang)}</label>
                  <input type="date" value={newPayment.date} onChange={(e) => setNewPayment(p => ({ ...p, date: e.target.value }))}
                    className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">{tr("monthly.pay_note", lang)}</label>
                  <input value={newPayment.note} onChange={(e) => setNewPayment(p => ({ ...p, note: e.target.value }))}
                    placeholder="banka, nakit..." className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm w-36 bg-white dark:bg-gray-700" />
                </div>
                <Button disabled={!newPayment.companyId || !newPayment.amount}
                  onClick={() => setShowConfirm(true)}>
                  {tr("monthly.review_payment", lang)}
                </Button>
              </div>
            ) : (
              <div className="border-2 border-navy dark:border-blue-400 rounded-lg p-4">
                <p className="text-sm font-medium mb-2">{tr("monthly.confirm_payment", lang)}</p>
                <p className="text-sm">
                  {results.find(r => r.company_id === newPayment.companyId)?.company_name}:{" "}
                  <strong>{formatRon(parseRonInput(newPayment.amount))}</strong> — {newPayment.date}
                  {newPayment.note && ` (${newPayment.note})`}
                </p>
                <div className="flex gap-2 mt-3">
                  <Button onClick={handleAddPayment}>{tr("monthly.confirm_save", lang)}</Button>
                  <Button variant="secondary" onClick={() => setShowConfirm(false)}>{tr("companies.cancel", lang)}</Button>
                </div>
              </div>
            )}
          </SectionCard>
        </>
      )}
    </PageLayout>
  );
}
