"use client";

import { useEffect, useState } from "react";
import { getHistory, deleteRun, getHistoryExcelUrl } from "@/lib/api";
import type { HistoryEntry } from "@/types";

const MONTHS = [
  "","January","February","March","April","May","June",
  "July","August","September","October","November","December",
];

export default function HistoryPage() {
  const [runs, setRuns] = useState<HistoryEntry[]>([]);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setRuns(await getHistory());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteRun(id);
      await load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Run History</h2>
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}

      {runs.length === 0 ? (
        <p className="text-gray-500 text-sm">No past runs yet.</p>
      ) : (
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-gray-100">
              <th className="text-left p-2 border">Period</th>
              <th className="text-left p-2 border">Generated</th>
              <th className="text-right p-2 border">Companies</th>
              <th className="text-left p-2 border">Language</th>
              <th className="p-2 border">Actions</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="p-2 border">{MONTHS[r.month]} {r.year}</td>
                <td className="p-2 border">{r.generated_at.slice(0, 10)}</td>
                <td className="p-2 border text-right">{r.company_count}</td>
                <td className="p-2 border uppercase">{r.language}</td>
                <td className="p-2 border space-x-2">
                  <a href={getHistoryExcelUrl(r.id)} download
                    className="text-blue-600 hover:underline text-xs">Download</a>
                  <button onClick={() => handleDelete(r.id)}
                    className="text-red-600 hover:underline text-xs">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
