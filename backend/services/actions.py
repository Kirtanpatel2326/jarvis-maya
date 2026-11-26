import os
import subprocess
import webbrowser

class MacAutomation:
    @staticmethod
    def open_application(app_name: str) -> str:
        """Opens native Mac apps (e.g., Safari, Terminal, Spotify, VS Code)."""
        clean_app = app_name.strip().replace('"', '')
        try:
            subprocess.run(["open", "-a", clean_app], check=True)
            return f"Successfully opened {clean_app}."
        except Exception as e:
            return f"Failed to open application: {e}"

    @staticmethod
    def run_applescript(script: str) -> str:
        """Executes AppleScript commands (e.g., control volume, media playback)."""
        try:
            p = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = p.communicate()
            return stdout.strip() if stdout else ("Executed." if not stderr else f"Error: {stderr.strip()}")
        except Exception as e:
            return f"AppleScript error: {e}"

    @staticmethod
    def adjust_volume(level: int) -> str:
        """Sets Mac system volume from 0 to 100%."""
        scaled = max(0, min(100, level))
        # AppleScript volume scale is 0 to 7
        as_vol = int((scaled / 100) * 7)
        return MacAutomation.run_applescript(f"set volume {as_vol}")

    @staticmethod
    def search_web(query: str) -> str:
        """Opens a search in your default web browser."""
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching the web for: {query}"
