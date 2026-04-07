"use client";

import { useState, useEffect } from "react";
import { calculate, getCompanies, getPayments, updatePayment, getBalances } from "@/lib/api";
import { formatRon, parseRonInput } from "@/lib/formatting";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard, MoneyInput, DataTable, Button, ExportPanel } from "@/components";
import type { MonthlyInput, AllocationResult, Company, PaymentStatus, OutstandingBalance } from "@/types";

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
  const [previewTab, setPreviewTab] = useState("summary");
  const [payments, setPayments] = useState<Record<string, PaymentStatus>>({});
  const [balances, setBalances] = useState<Record<string, OutstandingBalance>>({});
  const [paidInputs, setPaidInputs] = useState<Record<string, string>>({});

  useEffect(() => {
    getCompanies().then(setCompanies).catch(() => setError(tr("error.backend_down", lang)));
  }, [lang]);

  const buildInput = (): MonthlyInput => {
    const mi: Record<string, number> = {};
    for (const k of [...INVOICE_KEYS, ...EXTERNAL_KEYS, ...NEW_COST_KEYS]) mi[k] = parseRonInput(raw[k] || "");
    return mi as unknown as MonthlyInput;
  };

  const handleGenerate = async () => {
    setError(""); setResults(null); setLoading(true);
    try {
      const mi = buildInput();
      const res = await calculate({ month, year, language: lang, monthly_input: mi });
      setResults(res.results); setRunId(res.run_id); setFilename(res.filename);
      setFrozenInput(mi);
      // Load payment status for this month
      try {
        const payData = await getPayments(year, month);
        setPayments(payData);
        const balData = await getBalances(year, month);
        setBalances(balData);
        // Pre-fill paid inputs from existing data
        const inputs: Record<string, string> = {};
        for (const r of res.results) {
          const p = payData[r.company_id];
          if (p?.paid_amount) inputs[r.company_id] = String(p.paid_amount);
        }
        setPaidInputs(inputs);
      } catch { /* payments system optional */ }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally { setLoading(false); }
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

  return (
    <PageLayout title={tr("monthly.title", lang)}>
      <SectionCard>
        <div className="flex gap-4">
          <div>
            <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">{tr("monthly.month", lang)}</label>
            <select value={month} onChange={(e) => setMonth(+e.target.value)}
              className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700">
              {months.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">{tr("monthly.year", lang)}</label>
            <input type="number" value={year} onChange={(e) => setYear(+e.target.value)}
              className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm w-24 bg-white dark:bg-gray-700" />
          </div>
        </div>
      </SectionCard>

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
        <p className="text-xs text-gray-400 mt-3">
          {tr("monthly.auto_costs_note", lang)}
        </p>
      </SectionCard>

      <Button onClick={handleGenerate} disabled={loading}>
        {loading ? tr("monthly.generating", lang) : tr("monthly.generate", lang)}
      </Button>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {results && (
        <>
          {/* In-app preview tabs */}
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
                data={results}
                keyField="company_id"
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
                  ["gas_hotel", "Gas (Hotel)"],
                  ["gas_ground_floor", "Gas (GF)"],
                  ["gas_first_floor", "Gas (1F)"],
                  ["consumables", tr("field.consumables", lang)],
                  ["drinking_water", tr("field.drinking_water", lang)],
                  ["printer", tr("field.printer", lang)],
                  ["internet", tr("field.internet", lang)],
                  ["maintenance", "Maintenance"],
                  ["hotel_rent", "Hotel Rent"],
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

          {/* Payment tracking */}
          <SectionCard title={tr("monthly.payments", lang)}>
            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-navy text-white">
                    <th className="p-2.5 text-left text-xs uppercase">{tr("table.company", lang)}</th>
                    <th className="p-2.5 text-right text-xs uppercase">{tr("monthly.amount_due", lang)}</th>
                    <th className="p-2.5 text-right text-xs uppercase">{tr("monthly.prev_balance", lang)}</th>
                    <th className="p-2.5 text-right text-xs uppercase">{tr("monthly.total_due", lang)}</th>
                    <th className="p-2.5 text-center text-xs uppercase">{tr("monthly.paid_amount", lang)}</th>
                    <th className="p-2.5 text-right text-xs uppercase">{tr("monthly.net_balance", lang)}</th>
                    <th className="p-2.5 text-center text-xs uppercase"></th>
                  </tr>
                </thead>
                <tbody>
                  {results.filter(r => r.total > 0).map((r, i) => {
                    const prevBal = balances[r.company_id]?.total_outstanding || 0;
                    const totalDue = r.total + prevBal;
                    const paidStr = paidInputs[r.company_id] || "";
                    const paidAmt = parseFloat(paidStr.replace(",", ".")) || 0;
                    const netBalance = Math.round((totalDue - paidAmt) * 100) / 100;
                    const isPaid = payments[r.company_id]?.paid || false;

                    return (
                      <tr key={r.company_id}
                        className={`${i % 2 === 0 ? "bg-white dark:bg-card-dark" : "bg-gray-50/60 dark:bg-gray-800/40"}
                          hover:bg-blue-50/50 dark:hover:bg-navy-light/10`}>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 font-medium">
                          {r.company_name}
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums">
                          {formatRon(r.total)}
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums">
                          {prevBal > 0 ? (
                            <span className="text-red-600">{formatRon(prevBal)}</span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums font-semibold">
                          {formatRon(totalDue)}
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-center">
                          <div className="flex items-center justify-center gap-1">
                            <input
                              type="text"
                              value={paidStr}
                              onChange={(e) => setPaidInputs(p => ({ ...p, [r.company_id]: e.target.value }))}
                              placeholder="0"
                              className="w-28 border dark:border-gray-600 rounded px-2 py-1 text-sm text-right
                                         bg-white dark:bg-gray-700 tabular-nums"
                            />
                            <span className="text-xs text-gray-400">RON</span>
                          </div>
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums">
                          <span className={netBalance > 0 ? "text-red-600 font-semibold" : "text-green-600 font-semibold"}>
                            {netBalance <= 0 ? tr("manager.paid", lang) : formatRon(netBalance)}
                          </span>
                        </td>
                        <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-center">
                          <Button
                            variant={isPaid ? "secondary" : "primary"}
                            className="text-xs px-2 py-1"
                            onClick={async () => {
                              try {
                                await updatePayment(year, month, {
                                  company_id: r.company_id,
                                  paid: !isPaid,
                                  paid_amount: paidAmt || r.total,
                                  paid_date: !isPaid ? new Date().toISOString().slice(0, 10) : "",
                                });
                                const payData = await getPayments(year, month);
                                setPayments(payData);
                                const balData = await getBalances(year, month);
                                setBalances(balData);
                              } catch { /* ignore */ }
                            }}
                          >
                            {isPaid ? "✓" : tr("monthly.save_payment", lang)}
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr className="bg-gray-50 dark:bg-gray-800 font-semibold">
                    <td className="p-2.5 border-t-2 border-navy dark:border-blue-400">{tr("table.total", lang)}</td>
                    <td className="p-2.5 border-t-2 border-navy dark:border-blue-400 text-right tabular-nums">
                      {formatRon(results.reduce((s, r) => s + r.total, 0))}
                    </td>
                    <td className="p-2.5 border-t-2 border-navy dark:border-blue-400 text-right tabular-nums text-red-600">
                      {formatRon(results.reduce((s, r) => s + (balances[r.company_id]?.total_outstanding || 0), 0))}
                    </td>
                    <td className="p-2.5 border-t-2 border-navy dark:border-blue-400 text-right tabular-nums">
                      {formatRon(results.reduce((s, r) => s + r.total + (balances[r.company_id]?.total_outstanding || 0), 0))}
                    </td>
                    <td className="p-2.5 border-t-2 border-navy dark:border-blue-400 text-right tabular-nums">
                      {formatRon(results.filter(r => r.total > 0).reduce((s, r) => {
                        const v = parseFloat((paidInputs[r.company_id] || "0").replace(",", ".")) || 0;
                        return s + v;
                      }, 0))}
                    </td>
                    <td className="p-2.5 border-t-2 border-navy dark:border-blue-400 text-right tabular-nums">
                      {formatRon(results.filter(r => r.total > 0).reduce((s, r) => {
                        const prevBal = balances[r.company_id]?.total_outstanding || 0;
                        const totalDue = r.total + prevBal;
                        const paidAmt = parseFloat((paidInputs[r.company_id] || "0").replace(",", ".")) || 0;
                        return s + Math.max(0, totalDue - paidAmt);
                      }, 0))}
                    </td>
                    <td className="p-2.5 border-t-2 border-navy dark:border-blue-400"></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </SectionCard>

          <ExportPanel results={results} companies={companies} runId={runId}
            filename={filename} month={month} year={year} language={lang}
            monthlyInput={frozenInput!} />
        </>
      )}
    </PageLayout>
  );
}
