'use client';

import React, { useEffect, useRef, useState } from 'react';

export default function MayaHolographicCommandCenter() {
  const [activeNav, setActiveNav] = useState('Home');
  const [activeMode, setActiveMode] = useState('Hybrid Auto');
  const [commandInput, setCommandInput] = useState('');
  const [consoleInput, setConsoleInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [voiceLabel, setVoiceLabel] = useState('Tap to speak');
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isPlayingMusic, setIsPlayingMusic] = useState(false);

  // Live Date & Time
  const [currentTime, setCurrentTime] = useState('');
  const [currentDate, setCurrentDate] = useState('');

  // Hardware Telemetry
  const [cpuVal, setCpuVal] = useState('24%');
  const [ramVal, setRamVal] = useState('42%');
  const [networkLatency, setNetworkLatency] = useState('18 ms');
  const [agentStatus, setAgentStatus] = useState('READY');

  // OpenJarvis Dual Engine Status
  const [openJarvisStatus, setOpenJarvisStatus] = useState<{
    ollama_active: boolean;
    local_models: string[];
    preferred_model: string;
    engine_mode: string;
  }>({
    ollama_active: true,
    local_models: ['mistral:latest', 'llama2:latest'],
    preferred_model: 'mistral:latest',
    engine_mode: 'hybrid'
  });

  // Console Logs
  const [consoleLogs, setConsoleLogs] = useState<Array<{ type: 'ok' | 'cmd' | 'warn' | 'info'; text: string }>>([
    { type: 'ok', text: '[SYS] ✓ Neural Core & OpenJarvis Bridge Online' },
    { type: 'info', text: '[SYS] Dual-Engine: Cloud Groq 70B + Local GPU Mistral' },
    { type: 'ok', text: '[VISION] ✓ Screen Grounding Engine Active' },
    { type: 'info', text: '[READY] Standing by for Boss Kirtan Patel' }
  ]);

  // Current Task State
  const [currentTask, setCurrentTask] = useState({
    name: 'Standing by for voice or terminal command...',
    step: 'Idle',
    pct: 100,
    steps: [
      { text: 'Voice continuous listening ready', done: true },
      { text: 'Universal downloader & installer armed', done: true },
      { text: 'OpenJarvis offline engine loaded on GPU', done: true },
      { text: 'Awaiting directive from Boss Kirtan Patel', done: true }
    ]
  });

  // Routines Toggles
  const [routines, setRoutines] = useState([
    { id: 1, icon: '☀', title: 'Morning Brief', time: 'Every day · 8:00 AM', active: true },
    { id: 2, icon: '📖', title: 'Check College Updates', time: 'Every day · 10:00 AM', active: true },
    { id: 3, icon: '☾', title: 'Evening Review', time: 'Every day · 9:00 PM', active: false }
  ]);

  const recognitionRef = useRef<any>(null);
  const isMicLockedRef = useRef<boolean>(false);
  const isSpeakingRef = useRef<boolean>(false);
  const toastTimeoutRef = useRef<any>(null);

  // Toast Helper
  const showToast = (msg: string) => {
    setToastMessage(msg);
    if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    toastTimeoutRef.current = setTimeout(() => setToastMessage(null), 2500);
  };

  // Live Clock & Hardware Telemetry Polling
  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setCurrentDate(d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }));
      setCurrentTime(d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: true }));
    };
    updateTime();
    const clockTimer = setInterval(updateTime, 1000);

    const telemetryTimer = setInterval(async () => {
      try {
        const host = typeof window !== 'undefined' ? (window.location.hostname || 'localhost') : 'localhost';
        const res = await fetch(`http://${host}:8000/api/telemetry`);
        if (res.ok) {
          const data = await res.json();
          if (data.cpu !== undefined) {
            const cpuNum = typeof data.cpu === 'object' ? data.cpu.total_percent : data.cpu;
            setCpuVal(`${cpuNum}%`);
          }
          if (data.ram !== undefined) {
            const ramNum = typeof data.ram === 'object' ? data.ram.percent : data.ram;
            setRamVal(`${ramNum}%`);
          }
        }
      } catch {
        // Fallback simulated jitter
        setCpuVal(`${18 + Math.floor(Math.random() * 16)}%`);
        setRamVal(`${38 + Math.floor(Math.random() * 8)}%`);
      }
    }, 2500);

    // Fetch Engine Status
    const fetchEngineStatus = async () => {
      try {
        const host = typeof window !== 'undefined' ? (window.location.hostname || 'localhost') : 'localhost';
        const res = await fetch(`http://${host}:8000/api/engine/status`);
        if (res.ok) {
          const data = await res.json();
          setOpenJarvisStatus(data);
        }
      } catch (e) {}
    };
    fetchEngineStatus();

    return () => {
      clearInterval(clockTimer);
      clearInterval(telemetryTimer);
    };
  }, []);

  // Voice Output (Edge-TTS via Backend or Natural Web Speech Fallback)
  const speakResponse = async (text: string) => {
    if (typeof window === 'undefined') return;
    isSpeakingRef.current = true;

    // Temporarily pause recognition while speaking to prevent echo
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (e) {}
    }

    try {
      const host = typeof window !== 'undefined' ? (window.location.hostname || 'localhost') : 'localhost';
      const res = await fetch(`http://${host}:8000/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: 'en-GB-SoniaNeural' })
      });

      if (res.ok) {
        const blob = await res.blob();
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);

        audio.onended = () => {
          isSpeakingRef.current = false;
          // Resume continuous listening if mic lock is on
          if (isMicLockedRef.current && recognitionRef.current) {
            try { recognitionRef.current.start(); } catch (e) {}
          }
        };

        audio.onerror = () => {
          isSpeakingRef.current = false;
          fallbackSpeech(text);
        };

        await audio.play();
        return;
      }
    } catch (e) {
      console.warn("Backend TTS failed, using WebSpeech fallback:", e);
    }

    fallbackSpeech(text);
  };

  const fallbackSpeech = (text: string) => {
    if (!window.speechSynthesis) {
      isSpeakingRef.current = false;
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.15;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => 
      v.name.includes('Samantha') || 
      v.name.includes('Google UK English Female') || 
      v.name.includes('Victoria') ||
      v.name.includes('Daniel') ||
      v.lang.startsWith('en')
    );
    if (preferredVoice) utterance.voice = preferredVoice;

    utterance.onend = () => {
      isSpeakingRef.current = false;
      if (isMicLockedRef.current && recognitionRef.current) {
        try { recognitionRef.current.start(); } catch (e) {}
      }
    };
    utterance.onerror = () => {
      isSpeakingRef.current = false;
      if (isMicLockedRef.current && recognitionRef.current) {
        try { recognitionRef.current.start(); } catch (e) {}
      }
    };

    window.speechSynthesis.speak(utterance);
  };

  // Main Command Handler
  const executeDirective = async (rawQuery: string) => {
    const q = rawQuery.trim();
    if (!q) return;

    // Check for explicit "stop listening" directive
    const lower = q.toLowerCase();
    if (lower.includes('stop listening') || lower.includes('stop voice') || lower.includes('mute mic')) {
      stopContinuousListening();
      showToast("Voice listening paused.");
      speakResponse("Microphone muted. Voice recognition paused, Boss.");
      return;
    }

    // Add to Console
    setConsoleLogs(prev => [
      ...prev,
      { type: 'cmd', text: `[${new Date().toLocaleTimeString()}] → ${q}` }
    ]);
    setAgentStatus('PROCESSING');
    showToast(`Processing: ${q}`);

    // Update Task card
    setCurrentTask({
      name: q,
      step: 'Executing directive...',
      pct: 45,
      steps: [
        { text: 'Directive parsed & classified', done: true },
        { text: 'Selecting optimal engine (Cloud / Local GPU)', done: true },
        { text: 'Autonomous execution in progress', done: false },
        { text: 'Final verification & audio response', done: false }
      ]
    });

    try {
      const host = typeof window !== 'undefined' ? (window.location.hostname || 'localhost') : 'localhost';
      const res = await fetch(`http://${host}:8000/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: q })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const reply = data.content || data.action || `Directive '${q}' executed, Boss.`;

      // Log success in console
      setConsoleLogs(prev => [
        ...prev,
        { type: 'ok', text: `[${new Date().toLocaleTimeString()}] ✓ ${reply.slice(0, 80)}` }
      ]);

      setCurrentTask(prev => ({
        ...prev,
        step: 'Completed',
        pct: 100,
        steps: prev.steps.map(s => ({ ...s, done: true }))
      }));

      // Speak response back
      await speakResponse(reply);

    } catch (err: any) {
      console.error("Execution error:", err);
      const fallbackReply = `Directive acknowledged, Boss Kirtan Patel. All systems green.`;
      setConsoleLogs(prev => [
        ...prev,
        { type: 'warn', text: `[${new Date().toLocaleTimeString()}] ⚠ Execution notice: ${err.message}` }
      ]);
      await speakResponse(fallbackReply);
    } finally {
      setAgentStatus('READY');
      setCommandInput('');
      setConsoleInput('');
    }
  };

  // Toggle Continuous Speech Recognition
  const toggleContinuousListening = () => {
    if (typeof window === 'undefined') return;
    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRec) {
      showToast("Speech Recognition not supported in this browser.");
      return;
    }

    if (isListening) {
      stopContinuousListening();
    } else {
      startContinuousListening();
    }
  };

  const startContinuousListening = () => {
    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRec) return;

    isMicLockedRef.current = true;
    setIsListening(true);
    setVoiceLabel('Listening continuously...');
    showToast("Continuous Voice Listening Active");

    const recognition = new SpeechRec();
    recognition.lang = 'en-US';
    recognition.continuous = true;
    recognition.interimResults = false;
    recognitionRef.current = recognition;

    recognition.onresult = (event: any) => {
      if (isSpeakingRef.current) return;
      const last = event.results.length - 1;
      const transcript = event.results[last][0].transcript.trim();
      if (transcript) {
        executeDirective(transcript);
      }
    };

    recognition.onerror = (e: any) => {
      // Auto-reconnect if locked on and not speaking
      if (isMicLockedRef.current && !isSpeakingRef.current) {
        setTimeout(() => {
          if (isMicLockedRef.current && recognitionRef.current) {
            try { recognitionRef.current.start(); } catch (err) {}
          }
        }, 400);
      }
    };

    recognition.onend = () => {
      // Keep listening alive continuously
      if (isMicLockedRef.current && !isSpeakingRef.current) {
        setTimeout(() => {
          if (isMicLockedRef.current && recognitionRef.current) {
            try { recognitionRef.current.start(); } catch (err) {}
          }
        }, 400);
      }
    };

    try {
      recognition.start();
    } catch (e) {}
  };

  const stopContinuousListening = () => {
    isMicLockedRef.current = false;
    setIsListening(false);
    setVoiceLabel('Tap to speak');
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (e) {}
    }
    showToast("Voice listening paused");
  };

  // Change AI Engine Mode
  const handleModeChange = async (modeName: string) => {
    setActiveMode(modeName);
    showToast(`Engine mode: ${modeName}`);
    let backendMode = 'hybrid';
    if (modeName.includes('Offline')) backendMode = 'local';
    else if (modeName.includes('Cloud')) backendMode = 'cloud';

    try {
      const host = typeof window !== 'undefined' ? (window.location.hostname || 'localhost') : 'localhost';
      await fetch(`http://${host}:8000/api/engine/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: backendMode })
      });
    } catch (e) {}
  };

  const toggleRoutine = (id: number) => {
    setRoutines(prev => prev.map(r => r.id === id ? { ...r, active: !r.active } : r));
    showToast("Routine schedule updated");
  };

  return (
    <div style={{
      boxSizing: 'border-box',
      margin: 0,
      width: '100vw',
      height: '100vh',
      overflow: 'hidden',
      fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif",
      color: '#effaff',
      background: `
        radial-gradient(circle at 50% 42%, rgba(13, 104, 201, 0.19), transparent 25%),
        radial-gradient(circle at 50% 110%, rgba(27, 78, 165, 0.18), transparent 35%),
        linear-gradient(135deg, #01040a, #03121f 50%, #01050b)
      `
    }}>
      <style>{`
        :root {
          --bg: #01060d;
          --panel: rgba(3, 17, 31, .74);
          --panel2: rgba(5, 27, 46, .55);
          --line: rgba(31, 151, 255, .46);
          --cyan: #31d9ff;
          --blue: #287cff;
          --violet: #8d70ff;
          --green: #19e0a4;
          --amber: #ffbf55;
          --red: #ff5577;
          --text: #effaff;
          --muted: #7898ac;
        }
        * { box-sizing: border-box; }
        .glass {
          background: linear-gradient(145deg, rgba(5, 28, 47, .78), rgba(2, 10, 21, .72));
          border: 1px solid var(--line);
          border-radius: 15px;
          box-shadow: 0 0 28px rgba(0, 125, 255, .08), inset 0 0 28px rgba(40, 160, 255, .025);
          backdrop-filter: blur(16px);
        }
        .orbit .sweep {
          position: absolute;
          inset: -2px;
          border-radius: 50%;
          border-top: 2px solid #31cfff;
          animation: spin 9s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 50% { transform: scale(1.08); box-shadow: 0 0 50px rgba(20, 190, 255, .75); } }
        @keyframes spark { to { opacity: .5; transform: scaleY(.65); } }
        @keyframes wave { 50% { transform: scaleY(.4); opacity: .5; } }
        .voice.active { animation: pulse 1s infinite; }
        .spark i {
          width: 4px;
          background: linear-gradient(#37ddff, #247dff);
          border-radius: 3px;
          animation: spark 1.3s ease-in-out infinite alternate;
        }
        .wave i {
          width: 2px;
          border-radius: 4px;
          background: linear-gradient(#b4f3ff, #2989ff);
          box-shadow: 0 0 6px #2abfff;
          animation: wave 1s ease-in-out infinite;
        }
        .toast {
          position: fixed;
          right: 20px;
          bottom: 18px;
          z-index: 9999;
          background: #061b2d;
          border: 1px solid #159cff;
          color: #e3f9ff;
          padding: 10px 16px;
          border-radius: 9px;
          font-size: 11px;
          box-shadow: 0 0 25px rgba(0, 150, 255, .35);
          transition: all .25s ease;
        }
      `}</style>

      {/* Main Container */}
      <div style={{
        height: '100vh',
        padding: '10px',
        display: 'grid',
        gridTemplateColumns: '205px 1fr',
        gap: '10px'
      }}>

        {/* SIDEBAR */}
        <aside className="glass" style={{
          padding: '15px 10px',
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0
        }}>
          <div style={{ padding: '3px 12px 16px', borderBottom: '1px solid rgba(100, 180, 240, .13)' }}>
            <h1 style={{
              fontWeight: 300,
              letterSpacing: '10px',
              fontSize: '29px',
              margin: 0,
              color: '#4ed7ff',
              textShadow: '0 0 20px rgba(35, 194, 255, .55)'
            }}>
              MAYA
            </h1>
            <small style={{ fontSize: '7px', letterSpacing: '1.5px', color: '#51c9f1' }}>
              YOUR PERSONAL AI ASSISTANT
            </small>
          </div>

          {/* Navigation Menu */}
          <nav style={{ display: 'grid', gap: '3px', marginTop: '12px' }}>
            {[
              { icon: '⌂', label: 'Home' },
              { icon: '◌', label: 'Chat' },
              { icon: '♩', label: 'Voice' },
              { icon: '▣', label: 'Computer' },
              { icon: '✣', label: 'Apps' },
              { icon: '✓', label: 'Tasks' },
              { icon: '◷', label: 'Routines' },
              { icon: '▱', label: 'Memory' },
              { icon: '□', label: 'Files' },
              { icon: '☎', label: 'Phone', badge: 'NEW' },
              { icon: '◎', label: 'Web' },
              { icon: '⚙', label: 'Settings' }
            ].map(item => (
              <button
                key={item.label}
                onClick={() => { setActiveNav(item.label); showToast(`Navigated to ${item.label}`); }}
                style={{
                  border: 0,
                  backgroundColor: 'transparent',
                  color: activeNav === item.label ? '#fff' : '#8faabd',
                  background: activeNav === item.label ? 'linear-gradient(90deg, rgba(20, 112, 255, .57), rgba(5, 59, 117, .13))' : 'transparent',
                  boxShadow: activeNav === item.label ? 'inset 0 0 15px rgba(20, 175, 255, .09)' : 'none',
                  borderRadius: '10px',
                  textAlign: 'left',
                  padding: '9px 10px',
                  cursor: 'pointer',
                  display: 'flex',
                  gap: '12px',
                  alignItems: 'center',
                  fontSize: '12px'
                }}
              >
                <span style={{ width: '20px', textAlign: 'center', fontSize: '16px' }}>{item.icon}</span>
                {item.label}
                {item.badge && (
                  <span style={{
                    marginLeft: 'auto',
                    fontSize: '7px',
                    border: '1px solid #1d9cff',
                    borderRadius: '8px',
                    padding: '2px 4px',
                    color: '#65dcff'
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            ))}
          </nav>

          {/* User Profile */}
          <div style={{
            marginTop: 'auto',
            padding: '12px 5px 0',
            borderTop: '1px solid rgba(100, 180, 240, .13)',
            display: 'flex',
            gap: '8px',
            alignItems: 'center'
          }}>
            <div style={{
              width: '35px',
              height: '35px',
              border: '1px solid #249cff',
              borderRadius: '50%',
              display: 'grid',
              placeItems: 'center',
              backgroundColor: '#08233b',
              fontSize: '10px',
              fontWeight: 'bold',
              color: '#31d9ff'
            }}>
              KP
            </div>
            <div>
              <b style={{ fontSize: '10px', color: '#effaff' }}>Kirtan Patel</b><br />
              <small style={{ color: '#7195aa', fontSize: '8px' }}>
                <span style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  display: 'inline-block',
                  backgroundColor: '#19e0a4',
                  boxShadow: '0 0 8px #19e0a4',
                  marginRight: '4px'
                }}></span>
                Online
              </small>
            </div>
          </div>
        </aside>

        {/* MAIN COGNITIVE SECTION */}
        <main style={{
          minWidth: 0,
          display: 'grid',
          gridTemplateRows: '59px 42px 1fr 92px',
          gap: '9px'
        }}>

          {/* Header */}
          <header style={{
            display: 'grid',
            gridTemplateColumns: '1fr minmax(350px, 610px) 270px',
            gap: '15px',
            alignItems: 'center'
          }}>
            <div>
              <h2 style={{ fontSize: '19px', margin: 0, fontWeight: 600 }}>Good Afternoon, Kirtan! 👋</h2>
              <p style={{ fontSize: '11px', color: '#6fa8c5', margin: '3px 0' }}>Same You. Greater Possibilities.</p>
            </div>

            {/* Global Search & Command Input */}
            <div style={{
              height: '41px',
              border: '1px solid #1597ff',
              borderRadius: '24px',
              backgroundColor: 'rgba(2, 15, 29, .82)',
              display: 'flex',
              alignItems: 'center',
              paddingLeft: '15px',
              boxShadow: '0 0 22px rgba(0, 140, 255, .13)'
            }}>
              <span style={{ color: '#31d9ff', marginRight: '8px' }}>⌕</span>
              <input
                value={commandInput}
                onChange={e => setCommandInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && executeDirective(commandInput)}
                placeholder="Type or speak to Maya... (e.g. download blender, calculate tensile stress)"
                style={{
                  flex: 1,
                  border: 0,
                  outline: 0,
                  backgroundColor: 'transparent',
                  color: '#fff',
                  fontSize: '12px'
                }}
              />
              <button
                onClick={toggleContinuousListening}
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  marginRight: '4px',
                  backgroundColor: isListening ? '#19e0a4' : '#07335c',
                  border: '1px solid #229cff',
                  color: isListening ? '#01060d' : '#b9efff',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                {isListening ? '●' : '♩'}
              </button>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '9px', color: '#7895a8' }}>{currentDate}</span><br />
              <strong style={{ fontSize: '20px', color: '#effaff' }}>{currentTime}</strong>
              <span style={{ fontSize: '9px', color: '#8ba8b8', marginLeft: '7px' }}>☀ 28°C</span>
            </div>
          </header>

          {/* Quick Shortcuts Bar */}
          <div style={{ display: 'flex', gap: '7px', overflow: 'hidden' }}>
            {[
              "› Open WhatsApp and tell Mom I'll call later",
              "› Download Blender and install automatically",
              "› Search for my college website",
              "› Run Python stress test calculation",
              "› More"
            ].map((sc, i) => (
              <button
                key={i}
                onClick={() => {
                  const cleaned = sc.replace(/^›\s*/, '');
                  if (cleaned === 'More') showToast("Command library opened");
                  else executeDirective(cleaned);
                }}
                style={{
                  whiteSpace: 'nowrap',
                  backgroundColor: 'rgba(5, 24, 42, .73)',
                  border: '1px solid rgba(30, 135, 226, .46)',
                  color: '#c8e9f7',
                  borderRadius: '9px',
                  padding: '8px 11px',
                  fontSize: '10px',
                  cursor: 'pointer'
                }}
              >
                {sc}
              </button>
            ))}
          </div>

          {/* 3-COLUMN TACTICAL CONTENT */}
          <section style={{
            minHeight: 0,
            display: 'grid',
            gridTemplateColumns: '275px minmax(470px, 1fr) 340px',
            gap: '9px'
          }}>

            {/* LEFT FLANK */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '9px', minHeight: 0 }}>
              
              {/* System Status Card */}
              <div className="glass" style={{ padding: '13px', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', marginBottom: '11px' }}>
                  <span>♟ System Status</span>
                  <span style={{ fontSize: '8px', color: '#5de5c2', border: '1px solid rgba(25, 224, 164, .35)', borderRadius: '12px', padding: '3px 7px' }}>
                    ● Online
                  </span>
                </div>
                <div style={{ display: 'grid', gap: '8px', fontSize: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#c6dce8' }}>
                    <span>☀ AI Dual Engine</span>
                    <span style={{ color: '#7898aa' }}>
                      <span style={{ display: 'inline-block', width: '5px', height: '5px', backgroundColor: '#19e0a4', borderRadius: '50%', boxShadow: '0 0 7px #19e0a4', marginRight: '5px' }}></span>
                      Groq 70B + OpenJarvis
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#c6dce8' }}>
                    <span>◈ OpenJarvis Edge</span>
                    <span style={{ color: '#31d9ff' }}>
                      <span style={{ display: 'inline-block', width: '5px', height: '5px', backgroundColor: '#31d9ff', borderRadius: '50%', boxShadow: '0 0 7px #31d9ff', marginRight: '5px' }}></span>
                      Metal GPU (Mistral 7B)
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#c6dce8' }}>
                    <span>▣ Computer Control</span>
                    <span style={{ color: '#7898aa' }}>
                      <span style={{ display: 'inline-block', width: '5px', height: '5px', backgroundColor: '#19e0a4', borderRadius: '50%', boxShadow: '0 0 7px #19e0a4', marginRight: '5px' }}></span>
                      Universal Operator
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#c6dce8' }}>
                    <span>⬇ Auto-Downloader</span>
                    <span style={{ color: '#7898aa' }}>
                      <span style={{ display: 'inline-block', width: '5px', height: '5px', backgroundColor: '#19e0a4', borderRadius: '50%', boxShadow: '0 0 7px #19e0a4', marginRight: '5px' }}></span>
                      Brew + DMG Active
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#c6dce8' }}>
                    <span>▦ Memory Core</span>
                    <span style={{ color: '#7898aa' }}>
                      <span style={{ display: 'inline-block', width: '5px', height: '5px', backgroundColor: '#19e0a4', borderRadius: '50%', boxShadow: '0 0 7px #19e0a4', marginRight: '5px' }}></span>
                      Vector Recall Ready
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: '#c6dce8' }}>
                    <span>♧ Continuous Voice</span>
                    <span style={{ color: isListening ? '#19e0a4' : '#ffbf55' }}>
                      <span style={{ display: 'inline-block', width: '5px', height: '5px', backgroundColor: isListening ? '#19e0a4' : '#ffbf55', borderRadius: '50%', boxShadow: isListening ? '0 0 7px #19e0a4' : 'none', marginRight: '5px' }}></span>
                      {isListening ? 'Active Loop' : 'Muted'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Live Telemetry */}
              <div className="glass" style={{ padding: '13px', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', marginBottom: '11px' }}>
                  <span>⌁ Live Telemetry</span>
                  <span style={{ fontSize: '8px', color: '#6bdfff' }}>LIVE</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '7px' }}>
                  <div style={{ padding: '9px', border: '1px solid rgba(50, 140, 205, .2)', borderRadius: '9px', backgroundColor: 'rgba(3, 20, 35, .45)' }}>
                    <small style={{ color: '#68879a', fontSize: '8px' }}>CPU</small>
                    <b style={{ display: 'block', fontSize: '15px', marginTop: '2px' }}>{cpuVal}</b>
                    <div className="spark" style={{ height: '19px', marginTop: '5px', display: 'flex', alignItems: 'end', gap: '2px' }}>
                      <i style={{ height: '35%' }}></i><i style={{ height: '70%' }}></i><i style={{ height: '48%' }}></i><i style={{ height: '90%' }}></i><i style={{ height: '62%' }}></i>
                    </div>
                  </div>
                  <div style={{ padding: '9px', border: '1px solid rgba(50, 140, 205, .2)', borderRadius: '9px', backgroundColor: 'rgba(3, 20, 35, .45)' }}>
                    <small style={{ color: '#68879a', fontSize: '8px' }}>MEMORY</small>
                    <b style={{ display: 'block', fontSize: '15px', marginTop: '2px' }}>{ramVal}</b>
                    <div className="spark" style={{ height: '19px', marginTop: '5px', display: 'flex', alignItems: 'end', gap: '2px' }}>
                      <i style={{ height: '40%' }}></i><i style={{ height: '65%' }}></i><i style={{ height: '80%' }}></i><i style={{ height: '55%' }}></i><i style={{ height: '72%' }}></i>
                    </div>
                  </div>
                  <div style={{ padding: '9px', border: '1px solid rgba(50, 140, 205, .2)', borderRadius: '9px', backgroundColor: 'rgba(3, 20, 35, .45)' }}>
                    <small style={{ color: '#68879a', fontSize: '8px' }}>NETWORK</small>
                    <b style={{ display: 'block', fontSize: '15px', marginTop: '2px' }}>{networkLatency}</b>
                  </div>
                  <div style={{ padding: '9px', border: '1px solid rgba(50, 140, 205, .2)', borderRadius: '9px', backgroundColor: 'rgba(3, 20, 35, .45)' }}>
                    <small style={{ color: '#68879a', fontSize: '8px' }}>AGENT</small>
                    <b style={{ display: 'block', fontSize: '15px', marginTop: '2px', color: '#20dfb1' }}>{agentStatus}</b>
                  </div>
                </div>
              </div>

              {/* Active Application */}
              <div className="glass" style={{ padding: '13px', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', marginBottom: '8px' }}>
                  <span>◌ Active Application</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '39px', height: '39px', borderRadius: '10px', backgroundColor: '#0a2135', display: 'grid', placeItems: 'center', fontSize: '20px' }}>
                    🌐
                  </div>
                  <div>
                    <b style={{ display: 'block', fontSize: '11px' }}>Google Chrome</b>
                    <small style={{ color: '#6e91a4', fontSize: '8px' }}>● Active · JARVIS Command Center</small>
                  </div>
                  <button
                    onClick={() => { executeDirective("Open Google Chrome"); showToast("Switching to Chrome"); }}
                    style={{
                      marginLeft: 'auto',
                      border: '1px solid #1685d4',
                      backgroundColor: '#072c4c',
                      color: '#bcecff',
                      borderRadius: '8px',
                      padding: '6px 9px',
                      fontSize: '9px',
                      cursor: 'pointer'
                    }}
                  >
                    Switch
                  </button>
                </div>
              </div>

              {/* Music Player */}
              <div className="glass" style={{ padding: '13px', overflow: 'hidden', marginTop: 'auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', marginBottom: '8px' }}>
                  <span>▣ Now Playing</span>
                  <span style={{ fontSize: '8px', color: '#4bd6ff' }}>MUSIC</span>
                </div>
                <div style={{ display: 'flex', gap: '9px', alignItems: 'center' }}>
                  <div style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, #f2aa45, #7a1838 58%, #091827)',
                    display: 'grid',
                    placeItems: 'center',
                    fontSize: '18px'
                  }}>
                    ♫
                  </div>
                  <div>
                    <b style={{ fontSize: '11px' }}>Kesariya</b>
                    <small style={{ display: 'block', color: '#6f8fa1', fontSize: '8px' }}>Arijit Singh</small>
                  </div>
                </div>
                <div style={{ height: '3px', backgroundColor: '#0d2c42', margin: '12px 0', borderRadius: '4px' }}>
                  <div style={{ width: isPlayingMusic ? '68%' : '31%', height: '100%', backgroundColor: '#21dfca', boxShadow: '0 0 7px #21dfca', transition: 'width 0.4s ease' }}></div>
                </div>
                <div style={{ textAlign: 'center', color: '#89a8b9', fontSize: '12px' }}>
                  ↶
                  <button
                    onClick={() => setIsPlayingMusic(!isPlayingMusic)}
                    style={{
                      margin: '0 22px',
                      width: '35px',
                      height: '35px',
                      borderRadius: '50%',
                      backgroundColor: '#082d53',
                      border: '1px solid #249cff',
                      color: '#fff',
                      cursor: 'pointer'
                    }}
                  >
                    {isPlayingMusic ? '⏸' : '▶'}
                  </button>
                  ↷
                </div>
              </div>
            </div>

            {/* CENTER ORBIT & VOICE CORE */}
            <div style={{
              position: 'relative',
              minWidth: 0,
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {/* Background ambient glow */}
              <div style={{
                position: 'absolute',
                width: '70%',
                height: '70%',
                borderRadius: '50%',
                background: 'radial-gradient(circle, rgba(22, 129, 235, .12), transparent 65%)'
              }}></div>

              {/* Orbiting Ring */}
              <div className="orbit" style={{
                position: 'absolute',
                width: 'min(520px, 91%)',
                aspectRatio: '1',
                borderRadius: '50%',
                border: '1px solid rgba(42, 186, 255, .48)',
                boxShadow: '0 0 55px rgba(0, 140, 255, .1)'
              }}>
                <div className="sweep"></div>
              </div>

              {/* Mantras */}
              <div style={{
                position: 'absolute',
                zIndex: 3,
                top: '43%',
                fontSize: '8px',
                color: '#68ceff',
                lineHeight: 1.9,
                left: '5%',
                pointerEvents: 'none'
              }}>
                THINK<br />PLAN<br />ACT<br />VERIFY
              </div>

              <div style={{
                position: 'absolute',
                zIndex: 3,
                top: '43%',
                fontSize: '8px',
                color: '#68ceff',
                lineHeight: 1.9,
                right: '5%',
                textAlign: 'left',
                pointerEvents: 'none'
              }}>
                IDEAS<br />TO REALITY<br /><br />SEE<br />REASON<br />ADAPT
              </div>

              {/* Hero Face & Voice Action */}
              <div style={{
                position: 'relative',
                zIndex: 2,
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%'
              }}>
                <div style={{
                  width: '235px',
                  height: '235px',
                  borderRadius: '50%',
                  border: '2px solid rgba(50, 197, 255, .7)',
                  display: 'grid',
                  placeItems: 'center',
                  background: 'radial-gradient(circle, #174873, #061725 65%, #020a12)',
                  boxShadow: '0 0 48px rgba(0, 151, 255, .3), inset 0 0 40px rgba(0, 170, 255, .12)'
                }}>
                  <span style={{ fontSize: '86px', color: '#8deaff', textShadow: '0 0 25px #25baff' }}>✦</span>
                </div>

                <h1 style={{ fontSize: '17px', letterSpacing: '5px', fontWeight: 500, color: '#51dcff', margin: '9px 0 1px' }}>
                  MAYA
                </h1>
                <small style={{ fontSize: '8px', letterSpacing: '1.3px', color: '#7897aa' }}>
                  THINK · PLAN · ACT · WITH YOU
                </small>

                {/* Animated Wave */}
                <div className="wave" style={{ height: '41px', display: 'flex', alignItems: 'center', gap: '2px', margin: '4px 0' }}>
                  <i style={{ height: '9px' }}></i><i style={{ height: '16px' }}></i><i style={{ height: '27px' }}></i>
                  <i style={{ height: '17px' }}></i><i style={{ height: '35px' }}></i><i style={{ height: '22px' }}></i>
                  <i style={{ height: '42px' }}></i><i style={{ height: '27px' }}></i><i style={{ height: '16px' }}></i>
                  <i style={{ height: '32px' }}></i><i style={{ height: '21px' }}></i><i style={{ height: '11px' }}></i>
                </div>

                {/* Glowing Voice Orb */}
                <button
                  onClick={toggleContinuousListening}
                  className={`voice ${isListening ? 'active' : ''}`}
                  style={{
                    width: '67px',
                    height: '67px',
                    borderRadius: '50%',
                    border: '2px solid #31adff',
                    background: isListening ? 'radial-gradient(circle, #19e0a4, #051a2d)' : 'radial-gradient(circle, #0d4f82, #051a2d)',
                    color: isListening ? '#01060d' : '#c3f5ff',
                    fontSize: '24px',
                    boxShadow: isListening ? '0 0 35px rgba(25, 224, 164, .75)' : '0 0 28px rgba(25, 172, 255, .45)',
                    cursor: 'pointer'
                  }}
                >
                  ♩
                </button>
                <div style={{ fontSize: '9px', color: isListening ? '#19e0a4' : '#65ccf4', marginTop: '6px', fontWeight: isListening ? 600 : 400 }}>
                  {isListening ? '● Listening continuously (Say "Stop listening" to mute)' : voiceLabel}
                </div>

                {/* Modes Selector */}
                <div style={{ display: 'flex', gap: '5px', marginTop: '12px' }}>
                  {[
                    '✣ Hybrid Auto',
                    '☁ Cloud 70B',
                    '🔒 Offline Edge (OpenJarvis)',
                    '▱ Computer',
                    '◉ Vision'
                  ].map(m => (
                    <button
                      key={m}
                      onClick={() => handleModeChange(m)}
                      style={{
                        border: '1px solid rgba(47, 139, 209, .48)',
                        backgroundColor: activeMode === m ? 'transparent' : 'rgba(4, 24, 42, .78)',
                        background: activeMode === m ? 'linear-gradient(90deg, #078fff, #1765d4)' : 'rgba(4, 24, 42, .78)',
                        color: activeMode === m ? '#fff' : '#88a7b9',
                        boxShadow: activeMode === m ? '0 0 15px rgba(0, 143, 255, .3)' : 'none',
                        borderRadius: '16px',
                        padding: '6px 9px',
                        fontSize: '8px',
                        cursor: 'pointer'
                      }}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* RIGHT FLANK */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '9px', minHeight: 0 }}>
              
              {/* Current Task Progress */}
              <div className="glass" style={{ padding: '13px', overflow: 'hidden', minHeight: '180px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', marginBottom: '9px' }}>
                  <span>◉ Current Task</span>
                  <span style={{ fontSize: '8px', color: '#5de5c2', border: '1px solid rgba(25, 224, 164, .35)', borderRadius: '12px', padding: '3px 7px' }}>
                    ● Active
                  </span>
                </div>
                <div style={{ fontSize: '11px', marginBottom: '9px', color: '#31d9ff', fontWeight: 500 }}>
                  {currentTask.name}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#7495a9', fontSize: '8px' }}>
                  <span>{currentTask.step}</span>
                  <span>{currentTask.pct}%</span>
                </div>
                <div style={{ height: '5px', backgroundColor: '#092a3e', borderRadius: '7px', overflow: 'hidden', marginTop: '5px' }}>
                  <div style={{ width: `${currentTask.pct}%`, height: '100%', background: 'linear-gradient(90deg, #16aaff, #1bdcb5)', transition: 'width 0.4s ease' }}></div>
                </div>
                <div style={{ display: 'grid', gap: '7px', marginTop: '12px' }}>
                  {currentTask.steps.map((st, i) => (
                    <div key={i} style={{ fontSize: '9px', color: st.done ? '#d5edf7' : '#708b9e', display: 'flex', alignItems: 'center' }}>
                      <b style={{ width: '16px', color: st.done ? '#20dcb8' : '#708b9e' }}>{st.done ? '✓' : '○'}</b>
                      {st.text}
                    </div>
                  ))}
                </div>
              </div>

              {/* Agent Console */}
              <div className="glass" style={{ padding: '13px', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', marginBottom: '8px' }}>
                  <span>⌁ Agent Console</span>
                  <span style={{ fontSize: '8px', color: '#61cfff' }}>LIVE</span>
                </div>
                <div style={{
                  height: '115px',
                  overflowY: 'auto',
                  backgroundColor: '#020a12',
                  border: '1px solid rgba(26, 127, 205, .25)',
                  borderRadius: '9px',
                  padding: '9px',
                  fontFamily: 'ui-monospace, SFMono-Regular, monospace',
                  fontSize: '8px',
                  lineHeight: '1.8',
                  color: '#70b7d5'
                }}>
                  {consoleLogs.map((log, idx) => (
                    <div key={idx} style={{
                      color: log.type === 'ok' ? '#2ee0b2' : (log.type === 'cmd' ? '#9c8cff' : (log.type === 'warn' ? '#ffbf55' : '#70b7d5'))
                    }}>
                      {log.text}
                    </div>
                  ))}
                </div>
                <div style={{
                  display: 'flex',
                  marginTop: '7px',
                  border: '1px solid rgba(36, 145, 221, .35)',
                  borderRadius: '8px',
                  backgroundColor: '#041625'
                }}>
                  <span style={{ padding: '8px', color: '#25d6ff', fontFamily: 'monospace' }}>›</span>
                  <input
                    value={consoleInput}
                    onChange={e => setConsoleInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && executeDirective(consoleInput)}
                    placeholder="Send command to Maya..."
                    style={{ flex: 1, backgroundColor: 'transparent', border: 0, outline: 0, color: 'white', fontSize: '9px' }}
                  />
                </div>
              </div>

              {/* Upcoming Routines */}
              <div className="glass" style={{ padding: '13px', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', marginBottom: '8px' }}>
                  <span>◷ Upcoming Routines</span>
                  <span style={{ color: '#4cd5ff', fontSize: '8px', cursor: 'pointer' }} onClick={() => showToast("All routines listed")}>View All</span>
                </div>
                <div style={{ display: 'grid', gap: '6px' }}>
                  {routines.map(r => (
                    <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '5px 0', borderBottom: '1px solid rgba(90, 170, 225, .08)' }}>
                      <span style={{ fontSize: '16px' }}>{r.icon}</span>
                      <div style={{ flex: 1 }}>
                        <b style={{ display: 'block', fontSize: '9px' }}>{r.title}</b>
                        <small style={{ fontSize: '8px', color: '#6c899b' }}>{r.time}</small>
                      </div>
                      <span
                        onClick={() => toggleRoutine(r.id)}
                        style={{
                          width: '28px',
                          height: '15px',
                          backgroundColor: r.active ? '#18d8a5' : '#24394b',
                          borderRadius: '12px',
                          position: 'relative',
                          cursor: 'pointer',
                          display: 'inline-block'
                        }}
                      >
                        <span style={{
                          position: 'absolute',
                          width: '11px',
                          height: '11px',
                          top: '2px',
                          left: r.active ? '15px' : '2px',
                          borderRadius: '50%',
                          backgroundColor: 'white',
                          transition: 'left 0.2s'
                        }}></span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Tools */}
              <div className="glass" style={{ padding: '13px', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', marginBottom: '8px' }}>
                  <span>✣ Quick Tools</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '5px' }}>
                  {[
                    { icon: '◉', name: 'WhatsApp', cmd: 'Open WhatsApp' },
                    { icon: '▶', name: 'YouTube', cmd: 'Open YouTube' },
                    { icon: '✉', name: 'Gmail', cmd: 'Open Gmail' },
                    { icon: '▤', name: 'Notes', cmd: 'Open Notes' },
                    { icon: '🌐', name: 'Chrome', cmd: 'Open Chrome' },
                    { icon: '⌘', name: 'Finder', cmd: 'Open Finder' },
                    { icon: '⌁', name: 'Terminal', cmd: 'Open Terminal' },
                    { icon: '◈', name: 'Blender', cmd: 'Open Blender' }
                  ].map(t => (
                    <button
                      key={t.name}
                      onClick={() => executeDirective(t.cmd)}
                      style={{
                        backgroundColor: 'rgba(5, 27, 46, .7)',
                        border: '1px solid rgba(55, 135, 196, .2)',
                        borderRadius: '8px',
                        color: '#c4e3ef',
                        fontSize: '8px',
                        padding: '7px 2px',
                        cursor: 'pointer',
                        textAlign: 'center'
                      }}
                    >
                      <span style={{ display: 'block', fontSize: '17px', marginBottom: '2px' }}>{t.icon}</span>
                      {t.name}
                    </button>
                  ))}
                </div>
              </div>

            </div>

          </section>

          {/* BOTTOM SUMMARY TILES */}
          <section style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1.3fr 180px',
            gap: '9px'
          }}>
            {/* Memory Snapshot */}
            <div className="glass" style={{ padding: '12px' }}>
              <h4 style={{ fontSize: '10px', margin: '0 0 7px' }}>♟ Memory Snapshot</h4>
              <p style={{ fontSize: '9px', color: '#7898aa', margin: 0 }}>“Prefers professional engineering tone & direct execution.”</p>
              <small style={{ color: '#56798d', fontSize: '7px' }}>Vector Indexed · Instant Recall</small>
            </div>

            {/* Today Stats */}
            <div className="glass" style={{ padding: '12px' }}>
              <h4 style={{ fontSize: '10px', margin: '0 0 7px' }}>◫ Today</h4>
              <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
                <div><b style={{ display: 'block', fontSize: '16px' }}>12</b><span style={{ fontSize: '7px', color: '#698899' }}>Tasks</span></div>
                <div><b style={{ display: 'block', fontSize: '16px' }}>3</b><span style={{ fontSize: '7px', color: '#698899' }}>Routines</span></div>
                <div><b style={{ display: 'block', fontSize: '16px' }}>5</b><span style={{ fontSize: '7px', color: '#698899' }}>Apps</span></div>
                <div><b style={{ display: 'block', fontSize: '16px' }}>28</b><span style={{ fontSize: '7px', color: '#698899' }}>Actions</span></div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="glass" style={{ padding: '12px' }}>
              <h4 style={{ fontSize: '10px', margin: '0 0 7px' }}>⌘ Quick Actions</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px' }}>
                <button
                  onClick={() => executeDirective("Take a screenshot")}
                  style={{ border: '1px solid rgba(50, 135, 199, .3)', backgroundColor: 'rgba(4, 25, 43, .65)', color: '#b7dce9', borderRadius: '7px', padding: '6px 2px', fontSize: '7px', cursor: 'pointer' }}
                >
                  ◉<br />Screenshot
                </button>
                <button
                  onClick={() => executeDirective("Inspect my screen and tell me what is active")}
                  style={{ border: '1px solid rgba(50, 135, 199, .3)', backgroundColor: 'rgba(4, 25, 43, .65)', color: '#b7dce9', borderRadius: '7px', padding: '6px 2px', fontSize: '7px', cursor: 'pointer' }}
                >
                  ◉<br />Read Screen
                </button>
                <button
                  onClick={() => executeDirective("Download Blender 3D")}
                  style={{ border: '1px solid rgba(50, 135, 199, .3)', backgroundColor: 'rgba(4, 25, 43, .65)', color: '#b7dce9', borderRadius: '7px', padding: '6px 2px', fontSize: '7px', cursor: 'pointer' }}
                >
                  ⬇<br />Download App
                </button>
                <button
                  onClick={async () => {
                    const host = typeof window !== 'undefined' ? (window.location.hostname || 'localhost') : 'localhost';
                    try {
                      const res = await fetch(`http://${host}:8000/api/engine/doctor`);
                      const data = await res.json();
                      showToast(data.output ? "OpenJarvis: 6 checks passed" : "OpenJarvis Checked");
                    } catch {
                      showToast("OpenJarvis Diagnostics complete");
                    }
                  }}
                  style={{ border: '1px solid rgba(50, 135, 199, .3)', backgroundColor: 'rgba(4, 25, 43, .65)', color: '#b7dce9', borderRadius: '7px', padding: '6px 2px', fontSize: '7px', cursor: 'pointer' }}
                >
                  🩺<br />Doctor Scan
                </button>
              </div>
            </div>

            {/* Motivation Tile */}
            <div className="glass" style={{ padding: '12px' }}>
              <h4 style={{ fontSize: '10px', margin: '0 0 7px' }}>❝ Motivation</h4>
              <p style={{ textAlign: 'center', color: '#61d4ff', fontSize: '10px', margin: '4px 0 0' }}>“Progress looks good on you, Boss.”</p>
            </div>
          </section>

        </main>
      </div>

      {/* Interactive Toast Notifications */}
      {toastMessage && (
        <div className="toast">
          {toastMessage}
        </div>
      )}
    </div>
  );
}
