import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('backend/.env')

class JarvisBrain:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.environ.get("NVIDIA_API_KEY")
        )

    def ask(self, user_prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are J.A.R.V.I.S., Boss Kirtan Patel's highly intelligent AI assistant. Keep responses short and witty."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.6,
            top_p=0.95,
            max_tokens=1024,
            stream=False 
        )
        
        return completion.choices[0].message.content

brain = JarvisBrain()
response_text = brain.ask("Tell me a quick 1-sentence greeting, J.A.R.V.I.S style.")
print("J.A.R.V.I.S:", response_text)
