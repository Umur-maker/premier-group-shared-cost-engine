"use client";

import { useState, useEffect } from "react";
import { calculate, getCompanies } from "@/lib/api";
import { formatRon, parseRonInput } from "@/lib/formatting";
import { useApp } from "@/lib/AppContext";
import { tr, monthNames } from "@/lib/i18n";
import { PageLayout, SectionCard, MoneyInput, DataTable, Button, ExportPanel } from "@/components";
import type { MonthlyInput, AllocationResult, Company } from "@/types";

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
          <SectionCard title={tr("monthly.preview", lang)}>
            <DataTable columns={cols} data={results} keyField="company_id" />
          </SectionCard>
          <ExportPanel results={results} companies={companies} runId={runId}
            filename={filename} month={month} year={year} language={lang}
            monthlyInput={frozenInput!} />
        </>
      )}
    </PageLayout>
  );
}
