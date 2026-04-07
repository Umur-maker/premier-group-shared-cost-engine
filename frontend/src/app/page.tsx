"use client";

import { useState, useEffect } from "react";
import { calculatePreview, saveOfficial, checkMonth, getCompanies, getRunPayments, addPaymentEntry, deletePaymentEntry, getAllBalances } from "@/lib/api";
import { formatRon, parseRonInput } from "@/lib/formatting";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard, MoneyInput, DataTable, Button, ExportPanel } from "@/components";
import type { MonthlyInput, AllocationResult, Company, PaymentEntry } from "@/types";

const INVOICE_KEYS: (keyof MonthlyInput)[] = [
  "electricity_total", "water_total", "garbage_total",
  "hotel_gas_total", "ground_floor_gas_total", "first_floor_gas_total",
];
const EXTERNAL_KEYS: (keyof MonthlyInput)[] = [
  "external_electricity", "external_water", "external_garbage",
  "external_hotel_gas", "external_gf_gas", "external_ff_gas",
];
const NEW_COST_KEYS: (keyof MonthlyInput)[] = [
  "consumables_total", "drinking_water_total", "printer_total", "internet_total",
];
const INVOICE_I18N = [
  "field.electricity", "field.water", "field.garbage",
  "field.hotel_gas", "field.gf_gas", "field.ff_gas",
];
const EXTERNAL_I18N = [
  "field.ext_electricity", "field.ext_water", "field.ext_garbage",
  "field.ext_hotel_gas", "field.ext_gf_gas", "field.ext_ff_gas",
];
const NEW_COST_I18N = [
  "field.consumables", "field.drinking_water", "field.printer", "field.internet",
];

type PageState = "input" | "preview" | "saved";

