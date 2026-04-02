"use client";

import { useEffect, useState } from "react";
import { getSettings, saveSettings } from "@/lib/api";
import { PageLayout, SectionCard, Button } from "@/components";
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

  if (!settings || !pending) return <p className="p-6 text-gray-500">Loading...</p>;

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
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
  };

  return (
    <PageLayout title="Settings">
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {/* Allocation Ratios */}
      <SectionCard title="Allocation Ratios">
        <p className="text-xs text-gray-400 mb-4">
          Edit sqm %. Person % is calculated automatically (100 - sqm %).
        </p>
        <div className="space-y-3">
          {EXPENSE_TYPES.map((et) => {
            const r = pending.ratios[et];
            return (
              <div key={et} className="flex items-center gap-4">
                <span className="w-28 text-sm capitalize font-medium">{et}</span>
                <label className="text-xs text-gray-500">sqm %</label>
                <input type="number" min={0} max={100} step={5} value={r.sqm_weight}
                  onChange={(e) => setSqm(et, +e.target.value)}
                  className="border rounded px-2 py-1.5 w-20 text-sm text-center" />
                <span className="text-sm text-blue-600 font-semibold">
                  person: {r.headcount_weight}%
                </span>
              </div>
            );
          })}
        </div>
        {changed && (
          <div className="mt-4 pt-3 border-t border-gray-200">
            <p className="text-yellow-600 text-xs mb-2">Unsaved changes</p>
            <Button onClick={handleSave}>Save Settings</Button>
          </div>
        )}
        {saved && <p className="text-green-600 text-xs mt-2">Settings saved.</p>}
      </SectionCard>

      {/* Language */}
      <SectionCard title="Language">
        <p className="text-xs text-gray-400 mb-2">
          Language affects Excel report labels and month names.
        </p>
        <select className="border rounded px-2 py-1.5 text-sm">
          <option value="en">English</option>
          <option value="ro">Romanian</option>
        </select>
      </SectionCard>

      {/* Appearance */}
      <SectionCard title="Appearance">
        <p className="text-xs text-gray-400 mb-2">Theme preference (coming in Phase 4).</p>
        <div className="flex gap-3">
          <label className="flex items-center gap-1 text-sm">
            <input type="radio" name="theme" value="light" defaultChecked /> Light
          </label>
          <label className="flex items-center gap-1 text-sm">
            <input type="radio" name="theme" value="dark" /> Dark
          </label>
        </div>
      </SectionCard>
    </PageLayout>
  );
}
