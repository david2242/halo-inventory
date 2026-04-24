"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import type { AuthUser, UserListResponse, UserRole } from "@/lib/types";

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", full_name: "", role: "delegate" as UserRole, password: "" });
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  if (currentUser?.role !== "director") {
    return <p className="text-gray-500 text-sm">Nincs hozzáférése ehhez az oldalhoz.</p>;
  }

  function load() {
    api.get<UserListResponse>("/users")
      .then((r) => setUsers(r.data.items))
      .finally(() => setLoading(false));
  }

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => { load(); }, []);

  function set(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setCreating(true);
    try {
      await api.post("/users", form);
      setForm({ email: "", full_name: "", role: "delegate", password: "" });
      setShowForm(false);
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Hiba történt.");
    } finally {
      setCreating(false);
    }
  }

  async function handleDeactivate(u: AuthUser) {
    if (!confirm(`Deaktiválja: ${u.full_name}?`)) return;
    await api.delete(`/users/${u.id}`);
    load();
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Felhasználók</h2>
        <button onClick={() => setShowForm((s) => !s)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
          {showForm ? "Mégsem" : "+ Új felhasználó"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white rounded-xl shadow-sm p-5 mb-5 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Teljes név *</label>
              <input required value={form.full_name} onChange={(e) => set("full_name", e.target.value)} className="input" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">E-mail *</label>
              <input required type="email" value={form.email} onChange={(e) => set("email", e.target.value)} className="input" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Szerepkör</label>
              <select value={form.role} onChange={(e) => set("role", e.target.value)} className="input">
                <option value="delegate">Megbízott</option>
                <option value="director">Intézményvezető</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Jelszó *</label>
              <input required type="password" value={form.password} onChange={(e) => set("password", e.target.value)}
                minLength={8} className="input" />
            </div>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={creating}
            className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-60">
            Létrehozás
          </button>
        </form>
      )}

      {loading ? (
        <p className="text-gray-500 text-sm">Betöltés...</p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Név</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">E-mail</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Szerepkör</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Státusz</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{u.full_name}</td>
                  <td className="px-4 py-3 text-gray-600">{u.email}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {u.role === "director" ? "Intézményvezető" : "Megbízott"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                      u.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-400"
                    }`}>
                      {u.is_active ? "Aktív" : "Inaktív"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {u.is_active && u.id !== currentUser?.id && (
                      <button onClick={() => handleDeactivate(u)}
                        className="text-xs text-red-500 hover:text-red-700">
                        Deaktivál
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
