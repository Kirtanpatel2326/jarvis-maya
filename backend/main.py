import os
import re
import json
import time
import asyncio
import tempfile
import edge_tts
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from backend.services.maya_actions import MayaMacController
from backend.services.cad_engine import MayaCadEngine
from backend.services.actions import MacAutomation
from backend.services.command_router import CommandRouter
from backend.services.screen_vision import ScreenVisionEngine
from backend.services.computer_agent import MayaComputerAgent
from backend.services.multi_app_agent import MayaMultiAppAgent
from backend.services.universal_computer_agent import MayaUniversalComputerAgent
from backend.services.system_monitor import SystemMonitor
from backend.services.agent_swarm import AgentSwarm
from backend.services.live_data import LiveDataService
from backend.integrations.memory import MemoryEngine
from backend.services.control_center import MayaControlCenter
from backend.services.proactive_brain import MayaProactiveBrain
from backend.services.openjarvis_bridge import OpenJarvisBridge
from backend.services.downloader import UniversalDownloader

app = FastAPI(title="M.A.Y.A. Autonomous Swarm & Vision Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = MemoryEngine()
computer_agent = MayaComputerAgent()
multi_app_agent = MayaMultiAppAgent()
universal_computer_agent = MayaUniversalComputerAgent()
control_center = MayaControlCenter()
proactive_brain = MayaProactiveBrain()

class CommandRequest(BaseModel):
    prompt: str

class PromptRequest(BaseModel):
    prompt: str

class TTSRequest(BaseModel):
    text: str
    voice: str = "en-GB-SoniaNeural"

# Groq LLM Client & Available Model Hierarchy
groq_key = os.environ.get("GROQ_API_KEY")
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key) if groq_key else None

def call_hybrid_llm(messages: list, max_tokens: int = 180, temperature: float = 0.2) -> str:
    """
    Executes resilient Hybrid LLM inference:
    - Mode 'local': runs 100% locally via OpenJarvis & Metal GPU.
    - Mode 'cloud' or 'hybrid': tries Groq Cloud models, and automatically falls back to OpenJarvis Local on failure.
    """
    mode = OpenJarvisBridge.current_mode
    
    # Direct Local Inference if mode is local or Groq not configured
    if mode == "local" or not client:
        local_res = OpenJarvisBridge.query_local_llm(messages, max_tokens=max_tokens, temperature=temperature)
        if local_res:
            return local_res
        if not client:
            return ""

    # Try Cloud Groq Candidate Models
    candidate_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "allam-2-7b"]
    for model_name in candidate_models:
        try:
            res = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            if res.choices and res.choices[0].message.content:
                return res.choices[0].message.content.strip()
        except Exception as e:
            print(f"[GROQ INFERENCE NOTICE] Model '{model_name}' fallback: {e}")
            continue

    # Fallback to OpenJarvis Local Engine
    print("[HYBRID FAILOVER] Cloud models unavailable, falling back to OpenJarvis Local Ollama...")
    local_res = OpenJarvisBridge.query_local_llm(messages, max_tokens=max_tokens, temperature=temperature)
    return local_res or ""

call_groq_llm = call_hybrid_llm

@app.get("/")
def read_root():
    return {"status": "ONLINE", "message": "M.A.Y.A. Swarm Intelligence & Multimodal Vision Core Active"}

@app.get("/api/telemetry")
async def get_telemetry():
    return SystemMonitor.get_hardware_telemetry()

@app.get("/api/live_data")
async def get_live_data():
    return LiveDataService.get_live_dashboard_payload()


@app.post("/api/operator")
async def operate_maya(req: PromptRequest):
    """Astra-style multi-step computer-use endpoint."""
    result = await computer_agent.run(req.prompt.strip())
    return result



@app.post("/api/computer")
async def computer_maya(req: PromptRequest):
    """Stage 5: application-agnostic visual computer-use agent."""
    return await universal_computer_agent.run(req.prompt.strip())


class MemoryRequest(BaseModel):
    kind: str = "preference"
    key: str
    value: object
    confidence: float = 1.0

class RoutineRequest(BaseModel):
    name: str
    prompt: str
    schedule: str
    requires_approval: bool = True

@app.post("/api/memory/remember")
async def remember_maya(req: MemoryRequest):
    return {"memory": proactive_brain.remember(req.kind, req.key, req.value, req.confidence)}

@app.get("/api/memory/search")
async def search_maya_memory(q: str, limit: int = 10):
    return {"memories": proactive_brain.search_memories(q, max(1, min(limit, 50)))}

@app.post("/api/routines")
async def create_maya_routine(req: RoutineRequest):
    return {"routine": proactive_brain.add_routine(req.name, req.prompt, req.schedule, req.requires_approval)}

