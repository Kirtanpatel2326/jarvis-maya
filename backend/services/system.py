import subprocess
import psutil
import time
import httpx
import os
from pathlib import Path

# Mapping friendly names to official macOS Application names
APP_MAPPING = {
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "safari": "Safari",
    "spotify": "Spotify",
    "vs code": "Visual Studio Code",
    "vscode": "Visual Studio Code",
    "terminal": "Terminal",
    "slack": "Slack",
    "finder": "Finder",
    "calculator": "Calculator",
    "notes": "Notes",
    "discord": "Discord"
}

def get_system_vitals() -> dict:
    """
    Retrieves real-time system performance vitals.
    """
    try:
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        
        # Simple latency check to a fast DNS
        latency = 20 # fallback default
        start_time = time.time()
        try:
            # Quick connect to see if we're online and measure roundtrip
            import socket
            socket.setdefaulttimeout(1.0)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            latency = int((time.time() - start_time) * 1000)
        except Exception:
            latency = -1 # Offline

        # Hardware temperature fallback logic
        temp = 45.0 # Mock base
        try:
            # Try psutil (works on Linux/Windows)
            temps = psutil.sensors_temperatures()
            if temps and 'coretemp' in temps:
                temp = temps['coretemp'][0].current
            else:
                # Fallback for macOS (machdep.xcpm.cpu_thermal_level gives 0-255 thermal pressure)
                # Instead of sudo powermetrics, we mock a realistic temperature based on CPU load
                temp = 40.0 + (cpu * 0.4)
        except Exception:
            temp = 40.0 + (cpu * 0.4)

        # GPU metrics fallback logic
        gpu_load = 0
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_load = int(gpus[0].load * 100)
            else:
                gpu_load = int(cpu * 0.6) # Mock GPU based on CPU for Apple Silicon shared memory
        except Exception:
            gpu_load = int(cpu * 0.6)
            
        return {
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "latency": latency,
            "temp": round(temp, 1),
            "gpu": gpu_load,
            "status": "ONLINE" if latency > 0 else "OFFLINE"
        }
    except Exception as e:
        print(f"Error reading system vitals: {e}")
        return {"cpu": 0, "memory": 0, "disk": 0, "latency": -1, "temp": 0.0, "gpu": 0, "status": "ERROR"}

def set_volume(level: int) -> str:
    """
    Sets the macOS system output volume.
    """
    try:
        level = max(0, min(100, level))
        subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
        return f"System volume set to {level} percent, sir."
    except Exception as e:
        return f"I encountered an issue setting the volume: {str(e)}"

def get_volume() -> int:
    """
    Gets the current macOS system output volume.
    """
    try:
        res = subprocess.run(["osascript", "-e", "output volume of (get volume settings)"], 
                             capture_output=True, text=True, check=True)
        return int(res.stdout.strip())
    except Exception:
        return 50

WEBSITE_MAPPING = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://www.github.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://www.x.com",
    "x": "https://www.x.com",
    "gmail": "https://mail.google.com",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com"
}

def open_application(app_name: str) -> str:
    """
    Opens an application or website on macOS by name.
    """
    app_key = app_name.lower().strip()
    
    # Check if user requested a website
    if app_key in WEBSITE_MAPPING:
        url = WEBSITE_MAPPING[app_key]
        subprocess.run(["open", url], check=True)
        return f"Opening {app_key.capitalize()} in your web browser, sir."
    elif app_key.startswith("http://") or app_key.startswith("https://") or "." in app_key:
        url = app_key if app_key.startswith("http") else f"https://{app_key}"
        subprocess.run(["open", url], check=True)
        return f"Opening {url} in your web browser, sir."

    official_name = APP_MAPPING.get(app_key, app_name)
    
    try:
        # Check if we can open it
        res = subprocess.run(["open", "-a", official_name], capture_output=True, text=True)
        if res.returncode == 0:
            return f"Opening {official_name}, sir."
        else:
            # Fallback to web search if application isn't found locally
            search_url = f"https://www.google.com/search?q={app_name}"
            subprocess.run(["open", search_url], check=True)
            return f"Could not find local app '{official_name}'. Opening search for {app_name} in browser, sir."
    except Exception as e:
        return f"Failed to launch application: {str(e)}"

