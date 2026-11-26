'use client';

import React, { useEffect, useState } from 'react';

interface QrModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const QrModal: React.FC<QrModalProps> = ({ isOpen, onClose }) => {
  const [networkInfo, setNetworkInfo] = useState<{ ip: string; mobile_url: string; qr_code: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      const host = typeof window !== 'undefined' ? (window.location.hostname || 'localhost') : 'localhost';
      fetch(`http://${host}:8000/api/network_info`)
        .then((res) => res.json())
        .then((data) => {
          setNetworkInfo(data);
          setLoading(false);
        })
        .catch(() => {
          const fallbackHost = typeof window !== 'undefined' ? (window.location.hostname || '172.20.10.2') : '172.20.10.2';
          setNetworkInfo({
            ip: fallbackHost,
            mobile_url: `http://${fallbackHost}:3005`,
            qr_code: `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=http://${fallbackHost}:3005&color=00f0ff&bgcolor=030712`
          });
          setLoading(false);
        });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 select-none font-mono">
      <div className="stark-glass pointer-events-auto rounded-2xl p-6 max-w-sm w-full border border-[#00f0ff]/40 shadow-[0_0_30px_rgba(0,240,255,0.2)] text-center relative animate-fadeIn">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-[#00f0ff] font-bold text-sm transition-colors"
        >
          ✕
        </button>

        <div className="flex items-center justify-center gap-2 mb-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#00f0ff] animate-ping" />
          <h2 className="text-sm font-bold tracking-widest text-[#00f0ff]">MOBILE HUD SCANNER</h2>
        </div>

        <p className="text-[11px] text-slate-400 mb-4">
          Scan with your Phone Camera to open J.A.R.V.I.S. instantly on Wi-Fi!
        </p>

        {/* QR Code Container */}
        <div className="bg-[#030712] p-4 rounded-xl border border-[#00f0ff]/30 inline-block my-2 shadow-[0_0_15px_rgba(0,240,255,0.15)]">
          {loading ? (
            <div className="w-48 h-48 flex items-center justify-center text-xs text-[#00f0ff] animate-pulse">
              GENERATING QR CODE...
            </div>
          ) : (
            <img
              src={networkInfo?.qr_code}
              alt="J.A.R.V.I.S. Mobile QR Code"
              className="w-48 h-48 rounded-lg object-contain mx-auto border border-[#00f0ff]/20"
            />
          )}
        </div>

        {/* Direct Link */}
        <div className="mt-3 bg-[#030712]/80 p-2.5 rounded-lg border border-[#00f0ff]/20 text-[11px]">
          <span className="text-slate-400">WI-FI LINK: </span>
          <a
            href={networkInfo?.mobile_url}
            target="_blank"
            rel="noreferrer"
            className="text-[#00f0ff] font-bold hover:underline break-all"
          >
            {networkInfo?.mobile_url}
          </a>
        </div>

        <button
          onClick={onClose}
          className="mt-5 w-full bg-[#00f0ff]/10 hover:bg-[#00f0ff]/25 border border-[#00f0ff] text-[#00f0ff] font-bold py-2.5 rounded-xl text-xs transition-all shadow-[0_0_15px_rgba(0,240,255,0.2)]"
        >
          CLOSE SCANNER
        </button>
      </div>
    </div>
  );
};

export default QrModal;
