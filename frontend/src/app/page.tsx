"use client";

import { useState, useEffect } from "react";
import { calculatePreview, saveOfficial, checkMonth, getCompanies } from "@/lib/api";
import { formatRon, parseRonInput } from "@/lib/formatting";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard, MoneyInput, DataTable, Button, ExportPanel } from "@/components";
import type { MonthlyInput, AllocationResult, Company, AllocationWarning } from "@/types";

const ALL_COST_KEYS: (keyof MonthlyInput)[] = [
  "electricity_total", "water_total", "garbage_total",
  "hotel_gas_total", "ground_floor_gas_total", "first_floor_gas_total",
  "consumables_total", "printer_total",
  "internet_total", "cleaning_cost", "security_cameras_cost",
];
const ALL_COST_I18N = [
  "field.electricity", "field.water", "field.garbage",
  "field.hotel_gas", "field.gf_gas", "field.ff_gas",
  "field.consumables", "field.printer",
  "field.internet", "field.cleaning", "field.security_cameras",
];
const EXTERNAL_KEYS: (keyof MonthlyInput)[] = [
  "external_electricity", "external_water", "external_garbage",
  "external_hotel_gas", "external_gf_gas", "external_ff_gas",
];
const EXTERNAL_I18N = [
  "field.ext_electricity", "field.ext_water", "field.ext_garbage",
  "field.ext_hotel_gas", "field.ext_gf_gas", "field.ext_ff_gas",
];

type PageState = "input" | "preview" | "saved";

