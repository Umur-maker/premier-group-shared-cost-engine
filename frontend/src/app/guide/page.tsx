"use client";

import { useState } from "react";
import { useApp } from "@/lib/AppContext";
import { tr } from "@/lib/i18n";
import { PageLayout, SectionCard } from "@/components";

const CATEGORIES = [
  {
    category: "getting_started",
    sections: [
      { key: "quickstart", icon: "\u26a1" },
      { key: "first_month", icon: "\ud83d\udcc5" },
    ],
  },
  {
    category: "daily_work",
    sections: [
      { key: "monthly", icon: "\ud83d\udcdd" },
      { key: "payments", icon: "\ud83d\udcb3" },
      { key: "companies", icon: "\ud83c\udfe2" },
    ],
  },
  {
    category: "review",
    sections: [
      { key: "history", icon: "\ud83d\udcc2" },
      { key: "reports", icon: "\ud83d\udcca" },
      { key: "manager", icon: "\ud83d\udcbc" },
    ],
  },
  {
    category: "system",
    sections: [
      { key: "settings", icon: "\u2699\ufe0f" },
      { key: "data_mgmt", icon: "\ud83d\udbe4" },
      { key: "formula", icon: "\ud83e\uddee" },
    ],
  },
];

const STEPS: Record<string, number> = {
  quickstart: 5, first_month: 6,
  monthly: 8, payments: 5, companies: 6,
  history: 6, reports: 5, manager: 7,
  settings: 5, data_mgmt: 5, formula: 9,
};

export default function GuidePage() {
  const { lang } = useApp();
  const [expanded, setExpanded] = useState<string | null>("quickstart");

  return (
    <PageLayout title={tr("guide.title", lang)}>
      <SectionCard>
        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
          {tr("guide.welcome", lang)}
        </p>
      </SectionCard>

      {CATEGORIES.map(({ category, sections }) => (
        <div key={category}>
          <h3 className="text-[11px] font-bold text-navy/60 dark:text-blue-300/70 uppercase tracking-widest mb-3 mt-2">
            {tr(`guide.cat_${category}`, lang)}
          </h3>
          <div className="space-y-2">
            {sections.map(({ key, icon }) => {
              const isOpen = expanded === key;
              const stepCount = STEPS[key] || 0;

              return (
                <SectionCard key={key} className={isOpen ? "ring-1 ring-navy/20 dark:ring-blue-400/30" : ""}>
                  <button
                    onClick={() => setExpanded(isOpen ? null : key)}
                    className="w-full flex items-center gap-3 text-left"
                  >
                    <span className={`w-9 h-9 rounded-lg flex items-center justify-center text-base shrink-0
                      ${isOpen
                        ? "bg-navy text-white"
                        : "bg-gray-100 dark:bg-gray-700"
                      }`}>
                      {icon}
                    </span>
                    <span className={`text-sm font-semibold flex-1 ${isOpen ? "text-navy dark:text-white" : "text-gray-700 dark:text-gray-300"}`}>
                      {tr(`guide.${key}_title`, lang)}
                    </span>
                    <span className="text-gray-400 text-xs">{isOpen ? "\u25b2" : "\u25bc"}</span>
                  </button>

                  {isOpen && (
                    <div className="mt-4 pl-12 space-y-2.5">
                      {Array.from({ length: stepCount }, (_, i) => {
                        const text = tr(`guide.${key}_${i + 1}`, lang);
                        const isTip = text.startsWith("\u2139\ufe0f") || text.startsWith("TIP:") || text.startsWith("\u0130PUCU:") || text.startsWith("SFAT:");
                        const isWarning = text.startsWith("\u26a0\ufe0f") || text.startsWith("WARNING:") || text.startsWith("UYARI:") || text.startsWith("ATENTIE:");
                        const isFormula = key === "formula" && (i === 1 || i === 4);

                        return (
                          <div key={i} className={`flex gap-3 items-start ${
                            isTip ? "bg-blue-50 dark:bg-blue-900/20 px-3 py-2 rounded-lg -ml-3" :
                            isWarning ? "bg-amber-50 dark:bg-amber-900/20 px-3 py-2 rounded-lg -ml-3" : ""
                          }`}>
                            <span className={`w-5 h-5 rounded-full text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5
                              ${isTip ? "bg-blue-200 dark:bg-blue-700 text-blue-700 dark:text-blue-200" :
                                isWarning ? "bg-amber-200 dark:bg-amber-700 text-amber-700 dark:text-amber-200" :
                                "bg-navy/10 dark:bg-blue-400/15 text-navy dark:text-blue-300"}`}>
                              {isTip ? "i" : isWarning ? "!" : i + 1}
                            </span>
                            <p className={`text-sm leading-relaxed ${
                              isFormula ? "font-mono bg-gray-50 dark:bg-gray-800 px-3 py-2 rounded-lg text-navy dark:text-blue-300 text-xs" :
                              isTip ? "text-blue-700 dark:text-blue-300" :
                              isWarning ? "text-amber-700 dark:text-amber-300" :
                              "text-gray-600 dark:text-gray-400"
                            }`}>
                              {text}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </SectionCard>
              );
            })}
          </div>
        </div>
      ))}
    </PageLayout>
  );
}
