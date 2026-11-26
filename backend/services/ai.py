import os
import json
import asyncio
from openai import OpenAI
from backend.integrations.memory import MemoryEngine
from backend.services.tools import TOOL_REGISTRY, TOOLS_SCHEMA
from backend.services.openjarvis_bridge import OpenJarvisBridge

class JarvisBrain:
    def __init__(self):
        self.memory = MemoryEngine()
        groq_key = os.environ.get("GROQ_API_KEY", "")
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_key
        ) if groq_key else None

    async def process_prompt(self, user_prompt: str, mode: str = "hybrid") -> dict:
        context = self.memory.recall_context(user_prompt)
        messages = [
            {"role": "system", "content": "You are J.A.R.V.I.S., Boss Kirtan Patel's personal AI assistant. Address the user as 'Boss Kirtan Patel' or 'sir'. Speak authoritatively and concisely. Use tools when needed to fulfill commands directly."},
            {"role": "user", "content": f"Context: {context}\nQuery: {user_prompt}" if context else user_prompt}
        ]

        loop = asyncio.get_running_loop()

        # Check if local mode explicitly requested
        if mode == "local" or OpenJarvisBridge.current_mode == "local" or not self.client:
            local_reply = await loop.run_in_executor(
                None,
                lambda: OpenJarvisBridge.query_local_llm(messages, max_tokens=180)
            )
            if local_reply:
                self.memory.store_memory(
                    memory_id=str(loop.time()),
                    text_content=f"User: {user_prompt} | JARVIS (Local): {local_reply}"
                )
                return {
                    "content": local_reply,
                    "speech": local_reply,
                    "engine": f"OpenJarvis Local Metal ({OpenJarvisBridge.preferred_local_model})",
                    "status": "success",
                    "mode": "local"
                }

        # Try Cloud Groq first if hybrid or cloud mode
        try:
            # --- First Pass: Model decides if tools are required ---
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    tools=TOOLS_SCHEMA,
                    tool_choice="auto",
                    temperature=0.2
                )
            )
            msg = response.choices[0].message

            # --- Second Pass: Execute Tool Call if requested ---
            if msg.tool_calls:
                messages.append(msg)
                for tool_call in msg.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    handler = TOOL_REGISTRY.get(fn_name)

                    tool_result = handler(**fn_args) if handler else json.dumps({"error": "Tool not found."})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fn_name,
                        "content": tool_result
                    })

                final_response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages,
                        temperature=0.2
                    )
                )
                final_content = final_response.choices[0].message.content
            else:
                final_content = msg.content

            # Save turn to local memory
            self.memory.store_memory(
                memory_id=str(loop.time()),
                text_content=f"User: {user_prompt} | JARVIS: {final_content}"
            )

            return {
                "content": final_content,
                "speech": final_content,
                "engine": "Cloud Groq Llama 3.3 70B (Tool-Enabled)",
                "status": "success",
                "mode": "cloud"
            }
        except Exception as cloud_err:
            print(f"[JARVIS BRAIN] Cloud inference failed ({cloud_err}), falling back to OpenJarvis Local Engine...")
            # Seamless Fallback to OpenJarvis Local Ollama Engine
            try:
                fallback_reply = await loop.run_in_executor(
                    None,
                    lambda: OpenJarvisBridge.query_local_llm(messages, max_tokens=180)
                )
                if fallback_reply:
                    self.memory.store_memory(
                        memory_id=str(loop.time()),
                        text_content=f"User: {user_prompt} | JARVIS (Fallback Local): {fallback_reply}"
                    )
                    return {
                        "content": fallback_reply,
                        "speech": fallback_reply,
                        "engine": f"OpenJarvis Local Metal ({OpenJarvisBridge.preferred_local_model}) [Offline Failover]",
                        "status": "success",
                        "mode": "hybrid_failover"
                    }
            except Exception as local_err:
                print(f"[JARVIS BRAIN] Local inference fallback error: {local_err}")

            return {
                "content": f"Neural connection degraded: {cloud_err}",
                "speech": f"Neural connection degraded: {cloud_err}",
                "engine": "Offline Protocol",
                "status": "failed"
            }
