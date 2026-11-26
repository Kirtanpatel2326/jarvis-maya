import os
import base64
import subprocess
from typing import Optional, Dict, Any

SCREENSHOT_PATH = "/tmp/maya_desktop_capture.jpg"

class ScreenVisionEngine:
    @staticmethod
    def capture_active_screen() -> Optional[str]:
        """Captures the active macOS desktop and converts it to a base64 JPEG string."""
        try:
            # Native macOS screencapture utility (quiet mode, compressed JPEG)
            subprocess.run(["screencapture", "-x", "-t", "jpg", SCREENSHOT_PATH], check=True)
            
            if os.path.exists(SCREENSHOT_PATH):
                with open(SCREENSHOT_PATH, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"[VISION ERROR] Screencapture failed: {e}")
        return None

    @staticmethod
    def get_active_window_metadata() -> str:
        """Extracts frontmost macOS window and active browser tab information via AppleScript."""
        script = """
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            set windowTitle to ""
            try
                set windowTitle to name of front window of first application process whose frontmost is true
            end try
        end tell
        
        set extraInfo to ""
        if frontApp is "Google Chrome" then
            tell application "Google Chrome"
                try
                    set currentTab to active tab of front window
                    set extraInfo to " [Chrome Tab: '" & (title of currentTab) & "']"
                end try
            end tell
        else if frontApp is "Safari" then
            tell application "Safari"
                try
                    set currentTab to current tab of front window
                    set extraInfo to " [Safari Tab: '" & (name of currentTab) & "']"
                end try
            end tell
        end if
        
        return "Active App: " & frontApp & ", Window: '" & windowTitle & "'" & extraInfo
        """
        try:
            p = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, _ = p.communicate()
            return stdout.strip() if stdout else "Active Desktop Screen"
        except Exception as e:
            return f"Active Desktop Screen (Error: {e})"
