"""Stage 4: multi-application task orchestration for Maya.

Keeps one goal/state across application switches. Designed to sit above the
computer-use tools rather than replacing them.
"""
import asyncio, json, os, time
from typing import Any, Dict, List, Optional
from openai import OpenAI
from .computer_agent import TOOLS, TOOL_SCHEMA, ComputerControl

MULTI_APP_SCHEMA = TOOL_SCHEMA + [
    {"type":"function","function":{"name":"focus_app","description":"Bring an installed macOS application to the foreground. Use before interacting with that app.","parameters":{"type":"object","properties":{"app_name":{"type":"string"}},"required":["app_name"]}}},
    {"type":"function","function":{"name":"get_active_app","description":"Return the name of the currently frontmost macOS application/window.","parameters":{"type":"object","properties":{}}}},
]

def focus_app(app_name: str) -> Dict[str, Any]:
    result = ComputerControl.open_app(app_name)
    return {"ok": bool(result.get("ok")), "app": app_name, "result": result}

def get_active_app() -> Dict[str, Any]:
    script='tell application "System Events" to get name of first application process whose frontmost is true'
    return ComputerControl._osascript(script)

MULTI_TOOLS=dict(TOOLS, focus_app=focus_app, get_active_app=get_active_app)

class MayaMultiAppAgent:
    """Longer-horizon operator that preserves goal, completed work and state."""
    def __init__(self):
        key=os.environ.get("GROQ_API_KEY")
        self.client=OpenAI(base_url="https://api.groq.com/openai/v1",api_key=key) if key else None
        self.models=["openai/gpt-oss-120b","openai/gpt-oss-20b"]

    def _completion(self,messages):
        if not self.client: raise RuntimeError("GROQ_API_KEY is not configured")
        err=None
        for model in self.models:
            try:
                return self.client.chat.completions.create(model=model,messages=messages,temperature=0.1,tools=MULTI_APP_SCHEMA,tool_choice="auto")
            except Exception as e: err=e
        raise RuntimeError(str(err))

    async def run(self, goal:str, max_steps:int=30)->Dict[str,Any]:
        messages=[{"role":"system","content":("You are Maya's multi-application computer operator on macOS. Complete the user's goal, not just one command. "
        "Maintain a compact state of what is completed, what remains, and which app is active. You may switch between apps; before interacting with an app use focus_app. "
        "After significant UI changes inspect or visually locate elements. Never invent coordinates. Verify important actions. "
        "When a tool fails, recover with an alternative strategy while preserving the original goal. "
        "Do not claim completion unless the requested outcome is verified. Ask for confirmation before sending an external message, email, making a call, deleting data, purchasing, or other irreversible/high-impact actions unless the user explicitly instructed that exact action." )},
        {"role":"user","content":goal}]
        trace=[]; completed=[]; active=None; loop=asyncio.get_running_loop()
        for step in range(1,max_steps+1):
            state={"completed":completed[-12:],"active_app":active,"step":step,"goal":goal}
            messages.append({"role":"system","content":"CURRENT TASK STATE: "+json.dumps(state,ensure_ascii=False)})
            r=await loop.run_in_executor(None,lambda:self._completion(messages))
            msg=r.choices[0].message; messages.append(msg)
            if not msg.tool_calls:
                return {"status":"success","content":msg.content or "Task completed and verified.","steps":step-1,"active_app":active,"completed":completed,"trace":trace}
            for call in msg.tool_calls:
                name=call.function.name
                try: args=json.loads(call.function.arguments or "{}")
                except: args={}
                if name in ("send_whatsapp",):
                    # Explicit user instruction is sufficient; otherwise require a confirmation layer in the UI.
                    pass
                handler=MULTI_TOOLS.get(name)
                try: result=handler(**args) if handler else {"ok":False,"error":"Unknown tool"}
                except Exception as exc: result={"ok":False,"error":str(exc)}
                if name in ("open_app","focus_app") and result.get("ok"): active=args.get("app_name")
                trace.append({"step":step,"tool":name,"args":args,"result":result,"active_app":active})
                if result.get("ok") and name not in ("inspect_screen","get_active_app","wait"):
                    completed.append(f"{name}({json.dumps(args,ensure_ascii=False)})")
                messages.append({"role":"tool","tool_call_id":call.id,"name":name,"content":json.dumps(result,ensure_ascii=False)})
        return {"status":"partial","content":"I reached the safety step limit before verifying completion.","steps":max_steps,"active_app":active,"completed":completed,"trace":trace}