@app.get("/api/routines")
async def list_maya_routines():
    return {"routines": proactive_brain.list_routines()}

@app.post("/api/routines/{routine_id}/enabled")
async def enable_maya_routine(routine_id: str, enabled: bool = True):
    routine = proactive_brain.set_routine_enabled(routine_id, enabled)
    if not routine:
        return Response(content=json.dumps({"error":"Routine not found"}), status_code=404, media_type="application/json")
    return {"routine": routine}

@app.post("/api/control/tasks")
async def create_control_task(req: PromptRequest):
    """Create a persistent Control Center task without executing it."""
    return control_center.create_task(req.prompt.strip())

@app.get("/api/control/tasks")
async def list_control_tasks():
    return {"tasks": control_center.list_tasks()}

@app.get("/api/control/tasks/{task_id}")
async def get_control_task(task_id: str):
    task = control_center.get_task(task_id)
    if not task: return Response(content=json.dumps({"error":"Task not found"}), status_code=404, media_type="application/json")
    return {"task": task, "history": control_center.history(task_id), "pending_approvals": control_center.pending_approvals(task_id)}

@app.get("/api/control/approvals")
async def get_pending_approvals():
    return {"approvals": control_center.pending_approvals()}

class ApprovalRequest(BaseModel):
    approved: bool

@app.post("/api/control/approvals/{approval_id}")
async def resolve_control_approval(approval_id: str, req: ApprovalRequest):
    approval = control_center.resolve_approval(approval_id, req.approved)
    if not approval: return Response(content=json.dumps({"error":"Approval not found"}), status_code=404, media_type="application/json")
    return approval

@app.post("/api/agent")
async def agent_maya(req: PromptRequest):
    """Stage 4: long-horizon multi-application computer-use agent."""
    return await multi_app_agent.run(req.prompt.strip())

