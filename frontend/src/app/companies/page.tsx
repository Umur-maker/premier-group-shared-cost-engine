"use client";

import { useEffect, useState } from "react";
import { getCompanies, createCompany, updateCompany } from "@/lib/api";
import type { Company } from "@/types";

const FLOORS = ["ground_floor", "first_floor", "mezzanine", "hotel"];

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [addName, setAddName] = useState("");
  const [addArea, setAddArea] = useState("0");
  const [addPersons, setAddPersons] = useState("1");
  const [addFloor, setAddFloor] = useState("ground_floor");
  const [editingId, setEditingId] = useState<string | null>(null);

  const load = async () => {
    try {
      setCompanies(await getCompanies());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    setError("");
    try {
      await createCompany({
        name: addName, area_m2: parseFloat(addArea),
        headcount_default: parseInt(addPersons), floor: addFloor,
      });
      setAddName(""); setAddArea("0"); setAddPersons("1"); setShowAdd(false);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  const handleSave = async (c: Company, updates: Partial<Company>) => {
    setError("");
    try {
      await updateCompany(c.id, updates);
      setEditingId(null);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Companies</h2>
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}

      <button onClick={() => setShowAdd(!showAdd)}
        className="bg-blue-600 text-white px-4 py-1 rounded text-sm mb-4 hover:bg-blue-700">
        {showAdd ? "Cancel" : "+ Add Company"}
      </button>

      {showAdd && (
        <div className="border rounded p-4 mb-4 bg-white">
          <div className="grid grid-cols-4 gap-3 mb-3">
            <div>
              <label className="text-xs text-gray-600">Name</label>
              <input value={addName} onChange={(e) => setAddName(e.target.value)}
                className="w-full border rounded px-2 py-1 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-600">Area (m²)</label>
              <input value={addArea} onChange={(e) => setAddArea(e.target.value)}
                className="w-full border rounded px-2 py-1 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-600">Persons</label>
              <input value={addPersons} onChange={(e) => setAddPersons(e.target.value)}
                className="w-full border rounded px-2 py-1 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-600">Floor</label>
              <select value={addFloor} onChange={(e) => setAddFloor(e.target.value)}
                className="w-full border rounded px-2 py-1 text-sm">
                {FLOORS.map((f) => <option key={f} value={f}>{f.replace("_", " ")}</option>)}
              </select>
            </div>
          </div>
          <button onClick={handleAdd}
            className="bg-green-600 text-white px-4 py-1 rounded text-sm hover:bg-green-700">
            Save New Company
          </button>
        </div>
      )}

      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="text-left p-2 border">#</th>
            <th className="text-left p-2 border">Name</th>
            <th className="text-right p-2 border">Area (m²)</th>
            <th className="text-right p-2 border">Persons</th>
            <th className="text-left p-2 border">Floor</th>
            <th className="text-center p-2 border">Heating</th>
            <th className="text-center p-2 border">Active</th>
            <th className="text-left p-2 border">Contact</th>
            <th className="p-2 border"></th>
          </tr>
        </thead>
        <tbody>
          {companies.map((c, i) => (
            <tr key={c.id} className="hover:bg-gray-50">
              <td className="p-2 border">{i + 1}</td>
              <td className="p-2 border">{c.name}</td>
              <td className="p-2 border text-right">{c.area_m2}</td>
              <td className="p-2 border text-right">{c.headcount_default}</td>
              <td className="p-2 border">{c.floor.replace("_", " ")}</td>
              <td className="p-2 border text-center">{c.has_heating ? "Yes" : "No"}</td>
              <td className="p-2 border text-center">{c.active ? "🟢" : "🔴"}</td>
              <td className="p-2 border text-xs text-gray-500">
                {c.contact_person}{c.phone ? ` | ${c.phone}` : ""}
              </td>
              <td className="p-2 border">
                {editingId === c.id ? (
                  <button onClick={() => handleSave(c, { active: !c.active })}
                    className="text-xs text-blue-600 hover:underline">
                    Toggle Active
                  </button>
                ) : (
                  <button onClick={() => setEditingId(c.id)}
                    className="text-xs text-blue-600 hover:underline">
                    Edit
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
