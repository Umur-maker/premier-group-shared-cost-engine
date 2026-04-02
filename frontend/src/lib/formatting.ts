/**
 * Format a number as Romanian currency: 5.325,54 RON
 */
export function formatRon(value: number): string {
  if (value === 0) return "0,00 RON";
  const neg = value < 0;
  const abs = Math.abs(value);
  const int = Math.floor(abs);
  const dec = Math.round((abs - int) * 100);
  const intStr = int.toLocaleString("de-DE"); // dots as thousands separator
  const result = `${intStr},${String(dec).padStart(2, "0")} RON`;
  return neg ? `-${result}` : result;
}

/**
 * Parse user input that may use comma or dot as decimal separator.
 * Returns 0 for empty strings.
 */
export function parseRonInput(val: string): number {
  let v = val.trim().replace(/\s/g, "").replace(/RON|ron|Lei|lei/g, "").trim();
  if (!v) return 0;

  const hasDot = v.includes(".");
  const hasComma = v.includes(",");

  if (hasDot && hasComma) {
    if (v.lastIndexOf(",") > v.lastIndexOf(".")) {
      v = v.replace(/\./g, "").replace(",", ".");
    } else {
      v = v.replace(/,/g, "");
    }
  } else if (hasComma && !hasDot) {
    const parts = v.split(",");
    if (parts.length === 2 && parts[1].length <= 2) {
      v = v.replace(",", ".");
    } else {
      v = v.replace(/,/g, "");
    }
  }

  const num = parseFloat(v);
  if (isNaN(num) || num < 0) throw new Error("Invalid amount");
  return num;
}