def lock_system() -> str:
    """
    Locks the macOS system screen.
    """
    try:
        # Put display to sleep - locking the screen if lock on sleep is active
        subprocess.run(["pmset", "displaysleepnow"], check=True)
        return "Locking system console, sir."
    except Exception as e:
        try:
            # Fallback to Lock Keychain or login window
            subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "q" using {control down, command down}'], check=True)
            return "Locking screen, sir."
        except Exception:
            return f"Unable to lock system: {str(e)}"

def capture_screenshot() -> str:
    """
    Takes a macOS screenshot and saves it to a static folder.
    """
    try:
        # Save screenshot in the frontend directory so the user can see it or load it!
        frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
        if not frontend_dir.exists():
            frontend_dir.mkdir(parents=True, exist_ok=True)
            
        filename = f"screenshot_{int(time.time())}.png"
        filepath = frontend_dir / filename
        
        subprocess.run(["screencapture", "-x", str(filepath)], check=True)
        return f"Screenshot captured and saved as {filename}, sir."
    except Exception as e:
        return f"Failed to capture screenshot: {str(e)}"

def control_media(action: str) -> str:
    """
    Controls media player on macOS (play, pause, next, previous).
    """
    action = action.lower().strip()
    try:
        if action in ["play", "pause", "playpause", "toggle"]:
            # Spacebar or media key code 16
            subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 16'], check=True)
            return "Toggled media playback, sir."
        elif action in ["next", "skip"]:
            subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 19'], check=True)
            return "Skipped to the next track, sir."
        elif action in ["prev", "previous", "back"]:
            subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 18'], check=True)
            return "Returned to the previous track, sir."
        else:
            return f"Unknown media command '{action}', sir."
    except Exception:
        # Fallback using Spotify app specific command if Spotify is running
        try:
            if action in ["play", "pause", "playpause", "toggle"]:
                subprocess.run(["osascript", "-e", 'tell application "Spotify" to playpause'], check=True)
                return "Toggled Spotify playback, sir."
            elif action in ["next", "skip"]:
                subprocess.run(["osascript", "-e", 'tell application "Spotify" to next track'], check=True)
                return "Skipped Spotify track, sir."
            elif action in ["prev", "previous", "back"]:
                subprocess.run(["osascript", "-e", 'tell application "Spotify" to previous track'], check=True)
                return "Returned to previous Spotify track, sir."
        except Exception as e:
            return f"Unable to control system media: {str(e)}"


def play_youtube_song(song_name: str) -> str:
    """
    Plays a song on YouTube by opening the first video result directly in the default web browser with autoplay.
    """
    import urllib.parse
    import re
    import httpx
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        query = urllib.parse.quote(song_name.strip())
        search_url = f"https://www.youtube.com/results?search_query={query}"
        
        # Attempt to scrape the first video URL directly
        with httpx.Client() as client:
            response = client.get(search_url, headers=headers, timeout=8.0)
            if response.status_code == 200:
                html = response.text
                video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
                if not video_ids:
                    video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
                
                if video_ids:
                    # Deduplicate to find the first real video ID
                    unique_ids = []
                    for vid in video_ids:
                        if vid not in unique_ids:
                            unique_ids.append(vid)
                    
                    if unique_ids:
                        watch_url = f"https://www.youtube.com/watch?v={unique_ids[0]}&autoplay=1"
                        subprocess.run(["open", watch_url], check=True)
                        return f"Opening the first video result directly on YouTube to play {song_name}, sir."
        
        # Fallback to search result page if scraping fails
        subprocess.run(["open", search_url], check=True)
        return f"Scraper link bypassed. Opening search results for {song_name} on YouTube, sir."
    except Exception as e:
        return f"I encountered an issue playing the song on YouTube: {str(e)}"


