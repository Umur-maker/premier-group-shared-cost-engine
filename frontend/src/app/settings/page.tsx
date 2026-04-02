"use client";

import { useEffect, useState } from "react";
import { getSettings, saveSettings } from "@/lib/api";
import type { Settings } from "@/types";

const EXPENSE_TYPES = ["electricity", "gas", "water", "garbage"] as const;

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [pending, setPending] = useState<Settings | null>(null);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getSettings().then((s) => { setSettings(s); setPending(s); });
  }, []);

  if (!settings || !pending) return <p>Loading...</p>;

  const changed = JSON.stringify(settings.ratios) !== JSON.stringify(pending.ratios);

  const setSqm = (type: string, val: number) => {
    setPending((prev) => prev ? {
      ...prev,
      ratios: { ...prev.ratios, [type]: { sqm_weight: val, headcount_weight: 100 - val } },
    } : prev);
    setSaved(false);
  };

  const handleSave = async () => {
    setError("");
    try {
      await saveSettings(pending);
      setSettings(pending);
      setSaved(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Settings</h2>
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}

      <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Allocation Ratios</h3>
      <p className="text-xs text-gray-400 mb-3">Edit sqm %. Person % is calculated automatically.</p>

      <div className="space-y-3">
        {EXPENSE_TYPES.map((et) => {
          const r = pending.ratios[et];
          return (
            <div key={et} className="flex items-center gap-4">
              <span className="w-28 text-sm capitalize">{et}</span>
              <label className="text-xs text-gray-500">sqm %</label>
              <input type="number" min={0} max={100} step={5} value={r.sqm_weight}
                onChange={(e) => setSqm(et, +e.target.value)}
                className="border rounded px-2 py-1 w-20 text-sm" />
              <span className="text-sm text-blue-600 font-semibold">
                person %: {r.headcount_weight}
              </span>
            </div>
          );
        })}
      </div>

      {changed && (
        <div className="mt-4">
          <p className="text-yellow-600 text-sm mb-2">You have unsaved changes.</p>
          <button onClick={handleSave}
            className="bg-blue-600 text-white px-4 py-1 rounded text-sm hover:bg-blue-700">
            Save Settings
          </button>
        </div>
      )}
      {saved && <p className="text-green-600 text-sm mt-2">Settings saved.</p>}
    </div>
  );
}
