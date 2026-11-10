"""engine_identity.py — capture and verify the engine's identity (gate 0.4).

Gate 0.4: the engine's identity (container image, argv, versions) is unobservable
at grade time unless it is captured at run start and pinned.  This module captures
everything the server will disclose via metadata GETs, records UNOBSERVABLE (with
the endpoint tried and its status) where it will not, and provides the check that
compares a capture against a pinned expectation.

Metadata GETs only.  No completion path (/v1/chat/completions, /generate, ...) is
ever touched.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

UNOBSERVABLE = "UNOBSERVABLE"

REQUIRED_FIELDS = ["model_id", "served_model_name", "engine_version"]
OPTIONAL_FIELDS = ["argv", "image_or_container", "model_path", "revision"]

COMPLETION_PATHS = [
    "/v1/chat/completions",
    "/v1/completions",
    "/v1/responses",
    "/generate",
    "/api/generate",
    "/continue_generation",
]

METADATA_ENDPOINTS = [
    "/",
    "/health",
    "/v1/models",
    "/server_info",
    "/model_info",
    "/get_model_info",
    "/api/tags",
    "/metrics",
    "/openapi.json",
    "/v1/loads",
    "/get_load",
    "/weight_version",
    "/get_weight_version",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _http_get(url: str, timeout: float = 3.0):
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=float(timeout)) as resp:
            raw = resp.read()
            status = getattr(resp, "status", 200)
            try:
                text = raw.decode("utf-8", "replace")
            except Exception:
                text = repr(raw[:200])
            return status, text, None
    except urllib.error.HTTPError as exc:
        try:
            text = exc.read().decode("utf-8", "replace")
        except Exception:
            text = ""
        return exc.code, text, None
    except Exception as exc:
        return None, "", "%s: %s" % (type(exc).__name__, exc)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def _trunc(text: str, limit: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "\u2026"


def _safe_json(text: str):
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError, TypeError):
        return None


def capture(base_url: str, timeout: float = 3.0, out_path: Optional[str] = None) -> Dict[str, Any]:
    base = str(base_url).rstrip("/")
    endpoints: List[Dict[str, Any]] = []
    bodies: Dict[str, str] = {}
    statuses: Dict[str, Any] = {}

    for path in METADATA_ENDPOINTS:
        url = base + path
        status, text, err = _http_get(url, timeout=timeout)
        endpoints.append({
            "path": path,
            "url": url,
            "method": "GET",
            "status": status,
            "body_excerpt": _trunc(text, 240) if text else ("" if err is None else _trunc(err, 240)),
            "digest": _digest(text) if text else None,
            "error": err,
        })
        bodies[path] = text or ""
        statuses[path] = status

    model_id = UNOBSERVABLE
    served_model_name = UNOBSERVABLE
    model_probe = "GET %s/v1/models" % base
    v1_text = bodies.get("/v1/models", "")
    v1_json = _safe_json(v1_text)
    if isinstance(v1_json, dict):
        entries = v1_json.get("data") or v1_json.get("models") or []
        if entries and isinstance(entries[0], dict):
            first = entries[0]
            model_id = (first.get("id") or first.get("model") or first.get("name")
                        or UNOBSERVABLE)
            served_model_name = (first.get("id") or first.get("root") or first.get("model")
                                 or model_id)
            model_probe = "GET %s/v1/models -> id=%r" % (base, model_id)
        else:
            model_probe = "GET %s/v1/models -> %s" % (base, "no model entries")
    else:
        model_probe = "GET %s/v1/models -> %s" % (base, "no response")

    engine_version = UNOBSERVABLE
    argv = UNOBSERVABLE
    image_or_container = UNOBSERVABLE
    model_path = UNOBSERVABLE
    revision = UNOBSERVABLE
    server_probe = "GET %s/server_info" % base
    si_text = bodies.get("/server_info", "")
    si_json = _safe_json(si_text)
    if isinstance(si_json, dict):
        engine_version = si_json.get("version", UNOBSERVABLE) or UNOBSERVABLE
        model_path = si_json.get("model_path", UNOBSERVABLE) or UNOBSERVABLE
        revision = si_json.get("revision", UNOBSERVABLE) or UNOBSERVABLE
        for key in ("argv", "args", "command_line", "cmdline", "launch_args"):
            if si_json.get(key) not in (None, "", UNOBSERVABLE):
                argv = si_json.get(key)
                break
        for key in ("image", "image_digest", "image_id", "container", "container_id",
                    "container_image", "docker_image"):
            if si_json.get(key) not in (None, "", UNOBSERVABLE):
                image_or_container = si_json.get(key)
                break
        server_probe = ("GET %s/server_info -> version=%r argv=%r image=%r"
                        % (base, engine_version, argv, image_or_container))
    else:
        server_probe = "GET %s/server_info -> %s" % (base, "no response")

    model_info_probe = "GET %s/model_info" % base
    mi_text = bodies.get("/model_info", "")
    mi_json = _safe_json(mi_text)
    if isinstance(mi_json, dict):
        if model_path == UNOBSERVABLE:
            model_path = mi_json.get("model_path", model_path) or model_path
        if revision == UNOBSERVABLE:
            revision = mi_json.get("revision", revision) or revision
        model_info_probe = "GET %s/model_info -> ok" % base
    else:
        model_info_probe = "GET %s/model_info -> %s" % (base, "no response")

    health_probe = "GET %s/health" % base
    health_text = bodies.get("/health", "")
    health_json = _safe_json(health_text)
    if isinstance(health_json, dict):
        if argv == UNOBSERVABLE:
            for key in ("argv", "args", "command_line", "cmdline"):
                if health_json.get(key) not in (None, "", UNOBSERVABLE):
                    argv = health_json.get(key)
                    break
        if image_or_container == UNOBSERVABLE:
            for key in ("image", "image_digest", "image_id", "container", "container_id",
                        "container_image", "docker_image"):
                if health_json.get(key) not in (None, "", UNOBSERVABLE):
                    image_or_container = health_json.get(key)
                    break
        health_probe = "GET %s/health -> argv=%r image=%r" % (base, argv, image_or_container)
    else:
        health_probe = "GET %s/health -> status=%s" % (base, statuses.get("/health"))

    identity = {
        "schema": "engine-identity/1",
        "captured_at": _utc_now(),
        "base_url": base,
        "model_id": model_id,
        "served_model_name": served_model_name,
        "engine_version": engine_version,
        "argv": argv,
        "image_or_container": image_or_container,
        "model_path": model_path,
        "revision": revision,
        "probes": {
            "model": model_probe,
            "server": server_probe,
            "model_info": model_info_probe,
            "health": health_probe,
        },
        "argv_probe": (
            server_probe if argv != UNOBSERVABLE else
            "GET %s/server_info (status=%s) + GET %s/health (status=%s): no argv field disclosed"
            % (base, statuses.get("/server_info"), base, statuses.get("/health"))
        ),
        "image_probe": (
            server_probe if image_or_container != UNOBSERVABLE else
            "GET %s/server_info (status=%s) + GET %s/health (status=%s): no image/container field disclosed"
            % (base, statuses.get("/server_info"), base, statuses.get("/health"))
        ),
        "endpoints": endpoints,
        "completion_paths_touched": [],
        "completion_paths_avoided": list(COMPLETION_PATHS),
    }

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(identity, fh, indent=2, sort_keys=True)
            fh.write("\n")

    return identity


def check(captured: Dict[str, Any], pinned: Dict[str, Any],
         required: Optional[List[str]] = None) -> (bool, List[str]):
    required = list(required if required is not None else REQUIRED_FIELDS)
    failures: List[str] = []
    for field in required:
        cv = captured.get(field)
        pv = pinned.get(field)
        if isinstance(pinned, dict) and "captured_identity" in pinned and field not in pinned:
            pv = pinned.get("captured_identity", {}).get(field)
        if cv == UNOBSERVABLE or cv is None:
            failures.append("%s: captured is %r (UNOBSERVABLE/missing)" % (field, cv))
        if pv == UNOBSERVABLE or pv is None:
            failures.append("%s: pinned is %r (UNOBSERVABLE/missing)" % (field, pv))
        if cv != pv:
            failures.append("%s: mismatch captured=%r pinned=%r" % (field, cv, pv))
    for field in OPTIONAL_FIELDS:
        if field in captured or field in pinned or (isinstance(pinned, dict) and "captured_identity" in pinned and field in pinned.get("captured_identity", {})):
            cv = captured.get(field, UNOBSERVABLE)
            pv = pinned.get(field, UNOBSERVABLE)
            if isinstance(pinned, dict) and "captured_identity" in pinned and field not in pinned:
                pv = pinned.get("captured_identity", {}).get(field, UNOBSERVABLE)
            if cv != pv and not (cv == UNOBSERVABLE and pv == UNOBSERVABLE):
                failures.append("%s: mismatch captured=%r pinned=%r" % (field, cv, pv))
    return (len(failures) == 0), failures


def gate_check(captured, pinned, required=None):
    return check(captured, pinned, required)


def verify(captured, pinned, required=None):
    return check(captured, pinned, required)


def assert_identity(captured, pinned, required=None):
    ok, failures = check(captured, pinned, required)
    if not ok:
        raise AssertionError("engine identity mismatch:\n  " + "\n  ".join(failures))
    return True


def stamp_into_manifest(manifest: Dict[str, Any], identity: Dict[str, Any]) -> Dict[str, Any]:
    manifest = dict(manifest)
    manifest["engine_identity"] = identity
    fp = manifest.get("fingerprints")
    if isinstance(fp, dict):
        fp = dict(fp)
        fp["engine"] = {
            "image_digest": identity.get("image_or_container", UNOBSERVABLE),
            "exact_argv": identity.get("argv", UNOBSERVABLE),
            "probe": identity.get("probes", {}).get("server", ""),
            "engine_version": identity.get("engine_version", UNOBSERVABLE),
            "model_id": identity.get("model_id", UNOBSERVABLE),
        }
        manifest["fingerprints"] = fp
    return manifest


def stamp_into_row(row: Dict[str, Any], identity: Dict[str, Any]) -> Dict[str, Any]:
    row = dict(row)
    row["engine_identity"] = {
        "model_id": identity.get("model_id", UNOBSERVABLE),
        "engine_version": identity.get("engine_version", UNOBSERVABLE),
        "argv": identity.get("argv", UNOBSERVABLE),
        "image_or_container": identity.get("image_or_container", UNOBSERVABLE),
    }
    return row


capture_identity = capture
probe = capture
probe_engine_identity = capture
check_identity = check
verify_identity = verify


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Capture engine identity (gate 0.4)")
    ap.add_argument("--base-url", default="http://192.168.2.168:8012")
    ap.add_argument("--out", default="experiments/ptr-engine/measure/ENGINE-IDENTITY.json")
    ap.add_argument("--timeout", type=float, default=3.0)
    ap.add_argument("--pin", default=None, help="pinned expectation JSON to check against")
    ap.add_argument("--check", action="store_true", help="compare capture to --pin and exit nonzero on mismatch")
    args = ap.parse_args(argv)
    ident = capture(args.base_url, timeout=args.timeout, out_path=args.out)
    print(json.dumps({
        "model_id": ident["model_id"],
        "served_model_name": ident["served_model_name"],
        "engine_version": ident["engine_version"],
        "argv": ident["argv"],
        "image_or_container": ident["image_or_container"],
        "out": args.out,
    }, indent=2))
    if args.pin:
        with open(args.pin, encoding="utf-8") as fh:
            pinned = json.load(fh)
        if "captured_identity" in pinned:
            pinned = pinned["captured_identity"]
        ok, failures = check(ident, pinned)
        print("CHECK:", "PASS" if ok else "FAIL")
        for f in failures:
            print("  -", f)
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
echo "written"; ls -la experiments/ptr-engine/longrun/engine_identity.py