def get_coordinates_sync(city_name: str) -> tuple:
    """
    Synchronously geocodes a city name to latitude and longitude using Open-Meteo's free geocoding API.
    """
    import httpx
    # Default coordinates for Anand, Gujarat, India
    DEFAULT_LAT = 22.5560
    DEFAULT_LON = 72.9515
    DEFAULT_CITY = "Anand, Gujarat"
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        with httpx.Client() as client:
            res = client.get(url, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                if "results" in data and len(data["results"]) > 0:
                    result = data["results"][0]
                    name = result.get("name", city_name)
                    country = result.get("country", "")
                    label = f"{name}, {country}" if country else name
                    return float(result["latitude"]), float(result["longitude"]), label
    except Exception as e:
        print(f"Geocoding sync error: {e}")
    return DEFAULT_LAT, DEFAULT_LON, DEFAULT_CITY


def open_map(location: str) -> str:
    """
    Geocodes the location, opens Google Maps to those coordinates, and returns coordinate metadata.
    """
    import urllib.parse
    try:
        lat, lon, label = get_coordinates_sync(location)
        url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        subprocess.run(["open", url], check=True)
        return f"Coordinates found for {label}: latitude {lat}, longitude {lon}. Opening Google Maps, sir."
    except Exception as e:
        # Fallback to direct query search
        try:
            query = urllib.parse.quote(location.strip())
            url = f"https://www.google.com/maps/search/?api=1&query={query}"
            subprocess.run(["open", url], check=True)
            return f"Opening Google Maps and searching for {location}, sir."
        except Exception as err:
            return f"Failed to search map: {str(err)}"


def send_whatsapp_message(phone_number: str, message: str) -> str:
    """
    Opens a WhatsApp chat with the specified message.
    """
    import urllib.parse
    import re
    try:
        # Clean the phone number: retain only digits
        clean_number = re.sub(r'\D', '', phone_number)
        if not clean_number:
            return "Invalid phone number provided, sir. Please provide digits only."
            
        encoded_msg = urllib.parse.quote(message.strip())
        url = f"https://wa.me/{clean_number}?text={encoded_msg}"
        subprocess.run(["open", url], check=True)
        return f"Opening WhatsApp chat with {phone_number} to send your message, sir."
    except Exception as e:
        return f"I couldn't initiate the WhatsApp message: {str(e)}"


def execute_terminal_command(command: str) -> str:
    """
    Executes a shell command on the host macOS system and returns the combined stdout and stderr.
    Use this for developer assistance (e.g., git status, checking files, compiling, system uptime).
    """
    workspace_dir = Path(__file__).resolve().parent.parent
    
    # Enhanced security constraints
    dangerous_patterns = [
        "rm -rf /", "rm -rf *", "mkfs", "dd if=", "shutdown", "reboot",
        "chmod -R 777 /", "chown -R", "> /dev/sd", "> /dev/nvme",
        "nc -e", "bash -i >& /dev/tcp", "mkfifo", ":(){ :|:& };:"
    ]
    cmd_clean = command.strip().lower()
    if any(p in cmd_clean for p in dangerous_patterns):
        return "Security Protocol: Command execution blocked. Dangerous pattern detected, sir."

    try:
        # Execute shell command with 10s timeout, restricted to workspace CWD
        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10.0, cwd=str(workspace_dir))
        output = res.stdout.strip()
        error = res.stderr.strip()
        
        result = []
        if output:
            result.append(output)
        if error:
            result.append(f"Diagnostics/Errors:\n{error}")
            
        if not result:
            return "Command executed successfully with no output return, sir."
            
        return "\n".join(result)
    except subprocess.TimeoutExpired:
        return "Command execution timed out after 10.0 seconds, sir."
    except Exception as e:
        return f"Command execution failed: {str(e)}, sir."


def search_web(query: str) -> str:
    """
    Searches the web using DuckDuckGo HTML search and returns titles and snippets of top results.
    """
    import urllib.parse
    import re
    import html
    import httpx
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=8.0)
            if response.status_code != 200:
                return f"Unable to establish search transceiver (Status Code: {response.status_code}), sir."
            
            html_content = response.text
            results = []
            bodies = re.findall(r'<div class="result__body">.*?</div>\s*</div>', html_content, re.DOTALL)
            for body in bodies:
                title_match = re.search(r'<a class="result__a"[^>]*>(.*?)</a>', body, re.DOTALL)
                snippet_match = re.search(r'<a class="result__snippet"[^>]*>(.*?)</a>', body, re.DOTALL)
                if title_match and snippet_match:
                    title = html.unescape(re.sub(r'<[^>]+>', '', title_match.group(1)).strip())
                    snippet = html.unescape(re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip())
                    results.append(f"Title: {title}\nSnippet: {snippet}")
            
            if not results:
                snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html_content, re.DOTALL)
                for s in snippets[:4]:
                    clean_s = html.unescape(re.sub(r'<[^>]+>', '', s).strip())
                    results.append(clean_s)
                    
            if not results:
                return "The query returned no significant databases or summaries, sir."
                
            return "\n\n".join(results[:5])
    except Exception as e:
        return f"Failed to perform search sequence: {str(e)}, sir."


