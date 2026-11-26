import os
import json
import subprocess
import webbrowser
from typing import Dict, Any

# Tool 1: Real-time Weather Fetcher
def get_current_weather(location: str) -> str:
    """Simulated or API-backed live weather report."""
    return json.dumps({
        "location": location,
        "temperature": "29°C",
        "condition": "Partly Cloudy",
        "humidity": "68%"
    })

# Tool 2: Open Web URL / Search (YouTube, Google, etc.)
def open_url(url_or_query: str) -> str:
    """Opens a website or performs a browser search on macOS."""
    target = url_or_query.strip()
    if not target.startswith("http://") and not target.startswith("https://"):
        if "youtube" in target.lower():
            target = f"https://www.youtube.com/results?search_query={target.replace(' ', '+')}"
        elif "." in target and " " not in target:
            target = f"https://{target}"
        else:
            target = f"https://www.google.com/search?q={target.replace(' ', '+')}"
    
    try:
        subprocess.Popen(["open", target])
        return json.dumps({"status": "opened", "target": target})
    except Exception as e:
        return json.dumps({"error": str(e)})

# Tool 3: Open macOS Applications (Finder, Safari, Chrome, Terminal, Calculator, etc.)
def open_mac_app(app_name: str) -> str:
    """Opens any application on macOS by name."""
    try:
        subprocess.Popen(["open", "-a", app_name])
        return json.dumps({"status": "opened_app", "app": app_name})
    except Exception as e:
        return json.dumps({"error": str(e)})

# Tool 4: Local System Command Runner (Whitelisted CLI)
def execute_system_command(command: str) -> str:
    """Executes safe diagnostic terminal commands."""
    allowed_prefixes = ["uptime", "whoami", "df -h", "date", "sw_vers", "ls", "pwd"]
    if not any(command.strip().startswith(prefix) for prefix in allowed_prefixes):
        return json.dumps({"error": f"Command '{command}' rejected by safety policy."})
    
    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
        return json.dumps({"output": output.strip()})
    except Exception as e:
        return json.dumps({"error": str(e)})

# Registry mapping tool names to functions
TOOL_REGISTRY = {
    "get_current_weather": get_current_weather,
    "open_url": open_url,
    "open_mac_app": open_mac_app,
    "execute_system_command": execute_system_command
}

# OpenAI/Groq Tool Declarations
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current weather conditions for a specified city or location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name, e.g., 'Anand, India'"}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a website URL or YouTube video/search query in the default web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url_or_query": {"type": "string", "description": "URL (e.g. 'https://youtube.com') or search topic (e.g. 'YouTube iron man theme')"}
                },
                "required": ["url_or_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_mac_app",
            "description": "Launch any application installed on macOS (e.g., 'Safari', 'Google Chrome', 'Finder', 'Terminal', 'Calculator', 'Notes', 'Spotify').",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the macOS app to open"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_system_command",
            "description": "Execute a whitelisted diagnostic command on the host OS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Safe CLI command: uptime, whoami, df -h, date, ls, pwd"}
                },
                "required": ["command"]
            }
        }
    }
]
