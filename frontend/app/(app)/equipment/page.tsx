"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Equipment, EquipmentListResponse, EquipmentCategory, EquipmentStatus, Location, LocationListResponse } from "@/lib/types";

const CATEGORY_LABELS: Record<EquipmentCategory, string> = {
  laptop: "Laptop",
  desktop: "Asztali PC",
  printer: "Nyomtató",
  phone: "Telefon",
  tablet: "Tablet",
  monitor: "Monitor",
  projector: "Projektor",
  other: "Egyéb",
};

export default function EquipmentPage() {
  const [items, setItems] = useState<Equipment[]>([]);
  const [total, setTotal] = useState(0);
  const [locations, setLocations] = useState<Location[]>([]);
  const [locationId, setLocationId] = useState("");
  const [status, setStatus] = useState<EquipmentStatus | "">("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const pageSize = 50;

  useEffect(() => {
    api.get<LocationListResponse>("/locations").then((r) => setLocations(r.data.items));
  }, []);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string | number> = { page, page_size: pageSize };
    if (locationId) params.location_id = locationId;
    if (status) params.status = status;
    api
      .get<EquipmentListResponse>("/equipment", { params })
      .then((r) => {
        setItems(r.data.items);
        setTotal(r.data.total);
      })
      .finally(() => setLoading(false));
  }, [locationId, status, page]);

  function handleFilter() {
    setPage(1);
  }

  async function handleRetire(eq: Equipment) {
    const reason = window.prompt(`Selejtezés oka: ${eq.name}`);
    if (!reason || reason.length < 5) return;
    await api.post(`/equipment/${eq.id}/retire`, { reason });
    setItems((prev) => prev.map((e) => e.id === eq.id ? { ...e, status: "retired" } : e));
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Eszközök ({total})</h2>
        <Link
          href="/equipment/new"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors"
        >
          + Új eszköz
        </Link>
      </div>

      <div className="flex gap-3 mb-4">
        <select
          value={locationId}
          onChange={(e) => { setLocationId(e.target.value); handleFilter(); }}
          className="border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="">Minden telephely</option>
          {locations.map((l) => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value as EquipmentStatus | ""); handleFilter(); }}
          className="border rounded-lg px-3 py-1.5 text-sm"
        >
          <option value="active">Aktív</option>
          <option value="retired">Selejtezett</option>
          <option value="">Összes</option>
        </select>
      </div>

      {loading ? (
        <p className="text-gray-500 text-sm">Betöltés...</p>
      ) : items.length === 0 ? (
        <p className="text-gray-500 text-sm">Nincs találat.</p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Név</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Kategória</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Telephely</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Státusz</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map((eq) => (
                <tr key={eq.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">
                    <Link href={`/equipment/${eq.id}`} className="hover:text-blue-600">
                      {eq.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{CATEGORY_LABELS[eq.category]}</td>
                  <td className="px-4 py-3 text-gray-600">{locations.find(l => l.id === eq.location_id)?.name ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                      eq.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                    }`}>
                      {eq.status === "active" ? "Aktív" : "Selejtezett"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {eq.status === "active" && (
                      <button
                        onClick={() => handleRetire(eq)}
                        className="text-xs text-red-500 hover:text-red-700"
                      >
                        Selejtez
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {total > pageSize && (
        <div className="flex gap-2 mt-4 justify-center text-sm">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 border rounded disabled:opacity-40">←</button>
          <span className="px-3 py-1">Oldal {page} / {Math.ceil(total / pageSize)}</span>
          <button disabled={page >= Math.ceil(total / pageSize)} onClick={() => setPage(p => p + 1)} className="px-3 py-1 border rounded disabled:opacity-40">→</button>
        </div>
      )}
    </div>
  );
}