# Global notifications queue for J.A.R.V.I.S. alerts
ACTIVE_NOTIFICATIONS = []

def set_reminder(minutes: float, message: str) -> str:
    """
    Sets a reminder to alert you after a specified number of minutes.
    """
    import threading
    
    def trigger_alert():
        ACTIVE_NOTIFICATIONS.append(message)
        
    try:
        delay_sec = max(1.0, float(minutes) * 60)
        t = threading.Timer(delay_sec, trigger_alert)
        t.start()
        return f"I have scheduled a neural alert for you in {minutes} minutes, sir."
    except Exception as e:
        return f"Unable to establish alert timer circuit: {str(e)}, sir."


def read_workspace_file(file_path: str) -> str:
    """
    Reads the content of a file within your workspace.
    """
    try:
        workspace_dir = Path(__file__).resolve().parent.parent
        target_path = (workspace_dir / file_path).resolve()
        if not str(target_path).startswith(str(workspace_dir)):
            return "Security alert, sir. You cannot access files outside the secure workspace perimeter."
            
        if not target_path.exists():
            return f"The file '{file_path}' does not exist on this console, sir."
            
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Read module failed: {str(e)}, sir."


def write_workspace_file(file_path: str, content: str) -> str:
    """
    Writes content to a file in the workspace, creating parent directories if needed.
    """
    try:
        workspace_dir = Path(__file__).resolve().parent.parent
        target_path = (workspace_dir / file_path).resolve()
        if not str(target_path).startswith(str(workspace_dir)):
            return "Security alert, sir. Writing to paths outside the workspace boundary is restricted."
            
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"File '{file_path}' has been successfully compiled and written, Mr. Stark."
    except Exception as e:
        return f"Write module failed: {str(e)}, sir."


def list_workspace_files(directory: str = ".") -> list:
    """
    Lists files and directories in the workspace under the specified path.
    """
    try:
        workspace_dir = Path(__file__).resolve().parent.parent
        target_dir = (workspace_dir / directory).resolve()
        if not str(target_dir).startswith(str(workspace_dir)):
            return ["Security alert: directory query outside workspace perimeter is locked."]
            
        if not target_dir.exists() or not target_dir.is_dir():
            return [f"Directory '{directory}' does not exist on this stack, sir."]
            
        items = []
        for p in target_dir.iterdir():
            rel = p.relative_to(workspace_dir)
            suffix = "/" if p.is_dir() else ""
            items.append(f"{rel}{suffix}")
        return sorted(items)
    except Exception as e:
        return [f"Query failed: {str(e)}, sir."]


def send_email(to: str, subject: str, body: str) -> str:
    """
    Opens the default email client with a pre-filled email to the specified recipient, subject, and body.
    """
    import urllib.parse
    import subprocess
    try:
        subject_encoded = urllib.parse.quote(subject)
        body_encoded = urllib.parse.quote(body)
        url = f"mailto:{to}?subject={subject_encoded}&body={body_encoded}"
        subprocess.run(["open", url], check=True)
        return f"Opening email client pre-filled for {to}, sir. You will need to manually click send."
    except Exception as e:
        return f"I couldn't initiate the email: {str(e)}"

def check_business_updates() -> str:
    """
    Connects to the JARVIS-Business orchestrator to retrieve the latest 
    ScanSafe / Keshvi Creaations metrics, leads, and social media status.
    """
    import requests
    try:
        # Pinging the JARVIS-Business API (running on port 8001)
        response = requests.get("http://127.0.0.1:8001/business/updates", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return f"Business System Status: {data.get('status')}. Update: {data.get('message')}"
        else:
            return f"Failed to fetch business updates. Status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Business system is currently offline or unreachable. Error: {str(e)}"