export default function MonthlyInputPage() {
  const { lang } = useApp();
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [raw, setRaw] = useState<Record<string, string>>({});
  const [results, setResults] = useState<AllocationResult[] | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [runId, setRunId] = useState("");
  const [filename, setFilename] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [frozenInput, setFrozenInput] = useState<MonthlyInput | null>(null);
  const [pageState, setPageState] = useState<PageState>("input");
  const [previewTab, setPreviewTab] = useState("summary");

  // Payment state
  const [payments, setPayments] = useState<PaymentEntry[]>([]);
  const [balances, setBalances] = useState<Record<string, number>>({});
  const [newPayment, setNewPayment] = useState<{ companyId: string; amount: string; date: string; note: string }>({
    companyId: "", amount: "", date: new Date().toISOString().slice(0, 10), note: "",
  });
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    getCompanies().then(setCompanies).catch(() => setError(tr("error.backend_down", lang)));
  }, [lang]);

  const buildInput = (): MonthlyInput => {
    const mi: Record<string, number> = {};
    for (const k of [...INVOICE_KEYS, ...EXTERNAL_KEYS, ...NEW_COST_KEYS]) mi[k] = parseRonInput(raw[k] || "");
    return mi as unknown as MonthlyInput;
  };

  // Step 1: Preview
  const handlePreview = async () => {
    setError(""); setResults(null); setLoading(true);
    try {
      const mi = buildInput();
      const res = await calculatePreview({ month, year, language: lang, monthly_input: mi });
      setResults(res.results); setFilename(res.filename); setFrozenInput(mi);
      setPageState("preview");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally { setLoading(false); }
  };

  // Step 2: Save
  const handleSave = async () => {
    if (!frozenInput) return;
    setError(""); setLoading(true);
    try {
      // Check if month already has a report
      const check = await checkMonth(year, month);
      if (check.exists) {
        if (!confirm(tr("monthly.replace_warning", lang))) {
          setLoading(false);
          return;
        }
      }
      const res = await saveOfficial({ month, year, language: lang, monthly_input: frozenInput });
      setRunId(res.run_id); setFilename(res.filename); setResults(res.results);
      setPageState("saved");
      // Load payments + balances
      const [payData, balData] = await Promise.all([
        getRunPayments(res.run_id),
        getAllBalances(),
      ]);
      setPayments(payData);
      setBalances(balData);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally { setLoading(false); }
  };

  // Add payment entry
  const handleAddPayment = async () => {
    if (!runId || !newPayment.companyId || !newPayment.amount) return;
    try {
      const amount = parseRonInput(newPayment.amount);
      await addPaymentEntry(runId, {
        company_id: newPayment.companyId, amount, date: newPayment.date, note: newPayment.note,
      });
      setNewPayment({ companyId: "", amount: "", date: new Date().toISOString().slice(0, 10), note: "" });
      setShowConfirm(false);
      const [payData, balData] = await Promise.all([getRunPayments(runId), getAllBalances()]);
      setPayments(payData);
      setBalances(balData);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
  };

  const handleDeletePayment = async (paymentId: string) => {
    if (!confirm(tr("monthly.delete_payment_confirm", lang))) return;
    try {
      await deletePaymentEntry(paymentId);
      const [payData, balData] = await Promise.all([getRunPayments(runId), getAllBalances()]);
      setPayments(payData);
      setBalances(balData);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
  };

  const months = monthNames(lang);
  const cols = [
    { key: "company_name", header: tr("table.company", lang) },
    { key: "electricity", header: tr("table.elec", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.electricity) },
    { key: "water", header: tr("table.water", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.water) },
    { key: "garbage", header: tr("table.garb", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.garbage) },
    { key: "gas_hotel", header: tr("table.gas_h", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.gas_hotel) },
    { key: "gas_ground_floor", header: tr("table.gas_gf", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.gas_ground_floor) },
    { key: "gas_first_floor", header: tr("table.gas_ff", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.gas_first_floor) },
    { key: "consumables", header: tr("table.consum", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.consumables) },
    { key: "drinking_water", header: tr("table.dw", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.drinking_water) },
    { key: "printer", header: tr("table.printer", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.printer) },
    { key: "internet", header: tr("table.internet", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.internet) },
    { key: "maintenance", header: tr("table.maint", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.maintenance) },
    { key: "hotel_rent", header: tr("table.rent", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.hotel_rent) },
    { key: "total", header: tr("table.total", lang), align: "right" as const, bold: true, render: (r: AllocationResult) => formatRon(r.total) },
  ];

  const activeCompaniesWithDue = results?.filter(r => r.total > 0) || [];

  return (
    <PageLayout title={tr("monthly.title", lang)}>
      {/* Period selector */}
      <SectionCard>
        <div className="flex gap-4 items-end">
          <div>
            <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">{tr("monthly.month", lang)}</label>
            <select value={month} onChange={(e) => { setMonth(+e.target.value); setPageState("input"); setResults(null); }}
              className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700">
              {months.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">{tr("monthly.year", lang)}</label>
            <input type="number" value={year} onChange={(e) => { setYear(+e.target.value); setPageState("input"); setResults(null); }}
              className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm w-24 bg-white dark:bg-gray-700" />
          </div>
          {pageState !== "input" && (
            <Button variant="secondary" onClick={() => { setPageState("input"); setResults(null); setRunId(""); }}>
              {tr("monthly.back_to_input", lang)}
            </Button>
          )}
        </div>
      </SectionCard>

      {/* Input section — only visible in input state */}
      {pageState === "input" && (
        <>
          <SectionCard title={tr("monthly.invoices", lang)}>
            <div className="grid grid-cols-3 gap-4">
              {INVOICE_KEYS.map((k, i) => (
                <MoneyInput key={k} label={tr(INVOICE_I18N[i], lang)}
                  value={raw[k] || ""} onChange={(v) => setRaw((p) => ({ ...p, [k]: v }))}
                  placeholder="5.325,54" />
              ))}
            </div>
          </SectionCard>

          <SectionCard title={tr("monthly.external", lang)}>
            <div className="grid grid-cols-3 gap-4">
              {EXTERNAL_KEYS.map((k, i) => (
                <MoneyInput key={k} label={tr(EXTERNAL_I18N[i], lang)}
                  value={raw[k] || ""} onChange={(v) => setRaw((p) => ({ ...p, [k]: v }))}
                  placeholder="0" />
              ))}
            </div>
          </SectionCard>

          <SectionCard title={tr("monthly.other_costs", lang)}>
            <div className="grid grid-cols-4 gap-4">
              {NEW_COST_KEYS.map((k, i) => (
                <MoneyInput key={k} label={tr(NEW_COST_I18N[i], lang)}
                  value={raw[k] || ""} onChange={(v) => setRaw((p) => ({ ...p, [k]: v }))}
                  placeholder="0" />
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-3">{tr("monthly.auto_costs_note", lang)}</p>
          </SectionCard>

          <Button onClick={handlePreview} disabled={loading}>
            {loading ? tr("monthly.generating", lang) : tr("monthly.preview_btn", lang)}
          </Button>
        </>
      )}

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {/* Preview / Saved results */}
      {results && (pageState === "preview" || pageState === "saved") && (
        <>
          {/* Status badge */}
          <SectionCard>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                  pageState === "saved"
                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                    : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                }`}>
                  {pageState === "saved" ? tr("monthly.status_saved", lang) : tr("monthly.status_preview", lang)}
                </span>
                <span className="text-sm text-gray-500">{months[month - 1]} {year}</span>
              </div>
              {pageState === "preview" && (
                <Button onClick={handleSave} disabled={loading}>
                  {loading ? "..." : tr("monthly.save_official", lang)}
                </Button>
              )}
            </div>
          </SectionCard>

          {/* Preview tabs */}
          <SectionCard>
            <div className="flex gap-2 mb-4">
              {["summary", "detailed", "totals"].map((tab) => (
                <button key={tab} onClick={() => setPreviewTab(tab)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    previewTab === tab
                      ? "bg-navy text-white"
                      : "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200"
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
                data={results} keyField="company_id"
              />
            )}
            {previewTab === "detailed" && (
              <DataTable columns={cols} data={results} keyField="company_id" />
            )}
            {previewTab === "totals" && (
              <div className="space-y-3">
                {[
                  ["electricity", tr("field.electricity", lang)],
                  ["water", tr("field.water", lang)],
                  ["garbage", tr("field.garbage", lang)],
                  ["gas_hotel", "Gas (Hotel)"], ["gas_ground_floor", "Gas (GF)"], ["gas_first_floor", "Gas (1F)"],
                  ["consumables", tr("field.consumables", lang)],
                  ["drinking_water", tr("field.drinking_water", lang)],
                  ["printer", tr("field.printer", lang)],
                  ["internet", tr("field.internet", lang)],
                  ["maintenance", "Maintenance"], ["hotel_rent", "Hotel Rent"],
                ].map(([key, label]) => {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const total = results.reduce((s, r) => s + ((r as any)[key] || 0), 0);
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
                    {formatRon(results.reduce((s, r) => s + r.total, 0))}
                  </span>
                </div>
              </div>
            )}
          </SectionCard>

          {/* Export panel — only when saved */}
          {pageState === "saved" && frozenInput && (
            <ExportPanel results={results} companies={companies} runId={runId}
              filename={filename} month={month} year={year} language={lang}
              monthlyInput={frozenInput} />
          )}

          {/* Payment tracking — only when saved */}
          {pageState === "saved" && runId && (
            <SectionCard title={tr("monthly.payments", lang)}>
              {/* Existing payments */}
              {payments.length > 0 && (
                <div className="mb-4">
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
                          const companyName = results.find(r => r.company_id === p.company_id)?.company_name || p.company_id;
                          return (
                            <tr key={p.id} className={i % 2 === 0 ? "bg-white dark:bg-card-dark" : "bg-gray-50/60 dark:bg-gray-800/40"}>
                              <td className="p-2.5 border-b border-gray-100 dark:border-gray-700">{companyName}</td>
                              <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums">{formatRon(p.amount)}</td>
                              <td className="p-2.5 border-b border-gray-100 dark:border-gray-700">{p.date}</td>
                              <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-gray-500">{p.note}</td>
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
                </div>
              )}

              {/* Balance summary */}
              <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                {activeCompaniesWithDue.slice(0, 8).map(r => {
                  const bal = balances[r.company_id] || 0;
                  const paid = payments.filter(p => p.company_id === r.company_id).reduce((s, p) => s + p.amount, 0);
                  return (
                    <div key={r.company_id} className="text-xs border dark:border-gray-700 rounded p-2">
                      <div className="font-medium truncate">{r.company_name}</div>
                      <div className="text-gray-500">{tr("monthly.amount_due", lang)}: {formatRon(r.total)}</div>
                      <div className="text-green-600">{tr("manager.paid", lang)}: {formatRon(paid)}</div>
                      <div className={bal > 0 ? "text-red-600 font-semibold" : "text-green-600 font-semibold"}>
                        {bal > 0 ? formatRon(bal) : bal < 0 ? `${tr("monthly.credit", lang)}: ${formatRon(Math.abs(bal))}` : tr("manager.paid", lang)}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Add payment form */}
              {!showConfirm ? (
                <div className="flex items-end gap-3 flex-wrap">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">{tr("table.company", lang)}</label>
                    <select value={newPayment.companyId} onChange={(e) => setNewPayment(p => ({ ...p, companyId: e.target.value }))}
                      className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700 min-w-[180px]">
                      <option value="">...</option>
                      {activeCompaniesWithDue.map(r => (
                        <option key={r.company_id} value={r.company_id}>{r.company_name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">{tr("monthly.paid_amount", lang)} (RON)</label>
                    <input value={newPayment.amount} onChange={(e) => setNewPayment(p => ({ ...p, amount: e.target.value }))}
                      placeholder="0" className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm w-28 bg-white dark:bg-gray-700" />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">{tr("monthly.pay_date", lang)}</label>
                    <input type="date" value={newPayment.date} onChange={(e) => setNewPayment(p => ({ ...p, date: e.target.value }))}
                      className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700" />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">{tr("monthly.pay_note", lang)}</label>
                    <input value={newPayment.note} onChange={(e) => setNewPayment(p => ({ ...p, note: e.target.value }))}
                      placeholder="bank, cash..." className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm w-32 bg-white dark:bg-gray-700" />
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
                    {results.find(r => r.company_id === newPayment.companyId)?.company_name}: <strong>{formatRon(parseRonInput(newPayment.amount))}</strong> — {newPayment.date} {newPayment.note && `(${newPayment.note})`}
                  </p>
                  <div className="flex gap-2 mt-3">
                    <Button onClick={handleAddPayment}>{tr("monthly.confirm_save", lang)}</Button>
                    <Button variant="secondary" onClick={() => setShowConfirm(false)}>{tr("companies.cancel", lang)}</Button>
                  </div>
                </div>
              )}
            </SectionCard>
          )}
        </>
      )}
    </PageLayout>
  );
}
