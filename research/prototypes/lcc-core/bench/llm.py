"""Call Claude through the local subscription CLI (`claude -p`), with an on-disk cache so reruns are free.

No API keys: this uses the logged-in Claude Code subscription. Tools, MCP servers and settings are off.
"""
import hashlib
import json
import os
import subprocess
import time

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BENCH_DIR, "cache")
TIMEOUT_S = 300


def call(model, system_prompt, prompt, schema):
    """Return (parsed_json, usage, seconds, cached)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.sha256(json.dumps([model, system_prompt, prompt, schema]).encode()).hexdigest()[:24]
    cache_path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(cache_path):
        with open(cache_path) as file:
            stored = json.load(file)
        return stored["output"], stored["usage"], stored["seconds"], True
    command = ["claude", "-p", "--model", model, "--strict-mcp-config", "--tools", "", "--setting-sources", "",
               "--disable-slash-commands", "--no-session-persistence", "--system-prompt", system_prompt,
               "--output-format", "json", "--json-schema", json.dumps(schema)]
    started = time.time()
    completed = subprocess.run(command, input=prompt, capture_output=True, text=True, timeout=TIMEOUT_S, cwd="/tmp")
    seconds = time.time() - started
    raw = completed.stdout
    payload = json.loads(raw[raw.find("{"):])
    if payload.get("is_error"):
        raise RuntimeError(str(payload.get("result"))[:500] + completed.stderr[-300:])
    output = payload.get("structured_output")
    if output is None:
        output = json.loads(payload.get("result", "{}"))
    usage = payload.get("usage", {})
    with open(cache_path, "w") as file:
        json.dump({"output": output, "usage": usage, "seconds": seconds}, file)
    return output, usage, seconds, False


def input_tokens(usage):
    return (usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0))
