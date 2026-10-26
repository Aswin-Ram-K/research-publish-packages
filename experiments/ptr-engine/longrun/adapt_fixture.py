#!/usr/bin/env python3
"""Adapt an AUTHORED fixture (``consonance.fixture/1``) to a RUNTIME fixture
(``consonance.longrun-fixture/1``) that ``run_longrun.py`` can load.

Why this exists: ``fixtures/LR-0{1..6}.json`` are authored by the suite card in the
``consonance.fixture/1`` schema (sources pinned by path+pointer+sha256, turns carrying an
``instruction``).  ``run_longrun.py:137`` instead requires ``consonance.longrun-fixture/1``
plus ``N``, ``wall_tokens``, ``bytes_per_token``, ``system_prompt``, ``items`` and
``turns`` numbered 1..N, and ``:650`` computes requests as ``N x reps``.  Neither side's
authored artefact is edited here: this adapter is the only bridge.

Usage:
    adapt_fixture.py --all
    adapt_fixture.py --fixture experiments/ptr-engine/longrun/fixtures/LR-04.json
    adapt_fixture.py --all --out-dir experiments/ptr-engine/longrun/runtime

Measurements (recorded, not guessed):
  * ``bytes_per_token``  = total UTF-8 bytes of the loaded item bodies / token count of
    the same text under tiktoken ``cl100k_base`` (loaded from the local cache; offline).
  * digests are sha256 over raw file bytes.  A source that cannot be read, or whose file
    digest differs from the authored ``sources[].sha256``, is a HARD FAILURE: the source is
    named and the adapter stops.  No placeholder is ever substituted.

Zero network access.  Run with ``.venv/bin/python`` so the package imports resolve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

AUTHORED_SCHEMA = "consonance.fixture/1"
RUNTIME_SCHEMA = "consonance.longrun-fixture/1"

# The one fixed system prompt this adapter declares for every runtime fixture.
SYSTEM_PROMPT = (
    "You are a long-horizon coding agent working on the ptr-engine acceptance target. "
    "Work only from the pinned working set shown to you; obey every negative constraint; "
    "never claim a command you did not run, and never restate a fact you did not read."
)

# Defaults used when the authored fixture does not state a value.
DEFAULT_WALL_TOKENS = 65536
DEFAULT_FIXTURE_DIR = "experiments/ptr-engine/longrun/fixtures"
DEFAULT_OUT_DIR = "experiments/ptr-engine/longrun/runtime"

_POINTER_RE = re.compile(r"^#L(\d+)(?:-L(\d+))?$")


class AdaptError(RuntimeError):
    """A source could not be loaded or its pinned digest did not match."""


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def _normalise_digest(value: str) -> str:
    value = (value or "").strip().lower()
    return value[7:] if value.startswith("sha256:") else value


def slice_pointer(text: str, pointer: str | None) -> str:
    """Return the inclusive 1-based line slice named by a ``#L<start>-L<end>`` pointer."""
    if not pointer:
        return text
    m = _POINTER_RE.match(pointer.strip())
    if not m:
        raise AdaptError(f"unsupported pointer {pointer!r} (expected #L<a> or #L<a>-L<b>)")
    start = int(m.group(1))
    end = int(m.group(2) or start)
    if start < 1 or end < start:
        raise AdaptError(f"pointer {pointer!r} is not a valid 1-based range")
    lines = text.splitlines(keepends=True)
    if end > len(lines):
        raise AdaptError(f"pointer {pointer!r} exceeds the file ({len(lines)} lines)")
    return "".join(lines[start - 1:end])


def load_items(sources: list[dict]) -> tuple[list[dict], list[str]]:
    """Load every pinned source body; verify its digest; hard-fail on anything else."""
    items: list[dict] = []
    verified: list[str] = []
    for src in sources:
        sid = src.get("id") or "<unnamed>"
        path = src.get("path")
        expected = _normalise_digest(src.get("sha256", ""))
        if not path:
            raise AdaptError(f"source {sid!r} has no path")
        if not expected:
            raise AdaptError(f"source {sid!r} has no sha256 to verify against")
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            raise AdaptError(f"source {sid!r} cannot be loaded from {path}: {exc}") from exc
        actual = sha256_bytes(raw)
        if actual != expected:
            raise AdaptError(
                f"source {sid!r} DIGEST MISMATCH at {path}: authored {expected}, measured {actual}"
            )
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AdaptError(f"source {sid!r} at {path} is not UTF-8: {exc}") from exc
        body = slice_pointer(text, src.get("pointer"))
        items.append({
            "id": sid,
            "body": body,
            "source": {"path": path, "pointer": src.get("pointer"),
                       "sha256": "sha256:" + actual},
            "body_sha256": "sha256:" + sha256_text(body),
            "body_bytes": len(body.encode("utf-8")),
        })
        verified.append(f"{sid} sha256:{actual[:16]}")
    return items, verified


def measure_bytes_per_token(items: list[dict]) -> tuple[float, int, int]:
    """Measure bytes-per-token from the loaded bodies (tiktoken cl100k_base, local cache)."""
    import tiktoken

    text = "\n\n".join(it["body"] for it in items)
    nbytes = len(text.encode("utf-8"))
    ntokens = len(tiktoken.get_encoding("cl100k_base").encode(text))
    if nbytes <= 0 or ntokens <= 0:
        raise AdaptError("cannot measure bytes_per_token from empty bodies")
    return round(nbytes / ntokens, 4), nbytes, ntokens