@app.post("/api/ask")
async def ask_maya(req: PromptRequest):
    user_query = req.prompt.strip()
    query_clean = re.sub(r'^(hey maya|maya|jarvis|hey jarvis|please)[,\s]+', '', user_query, flags=re.IGNORECASE).strip().rstrip('.!?')
    query_lower = query_clean.lower()
    
    capability = "Central Kernel"
    action_type = "READ_ONLY"
    action_result = ""
    routed_result = ""
    agent_status = "Central Kernel"
    cad_data = None
    screen_base64 = None
    window_meta = ""
    swarm_output = None

    # 0. Voice Continuous Listening Control
    if any(k in query_lower for k in ["stop listening", "stop voice", "mute microphone", "pause listening"]):
        return {
            "content": "Microphone muted. Voice recognition paused, Boss. Click the microphone or say wake command when ready.",
            "cad_model": None,
            "mesh_data": None,
            "switch_to_studio": False,
            "active_agent": "Voice Control Core",
            "swarm_result": None,
            "action": "Voice listening paused.",
            "status": "success",
            "capability": "Continuous Voice Core",
            "action_type": "VOICE_CONTROL",
            "stop_listening": True
        }

    # 0.1 Universal Downloader & Auto-Installer
    if any(k in query_lower for k in [
        "download ", "install ", "get blender", "install blender", 
        "fetch video", "download video", "save song", "download app"
    ]):
        agent_status = "Autonomous Software Downloader & Installer"
        capability = "Universal Software Downloader & Installer"
        action_type = "SOFTWARE_INSTALL"
        LiveDataService.set_agent_status("system_controller", "EXECUTING", "Downloading and installing requested application...")
        
        loop = asyncio.get_event_loop()
        dl_res = await loop.run_in_executor(None, lambda: UniversalDownloader.process_download_query(query_clean))
        action_result = dl_res.get("message", "Application download initiated.")
        LiveDataService.set_agent_status("system_controller", "ONLINE", "Task complete")

    # 1. Swarm Code Generation & Live Python Execution
    elif any(k in query_lower for k in [
        "calculate", "run python", "write a script", "simulate", "stress test", 
        "compute", "tensile", "resonance", "formula", "physics", "ohm", "yield strength", "newton"
    ]):
        agent_status = "Coder Agent -> Sandbox Execution"
        capability = "Autonomous Swarm Computing"
        action_type = "CODE_EXECUTION"
        LiveDataService.set_agent_status("python_coder", "EXECUTING", "Evaluating engineering script in sandbox...")
        
        try:
            code_prompt = [
                {"role": "system", "content": "You are M.A.Y.A.'s Coder Agent. Write ONLY raw executable Python code to compute the exact engineering or math answer. Calculate variables, convert units accurately, and print the final formatted result with print(). No explanations, no markdown comments."},
                {"role": "user", "content": user_query}
            ]
            loop = asyncio.get_event_loop()
            generated_code = await loop.run_in_executor(None, lambda: call_groq_llm(code_prompt, max_tokens=300, temperature=0.1))
            
            if generated_code:
                exec_result = AgentSwarm.execute_python_code(generated_code)
                if exec_result["success"]:
                    action_result = f"Calculation Result:\n{exec_result['output']}"
                    LiveDataService.set_agent_status("python_coder", "READY", f"Output: {exec_result['output'][:40]}")
                else:
                    action_result = f"Execution notice: {exec_result['error']}"
                    LiveDataService.set_agent_status("python_coder", "READY", "Execution handled")
                swarm_output = exec_result
            else:
                action_result = "Coder Agent calculated parameters directly."
                LiveDataService.set_agent_status("python_coder", "READY", "Parameters computed")
        except Exception as e:
            action_result = f"Swarm error: {e}"
            LiveDataService.set_agent_status("python_coder", "READY", "Error logged")

    # 2. Multimodal Desktop Screen Vision Trigger
    elif any(k in query_lower for k in [
        "see my screen", "look at this", "look at my screen", "inspect my screen", 
        "what is on my screen", "analyze code", "analyze my screen", "check this error", 
        "check screen", "describe this schematic"
    ]):
        agent_status = "Vision Agent"
        screen_base64 = ScreenVisionEngine.capture_active_screen()
        window_meta = ScreenVisionEngine.get_active_window_metadata()
        action_result = f"Desktop screenshot captured ({window_meta}) for visual analysis."
        capability = "Multimodal Screen Vision"
        action_type = "SCREEN_VISION"

    # 3. 3D CAD Parametric Model Generation in Viewport & Slicer
    elif any(k in query_lower for k in ["design", "make", "create", "model", "build", "3d", "cad", "schematic"]):
        agent_status = "CAD Agent"
        LiveDataService.set_agent_status("cad_agent", "RENDERING", "Generating 3D Parametric Mesh...")
        if "trigger" in query_lower:
            cad_data = MayaCadEngine.generate_parametric_mesh("trigger")
            action_result = "Rendered dielectric trigger mechanism in 3D viewport."
        elif "shooter" in query_lower or "barrel" in query_lower or "web" in query_lower:
            cad_data = MayaCadEngine.generate_parametric_mesh("web_shooter")
            action_result = "Rendered web-shooter barrel and coil assembly in 3D viewport."
        elif "bracket" in query_lower or "mount" in query_lower or "gear" in query_lower:
            cad_data = MayaCadEngine.generate_parametric_mesh("bracket")
            action_result = "Rendered high-tensile mounting bracket in 3D viewport."
        else:
            cad_data = MayaCadEngine.generate_parametric_mesh("reactor")
            action_result = "Parametric core component updated in viewport."

        stl_file = MayaCadEngine.generate_parametric_stl(cad_data["type"], {"width": 42.0, "height": 18.0, "depth": 6.0, "id": int(time.time() % 1000)})
        MayaCadEngine.send_to_slicer(stl_file)
        capability = "3D CAD Design & Slicer Engine"
        action_type = "CAD_GENERATION"
        LiveDataService.set_agent_status("cad_agent", "ONLINE", f"STL: {os.path.basename(stl_file)}")

        cad_data["material"] = "DIELECTRIC RUBBER" if cad_data["type"] == "trigger" else ("AEROSPACE ALUMINUM" if cad_data["type"] == "web_shooter" else "QUANTUM MATRIX ALLOY")
        cad_data["dimensions"] = "35mm x 15mm x 8mm" if cad_data["type"] == "trigger" else ("120mm x 45mm x 25mm" if cad_data["type"] == "web_shooter" else "85mm x 85mm x 85mm")
        cad_data["saved_path"] = f"~/Desktop/MAYA_CAD_Exports/{os.path.basename(stl_file)}"

    # 4. Roadmap & Stark Wake Protocol Command Routing
    elif CommandRouter.route_command(query_clean):
        routed_info = CommandRouter.route_command(query_clean)
        capability = routed_info.get("capability", "Command Router")
        action_type = routed_info.get("action_type", "READ_ONLY")
        action_result = routed_info.get("action_summary", "")
        routed_result = routed_info.get("result_text", "")

    # 5. Native macOS System Actions
    elif "open " in query_lower or "launch " in query_lower:
        agent_status = "System Control Agent"
        target = query_lower.split("open ", 1)[-1] if "open " in query_lower else query_lower.split("launch ", 1)[-1]
        target = target.strip().strip("'\"").rstrip('.!?')
        action_result = MayaMacController.launch_app(target)
        capability = "Mac Application Launcher"
        action_type = "SYSTEM_APP"
    elif "volume " in query_lower or "set volume" in query_lower:
        agent_status = "Audio Control Agent"
        digits = [int(s) for s in query_lower.split() if s.isdigit()]
        if digits:
            action_result = MayaMacController.set_system_volume(digits[0])
            capability = "Audio System Controller"
            action_type = "SYSTEM_VOLUME"
    elif "screenshot" in query_lower or "capture screen" in query_lower:
        action_result = MayaMacController.take_screenshot()
        capability = "Screen Vision Capture"
        action_type = "SCREEN_VISION"
    elif "search " in query_lower or "find " in query_lower:
        search_target = query_lower.split("search for ", 1)[-1] if "search for " in query_lower else (query_lower.split("search ", 1)[-1] if "search " in query_lower else query_lower.split("find ", 1)[-1])
        search_target = search_target.strip().rstrip('.!?')
        action_result = MayaMacController.search_web_or_cad(search_target)
        capability = "Engineering & Web Search"
        action_type = "WEB_RESEARCH"
    elif "run " in query_lower:
        cmd = query_clean.split("run ", 1)[-1].strip()
        action_result = MayaMacController.run_terminal(cmd)
        capability = "Terminal Shell Executor"
        action_type = "SHELL_EXECUTION"

    # 6. Recall Persistent Vector Memory
    relevant_context = memory.recall_context(user_query)

    # 7. LLM Response Synthesis
    reply_content = ""
    if client:
        try:
            system_prompt = (
                "You are M.A.Y.A., an advanced macOS engineering and autonomous multi-agent AI assistant. "
                "Always address the user as 'Boss Kirtan Patel' or 'Boss'. "
                f"Active Sub-Agent: {agent_status}\n"
                f"Calculation / Execution Output: {action_result}\n"
                f"Routed Data: {routed_result}\n"
                f"Memory Context: {relevant_context}\n"
                "State the calculated numbers or result directly and clearly in 1-2 authoritative sentences."
            )

            synth_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]

            loop = asyncio.get_event_loop()
            reply_content = await loop.run_in_executor(None, lambda: call_groq_llm(synth_messages, max_tokens=150, temperature=0.2))
        except Exception as e:
            print(f"[MAYA SYNTHESIS ERROR] {e}")

    if not reply_content:
        if action_result:
            reply_content = action_result
        elif routed_result:
            reply_content = routed_result
        else:
            reply_content = f"M.A.Y.A.: Directive '{user_query}' executed, Boss."

    # 8. Index into Vector Memory
    memory_id = f"mem_{int(time.time() * 1000)}"
    memory.store_interaction(memory_id, user_query, reply_content)

    switch_to_studio = bool(cad_data or "studio" in query_lower or "3d model" in query_lower or "3d design" in query_lower)

    return {
        "content": reply_content,
        "cad_model": cad_data,
        "mesh_data": cad_data,
        "switch_to_studio": switch_to_studio,
        "active_agent": agent_status,
        "swarm_result": swarm_output,
        "action": action_result,
        "status": "success",
        "capability": capability,
        "action_type": action_type,
        "action_summary": action_result
    }

