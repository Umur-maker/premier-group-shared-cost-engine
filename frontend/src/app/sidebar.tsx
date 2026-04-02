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
    { href: "/companies", label: tr("nav.companies", lang) },
    { href: "/settings", label: tr("nav.settings", lang) },
    { href: "/history", label: tr("nav.history", lang) },
  ];

  return (
    <aside className="w-60 bg-sidebar-bg dark:bg-sidebar-dark flex-shrink-0 flex flex-col">
      {/* Logo */}
      <div className="p-5 pb-3">
        <Image src="/logo.png" alt="Premier Business Center" width={180} height={60}
          className="mb-2" priority />
        <p className="text-[11px] text-blue-200 tracking-wide uppercase">
          {tr("app.subtitle", lang)}
        </p>
      </div>

      {/* Divider */}
      <div className="mx-4 border-t border-white/15" />

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-0.5">
        {nav.map((item) => (
          <Link key={item.href} href={item.href}
            className={`block px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
              pathname === item.href
                ? "bg-accent text-white"
                : "text-blue-100 hover:bg-white/10 hover:text-white"
            }`}>
            {item.label}
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 text-[10px] text-blue-300/50">
        v2.0
      </div>
    </aside>
  );
}
