import React from "react";

interface QRCodeProps {
  value: string;
  size?: number;
  className?: string;
}

export function QRCode({ value, size = 180, className = "" }: QRCodeProps) {
  // Using QuickChart QR service for crisp vector-like QR code
  const encoded = encodeURIComponent(value);
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encoded}&margin=8&color=1e1b4b`;

  return (
    <div
      className={`inline-flex items-center justify-center p-3 bg-white rounded-2xl border-2 border-indigo-100 shadow-sm ${className}`}
    >
      <img
        src={qrUrl}
        alt={`Mã QR Check-in: ${value}`}
        width={size}
        height={size}
        className="rounded-lg object-contain"
        loading="lazy"
      />
    </div>
  );
}
