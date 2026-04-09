"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { Toast } from "@/components";

interface AppState {
  lang: string;
  setLang: (l: string) => void;
  theme: "light" | "dark";
  setTheme: (t: "light" | "dark") => void;
  showToast: (message: string, type: "success" | "error") => void;
}

const AppContext = createContext<AppState>({
  lang: "en", setLang: () => {},
  theme: "light", setTheme: () => {},
  showToast: () => {},
});

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState("en");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("pbc_lang");
    if (saved) setLang(saved);
    const savedTheme = localStorage.getItem("pbc_theme") as "light" | "dark" | null;
    if (savedTheme) setTheme(savedTheme);
  }, []);

  const handleSetLang = (l: string) => {
    setLang(l);
    localStorage.setItem("pbc_lang", l);
  };

  const handleSetTheme = (t: "light" | "dark") => {
    setTheme(t);
    localStorage.setItem("pbc_theme", t);
  };

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  const showToast = useCallback((message: string, type: "success" | "error") => {
    setToast({ message, type });
  }, []);

  const clearToast = useCallback(() => setToast(null), []);

  return (
    <AppContext.Provider value={{ lang, setLang: handleSetLang, theme, setTheme: handleSetTheme, showToast }}>
      {children}
      {toast && <Toast message={toast.message} type={toast.type} onClose={clearToast} />}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}
