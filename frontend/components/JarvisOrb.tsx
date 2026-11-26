"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createOrbScene, type OrbSceneApi } from "@/lib/orbScene";
import { HandTracker, type TrackerStatus } from "@/lib/handTracker";
import HudOverlay, { SuitMode } from "./HudOverlay";
import { VisionSolverModal } from "./VisionSolverModal";
import { QrModal } from "./QrModal";

type CameraState = "off" | "starting" | "on" | "error";

const MODE_LABEL: Record<TrackerStatus["mode"], string> = {
  idle: "STANDBY",
  spin: "SPIN",
  zoom: "ZOOM",
};

export default function JarvisOrb() {
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<OrbSceneApi | null>(null);
  const trackerRef = useRef<HandTracker | null>(null);

  const [camera, setCamera] = useState<CameraState>("off");
  const [status, setStatus] = useState<TrackerStatus>({ hands: 0, mode: "idle" });
  const [error, setError] = useState<string | null>(null);

  const [suitMode, setSuitMode] = useState<SuitMode>("CLASSIC");
  const [showVisionModal, setShowVisionModal] = useState(false);
  const [showQrModal, setShowQrModal] = useState(false);
  const [isStudyMode, setIsStudyMode] = useState(false);
  const [isSilent, setIsSilent] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const scene = createOrbScene(container);
    sceneRef.current = scene;
    return () => {
      trackerRef.current?.stop();
      trackerRef.current = null;
      scene.dispose();
      sceneRef.current = null;
    };
  }, []);

  const stopGestures = useCallback(() => {
    trackerRef.current?.stop();
    trackerRef.current = null;
    setCamera("off");
    setStatus({ hands: 0, mode: "idle" });
  }, []);

  const startGestures = useCallback(async () => {
    const video = videoRef.current;
    const overlay = overlayRef.current;
    if (!video || !overlay || trackerRef.current) return;

    setCamera("starting");
    setError(null);

    const tracker = new HandTracker(video, overlay, {
      onRotate: (dt, dp) => sceneRef.current?.rotateBy(dt, dp),
      onZoom: (factor) => sceneRef.current?.zoomBy(factor),
      onStatus: setStatus,
    });
    trackerRef.current = tracker;

    try {
      await tracker.start();
      setCamera("on");
    } catch (err) {
      trackerRef.current = null;
      tracker.stop();
      setCamera("error");
      setError(
        err instanceof DOMException && err.name === "NotAllowedError"
          ? "CAMERA ACCESS DENIED"
          : "TRACKING INIT FAILED",
      );
    }
  }, []);

  const toggleGestures = useCallback(() => {
    if (trackerRef.current) stopGestures();
    else void startGestures();
  }, [startGestures, stopGestures]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      switch (e.key) {
        case "+":
        case "=":
          sceneRef.current?.zoomIn();
          break;
        case "-":
        case "_":
          sceneRef.current?.zoomOut();
          break;
        case "r":
        case "R":
          sceneRef.current?.resetView();
          break;
        case "g":
        case "G":
          toggleGestures();
          break;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [toggleGestures]);

  const cameraOn = camera === "on";

  // Chat & Voice integration state
  const [inputText, setInputText] = useState("");
  const [responseLog, setResponseLog] = useState<string | null>("SYSTEM READY. STANDING BY FOR COMMANDS, BOSS.");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);

  // 4D Hologram Fabrication State
  const [hologramData, setHologramData] = useState<{ active: boolean; prompt: string; shape_type: string; stats: any } | null>(null);
  const [hardwareData, setHardwareData] = useState<{ status: string; active_ports: string[]; count: number } | null>(null);
  const [visionData, setVisionData] = useState<{ active: boolean; target: string; status: string } | null>(null);

  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef(false);

  const getApiHost = () => (typeof window !== "undefined" ? window.location.hostname || "localhost" : "localhost");

  const checkHologramState = useCallback(async () => {
    try {
      const res = await fetch(`http://${getApiHost()}:8000/hologram`);
      if (res.ok) {
        const data = await res.json();
        setHologramData(data);
      }
    } catch {}
  }, []);

  const checkHardwareState = useCallback(async () => {
    try {
      const res = await fetch(`http://${getApiHost()}:8000/hardware`);
      if (res.ok) setHardwareData(await res.json());
      const vRes = await fetch(`http://${getApiHost()}:8000/vision`);
      if (vRes.ok) setVisionData(await vRes.json());
    } catch {}
  }, []);

  useEffect(() => {
    checkHologramState();
    checkHardwareState();
    const interval = setInterval(() => {
      checkHologramState();
      checkHardwareState();
    }, 4000);
    return () => clearInterval(interval);
  }, [checkHologramState, checkHardwareState]);

  useEffect(() => {
    isListeningRef.current = isListening;
  }, [isListening]);

  useEffect(() => {
    if (typeof document !== "undefined") {
      if (hologramData?.active && hologramData?.shape_type) {
        document.body.classList.add("hologram-stage");
        sceneRef.current?.setHologramType(hologramData.shape_type as any, true);
      } else {
        document.body.classList.remove("hologram-stage");
        sceneRef.current?.setHologramType("orb", false);
      }
    }
  }, [hologramData?.active, hologramData?.shape_type]);

  const speakResponse = useCallback(async (text: string) => {
    if (isSilent) return;
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch {}
    }

    let playedElevenLabs = false;
    try {
      const res = await fetch(`http://${getApiHost()}:8000/proxy_tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      if (res.ok) {
        const contentType = res.headers.get("content-type") || "";
        if (contentType.includes("audio")) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          audio.onended = () => {
            if (isListeningRef.current) {
              setTimeout(() => {
                if (isListeningRef.current && recognitionRef.current) {
                  try { recognitionRef.current.start(); } catch {}
                }
              }, 600);
            }
          };
          await audio.play();
          playedElevenLabs = true;
        }
      }
    } catch {
      playedElevenLabs = false;
    }

    if (!playedElevenLabs && typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.resume();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      utterance.pitch = 0.95;

      const voices = window.speechSynthesis.getVoices();
      const engVoice = voices.find(v => v.lang.includes("en-GB") || v.name.includes("Daniel") || v.lang.includes("en"));
      if (engVoice) utterance.voice = engVoice;

      utterance.onend = () => {
        if (isListeningRef.current) {
          setTimeout(() => {
            if (isListeningRef.current && recognitionRef.current) {
              try { recognitionRef.current.start(); } catch {}
            }
          }, 600);
        }
      };
      window.speechSynthesis.speak(utterance);
    }
  }, [isSilent]);

  const sendQuery = async (queryText: string) => {
    if (!queryText.trim() || isProcessing) return;
    setIsProcessing(true);
    setInputText("");

    const finalPrompt = isStudyMode
      ? `[STUDY Q&A FLASHCARD MODE] Provide a structured breakdown for: ${queryText}`
      : queryText;

    try {
      const res = await fetch(`http://${getApiHost()}:8000/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: finalPrompt })
      });
      const data = await res.json();
      const replyText = data.content || data.speech || data.result || "Command executed, Boss.";
      setResponseLog(replyText);
      speakResponse(replyText);
      checkHologramState();
    } catch {
      const fallbackMsg = "Local JARVIS core online. Request processed.";
      setResponseLog(fallbackMsg);
      speakResponse(fallbackMsg);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSelectMode = (mode: SuitMode) => {
    setSuitMode(mode);
    let announcement = "Mark 85 Classic HUD online.";
    if (mode === "HULKBUSTER") announcement = "Hulkbuster heavy defense override engaged, Boss!";
    else if (mode === "STEALTH") announcement = "Stealth vision OCR solver mode active.";
    else if (mode === "TACTICAL") announcement = "Tactical diagnostics matrix online.";
    speakResponse(announcement);
  };

  const toggleMic = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognitionClass = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      alert("Speech Recognition not supported in this browser. Please use Chrome or Safari.");
      return;
    }

    if (isListening) {
      isListeningRef.current = false;
      setIsListening(false);
      recognitionRef.current?.stop();
    } else {
      const rec = new SpeechRecognitionClass();
      rec.continuous = true;
      rec.interimResults = false;
      rec.lang = "en-US";

      rec.onstart = () => {
        setIsListening(true);
        isListeningRef.current = true;
      };

      rec.onresult = (e: any) => {
        const transcript = e.results[e.results.length - 1][0].transcript;
        if (transcript.trim()) {
          setInputText(transcript);
          sendQuery(transcript);
        }
      };

      rec.onerror = () => setIsListening(false);
      rec.onend = () => {
        if (isListeningRef.current) {
          try { rec.start(); } catch {}
        } else {
          setIsListening(false);
        }
      };

      recognitionRef.current = rec;
      rec.start();
    }
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-[#030712] font-mono select-none">
      {/* 3D Arc Reactor Orb & 4D Blueprint Stage Canvas */}
      <div ref={containerRef} className="absolute inset-0 z-0 w-full h-full" />

      {/* Hidden Gesture Video & Overlay Canvas */}
      <video ref={videoRef} className="hidden" playsInline muted />
      <canvas ref={overlayRef} className="absolute top-4 right-4 z-20 w-36 h-28 rounded-xl border border-[#00f0ff]/30 pointer-events-none hidden" />

      {/* Sleek Stark Telemetry HUD Overlay */}
      <HudOverlay
        status={isProcessing ? "THINKING..." : "ONLINE"}
        activeEngine="Groq Llama 3.3 70B / Gemini 2.0"
        cpuLoad={18.4}
        ramUsage={64.2}
        currentMode={suitMode}
        onSelectMode={handleSelectMode}
        onOpenQr={() => setShowQrModal(true)}
        isStudyMode={isStudyMode}
        onToggleStudyMode={() => setIsStudyMode(!isStudyMode)}
        onOpenVisionSolver={() => setShowVisionModal(true)}
        isSilent={isSilent}
      />

      {/* Top Left: Physical Hardware Device Status Badge */}
      {hardwareData && (
        <div className="absolute top-20 left-6 z-20 stark-glass rounded-xl p-3 max-w-xs border border-[#00f0ff]/30 pointer-events-auto">
          <div className="flex items-center gap-2 text-xs font-bold text-[#00f0ff] mb-1">
            <span className="w-2 h-2 rounded-full bg-[#00f0ff] animate-ping" />
            <span>⚡ PHYSICAL HARDWARE LINK</span>
          </div>
          <p className="text-[11px] text-slate-300">
            PORTS: <span className="text-white font-bold">{hardwareData.count} ACTIVE</span>
          </p>
          <p className="text-[10px] text-slate-400 truncate">
            {hardwareData.active_ports.join(", ") || "Searching Serial/USB ports..."}
          </p>
        </div>
      )}

      {/* Top Right: 4D Hologram Fabrication Stats Badge */}
      {hologramData?.active && (
        <div className="absolute top-20 right-6 z-20 stark-glass rounded-xl p-3 max-w-xs border border-[#00f0ff]/40 shadow-[0_0_25px_rgba(0,240,255,0.25)] pointer-events-auto animate-fadeIn">
          <div className="flex items-center justify-between text-xs font-bold text-[#00f0ff] mb-1">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#00f0ff] animate-ping" />
              <span>🎨 4D FABRICATION ACTIVE</span>
            </span>
            <button
              onClick={async () => {
                await fetch(`http://${getApiHost()}:8000/hologram/clear`, { method: "POST" });
                checkHologramState();
              }}
              className="text-slate-400 hover:text-white text-[10px]"
            >
              ✕ DISMISS
            </button>
          </div>
          <p className="text-[11px] text-white font-bold truncate">"{hologramData.prompt}"</p>
          <p className="text-[10px] text-slate-400">TYPE: <span className="text-[#00f0ff] uppercase">{hologramData.shape_type}</span></p>
        </div>
      )}

      {/* Terminal Response Log Display */}
      {responseLog && (
        <div className="absolute bottom-24 sm:bottom-28 left-4 right-4 sm:left-1/2 sm:-translate-x-1/2 sm:max-w-2xl z-20 pointer-events-auto">
          <div className="stark-glass p-4 rounded-xl border border-[#00f0ff]/30 text-xs text-slate-200 shadow-[0_0_20px_rgba(0,240,255,0.15)] leading-relaxed max-h-48 overflow-y-auto">
            <div className="flex items-center justify-between mb-1 text-[10px] text-slate-400 border-b border-[#00f0ff]/20 pb-1 font-bold">
              <span>⚡ J.A.R.V.I.S. INTELLIGENCE OUTPUT</span>
              <span>{isProcessing ? "PROCESSING..." : "LIVE"}</span>
            </div>
            <div className="whitespace-pre-wrap">{responseLog}</div>
          </div>
        </div>
      )}

      {/* Command Input Bar */}
      <div className="absolute bottom-6 left-4 right-4 sm:left-1/2 sm:-translate-x-1/2 sm:max-w-2xl z-20 pointer-events-auto">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendQuery(inputText);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask J.A.R.V.I.S. to search, model 3D objects, answer questions..."
            className="flex-1 stark-glass rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[#00f0ff] border border-[#00f0ff]/30 shadow-[0_0_15px_rgba(0,240,255,0.15)]"
          />

          <button
            type="button"
            onClick={toggleMic}
            className={`stark-glass rounded-xl px-4 py-3 text-xs font-bold transition-all border ${
              isListening
                ? "bg-red-500/30 border-red-500 text-red-300 animate-pulse shadow-[0_0_20px_#ff0000]"
                : "border-[#00f0ff]/40 text-[#00f0ff] hover:bg-[#00f0ff]/20"
            }`}
          >
            {isListening ? "🎙️ LISTENING…" : "🎤 SPEAK"}
          </button>

          <button
            type="button"
            onClick={toggleGestures}
            className={`stark-glass rounded-xl px-3 py-3 text-xs font-bold transition-all border ${
              cameraOn
                ? "bg-[#00f0ff]/30 border-[#00f0ff] text-white shadow-[0_0_15px_#00f0ff]"
                : "border-[#00f0ff]/40 text-[#00f0ff] hover:bg-[#00f0ff]/10"
            }`}
            title="Toggle Webcam Hand Gestures (G key)"
          >
            ✋ GESTURE
          </button>

          <button
            type="submit"
            disabled={isProcessing}
            className="stark-glass bg-[#00f0ff]/20 hover:bg-[#00f0ff]/35 border border-[#00f0ff] text-[#00f0ff] font-bold px-5 py-3 rounded-xl text-xs transition-all shadow-[0_0_20px_rgba(0,240,255,0.3)]"
          >
            EXECUTE
          </button>
        </form>
      </div>

      {/* Vision Solver Modal */}
      <VisionSolverModal
        isOpen={showVisionModal}
        onClose={() => setShowVisionModal(false)}
        isSilent={isSilent}
        onToggleSilent={() => setIsSilent(!isSilent)}
      />

      {/* QR Code Modal */}
      <QrModal isOpen={showQrModal} onClose={() => setShowQrModal(false)} />
    </div>
  );
}
