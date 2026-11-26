import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    @property
    def gemini_api_key(self) -> str:
        # Reload environment variables in case they were updated
        load_dotenv(dotenv_path=ENV_PATH, override=False)
        return os.getenv("GEMINI_API_KEY", "")

    @property
    def nvidia_api_key(self) -> str:
        load_dotenv(dotenv_path=ENV_PATH, override=False)
        return os.getenv("NVIDIA_API_KEY", "")

    @property
    def elevenlabs_api_key(self) -> str:
        load_dotenv(dotenv_path=ENV_PATH, override=False)
        return os.getenv("ELEVENLABS_API_KEY", "")

    @property
    def elevenlabs_voice_id(self) -> str:
        load_dotenv(dotenv_path=ENV_PATH, override=False)
        return os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    @property
    def user_name(self) -> str:
        load_dotenv(dotenv_path=ENV_PATH, override=False)
        return os.getenv("USER_NAME", "Tony Stark")

settings = Settings()

def save_config(gemini_key: str = None, elevenlabs_key: str = None, user_name: str = None) -> bool:
    """
    Saves new keys and user name back to the .env file.
    """
    try:
        lines = []
        if ENV_PATH.exists():
            with open(ENV_PATH, "r") as f:
                lines = f.readlines()
        
        # Track which keys we updated
        updated_gemini = False
        updated_elevenlabs = False
        updated_username = False
        
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("GEMINI_API_KEY=") and gemini_key is not None:
                new_lines.append(f"GEMINI_API_KEY={gemini_key}\n")
                updated_gemini = True
            elif stripped.startswith("ELEVENLABS_API_KEY=") and elevenlabs_key is not None:
                new_lines.append(f"ELEVENLABS_API_KEY={elevenlabs_key}\n")
                updated_elevenlabs = True
            elif stripped.startswith("USER_NAME=") and user_name is not None:
                new_lines.append(f"USER_NAME={user_name}\n")
                updated_username = True
            else:
                new_lines.append(line)
        
        # Append if they weren't in the file
        if not updated_gemini and gemini_key is not None:
            new_lines.append(f"GEMINI_API_KEY={gemini_key}\n")
        if not updated_elevenlabs and elevenlabs_key is not None:
            new_lines.append(f"ELEVENLABS_API_KEY={elevenlabs_key}\n")
        if not updated_username and user_name is not None:
            new_lines.append(f"USER_NAME={user_name}\n")
            
        with open(ENV_PATH, "w") as f:
            f.writelines(new_lines)
            
        # Reload environment
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
