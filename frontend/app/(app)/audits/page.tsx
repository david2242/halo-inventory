"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { AuditSession, AuditListResponse, Location, LocationListResponse } from "@/lib/types";

export default function AuditsPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<AuditSession[]>([]);
  const [total, setTotal] = useState(0);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState("");
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  function loadLocations() {
    return api.get<LocationListResponse>("/locations").then((r) => setLocations(r.data.items));
  }

  function loadSessions() {
    return api.get<AuditListResponse>("/audits").then((r) => {
      setSessions(r.data.items);
      setTotal(r.data.total);
    });
  }

  useEffect(() => {
    Promise.all([loadLocations(), loadSessions()]).finally(() => setLoading(false));
  }, []);

  async function handleStart() {
    if (!selectedLocation) return;
    setStarting(true);
    try {
      const { data } = await api.post<AuditSession>("/audits", { location_id: selectedLocation });
      router.push(`/audits/${data.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg ?? "Hiba.");
    } finally {
      setStarting(false);
    }
  }

  function locName(id: string) {
    return locations.find((l) => l.id === id)?.name ?? id;
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Auditok ({total})</h2>

      <div className="bg-white rounded-xl shadow-sm p-5 mb-6 flex gap-3 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">Telephely</label>
          <select value={selectedLocation} onChange={(e) => setSelectedLocation(e.target.value)} className="input">
            <option value="">Válassz telephelyet...</option>
            {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </div>
        <button onClick={handleStart} disabled={!selectedLocation || starting}
          className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-60">
          Audit indítása
        </button>
      </div>

      {loading ? (
        <p className="text-gray-500 text-sm">Betöltés...</p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Telephely</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Indítva</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Státusz</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {sessions.map((s) => (
                <tr key={s.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{locName(s.location_id)}</td>
                  <td className="px-4 py-3 text-gray-600">{new Date(s.started_at).toLocaleString("hu-HU")}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                      s.status === "in_progress" ? "bg-yellow-100 text-yellow-700" : "bg-green-100 text-green-700"
                    }`}>
                      {s.status === "in_progress" ? "Folyamatban" : "Befejezett"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link href={`/audits/${s.id}`} className="text-sm text-blue-600 hover:underline">
                      Részletek
                    </Link>
                  </td>
                </tr>
              ))}
              {sessions.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-400">Nincs audit.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
