"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Location, LocationListResponse } from "@/lib/types";

export default function LocationsPage() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");
  const [newAddress, setNewAddress] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  function load() {
    setLoading(true);
    api.get<LocationListResponse>("/locations")
      .then((r) => setLocations(r.data.items))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setCreating(true);
    try {
      await api.post("/locations", { name: newName, address: newAddress || undefined });
      setNewName("");
      setNewAddress("");
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Hiba történt.");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(loc: Location) {
    if (!confirm(`Törli: ${loc.name}?`)) return;
    try {
      await api.delete(`/locations/${loc.id}`);
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg ?? "Nem törölhető (aktív eszközök).");
    }
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-semibold mb-6">Telephelyek</h2>

      <form onSubmit={handleCreate} className="bg-white rounded-xl shadow-sm p-5 mb-6 flex gap-3">
        <input
          required
          placeholder="Telephely neve *"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          className="input flex-1"
        />
        <input
          placeholder="Cím (opcionális)"
          value={newAddress}
          onChange={(e) => setNewAddress(e.target.value)}
          className="input flex-1"
        />
        <button type="submit" disabled={creating}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-60 whitespace-nowrap">
          + Hozzáad
        </button>
      </form>
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {loading ? (
        <p className="text-gray-500 text-sm">Betöltés...</p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Telephely</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Cím</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {locations.map((loc) => (
                <tr key={loc.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{loc.name}</td>
                  <td className="px-4 py-3 text-gray-600">{loc.address ?? "—"}</td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleDelete(loc)}
                      className="text-xs text-red-500 hover:text-red-700">
                      Töröl
                    </button>
                  </td>
                </tr>
              ))}
              {locations.length === 0 && (
                <tr><td colSpan={3} className="px-4 py-6 text-center text-gray-400">Nincs telephely.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
