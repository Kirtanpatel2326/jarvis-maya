'use client';

import React from 'react';

export type SuitMode = 'CLASSIC' | 'HULKBUSTER' | 'STEALTH' | 'TACTICAL';

interface HudOverlayProps {
  status: string;
  activeEngine: string;
  cpuLoad: number;
  ramUsage: number;
  currentMode?: SuitMode;
  onSelectMode?: (mode: SuitMode) => void;
  onOpenQr?: () => void;
  isStudyMode?: boolean;
  onToggleStudyMode?: () => void;
  onOpenVisionSolver?: () => void;
  isSilent?: boolean;
}

export const HudOverlay: React.FC<HudOverlayProps> = ({
  status,
  activeEngine,
  cpuLoad,
  ramUsage,
  currentMode = 'CLASSIC',
  onSelectMode,
  onOpenQr,
  isStudyMode = false,
  onToggleStudyMode,
  onOpenVisionSolver,
  isSilent = false,
}) => {
  const getModeColor = (mode: SuitMode) => {
    switch (mode) {
      case 'HULKBUSTER':
        return 'text-red-500 border-red-500/60 shadow-[0_0_20px_rgba(255,34,0,0.4)]';
      case 'STEALTH':
        return 'text-emerald-400 border-emerald-400/60 shadow-[0_0_20px_rgba(0,255,102,0.4)]';
      case 'TACTICAL':
        return 'text-blue-400 border-blue-400/60 shadow-[0_0_20px_rgba(0,102,255,0.4)]';
      default:
        return 'text-[#00f0ff] border-[#00f0ff]/60 shadow-[0_0_20px_rgba(0,240,255,0.4)]';
    }
  };

  return (
    <div className="fixed inset-0 pointer-events-none z-10 flex flex-col justify-between p-4 sm:p-6 select-none font-mono">
      {/* Top Navigation Diagnostics */}
      <div className="flex justify-between items-start flex-wrap gap-3">
        <div className="stark-glass pointer-events-auto rounded-xl p-3.5 text-xs text-[#00f0ff]">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-[#00f0ff] animate-ping" />
            <span className="font-bold tracking-widest stark-glow text-sm">
              J.A.R.V.I.S. [{currentMode}]
            </span>
          </div>
          <p className="text-slate-400 text-[11px]">ACTIVE ENGINE: <span className="text-white">{activeEngine}</span></p>
        </div>

        {/* 4 Suit Mode Selector Tabs */}
        {onSelectMode && (
          <div className="stark-glass pointer-events-auto rounded-xl p-1.5 flex gap-1.5 flex-wrap">
            {(['CLASSIC', 'HULKBUSTER', 'STEALTH', 'TACTICAL'] as SuitMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => onSelectMode(mode)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  currentMode === mode
                    ? `${getModeColor(mode)} bg-white/10 border`
                    : 'text-slate-400 hover:text-white border border-transparent'
                }`}
              >
                {mode === 'HULKBUSTER' ? '🛡️ HULKBUSTER' : mode === 'STEALTH' ? '🤫 STEALTH' : mode === 'TACTICAL' ? '📊 TACTICAL' : '⚛️ MARK-85'}
              </button>
            ))}
          </div>
        )}

        {/* Action Toolbar */}
        <div className="flex gap-2 pointer-events-auto flex-wrap justify-end">
          {onOpenVisionSolver && (
            <button
              onClick={onOpenVisionSolver}
              className="stark-glass rounded-xl px-3.5 py-2 text-xs text-[#00f0ff] hover:bg-[#00f0ff]/20 font-bold transition-all border border-[#00f0ff]/40 shadow-[0_0_15px_rgba(0,240,255,0.2)] flex items-center gap-1.5"
            >
              👁️ SOLVER
            </button>
          )}

          {onToggleStudyMode && (
            <button
              onClick={onToggleStudyMode}
              className={`stark-glass rounded-xl px-3.5 py-2 text-xs font-bold transition-all ${
                isStudyMode
                  ? 'bg-[#00f0ff]/25 border-[#00f0ff] text-white shadow-[0_0_15px_#00f0ff]'
                  : 'text-[#00f0ff] hover:bg-[#00f0ff]/10'
              }`}
            >
              📚 {isStudyMode ? 'STUDY MODE: ON' : 'STUDY MODE'}
            </button>
          )}

          {onOpenQr && (
            <button
              onClick={onOpenQr}
              className="stark-glass rounded-xl px-3.5 py-2 text-xs text-[#00f0ff] hover:bg-[#00f0ff]/10 font-bold transition-all flex items-center gap-1.5"
            >
              📱 QR
            </button>
          )}

          {/* System State Indicator */}
          <div className="stark-glass rounded-xl px-3.5 py-2 text-xs text-white">
            STATE: <span className="text-[#00f0ff] font-bold tracking-wider uppercase">{status}</span>
          </div>
        </div>
      </div>

      {/* Bottom Hardware Telemetry */}
      <div className="flex justify-between items-end">
        <div className="stark-glass pointer-events-auto rounded-xl p-3 text-[10px] text-slate-400 flex gap-4">
          <div>CPU: <span className="text-[#00f0ff]">{cpuLoad}%</span></div>
          <div>RAM: <span className="text-[#00f0ff]">{ramUsage}%</span></div>
          <div>FPS: <span className="text-white">60</span></div>
          <div>MODE: <span className="text-white font-bold">{currentMode}</span></div>
          {isSilent && <div className="text-amber-300">🤫 STEALTH</div>}
        </div>

        <div className="text-[10px] text-slate-500 tracking-widest uppercase hidden sm:block">
          STARK_CORE_GESTURE_INTERFACE // ONLINE
        </div>
      </div>
    </div>
  );
};

export default HudOverlay;
