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
    <div className="overflow-x-auto rounded-md border border-gray-200 dark:border-gray-700">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-navy text-white">
            {columns.map((col) => (
              <th key={col.key}
                className={`p-2.5 text-${col.align || "left"}
                  ${col.bold ? "font-bold" : "font-semibold"} text-xs uppercase tracking-wide`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={String(row[keyField])}
              className={`${i % 2 === 0 ? "bg-white dark:bg-card-dark" : "bg-gray-50 dark:bg-gray-800"}
                hover:bg-blue-50 dark:hover:bg-navy-light/20 transition-colors`}>
              {columns.map((col) => (
                <td key={col.key}
                  className={`p-2.5 border-b border-gray-100 dark:border-gray-700 text-${col.align || "left"}
                    ${col.bold ? "font-bold" : ""}`}>
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
