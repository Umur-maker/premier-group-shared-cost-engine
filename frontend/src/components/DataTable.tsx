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
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100">
            {columns.map((col) => (
              <th key={col.key}
                className={`p-2 border border-gray-200 text-${col.align || "left"}
                  ${col.bold ? "font-bold" : "font-semibold"} text-gray-700`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={String(row[keyField])} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td key={col.key}
                  className={`p-2 border border-gray-200 text-${col.align || "left"}
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
