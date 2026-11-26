import os
import urllib.request
import urllib.parse
import json
import subprocess
import time

# Ensure local traffic bypasses any sandbox proxies
os.environ["no_proxy"] = "127.0.0.1,localhost,::1"


def send_notification(title, message):
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script])
    except Exception as e:
        print(f"Failed to send notification: {e}")

def play_audio_or_say(text):
    # Try to fetch TTS from JARVIS
    try:
        encoded_text = urllib.parse.quote(text)
        tts_url = f"http://127.0.0.1:8000/tts?text={encoded_text}"
        req = urllib.request.Request(tts_url)
        
        # Download the audio file
        audio_path = "/tmp/jarvis_greeting.mp3"
        with urllib.request.urlopen(req, timeout=10) as response:
            with open(audio_path, 'wb') as f:
                f.write(response.read())
                
        # Play via afplay
        subprocess.run(["afplay", audio_path])
        
    except Exception as e:
        print(f"ElevenLabs TTS failed or not configured. Falling back to native macOS voice. Error: {e}")
        subprocess.run(["say", text])

def main():
    # Wait a few seconds for servers to start if they are also launching on boot
    time.sleep(5)
    
    try:
        # Fetch Briefing
        req = urllib.request.Request("http://127.0.0.1:8000/briefing")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            briefing_text = data.get("text", "Good morning, sir. Briefing data is currently unavailable.")
            
        send_notification("J.A.R.V.I.S.", "System online. Initiating morning briefing.")
        play_audio_or_say(briefing_text)
        
    except Exception as e:
        print(f"Failed to reach JARVIS server: {e}")
        send_notification("J.A.R.V.I.S.", "Failed to connect to core system.")
        subprocess.run(["say", "Good morning, sir. I am currently unable to connect to the core server for your briefing."])

if __name__ == "__main__":
    main()
