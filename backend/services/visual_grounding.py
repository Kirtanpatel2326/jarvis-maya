"""Visual grounding for MAYA's macOS computer-use agent.

The model receives the current screenshot and returns a structured target/coordinate.
Coordinates are normalized so Retina/non-Retina displays can be handled safely.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

SCREEN_PATH = "/tmp/maya_visual_grounding.jpg"


class VisualGroundingEngine:
    def __init__(self) -> None:
        self.provider = os.getenv("MAYA_VISION_PROVIDER", "groq").lower()
        self.model = os.getenv("MAYA_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        self.client = None
        if OpenAI:
            if self.provider == "openai":
                key = os.getenv("OPENAI_API_KEY")
                if key:
                    self.client = OpenAI(api_key=key)
            else:
                key = os.getenv("GROQ_API_KEY")
                if key:
                    self.client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key)

    @staticmethod
    def capture() -> Optional[Path]:
        try:
            subprocess.run(["screencapture", "-x", "-t", "jpg", SCREEN_PATH], check=True, timeout=10)
            path = Path(SCREEN_PATH)
            return path if path.exists() else None
        except Exception as exc:
            print(f"[VISUAL GROUNDING] capture failed: {exc}")
            return None

    @staticmethod
    def _screen_logical_size() -> tuple[int, int]:
        # Prefer Quartz when installed; fall back to Finder desktop bounds.
        try:
            import Quartz  # type: ignore
            bounds = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
            return int(bounds.size.width), int(bounds.size.height)
        except Exception:
            script = 'tell application "Finder" to get bounds of window of desktop'
            try:
                out = subprocess.check_output(["osascript", "-e", script], text=True, timeout=5).strip()
                nums = [int(x) for x in re.findall(r"-?\d+", out)]
                if len(nums) >= 4:
                    return nums[2] - nums[0], nums[3] - nums[1]
            except Exception:
                pass
        return 1440, 900

    @staticmethod
    def _image_data_url(path: Path) -> str:
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/jpeg;base64,{data}"

    def locate(self, description: str) -> Dict[str, Any]:
        path = self.capture()
        if not path:
            return {"ok": False, "error": "Could not capture the screen."}
        if not self.client:
            return {"ok": False, "error": "Vision provider is not configured."}

        prompt = f"""You are MAYA's GUI visual-grounding module on macOS.
Look at the screenshot and locate the UI element described below.
Description: {description}

Return ONLY valid JSON in this exact shape:
{{"found": true, "x": 0.0, "y": 0.0, "confidence": 0.0, "label": "short label"}}

x and y MUST be normalized from 0.0 to 1.0 relative to the full screenshot.
Choose the center of the clickable/input element, not nearby text.
If it is not visible, return {{"found": false, "x": 0, "y": 0, "confidence": 0, "label": "not visible"}}.
Do not guess when confidence would be below 0.55."""

        try:
            image_url = self._image_data_url(path)
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                max_tokens=220,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }],
            )
            raw = response.choices[0].message.content or ""
            match = re.search(r"\{.*\}", raw, re.S)
            if not match:
                return {"ok": False, "error": "Vision model returned non-JSON output.", "raw": raw[:500]}
            result = json.loads(match.group(0))
            if not result.get("found"):
                return {"ok": False, "found": False, "label": result.get("label", "not visible")}

            x = max(0.0, min(1.0, float(result["x"])))
            y = max(0.0, min(1.0, float(result["y"])))
            width, height = self._screen_logical_size()
            result.update({
                "ok": True,
                "x": round(x * width),
                "y": round(y * height),
                "normalized_x": x,
                "normalized_y": y,
                "screen_width": width,
                "screen_height": height,
            })
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
