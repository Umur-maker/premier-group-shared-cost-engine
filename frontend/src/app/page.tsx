"use client";

import { useState, useEffect } from "react";
import { calculate, getCompanies } from "@/lib/api";
import { formatRon, parseRonInput } from "@/lib/formatting";
import { PageLayout, SectionCard, MoneyInput, DataTable, Button, ExportPanel } from "@/components";
import type { MonthlyInput, AllocationResult, Company } from "@/types";

const MONTHS = ["January","February","March","April","May","June",
  "July","August","September","October","November","December"];

const INVOICE_FIELDS: { key: keyof MonthlyInput; label: string }[] = [
  { key: "electricity_total", label: "Electricity" },
  { key: "water_total", label: "Water" },
  { key: "garbage_total", label: "Garbage" },
  { key: "hotel_gas_total", label: "Hotel Gas" },
  { key: "ground_floor_gas_total", label: "Ground Floor Gas" },
  { key: "first_floor_gas_total", label: "First Floor Gas" },
];

const EXTERNAL_FIELDS: { key: keyof MonthlyInput; label: string }[] = [
  { key: "external_electricity", label: "Ext. Electricity" },
  { key: "external_water", label: "Ext. Water" },
  { key: "external_garbage", label: "Ext. Garbage" },
  { key: "external_hotel_gas", label: "Ext. Hotel Gas" },
  { key: "external_gf_gas", label: "Ext. GF Gas" },
  { key: "external_ff_gas", label: "Ext. FF Gas" },
];

export default function MonthlyInputPage() {
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

  useEffect(() => { getCompanies().then(setCompanies); }, []);

  const buildInput = (): MonthlyInput => {
    const mi: Record<string, number> = {};
    for (const f of [...INVOICE_FIELDS, ...EXTERNAL_FIELDS]) {
      mi[f.key] = parseRonInput(raw[f.key] || "");
    }
    return mi as unknown as MonthlyInput;
  };

  const handleGenerate = async () => {
    setError(""); setResults(null); setLoading(true);
    try {
      const mi = buildInput();
      const res = await calculate({ month, year, language: "en", monthly_input: mi });
      setResults(res.results);
      setRunId(res.run_id);
      setFilename(res.filename);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  const resultColumns = [
    { key: "company_name", header: "Company" },
    { key: "electricity", header: "Elec.", align: "right" as const, render: (r: AllocationResult) => formatRon(r.electricity) },
    { key: "water", header: "Water", align: "right" as const, render: (r: AllocationResult) => formatRon(r.water) },
    { key: "garbage", header: "Garb.", align: "right" as const, render: (r: AllocationResult) => formatRon(r.garbage) },
    { key: "gas_hotel", header: "Gas(H)", align: "right" as const, render: (r: AllocationResult) => formatRon(r.gas_hotel) },
    { key: "gas_ground_floor", header: "Gas(GF)", align: "right" as const, render: (r: AllocationResult) => formatRon(r.gas_ground_floor) },
    { key: "gas_first_floor", header: "Gas(1F)", align: "right" as const, render: (r: AllocationResult) => formatRon(r.gas_first_floor) },
    { key: "total", header: "Total", align: "right" as const, bold: true, render: (r: AllocationResult) => formatRon(r.total) },
  ];

  return (
    <PageLayout title="Monthly Input">
      <SectionCard>
        <div className="flex gap-4 mb-4">
          <div>
            <label className="block text-xs text-gray-600 mb-1">Month</label>
            <select value={month} onChange={(e) => setMonth(+e.target.value)}
              className="border rounded px-2 py-1.5 text-sm">
              {MONTHS.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Year</label>
            <input type="number" value={year} onChange={(e) => setYear(+e.target.value)}
              className="border rounded px-2 py-1.5 text-sm w-24" />
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Invoice Totals">
        <div className="grid grid-cols-3 gap-4">
          {INVOICE_FIELDS.map((f) => (
            <MoneyInput key={f.key} label={f.label}
              value={raw[f.key] || ""}
              onChange={(v) => setRaw((p) => ({ ...p, [f.key]: v }))}
              placeholder="5.325,54" />
          ))}
        </div>
      </SectionCard>

      <SectionCard title="External Usage">
        <div className="grid grid-cols-3 gap-4">
          {EXTERNAL_FIELDS.map((f) => (
            <MoneyInput key={f.key} label={f.label}
              value={raw[f.key] || ""}
              onChange={(v) => setRaw((p) => ({ ...p, [f.key]: v }))}
              placeholder="0" />
          ))}
        </div>
      </SectionCard>

      <Button onClick={handleGenerate} disabled={loading}>
        {loading ? "Generating..." : "Generate Report"}
      </Button>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {results && (
        <>
          <SectionCard title="Allocation Preview (RON)">
            <DataTable columns={resultColumns} data={results} keyField="company_id" />
          </SectionCard>

          <ExportPanel
            results={results}
            companies={companies}
            runId={runId}
            filename={filename}
            month={month}
            year={year}
            language="en"
            monthlyInput={buildInput()}
          />
        </>
      )}
    </PageLayout>
  );
}
