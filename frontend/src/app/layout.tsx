import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "./sidebar";
import { AppProvider } from "@/lib/AppContext";

export const metadata: Metadata = {
  title: "Premier Business Center",
  description: "Shared Cost Engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen flex bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors">
        <AppProvider>
          <Sidebar />
          <main className="flex-1 p-6 overflow-auto">{children}</main>
        </AppProvider>
      </body>
    </html>
  );
}
