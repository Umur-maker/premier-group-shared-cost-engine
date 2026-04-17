"use client";

import { useEffect, useState } from "react";
import { useRef } from "react";
import { getSettings, saveSettings, getBackupUrl, importCompanies, exportCompaniesUrl, listBackups, restoreBackup, saveMeetingRoom } from "@/lib/api";
import { useApp } from "@/lib/AppContext";
import { tr } from "@/lib/i18n";
import { PageLayout, SectionCard, Button } from "@/components";
import type { Settings } from "@/types";

const RATIO_TYPES = ["electricity", "gas", "water", "garbage", "consumables"] as const;

export default function SettingsPage() {
  const { lang, setLang, theme, setTheme, showToast } = useApp();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dataDir, setDataDir] = useState<string>("");
  const [backups, setBackups] = useState<{ id: string; timestamp: string; companies_count: number }[]>([]);

  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const api = (globalThis as any).window?.electronAPI;
    if (api?.getDataDir) {
      api.getDataDir().then(setDataDir);
    }
    listBackups().then((res) => setBackups(res.backups || [])).catch(() => {});
  }, []);

  const formatTimestamp = (ts: string) => {
    // "YYYYMMDD_HHMMSS" → "YYYY-MM-DD HH:MM:SS"
    if (ts.length !== 15 || !ts.includes("_")) return ts;
    const d = ts.slice(0, 8);
    const t = ts.slice(9);
    return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)} ${t.slice(0, 2)}:${t.slice(2, 4)}:${t.slice(4, 6)}`;
  };
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

  const changed = JSON.stringify(settings) !== JSON.stringify(pending);

  const setSqm = (type: string, val: number) => {
    setPending((prev) => prev ? {
      ...prev,
      ratios: { ...prev.ratios, [type]: { sqm_weight: val, headcount_weight: 100 - val } },
    } : prev);
    setSaved(false);
  };

  const setFinancial = (key: keyof Settings, val: number) => {
    setPending((prev) => prev ? { ...prev, [key]: val } : prev);
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
          {RATIO_TYPES.map((et) => {
            const r = pending.ratios[et];
            if (!r) return null;
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
      </SectionCard>

      <SectionCard title={tr("settings.financial", lang)}>
        <p className="text-xs text-gray-400 mb-4">{tr("settings.financial_help", lang)}</p>
        <div>
          <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
            {tr("settings.eur_rate", lang)}
          </label>
          <input type="number" step="0.01" value={pending.eur_ron_rate}
            onChange={(e) => setFinancial("eur_ron_rate", +e.target.value)}
            className="w-48 border dark:border-gray-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-gray-700" />
          <p className="text-xs text-gray-400 mt-2">{tr("settings.eur_rate_note", lang)}</p>
        </div>
      </SectionCard>

      {/* Meeting Room Settings */}
      <SectionCard title={tr("settings.meeting_room", lang)}>
        <p className="text-xs text-gray-400 mb-4">{tr("settings.meeting_room_desc", lang)}</p>
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={!!pending.meeting_room?.active}
              onChange={(e) => setPending(p => p ? {
                ...p,
                meeting_room: { active: e.target.checked, area_m2: p.meeting_room?.area_m2 || 0, floor: p.meeting_room?.floor || "first_floor" },
              } : p)} />
            {tr("settings.meeting_room_active", lang)}
          </label>
          <div>
            <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
              {tr("settings.meeting_room_area", lang)}
            </label>
            <input type="number" step="0.01" min="0"
              value={pending.meeting_room?.area_m2 || 0}
              disabled={!pending.meeting_room?.active}
              onChange={(e) => setPending(p => p ? {
                ...p,
                meeting_room: { active: p.meeting_room?.active || false, area_m2: +e.target.value, floor: p.meeting_room?.floor || "first_floor" },
              } : p)}
              className="w-48 border dark:border-gray-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-gray-700 disabled:opacity-50" />
          </div>
          <Button variant="secondary" onClick={async () => {
            const mr = pending.meeting_room || { active: false, area_m2: 0, floor: "first_floor" };
            try {
              await saveMeetingRoom({ active: mr.active, area_m2: mr.area_m2, floor: mr.floor });
              setSettings(s => s ? { ...s, meeting_room: mr } : s);
              showToast(tr("settings.meeting_room_saved", lang), "success");
            } catch (e: unknown) {
              showToast(e instanceof Error ? e.message : "Error", "error");
            }
          }}>
            {tr("settings.save", lang)}
          </Button>
        </div>
      </SectionCard>

      {changed && (
        <div className="flex items-center gap-3">
          <p className="text-yellow-600 text-xs">{tr("settings.unsaved", lang)}</p>
          <Button onClick={handleSave}>{tr("settings.save", lang)}</Button>
        </div>
      )}
      {saved && <p className="text-green-600 text-xs">{tr("settings.saved", lang)}</p>}

      <SectionCard title={tr("settings.language", lang)}>
        <p className="text-xs text-gray-400 mb-2">{tr("settings.language_help", lang)}</p>
        <select value={lang} onChange={(e) => setLang(e.target.value)}
          className="border dark:border-gray-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-gray-700">
          <option value="en">English</option>
          <option value="ro">Romana</option>
          <option value="tr">Turkce</option>
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

      <SectionCard title={tr("settings.import_companies", lang)}>
        <p className="text-sm text-gray-500 mb-3">{tr("settings.import_desc", lang)}</p>
        <div className="flex gap-3">
          <input type="file" accept=".json" ref={fileInputRef} className="hidden"
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              if (!confirm(tr("settings.import_desc", lang))) {
                if (fileInputRef.current) fileInputRef.current.value = "";
                return;
              }
              try {
                const result = await importCompanies(file);
                showToast(tr("settings.import_success", lang).replace("{count}", String(result.count)), "success");
              } catch (err: unknown) {
                showToast(err instanceof Error ? err.message : "Import failed", "error");
              }
              if (fileInputRef.current) fileInputRef.current.value = "";
            }} />
          <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
            {tr("settings.import_btn", lang)}
          </Button>
        </div>
      </SectionCard>

      <SectionCard title={tr("settings.export_companies", lang)}>
        <p className="text-sm text-gray-500 mb-3">{tr("settings.export_desc", lang)}</p>
        <Button variant="secondary" onClick={async () => {
          try {
            const res = await fetch(exportCompaniesUrl());
            const data = await res.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "companies.json";
            a.click();
            URL.revokeObjectURL(url);
          } catch { showToast("Export failed", "error"); }
        }}>
          {tr("settings.export_companies", lang)}
        </Button>
      </SectionCard>

      {dataDir && (
        <SectionCard title={tr("settings.data_location", lang)}>
          <p className="text-sm text-gray-500 mb-3">{tr("settings.data_location_desc", lang)}</p>
          <div className="flex flex-col gap-2">
            <div className="text-xs text-gray-600 dark:text-gray-400">
              <span className="font-semibold">{tr("settings.current_path", lang)}:</span>
              <span className="ml-2 font-mono break-all">{dataDir}</span>
            </div>
            <div>
              <Button variant="secondary" onClick={async () => {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const api = (globalThis as any).window?.electronAPI;
                if (!api) return;
                const selected = await api.selectDataDir();
                if (!selected) return;
                const result = await api.setDataDir(selected);
                if (result.success) {
                  showToast(tr("settings.restart_required", lang), "success");
                } else {
                  showToast(result.error || "Failed", "error");
                }
              }}>
                {tr("settings.change_location", lang)}
              </Button>
            </div>
          </div>
        </SectionCard>
      )}

      <SectionCard title={tr("settings.backup", lang)}>
        <p className="text-sm text-gray-500 mb-3">{tr("settings.backup_desc", lang)}</p>
        <a href={getBackupUrl()} download>
          <Button variant="secondary">{tr("settings.backup", lang)}</Button>
        </a>
      </SectionCard>

      <SectionCard title={tr("settings.auto_backups", lang)}>
        <p className="text-sm text-gray-500 mb-3">{tr("settings.auto_backups_desc", lang)}</p>
        {backups.length === 0 ? (
          <p className="text-sm text-gray-400 italic">{tr("settings.no_backups", lang)}</p>
        ) : (
          <div className="max-h-64 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
            {backups.map((b, i) => (
              <div key={b.id}
                className={`flex items-center justify-between px-3 py-2 text-sm
                  ${i % 2 === 0 ? "bg-white dark:bg-card-dark" : "bg-gray-50/60 dark:bg-gray-800/40"}`}>
                <div>
                  <span className="font-mono text-xs text-gray-600 dark:text-gray-400">
                    {formatTimestamp(b.timestamp)}
                  </span>
                  <span className="ml-3 text-xs text-gray-400">
                    {b.companies_count} {tr("settings.backup_companies", lang)}
                  </span>
                </div>
                <Button variant="secondary" className="text-xs px-3 py-1"
                  onClick={async () => {
                    if (!confirm(tr("settings.restore_confirm", lang))) return;
                    try {
                      await restoreBackup(b.id);
                      showToast(tr("settings.restore_success", lang), "success");
                      setTimeout(() => window.location.reload(), 1500);
                    } catch (err: unknown) {
                      showToast(err instanceof Error ? err.message : "Restore failed", "error");
                    }
                  }}>
                  {tr("settings.restore_backup", lang)}
                </Button>
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </PageLayout>
  );
}
