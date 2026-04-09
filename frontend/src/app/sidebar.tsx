"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/lib/AppContext";
import { tr } from "@/lib/i18n";

export function Sidebar() {
  const pathname = usePathname();
  const { lang } = useApp();

  const nav = [
    { href: "/", label: tr("nav.monthly", lang) },
    { href: "/payments", label: tr("nav.payments", lang) },
    { href: "/companies", label: tr("nav.companies", lang) },
    { href: "/history", label: tr("nav.history", lang) },
    { href: "/reports", label: tr("nav.reports", lang) },
    { href: "/manager", label: tr("nav.manager", lang) },
    { href: "/settings", label: tr("nav.settings", lang) },
    { href: "/guide", label: tr("nav.guide", lang) },
  ];

  return (
    <aside className="w-60 bg-sidebar-bg dark:bg-sidebar-dark flex-shrink-0 flex flex-col shadow-lg">
      <div className="px-5 pt-6 pb-4">
        <Image src="/logo.png" alt="Premier Business Center" width={180} height={60}
          className="mb-3" priority />
        <p className="text-[10px] text-blue-200/70 tracking-widest uppercase font-medium">
          {tr("app.subtitle", lang)}
        </p>
      </div>

      <div className="mx-5 border-t border-white/10" />

      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map((item) => (
          <Link key={item.href} href={item.href}
            className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-[13px] font-medium
              transition-all duration-150 ${
              pathname === item.href
                ? "bg-accent text-white shadow-sm"
                : "text-blue-100/80 hover:bg-white/8 hover:text-white"
            }`}>
            {pathname === item.href && (
              <span className="w-1 h-4 bg-white/60 rounded-full" />
            )}
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="px-5 pb-4 text-[10px] text-blue-300/30 font-medium">
        v3.1.1
      </div>
    </aside>
  );
}
