"use client";

import { useState } from "react";
import { useApp } from "@/lib/AppContext";
import { tr } from "@/lib/i18n";
import { PageLayout, SectionCard } from "@/components";

const SECTIONS = [
  { key: "monthly", icon: "1" },
  { key: "companies", icon: "2" },
  { key: "payments", icon: "3" },
  { key: "history", icon: "4" },
  { key: "reports", icon: "5" },
  { key: "manager", icon: "6" },
  { key: "settings", icon: "7" },
  { key: "formula", icon: "f(x)" },
] as const;

const STEPS: Record<string, number> = {
  monthly: 6, companies: 3, payments: 3, history: 4,
  reports: 3, manager: 5, settings: 3, formula: 7,
};

export default function GuidePage() {
  const { lang } = useApp();
  const [expanded, setExpanded] = useState<string | null>("monthly");

  return (
    <PageLayout title={tr("guide.title", lang)}>
      <SectionCard>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
          {tr("guide.welcome", lang)}
        </p>
      </SectionCard>

      <div className="space-y-3">
        {SECTIONS.map(({ key, icon }) => {
          const isOpen = expanded === key;
          const stepCount = STEPS[key];

          return (
            <SectionCard key={key} className={isOpen ? "ring-1 ring-navy/20 dark:ring-blue-400/30" : ""}>
              <button
                onClick={() => setExpanded(isOpen ? null : key)}
                className="w-full flex items-center gap-3 text-left"
              >
                <span className={`w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold shrink-0
                  ${isOpen
                    ? "bg-navy text-white"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
                  }`}>
                  {icon}
                </span>
                <span className={`text-sm font-semibold flex-1 ${isOpen ? "text-navy dark:text-white" : "text-gray-700 dark:text-gray-300"}`}>
                  {tr(`guide.${key}_title`, lang)}
                </span>
                <span className="text-gray-400 text-xs">{isOpen ? "▲" : "▼"}</span>
              </button>

              {isOpen && (
                <div className="mt-4 pl-12 space-y-2.5">
                  {Array.from({ length: stepCount }, (_, i) => (
                    <div key={i} className="flex gap-3 items-start">
                      <span className="w-5 h-5 rounded-full bg-navy/10 dark:bg-blue-400/15 text-navy dark:text-blue-300 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                        {i + 1}
                      </span>
                      <p className={`text-sm leading-relaxed text-gray-600 dark:text-gray-400 ${
                        key === "formula" && i === 1 ? "font-mono bg-gray-50 dark:bg-gray-800 px-3 py-2 rounded-lg text-navy dark:text-blue-300 text-xs" : ""
                      }`}>
                        {tr(`guide.${key}_${i + 1}`, lang)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>
          );
        })}
      </div>
    </PageLayout>
  );
}
