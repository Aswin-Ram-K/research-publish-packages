#!/usr/bin/env python3
"""Compute the four contract fingerprints for the pilot's serving configuration.

The interface contract (``handoff from consonance/INTERFACE_CONTRACT.md`` §1)
says two arms are comparable only when model, tokenizer, renderer and engine
fingerprints are equal.  Every envelope written by this pilot names these four
digests, and a run whose fingerprints differ is a different experiment.

Inputs are the pinned capture files, never the live server: a fingerprint that
changes because a server was re-profiled is not a fingerprint.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
WT = Path(__file__).resolve().parents[5]
SERVER_INFO = CELL / "notes/server-info-2026-11-04-occamy.json"
INSPECT = CELL / "notes/container-inspect-2026-11-04.json"
RENDER = WT / "src/resextract/context/render.py"
ADAPTER = CELL / "tools/adapter.py"


def digest(obj) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    info = json.loads(SERVER_INFO.read_text())
    inner = info["internal_states"][0]
    container = json.loads(INSPECT.read_text())[0]

    model = {
        "model_path": inner["model_path"],
        "quantization": inner["quantization"],
        "dtype": inner["dtype"],
        "context_length": inner["context_length"],
        "served_model_name": inner["served_model_name"],
    }
    tokenizer = {
        "tokenizer_path": inner["tokenizer_path"],
        "tokenizer_backend": inner["tokenizer_backend"],
        "tokenizer_mode": inner["tokenizer_mode"],
        "chat_template": inner["chat_template"],
        "tool_call_parser": inner["tool_call_parser"],
        "reasoning_parser": inner["reasoning_parser"],
    }
    engine = {
        "image": container["Image"],
        "args": container["Args"],
        "env_offline": [
            e for e in container["Config"]["Env"] if e.split("=")[0] in
            {"HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "PYTORCH_CUDA_ALLOC_CONF", "SGLANG_CACHE_DIR"}
        ],
    }
    renderer = {
        "render_py": file_digest(RENDER),
        "adapter_py": file_digest(ADAPTER),
        "message_assembly": "system message, then alternating user/assistant messages; no hidden padding",
    }
    out = {
        "schema": "typed-context-pilot.fingerprints/1",
        "model": model,
        "model_fingerprint": digest(model),
        "tokenizer": tokenizer,
        "tokenizer_fingerprint": digest(tokenizer),
        "renderer": renderer,
        "renderer_fingerprint": digest(renderer),
        "engine": engine,
        "engine_fingerprint": digest(engine),
        "version": info.get("version"),
        "sources": {
            "server_info": str(SERVER_INFO),
            "server_info_sha256": file_digest(SERVER_INFO),
            "container_inspect": str(INSPECT),
            "container_inspect_sha256": file_digest(INSPECT),
        },
    }
    path = CELL / "envelopes/fingerprints.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n")
    for key in ("model_fingerprint", "tokenizer_fingerprint", "renderer_fingerprint", "engine_fingerprint"):
        print(f"{key:24s} {out[key]}")
    print("version", out["version"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
