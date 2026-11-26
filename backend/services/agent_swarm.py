import sys
import io
import re
import traceback
import subprocess
import tempfile
import os

class AgentSwarm:
    @staticmethod
    def execute_python_code(code_str: str) -> dict:
        """Executes generated engineering/math Python code in a safe temporary environment."""
        if not code_str:
            return {"success": False, "output": "", "error": "No code provided to execute."}

        # Extract python code block if markdown formatting is present
        if "```" in code_str:
            matches = re.findall(r"```(?:python)?\s*([\s\S]*?)```", code_str)
            if matches:
                clean_code = matches[0].strip()
            else:
                clean_code = code_str.replace("```python", "").replace("```", "").strip()
        else:
            clean_code = code_str.strip()

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as temp_file:
            temp_file.write(clean_code)
            temp_path = temp_file.name

        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=8
            )
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            return {
                "success": result.returncode == 0,
                "output": output if output else "Script executed successfully with no stdout.",
                "error": error,
                "code": clean_code
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": "Execution timed out (8s limit).", "code": clean_code}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e), "code": clean_code}
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
