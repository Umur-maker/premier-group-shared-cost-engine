"use client";

import { useEffect, useState } from "react";
import { getHistory, getRunDetail, getRunPayments, getAllBalances, getCompanies } from "@/lib/api";
import { formatRon } from "@/lib/formatting";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard, Button } from "@/components";
import type { HistoryEntry, AllocationResult, PaymentEntry, MonthlyInput, Company } from "@/types";

function StatRow({ label, value, bold, color }: { label: string; value: number; bold?: boolean; color?: string }) {
  return (
    <div className={`flex justify-between items-center py-1.5 ${bold ? "border-t-2 border-navy dark:border-blue-400 pt-2 mt-1" : "border-b border-gray-100 dark:border-gray-700"}`}>
      <span className={`text-sm ${bold ? "font-bold text-navy dark:text-white" : ""}`}>{label}</span>
      <span className={`text-sm tabular-nums ${bold ? "text-lg font-bold" : "font-medium"} ${color || (bold ? "text-navy dark:text-white" : "")}`}>
        {formatRon(value)}
      </span>
    </div>
  );
}

interface PeriodData {
  results: AllocationResult[];
  inputs: MonthlyInput[];
  payments: PaymentEntry[];
  monthCount: number;
}

export default function ManagerPage() {
  const { lang } = useApp();
  const now = new Date();
  const [runs, setRuns] = useState<HistoryEntry[]>([]);
  const [fromMonth, setFromMonth] = useState(1);
  const [fromYear, setFromYear] = useState(now.getFullYear());
  const [toMonth, setToMonth] = useState(now.getMonth() + 1);
  const [toYear, setToYear] = useState(now.getFullYear());
  const [data, setData] = useState<PeriodData | null>(null);
  const [balances, setBalances] = useState<Record<string, number>>({});
  const [selectedCompany, setSelectedCompany] = useState<string>("");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const months = monthNames(lang);

  const [autoLoaded, setAutoLoaded] = useState(false);

  useEffect(() => {
    getHistory().then((h) => {
      setRuns(h);
      if (!autoLoaded && h.length > 0) setAutoLoaded(true);
    }).catch(() => setError(tr("error.backend_down", lang)));
    getCompanies().then(setCompanies).catch(() => {});
  }, [lang, autoLoaded]);

  useEffect(() => {
    if (autoLoaded && runs.length > 0 && !data && !loading) {
      handleLoad();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoLoaded, runs]);

  const handleLoad = async () => {
    setLoading(true);
    setError("");
    setData(null);
    try {
      const from = fromYear * 100 + fromMonth;
      const to = toYear * 100 + toMonth;
      const filtered = runs.filter((r) => {
        const v = r.year * 100 + r.month;
        return v >= from && v <= to;
      });

      if (filtered.length === 0) {
        setError(tr("manager.no_data", lang));
        setLoading(false);
        return;
      }

      const [details, balData] = await Promise.all([
        Promise.all(filtered.map((r) => getRunDetail(r.id))),
        getAllBalances(),
      ]);

      // Aggregate results across all months
      const aggregated = new Map<string, AllocationResult>();
      const allInputs: MonthlyInput[] = [];
      let allPayments: PaymentEntry[] = [];

      for (const detail of details) {
        if (detail.monthly_input) allInputs.push(detail.monthly_input);
        for (const r of detail.results || []) {
          const existing = aggregated.get(r.company_id);
          if (existing) {
            existing.electricity += r.electricity || 0;
            existing.water += r.water || 0;
            existing.garbage += r.garbage || 0;
            existing.gas_hotel += r.gas_hotel || 0;
            existing.gas_ground_floor += r.gas_ground_floor || 0;
            existing.gas_first_floor += r.gas_first_floor || 0;
            existing.consumables += r.consumables || 0;
            existing.printer += r.printer || 0;
            existing.internet += r.internet || 0;
            existing.maintenance += r.maintenance || 0;
            existing.maintenance_vat += r.maintenance_vat || 0;
            existing.rent += r.rent || 0;
            existing.rent_vat += r.rent_vat || 0;
            existing.total += r.total || 0;
          } else {
            aggregated.set(r.company_id, {
              ...r,
              electricity: r.electricity || 0, water: r.water || 0, garbage: r.garbage || 0,
              gas_hotel: r.gas_hotel || 0, gas_ground_floor: r.gas_ground_floor || 0, gas_first_floor: r.gas_first_floor || 0,
              consumables: r.consumables || 0, printer: r.printer || 0, internet: r.internet || 0,
              maintenance: r.maintenance || 0, maintenance_vat: r.maintenance_vat || 0,
              rent: r.rent || 0, rent_vat: r.rent_vat || 0, total: r.total || 0,
            });
          }
        }
      }

      // Load payments for each run
      const paymentResults = await Promise.all(filtered.map((r) => getRunPayments(r.id)));
      allPayments = paymentResults.flat();

      setData({
        results: Array.from(aggregated.values()),
        inputs: allInputs,
        payments: allPayments,
        monthCount: filtered.length,
      });
      setBalances(balData);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  // Compute financials from aggregated data
  const computeFinancials = () => {
    if (!data) return null;
    const { results, inputs } = data;

    // REVENUE: what companies are billed (use || 0 for old runs missing fields)
    const utilityIncome = results.reduce(
      (s, r) => s + (r.electricity || 0) + (r.water || 0) + (r.garbage || 0) + (r.gas_hotel || 0) + (r.gas_ground_floor || 0) + (r.gas_first_floor || 0) + (r.consumables || 0) + (r.printer || 0) + (r.internet || 0), 0
    );
    const maintenanceIncome = results.reduce((s, r) => s + (r.maintenance || 0), 0);
    const rentIncome = results.reduce((s, r) => s + (r.rent || 0), 0);
    const vatCollected = results.reduce((s, r) => s + (r.maintenance_vat || 0) + (r.rent_vat || 0), 0);
    const totalRevenue = results.reduce((s, r) => s + (r.total || 0), 0);

    // COSTS: what Premier actually pays (from monthly_input)
    const utilityCosts = inputs.reduce(
      (s, mi) =>
        s + (mi.electricity_total || 0) + (mi.water_total || 0) + (mi.garbage_total || 0) +
        (mi.hotel_gas_total || 0) + (mi.ground_floor_gas_total || 0) + (mi.first_floor_gas_total || 0) +
        (mi.consumables_total || 0) + (mi.printer_total || 0) + (mi.internet_total || 0),
      0
    );
    const serviceCosts = inputs.reduce(
      (s, mi) => s + (mi.cleaning_cost || 0) + (mi.security_cameras_cost || 0),
      0
    );
    const totalCosts = utilityCosts + serviceCosts;

    // PROFIT/LOSS
    const netResult = totalRevenue - totalCosts;

    // COLLECTION
    const totalBilled = totalRevenue;
    const totalPaid = data.payments.reduce((s, p) => s + p.amount, 0);
    const totalOutstanding = Object.values(balances).reduce((s, b) => s + Math.max(0, b), 0);
    const totalCredit = Object.values(balances).reduce((s, b) => s + Math.min(0, b), 0);

    return {
      utilityIncome, maintenanceIncome, rentIncome, vatCollected, totalRevenue,
      utilityCosts, serviceCosts, totalCosts,
      netResult,
      totalBilled, totalPaid, totalOutstanding, totalCredit,
    };
  };

  const fin = computeFinancials();

  return (
    <PageLayout title={tr("manager.title", lang)}>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {/* Period selector */}
      <SectionCard title={tr("manager.select_period", lang)}>
        <div className="flex items-end gap-4 flex-wrap">
          <div>
            <label className="block text-xs text-gray-500 mb-1">{tr("manager.from", lang)}</label>
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
            <label className="block text-xs text-gray-500 mb-1">{tr("manager.to", lang)}</label>
            <div className="flex gap-2">
              <select value={toMonth} onChange={(e) => setToMonth(+e.target.value)}
                className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700">
                {months.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
              </select>
              <input type="number" value={toYear} onChange={(e) => setToYear(+e.target.value)}
                className="border dark:border-gray-600 rounded px-2 py-1.5 text-sm w-20 bg-white dark:bg-gray-700" />
            </div>
          </div>
          <Button onClick={handleLoad} disabled={loading}>
            {loading ? "..." : tr("manager.generate", lang)}
          </Button>
        </div>
      </SectionCard>

      {data && fin && (
        <>
          {/* Period badge */}
          <div className="text-xs text-gray-500 text-right">
            {data.monthCount} {tr("manager.months_loaded", lang)}
          </div>

          {/* Top-level KPI cards */}
          <div className="grid grid-cols-4 gap-4">
            <SectionCard>
              <p className="text-xs text-gray-500 uppercase">{tr("manager.total_revenue", lang)}</p>
              <p className="text-2xl font-bold text-navy dark:text-white mt-1">{formatRon(fin.totalRevenue)}</p>
            </SectionCard>
            <SectionCard>
              <p className="text-xs text-gray-500 uppercase">{tr("manager.total_costs", lang)}</p>
              <p className="text-2xl font-bold text-gray-700 dark:text-gray-300 mt-1">{formatRon(fin.totalCosts)}</p>
            </SectionCard>
            <SectionCard>
              <p className="text-xs text-gray-500 uppercase">{tr("manager.net_result", lang)}</p>
              <p className={`text-2xl font-bold mt-1 ${fin.netResult >= 0 ? "text-green-600" : "text-red-600"}`}>
                {fin.netResult >= 0 ? "+" : ""}{formatRon(fin.netResult)}
              </p>
            </SectionCard>
            <SectionCard>
              <p className="text-xs text-gray-500 uppercase">{tr("manager.total_outstanding", lang)}</p>
              <p className="text-2xl font-bold text-red-600 mt-1">{formatRon(fin.totalOutstanding)}</p>
            </SectionCard>
          </div>

          {/* Revenue + Costs side by side */}
          <div className="grid grid-cols-2 gap-4">
            {/* Revenue breakdown */}
            <SectionCard title={tr("manager.revenue", lang)}>
              <div className="space-y-0">
                <StatRow label={tr("manager.utility_income", lang)} value={fin.utilityIncome} />
                <StatRow label={tr("manager.maintenance_income", lang)} value={fin.maintenanceIncome} />
                <StatRow label={tr("manager.rent_income", lang)} value={fin.rentIncome} />
                <StatRow label={tr("manager.vat_collected", lang)} value={fin.vatCollected} />
                <StatRow label={tr("manager.total_revenue", lang)} value={fin.totalRevenue} bold />
              </div>
            </SectionCard>

            {/* Costs breakdown */}
            <SectionCard title={tr("manager.costs", lang)}>
              <div className="space-y-0">
                <StatRow label={tr("manager.utility_costs", lang)} value={fin.utilityCosts} />
                <StatRow label={tr("manager.service_costs", lang)} value={fin.serviceCosts} />
                <StatRow label={tr("manager.total_costs", lang)} value={fin.totalCosts} bold />
              </div>
              <p className="text-xs text-gray-400 mt-3 italic">{tr("manager.passthrough_note", lang)}</p>
            </SectionCard>
          </div>

          {/* Collection status */}
          <SectionCard title={tr("manager.collection", lang)}>
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <p className="text-xs text-gray-500 uppercase">{tr("manager.total_billed", lang)}</p>
                <p className="text-lg font-bold text-navy dark:text-white">{formatRon(fin.totalBilled)}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-500 uppercase">{tr("manager.total_paid", lang)}</p>
                <p className="text-lg font-bold text-green-600">{formatRon(fin.totalPaid)}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-500 uppercase">{tr("manager.total_outstanding", lang)}</p>
                <p className="text-lg font-bold text-red-600">{formatRon(fin.totalOutstanding)}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-500 uppercase">{tr("monthly.credit", lang)}</p>
                <p className="text-lg font-bold text-blue-600">{formatRon(Math.abs(fin.totalCredit))}</p>
              </div>
            </div>

            {/* Per-company table */}
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
                  {data.results.filter(r => r.total > 0).map((r, i) => {
                    const companyPayments = data.payments.filter(p => p.company_id === r.company_id);
                    const paid = companyPayments.reduce((s, p) => s + p.amount, 0);
                    const bal = balances[r.company_id] || 0;
                    const isSelected = selectedCompany === r.company_id;

                    return (
                      <tr key={r.company_id} onClick={() => setSelectedCompany(isSelected ? "" : r.company_id)}
                        className={`cursor-pointer transition-colors ${isSelected ? "bg-blue-50 dark:bg-blue-900/30 ring-1 ring-blue-300 dark:ring-blue-600" : i % 2 === 0 ? "bg-white dark:bg-card-dark hover:bg-gray-50 dark:hover:bg-gray-800/60" : "bg-gray-50/60 dark:bg-gray-800/40 hover:bg-gray-100 dark:hover:bg-gray-700/60"}`}>
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
            <p className="text-xs text-gray-400 mt-2 italic">{tr("manager.click_row", lang)}</p>
          </SectionCard>

          {/* Company detail breakdown */}
          {selectedCompany && (() => {
            const r = data.results.find(x => x.company_id === selectedCompany);
            if (!r) return null;
            const companyPayments = data.payments.filter(p => p.company_id === selectedCompany);
            const paid = companyPayments.reduce((s, p) => s + p.amount, 0);
            const bal = balances[selectedCompany] || 0;

            const costItems: [string, number][] = [
              [tr("field.electricity", lang), r.electricity],
              [tr("field.water", lang), r.water],
              [tr("field.garbage", lang), r.garbage],
              [tr("field.hotel_gas", lang), r.gas_hotel],
              [tr("field.gf_gas", lang), r.gas_ground_floor],
              [tr("field.ff_gas", lang), r.gas_first_floor],
              [tr("field.consumables", lang), r.consumables],
              [tr("field.printer", lang), r.printer],
              [tr("field.internet", lang), r.internet],
              [tr("table.maint", lang), r.maintenance],
              [tr("table.maint_vat", lang), r.maintenance_vat],
              [tr("table.rent", lang), r.rent],
              [tr("table.rent_vat", lang), r.rent_vat],
            ];

            return (
              <SectionCard title={`${tr("manager.company_detail", lang)}: ${r.company_name}`}>
                <div className="grid grid-cols-2 gap-6">
                  {/* Cost breakdown */}
                  <div>
                    <h4 className="text-xs text-gray-500 uppercase mb-2 font-semibold">{tr("manager.cost_breakdown", lang)}</h4>
                    <div className="space-y-0">
                      {costItems.map(([label, amount]) =>
                        amount > 0 ? <StatRow key={label} label={label} value={amount} /> : null
                      )}
                      <StatRow label={tr("table.total", lang)} value={r.total} bold />
                    </div>
                  </div>

                  {/* Payment summary */}
                  <div>
                    <h4 className="text-xs text-gray-500 uppercase mb-2 font-semibold">{tr("manager.collection", lang)}</h4>
                    <div className="space-y-0">
                      <StatRow label={tr("manager.total_billed", lang)} value={r.total} />
                      <StatRow label={tr("manager.total_paid", lang)} value={paid} color="text-green-600" />
                      <StatRow
                        label={bal > 0 ? tr("manager.total_outstanding", lang) : tr("monthly.credit", lang)}
                        value={Math.abs(bal)}
                        bold
                        color={bal > 0 ? "text-red-600" : bal < 0 ? "text-blue-600" : "text-green-600"}
                      />
                    </div>

                    {companyPayments.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-xs text-gray-500 uppercase mb-2 font-semibold">{tr("monthly.payments", lang)}</h4>
                        <div className="space-y-1">
                          {companyPayments.map((p) => (
                            <div key={p.id} className="flex justify-between text-sm border-b border-gray-100 dark:border-gray-700 py-1">
                              <span className="text-gray-600 dark:text-gray-400">{p.date}{p.note ? ` — ${p.note}` : ""}</span>
                              <span className="tabular-nums text-green-600 font-medium">{formatRon(p.amount)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </SectionCard>
            );
          })()}

          {/* Contract expiration warnings */}
          {(() => {
            const today = new Date();
            const warnings = companies
              .filter((c) => c.active && c.expiration_date)
              .map((c) => {
                const parts = c.expiration_date.split(".");
                if (parts.length !== 3) return null;
                const exp = new Date(+parts[2], +parts[1] - 1, +parts[0]);
                const days = Math.ceil((exp.getTime() - today.getTime()) / 86400000);
                return { company: c.name, days, expired: days < 0 };
              })
              .filter((w) => w && w.days < 60)
              .sort((a, b) => a!.days - b!.days) as { company: string; days: number; expired: boolean }[];

            if (warnings.length === 0) return null;
            return (
              <SectionCard title={tr("manager.contract_expiring", lang)}>
                <div className="space-y-2">
                  {warnings.map((w) => (
                    <div key={w.company} className={`flex justify-between items-center py-1.5 px-3 rounded text-sm ${w.expired ? "bg-red-50 dark:bg-red-900/20" : "bg-yellow-50 dark:bg-yellow-900/20"}`}>
                      <span className="font-medium">{w.company}</span>
                      <span className={`font-semibold ${w.expired ? "text-red-600" : "text-yellow-600"}`}>
                        {w.expired
                          ? `${tr("manager.expired", lang)} (${Math.abs(w.days)} ${tr("manager.days_left", lang)})`
                          : `${w.days} ${tr("manager.days_left", lang)}`
                        }
                      </span>
                    </div>
                  ))}
                </div>
              </SectionCard>
            );
          })()}
        </>
      )}

      {!data && !loading && runs.length === 0 && (
        <SectionCard>
          <p className="text-gray-500 text-sm">{tr("manager.no_runs", lang)}</p>
        </SectionCard>
      )}
    </PageLayout>
  );
}
