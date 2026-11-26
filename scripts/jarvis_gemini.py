import os
import subprocess
from google import genai
from dotenv import load_dotenv

# Load the API key injected into backend/.env
load_dotenv('backend/.env')

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class JarvisBrain:
    def __init__(self, client):
        self.client = client

    def ask(self, user_prompt: str) -> str:
        system_instruction = (
            "You are J.A.R.V.I.S., Boss Kirtan Patel's highly intelligent, concise, "
            "and witty AI assistant. Respond in a high-tech, helpful peer voice."
        )
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{system_instruction}\n\nUser: {user_prompt}",
        )
        return response.text

brain = JarvisBrain(client)
response_text = brain.ask("Tell me a quick 1-sentence greeting, J.A.R.V.I.S style.")
print("J.A.R.V.I.S:", response_text)
