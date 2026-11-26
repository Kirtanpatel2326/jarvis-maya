import asyncio
import json
import os
import subprocess
import time
from typing import Any, Dict, List

from openai import OpenAI
from backend.services.actions import MacAutomation
from backend.services.screen_vision import ScreenVisionEngine
from backend.services.visual_grounding import VisualGroundingEngine


class ComputerControl:
    """Small, composable macOS control primitives for agentic workflows."""

    @staticmethod
    def _osascript(script: str) -> Dict[str, Any]:
        try:
            proc = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=20,
            )
            if proc.returncode != 0:
                return {"ok": False, "error": proc.stderr.strip() or "AppleScript failed"}
            return {"ok": True, "output": proc.stdout.strip()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    @classmethod
    def open_app(cls, app_name: str) -> Dict[str, Any]:
        result = MacAutomation.open_application(app_name)
        return {"ok": "Could not" not in result and "not found" not in result.lower(), "result": result}

    @classmethod
    def click(cls, x: int, y: int) -> Dict[str, Any]:
        # System Events click works without adding a Python GUI dependency.
        script = f'tell application "System Events" to click at {{{int(x)}, {int(y)}}}'
        return cls._osascript(script)

    @classmethod
    def double_click(cls, x: int, y: int) -> Dict[str, Any]:
        # Two controlled clicks are more portable than relying on UI scripting verbs.
        first = cls.click(x, y)
        time.sleep(0.12)
        second = cls.click(x, y)
        return {"ok": bool(first.get("ok") and second.get("ok")), "first": first, "second": second}

    @classmethod
    def type_text(cls, text: str) -> Dict[str, Any]:
        # Pass text as argv to avoid interpolation/escaping bugs in AppleScript.
        script = '''on run argv
set t to item 1 of argv
tell application "System Events" to keystroke t
end run'''
        try:
            proc = subprocess.run(
                ["osascript", "-e", script, text],
                capture_output=True,
                text=True,
                timeout=20,
            )
            if proc.returncode != 0:
                return {"ok": False, "error": proc.stderr.strip()}
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    @classmethod
    def press_key(cls, key: str) -> Dict[str, Any]:
        key = key.lower().strip()
        special = {
            "enter": 36,
            "return": 36,
            "tab": 48,
            "escape": 53,
            "esc": 53,
            "space": 49,
            "backspace": 51,
            "delete": 51,
            "up": 126,
            "down": 125,
            "left": 123,
            "right": 124,
        }
        if key in special:
            return cls._osascript(f'tell application "System Events" to key code {special[key]}')
        if len(key) == 1:
            return cls._osascript(f'tell application "System Events" to keystroke "{key}"')
        return {"ok": False, "error": f"Unsupported key: {key}"}

    @classmethod
    def hotkey(cls, keys: List[str]) -> Dict[str, Any]:
        modifiers = []
        base = None
        mod_map = {
            "cmd": "command down",
            "command": "command down",
            "ctrl": "control down",
            "control": "control down",
            "alt": "option down",
            "option": "option down",
            "shift": "shift down",
        }
        for key in keys:
            k = key.lower().strip()
            if k in mod_map:
                modifiers.append(mod_map[k])
            else:
                base = k
        if not base:
            return {"ok": False, "error": "Hotkey needs a non-modifier key"}
        using = " using {" + ", ".join(modifiers) + "}" if modifiers else ""
        if len(base) == 1:
            return cls._osascript(f'tell application "System Events" to keystroke "{base}"{using}')
        return {"ok": False, "error": f"Unsupported hotkey base key: {base}"}

    @classmethod
    def scroll(cls, amount: int) -> Dict[str, Any]:
        # Positive = up, negative = down.
        return cls._osascript(f'tell application "System Events" to scroll area 1 by {int(amount)}')

    @staticmethod
    def wait(seconds: float) -> Dict[str, Any]:
        time.sleep(max(0.0, min(float(seconds), 8.0)))
        return {"ok": True}

    @staticmethod
    def inspect_screen() -> Dict[str, Any]:
        image_b64 = ScreenVisionEngine.capture_active_screen()
        meta = ScreenVisionEngine.get_active_window_metadata()
        return {
            "ok": image_b64 is not None,
            "metadata": meta,
            "screenshot_available": image_b64 is not None,
        }

    @staticmethod
    def send_whatsapp(contact: str, message: str) -> Dict[str, Any]:
        return {"ok": True, "result": MacAutomation.send_whatsapp_message(contact, message)}

    @staticmethod
    def play_youtube(query: str) -> Dict[str, Any]:
        return {"ok": True, "result": MacAutomation.play_youtube(query)}

    @staticmethod
    def web_search(query: str) -> Dict[str, Any]:
        return {"ok": True, "result": MacAutomation.search_web(query)}


TOOLS = {
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
    "send_whatsapp": ComputerControl.send_whatsapp,
    "play_youtube": ComputerControl.play_youtube,
    "web_search": ComputerControl.web_search,
}

TOOL_SCHEMA = [
    {"type": "function", "function": {"name": "open_app", "description": "Open an installed macOS application.", "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]}}},
    {"type": "function", "function": {"name": "click", "description": "Click a screen coordinate.", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]}}},
    {"type": "function", "function": {"name": "double_click", "description": "Double-click a screen coordinate.", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]}}},
    {"type": "function", "function": {"name": "type_text", "description": "Type text into the currently focused field.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "press_key", "description": "Press one key such as enter, tab, escape, up, down, left, right.", "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}}},
    {"type": "function", "function": {"name": "hotkey", "description": "Press a keyboard shortcut, e.g. [cmd,l].", "parameters": {"type": "object", "properties": {"keys": {"type": "array", "items": {"type": "string"}}}, "required": ["keys"]}}},
    {"type": "function", "function": {"name": "scroll", "description": "Scroll the current UI. Positive is up, negative is down.", "parameters": {"type": "object", "properties": {"amount": {"type": "integer"}}, "required": ["amount"]}}},
    {"type": "function", "function": {"name": "wait", "description": "Wait briefly for a UI transition.", "parameters": {"type": "object", "properties": {"seconds": {"type": "number"}}, "required": ["seconds"]}}},
    {"type": "function", "function": {"name": "inspect_screen", "description": "Inspect the active app/window and capture a screenshot for verification.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "find_on_screen", "description": "Use visual AI to locate a visible UI element by description. Returns screen coordinates only when confidence is sufficient.", "parameters": {"type": "object", "properties": {"description": {"type": "string"}}, "required": ["description"]}}},
    {"type": "function", "function": {"name": "send_whatsapp", "description": "Send a WhatsApp message to a contact or number.", "parameters": {"type": "object", "properties": {"contact": {"type": "string"}, "message": {"type": "string"}}, "required": ["contact", "message"]}}},
    {"type": "function", "function": {"name": "play_youtube", "description": "Find and play a YouTube video for a query.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "web_search", "description": "Open a web search for a query.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
]


class MayaComputerAgent:
    """Tool-using operator loop: understand -> act -> observe -> continue -> finish."""

    def __init__(self):
        self.visual_grounding = VisualGroundingEngine()
        key = os.environ.get("GROQ_API_KEY")
        self.client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key) if key else None
        self.models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]

    def _completion(self, messages: List[Dict[str, Any]], tools=True):
        if not self.client:
            raise RuntimeError("GROQ_API_KEY is not configured")
        last_error = None
        for model in self.models:
            try:
                kwargs = dict(model=model, messages=messages, temperature=0.1)
                if tools:
                    kwargs.update(tools=TOOL_SCHEMA, tool_choice="auto")
                return self.client.chat.completions.create(**kwargs)
            except Exception as exc:
                last_error = exc
        raise RuntimeError(str(last_error) if last_error else "No model available")

    async def run(self, goal: str, max_steps: int = 12) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are M.A.Y.A. Computer Agent on macOS. Fulfill the user's goal by calling tools, not by merely explaining steps. "
                    "Work incrementally. After opening an app or changing the UI, inspect the screen. When you need to interact with an element whose coordinates are unknown, call find_on_screen with a precise description, then click the returned coordinates. Never invent coordinates. Verify important actions with another inspection. "
                    "Prefer dedicated tools (send_whatsapp, play_youtube, web_search) when they directly match the goal; otherwise use primitive keyboard/mouse tools. "
                    "Never claim success unless the tool results support it. If blocked by permissions or missing apps, state exactly what blocked you."
                ),
            },
            {"role": "user", "content": goal},
        ]
        trace: List[Dict[str, Any]] = []
        loop = asyncio.get_running_loop()

        for step in range(1, max_steps + 1):
            response = await loop.run_in_executor(None, lambda: self._completion(messages, tools=True))
            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                return {
                    "status": "success",
                    "content": msg.content or "Task completed.",
                    "steps": step - 1,
                    "trace": trace,
                }

            for call in msg.tool_calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                handler = TOOLS.get(name)
                if not handler:
                    result = {"ok": False, "error": f"Unknown tool: {name}"}
                else:
                    try:
                        result = handler(**args)
                    except Exception as exc:
                        result = {"ok": False, "error": str(exc)}

                trace.append({"step": step, "tool": name, "args": args, "result": result})
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        return {
            "status": "partial",
            "content": f"I reached the {max_steps}-step safety limit before I could verify completion.",
            "steps": max_steps,
            "trace": trace,
        }
