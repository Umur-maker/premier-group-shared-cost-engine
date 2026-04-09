"use client";

import { useEffect, useState } from "react";
import { getHistory, getRunDetail } from "@/lib/api";
import { formatRon } from "@/lib/formatting";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard, Button } from "@/components";
import type { HistoryEntry, AllocationResult } from "@/types";

const UTILITY_KEYS = ["electricity", "water", "garbage", "gas_hotel", "gas_ground_floor", "gas_first_floor"] as const;
const SERVICE_KEYS = ["consumables", "printer", "internet"] as const;
const FIXED_KEYS = ["maintenance", "maintenance_vat", "rent", "rent_vat"] as const;
const ALL_KEYS = [...UTILITY_KEYS, ...SERVICE_KEYS, ...FIXED_KEYS] as const;

function val(r: AllocationResult, k: string): number {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (r as any)[k] || 0;
}

function CostGroupTable({ title, keys, labelMap, data, grandTotalLabel }: {
  title: string;
  keys: readonly string[];
  labelMap: Record<string, string>;
  data: AllocationResult[];
  grandTotalLabel: string;
}) {
  const groupTotal = data.reduce((s, r) => s + keys.reduce((ss, k) => ss + val(r, k), 0), 0);
  if (groupTotal === 0) return null;

  return (
    <div>
      <h4 className="text-[11px] font-bold text-navy/60 dark:text-blue-300/70 uppercase tracking-widest mb-2">{title}</h4>
      <div className="overflow-x-auto rounded-lg border border-gray-200/80 dark:border-gray-700/60">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-navy/90 text-white">
              <th className="px-3 py-2.5 text-left text-[11px] uppercase tracking-wider font-semibold">{grandTotalLabel}</th>
              {keys.map((k) => (
                <th key={k} className="px-3 py-2.5 text-right text-[11px] uppercase tracking-wider font-semibold whitespace-nowrap">
                  {labelMap[k] || k}
                </th>
              ))}
              <th className="px-3 py-2.5 text-right text-[11px] uppercase tracking-wider font-bold bg-navy">
                {grandTotalLabel}
              </th>
            </tr>
          </thead>
          <tbody>
            {data.filter(r => keys.some(k => val(r, k) > 0)).map((r, i) => {
              const rowTotal = keys.reduce((s, k) => s + val(r, k), 0);
              return (
                <tr key={r.company_id}
                  className={`${i % 2 === 0 ? "bg-white dark:bg-card-dark" : "bg-gray-50/60 dark:bg-gray-800/40"}
                    hover:bg-blue-50/50 dark:hover:bg-navy-light/10 transition-colors`}>
                  <td className="px-3 py-2 border-b border-gray-100/80 dark:border-gray-700/50 font-medium">{r.company_name}</td>
                  {keys.map((k) => (
                    <td key={k} className="px-3 py-2 border-b border-gray-100/80 dark:border-gray-700/50 text-right tabular-nums text-gray-600 dark:text-gray-400">
                      {val(r, k) > 0 ? formatRon(val(r, k)) : <span className="text-gray-300 dark:text-gray-600">—</span>}
                    </td>
                  ))}
                  <td className="px-3 py-2 border-b border-gray-100/80 dark:border-gray-700/50 text-right tabular-nums font-semibold text-navy dark:text-white">
                    {formatRon(rowTotal)}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr className="bg-gray-50 dark:bg-gray-800/60 border-t-2 border-navy/20 dark:border-blue-400/30">
              <td className="px-3 py-2.5 font-bold text-navy dark:text-white">{grandTotalLabel}</td>
              {keys.map((k) => {
                const colTotal = data.reduce((s, r) => s + val(r, k), 0);
                return (
                  <td key={k} className="px-3 py-2.5 text-right tabular-nums font-semibold text-navy/80 dark:text-blue-300">
                    {colTotal > 0 ? formatRon(colTotal) : "—"}
                  </td>
                );
              })}
              <td className="px-3 py-2.5 text-right tabular-nums font-bold text-lg text-navy dark:text-white">
                {formatRon(groupTotal)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

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
  const [expandedCompany, setExpandedCompany] = useState<string | null>(null);
  const [monthCount, setMonthCount] = useState(0);

  const months = monthNames(lang);

  useEffect(() => {
    getHistory().then(setRuns).catch(() => setError(tr("error.backend_down", lang)));
  }, [lang]);

  const labelMap: Record<string, string> = {
    electricity: tr("field.electricity", lang),
    water: tr("field.water", lang),
    garbage: tr("field.garbage", lang),
    gas_hotel: tr("field.hotel_gas", lang),
    gas_ground_floor: tr("field.gf_gas", lang),
    gas_first_floor: tr("field.ff_gas", lang),
    consumables: tr("field.consumables", lang),
    printer: tr("field.printer", lang),
    internet: tr("field.internet", lang),
    maintenance: tr("table.maint", lang),
    maintenance_vat: tr("table.maint_vat", lang),
    rent: tr("table.rent", lang),
    rent_vat: tr("table.rent_vat", lang),
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setReportData(null);
    setExpandedCompany(null);
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

      setMonthCount(filtered.length);
      const details = await Promise.all(filtered.map((r) => getRunDetail(r.id)));

      const compMap = new Map<string, string>();
      details.forEach((d) => {
        (d.results || []).forEach((r) => compMap.set(r.company_id, r.company_name));
      });
      setCompanyNames(Array.from(compMap, ([id, name]) => ({ id, name })));

      const aggregated = new Map<string, AllocationResult>();
      for (const detail of details) {
        for (const r of (detail.results || [])) {
          if (selectedCompany !== "all" && r.company_id !== selectedCompany) continue;
          const existing = aggregated.get(r.company_id);
          if (existing) {
            for (const key of ALL_KEYS) {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (existing as any)[key] = (// eslint-disable-next-line @typescript-eslint/no-explicit-any
            (existing as any)[key] as number || 0) + (val(r, key));
            }
            existing.total += r.total || 0;
          } else {
            const copy = { ...r };
            for (const key of ALL_KEYS) {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              (copy as any)[key] = val(r, key);
            }
            copy.total = r.total || 0;
            aggregated.set(r.company_id, copy);
          }
        }
      }

      const result = Array.from(aggregated.values()).map((r) => {
        for (const key of ALL_KEYS) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (r as any)[key] = Math.round((// eslint-disable-next-line @typescript-eslint/no-explicit-any
          (r as any)[key] as number || 0) * 100) / 100;
        }
        r.total = Math.round(r.total * 100) / 100;
        return r;
      });

      setReportData(result.sort((a, b) => b.total - a.total));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  // KPI calculations
  const kpis = reportData ? {
    totalBilled: reportData.reduce((s, r) => s + r.total, 0),
    utilities: reportData.reduce((s, r) => s + UTILITY_KEYS.reduce((ss, k) => ss + val(r, k), 0), 0),
    services: reportData.reduce((s, r) => s + SERVICE_KEYS.reduce((ss, k) => ss + val(r, k), 0), 0),
    fixedGross: reportData.reduce((s, r) => s + FIXED_KEYS.reduce((ss, k) => ss + val(r, k), 0), 0),
    companyCount: reportData.filter(r => r.total > 0).length,
  } : null;

  return (
    <PageLayout title={tr("reports.title", lang)}>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {/* Period + Filter */}
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

      {reportData && kpis && (
        <>
          {/* KPI Cards */}
          <div className="flex items-center justify-between">
            <div className="text-xs text-gray-500">
              {monthCount} {tr("manager.months_loaded", lang)} | {kpis.companyCount} {tr("companies.active_count", lang)}
            </div>
            <Button variant="secondary" className="text-xs no-print" onClick={() => window.print()}>
              {tr("reports.print", lang)}
            </Button>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <SectionCard>
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">{tr("manager.total_revenue", lang)}</p>
              <p className="text-2xl font-bold text-navy dark:text-white mt-1 tabular-nums">{formatRon(kpis.totalBilled)}</p>
            </SectionCard>
            <SectionCard>
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">{tr("manager.utility_income", lang)}</p>
              <p className="text-xl font-bold text-blue-600 mt-1 tabular-nums">{formatRon(kpis.utilities)}</p>
              <p className="text-[10px] text-gray-400 mt-0.5">{kpis.totalBilled > 0 ? Math.round(kpis.utilities / kpis.totalBilled * 100) : 0}%</p>
            </SectionCard>
            <SectionCard>
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">{tr("manager.service_costs", lang)}</p>
              <p className="text-xl font-bold text-emerald-600 mt-1 tabular-nums">{formatRon(kpis.services)}</p>
              <p className="text-[10px] text-gray-400 mt-0.5">{kpis.totalBilled > 0 ? Math.round(kpis.services / kpis.totalBilled * 100) : 0}%</p>
            </SectionCard>
            <SectionCard>
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">{tr("manager.rent_income", lang)} + {tr("table.maint", lang)}</p>
              <p className="text-xl font-bold text-amber-600 mt-1 tabular-nums">{formatRon(kpis.fixedGross)}</p>
              <p className="text-[10px] text-gray-400 mt-0.5">{kpis.totalBilled > 0 ? Math.round(kpis.fixedGross / kpis.totalBilled * 100) : 0}%</p>
            </SectionCard>
          </div>

          {/* Categorized Tables */}
          <div className="space-y-5">
            <CostGroupTable
              title={tr("manager.utility_income", lang)}
              keys={UTILITY_KEYS}
              labelMap={labelMap}
              data={reportData}
              grandTotalLabel={tr("table.total", lang)}
            />

            <CostGroupTable
              title={tr("manager.service_costs", lang)}
              keys={SERVICE_KEYS}
              labelMap={labelMap}
              data={reportData}
              grandTotalLabel={tr("table.total", lang)}
            />

            <CostGroupTable
              title={`${tr("table.maint", lang)} & ${tr("table.rent", lang)} (+ 21% VAT)`}
              keys={FIXED_KEYS}
              labelMap={labelMap}
              data={reportData}
              grandTotalLabel={tr("table.total", lang)}
            />
          </div>

          {/* Grand Total Summary */}
          <SectionCard>
            <div className="overflow-x-auto rounded-lg border border-gray-200/80 dark:border-gray-700/60">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-navy text-white">
                    <th className="px-3 py-3 text-left text-[11px] uppercase tracking-wider font-semibold">{tr("table.company", lang)}</th>
                    <th className="px-3 py-3 text-right text-[11px] uppercase tracking-wider font-semibold">{tr("manager.utility_income", lang)}</th>
                    <th className="px-3 py-3 text-right text-[11px] uppercase tracking-wider font-semibold">{tr("manager.service_costs", lang)}</th>
                    <th className="px-3 py-3 text-right text-[11px] uppercase tracking-wider font-semibold">{tr("table.maint", lang)} + {tr("table.rent", lang)}</th>
                    <th className="px-3 py-3 text-right text-[11px] uppercase tracking-wider font-bold">{tr("table.total", lang)}</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.filter(r => r.total > 0).map((r, i) => {
                    const utilities = UTILITY_KEYS.reduce((s, k) => s + val(r, k), 0);
                    const services = SERVICE_KEYS.reduce((s, k) => s + val(r, k), 0);
                    const fixed = FIXED_KEYS.reduce((s, k) => s + val(r, k), 0);
                    const isExpanded = expandedCompany === r.company_id;

                    return (
                      <tr key={r.company_id}
                        onClick={() => setExpandedCompany(isExpanded ? null : r.company_id)}
                        className={`cursor-pointer transition-colors ${isExpanded ? "bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-200 dark:ring-blue-700" : i % 2 === 0 ? "bg-white dark:bg-card-dark hover:bg-gray-50 dark:hover:bg-gray-800/60" : "bg-gray-50/60 dark:bg-gray-800/40 hover:bg-gray-100 dark:hover:bg-gray-700/60"}`}>
                        <td className="px-3 py-2.5 border-b border-gray-100/80 dark:border-gray-700/50 font-medium">
                          <span className="mr-2 text-xs text-gray-400">{isExpanded ? "▼" : "▶"}</span>
                          {r.company_name}
                        </td>
                        <td className="px-3 py-2.5 border-b border-gray-100/80 dark:border-gray-700/50 text-right tabular-nums text-blue-600">{formatRon(utilities)}</td>
                        <td className="px-3 py-2.5 border-b border-gray-100/80 dark:border-gray-700/50 text-right tabular-nums text-emerald-600">{formatRon(services)}</td>
                        <td className="px-3 py-2.5 border-b border-gray-100/80 dark:border-gray-700/50 text-right tabular-nums text-amber-600">{formatRon(fixed)}</td>
                        <td className="px-3 py-2.5 border-b border-gray-100/80 dark:border-gray-700/50 text-right tabular-nums font-bold text-navy dark:text-white">{formatRon(r.total)}</td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr className="bg-navy/5 dark:bg-navy-light/10 border-t-2 border-navy/20 dark:border-blue-400/30">
                    <td className="px-3 py-3 font-bold text-navy dark:text-white">{tr("table.total", lang)}</td>
                    <td className="px-3 py-3 text-right tabular-nums font-bold text-blue-600">{formatRon(kpis.utilities)}</td>
                    <td className="px-3 py-3 text-right tabular-nums font-bold text-emerald-600">{formatRon(kpis.services)}</td>
                    <td className="px-3 py-3 text-right tabular-nums font-bold text-amber-600">{formatRon(kpis.fixedGross)}</td>
                    <td className="px-3 py-3 text-right tabular-nums font-bold text-xl text-navy dark:text-white">{formatRon(kpis.totalBilled)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </SectionCard>

          {/* Expanded Company Detail */}
          {expandedCompany && (() => {
            const r = reportData.find(x => x.company_id === expandedCompany);
            if (!r) return null;

            const sections = [
              { title: tr("manager.utility_income", lang), keys: UTILITY_KEYS, color: "text-blue-600" },
              { title: tr("manager.service_costs", lang), keys: SERVICE_KEYS, color: "text-emerald-600" },
              { title: `${tr("table.maint", lang)} & ${tr("table.rent", lang)}`, keys: FIXED_KEYS, color: "text-amber-600" },
            ];

            return (
              <SectionCard title={`${tr("manager.company_detail", lang)}: ${r.company_name}`}>
                <div className="grid grid-cols-3 gap-6">
                  {sections.map(({ title, keys, color }) => {
                    const sectionTotal = keys.reduce((s, k) => s + val(r, k), 0);
                    if (sectionTotal === 0) return <div key={title} />;
                    return (
                      <div key={title}>
                        <h4 className="text-[10px] text-gray-500 uppercase tracking-wider mb-2 font-semibold">{title}</h4>
                        <div className="space-y-0">
                          {keys.map((k) => {
                            const amount = val(r, k);
                            if (amount === 0) return null;
                            return (
                              <div key={k} className="flex justify-between items-center py-1.5 border-b border-gray-100 dark:border-gray-700">
                                <span className="text-sm">{labelMap[k]}</span>
                                <span className="text-sm tabular-nums font-medium">{formatRon(amount)}</span>
                              </div>
                            );
                          })}
                          <div className="flex justify-between items-center py-2 border-t-2 border-navy/20 dark:border-blue-400/30 mt-1">
                            <span className="text-sm font-bold">{tr("table.total", lang)}</span>
                            <span className={`text-sm tabular-nums font-bold ${color}`}>{formatRon(sectionTotal)}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between items-center mt-4 pt-3 border-t-2 border-navy dark:border-blue-400">
                  <span className="font-bold text-navy dark:text-white">{tr("reports.period_total", lang)}</span>
                  <span className="text-xl font-bold text-navy dark:text-white tabular-nums">{formatRon(r.total)}</span>
                </div>
              </SectionCard>
            );
          })()}
        </>
      )}
    </PageLayout>
  );
}
