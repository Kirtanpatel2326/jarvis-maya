import os
import re
import ssl
import time
import subprocess
import webbrowser
import urllib.parse
import urllib.request
from pathlib import Path

class MayaMacController:
    """macOS Hardware, CAD, Shell Execution, and App Control Core."""

    @staticmethod
    def execute_applescript(script: str) -> str:
        """Executes native AppleScript on macOS."""
        try:
            p = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = p.communicate()
            return stdout.strip() if stdout else ("Executed successfully." if not stderr else f"Error: {stderr.strip()}")
        except Exception as e:
            return f"AppleScript error: {e}"

    @staticmethod
    def launch_app(app_name: str) -> str:
        """Opens any Mac app (e.g. Blender, OpenSCAD, PrusaSlicer, Terminal, Chrome, VS Code, WhatsApp, FaceTime)."""
        clean_name = app_name.strip().replace('"', '').rstrip('.!?')
        
        # Direct launch attempt
        try:
            subprocess.run(["open", "-a", clean_name], check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            return f"M.A.Y.A.: Launched {clean_name}."
        except Exception:
            pass

        # Search /Applications
        app_dirs = ["/Applications", os.path.expanduser("~/Applications"), "/System/Applications"]
        for d in app_dirs:
            if os.path.exists(d):
                for item in os.listdir(d):
                    if item.endswith(".app") and clean_name.lower() in item.lower():
                        app_path = os.path.join(d, item)
                        try:
                            subprocess.run(["open", app_path], check=True)
                            return f"M.A.Y.A.: Launched {item.replace('.app', '')}."
                        except Exception as e:
                            return f"Could not launch {item}: {e}"

        # Common fallback for CAD/Maker apps
        if "blender" in clean_name.lower():
            return "M.A.Y.A.: Blender is not installed locally. You can install it via 'brew install --cask blender' or use OpenSCAD and PrusaSlicer which are fully active."

        return f"M.A.Y.A.: Application '{clean_name}' not found in /Applications."

    @staticmethod
    def run_terminal(command: str) -> str:
        """Executes a shell command or build script for CAD/microcontroller compilation."""
        try:
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT, timeout=15)
            return output.strip() if output else "Command executed successfully."
        except Exception as e:
            return f"Execution error: {e}"

    @staticmethod
    def take_screenshot() -> str:
        """Takes a desktop screenshot for vision analysis."""
        path = "/tmp/maya_desktop_screen.png"
        try:
            subprocess.run(["screencapture", "-x", path], check=True)
            return f"Desktop captured to {path}."
        except Exception as e:
            return f"Screenshot error: {e}"

    @staticmethod
    def set_system_volume(level: int) -> str:
        """Sets macOS audio volume (0-100)."""
        scaled = max(0, min(100, level))
        vol = int((scaled / 100) * 7)
        return MayaMacController.execute_applescript(f"set volume {vol}")

    @staticmethod
    def search_web_or_cad(query: str) -> str:
        """Searches engineering components, CAD datasheets, or web."""
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Searching for: {query}"
