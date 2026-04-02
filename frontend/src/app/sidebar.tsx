"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Monthly Input" },
  { href: "/companies", label: "Companies" },
  { href: "/settings", label: "Settings" },
  { href: "/history", label: "History" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-white border-r border-gray-200 p-4 flex-shrink-0">
      <h1 className="text-sm font-bold mb-1">Premier Business Center</h1>
      <p className="text-xs text-gray-500 mb-4">Shared Cost Engine</p>
      <nav className="space-y-1">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`block px-3 py-2 rounded text-sm ${
              pathname === item.href
                ? "bg-blue-600 text-white"
                : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
