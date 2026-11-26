# J.A.R.V.I.S. Security & Defense Grid Protocol

Prepared for: Boss Kirtan Patel
Security Rating: Class-A Shielding (Local-Loopback Isolation)

---

## 1. Threat Model & Shield Architecture
Unlike public cloud agents that transmit your data to third-party servers, J.A.R.V.I.S. operates on a **Local-First Sandbox model**. Your files, shell access, and configuration keys never leave your local machine.

---

## 2. Hardened Protections

### A. Local Loopback Binding (Port Filtering)
- The FastAPI backend binds exclusively to `127.0.0.1` (localhost). It is inaccessible from the external LAN or public internet.
- **Port Security:** Attempts to query port `8002` from external IP addresses are automatically dropped by the macOS loopback filter.

### B. Tightened CORS & Origin Sandbox
- Cross-Origin Resource Sharing (CORS) is configured to block requests coming from unauthorized public domains.
- Only local interfaces (localhost/127.0.0.1 and file protocols) can make requests to execute system terminal commands or modify settings.

### C. Encrypted Configuration Storage
- API keys (Gemini, ElevenLabs) are loaded directly from your protected `.env` file.
- The `.env` file resides inside the backend workspace directory, utilizing POSIX filesystem permissions (`chmod 600`) so that only your local user account can read or write key parameters.
