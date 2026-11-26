# J.A.R.V.I.S. & M.A.Y.A. — Autonomous AI Companion & Tactical Command Deck

A modern, full-stack autonomous AI desktop companion and web command center. Engineered for local performance, resilient hybrid model execution, voice interaction, and desktop task automation.

## Architecture

- **Frontend**: Next.js 16 and React 19 glassmorphism interface with telemetry gauges, live status monitors, and voice controls.
- **Backend Core**: FastAPI asynchronous service orchestrating natural language understanding, tools, and background tasks.
- **Hybrid Inference Engine**:
  - Primary: Cloud inference via OpenAI-compatible endpoints (Groq).
  - Local Failover: On-device model execution via Ollama and local GPU acceleration.
- **Voice System**: Continuous microphone listening loop with speech synthesis and automatic echo suppression.
- **Automation Subsystem**: Desktop management, application controls, and software package installation.

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── integrations/
│   └── services/
├── frontend/
│   ├── app/
│   ├── public/
│   └── package.json
├── scripts/
│   └── export_project.py
├── .env.example
├── requirements.txt
└── start.sh
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- macOS (Apple Silicon recommended for local GPU inference)

### Setup

1. Clone repository:
   ```bash
   git clone https://github.com/Kirtanpatel2326/jarvis-maya.git
   cd jarvis-maya
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. Configure environment:
   ```bash
   cp .env.example backend/.env
   ```

5. Launch services:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

The dashboard will be available at `http://localhost:3000` and API documentation at `http://localhost:8000/docs`.

## License

MIT License.
