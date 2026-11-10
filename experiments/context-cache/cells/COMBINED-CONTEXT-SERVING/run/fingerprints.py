#!/usr/bin/env python3
"""Compute the four independent fingerprints for COMBINED-CONTEXT-SERVING.

Reads evidence captured NOW into run/captures/. Writes run/FINGERPRINTS.json.
No network, no model request.

Renderer fingerprint formula (updated to include history construction):
sha256(json.dumps({
  'canonicalization': CONTROLS.json['canonical'],
  'preamble': shared preamble text from render_arms._preamble(sample fixture),
  'arm_templates': [(filename, sha256(filename)) for filename in
      arms/{canonical,store,render_arms,guard_constraints}.py + CONTROLS.json
      + run/driver.py (make_history: builds answer/claim/reference inputs for arms B and C)],
}, sort_keys=True))
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

CELL = Path(__file__).resolve().parents[1]
CAP = CELL / "run" / "captures"
OUT = CELL / "run" / "FINGERPRINTS.json"
ARMS = CELL / "arms"
if str(ARMS) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(ARMS))
import render_arms as _ra  # type: ignore


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main():
    models = json.loads((CAP / "models.json").read_text())
    m0 = models["data"][0]
    model_id = m0["id"]
    max_model_len = int(m0["max_model_len"])
    raw = (CAP / "docker_image_args.txt").read_text()
    image_digest = raw.splitlines()[0].strip().strip('"')
    # find JSON array in raw
    import re
    m = re.search(r"\[.*\]", raw, re.S)
    args_list = json.loads(m.group(0)) if m else []
    flag_string = " ".join(args_list)
    weights_path = ""
    for i, a in enumerate(args_list):
        if a == "--model-path" and i + 1 < len(args_list):
            weights_path = args_list[i + 1]
    weights_listing_sha = sha256_file(CAP / "weights_listing.txt")
    tokenize = json.loads((CAP / "tokenize.json").read_text())
    sglang_version = (CAP / "sglang_version.txt").read_text().strip()
    chat_template_sha = sha256_file(CAP / "chat_template.jinja")
    docker_inspect_sha = sha256_file(CAP / "docker_inspect.json")

    # renderer inputs
    renderer_inputs = []
    for name in ("canonical.py", "store.py", "render_arms.py", "guard_constraints.py", "CONTROLS.json"):
        p = ARMS / name
        if p.is_file():
            renderer_inputs.append((name, sha256_file(p)))
    # history-construction implementation (make_history) lives in run/driver.py
    driver_path = CELL / "run" / "driver.py"
    if driver_path.is_file():
        renderer_inputs.append(("driver.py (make_history)", sha256_file(driver_path)))
    controls_bytes = (ARMS / "CONTROLS.json").read_bytes()

    # ---- model fingerprint ----
    model_payload = {
        "model_id": model_id,
        "max_model_len": max_model_len,
        "weights_path": weights_path,
        "weights_listing_sha256": weights_listing_sha,
    }
    model_fp = sha256_bytes(json.dumps(model_payload, sort_keys=True).encode())

    # ---- tokenizer+template fingerprint ----
    tok_payload = {
        "tokenize_count": tokenize.get("count"),
        "tokenize_tokens": tokenize.get("tokens"),
        "max_model_len_from_tokenize": tokenize.get("max_model_len"),
        "chat_template_sha256": chat_template_sha,
    }
    tok_fp = sha256_bytes(json.dumps(tok_payload, sort_keys=True).encode())

    # ---- renderer fingerprint ----
    import json as _j
    _sample = _j.loads((ARMS / "fixtures" / "sample.json").read_text())
    _preamble_text = _ra._preamble(_sample)
    renderer_payload = {
        "canonicalization": json.loads(controls_bytes)["canonical"],
        "preamble": _preamble_text,
        "arm_templates": renderer_inputs,
    }
    renderer_fp = sha256_bytes(json.dumps(renderer_payload, sort_keys=True).encode())

    # ---- engine+flags fingerprint ----
    engine_payload = {
        "image_digest": image_digest,
        "sglang_version": sglang_version,
        "flag_string": flag_string,
        "docker_inspect_sha256": docker_inspect_sha,
    }
    engine_fp = sha256_bytes(json.dumps(engine_payload, sort_keys=True).encode())

    out = {
        "run_id": "CCS-2026-11-05",
        "captured_at_utc": "2026-11-05",
        "model": {
            "digest": model_fp,
            "formula": "sha256(json.dumps({'model_id':<from /v1/models>, 'max_model_len':<from /v1/models>, 'weights_path':<--model-path arg>, 'weights_listing_sha256':sha256(run/captures/weights_listing.txt)}, sort_keys=True))",
            "model_id": model_id,
            "max_model_len": max_model_len,
            "weights_path": weights_path,
            "weights_listing_sha256": weights_listing_sha,
        },
        "tokenizer_template": {
            "digest": tok_fp,
            "formula": "sha256(json.dumps({'tokenize_count':<POST /tokenize count>, 'tokenize_tokens':<POST /tokenize tokens>, 'max_model_len_from_tokenize':<POST /tokenize max_model_len>, 'chat_template_sha256':sha256(run/captures/chat_template.jinja)}, sort_keys=True))",
            "note": "POST /tokenize is an HTTP request but NOT a model request; counted separately from the 1500 model-request reservation.",
            "tokenize_sample": tokenize,
            "chat_template_sha256": chat_template_sha,
        },
        "renderer": {
            "digest": renderer_fp,
            "formula": "sha256(json.dumps({'canonicalization':CONTROLS.json['canonical'], 'preamble':<shared preamble text from render_arms._preamble(sample fixture)>, 'arm_templates':[(filename, sha256(filename)) for filename in arms/{canonical,store,render_arms,guard_constraints}.py + CONTROLS.json + run/driver.py (make_history)]}, sort_keys=True))",
            "inputs": renderer_inputs,
        },
        "engine_flags": {
            "digest": engine_fp,
            "formula": "sha256(json.dumps({'image_digest':<docker inspect .Image>, 'sglang_version':<docker exec sglang.__version__>, 'flag_string':<' '.join(docker inspect .Args)>, 'docker_inspect_sha256':sha256(run/captures/docker_inspect.json)}, sort_keys=True))",
            "image_digest": image_digest,
            "sglang_version": sglang_version,
            "flag_string": flag_string,
        },
        "calibration": {
            "sample_tokens": tokenize.get("count"),
            "sample_text": "hello world",
        },
    }
    old_digest = None
    if OUT.is_file():
        try:
            old_digest = json.loads(OUT.read_text()).get("renderer", {}).get("digest")
        except Exception:
            old_digest = None
    out["renderer"]["renderer_history"] = {
        "old_digest": old_digest,
        "new_digest": renderer_fp,
        "note": (
            "Rows written before this change carry old_digest. "
            "For the arm/render code the renderer is unchanged, so the current run's rows and the new digest "
            "describe the same renderer for arm code; however the history builder (make_history in run/driver.py) "
            "was unverified before this change, so identical history construction cannot be claimed for prior rows."
        ),
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print("model=" + model_fp[:12])
    print("tokenizer_template=" + tok_fp[:12])
    print("renderer=" + renderer_fp[:12])
    print("engine_flags=" + engine_fp[:12])


if __name__ == "__main__":
    main()
