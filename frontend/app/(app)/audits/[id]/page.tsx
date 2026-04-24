"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import type { AuditDetail, AuditItem } from "@/lib/types";

const QrScanner = dynamic(() => import("@/components/QrScanner"), { ssr: false });

export default function AuditDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [detail, setDetail] = useState<AuditDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [lastScan, setLastScan] = useState<string | null>(null);

  const load = useCallback(() => {
    return api.get<AuditDetail>(`/audits/${id}`).then((r) => setDetail(r.data));
  }, [id]);

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, [load]);

  const handleScan = useCallback(async (qrCode: string) => {
    if (lastScan === qrCode) return;
    setLastScan(qrCode);
    try {
      await api.post(`/audits/${id}/scan`, { qr_code: qrCode });
      await load();
    } catch {
      alert("QR kód nem található ebben az auditban.");
    }
    setTimeout(() => setLastScan(null), 2000);
  }, [id, lastScan, load]);

  async function handleManual(item: AuditItem, isPresent: boolean) {
    await api.post(`/audits/${id}/manual`, {
      equipment_id: item.equipment_id,
      is_present: isPresent,
    });
    await load();
  }

  async function handleComplete() {
    if (!confirm("Lezárja az auditot?")) return;
    setCompleting(true);
    try {
      await api.post(`/audits/${id}/complete`);
      router.push(`/audits/${id}/report`);
    } finally {
      setCompleting(false);
    }
  }

  if (loading) return <p className="text-gray-500 text-sm">Betöltés...</p>;
  if (!detail) return <p className="text-red-500 text-sm">Audit nem található.</p>;

  const { session, summary, items } = detail;
  const inProgress = session.status === "in_progress";

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold">Audit részletek</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Indítva: {new Date(session.started_at).toLocaleString("hu-HU")}
          </p>
        </div>
        <div className="flex gap-2">
          {inProgress && (
            <>
              <button onClick={() => setScanning((s) => !s)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                  scanning ? "bg-blue-600 text-white border-blue-600" : "hover:bg-gray-50"
                }`}>
                {scanning ? "Scanner bezár" : "QR Scan"}
              </button>
              <button onClick={handleComplete} disabled={completing}
                className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700 disabled:opacity-60">
                Lezárás
              </button>
            </>
          )}
          {!inProgress && (
            <button onClick={() => router.push(`/audits/${id}/report`)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
              Riport
            </button>
          )}
        </div>
      </div>

      {/* Summary badges */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        {[
          { label: "Összesen", value: summary.total, color: "bg-gray-100 text-gray-700" },
          { label: "Megvan", value: summary.present, color: "bg-green-100 text-green-700" },
          { label: "Hiányzik", value: summary.missing, color: "bg-red-100 text-red-700" },
          { label: "Nem ellenőrzött", value: summary.unchecked, color: "bg-yellow-100 text-yellow-700" },
        ].map((s) => (
          <div key={s.label} className={`rounded-xl p-4 text-center ${s.color}`}>
            <div className="text-2xl font-bold">{s.value}</div>
            <div className="text-xs mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {scanning && inProgress && (
        <div className="bg-white rounded-xl shadow-sm p-4 mb-5">
          <p className="text-sm font-medium mb-3">Szkenneld be a QR-kódot:</p>
          <QrScanner onScan={handleScan} />
          {lastScan && <p className="text-xs text-gray-500 mt-2 text-center">Legutóbbi scan: {lastScan}</p>}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Eszköz</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Módszer</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Státusz</th>
              {inProgress && <th className="px-4 py-3"></th>}
            </tr>
          </thead>
          <tbody className="divide-y">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{item.equipment?.name ?? item.equipment_id}</td>
                <td className="px-4 py-3 text-gray-600">
                  {item.check_method === "scan" ? "Scan" : item.check_method === "manual" ? "Kézi" : "—"}
                </td>
                <td className="px-4 py-3">
                  {item.is_present === true && (
                    <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">Megvan</span>
                  )}
                  {item.is_present === false && (
                    <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">Hiányzik</span>
                  )}
                  {item.is_present === null || item.is_present === undefined ? (
                    <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">Nem ellenőrzött</span>
                  ) : null}
                </td>
                {inProgress && (
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleManual(item, true)}
                      className="text-xs text-green-600 hover:text-green-800 mr-2">✓ Megvan</button>
                    <button onClick={() => handleManual(item, false)}
                      className="text-xs text-red-500 hover:text-red-700">✗ Hiányzik</button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
