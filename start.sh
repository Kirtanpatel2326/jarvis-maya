#!/bin/bash

# Load local environment if present
if [ -f "backend/.env" ]; then
    set -a
    source backend/.env
    set +a
elif [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

export PATH="$HOME/.hermes/node/bin:/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"

echo "=================================================="
echo "    STARTING J.A.R.V.I.S. UNIFIED MASTER CORE     "
echo "    HYBRID CLOUD + OPENJARVIS LOCAL GPU ENGINE    "
echo "=================================================="

# Ensure OpenJarvis / Ollama daemon is running
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "[OPENJARVIS] Starting background Ollama Metal GPU daemon..."
    ollama serve > /Users/kirtanpatel/.openjarvis/ollama_serve.log 2>&1 &
    sleep 2
fi

# Auto-recovery: FastAPI Backend
run_backend() {
    until python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload; do
        echo "[J.A.R.V.I.S. Core] Backend process exited. Respawning in 1s..." >&2
        sleep 1
    done
}

# Auto-recovery: Next.js Frontend
run_frontend() {
    cd frontend || exit
    until npm run dev -- -p 3000 -H 0.0.0.0; do
        echo "[J.A.R.V.I.S. HUD] Frontend process exited. Respawning in 1s..." >&2
        sleep 1
    done
}

run_backend &
run_frontend &

wait