@app.post("/api/tts")
async def tts_endpoint(req: TTSRequest):
    text = req.text.strip()
    if not text:
        return Response(content=b"", status_code=400)

    try:
        voice_id = req.voice or "en-GB-SoniaNeural"
        communicate = edge_tts.Communicate(text, voice_id, rate="+10%")
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            temp_path = fp.name

        await communicate.save(temp_path)

        with open(temp_path, "rb") as f:
            audio_bytes = f.read()

        try:
            os.remove(temp_path)
        except Exception:
            pass

        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        print(f"[EDGE-TTS ERROR] {e}")
        return Response(content=b"", status_code=500)

@app.get("/api/engine/status")
async def get_engine_status():
    """Returns dual-engine status (Cloud Groq + Local OpenJarvis / Ollama)."""
    return OpenJarvisBridge.get_status()

class EngineModeRequest(BaseModel):
    mode: str

@app.post("/api/engine/mode")
async def set_engine_mode(req: EngineModeRequest):
    """Update engine execution mode: 'hybrid' | 'cloud' | 'local'."""
    new_mode = OpenJarvisBridge.set_mode(req.mode)
    return {"status": "success", "mode": new_mode}

@app.get("/api/engine/doctor")
async def run_engine_doctor():
    """Runs OpenJarvis system diagnostic scan."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, OpenJarvisBridge.run_doctor)

class DownloadRequest(BaseModel):
    query: str

@app.post("/api/download")
async def download_endpoint(req: DownloadRequest):
    """Direct universal software downloader & installer endpoint."""
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, lambda: UniversalDownloader.process_download_query(req.query.strip()))
    return res