export default function MonthlyInputPage() {
  const { lang, showToast } = useApp();
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
  const [warnings, setWarnings] = useState<AllocationWarning[]>([]);

  useEffect(() => {
    getCompanies().then(setCompanies).catch(() => setError(tr("error.backend_down", lang)));
  }, [lang]);

  const buildInput = (): MonthlyInput => {
    const mi: Record<string, number> = {};
    const allKeys = [...ALL_COST_KEYS, ...EXTERNAL_KEYS];
    const allLabels = [...ALL_COST_I18N, ...EXTERNAL_I18N];
    for (let i = 0; i < allKeys.length; i++) {
      const k = allKeys[i];
      try {
        mi[k] = parseRonInput(raw[k] || "");
      } catch {
        throw new Error(`${tr(allLabels[i], lang)}: ${tr("error.invalid_amount", lang)}`);
      }
    }
    return mi as unknown as MonthlyInput;
  };

  // Step 1: Preview
  const handlePreview = async () => {
    setError(""); setResults(null); setWarnings([]); setLoading(true);
    try {
      const mi = buildInput();
      const res = await calculatePreview({ month, year, language: lang, monthly_input: mi });
      setResults(res.results); setFilename(res.filename); setFrozenInput(mi);
      setWarnings(res.warnings || []);
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
      showToast(tr("monthly.status_saved", lang), "success");
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
    { key: "printer", header: tr("table.printer", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.printer) },
    { key: "internet", header: tr("table.internet", lang), align: "right" as const, render: (r: AllocationResult) => formatRon(r.internet) },
    { key: "maintenance", header: tr("table.maint", lang), align: "right" as const,
      render: (r: AllocationResult) => formatRon(r.maintenance + (r.maintenance_vat || 0)) },
    { key: "rent", header: tr("table.rent", lang), align: "right" as const,
      render: (r: AllocationResult) => formatRon(r.rent + (r.rent_vat || 0)) },
    { key: "total", header: tr("table.total", lang), align: "right" as const, bold: true, render: (r: AllocationResult) => formatRon(r.total) },
  ];

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

      {/* Welcome state for fresh install */}
      {companies.filter(c => c.active).length === 0 && pageState === "input" && (
        <SectionCard>
          <div className="text-center py-6">
            <p className="text-gray-500 text-sm">{tr("empty.welcome", lang)}</p>
          </div>
        </SectionCard>
      )}

      {/* Input section — only visible in input state */}
      {pageState === "input" && companies.filter(c => c.active).length > 0 && (
        <>
          <SectionCard title={tr("monthly.costs", lang)}>
            {/* Utility Bills */}
            <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-2">
              {tr("monthly.group_utilities", lang)}
            </p>
            <div className="grid grid-cols-3 gap-4 mb-5">
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <MoneyInput key={ALL_COST_KEYS[i]} label={tr(ALL_COST_I18N[i], lang)}
                  value={raw[ALL_COST_KEYS[i]] || ""} onChange={(v) => setRaw((p) => ({ ...p, [ALL_COST_KEYS[i]]: v }))}
                  placeholder="0" />
              ))}
            </div>

            {/* Services */}
            <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold mb-2">
              {tr("monthly.group_services", lang)}
            </p>
            <div className="grid grid-cols-3 gap-4 mb-5">
              {[6, 7, 8].map((i) => (
                <MoneyInput key={ALL_COST_KEYS[i]} label={tr(ALL_COST_I18N[i], lang)}
                  value={raw[ALL_COST_KEYS[i]] || ""} onChange={(v) => setRaw((p) => ({ ...p, [ALL_COST_KEYS[i]]: v }))}
                  placeholder="0" />
              ))}
            </div>

            {/* Manager Costs */}
            <p className="text-[10px] text-amber-600 dark:text-amber-400 uppercase tracking-wider font-semibold mb-2">
              {tr("monthly.group_manager", lang)}
            </p>
            <div className="grid grid-cols-3 gap-4">
              {[9, 10].map((i) => (
                <MoneyInput key={ALL_COST_KEYS[i]} label={tr(ALL_COST_I18N[i], lang)}
                  value={raw[ALL_COST_KEYS[i]] || ""} onChange={(v) => setRaw((p) => ({ ...p, [ALL_COST_KEYS[i]]: v }))}
                  placeholder="0" />
              ))}
            </div>

            <p className="text-xs text-gray-400 mt-3">{tr("monthly.auto_costs_note", lang)}</p>
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
                <Button onClick={handleSave} disabled={loading || warnings.length > 0}
                  title={warnings.length > 0 ? warnings[0].message : ""}>
                  {loading ? "..." : tr("monthly.save_official", lang)}
                </Button>
              )}
            </div>
          </SectionCard>

          {/* Warnings */}
          {warnings.length > 0 && (
            <SectionCard>
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg p-4">
                <h3 className="font-bold text-red-700 dark:text-red-400 text-sm mb-2">
                  {tr("monthly.warnings_title", lang)}
                </h3>
                <ul className="space-y-1">
                  {warnings.map((w, i) => (
                    <li key={i} className="text-sm text-red-700 dark:text-red-300">
                      {w.message}
                    </li>
                  ))}
                </ul>
                <p className="text-xs text-red-600 dark:text-red-400 mt-3 italic">
                  {tr("monthly.warnings_block_save", lang)}
                </p>
              </div>
            </SectionCard>
          )}

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
              <div className="space-y-4">
                {/* Utilities */}
                <div>
                  <h4 className="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5 font-semibold">{tr("manager.utility_income", lang)}</h4>
                  {[
                    ["electricity", tr("field.electricity", lang)],
                    ["water", tr("field.water", lang)],
                    ["garbage", tr("field.garbage", lang)],
                    ["gas_hotel", tr("field.hotel_gas", lang)],
                    ["gas_ground_floor", tr("field.gf_gas", lang)],
                    ["gas_first_floor", tr("field.ff_gas", lang)],
                  ].map(([key, label]) => {
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    const total = results.reduce((s, r) => s + ((r as any)[key] || 0), 0);
                    if (total === 0) return null;
                    return (
                      <div key={key} className="flex justify-between items-center py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-sm">{label}</span>
                        <span className="text-sm font-medium tabular-nums text-blue-600">{formatRon(total)}</span>
                      </div>
                    );
                  })}
                </div>
                {/* Services */}
                <div>
                  <h4 className="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5 font-semibold">{tr("manager.service_costs", lang)}</h4>
                  {[
                    ["consumables", tr("field.consumables", lang)],
                    ["printer", tr("field.printer", lang)],
                    ["internet", tr("field.internet", lang)],
                  ].map(([key, label]) => {
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    const total = results.reduce((s, r) => s + ((r as any)[key] || 0), 0);
                    if (total === 0) return null;
                    return (
                      <div key={key} className="flex justify-between items-center py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-sm">{label}</span>
                        <span className="text-sm font-medium tabular-nums text-emerald-600">{formatRon(total)}</span>
                      </div>
                    );
                  })}
                </div>
                {/* Fixed Costs */}
                <div>
                  <h4 className="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5 font-semibold">{tr("table.maint", lang)} & {tr("table.rent", lang)}</h4>
                  {[
                    ["maintenance", tr("table.maint", lang)],
                    ["rent", tr("table.rent", lang)],
                  ].map(([key, label]) => {
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    let total = results.reduce((s, r) => s + ((r as any)[key] || 0), 0);
                    if (key === "maintenance") total += results.reduce((s, r) => s + (r.maintenance_vat || 0), 0);
                    if (key === "rent") total += results.reduce((s, r) => s + (r.rent_vat || 0), 0);
                    if (total === 0) return null;
                    return (
                      <div key={key} className="flex justify-between items-center py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-sm">{label} <span className="text-xs text-gray-400">(+21% VAT)</span></span>
                        <span className="text-sm font-medium tabular-nums text-amber-600">{formatRon(total)}</span>
                      </div>
                    );
                  })}
                </div>
                {/* Grand Total */}
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

        </>
      )}
    </PageLayout>
  );
}
