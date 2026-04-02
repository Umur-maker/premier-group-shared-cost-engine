"use client";

import { useEffect, useState } from "react";
import { getCompanies, createCompany, updateCompany } from "@/lib/api";
import { PageLayout, SectionCard, FormRow, Button } from "@/components";
import type { Company } from "@/types";

const FLOORS = ["ground_floor", "first_floor", "mezzanine", "hotel"];
const FLOOR_LABELS: Record<string, string> = {
  ground_floor: "Ground Floor", first_floor: "First Floor",
  mezzanine: "Mezzanine", hotel: "Hotel",
};

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", area: "0", persons: "1", floor: "ground_floor" });

  const load = async () => {
    try { setCompanies(await getCompanies()); } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };
  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    setError("");
    try {
      await createCompany({
        name: form.name, area_m2: parseFloat(form.area),
        headcount_default: parseInt(form.persons), floor: form.floor,
      });
      setForm({ name: "", area: "0", persons: "1", floor: "ground_floor" });
      setShowAdd(false);
      await load();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
  };

  const toggleActive = async (c: Company) => {
    try {
      await updateCompany(c.id, { active: !c.active });
      await load();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
  };

  return (
    <PageLayout title="Companies">
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {/* Add Company */}
      <SectionCard>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">
            {companies.filter((c) => c.active).length} active companies
          </span>
          <Button variant={showAdd ? "secondary" : "primary"} onClick={() => setShowAdd(!showAdd)}>
            {showAdd ? "Cancel" : "+ Add Company"}
          </Button>
        </div>

        {showAdd && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-4 gap-4 mb-3">
              <FormRow label="Company Name">
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full border rounded px-2 py-1.5 text-sm" />
              </FormRow>
              <FormRow label="Area (m²)">
                <input value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })}
                  className="w-full border rounded px-2 py-1.5 text-sm" />
              </FormRow>
              <FormRow label="Persons">
                <input value={form.persons} onChange={(e) => setForm({ ...form, persons: e.target.value })}
                  className="w-full border rounded px-2 py-1.5 text-sm" />
              </FormRow>
              <FormRow label="Floor">
                <select value={form.floor} onChange={(e) => setForm({ ...form, floor: e.target.value })}
                  className="w-full border rounded px-2 py-1.5 text-sm">
                  {FLOORS.map((f) => <option key={f} value={f}>{FLOOR_LABELS[f]}</option>)}
                </select>
              </FormRow>
            </div>
            <Button onClick={handleAdd}>Save New Company</Button>
          </div>
        )}
      </SectionCard>

      {/* Company List */}
      <SectionCard title="Company List">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-50">
              <th className="text-left p-2 border-b">#</th>
              <th className="text-left p-2 border-b">Name</th>
              <th className="text-right p-2 border-b">Area</th>
              <th className="text-right p-2 border-b">Persons</th>
              <th className="text-left p-2 border-b">Floor</th>
              <th className="text-center p-2 border-b">Gas</th>
              <th className="text-center p-2 border-b">Active</th>
              <th className="text-left p-2 border-b">Contact</th>
              <th className="p-2 border-b"></th>
            </tr>
          </thead>
          <tbody>
            {companies.map((c, i) => (
              <tr key={c.id} className={`hover:bg-gray-50 ${!c.active ? "opacity-50" : ""}`}>
                <td className="p-2 border-b text-gray-400">{i + 1}</td>
                <td className="p-2 border-b font-medium">{c.name}</td>
                <td className="p-2 border-b text-right">{c.area_m2} m²</td>
                <td className="p-2 border-b text-right">{c.headcount_default}</td>
                <td className="p-2 border-b">{FLOOR_LABELS[c.floor] || c.floor}</td>
                <td className="p-2 border-b text-center">{c.has_heating ? "✓" : "—"}</td>
                <td className="p-2 border-b text-center">{c.active ? "🟢" : "🔴"}</td>
                <td className="p-2 border-b text-xs text-gray-500">
                  {c.contact_person}{c.phone ? ` · ${c.phone}` : ""}
                </td>
                <td className="p-2 border-b">
                  <button onClick={() => toggleActive(c)}
                    className="text-xs text-blue-600 hover:underline">
                    {c.active ? "Deactivate" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </SectionCard>
    </PageLayout>
  );
}
