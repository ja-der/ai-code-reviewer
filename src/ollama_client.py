import subprocess
import json
import re


def call_ollama(model: str, prompt: str, system: str = "") -> str:
    """
    Calls the Ollama CLI and returns the model output as text.
    """
    try:
        # Run ollama prompt command and capture JSON output
        result = subprocess.run(
            ["ollama", "run", model],
            input=f"{system}\n{prompt}",
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print("❌ Ollama command failed:", e.stderr)
        return ""


def try_extract_json(text: str):
    """
    Attempts to extract and parse JSON content from model output.
    """
    # Find JSON block in text
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        print("⚠️ No JSON found in model output")
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        print("⚠️ Failed to parse model output as JSON")
        return None
