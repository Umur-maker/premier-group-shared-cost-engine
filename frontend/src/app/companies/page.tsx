"use client";

import { useEffect, useState } from "react";
import { getCompanies, createCompany, updateCompany, API_BASE } from "@/lib/api";
import { useApp } from "@/lib/AppContext";
import { tr, floorLabel } from "@/lib/i18n";
import { PageLayout, SectionCard, FormRow, Button } from "@/components";
import type { Company } from "@/types";

// Building and floor options
const BUILDINGS = ["C1", "C4", "C5", "Mendeleev", "Vitan Plaza"];
const FLOORS = ["ground_floor", "first_floor", "hotel"];
const EMPTY: Partial<Company> = {
  name: "", area_m2: 0, headcount_default: 1, building: "C4", floor: "ground_floor",
  has_heating: true, electricity_eligible: true, water_eligible: true, garbage_eligible: true,
  office_no: "", contact_person: "", phone: "", email: "",
  beginning_date: "", expiration_date: "", notes: "", monthly_rent_eur: 0,
};

export default function CompaniesPage() {
  const { lang } = useApp();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<Partial<Company>>({ ...EMPTY });

  const load = async () => {
    try { setCompanies(await getCompanies()); } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error"); }
  };
  useEffect(() => { load(); }, []);

  const f = (key: keyof Company, val: string | number | boolean) =>
    setForm((p) => ({ ...p, [key]: val }));

  const handleAdd = async () => {
    setError("");
    try {
      await createCompany(form);
      setForm({ ...EMPTY }); setShowAdd(false); await load();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
  };

  const startEdit = (c: Company) => { setEditId(c.id); setForm({ ...c }); };

  const handleSave = async () => {
    if (!editId) return;
    setError("");
    try {
      await updateCompany(editId, form);
      setEditId(null); await load();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
  };

  const inputCls = "w-full border dark:border-gray-600 rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-700";

  const renderForm = (isEdit: boolean) => (
    <div className="space-y-4">
      <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{tr("companies.basic", lang)}</p>
      <div className="grid grid-cols-6 gap-3">
        <FormRow label={tr("companies.name", lang)} className="col-span-2">
          <input value={form.name || ""} onChange={(e) => f("name", e.target.value)} className={inputCls} />
        </FormRow>
        <FormRow label={tr("companies.building", lang)}>
          <select value={form.building || "C4"} onChange={(e) => f("building", e.target.value)} className={inputCls}>
            {BUILDINGS.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>
        </FormRow>
        <FormRow label={tr("companies.floor", lang)}>
          <select value={form.floor || "ground_floor"} onChange={(e) => f("floor", e.target.value)} className={inputCls}>
            {FLOORS.map((fl) => <option key={fl} value={fl}>{floorLabel(fl, lang)}</option>)}
          </select>
        </FormRow>
        <FormRow label={tr("companies.office_no", lang)}>
          <input value={form.office_no || ""} onChange={(e) => f("office_no", e.target.value)} className={inputCls} />
        </FormRow>
        <FormRow label={tr("companies.area", lang)}>
          <input type="number" step="0.01" value={form.area_m2 || 0}
            onChange={(e) => f("area_m2", parseFloat(e.target.value))} className={inputCls} />
        </FormRow>
      </div>
      <div className="grid grid-cols-6 gap-3">
        <FormRow label={tr("companies.persons", lang)}>
          <input type="number" min={0} value={form.headcount_default || 0}
            onChange={(e) => f("headcount_default", parseInt(e.target.value))} className={inputCls} />
        </FormRow>
        <FormRow label={tr("companies.rent", lang)}>
          <input type="number" step="1" min={0} value={form.monthly_rent_eur || 0}
            onChange={(e) => f("monthly_rent_eur", parseFloat(e.target.value) || 0)} className={inputCls} />
        </FormRow>
      </div>

      <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{tr("companies.utilities", lang)}</p>
      <div className="flex gap-6 flex-wrap">
        {([["has_heating", "companies.heating"], ["electricity_eligible", "field.electricity"],
           ["water_eligible", "field.water"], ["garbage_eligible", "field.garbage"]] as const).map(([key, label]) => (
          <label key={key} className="flex items-center gap-1.5 text-sm">
            <input type="checkbox" checked={!!form[key as keyof Company]}
              onChange={(e) => f(key as keyof Company, e.target.checked)} />
            {tr(label, lang)}
          </label>
        ))}
        {isEdit && (
          <label className="flex items-center gap-1.5 text-sm">
            <input type="checkbox" checked={!!form.active}
              onChange={(e) => f("active", e.target.checked)} />
            {tr("companies.active", lang)}
          </label>
        )}
      </div>

      <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">{tr("companies.contact_details", lang)}</p>
      <div className="grid grid-cols-4 gap-3">
        <FormRow label={tr("companies.contact", lang)}>
          <input value={form.contact_person || ""} onChange={(e) => f("contact_person", e.target.value)} className={inputCls} />
        </FormRow>
        <FormRow label={tr("companies.phone", lang)}>
          <input value={form.phone || ""} onChange={(e) => f("phone", e.target.value)} className={inputCls} />
        </FormRow>
        <FormRow label={tr("companies.email", lang)}>
          <input value={form.email || ""} onChange={(e) => f("email", e.target.value)} className={inputCls} />
        </FormRow>
        <div />
        <FormRow label={tr("companies.begin_date", lang)}>
          <input value={form.beginning_date || ""} onChange={(e) => f("beginning_date", e.target.value)} className={inputCls} />
        </FormRow>
        <FormRow label={tr("companies.end_date", lang)}>
          <input value={form.expiration_date || ""} onChange={(e) => f("expiration_date", e.target.value)} className={inputCls} />
        </FormRow>
        <FormRow label={tr("companies.notes", lang)} className="col-span-2">
          <textarea value={form.notes || ""} onChange={(e) => f("notes", e.target.value)} rows={2} className={inputCls} />
        </FormRow>
      </div>

      <div className="flex gap-2">
        <Button onClick={isEdit ? handleSave : handleAdd}>
          {isEdit ? tr("companies.save", lang) : tr("companies.save_new", lang)}
        </Button>
        <Button variant="secondary" onClick={() => { setShowAdd(false); setEditId(null); }}>
          {tr("companies.cancel", lang)}
        </Button>
      </div>
    </div>
  );

  return (
    <PageLayout title={tr("companies.title", lang)}>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      <SectionCard>
        <div className="flex items-center justify-between">
          <span className="text-sm">
            {companies.filter((c) => c.active).length} {tr("companies.active_count", lang)}
          </span>
          {!showAdd && !editId && (
            <Button onClick={() => { setShowAdd(true); setForm({ ...EMPTY }); }}>
              {tr("companies.add", lang)}
            </Button>
          )}
        </div>
        {showAdd && <div className="mt-4 pt-4 border-t dark:border-gray-700">{renderForm(false)}</div>}
      </SectionCard>

      {editId && (
        <SectionCard title={`${tr("companies.edit", lang)}: ${form.name}`}>
          {renderForm(true)}
        </SectionCard>
      )}

      <SectionCard title={tr("companies.title", lang)}>
        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-navy text-white">
                <th className="p-2.5 text-left text-xs uppercase tracking-wide">#</th>
                <th className="p-2.5 text-left text-xs uppercase tracking-wide">{tr("companies.name", lang)}</th>
                <th className="p-2.5 text-left text-xs uppercase tracking-wide">{tr("companies.building", lang)}</th>
                <th className="p-2.5 text-left text-xs uppercase tracking-wide">{tr("companies.floor", lang)}</th>
                <th className="p-2.5 text-left text-xs uppercase tracking-wide">{tr("companies.office_no", lang)}</th>
                <th className="p-2.5 text-right text-xs uppercase tracking-wide">{tr("companies.area", lang)}</th>
                <th className="p-2.5 text-right text-xs uppercase tracking-wide">{tr("companies.persons", lang)}</th>
                <th className="p-2.5 text-center text-xs uppercase tracking-wide">{tr("companies.active", lang)}</th>
                <th className="p-2.5 text-xs uppercase tracking-wide"></th>
              </tr>
            </thead>
            <tbody>
              {companies.map((c, i) => (
                <tr key={c.id}
                  className={`${i % 2 === 0 ? "bg-white dark:bg-card-dark" : "bg-gray-50/60 dark:bg-gray-800/40"}
                    hover:bg-blue-50/50 dark:hover:bg-navy-light/10 transition-colors
                    ${!c.active ? "opacity-50" : ""}`}>
                  <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-gray-400">{i + 1}</td>
                  <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 font-medium">{c.name}</td>
                  <td className="p-2.5 border-b border-gray-100 dark:border-gray-700">{c.building}</td>
                  <td className="p-2.5 border-b border-gray-100 dark:border-gray-700">{floorLabel(c.floor, lang)}</td>
                  <td className="p-2.5 border-b border-gray-100 dark:border-gray-700">{c.office_no || "—"}</td>
                  <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums">{c.area_m2} m²</td>
                  <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-right tabular-nums">{c.headcount_default}</td>
                  <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 text-center">{c.active ? "🟢" : "🔴"}</td>
                  <td className="p-2.5 border-b border-gray-100 dark:border-gray-700 space-x-2">
                    <button onClick={() => startEdit(c)}
                      className="text-xs text-blue-600 hover:underline">
                      {tr("companies.edit", lang)}
                    </button>
                    {c.active && c.electricity_eligible && (
                      <a href={`${API_BASE}/api/calculate/agreement/${c.id}?language=${lang}`}
                        download className="text-xs text-navy dark:text-blue-300 hover:underline">
                        {tr("companies.agreement", lang)}
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </PageLayout>
  );
}
