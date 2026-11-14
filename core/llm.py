"""Model access for parse.py and extract.py: one structured-output call, cached as a fixture.

The product calls models through the Vercel AI Gateway (OpenAI-compatible), server side only. The key is read from
env AI_GATEWAY_API_KEY, or from the repo's .env (gitignored); it is never logged or written anywhere.

Every answer is stored under a fixtures directory, keyed by a hash of (model, system prompt, prompt, schema). A
call with the same inputs replays the fixture for free, so tests run without the key. live=True skips the replay
and records a new answer.

Written 14 Nov 2026 (workstream P). The fixture cache follows bench/llm.py of the research prototype
(night-shift/2026-11-13-kva-plan), which cached `claude -p` answers the same way.
"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATEWAY_URL = "https://ai-gateway.vercel.sh/v1"
KEY_NAME = "AI_GATEWAY_API_KEY"


class FixtureMissing(RuntimeError):
    """No recorded model answer for this prompt and AI_GATEWAY_API_KEY is not set."""


def load_dotenv(path=os.path.join(ROOT, ".env")):
    """Put AI_GATEWAY_API_KEY from the repo's .env into the environment if it is not set there."""
    if os.environ.get(KEY_NAME) or not os.path.exists(path):
        return
    with open(path) as file:
        for line in file:
            name, _, value = line.strip().partition("=")
            if name == KEY_NAME and value.strip():
                os.environ[name] = value.strip().strip('"').strip("'")


def fixture_key(model, system, prompt, schema):
    return hashlib.sha256(json.dumps([model, system, prompt, schema]).encode()).hexdigest()[:24]


def gateway_call(model, system, prompt, schema, max_tokens=1200, schema_name="output"):
    """One structured-output call through the gateway. Returns (parsed dict, usage dict)."""
    from openai import OpenAI
    client = OpenAI(base_url=GATEWAY_URL, api_key=os.environ[KEY_NAME])
    response = client.chat.completions.create(
        model=model, temperature=0, max_tokens=max_tokens,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": schema_name, "schema": schema, "strict": True}},
    )
    content = response.choices[0].message.content or ""
    start, end = content.find("{"), content.rfind("}")
    output = json.loads(content[start:end + 1])
    usage = response.usage.model_dump() if response.usage else {}
    return output, usage


def cached_call(model, system, prompt, schema, fixtures_dir, live=False, call=None, note=None, max_tokens=1200):
    """Return (output, meta). meta = {"source": "fixture"|"live", "recorded_by", "key"}.

    `call(model, system, prompt, schema) -> (output, usage)` replaces the gateway (tests, other recorders); its
    attribute `recorded_by` names it in the fixture. `note` is stored for a person reading the fixture.
    """
    key = fixture_key(model, system, prompt, schema)
    path = os.path.join(fixtures_dir, f"{key}.json")
    if not live and os.path.exists(path):
        with open(path) as file:
            stored = json.load(file)
        return stored["output"], {"source": "fixture", "recorded_by": stored.get("recorded_by"), "key": key}
    if call is None:
        load_dotenv()
        if not os.environ.get(KEY_NAME):
            raise FixtureMissing(f"no fixture {key} and {KEY_NAME} is not set")
        output, usage = gateway_call(model, system, prompt, schema, max_tokens=max_tokens)
        recorded_by = f"vercel-ai-gateway {model}"
    else:
        output, usage = call(model, system, prompt, schema)
        recorded_by = getattr(call, "recorded_by", "custom")
    os.makedirs(fixtures_dir, exist_ok=True)
    with open(path, "w") as file:
        json.dump({"note": note, "model": model, "recorded_by": recorded_by, "output": output, "usage": usage},
                  file, indent=1, ensure_ascii=False)
    return output, {"source": "live", "recorded_by": recorded_by, "key": key}