def authored_turn_question(turn: dict) -> str:
    """Authored turns carry ``instruction``; a ``question`` key wins when present."""
    for key in ("question", "instruction"):
        value = turn.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise AdaptError(f"turn {turn.get('turn')!r} carries neither question nor instruction")


def adapt(path: str) -> dict:
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise AdaptError(f"cannot read authored fixture {path}: {exc}") from exc
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdaptError(f"authored fixture {path} is not JSON: {exc}") from exc

    schema = doc.get("schema")
    if schema != AUTHORED_SCHEMA:
        raise AdaptError(
            f"{path}: unsupported authored schema {schema!r} (expected {AUTHORED_SCHEMA!r})"
        )
    task_id = doc.get("task_id")
    if not task_id:
        raise AdaptError(f"{path}: authored fixture has no task_id")
    if not doc.get("sources"):
        raise AdaptError(f"{path}: authored fixture has no sources")
    if not doc.get("turns"):
        raise AdaptError(f"{path}: authored fixture has no turns")

    items, verified = load_items(doc["sources"])

    turns = sorted(doc["turns"], key=lambda t: int(t["turn"]))
    numbered = [int(t["turn"]) for t in turns]
    if numbered != list(range(1, len(turns) + 1)):
        raise AdaptError(f"{path}: authored turns are not numbered 1..{len(turns)}: {numbered[:5]}…")
    n = len(turns)
    if n != max(numbered):
        raise AdaptError(f"{path}: N = len(turns) = {n} but max(turn) = {max(numbered)}")

    runtime_turns = []
    for t in turns:
        entry = {"turn": int(t["turn"]), "question": authored_turn_question(t)}
        if t.get("kind"):
            entry["kind"] = t["kind"]
        runtime_turns.append(entry)

    bpt, nbytes, ntokens = measure_bytes_per_token(items)

    wall_tokens = doc.get("wall_tokens")
    if wall_tokens is None and isinstance(doc.get("long_run"), dict):
        wall_tokens = doc["long_run"].get("wall_tokens")
    stated = wall_tokens is not None
    wall_tokens = int(wall_tokens) if stated else DEFAULT_WALL_TOKENS

    runtime = {
        "schema": RUNTIME_SCHEMA,
        "task_id": task_id,
        "N": n,
        "wall_tokens": wall_tokens,
        "window_tokens": wall_tokens,
        "bytes_per_token": bpt,
        "system_prompt": SYSTEM_PROMPT,
        "items": items,
        "turns": runtime_turns,
        "checkpoints": doc.get("checkpoints", []),
        "acceptance": doc.get("acceptance", {}),
        "repair": doc.get("repair", {}),
        "expected": doc.get("expected", {}),
        "derived_from": {"path": os.path.abspath(path), "sha256": sha256_bytes(raw)},
        "adaptation": {
            "adapter": "experiments/ptr-engine/longrun/adapt_fixture.py",
            "authored_schema": AUTHORED_SCHEMA,
            "bytes_per_token_method": "tiktoken cl100k_base tokens over the loaded item bodies",
            "body_bytes": nbytes,
            "body_tokens": ntokens,
            "wall_tokens_default_used": not stated,
            "wall_tokens_default": DEFAULT_WALL_TOKENS,
            "turn_field_mapped": "instruction -> question",
            "sources_verified": verified,
        },
    }
    return runtime


def runtime_path(out_dir: str, task_id: str) -> str:
    return os.path.join(out_dir, f"{task_id}.json")


def write_runtime(runtime: dict, out_dir: str) -> tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    path = runtime_path(out_dir, runtime["task_id"])
    data = json.dumps(runtime, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data)
    return path, sha256_text(data)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all", action="store_true", help="adapt every authored fixture")
    ap.add_argument("--fixture", action="append", default=None,
                    help="authored fixture to adapt (repeatable)")
    ap.add_argument("--fixture-dir", default=DEFAULT_FIXTURE_DIR)
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)

    if args.all:
        paths = sorted(
            os.path.join(args.fixture_dir, name)
            for name in os.listdir(args.fixture_dir)
            if re.match(r"^LR-\d+.*\.json$", name)
        )
    elif args.fixture:
        paths = list(args.fixture)
    else:
        ap.error("give --all or --fixture PATH")
        return 2

    if not paths:
        print(f"no authored fixtures found in {args.fixture_dir}", file=sys.stderr)
        return 2

    rc = 0
    for path in paths:
        try:
            runtime = adapt(path)
        except AdaptError as exc:
            print(f"ADAPT FAILED {path}: {exc}", file=sys.stderr)
            rc = 1
            continue
        out, sha = write_runtime(runtime, args.out_dir)
        a = runtime["adaptation"]
        print(f"{out}  sha256:{sha}")
        print(f"  task_id={runtime['task_id']} N={runtime['N']} items={len(runtime['items'])} "
              f"wall_tokens={runtime['wall_tokens']} "
              f"bytes_per_token={runtime['bytes_per_token']} "
              f"(from {a['body_bytes']} B / {a['body_tokens']} tok) "
              f"derived_from=sha256:{runtime['derived_from']['sha256'][:16]}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
