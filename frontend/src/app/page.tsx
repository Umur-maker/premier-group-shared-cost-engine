"use client";

import { useState } from "react";
import { calculate, getExcelUrl } from "@/lib/api";
import type { MonthlyInput, AllocationResult } from "@/types";

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December",
];

const INVOICE_FIELDS: { key: keyof MonthlyInput; label: string }[] = [
  { key: "electricity_total", label: "Electricity" },
  { key: "water_total", label: "Water" },
  { key: "garbage_total", label: "Garbage" },
  { key: "hotel_gas_total", label: "Hotel Gas" },
  { key: "ground_floor_gas_total", label: "Ground Floor Gas" },
  { key: "first_floor_gas_total", label: "First Floor Gas" },
];

const EXTERNAL_FIELDS: { key: keyof MonthlyInput; label: string }[] = [
  { key: "external_electricity", label: "External Electricity" },
  { key: "external_water", label: "External Water" },
  { key: "external_garbage", label: "External Garbage" },
  { key: "external_hotel_gas", label: "External Hotel Gas" },
  { key: "external_gf_gas", label: "External GF Gas" },
  { key: "external_ff_gas", label: "External FF Gas" },
];

const EMPTY_INPUT: MonthlyInput = {
  electricity_total: 0, water_total: 0, garbage_total: 0,
  hotel_gas_total: 0, ground_floor_gas_total: 0, first_floor_gas_total: 0,
  external_electricity: 0, external_water: 0, external_garbage: 0,
  external_hotel_gas: 0, external_gf_gas: 0, external_ff_gas: 0,
};

export default function MonthlyInputPage() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [input, setInput] = useState<MonthlyInput>({ ...EMPTY_INPUT });
  const [results, setResults] = useState<AllocationResult[] | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [filename, setFilename] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const setField = (key: keyof MonthlyInput, val: string) => {
    const v = val.replace(",", ".");
    const num = v === "" ? 0 : parseFloat(v);
    if (!isNaN(num)) setInput((prev) => ({ ...prev, [key]: num }));
  };

  const handleGenerate = async () => {
    setError("");
    setResults(null);
    setLoading(true);
    try {
      const res = await calculate({ month, year, language: "en", monthly_input: input });
      setResults(res.results);
      setRunId(res.run_id);
      setFilename(res.filename);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Monthly Input</h2>

      <div className="flex gap-4 mb-4">
        <select value={month} onChange={(e) => setMonth(+e.target.value)}
          className="border rounded px-2 py-1">
          {MONTHS.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
        </select>
        <input type="number" value={year} onChange={(e) => setYear(+e.target.value)}
          className="border rounded px-2 py-1 w-24" />
      </div>

      <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Invoice Totals (RON)</h3>
      <div className="grid grid-cols-3 gap-3 mb-4">
        {INVOICE_FIELDS.map((f) => (
          <div key={f.key}>
            <label className="text-xs text-gray-600">{f.label}</label>
            <input type="text" placeholder="0"
              onChange={(e) => setField(f.key, e.target.value)}
              className="w-full border rounded px-2 py-1 text-sm" />
          </div>
        ))}
      </div>

      <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">External Usage (RON)</h3>
      <div className="grid grid-cols-3 gap-3 mb-4">
        {EXTERNAL_FIELDS.map((f) => (
          <div key={f.key}>
            <label className="text-xs text-gray-600">{f.label}</label>
            <input type="text" placeholder="0"
              onChange={(e) => setField(f.key, e.target.value)}
              className="w-full border rounded px-2 py-1 text-sm" />
          </div>
        ))}
      </div>

      <button onClick={handleGenerate} disabled={loading}
        className="bg-blue-600 text-white px-6 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50">
        {loading ? "Generating..." : "Generate Excel Report"}
      </button>

      {error && <p className="text-red-600 text-sm mt-2">{error}</p>}

      {results && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Allocation Preview</h3>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="text-left p-2 border">Company</th>
                <th className="text-right p-2 border">Elec.</th>
                <th className="text-right p-2 border">Water</th>
                <th className="text-right p-2 border">Garb.</th>
                <th className="text-right p-2 border">Gas(H)</th>
                <th className="text-right p-2 border">Gas(GF)</th>
                <th className="text-right p-2 border">Gas(1F)</th>
                <th className="text-right p-2 border font-bold">Total</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.company_id} className="hover:bg-gray-50">
                  <td className="p-2 border">{r.company_name}</td>
                  <td className="p-2 border text-right">{r.electricity.toFixed(2)}</td>
                  <td className="p-2 border text-right">{r.water.toFixed(2)}</td>
                  <td className="p-2 border text-right">{r.garbage.toFixed(2)}</td>
                  <td className="p-2 border text-right">{r.gas_hotel.toFixed(2)}</td>
                  <td className="p-2 border text-right">{r.gas_ground_floor.toFixed(2)}</td>
                  <td className="p-2 border text-right">{r.gas_first_floor.toFixed(2)}</td>
                  <td className="p-2 border text-right font-bold">{r.total.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {runId && (
            <a href={getExcelUrl(runId)} download={filename}
              className="inline-block mt-3 bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700">
              Download {filename}
            </a>
          )}
        </div>
      )}
    </div>
  );
}
