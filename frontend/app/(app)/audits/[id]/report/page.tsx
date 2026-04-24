"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { AuditReport, Equipment } from "@/lib/types";

export default function AuditReportPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [report, setReport] = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AuditReport>(`/audits/${id}/report`)
      .then((r) => setReport(r.data))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-gray-500 text-sm">Betöltés...</p>;
  if (!report) return <p className="text-red-500 text-sm">Riport nem található.</p>;

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold">Audit riport</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Auditor: {report.auditor_name} · {new Date(report.session.started_at).toLocaleDateString("hu-HU")}
          </p>
        </div>
        <button onClick={() => router.push("/audits")}
          className="text-sm text-blue-600 hover:underline">← Vissza</button>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6">
        {[
          { label: "Összesen", value: report.summary.total, color: "bg-gray-100 text-gray-700" },
          { label: "Megvan", value: report.summary.present, color: "bg-green-100 text-green-700" },
          { label: "Hiányzik", value: report.summary.missing, color: "bg-red-100 text-red-700" },
          { label: "Nem ellenőrzött", value: report.summary.unchecked, color: "bg-yellow-100 text-yellow-700" },
        ].map((s) => (
          <div key={s.label} className={`rounded-xl p-4 text-center ${s.color}`}>
            <div className="text-2xl font-bold">{s.value}</div>
            <div className="text-xs mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {report.missing_items.length > 0 && (
        <Section title="Hiányzó eszközök" items={report.missing_items} colorClass="bg-red-50 border-red-200" />
      )}
      {report.unchecked_items.length > 0 && (
        <Section title="Nem ellenőrzött" items={report.unchecked_items} colorClass="bg-yellow-50 border-yellow-200" />
      )}
      {report.present_items.length > 0 && (
        <Section title="Megtalált eszközök" items={report.present_items} colorClass="bg-green-50 border-green-200" />
      )}
    </div>
  );
}

function Section({ title, items, colorClass }: { title: string; items: Equipment[]; colorClass: string }) {
  return (
    <div className={`rounded-xl border p-4 mb-4 ${colorClass}`}>
      <h3 className="font-medium mb-3">{title} ({items.length})</h3>
      <ul className="space-y-1">
        {items.map((eq) => (
          <li key={eq.id} className="text-sm flex justify-between">
            <span>{eq.name}</span>
            <span className="text-gray-500">{eq.serial_number ?? "—"}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
