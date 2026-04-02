"use client";

import { useEffect, useState } from "react";
import { getHistory, deleteRun, getHistoryExcelUrl } from "@/lib/api";
import { PageLayout, SectionCard, Button } from "@/components";
import type { HistoryEntry } from "@/types";

const MONTHS = ["","January","February","March","April","May","June",
  "July","August","September","October","November","December"];

export default function HistoryPage() {
  const [runs, setRuns] = useState<HistoryEntry[]>([]);
  const [error, setError] = useState("");

  const load = async () => {
    try { setRuns(await getHistory()); } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };
  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string) => {
    try { await deleteRun(id); await load(); } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    }
  };

  return (
    <PageLayout title="Run History">
      {error && <p className="text-red-600 text-sm">{error}</p>}

      {runs.length === 0 ? (
        <SectionCard>
          <p className="text-gray-500 text-sm">No past runs yet. Generate a report from Monthly Input.</p>
        </SectionCard>
      ) : (
        <SectionCard>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left p-2 border-b">Period</th>
                <th className="text-left p-2 border-b">Generated</th>
                <th className="text-right p-2 border-b">Companies</th>
                <th className="text-left p-2 border-b">Lang</th>
                <th className="p-2 border-b">Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="p-2 border-b font-medium">
                    {MONTHS[r.month]} {r.year}
                  </td>
                  <td className="p-2 border-b text-gray-500">
                    {r.generated_at.slice(0, 10)}
                  </td>
                  <td className="p-2 border-b text-right">{r.company_count}</td>
                  <td className="p-2 border-b uppercase text-gray-500">{r.language}</td>
                  <td className="p-2 border-b space-x-2">
                    <a href={getHistoryExcelUrl(r.id)} download
                      className="text-blue-600 hover:underline text-xs">Download</a>
                    <button onClick={() => handleDelete(r.id)}
                      className="text-red-600 hover:underline text-xs">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>
      )}
    </PageLayout>
  );
}
