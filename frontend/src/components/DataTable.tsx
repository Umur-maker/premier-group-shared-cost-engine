/* eslint-disable @typescript-eslint/no-explicit-any */

export interface Column {
  key: string;
  header: string;
  align?: "left" | "right" | "center";
  render?: (row: any) => React.ReactNode;
  bold?: boolean;
}

interface DataTableProps {
  columns: Column[];
  data: any[];
  keyField: string;
}

export function DataTable({ columns, data, keyField }: DataTableProps) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200/80 dark:border-gray-700/60
      shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-navy text-white">
            {columns.map((col) => (
              <th key={col.key}
                className={`px-3 py-3 text-${col.align || "left"}
                  ${col.bold ? "font-bold" : "font-semibold"} text-[11px] uppercase tracking-wider`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={String(row[keyField])}
              className={`${i % 2 === 0 ? "bg-white dark:bg-card-dark" : "bg-gray-50/60 dark:bg-gray-800/40"}
                hover:bg-blue-50/50 dark:hover:bg-navy-light/10 transition-colors duration-100`}>
              {columns.map((col) => (
                <td key={col.key}
                  className={`px-3 py-2.5 border-b border-gray-100/80 dark:border-gray-700/50 text-${col.align || "left"}
                    ${col.bold ? "font-semibold text-navy dark:text-white" : ""} tabular-nums`}>
                  {col.render ? col.render(row) : String(row[col.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
