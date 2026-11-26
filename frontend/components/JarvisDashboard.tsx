'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

// --- Zero-Dependency Web Audio Synthesizer ---
class SoundController {
  private ctx: AudioContext | null = null;

  private init() {
    if (!this.ctx && typeof window !== 'undefined') {
      this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
  }

  playUiBeep(freq = 880, duration = 0.08) {
    this.init();
    if (!this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(0.1, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch {}
  }
}

const sound = new SoundController();

export default function JarvisDashboard() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<Array<{ role: string; text: string }>>([
    { role: 'assistant', text: 'All core systems online, Boss. How may I assist you today?' },
  ]);
  const [isThinking, setIsThinking] = useState(false);

  // --- Three.js Holographic Orb Generator ---
  useEffect(() => {
    if (!canvasRef.current) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 4.5;

    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);

    // Inner Core
    const coreGeo = new THREE.IcosahedronGeometry(1.2, 2);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      wireframe: true,
      transparent: true,
      opacity: 0.8,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    scene.add(coreMesh);

    // Outer Energy Ring
    const ringGeo = new THREE.TorusGeometry(1.8, 0.02, 16, 100);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, wireframe: true });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    scene.add(ringMesh);

    let animationFrameId: number;
    const animate = () => {
      coreMesh.rotation.x += 0.005;
      coreMesh.rotation.y += 0.01;
      ringMesh.rotation.x -= 0.008;
      ringMesh.rotation.y += 0.003;

      renderer.render(scene, camera);
      animationFrameId = requestAnimationFrame(animate);
    };
    animate();

    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, []);

  // --- Command Handler ---
  const handleSend = async () => {
    if (!prompt.trim() || isThinking) return;

    sound.playUiBeep(1200, 0.06);
    const userMsg = prompt.trim();
    setPrompt('');
    setMessages((prev) => [...prev, { role: 'user', text: userMsg }]);
    setIsThinking(true);

    try {
      // Connects to your local FastAPI backend endpoint
      const res = await fetch('http://localhost:8000/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userMsg }),
      });
      if (res.ok) {
        const data = await res.json();
        const speech = data.speech || data.content || data.result || 'Command executed, Boss.';
        setMessages((prev) => [...prev, { role: 'assistant', text: speech }]);
      } else {
        throw new Error('Server error');
      }
    } catch {
      // Offline / Local Simulation Fallback
      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', text: `[LOCAL CORE] Processed query: "${userMsg}". All local subsystems functioning normally.` },
        ]);
      }, 800);
    } finally {
      setIsThinking(false);
      sound.playUiBeep(600, 0.1);
    }
  };

  return (
    <div className="relative w-screen h-screen bg-[#030712] overflow-hidden font-mono text-white select-none">
      {/* 3D Holographic Canvas Background */}
      <canvas ref={canvasRef} className="absolute inset-0 z-0 pointer-events-none" />

      {/* Top Glassmorphic HUD Bar */}
      <header className="absolute top-0 left-0 right-0 z-10 flex justify-between items-center p-6 bg-slate-950/40 backdrop-blur-md border-b border-[#00f0ff]/20">
        <div className="flex items-center gap-3">
          <span className="w-3 h-3 rounded-full bg-[#00f0ff] animate-ping" />
          <h1 className="text-sm font-bold tracking-widest text-[#00f0ff]">J.A.R.V.I.S. CLASSIC // HUD</h1>
        </div>
        <div className="text-xs text-slate-400 flex items-center gap-4">
          <span>STATUS: <strong className={isThinking ? 'text-amber-400 animate-pulse' : 'text-emerald-400'}>{isThinking ? 'THINKING...' : 'ONLINE'}</strong></span>
        </div>
      </header>

      {/* Center HUD Workspace Overlay */}
      <main className="absolute inset-0 z-10 flex flex-col justify-between pt-24 pb-8 px-6 pointer-events-none">
        {/* Chat / Terminal Output Window */}
        <div className="pointer-events-auto max-w-md w-full max-h-[50vh] overflow-y-auto space-y-3 p-4 rounded-xl bg-slate-950/60 backdrop-blur-lg border border-[#00f0ff]/30 shadow-[0_0_20px_rgba(0,240,255,0.1)]">
          {messages.map((msg, i) => (
            <div key={i} className={`text-xs ${msg.role === 'user' ? 'text-amber-300 text-right' : 'text-[#00f0ff]'}`}>
              <span className="font-bold opacity-60">{msg.role === 'user' ? 'YOU' : 'JARVIS'}: </span>
              <span>{msg.text}</span>
            </div>
          ))}
        </div>

        {/* Bottom Command Input Bar */}
        <div className="pointer-events-auto max-w-xl w-full mx-auto flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Issue command or ask question..."
            className="flex-1 bg-slate-950/80 border border-[#00f0ff]/40 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-[#00f0ff] backdrop-blur-md shadow-[0_0_15px_rgba(0,240,255,0.1)]"
          />
          <button
            onClick={handleSend}
            disabled={isThinking}
            className="bg-[#00f0ff]/10 hover:bg-[#00f0ff]/30 border border-[#00f0ff] text-[#00f0ff] px-5 py-3 rounded-xl text-xs font-bold transition-all duration-200 shadow-[0_0_10px_rgba(0,240,255,0.2)]"
          >
            EXECUTE
          </button>
        </div>
      </main>
    </div>
  );
}
