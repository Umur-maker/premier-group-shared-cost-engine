"use client";

import { createContext, useContext, useState, useEffect } from "react";

interface AppState {
  lang: string;
  setLang: (l: string) => void;
  theme: "light" | "dark";
  setTheme: (t: "light" | "dark") => void;
}

const AppContext = createContext<AppState>({
  lang: "en", setLang: () => {},
  theme: "light", setTheme: () => {},
});

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState("en");
  const [theme, setTheme] = useState<"light" | "dark">("light");

  // Persist to localStorage
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

  // Apply theme class to html element
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  return (
    <AppContext.Provider value={{ lang, setLang: handleSetLang, theme, setTheme: handleSetTheme }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}
