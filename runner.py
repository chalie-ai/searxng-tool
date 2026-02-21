import sys
import json
import base64
from handler import execute


def _format_text(result: dict) -> str:
    """Format search results as readable text for LLM synthesis."""
    results = result.get("results", [])
    if not results:
        return result.get("message", "No results found.")
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r.get('title', '')}")
        if snippet := r.get("snippet", ""):
            lines.append(f"   {snippet}")
        if url := r.get("url", ""):
            lines.append(f"   {url}")
        if engine := r.get("engine", ""):
            lines.append(f"   [via {engine}]")
    return "\n".join(lines)


payload = json.loads(base64.b64decode(sys.argv[1]))
params = payload.get("params", {})
settings = payload.get("settings", {})
telemetry = payload.get("telemetry", {})
result = execute(topic="", params=params, config=settings, telemetry=telemetry)
result["text"] = _format_text(result)
print(json.dumps(result))
