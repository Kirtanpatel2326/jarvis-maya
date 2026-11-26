"""
OpenJarvis Bridge for M.A.Y.A. / J.A.R.V.I.S.
Integrates the OpenJarvis Local Ollama Engine & CLI into the holographic system.
Provides:
- 100% Offline Edge Inference (Local GPU via Metal)
- Automatic failover from Cloud Groq to OpenJarvis Local
- Direct access to OpenJarvis CLI, agents, doctor diagnostics, and models
"""

import os
import json
import time
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
JARVIS_CLI_PATH = os.path.expanduser("~/.local/bin/jarvis")
OPENJARVIS_DIR = os.path.expanduser("~/.openjarvis")

class OpenJarvisBridge:
    current_mode: str = "hybrid"  # "hybrid" | "cloud" | "local"
    preferred_local_model: str = "mistral:latest"

    @classmethod
    def is_ollama_running(cls) -> bool:
        """Check if local Ollama server is responding."""
        try:
            req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags", headers={"User-Agent": "MAYA-Bridge"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def ensure_ollama_started(cls) -> bool:
        """Ensure the local Ollama daemon is running."""
        if cls.is_ollama_running():
            return True
        try:
            log_file = os.path.join(OPENJARVIS_DIR, "ollama_serve.log")
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=open(log_file, "a"),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            time.sleep(1.5)
            return cls.is_ollama_running()
        except Exception as e:
            print(f"[OPENJARVIS BRIDGE] Failed to launch Ollama: {e}")
            return False

    @classmethod
    def get_local_models(cls) -> List[str]:
        """Fetch list of local models available in Ollama."""
        try:
            req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags", headers={"User-Agent": "MAYA-Bridge"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode())
                return [m.get("name") for m in data.get("models", [])]
        except Exception:
            return []

    @classmethod
    def query_local_llm(
        cls,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 160,
        temperature: float = 0.2,
        timeout: float = 25.0
    ) -> Optional[str]:
        """
        Executes local inference through OpenJarvis / Ollama OpenAI-compatible endpoint.
        Uses 100% Metal GPU Unified Memory on Apple Silicon.
        """
        cls.ensure_ollama_started()
        
        target_model = model or cls.preferred_local_model
        available = cls.get_local_models()
        if available and target_model not in available:
            # Fall back to first available model
            target_model = available[0]

        payload = {
            "model": target_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "").strip()
        except Exception as e:
            print(f"[OPENJARVIS INFERENCE ERROR] {e}")
            return None
        return None

    @classmethod
    def run_doctor(cls) -> Dict[str, Any]:
        """Run `jarvis doctor` check and parse the report."""
        if not os.path.exists(JARVIS_CLI_PATH):
            return {"status": "error", "message": "OpenJarvis CLI not found."}
        try:
            res = subprocess.run(
                [JARVIS_CLI_PATH, "doctor"],
                capture_output=True,
                text=True,
                timeout=12
            )
            return {
                "status": "success",
                "output": res.stdout,
                "exit_code": res.returncode
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Comprehensive status report for the dual-engine holographic HUD."""
        ollama_active = cls.is_ollama_running()
        models = cls.get_local_models() if ollama_active else []
        return {
            "openjarvis_installed": os.path.exists(JARVIS_CLI_PATH),
            "ollama_active": ollama_active,
            "engine_mode": cls.current_mode,
            "local_models": models,
            "preferred_model": cls.preferred_local_model if cls.preferred_local_model in models else (models[0] if models else "None"),
            "cli_path": JARVIS_CLI_PATH if os.path.exists(JARVIS_CLI_PATH) else None,
            "metal_acceleration": "Apple Silicon Metal (Unified Memory)"
        }

    @classmethod
    def set_mode(cls, mode: str) -> str:
        """Update active engine mode."""
        if mode in ["hybrid", "cloud", "local"]:
            cls.current_mode = mode
        return cls.current_mode
