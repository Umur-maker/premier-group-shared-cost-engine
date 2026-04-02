"use client";

import { useEffect, useState } from "react";
import { getSettings, saveSettings } from "@/lib/api";
import { useApp } from "@/lib/AppContext";
import { tr } from "@/lib/i18n";
import { PageLayout, SectionCard, Button } from "@/components";
import type { Settings } from "@/types";

const EXPENSE_TYPES = ["electricity", "gas", "water", "garbage"] as const;

export default function SettingsPage() {
  const { lang, setLang, theme, setTheme } = useApp();
  const [settings, setSettings] = useState<Settings | null>(null);
  const [pending, setPending] = useState<Settings | null>(null);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getSettings()
      .then((s) => { setSettings(s); setPending(s); })
      .catch(() => setError(tr("error.backend_down", lang)));
  }, [lang]);

  if (error && !settings) return <p className="p-6 text-red-600">{error}</p>;
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
    <PageLayout title={tr("settings.title", lang)}>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      <SectionCard title={tr("settings.ratios", lang)}>
        <p className="text-xs text-gray-400 mb-4">{tr("settings.ratios_help", lang)}</p>
        <div className="space-y-3">
          {EXPENSE_TYPES.map((et) => {
            const r = pending.ratios[et];
            return (
              <div key={et} className="flex items-center gap-4">
                <span className="w-28 text-sm capitalize font-medium">{et}</span>
                <label className="text-xs text-gray-500">sqm %</label>
                <input type="number" min={0} max={100} step={5} value={r.sqm_weight}
                  onChange={(e) => setSqm(et, +e.target.value)}
                  className="border dark:border-gray-600 rounded px-2 py-1.5 w-20 text-sm text-center
                             bg-white dark:bg-gray-700" />
                <span className="text-sm text-blue-600 dark:text-blue-400 font-semibold">
                  person: {r.headcount_weight}%
                </span>
              </div>
            );
          })}
        </div>
        {changed && (
          <div className="mt-4 pt-3 border-t dark:border-gray-700">
            <p className="text-yellow-600 text-xs mb-2">{tr("settings.unsaved", lang)}</p>
            <Button onClick={handleSave}>{tr("settings.save", lang)}</Button>
          </div>
        )}
        {saved && <p className="text-green-600 text-xs mt-2">{tr("settings.saved", lang)}</p>}
      </SectionCard>

      <SectionCard title={tr("settings.language", lang)}>
        <p className="text-xs text-gray-400 mb-2">{tr("settings.language_help", lang)}</p>
        <select value={lang} onChange={(e) => setLang(e.target.value)}
          className="border dark:border-gray-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-gray-700">
          <option value="en">English</option>
          <option value="ro">Romana</option>
        </select>
      </SectionCard>

      <SectionCard title={tr("settings.appearance", lang)}>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="radio" name="theme" checked={theme === "light"}
              onChange={() => setTheme("light")} />
            {tr("settings.light", lang)}
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="radio" name="theme" checked={theme === "dark"}
              onChange={() => setTheme("dark")} />
            {tr("settings.dark", lang)}
          </label>
        </div>
      </SectionCard>
    </PageLayout>
  );
}
