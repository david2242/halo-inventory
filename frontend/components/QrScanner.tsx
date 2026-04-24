"use client";

import { useEffect, useRef } from "react";
import { Html5Qrcode } from "html5-qrcode";

interface Props {
  onScan: (result: string) => void;
}

export default function QrScanner({ onScan }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const scannerRef = useRef<Html5Qrcode | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const id = "qr-reader-" + Math.random().toString(36).slice(2);
    containerRef.current.id = id;
    const scanner = new Html5Qrcode(id);
    scannerRef.current = scanner;

    scanner.start(
      { facingMode: "environment" },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      (text) => { onScan(text); },
      undefined
    ).catch(() => {});

    return () => {
      scanner.stop().catch(() => {}).finally(() => scanner.clear());
    };
  }, [onScan]);

  return <div ref={containerRef} className="w-full max-w-sm mx-auto" />;
}
