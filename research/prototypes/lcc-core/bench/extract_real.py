"""Run core/extract.py unchanged on real public documents (data_real/docs) with the onboarding registry
data_real/registries.json. Writes data_real/out/<doc>.json. Run with python -I.

  python -I bench/extract_real.py
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

BENCH_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BENCH_DIR)
for sub in ("core", "bench", "data"):
    sys.path.insert(0, os.path.join(ROOT, sub))

from extract import extract_document, read_document  # noqa: E402

REAL = os.path.join(ROOT, "data_real")
CACHE = os.path.join(REAL, "cache")


def call(model, system_prompt, prompt, schema):
    """Same `claude -p` command as bench/llm.py, but tolerant of CLI versions that print a JSON array of events."""
    import hashlib
    import subprocess
    import time
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha256(json.dumps([model, system_prompt, prompt, schema]).encode()).hexdigest()[:24]
    path = os.path.join(CACHE, key + ".json")
    if os.path.exists(path):
        stored = json.load(open(path))
        return stored["output"], stored["usage"], stored["seconds"], True
    command = ["claude", "-p", "--model", model, "--strict-mcp-config", "--tools", "", "--setting-sources", "",
               "--disable-slash-commands", "--no-session-persistence", "--system-prompt", system_prompt,
               "--output-format", "json", "--json-schema", json.dumps(schema)]
    started = time.time()
    done = subprocess.run(command, input=prompt, capture_output=True, text=True, timeout=600, cwd="/tmp")
    seconds = time.time() - started
    payload = json.loads(done.stdout)
    if isinstance(payload, list):
        payload = [item for item in payload if item.get("type") == "result"][-1]
    if payload.get("is_error"):
        raise RuntimeError(str(payload.get("result"))[:500])
    output = payload.get("structured_output")
    if output is None:
        output = json.loads(payload.get("result", "{}"))
    usage = payload.get("usage", {})
    json.dump({"output": output, "usage": usage, "seconds": seconds}, open(path, "w"))
    return output, usage, seconds, False
IDS = ["ADIENT-SSM-Q-R10", "ADIENT-LTR-UC", "ASTEMO-SCM-R4", "FORD-573-18V806"]
RUN = os.environ.get("ONLY", ",".join(IDS)).split(",")  # ONLY=FORD-573-18V806 REG=registries_ford_b.json OUT_SUFFIX=_B


def run(doc_id):
    path = os.path.join(REAL, "docs", doc_id + ".md")
    with open(os.path.join(REAL, os.environ.get("REG", "registries.json"))) as file:
        registries = {k: v for k, v in json.load(file).items() if not k.startswith("_")}
    result = extract_document(path, registries, IDS, call=call, guarded=True)
    _, body = read_document(path)
    result["chars"] = len(body)
    os.makedirs(os.path.join(REAL, "out"), exist_ok=True)
    with open(os.path.join(REAL, "out", doc_id + os.environ.get("OUT_SUFFIX", "") + ".json"), "w") as file:
        json.dump(result, file, indent=1, default=str)
    return doc_id, result


if __name__ == "__main__":
    with ThreadPoolExecutor(4) as pool:
        for doc_id, result in pool.map(run, RUN):
            print(f"{doc_id}: {result['chars']} chars, {result['chunks']} chunks, {len(result['accepted'])} kept, "
                  f"{len(result['review'])} review, {result['tokens_in']} in, {result['tokens_out']} out, "
                  f"{result['seconds']:.0f}s")
