"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/lib/AppContext";
import { tr } from "@/lib/i18n";

export function Sidebar() {
  const pathname = usePathname();
  const { lang } = useApp();

  const nav = [
    { href: "/", label: tr("nav.monthly", lang) },
    { href: "/companies", label: tr("nav.companies", lang) },
    { href: "/settings", label: tr("nav.settings", lang) },
    { href: "/history", label: tr("nav.history", lang) },
  ];

  return (
    <aside className="w-56 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4 flex-shrink-0">
      <h1 className="text-sm font-bold mb-1">{tr("app.title", lang)}</h1>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">{tr("app.subtitle", lang)}</p>
      <nav className="space-y-1">
        {nav.map((item) => (
          <Link key={item.href} href={item.href}
            className={`block px-3 py-2 rounded text-sm transition-colors ${
              pathname === item.href
                ? "bg-blue-600 text-white"
                : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            }`}>
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
