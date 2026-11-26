"""Stage 5: Universal computer-use layer for Maya.

This layer exposes generic computer primitives and an observe/act loop. It is
application-agnostic: the model decides what to do from the current screen,
while Python only provides safe, deterministic primitives.
"""
import asyncio
import json
import os
import subprocess
import time
from typing import Any, Dict, List

from openai import OpenAI
from .computer_agent import ComputerControl
from .visual_grounding import VisualGroundingEngine
from .screen_vision import ScreenVisionEngine


def _frontmost() -> Dict[str, Any]:
    return ComputerControl._osascript(
        'tell application "System Events" to get name of first application process whose frontmost is true'
    )


def _screen_size() -> Dict[str, Any]:
    script = 'tell application "Finder" to get bounds of window of desktop'
    return ComputerControl._osascript(script)


UNIVERSAL_TOOLS = {
    "open_app": ComputerControl.open_app,
    "click": ComputerControl.click,
    "double_click": ComputerControl.double_click,
    "type_text": ComputerControl.type_text,
    "press_key": ComputerControl.press_key,
    "hotkey": ComputerControl.hotkey,
    "scroll": ComputerControl.scroll,
    "wait": ComputerControl.wait,
    "inspect_screen": ComputerControl.inspect_screen,
    "find_on_screen": lambda description: VisualGroundingEngine().locate(description),
    "get_active_app": _frontmost,
    "get_screen_size": _screen_size,
}

UNIVERSAL_SCHEMA = [
    {"type":"function","function":{"name":"open_app","description":"Open a macOS application by name.","parameters":{"type":"object","properties":{"app_name":{"type":"string"}},"required":["app_name"]}}},
    {"type":"function","function":{"name":"click","description":"Click an exact screen coordinate returned by visual grounding. Never invent coordinates.","parameters":{"type":"object","properties":{"x":{"type":"integer"},"y":{"type":"integer"}},"required":["x","y"]}}},
    {"type":"function","function":{"name":"double_click","description":"Double-click an exact screen coordinate returned by visual grounding.","parameters":{"type":"object","properties":{"x":{"type":"integer"},"y":{"type":"integer"}},"required":["x","y"]}}},
    {"type":"function","function":{"name":"type_text","description":"Type text into the currently focused control.","parameters":{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}}},
    {"type":"function","function":{"name":"press_key","description":"Press a single key such as enter, tab, escape, up, down, left, right.","parameters":{"type":"object","properties":{"key":{"type":"string"}},"required":["key"]}}},
    {"type":"function","function":{"name":"hotkey","description":"Press a keyboard shortcut such as cmd+l or cmd+tab.","parameters":{"type":"object","properties":{"keys":{"type":"array","items":{"type":"string"}}},"required":["keys"]}}},
    {"type":"function","function":{"name":"scroll","description":"Scroll the current application. Positive is up, negative is down.","parameters":{"type":"object","properties":{"amount":{"type":"integer"}},"required":["amount"]}}},
    {"type":"function","function":{"name":"wait","description":"Wait for a UI transition.","parameters":{"type":"object","properties":{"seconds":{"type":"number"}},"required":["seconds"]}}},
    {"type":"function","function":{"name":"inspect_screen","description":"Capture and inspect the current screen/window state. Use after significant UI changes.","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"find_on_screen","description":"Locate a visible UI element from its natural-language description. Returns coordinates only when visual confidence is sufficient.","parameters":{"type":"object","properties":{"description":{"type":"string"}},"required":["description"]}}},
    {"type":"function","function":{"name":"get_active_app","description":"Get the current frontmost application.","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"get_screen_size","description":"Get desktop bounds when coordinate reasoning is necessary.","parameters":{"type":"object","properties":{}}}},
]


class MayaUniversalComputerAgent:
    def __init__(self):
        key = os.getenv("GROQ_API_KEY")
        self.client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key) if key else None
        self.models = [os.getenv("MAYA_AGENT_MODEL", "openai/gpt-oss-120b"), "openai/gpt-oss-20b"]
        self.vg = VisualGroundingEngine()

    def _completion(self, messages):
        if not self.client:
            raise RuntimeError("GROQ_API_KEY is not configured")
        last = None
        for model in self.models:
            try:
                return self.client.chat.completions.create(
                    model=model, messages=messages, temperature=0.05,
                    tools=UNIVERSAL_SCHEMA, tool_choice="auto"
                )
            except Exception as exc:
                last = exc
        raise RuntimeError(str(last) if last else "No model available")

    async def run(self, goal: str, max_steps: int = 40) -> Dict[str, Any]:
        messages = [
            {"role":"system","content":(
                "You are MAYA, a general computer-use operator on macOS. Your job is to finish the user's goal in real software. "
                "You are not a tutorial writer. Plan a small next action, execute it, observe the result, and continue. "
                "For unknown UI positions, use find_on_screen before clicking. Never invent coordinates. After opening an app, "
                "navigation, dialogs, submissions, or major changes, inspect the screen. Maintain the original goal throughout. "
                "If an action fails, diagnose from the new screen and choose another strategy. Do not claim success without evidence. "
                "For destructive, financial, account-changing, message-sending, email-sending, or calling actions, require explicit "
                "user confirmation immediately before the irreversible action unless the user explicitly authorized that exact action. "
                "Keep actions incremental and stop if macOS permissions prevent safe control."
            )},
            {"role":"user","content":goal},
        ]
        trace: List[Dict[str, Any]] = []
        completed: List[str] = []
        failures = 0
        loop = asyncio.get_running_loop()

        for step in range(1, max_steps + 1):
            state = {"step":step,"goal":goal,"completed":completed[-15:],"failures":failures}
            messages.append({"role":"system","content":"TASK STATE: "+json.dumps(state, ensure_ascii=False)})
            response = await loop.run_in_executor(None, lambda: self._completion(messages))
            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                return {"status":"success","content":msg.content or "Task completed.","steps":step-1,"completed":completed,"trace":trace}

            for call in msg.tool_calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments or "{}")
                except Exception:
                    args = {}
                handler = UNIVERSAL_TOOLS.get(name)
                if not handler:
                    result = {"ok":False,"error":f"Unknown tool: {name}"}
                else:
                    try:
                        result = handler(**args)
                    except Exception as exc:
                        result = {"ok":False,"error":str(exc)}
                if not result.get("ok", False):
                    failures += 1
                elif name not in {"inspect_screen","get_active_app","get_screen_size","wait"}:
                    completed.append(f"{name}: {json.dumps(args, ensure_ascii=False)}")
                trace.append({"step":step,"tool":name,"args":args,"result":result})
                messages.append({"role":"tool","tool_call_id":call.id,"name":name,"content":json.dumps(result, ensure_ascii=False)})

                if failures >= 6:
                    return {"status":"blocked","content":"I stopped after repeated failed computer actions. Review the screen/permissions and retry.","steps":step,"completed":completed,"trace":trace}

        return {"status":"partial","content":"I reached the safety limit before verifying completion.","steps":max_steps,"completed":completed,"trace":trace}
