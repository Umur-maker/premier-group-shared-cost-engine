"use client";

interface MoneyInputProps {
  label: string;
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
}

export function MoneyInput({ label, value, onChange, placeholder = "0" }: MoneyInputProps) {
  return (
    <div>
      <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">{label}</label>
      <div className="flex">
        <input type="text" value={value} onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="flex-1 border border-gray-300 dark:border-gray-600 rounded-l-md px-3 py-1.5 text-sm
                     bg-white dark:bg-gray-700 dark:text-gray-100
                     focus:outline-none focus:ring-1 focus:ring-navy focus:border-navy" />
        <span className="inline-flex items-center px-3 py-1.5 bg-navy text-white
                         text-xs font-bold tracking-wider rounded-r-md border border-navy select-none">
          RON
        </span>
      </div>
    </div>
  );
}
