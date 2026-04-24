"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { EquipmentCategory, Location, LocationListResponse } from "@/lib/types";

const CATEGORIES: { value: EquipmentCategory; label: string }[] = [
  { value: "laptop", label: "Laptop" },
  { value: "desktop", label: "Asztali PC" },
  { value: "printer", label: "Nyomtató" },
  { value: "phone", label: "Telefon" },
  { value: "tablet", label: "Tablet" },
  { value: "monitor", label: "Monitor" },
  { value: "projector", label: "Projektor" },
  { value: "other", label: "Egyéb" },
];

export default function NewEquipmentPage() {
  const router = useRouter();
  const [locations, setLocations] = useState<Location[]>([]);
  const [form, setForm] = useState({
    name: "",
    category: "laptop" as EquipmentCategory,
    location_id: "",
    manufacturer: "",
    model: "",
    serial_number: "",
    room: "",
    assigned_to: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get<LocationListResponse>("/locations").then((r) => {
      setLocations(r.data.items);
      if (r.data.items.length > 0) setForm((f) => ({ ...f, location_id: r.data.items[0].id }));
    });
  }, []);

  function set(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const body = {
        ...form,
        manufacturer: form.manufacturer || undefined,
        model: form.model || undefined,
        serial_number: form.serial_number || undefined,
        room: form.room || undefined,
        assigned_to: form.assigned_to || undefined,
      };
      await api.post("/equipment", body);
      router.push("/equipment");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Hiba történt.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-lg">
      <h2 className="text-xl font-semibold mb-6">Új eszköz felvétele</h2>
      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm p-6 space-y-4">
        <Field label="Név *">
          <input required value={form.name} onChange={(e) => set("name", e.target.value)}
            className="input" />
        </Field>
        <Field label="Kategória *">
          <select value={form.category} onChange={(e) => set("category", e.target.value)}
            className="input">
            {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </Field>
        <Field label="Telephely *">
          <select required value={form.location_id} onChange={(e) => set("location_id", e.target.value)}
            className="input">
            {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </Field>
        <Field label="Gyártó">
          <input value={form.manufacturer} onChange={(e) => set("manufacturer", e.target.value)} className="input" />
        </Field>
        <Field label="Modell">
          <input value={form.model} onChange={(e) => set("model", e.target.value)} className="input" />
        </Field>
        <Field label="Sorozatszám">
          <input value={form.serial_number} onChange={(e) => set("serial_number", e.target.value)} className="input" />
        </Field>
        <Field label="Szoba/iroda">
          <input value={form.room} onChange={(e) => set("room", e.target.value)} className="input" />
        </Field>
        <Field label="Felelős személy">
          <input value={form.assigned_to} onChange={(e) => set("assigned_to", e.target.value)} className="input" />
        </Field>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={loading}
            className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-60">
            Mentés
          </button>
          <button type="button" onClick={() => router.back()}
            className="px-5 py-2 rounded-lg text-sm border hover:bg-gray-50">
            Mégsem
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1">{label}</label>
      {children}
    </div>
  );
}
