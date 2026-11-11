#!/usr/bin/env python3
"""run_longrun.py — turn driver for the long-run arms (LONGRUN-PREREG §1-§6).

One invocation runs one (task x arm x rep) cell (or a list of arms) against an
OpenAI-compatible endpoint and appends ONE NDJSON row per request-turn to
``experiments/ptr-engine/measure/rows-longrun-<date>.jsonl``.  It never scores:
checkpoint answers are recorded raw and the scorer judges them.

Arms (exactly as LONGRUN-PREREG §1):
  transcript-grow     replay the whole history every turn; FIFO-truncate from the
                      front once the declared 64,000-token cap is crossed.
  transcript-compact  same replay, but at the cap the older turns are replaced by a
                      ~700-token digest (one extra digest request per wall); the recent
                      4 turns stay raw.
  pointer-stable      byte-identical frozen index prefix, bodies appended after it in
                      the suffix (one new body per turn, prefetched one turn ahead),
                      tail = short state line + current question.  Nothing before the
                      tail is ever rewritten.
  lease-reopen        close at the wall and reopen a fresh session carrying only the
                      frozen pointer index + a host-distilled state line (<=400 tok).
                      Reopens are host-side; only the turn itself is a request.

Fixture schema ``consonance.longrun-fixture/1`` (the real fixture is card 2a6c4761's
deliverable; the stub tree carries only ``{"stub": true}`` and is refused):
  {schema, task_id, N, window_tokens, wall_tokens, bytes_per_token, system_prompt,
   items:[{id, body, fact?}], turns:[{turn, question, note?{id,body}, checkpoint?}],
   lease_reopen_turns?:[23,56]}

Null semantics: ``normalize_cached_tokens`` below is the ONE place that decides what a
missing ``cached_tokens`` means, per RECORD.md "Endpoint null semantics settled"
(SGLang omits the key when it is 0 => 0; vLLM null is preserved as null).

Dry-run is fully offline: it writes the frozen manifest(s), prints the first three
request bodies per arm (byte count + sha256, exact bytes in the preview files), the
request count it would send, and exits 0.  It sends nothing and writes no row file.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import inspect
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from math import ceil
from typing import Optional, List

# ANSWER-CONTRACT (v5): the parser is grade_v5's own function, imported - never a
# second implementation. Same directory, stdlib only, no request, no model.
_LONGRUN_HERE = os.path.dirname(os.path.abspath(__file__))
# The repo root, anchored to THIS file rather than to the process cwd.  The
# manifest default below is a repo-root-relative path; resolving it against cwd
# meant a dry-run started from ``experiments/ptr-engine`` wrote its manifests to
# ``experiments/ptr-engine/experiments/ptr-engine/longrun/manifests/`` -- a stray
# tree that looked like evidence and was not.  Same class of bug as the preview
# hazard (docs/STATE.md §6 item 13): a default path that silently depends on cwd.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_LONGRUN_HERE)))
if _LONGRUN_HERE not in sys.path:
    sys.path.insert(0, _LONGRUN_HERE)
from grade_v5 import parse_answer_contract  # noqa: E402
import claim_mode  # noqa: E402  CLAIM-ROW-STAMP: the one claim resolver
import arm_cd  # noqa: E402  arms C and D logic
_PTR_ENGINE_ROOT = os.path.dirname(_LONGRUN_HERE)
if _PTR_ENGINE_ROOT not in sys.path:
    sys.path.insert(0, _PTR_ENGINE_ROOT)
from ptr_engine.pointer_table import make_ref  # noqa: E402
from ptr_engine.fetch_tool import extract_marker_refs  # noqa: E402
from ptr_engine.layers import COMPACT_EVERY  # noqa: E402

# STREAMING (WIRE-CLIENT): the ONE streaming implementation. Imported as a module, not
# as bare names, so the measured path provably calls client.send_chat and a test can
# monkeypatch that exact function to prove the client is on the path.
import client  # noqa: E402

ARMS = ("transcript-grow", "transcript-compact", "pointer-stable", "lease-reopen", "masking-no-fetch", "bounded-context-fetch", "spcc", "pinned", "pinned-recency")
DEFAULT_BASE_URL = "http://192.168.2.168:8012/v1"
DEFAULT_MODEL = "occamy-1.0-NVFP4"
DEFAULT_ENGINE = "sglang"

PREDICTIONS = {
    "transcript-grow": ("P2: A's tokens-to-verified-success >= 1.5x C's; at N=60 it hits the "
                        "window/cap and repairs from a front-truncated prefix."),
    "transcript-compact": ("P4: B lands within 2x of C on p95 TTFT but fails t30 where its "
                           "digest dropped the turn-2 code."),
    "pointer-stable": ("P1: C's p95 TTFT <= 0.5x A's, cached share >= 0.80 after turn 12; "
                       "P2: A's tokens-to-verified-success >= 1.5x C's."),
    "lease-reopen": ("P3: D has the lowest p95 TTFT but loses t30/t60 accuracy unless the "
                     "<=400-token state line carries the turn-2 fact and the turn-24 correction."),
    "masking-no-fetch": ("C: masking without fetch; masked bodies recoverable only via pointer."),
    "bounded-context-fetch": ("D: bounded-recoverable with fetch; 2 requests per turn."),
    "spcc": ("Stable-prefix compiler: byte-stable L0+L1 prefix, append-only L2 journal, "
             "scheduled compaction every 24 turns, fetch into L3 only."),
    "pinned": ("E7 D: drop the journal, record the fold in PINS; PLAN + facts pinned in the "
               "cached prefix, no recency line. Predictions: D < A on cost by ~2x (no summary "
               "call), D has the lowest refetch_count, D >= A on accuracy."),
    "pinned-recency": ("E7 E: D plus the two-tier todo's ACTIVE line rewritten into L3 every "
                       "turn. Prediction: E ~= D on cost, E >= D on accuracy; if E's accuracy "
                       "does not beat D's beyond the noise band, the todo is not worth its "
                       "tokens."),
}


# --------------------------------------------------------------------------- util
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def est_tokens(text: str, bytes_per_token: float) -> int:
    return ceil(len(text.encode("utf-8")) / float(bytes_per_token))


# ------------------------------------------------------------------- null semantics
def normalize_cached_tokens(raw_cached, engine: str):
    """THE null-semantics function — the only place a missing ``cached_tokens`` is decided.

    RECORD.md, "Endpoint null semantics settled 2026-10-26": SGLang *returns
    prompt_tokens_details but omits cached_tokens when it is 0*, so a null there is a
    measured zero; on vLLM the detail object is null and no cache counter exists, so a
    null is preserved as null and must never be imputed as 0.

    SGLang: None -> 0.   vLLM: None -> None.   Anything else: refuse to guess.
    """
    if raw_cached is not None:
        return int(raw_cached)
    if engine == "sglang":
        return 0
    if engine == "vllm":
        return None
    raise ValueError(f"no null semantics declared for engine={engine!r} (expected sglang|vllm)")


# ------------------------------------------------------------------------ fixture
class FixtureError(RuntimeError):
    pass


def load_fixture(path: str) -> dict:
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise FixtureError(f"cannot read fixture {path}: {exc}") from exc
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureError(f"fixture {path} is not JSON: {exc}") from exc
    if doc.get("stub") or not doc.get("items"):
        raise FixtureError(
            f"fixture {path} is a STUB (no items/turns). The real fixture tree is card "
            "2a6c4761's deliverable; use a constructed fixture with --fixture."
        )
    for key in ("schema", "task_id", "N", "bytes_per_token", "system_prompt",
                "items", "turns"):
        if key not in doc:
            raise FixtureError(f"fixture {path} missing required key {key!r}")
    # WALL-KEY: the wall may be declared per arm instead of once at top level. A fixture
    # that declares neither is unlaunchable; one that declares ONLY `wall_tokens_by_arm`
    # is complete (the top-level key is a legacy/cross-arm hint, not a requirement).
    if "wall_tokens" not in doc and not (isinstance(doc.get("wall_tokens_by_arm"), dict)
                                        and doc["wall_tokens_by_arm"]):
        raise FixtureError(f"fixture {path} declares neither 'wall_tokens' nor a non-empty "
                           "'wall_tokens_by_arm' — no arm has a wall")

    if doc["schema"] not in ("consonance.longrun-fixture/1", "consonance.longrun-fixture/2"):
        raise FixtureError(f"unsupported fixture schema {doc['schema']!r}")
    if not doc["items"] or not all({"id", "body"} <= set(it) for it in doc["items"]):
        raise FixtureError("fixture items must be non-empty {id, body} objects")

    # v2 pointer-field validation (when present). v1 fixtures omit these.
    documents = doc.get("documents", None)
    if documents is not None:
        if not isinstance(documents, list) or not documents:
            raise FixtureError("fixture documents must be a non-empty list")
        doc_map = {}
        for d in documents:
            if not isinstance(d, dict) or "doc_id" not in d:
                raise FixtureError("fixture document missing doc_id")
            did = d["doc_id"]
            if did in doc_map:
                raise FixtureError(f"duplicate document doc_id {did!r}")
            doc_map[did] = d
            scope = d.get("scope", "granted")
            if scope not in ("granted", "ungranted"):
                raise FixtureError(f"document {did!r} has invalid scope {scope!r}")
            revoked = bool(d.get("revoked", False))
            revoked_at = d.get("revoked_at_turn", None)
            if revoked:
                if not isinstance(revoked_at, int) or isinstance(revoked_at, bool):
                    raise FixtureError(f"document {did!r} revoked but revoked_at_turn is not an int (turn {revoked_at!r})")
            else:
                if revoked_at is not None:
                    raise FixtureError(f"document {did!r} revoked_at_turn set but revoked is false (turn {revoked_at!r})")
            revs = d.get("revisions")
            if not isinstance(revs, list) or not revs:
                raise FixtureError(f"document {did!r} revisions must be a non-empty list")
            seen_rev = set()
            for r in revs:
                if not isinstance(r, dict):
                    raise FixtureError(f"document {did!r} revision entry not an object")
                if "revision" not in r:
                    raise FixtureError(f"document {did!r} revision missing 'revision'")
                try:
                    rnum = int(r["revision"])
                except (TypeError, ValueError):
                    raise FixtureError(f"document {did!r} revision {r['revision']!r} is not an int")
                if rnum in seen_rev:
                    raise FixtureError(f"document {did!r} duplicate revision {rnum}")
                seen_rev.add(rnum)
                if "live_from_turn" in r:
                    try:
                        int(r["live_from_turn"])
                    except (TypeError, ValueError):
                        raise FixtureError(f"document {did!r} revision {rnum} live_from_turn not an int")
        # revision_schedule consistency
        sched = doc.get("revision_schedule", None)
        if isinstance(sched, list):
            for entry in sched:
                if not isinstance(entry, dict):
                    raise FixtureError("revision_schedule entry not an object")
                try:
                    sturn = int(entry["turn"])
                except (TypeError, ValueError):
                    raise FixtureError(f"revision_schedule turn {entry.get('turn')!r} is not an int")
                sdoc = entry.get("doc")
                if sdoc not in doc_map:
                    raise FixtureError(f"revision_schedule turn {sturn} references unknown doc {sdoc!r}")
                new_rev = entry.get("new_revision", None)
                ddoc = doc_map[sdoc]
                if new_rev is None:
                    # revoke turn must match document revoked_at_turn
                    if not bool(ddoc.get("revoked", False)):
                        raise FixtureError(f"revision_schedule turn {sturn} revokes {sdoc!r} but document is not revoked")
                    if int(ddoc.get("revoked_at_turn")) != sturn:
                        raise FixtureError(f"inconsistent revoke turn for document {sdoc!r}: revoked_at_turn={ddoc.get('revoked_at_turn')!r} vs schedule turn {sturn}")
                else:
                    try:
                        nrev = int(new_rev)
                    except (TypeError, ValueError):
                        raise FixtureError(f"revision_schedule turn {sturn} new_revision {new_rev!r} is not an int")
                    rev_obj = next((r for r in (ddoc.get("revisions") or []) if int(r.get("revision")) == nrev), None)
                    if rev_obj is None:
                        raise FixtureError(f"revision_schedule turn {sturn} references unknown revision {nrev} of {sdoc!r}")
                    if "live_from_turn" in rev_obj and int(rev_obj["live_from_turn"]) != sturn:
                        raise FixtureError(f"inconsistent revive turn for document {sdoc!r} revision {nrev}: live_from_turn={rev_obj.get('live_from_turn')!r} vs schedule turn {sturn}")
        # fetch_scenarios expected_outcome consistency
        scenarios = doc.get("fetch_scenarios", None)
        if isinstance(scenarios, list):
            for s in scenarios:
                if not isinstance(s, dict):
                    continue
                ref = s.get("ref")
                exp = s.get("expected_outcome")
                if not isinstance(ref, str):
                    continue
                did = ref.split("@", 1)[0]
                if did not in doc_map:
                    if exp != "NOT_FOUND":
                        raise FixtureError(f"fetch_scenarios ref {ref!r} expected_outcome {exp!r} inconsistent with document {did!r} (unknown)")
                    continue
                ddoc = doc_map[did]
                scope = ddoc.get("scope", "granted")
                revoked = bool(ddoc.get("revoked", False))
                if scope != "granted":
                    if exp != "SCOPE_UNGRANTED":
                        raise FixtureError(f"fetch_scenarios ref {ref!r} expected_outcome {exp!r} inconsistent with document {did!r} scope {scope!r}")
                elif revoked:
                    if exp != "STALE_OR_REVOKED":
                        raise FixtureError(f"fetch_scenarios ref {ref!r} expected_outcome {exp!r} inconsistent with document {did!r} revoked")
                else:
                    if exp not in ("OK", "STALE_OR_REVOKED"):
                        raise FixtureError(f"fetch_scenarios ref {ref!r} expected_outcome {exp!r} inconsistent with document {did!r}")
    # tool_outputs validation against documents
    for turn in doc["turns"]:
        tos = turn.get("tool_outputs", None)
        if tos is None:
            continue
        if not isinstance(tos, list):
            raise FixtureError(f"fixture turn {turn['turn']} tool_outputs is not a list")
        if documents is None:
            raise FixtureError(f"fixture turn {turn['turn']} has tool_outputs but no documents")
        for to in tos:
            if not isinstance(to, dict):
                raise FixtureError(f"fixture turn {turn['turn']} tool_outputs entry not an object")
            did = to.get("doc_id")
            if did not in doc_map:
                raise FixtureError(f"fixture turn {turn['turn']} tool_outputs references unknown doc_id {did!r}")
            try:
                rev = int(to.get("revision"))
            except (TypeError, ValueError):
                raise FixtureError(f"fixture turn {turn['turn']} tool_outputs revision {to.get('revision')!r} is not an int")
            ddoc = doc_map[did]
            revs = [int(r.get("revision")) for r in (ddoc.get("revisions") or []) if "revision" in r]
            if rev not in revs:
                raise FixtureError(f"fixture turn {turn['turn']} tool_outputs revision {rev} not in document {did!r} revisions {revs}")
            if "body" in to:
                rev_obj = next((r for r in (ddoc.get("revisions") or []) if int(r.get("revision")) == rev), None)
                if rev_obj is not None and "value" in rev_obj and str(to.get("body")) != str(rev_obj.get("value")):
                    raise FixtureError(f"fixture turn {turn['turn']} tool_outputs body != revision value for {did!r}@{rev}")
            if "doc_id" not in to or "revision" not in to or "body" not in to:
                raise FixtureError(f"fixture turn {turn['turn']} tool_outputs entry missing doc_id/revision/body")
    turns = sorted(doc["turns"], key=lambda t: int(t["turn"]))
    if [int(t["turn"]) for t in turns] != list(range(1, int(doc["N"]) + 1)):
        raise FixtureError("fixture turns must be numbered 1..N contiguously")
    for t in turns:
        if not isinstance(t.get("question"), str) or not t["question"]:
            raise FixtureError(f"fixture turn {t['turn']} has no question")
    doc["turns"] = turns
    try:
        from ptr_engine.pointer_table import reset_bodies
    except ImportError:
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from ptr_engine.pointer_table import reset_bodies
    reset_bodies(doc.get("task_id"))
    doc["_path"] = os.path.abspath(path)
    doc["_sha256"] = sha256_bytes(raw)
    return doc


def resolve_fixture_path(task: str) -> str | None:
    """Resolve a fixture path for a task id, searching the longrun tree.

    Returns the first candidate whose loaded ``task_id`` equals ``task``, or None.
    Search order: the canonical fixtures dir, then any tasks-* tree.
    """
    import glob as _glob
    here = os.path.dirname(os.path.abspath(__file__))
    candidates: list[str] = []
    # canonical flat fixture
    flat = os.path.join(here, "fixtures", str(task) + ".json")
    if os.path.exists(flat):
        candidates.append(flat)
    # any tasks-* tree
    for pat in ("tasks-*/*.json", "tasks-*/*/*.json", "tasks-*/*/*/*.json"):
        candidates.extend(sorted(_glob.glob(os.path.join(here, pat))))
    # filter by basename-ish and task_id
    matches = []
    for c in candidates:
        base = os.path.basename(c)
        if str(task) not in base:
            continue
        try:
            d = json.loads(open(c, encoding="utf-8").read())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(d, dict) and d.get("task_id") == task:
            matches.append(c)
    if not matches:
        return None
    # prefer the flat fixtures path, then shortest path
    matches.sort(key=lambda x: (0 if "/fixtures/" in x else 1, len(x)))
    return matches[0]


def index_lines(fixture: dict) -> str:
    """Frozen pointer index: fetchable ref, hash8, body length — no fact values.

    INDEX-REF-COHERENCE (U-SPCC-55): the refs are the ones the fetch tool
    accepts (``make_ref`` form, ``doc-<name>@r<rev>``), derived from the same
    pointer entries the fetch table is built from, so the index cannot
    advertise a ref that resolves to NOT_FOUND.  The SPCC arm's L1 is built by
    ``arm_cd.spcc_world_index`` from the same helper, so both arms read the
    same index.
    """
    return "\n".join(arm_cd.world_index_lines(fixture)) + "\n"


def body_block(item: dict) -> str:
    return f"BODY {item['id']} ({len(item['body'].encode('utf-8'))} B)\n{item['body']}\n"


def working_set_block(fixture: dict) -> str:
    bodies = "\n".join(body_block(it) for it in fixture["items"])
    return f"WORKING SET\nINDEX\n{index_lines(fixture)}\n{bodies}"


def _turn_tool_outputs(turn: dict) -> list:
    if not isinstance(turn, dict):
        return []
    tos = turn.get("tool_outputs")
    if not isinstance(tos, list):
        return []
    return [to for to in tos if isinstance(to, dict)]


def turn_user(t: int, turn: dict) -> str:
    text = ""
    note = turn.get("note")
    if note:
        text += f"[WORK NOTE {note.get('id', 'n' + str(t))}]\n{note['body']}\n"
    return text + f"QUESTION (T{t}): {turn['question']}"


def turn_block(t: int, turn: dict, answer: str, masked: bool = False,
               mask: bool = False, markers: Optional[List[str]] = None) -> str:
    """Render one turn. Tool-output bodies are part of the turn.

    Unmasked: each declared tool_output body is rendered (so a transcript arm
    sees the real tool output). Masked: each body is replaced in place by its
    pointer marker (short form ``[MASKED <ref>]``); question and answer survive
    verbatim and no body text remains.
    """
    masked = bool(masked or mask)
    base = turn_user(t, turn)
    tos = _turn_tool_outputs(turn)
    out_lines = [base]
    if tos:
        out_lines.append("TOOL OUTPUTS:")
        if markers is None:
            markers = []
            for to in tos:
                did = to.get("doc_id")
                rev = to.get("revision")
                if rev is None:
                    raise ValueError("tool_output missing required field: revision")
                markers.append(f"[MASKED {make_ref(did, rev)}]")
        for idx, to in enumerate(tos):
            if masked:
                m = markers[idx] if (isinstance(markers, list) and idx < len(markers)) else markers
                out_lines.append(str(m))
            else:
                out_lines.append(f"TOOL_OUTPUT ({to.get('doc_id')}@{to.get('revision')}): {to.get('body')}")
    out_lines.append(f"ANSWER (T{t}): {answer}")
    return "\n".join(out_lines)


# ------------------------------------------------------------------- tool channel
# OPT-IN, bounded `read_file` fetch channel (FETCH-CHANNEL).
# DEFAULT OFF: with `--tools` absent (or empty) none of the code below executes, no
# key is added to any row or manifest, and every request body is byte-identical to
# the runs recorded before this flag existed.  The channel exists because the
# pointer arms emit `<tool_call>…read_file…` and nothing ever served it
# (RUN-V4-GRID checkpoint 3, arm pointer-stable): the designed resolution path —
# pointer plus on-demand fetch — is what this implements.
TOOL_READ_CAP_LINES = 200
TOOL_READ_CAP_CHARS = 8000
TOOL_CALLS_PER_TURN = 2
# 8 was arbitrary and starved the checkpoint: the counted rounds were spent on turns
# 1-30, so the CP3 fetch the probe exists to test was refused 16 turns later
# (PROBE-CP3-FETCH census: fetch_budget_exhausted 136).  The real bound is the card's
# request budget; `budget` adds this cap on a --tools run only (--tools off is
# untouched) and `requests_spent = turn requests + follow-ups actually spent`.
# RUNNER-ROUNDS-48: the per-arm pool is PROVISIONING, not a behavioural bound.  v5 spent
# all 24 rounds inside turn 3 (one recon burst) and starved the T46 checkpoint, so the
# pool is one round per turn across the 48-turn cell (48) while the per-turn cap (3) is
# what actually bounds an ambitious model.  Overridable: --fetch-rounds-per-arm.
TOOL_FETCH_ROUNDS_PER_ARM = 48
# (b) PROBE-CP3-V6: ONE TURN MUST NOT CONSUME THE CELL.  PROBE-CP3-V5 spent all 24 rounds
# inside turn 3 (21 rounds in a single recon burst), which refused the T46 checkpoint read
# host-side (`fetch_budget_exhausted`) with no <tool_result> and no follow-up.  At most
# TOOL_FETCH_ROUNDS_PER_TURN fetch rounds are bought per turn; `--fetch-rounds-per-turn`
# overrides it, and the value is frozen in the manifest and stamped on every row.
TOOL_FETCH_ROUNDS_PER_TURN = 3
# (a) PROBE-CP3-V6: DO NOT PAY FOR LINES THAT ARE ALREADY IN THE PROMPT.  The pointer arm
# pins the full body of the items its index points at, then asks `read_file` for a range
# inside one of those very bodies.  Such a call is served from the pinned body:
# `served_from="prompt"`, no disk read, and NO BILLED ROUND — the round budget stays for
# the fetches that genuinely need it.  A flag rather than a code path so the offline test
# can prove the red-before-green (see tests/test_tool_channel3.py).
TOOL_SERVE_FROM_PROMPT = True
# STAGE-2-GREP: the episode loop's second tool.  `read_file` alone makes a lost journal
# repairable only by re-reading, which inflates the re-fetch rate the design measures
# (docs/AGENTIC-COMPACTION-AB.md §3.2); a bounded `grep` makes re-fetch a realistic
# choice and its cost the quantity E7 claims.  The bounds are constants here so the
# parser, the executor and the row record cannot drift apart.
TOOL_NAMES = ("read_file", "grep")
GREP_TOOL_NAME = "grep"
GREP_DEFAULT_GLOB = "*.py"
GREP_MAX_HITS = 20
GREP_MAX_PATTERN_CHARS = 200
GREP_MAX_LINE_CHARS = 200
#: Directories the grep walk never descends into.  `state/` holds run artefacts (row
#: files, snapshots, logs), not source: searching it would let a task's own evidence
#: answer the task.  `.venv`/`node_modules` are installed third-party bytes, not the
#: repository: leaving them in would make a hit list depend on whether a virtualenv
#: happens to exist under the root, which is a reproducibility hazard, not a feature.
GREP_SKIP_DIRS = (".git", "__pycache__", "state", ".venv", "node_modules")
# FETCH-CHANNEL path bases.  The arm emits `ptr_engine/resolve.py` — the string its own
# fixture index uses — which does not exist under the workspace root, so every
# well-formed call was refused `path_not_found` (54 of 68 rows).  A path now resolves
# under the workspace root first, then under the engine root, and the matching base is
# reported in the <tool_result base="workspace|engine"> attribute.
ENGINE_ROOT_REL = "experiments/ptr-engine"

_SECRET_BASENAMES = (".env", ".netrc")
_SECRET_PREFIXES = (".env.", "id_rsa", "id_ed25519", "id_dsa", "id_ecdsa")
_SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
_SECRET_STEMS = ("credentials", "secrets", "secret", "keys", "clients")


def tool_names(cfg) -> list[str]:
    """The run's declared tool list — one implementation, in the body-building client.

    TOOL-CHANNEL-WIRE: ``client.tools_enabled`` gates the ``tools`` member on the wire, so
    the runner's own gate must be the SAME predicate; two copies is how the label and the
    wire drifted apart in the first place.
    """
    return client.tool_names(cfg)


def tools_enabled(cfg) -> bool:
    return client.tools_enabled(cfg)


def fetch_tools_enabled(cfg) -> bool:
    return client.fetch_tools_enabled(cfg)


def fetch_rounds_per_turn(cfg) -> int:
    """(b) The per-turn fetch-round cap in force for this run: 0 means unbounded."""
    val = getattr(cfg, "fetch_rounds_per_turn", None)
    try:
        val = int(val)
    except (TypeError, ValueError):
        val = TOOL_FETCH_ROUNDS_PER_TURN
    return val if val >= 0 else TOOL_FETCH_ROUNDS_PER_TURN


def fetch_rounds_per_arm(cfg) -> int:
    """(RUNNER-ROUNDS-48) The per-arm fetch-round pool in force: --fetch-rounds-per-arm.

    Defaults to TOOL_FETCH_ROUNDS_PER_ARM (48).  One flag, one pool: this single value
    prices the projection (`projected_requests`), caps the channel (`fetch_rounds`, the
    `fetch_budget_exhausted` refusal) and is frozen in the manifest.  A non-positive
    value never reaches here: `main()` refuses it by name before any request, so this
    resolver only ever returns a positive integer.
    """
    val = getattr(cfg, "fetch_rounds_per_arm", None)
    try:
        val = int(val)
    except (TypeError, ValueError):
        val = TOOL_FETCH_ROUNDS_PER_ARM
    return val if val > 0 else TOOL_FETCH_ROUNDS_PER_ARM


class BudgetExhausted(RuntimeError):
    """A fetch follow-up would exceed the request budget."""


# ------------------------------------------------------------- REQUEST CAP GATE
# WIRE-CAP-GATE.  REQUEST-LEDGER owns the counting rule, and its `known_limit` was
# honest: a gate that reads rows on disk sees a request only AFTER the writer recorded
# it, so it buys detection, not prevention.  This class closes that hole with the
# record -> gate -> send ordering the ledger's conductor_wiring asked for:
#
#   * rows are read from disk ONCE, at run start (that is where the money already spent
#     lives); `spent_at_start` is that total;
#   * from then on the authority is an IN-MEMORY count.  `acquire()` reserves the next
#     request's slot BEFORE anything is sent, so the decision never depends on the row
#     writer having flushed, and a run that would exceed the declared allocation or the
#     global cap refuses here -- no socket, no row;
#   * the counting rule itself is NOT re-implemented: request_ledger.build_report() is
#     called, and its RULE is copied into the manifest so the two can be compared.
#
# Exit codes propagate unmodified out of run_cell -> main -> sys.exit: 4 (would exceed),
# 3 (usage / no rows), 5 (unreadable row file, nothing counted).  9 is reserved for a
# reconciliation divergence (a BUG: the run's count and the rows disagree).
DEFAULT_CAP_PATTERN = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "measure", "rows-*.jsonl")
CAP_GATE_SCHEMA = "consonance.longrun-cap-gate/1"
EXIT_CAP_DIVERGENCE = 9
# TREATMENTS: a launch whose treatment cannot fire inside the frozen horizon is refused
# BEFORE the first request.  8 was unused by every other exit path (2 usage, 3 manifest,
# 4 budget/turn failure, 5 rows unreadable, 6 runaway, 7 cell gate, 9 cap divergence).
EXIT_TREATMENTS_UNREACHABLE = 3   # = exit 3 "the run did not start"; already in RUNNER_CODES
HORIZON_TURNS = 48          # PARM-1 line 137 -- frozen; never a --flag, never raised
DIGEST_MAX_TOKENS = 700     # the COMPRESS instruction's own ceiling (compact arm, build())


class CapRefusal(RuntimeError):
    """A request would exceed the run allocation or the global cap -- nothing sent."""

    def __init__(self, message: str, gate=None):
        super().__init__(message)
        self.gate = gate


class CapUsageError(RuntimeError):
    """The gate cannot be constructed (bad flags) -- exit 3, the run does not start."""


class CapRowsUnreadable(RuntimeError):
    """A row file is unreadable, so the spent total is unknowable -- exit 5."""


def load_request_ledger(path: str | None = None):
    """Import the module that OWNS the counting rule.  Never a second copy of it."""
    import importlib.util

    target = (path or os.environ.get("REQUEST_LEDGER_TOOL")
              or os.path.join(_LONGRUN_HERE, "..", "tools", "request_ledger.py"))
    target = os.path.abspath(target)
    spec = importlib.util.spec_from_file_location("ptr_request_ledger", target)
    if spec is None or spec.loader is None:
        raise CapUsageError(f"cannot import the request ledger at {target}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except OSError as exc:
        raise CapUsageError(f"cannot import the request ledger at {target}: {exc}") from exc
    return module


class RequestCapGate:
    """Per-request brake: one in-memory authority, decided before the send."""

    def __init__(self, ledger, paths, cap: int, reserve: int, allocation,
                 own_rows: str | None = None, ceiling: int | None = None,
                 run_counter: dict | None = None):
        self.ledger = ledger
        self.paths = list(dict.fromkeys(os.path.abspath(p) for p in paths))
        # the run's OWN row file, added to the exit scan once the writer has created it
        self.own_rows = os.path.abspath(own_rows) if own_rows else None
        self.cap = int(cap)
        self.reserve = int(reserve)
        self.allocation = allocation
        # PREREG-CEILING-ON-THE-BRAKE (U-SPCC-40): the ceiling the declared claim was
        # admitted under, enforced on ACTUAL sends.  ``run_counter`` is the run-scoped
        # send tally shared by every cell of the run, so the ceiling is a RUN budget
        # (the scope PREREG-SPCC states it in), not a per-cell one that three arms could
        # each spend in full.  ``None`` ceiling = no prereg claim: nothing changes.
        self.ceiling = None if ceiling is None else int(ceiling)
        self.run_counter = run_counter if run_counter is not None else {"n": 0}
        if self.cap < 0 or self.reserve < 0 or (allocation is not None and allocation < 0):
            raise CapUsageError("--budget-cap, --budget-reserve and --request-allocation "
                                "must all be >= 0")
        if self.reserve > self.cap:
            raise CapUsageError(f"--budget-reserve {self.reserve} exceeds --budget-cap "
                                f"{self.cap} (no headroom exists)")
        self.headroom = self.cap - self.reserve
        self.spent_at_start = self._scan_total()
        self.used_in_run = 0

    # -- counting ----------------------------------------------------------------
    def _scan_total(self) -> int:
        try:
            report = self.ledger.build_report(self.paths, self.cap, self.reserve, 0)
        except self.ledger.RowsUnreadable as exc:
            raise CapRowsUnreadable(str(exc)) from exc
        return int(report["budget"]["spent"])

    def acquire(self, turn: int, kind: str = "turn") -> int:
        """Reserve one request slot BEFORE it is sent, or refuse (exit 4).

        Raising here is the whole point: the caller has not called send_chat yet, so a
        refusal writes no row and opens no socket.
        """
        would = self.used_in_run + 1
        spent = self.spent_at_start + self.used_in_run
        projected = spent + 1
        over_cap = projected > self.headroom
        over_alloc = self.allocation is not None and would > self.allocation
        run_sends = int(self.run_counter.get("n", 0))
        over_ceiling = self.ceiling is not None and (run_sends + 1) > self.ceiling
        if over_cap or over_alloc or over_ceiling:
            limits = ", ".join(name for name, hit in
                               (("global cap", over_cap), ("run allocation", over_alloc),
                                ("prereg request ceiling", over_ceiling)) if hit)
            over_by = (projected - self.headroom if over_cap
                       else run_sends + 1 - self.ceiling if over_ceiling
                       else would - int(self.allocation))
            raise CapRefusal(
                f"CAP REFUSED at T{turn} ({kind}) — over the {limits}: "
                f"spent={spent} would_spend={would} cap={self.cap} reserve={self.reserve} "
                f"headroom={self.headroom} allocation={self.allocation} "
                f"prereg_ceiling={self.ceiling} run_sends={run_sends} "
                f"used_in_run={self.used_in_run} turn={turn} kind={kind} "
                f"projected={projected} over_by={over_by} — nothing sent",
                self)
        self.used_in_run += 1
        self.run_counter["n"] = run_sends + 1
        return would

    # -- exit accounting ---------------------------------------------------------
    def _exit_paths(self) -> list[str]:
        paths = list(self.paths)
        if self.own_rows and os.path.exists(self.own_rows) and self.own_rows not in paths:
            paths.append(self.own_rows)
        return paths

    def reconcile(self) -> dict:
        """Re-read the rows: the run's own count must equal what the disk now says."""
        try:
            report = self.ledger.build_report(self._exit_paths(), self.cap, self.reserve, 0)
        except self.ledger.RowsUnreadable as exc:
            raise CapRowsUnreadable(str(exc)) from exc
        after = int(report["budget"]["spent"])
        expected = self.spent_at_start + self.used_in_run
        return {"spent_at_start": self.spent_at_start, "used_in_run": self.used_in_run,
                "spent_after": after, "expected": expected, "delta": after - expected}

    def manifest_block(self, reconciled: dict | None = None) -> dict:
        return {
            "schema": CAP_GATE_SCHEMA,
            "ordering": "record->gate->send: the slot is reserved BEFORE the request is issued",
            "counting_rule": getattr(self.ledger, "RULE", None),
            "cap": self.cap,
            "reserve": self.reserve,
            "headroom": self.headroom,
            "spent_at_start": self.spent_at_start,
            "allocation": self.allocation,
            "prereg_ceiling": self.ceiling,
            "run_sends": int(self.run_counter.get("n", 0)),
            # written before the first request (None) and again at exit (the count).
            "used_in_run": None if reconciled is None else self.used_in_run,
            "final_used_in_run": None if reconciled is None else self.used_in_run,
            "running_count": self.used_in_run,
            "reconcile": reconciled,
            "counted_files": [os.path.basename(p) for p in self.paths],
            "own_rows_file": os.path.basename(self.own_rows) if self.own_rows else None,
        }


def cell_turns(cfg, fixture: dict) -> int:
    """THE cell's turn scope: the fixture's N, cut to `--max-turns` when one is declared.

    ONE definition, read by every path that has to know how many turns the cell would
    execute: `projected_requests` (the price), `run_cell` (the live loop) and `run_dry`
    (the offline preview).  RUN-DRY-TURN-SCOPE: the preview used to loop
    `range(1, int(fixture["N"]) + 1)` and count `int(fixture["N"])`, so a 12-turn cell was
    priced at the fixture's 48 and the shortened cell could never be gated.  A second
    `min()` inside the preview is the bug, not the fix: the preview is computed over
    exactly the turns the run would execute.
    """
    n_turns = int(fixture["N"])
    max_turns = int(getattr(cfg, "max_turns", 0) or 0)
    if max_turns > 0:
        n_turns = min(n_turns, max_turns)
    return n_turns


def projected_requests(cfg, fixture: dict, arm: str) -> int:
    """The cell's request projection: turn requests + digests + the fetch-round pool."""
    n_turns = cell_turns(cfg, fixture)
    budget = n_turns + (expected_digests(fixture) if arm == "transcript-compact" else 0)
    if tools_enabled(cfg):
        budget += fetch_rounds_per_arm(cfg)
    return budget


def allocation_for(cfg, fixture: dict, arm: str):
    """`--request-allocation N` or the string 'projection' (the default)."""
    raw = getattr(cfg, "request_allocation", "projection")
    if raw is None or (isinstance(raw, str) and raw.strip().lower() in ("", "projection")):
        return projected_requests(cfg, fixture, arm)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise CapUsageError(f"--request-allocation must be a non-negative integer or "
                            f"'projection', got {raw!r}") from None
    if value < 0:
        raise CapUsageError(f"--request-allocation must be >= 0, got {value}")
    return value


def build_cap_gate(cfg, fixture: dict, arm: str, rows_path: str) -> RequestCapGate:
    import glob as globmod

    ledger = load_request_ledger(getattr(cfg, "request_ledger_tool", None))
    pattern = getattr(cfg, "budget_glob", None) or DEFAULT_CAP_PATTERN
    paths = sorted(globmod.glob(pattern), key=lambda p: os.path.basename(p))
    # The run's OWN row file is always in the scan, so the exit reconciliation compares
    # this run's count against this run's rows even when they live outside the corpus.
    # A file that does not exist yet holds zero rows (the writer creates it); it is not an
    # "unreadable" file, which is what exit 5 is reserved for.
    if os.path.exists(rows_path):
        paths.append(rows_path)
    cap = getattr(cfg, "budget_cap", None)
    cap = int(ledger.DEFAULT_CAP if cap is None else cap)
    # PREREG-CEILING-ON-THE-BRAKE (U-SPCC-40): the ceiling G3 admitted the claim under
    # (armed by enforce_prereg_gate) and the run-scoped send tally every cell shares, so
    # the ceiling is spent ONCE per run rather than once per arm.
    counter = getattr(cfg, "prereg_sends", None)
    if counter is None:
        counter = {"n": 0}
        cfg.prereg_sends = counter
    return RequestCapGate(ledger, paths, cap,
                          int(getattr(cfg, "budget_reserve", 0) or 0),
                          allocation_for(cfg, fixture, arm), own_rows=rows_path,
                          ceiling=getattr(cfg, "prereg_request_ceiling", None),
                          run_counter=counter)


def _observed_tools(rows_path: str, available: int | None) -> dict:
    """The `tools` block's OBSERVED totals, read from the cell's own rows.

    FETCH-ROUNDS-ACCOUNTING (U-SPCC-50): the `tools` block was frozen at launch and never
    updated, so a finished cell reported launch POLICY (`fetch_rounds_used: 0`) instead of
    what the arm did.  At finalisation the block is rewritten from the durable ledger:

    * `fetch_rounds_used` -- `fetch_rounds_spent`, the same derivation `--resume` uses, so
      a resumed cell and a fresh one report the same number for the same spend;
    * `fetch_rounds_available` -- the pool the rounds were drawn from (the frozen
      `max_fetch_rounds_per_arm`, carried through unchanged);
    * `tools_schema_sent` -- the WIRE fact: did any request of this cell actually carry
      the tool schema?  A `--tools` run whose schema never reached the wire is a
      different experiment from one where it did.
    """
    rows: list[dict] = []
    if os.path.exists(rows_path):
        with open(rows_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return {
        "fetch_rounds_used": fetch_rounds_spent(rows),
        "fetch_rounds_available": available,
        "tools_schema_sent": any(r.get("tools_schema_sent") is True for r in rows),
    }


def _gate_finish(gate: RequestCapGate, manifest_path: str | None, manifest_sha: str | None,
                 rows_path: str) -> tuple[dict, int]:
    """Reconcile at exit, write the final counts into the run manifest, return (rec, rc)."""
    try:
        rec = gate.reconcile()
    except CapRowsUnreadable as exc:
        print(f"CAP GATE ROWS at exit: {exc}", file=sys.stderr)
        return {"delta": None, "error": str(exc)}, 5
    print(f"cap-gate: allocation={gate.allocation} cap={gate.cap} reserve={gate.reserve} "
          f"spent_at_start={gate.spent_at_start} used_in_run={gate.used_in_run} "
          f"spent_after={rec['spent_after']} delta={rec['delta']}", file=sys.stderr)
    rc = 0
    if manifest_path and os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
            prior = ((doc.get("cap_gate") or {}).get("frozen_sha256"))
            block = gate.manifest_block(reconciled=rec)
            # The addendum names the bytes the ROWS were stamped with, so a later
            # --resume can still verify the frozen manifest it started from.
            block["frozen_sha256"] = prior or manifest_sha
            doc["cap_gate"] = block
            # FETCH-ROUNDS-ACCOUNTING (U-SPCC-50): the `tools` block is frozen at launch
            # and was never updated, so a finished cell reported launch policy rather than
            # what happened.  Rewrite it with the OBSERVED totals from the cell's rows.
            if isinstance(doc.get("tools"), dict):
                doc["tools"].update(_observed_tools(
                    rows_path, doc["tools"].get("max_fetch_rounds_per_arm")))
            data, final_sha = write_manifest(manifest_path, doc)
            print(f"cap-gate: final counts recorded in {manifest_path} "
                  f"({len(data)} B) sha256={final_sha}", file=sys.stderr)
        except (OSError, ValueError, TypeError) as exc:
            print(f"CAP GATE MANIFEST: cannot record the final counts in {manifest_path}: "
                  f"{type(exc).__name__}: {exc}", file=sys.stderr)
            rc = EXIT_CAP_DIVERGENCE
    if rec["delta"] > 0:
        # A row no request bought: the ledger and the run disagree about MONEY.  This is a
        # bug, not a rounding, and it fails the run.
        print(f"CAP GATE RECONCILE DIVERGENCE (delta=+{rec['delta']}): the run counted "
              f"{gate.used_in_run} request(s) but the rows gained "
              f"{rec['spent_after'] - rec['spent_at_start']} (spent_at_start="
              f"{rec['spent_at_start']} spent_after={rec['spent_after']} rows={rows_path}). "
              f"A divergence is a bug, not a rounding error.", file=sys.stderr)
        rc = EXIT_CAP_DIVERGENCE
    elif rec["delta"] < 0:
        # Requests that reached the wire whose rows could not be written before the run
        # stopped (a refusal can land mid-turn).  That makes the ledger UNDERSTATE the
        # spend, so the next gate check would see more headroom than exists: this is a
        # refusal (exit 9), not a printout.  Anything else lets a run walk past the gate
        # by dropping a row.
        headroom_before = gate.cap - gate.reserve - rec["spent_at_start"]
        headroom_after = gate.cap - gate.reserve - rec["spent_after"]
        print(f"CAP GATE UNRECORDED (delta={rec['delta']}) — refusing, exit "
              f"{EXIT_CAP_DIVERGENCE}: {-rec['delta']} request(s) reached the wire but "
              f"their rows were not written before the run stopped "
              f"(used_in_run={gate.used_in_run} rows_gained="
              f"{rec['spent_after'] - rec['spent_at_start']} headroom_before="
              f"{headroom_before} headroom_after={headroom_after} rows={rows_path}); "
              f"rows were not persisted, so the ledger cannot be trusted for the next "
              f"check — it would grant {-rec['delta']} request(s) beyond the true "
              f"headroom.", file=sys.stderr)
        rc = EXIT_CAP_DIVERGENCE
    else:
        print(f"cap-gate: reconciled — the run's count {gate.used_in_run} equals the rows "
              f"gained {rec['spent_after'] - rec['spent_at_start']} (delta 0)", file=sys.stderr)
    return rec, rc


def _cap_stop(exc: CapRefusal, gate: RequestCapGate, manifest_path: str | None,
              manifest_sha: str | None, rows_path: str) -> int:
    """Exit 4 for a refusal, after recording the arithmetic and reconciling."""
    print(str(exc), file=sys.stderr)
    _rec, rc = _gate_finish(gate, manifest_path, manifest_sha, rows_path)
    return 4 if rc == 0 else rc


def _abort_stop(rc: int, gate: RequestCapGate, manifest_path: str | None,
                manifest_sha: str | None, rows_path: str) -> int:
    """Leave an ABORTED run through the gate: reconcile first, then return `rc`.

    A runaway/abort still spent requests, so the unrecorded remainder has to be checked
    before the process exits -- otherwise the refusal that ended the run is the LAST thing
    anyone sees, and the next cell is granted headroom that does not exist.  A reconcile
    failure OUTRANKS the abort (its code is returned instead): a run whose spend is
    unrecorded must not be reported as merely runaway, and that failure is never swallowed
    into the abort's own code.
    """
    _rec, cap_rc = _gate_finish(gate, manifest_path, manifest_sha, rows_path)
    return rc if cap_rc == 0 else cap_rc


def _decode_json_objects(text: str) -> list:
    """Every decodable JSON value in `text`, in order. Never raises."""
    dec = json.JSONDecoder()
    out: list = []
    i = 0
    while True:
        j = text.find("{", i)
        if j < 0:
            return out
        try:
            obj, end = dec.raw_decode(text, j)
        except ValueError:
            i = j + 1
            continue
        out.append(obj)
        i = end


def _grep_call_from_object(obj: dict) -> Optional[dict]:
    """One `grep` call from a decoded JSON object, or None when it is unusable.

    STAGE-2-GREP: the discriminator is the `pattern` key, not the position of the
    object in the turn.  An EMPTY pattern is kept, not dropped: `execute_tool_call`
    refuses it by name (`missing_pattern`), so the row says the model asked and the
    harness refused, which is the same contract every other refusal follows.
    """
    pattern = obj.get("pattern")
    if not isinstance(pattern, str):
        return None
    glob = obj.get("glob")
    if not isinstance(glob, str) or not glob.strip():
        glob = GREP_DEFAULT_GLOB
    try:
        max_hits = int(obj.get("max_hits", GREP_MAX_HITS))
    except (TypeError, ValueError):
        max_hits = GREP_MAX_HITS
    return {"tool": GREP_TOOL_NAME, "pattern": pattern, "glob": glob.strip(),
            "max_hits": max_hits}


def parse_tool_calls(text: str) -> list[dict]:
    """Parse read_file and grep requests out of one model turn. Never raises.

    Accepts the observed shape, where the marker is repeated as a separator:

      <tool_call>2629 <tool_call>read_file <tool_call>{"path": "...", "start_line": 66, "end_line": 71}

    and a single well-formed JSON object following the token `read_file`.  A turn
    that never names `read_file` yields no calls, so prose JSON cannot trigger a read.

    STAGE-2-GREP: the same scan additionally accepts a JSON object carrying a
    `pattern` key after the token `grep`, producing
    ``{"tool": "grep", "pattern", "glob", "max_hits"}``.  The name gate is per tool:
    a turn that names only `grep` cannot produce a `read_file` call and vice versa,
    so prose JSON still cannot trigger either.
    """
    if not text:
        return []
    has_read = client.READ_FILE_TOOL_NAME in text
    has_grep = GREP_TOOL_NAME in text
    if not (has_read or has_grep):
        return []
    anchor = text.find("<tool_call>")
    if anchor >= 0:
        region = text[anchor:]
    else:
        region = text[min(text.find(n) for n in
                          (client.READ_FILE_TOOL_NAME, GREP_TOOL_NAME) if n in text):]
    calls: list[dict] = []
    for obj in _decode_json_objects(region):
        if not isinstance(obj, dict):
            continue
        if "pattern" in obj:
            if not has_grep:
                continue
            call = _grep_call_from_object(obj)
            if call is not None:
                calls.append(call)
            continue
        if not has_read:
            continue
        path = obj.get("path")
        if not isinstance(path, str) or not path.strip():
            continue
        try:
            start = int(obj.get("start_line", obj.get("start", 1)))
            end = int(obj.get("end_line", obj.get("end", start)))
        except (TypeError, ValueError):
            continue
        if start > end:
            start, end = end, start
        call = {"path": path.strip(), "start_line": max(1, start), "end_line": max(1, end)}
        # FETCH-CHANNEL-FIX: an identical repeat is KEPT, not silently dropped.  The
        # 2-per-turn cap already allows the arm's observed duplicate, and the executor
        # serves it from the cache (`cached="true"`): one read, one billed request.
        calls.append(call)
    return calls


def _call_from_arguments(call_id, name, arguments_json) -> tuple:
    """``(call|None, refusal|None)`` for ONE structured tool call's arguments.

    Never raises and never drops: an unusable call comes back as a RECORDED refusal so
    the turn row says the model asked and the harness refused, with the reason.
    """
    refusal = {"tool": name, "call_id": call_id, "error": "malformed_tool_arguments",
               "executed": False, "truncated": False, "billed": False}
    if name == client.FETCH_TOOL_NAME:
        if not isinstance(arguments_json, dict):
            return None, dict(refusal, reason="arguments_not_an_object")
        ref = arguments_json.get("ref")
        if not isinstance(ref, str) or not ref.strip():
            return None, dict(refusal, reason="missing_ref")
        rng = arguments_json.get("range")
        if isinstance(rng, dict):
            rng = (rng.get("start"), rng.get("end"))
        return ({"ref": ref.strip(), "range": rng,
                 "source": "structured_tool_call", "call_id": call_id}, None)
    if name == GREP_TOOL_NAME:
        # STAGE-2-GREP: the same refusal SHAPE as every other branch here (a recorded
        # refusal, never a dropped call) and the same refusal VOCABULARY as
        # `execute_tool_call`'s grep branch, so a structured call and a text call that
        # are equally wrong are equally named on the row.
        if not isinstance(arguments_json, dict):
            return None, dict(refusal, reason="arguments_not_an_object")
        pattern = arguments_json.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            return None, dict(refusal, reason="missing_pattern")
        if len(pattern) > GREP_MAX_PATTERN_CHARS:
            return None, dict(refusal, reason="pattern_too_long")
        try:
            re.compile(pattern)
        except re.error:
            return None, dict(refusal, reason="bad_pattern")
        glob = arguments_json.get("glob")
        if not isinstance(glob, str) or not glob.strip():
            glob = GREP_DEFAULT_GLOB
        try:
            max_hits = int(arguments_json.get("max_hits", GREP_MAX_HITS))
        except (TypeError, ValueError):
            max_hits = GREP_MAX_HITS
        return ({"tool": GREP_TOOL_NAME, "pattern": pattern, "glob": glob.strip(),
                 "max_hits": max_hits, "source": "structured_tool_call",
                 "call_id": call_id}, None)
    if name != client.READ_FILE_TOOL_NAME:
        return None, dict(refusal, reason="unknown_tool")
    if not isinstance(arguments_json, dict):
        return None, dict(refusal, reason="arguments_not_an_object")
    path = arguments_json.get("path")
    if not isinstance(path, str) or not path.strip():
        return None, dict(refusal, reason="missing_path")
    try:
        start = int(arguments_json.get("start_line", arguments_json.get("start", 1)))
        end = int(arguments_json.get("end_line", arguments_json.get("end", start)))
    except (TypeError, ValueError):
        return None, dict(refusal, reason="unparseable_range")
    if start > end:
        start, end = end, start
    return ({"path": path.strip(), "start_line": max(1, start), "end_line": max(1, end),
             "source": "structured_tool_call", "call_id": call_id}, None)


def calls_from_response(resp) -> tuple[list[dict], list[dict]]:
    """``(calls, refusals)`` for one model reply: STRUCTURED calls first, text second.

    TOOL-CHANNEL-WIRE: a tools-on reply carries ``message.tool_calls`` and
    ``content_len == 0`` (docs/TOOL-CHANNEL-ROOT-CAUSE.md §3, probe A), so the old text
    scan at :func:`parse_tool_calls` can never see it.  Structured calls are therefore
    consumed FIRST; the text parser runs only when the reply carries no structured call
    at all, which keeps every historical text-shaped reply working unchanged.
    """
    resp = resp or {}
    structured = resp.get("tool_calls") or []
    if not structured:
        return parse_tool_calls(resp.get("content") or ""), []
    calls: list[dict] = []
    refusals: list[dict] = []
    for rec in structured:
        if not isinstance(rec, dict):
            refusals.append({"tool": None, "call_id": None,
                             "error": "malformed_tool_arguments",
                             "reason": "call_not_an_object",
                             "executed": False, "truncated": False, "billed": False})
            continue
        name = rec.get("name")
        if rec.get("arguments_error"):
            refusals.append({"tool": name, "call_id": rec.get("id"),
                             "error": "malformed_tool_arguments",
                             "reason": rec["arguments_error"],
                             "arguments": rec.get("arguments"),
                             "executed": False, "truncated": False, "billed": False})
            continue
        call, refusal = _call_from_arguments(rec.get("id"), name, rec.get("arguments_json"))
        if call is not None:
            calls.append(call)
        if refusal is not None:
            refusal["arguments"] = rec.get("arguments")
            refusals.append(refusal)
    return calls, refusals


def unserviced_structured_calls(resp, calls) -> list[dict]:
    """Structured calls the fetch parser did NOT consume, verbatim.

    TOOL-CALL-CAPTURE (U-SPCC-49): ``arm_cd.parse_fetch_calls_from_response`` delegates to
    ``ptr_engine.fetch_tool.parse_fetch_calls``, which keeps ONLY calls whose
    ``function.name`` is ``"fetch"``.  The schema actually on the wire is ``read_file``
    (``TOOL_NAMES``), so a ``read_file`` call is filtered out and -- before this helper --
    vanished: no follow-up was bought, the empty content parsed as ``no_answer_line``, and
    nothing on the row said a call had ever been signalled.  Ten of the fetch arm's 48
    checkpoints in the corrected E1 cell died that way.

    A call is reported here when the parser consumed nothing at all, or when its ``id`` is
    absent from the ids the parser did consume.  An id-less call is assumed consumed once
    anything was consumed: the wire always carries ids (``call_…``), so this can only
    under-report, never invent a call.
    """
    raw = [c for c in ((resp or {}).get("tool_calls") or []) if isinstance(c, dict)]
    if not raw:
        return []
    if not calls:
        return raw
    served = {c.get("tool_call_id") for c in calls if c.get("tool_call_id")}
    return [c for c in raw if c.get("id") is not None and c.get("id") not in served]


def fetch_call_tool_names(cfg=None) -> tuple:
    """The tool names a fetch-arm reply may use: the run's DECLARED tools + ``fetch``.

    FETCH-NAME-DRIFT (U-SPCC-52): the fetch parser used to hardcode ``"fetch"`` while
    the wire schema declared ``read_file`` (``TOOL_NAMES``), so every ``read_file`` call
    was filtered out and its checkpoint scored ``unparsed``.  The parser now takes the
    declared set; this is where the run hands it over.  ``fetch`` is always included
    because the ARM_D prompt still teaches ``fetch(ref=...)``, and a run that declared
    neither name (``cfg is None``) falls back to ``TOOL_NAMES``.
    """
    names = list(client.tool_names(cfg)) if cfg is not None else list(TOOL_NAMES)
    # STAGE-2-GREP: `grep` is NOT a fetch.  `parse_fetch_calls` turns every accepted
    # call into `{"ref": args.get("ref") or args.get("path") or ""}`, so a grep call
    # admitted here would be served as a fetch with an EMPTY ref -- the model asks for
    # a pattern and gets a pointer-table refusal, which is a silent mis-service.  It is
    # excluded deliberately, so a grep call in a fetch arm stays UNSERVICED and is
    # reported by `unserviced_structured_calls` (protocol_violation
    # "tool_call_unserviced") instead of being answered with the wrong tool.
    names = [n for n in names if n != GREP_TOOL_NAME]
    if client.FETCH_TOOL_NAME not in names:
        names.append(client.FETCH_TOOL_NAME)
    return tuple(names)


def limit_calls(calls: list[dict], per_turn: int = TOOL_CALLS_PER_TURN):
    """Split one turn's calls into (executed batch, refused overflow). Hard 2-per-turn."""
    return list(calls[:per_turn]), list(calls[per_turn:])


def _is_secret_shaped(name: str) -> bool:
    low = name.lower()
    if low in _SECRET_BASENAMES or low.startswith(_SECRET_PREFIXES):
        return True
    if low.endswith(_SECRET_SUFFIXES):
        return True
    return any(low == stem or low.startswith(stem + ".") for stem in _SECRET_STEMS)


def _resolve_under(raw: str, root: str, allow_dir: bool = False) -> tuple:
    """Resolve one already-sanitised relative path under one base. Never opens the file.

    STAGE-2-GREP: `allow_dir` exists so `grep` can scope to a directory without a second
    copy of the containment rules.  The read channel keeps the default, so a directory is
    still `path_not_found` for `read_file` -- only the caller that can use one asks for it.
    """
    root_abs = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root_abs, raw))
    try:
        if os.path.commonpath([root_abs, target]) != root_abs:
            return None, "path_refused"
    except ValueError:
        return None, "path_refused"
    if target == root_abs:
        return None, "path_not_found"
    # `allow_dir` WIDENS the accepted kind, it does not replace it: a caller that can use
    # a directory can still use a file.
    ok = (os.path.isdir(target) or os.path.isfile(target)) if allow_dir else os.path.isfile(target)
    if not ok:
        return None, "path_not_found"
    return target, None


def resolve_read_path_base(path: str, root: str, engine_root=None,
                           allow_dir: bool = False) -> tuple:
    """(absolute_path, refusal_or_None, base) where base is 'workspace'|'engine'|None.

    FETCH-CHANNEL fix: the arm emits `ptr_engine/resolve.py`, the string its own fixture
    index uses, and resolving it from the workspace root alone refused every well-formed
    call `path_not_found`.  Order is workspace root FIRST, then the engine root, and the
    base that matched is reported.  The unsafe-path rules (absolute, `~`, `..`,
    realpath escape, secret-shaped) run ONCE on the raw string, so they are identical
    for both bases: a traversal attempt is `path_refused` with zero reads from either.
    """
    if not isinstance(path, str) or not path.strip():
        return None, "path_refused", None
    raw = path.strip().replace("\\", "/")
    if raw.startswith("/") or raw.startswith("~") or os.path.isabs(raw):
        return None, "path_refused", None
    if any(part == ".." for part in raw.split("/")):
        return None, "path_refused", None
    if _is_secret_shaped(raw.rsplit("/", 1)[-1]):
        return None, "path_refused", None
    target, reason = _resolve_under(raw, root, allow_dir)
    if target is not None:
        return target, None, "workspace"
    if engine_root is not None and reason == "path_not_found":
        e_target, e_reason = _resolve_under(raw, engine_root, allow_dir)
        if e_target is not None:
            return e_target, None, "engine"
        if e_reason == "path_refused":
            return None, "path_refused", None
    return None, reason, None


def resolve_read_path(path: str, root: str, engine_root=None) -> tuple:
    """Return (absolute_path, None) or (None, refusal_reason). Never opens the file."""
    target, reason, _base = resolve_read_path_base(path, root, engine_root)
    return target, reason


def _grep_refusal(reason: str, rec: dict) -> dict:
    """The refusal shape every tool call shares: a record, a block, no text."""
    rec["error"] = reason
    return {"record": rec, "block": f'<tool_result error="{reason}"/>', "text": ""}


def _execute_grep(call: dict, root: str, engine_root=None) -> dict:
    """Bounded regex search under `root`. Returns {record, block, text}.

    STAGE-2-GREP (docs/AGENTIC-COMPACTION-AB.md §3.2).  `read_file` alone makes a lost
    journal repairable only by re-reading, which inflates the re-fetch rate the design
    measures; this is the second tool, and it is bounded on every axis that could make
    it a second read channel:

      * `glob` (default ``*.py``) is matched with ``fnmatch`` against the BASENAME;
      * at most ``GREP_MAX_HITS`` (20) ``path:line: text`` lines come back, each
        truncated to ``GREP_MAX_LINE_CHARS`` (200) characters;
      * the walk never descends into ``GREP_SKIP_DIRS`` (``.git``, ``__pycache__``,
        ``state``) and every candidate is re-admitted through
        ``resolve_read_path_base``, so a symlink out of the root or a secret-shaped
        basename is refused exactly as a read would be.  Nothing is searched that a
        ``read_file`` could not read.

    `truncated` is exact, not a guess: the scan runs until it finds ``max_hits + 1``
    matches, so a result that happens to end exactly at the cap is not reported cut.
    """
    pattern = call.get("pattern")
    glob = call.get("glob") or GREP_DEFAULT_GLOB
    try:
        max_hits = int(call.get("max_hits", GREP_MAX_HITS))
    except (TypeError, ValueError):
        max_hits = GREP_MAX_HITS
    max_hits = max(1, min(max_hits, GREP_MAX_HITS))
    rec = {"tool": GREP_TOOL_NAME, "pattern": pattern, "glob": glob,
           "hits": 0, "files_scanned": 0, "executed": False, "truncated": False}
    if not isinstance(pattern, str) or not pattern:
        return _grep_refusal("missing_pattern", rec)
    if len(pattern) > GREP_MAX_PATTERN_CHARS:
        return _grep_refusal("pattern_too_long", rec)
    try:
        rx = re.compile(pattern)
    except re.error:
        return _grep_refusal("bad_pattern", rec)
    root_abs = os.path.realpath(root)
    # STAGE-2-GREP: a `path` argument is SCOPED, not ignored.  It goes through the same
    # `resolve_read_path_base` gate a read does, so `.env`, `~/.ssh/id_rsa`, an absolute
    # path or a `..` escape is refused with the read channel's own reason instead of
    # being silently dropped -- a grep that quietly searched the whole root after being
    # asked for one file would answer a question the model did not ask.
    scope = root_abs
    raw_path = call.get("path")
    if raw_path:
        target, reason, _base = resolve_read_path_base(raw_path, root_abs, engine_root,
                                                       allow_dir=True)
        if target is None:
            rec["path"] = raw_path
            return _grep_refusal(reason, rec)
        scope = target
        rec["path"] = raw_path
    hits: list[str] = []
    files_scanned = 0
    truncated = False
    if os.path.isfile(scope):
        walk = [(os.path.dirname(scope), [], [os.path.basename(scope)])]
    else:
        walk = os.walk(scope)
    for dirpath, dirnames, filenames in walk:
        # STAGE-2-GREP: the walk prunes the same names `read_file` refuses.  A directory
        # called `secrets/` or `keys/` is refused by `_is_secret_shaped` on its own
        # basename, so descending into it could only produce hits the read channel
        # would never have returned -- a leak by a second route.
        dirnames[:] = sorted(d for d in dirnames
                             if d not in GREP_SKIP_DIRS and not _is_secret_shaped(d))
        for name in sorted(filenames):
            if not fnmatch.fnmatch(name, glob):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root_abs).replace(os.sep, "/")
            target, reason, _base = resolve_read_path_base(rel, root_abs, engine_root)
            if target is None:
                continue
            files_scanned += 1
            try:
                with open(target, "r", encoding="utf-8", errors="replace") as fh:
                    lines = fh.readlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, start=1):
                if not rx.search(line):
                    continue
                text = line.rstrip("\n")
                if len(text) > GREP_MAX_LINE_CHARS:
                    text = text[:GREP_MAX_LINE_CHARS]
                hits.append(f"{rel}:{lineno}: {text}")
                if len(hits) > max_hits:
                    truncated = True
                    break
            if truncated:
                break
        if truncated:
            break
    if truncated:
        hits = hits[:max_hits]
    rec.update({"hits": len(hits), "files_scanned": files_scanned,
                "executed": True, "truncated": truncated})
    body = "\n".join(hits)
    attrs = (f'for="grep" pattern="{str(pattern).replace(chr(34), chr(39))}" '
             f'glob="{glob}" hits="{len(hits)}" files_scanned="{files_scanned}"')
    if truncated:
        attrs += ' truncated="true"'
    return {"record": rec, "block": f"<tool_result {attrs}>\n{body}\n</tool_result>",
            "text": body}


def execute_tool_call(call: dict, root: str, engine_root=None) -> dict:
    """Perform one bounded tool call. Returns {record, block, text}.

    `block` is the delimited tool result appended to the conversation; `record` is
    the `tool_calls` entry written to the row.  A refused or unsafe path injects
    `<tool_result error="path_refused"/>` and is never read.  `base` names the root
    that matched ("workspace" first, else "engine") and is reported both on the record
    and in the `<tool_result … base="…">` attribute.

    STAGE-2-GREP: dispatch is on ``call.get("tool", "read_file")``, so every call
    shape written before this change (which carries no `tool` key) still reads a file.
    """
    if call.get("tool", client.READ_FILE_TOOL_NAME) == GREP_TOOL_NAME:
        return _execute_grep(call, root, engine_root)
    target, reason, base = resolve_read_path_base(call["path"], root, engine_root)
    rec = {"path": call["path"], "start_line": call["start_line"],
           "end_line": call["end_line"], "executed": False, "truncated": False}
    if target is None:
        rec["error"] = reason
        return {"record": rec, "block": f'<tool_result error="{reason}"/>', "text": ""}
    try:
        with open(target, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        rec["error"] = "read_failed"
        return {"record": rec, "block": '<tool_result error="read_failed"/>', "text": ""}
    total = len(lines)
    if call["start_line"] > total:
        rec["error"] = "range_out_of_bounds"
        return {"record": rec, "block": '<tool_result error="range_out_of_bounds"/>', "text": ""}
    start = max(1, call["start_line"])
    end = min(max(start, call["end_line"]), total)
    truncated = False
    if end - start + 1 > TOOL_READ_CAP_LINES:
        end = start + TOOL_READ_CAP_LINES - 1
        truncated = True
    body = "".join(lines[start - 1:end]).rstrip("\n")
    if len(body) > TOOL_READ_CAP_CHARS:
        body = body[:TOOL_READ_CAP_CHARS]
        truncated = True
    rec.update({"executed": True, "truncated": truncated, "lines_returned": end - start + 1,
                "base": base})
    path_attr = call["path"].replace('"', "'")
    attrs = f'for="read_file" path="{path_attr}" lines="{start}-{end}" base="{base}"'
    if truncated:
        attrs += ' truncated="true"'
    return {"record": rec, "block": f"<tool_result {attrs}>\n{body}\n</tool_result>", "text": body}


def verify_snapshot_manifest(manifest_path: str) -> tuple:
    """``(root_sha256|None, refusal|None)`` for a build_snapshot.py manifest.

    STAGE-2-SNAPSHOT (docs/AGENTIC-COMPACTION-AB.md §3.2 item 1): a frozen root is only
    frozen if its bytes are re-checked.  Every entry is re-hashed here, BEFORE the first
    request, and the first difference is named ``snapshot_manifest_mismatch: <relpath>``
    so the abort says which file moved rather than that "something" did.

    The manifest lives INSIDE the snapshot it describes, so its own directory is the
    root the entries are relative to.  A `--root` that is not that directory is refused
    too: a manifest that does not describe the tree being read proves nothing.
    """
    try:
        with open(manifest_path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None, "snapshot_manifest_unreadable"
    if not isinstance(doc, dict):
        return None, "snapshot_manifest_unreadable"
    files = doc.get("files")
    root_sha = doc.get("root_sha256")
    if not isinstance(files, dict) or not isinstance(root_sha, str):
        return None, "snapshot_manifest_unreadable"
    base = os.path.dirname(os.path.abspath(manifest_path))
    for rel in sorted(files):
        try:
            got = sha256_file(os.path.join(base, rel))
        except OSError:
            return None, f"snapshot_manifest_mismatch: {rel}"
        if got != files[rel]:
            return None, f"snapshot_manifest_mismatch: {rel}"
    return root_sha, None


def _cached_result(res: dict, scope: str) -> dict:
    """The SAME <tool_result> again, marked `cached="true"`: no read, no request, no round.

    A duplicate of a call already answered (earlier in this turn, or in the conversation
    from an earlier turn) must not buy a second fetch: it is served from the cache and
    bills nothing.  Errors are returned verbatim and are never cached across turns.
    """
    rec = dict(res["record"])
    rec["cached"] = True
    rec["cache_scope"] = scope
    block = res["block"]
    if rec.get("executed") and block.endswith("</tool_result>") and 'cached="true"' not in block:
        head, sep, tail = block.partition(">")
        block = head + ' cached="true"' + sep + tail
    return {"record": rec, "block": block, "text": res["text"]}


def parse_pointer_range(pointer) -> tuple | None:
    """(start_line, end_line) from a fixture pointer such as `#L36-L110` or `#L39`.

    Returns None when the pointer is absent or unparseable: an item whose line range is
    not declared cannot be used to serve a range from the prompt, and is skipped rather
    than guessed at.
    """
    if not isinstance(pointer, str):
        return None
    nums = [int(n) for n in re.findall(r"\d+", pointer)]
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0], nums[0]
    return min(nums[0], nums[1]), max(nums[0], nums[1])


def pinned_views(fixture: dict, prompt: str) -> list[dict]:
    """The bodies the runner ACTUALLY pinned into this turn's prompt, with line ranges.

    Detected from the runner's own view — the exact `body_block(item)` text is searched in
    the prompt it just built — so it is right for every arm without special cases: pointer
    -stable pins the bodies of the items it points at, transcript-grow pins the working set
    until FIFO evicts it, and an arm that pins no body yields an empty list.  The line
    offsets come from the item's own `source.pointer` (e.g. `#L36-L110`), which is what
    makes a requested file range mappable onto the pinned text.
    """
    views: list[dict] = []
    if not prompt:
        return views
    for item in fixture.get("items") or []:
        try:
            block = body_block(item)
        except (KeyError, TypeError):
            continue
        if block not in prompt:
            continue
        src = item.get("source") or {}
        path = src.get("path")
        rng = parse_pointer_range(src.get("pointer"))
        if not isinstance(path, str) or not path.strip() or rng is None:
            continue
        views.append({"path": path.strip().replace("\\", "/"), "start": rng[0], "end": rng[1],
                      "lines": item["body"].split("\n"), "item_id": item.get("id")})
    return views


def find_pinned_view(views: list[dict], call: dict):
    """The pinned body that wholly contains `call`'s range, or None.

    Path matching is intentionally lenient in the same direction the fetch channel already
    is: the arm emits `ptr_engine/resolve.py` for the fixture's
    `experiments/ptr-engine/ptr_engine/resolve.py`, so a candidate matches on equality or
    on a `/`-anchored suffix.  The RANGE test is strict: the requested lines must lie
    inside the pinned range, so a read of lines the prompt never carried is still a fetch.
    """
    want = call["path"].strip().replace("\\", "/")
    while want.startswith("./"):
        want = want[2:]
    for view in views:
        have = view["path"]
        if not (want == have or have.endswith("/" + want)):
            continue
        if call["start_line"] < view["start"] or call["end_line"] > view["end"]:
            continue
        first = call["start_line"] - view["start"]
        last = call["end_line"] - view["start"] + 1
        if first < 0 or last > len(view["lines"]):
            continue
        return dict(view, first=first, last=last)
    return None


def serve_from_prompt(view: dict, call: dict) -> dict:
    """Answer a call from the lines the prompt already carries. `{record, block, text}`.

    The block is shaped exactly like a real `<tool_result>` so the arm reads it the same
    way, with `base="prompt" served_from="prompt"` naming its provenance.  `executed` is
    False and `billed` is False: nothing was read from disk and no fetch round was spent.
    """
    body = "\n".join(view["lines"][view["first"]:view["last"]])
    rec = {"path": call["path"], "start_line": call["start_line"], "end_line": call["end_line"],
           "executed": False, "truncated": False, "billed": False, "served_from": "prompt",
           "base": "prompt", "pinned_item": view.get("item_id"),
           "pinned_lines": f'{view["start"]}-{view["end"]}',
           "lines_returned": view["last"] - view["first"]}
    if len(body) > TOOL_READ_CAP_CHARS:
        body = body[:TOOL_READ_CAP_CHARS]
        rec["truncated"] = True
    path_attr = call["path"].replace('"', "'")
    attrs = (f'for="read_file" path="{path_attr}" lines="{call["start_line"]}-{call["end_line"]}"'
             ' base="prompt" served_from="prompt"')
    if rec["truncated"]:
        attrs += ' truncated="true"'
    return {"record": rec, "block": f"<tool_result {attrs}>\n{body}\n</tool_result>", "text": body}


def fetch_rounds_spent(rows: list[dict]) -> int:
    """Fetch rounds this cell has ALREADY spent, derived from its own rows.

    `--resume` used to reset the counter to 0, so a resumed arm could execute 20
    fetches while the counter reported 8/8 (PROBE-CP3-FETCH).  Every follow-up is
    fsync'd to its row, so the rows are the durable ledger: one round per
    `kind='tool-followup'` / `fetch_followup` row, and any `fetch_rounds_used` stamped
    on a turn row is taken as a floor.
    """
    spent = 0
    for row in rows:
        is_followup = row.get("kind") == "tool-followup" or row.get("fetch_followup") is True
        if is_followup:
            # PROBE-CP3-V6: only a follow-up that read fresh lines off disk is a BILLED
            # round.  A pinned serve (served_from="prompt") is a request but not a round,
            # so a resumed cell must not re-charge it against the per-arm round budget.
            # Rows written before `billed_round` existed are taken as billed.
            if row.get("billed_round") is False:
                continue
            spent += 1
        else:
            used = row.get("fetch_rounds_used")
            if isinstance(used, int) and used > spent:
                spent = used
    return spent


def followups_spent(rows: list[dict]) -> int:
    """Follow-up REQUESTS this cell has already bought (billed and prompt-served alike).

    The round budget and the request budget are different ledgers: (a) makes a pinned
    serve cost no round, it does not make it free.  This counter drives the follow-up
    allowance in run_cell so `requests_sent` can never exceed the card's bound.
    """
    return sum(1 for row in rows
               if row.get("kind") == "tool-followup" or row.get("fetch_followup") is True)


def _flush_partial_followups(followups, resp, row_sink, exc=None, keep_last=True):
    """Persist the follow-up rows a turn already bought before an exception unwinds.

    PAID-ROW-PERSISTENCE (U-SPCC-42): a mid-turn ``CapRefusal`` used to propagate out of
    the round loop before the rows for the follow-up requests already sent in that turn
    were written, so the exit reconciliation reported a NEGATIVE delta and the ledger
    understated the spend.  Every row for a request that reached the wire is now on disk
    before the exception leaves this function.

    ``keep_last`` leaves the FINAL follow-up row unwritten because the caller's turn row
    stands in its slot (the completed path writes it that way, so the row count is
    unchanged); a transport failure keeps nothing back, because the caller writes a
    failure row instead of a turn row.
    """
    if row_sink is not None:
        for row in (followups[:-1] if keep_last else followups):
            row_sink(row)
    if exc is not None:
        try:
            exc.partial_followups = list(followups)
            exc.partial_resp = resp
        except (AttributeError, TypeError):
            pass


def _persist_d_turn_row(rows_path, cfg, fixture, arm, rep, run_id, t, manifest_sha,
                        extras, info, initial_resp, error):
    """Persist the D arm's turn row before an exception unwinds past the paid send.

    PAID-ROW-PERSISTENCE (U-SPCC-43): ``arm_cd.service_fetches`` runs AFTER the turn's own
    request was paid for, and the turn's row used to be written only once the whole
    ``arm == arm_cd.ARM_D`` block had returned.  Anything that unwound out of that block
    before the send -- a malformed fetch call, an unrenderable fetch result -- therefore
    left a paid request with no row AND the run with no reconciliation at all.
    ``bounded-context-fetch`` is one of the three arms in E1, so that path could undercount
    an E1 run's spend.

    The row is the one the completed path already writes for the turn's own send
    (``kind="turn-initial"``), so neither the row schema nor the row count changes.
    """
    append_row(rows_path, make_row(
        cfg, fixture, arm, rep, run_id, t, initial_resp,
        initial_resp.get("content") if initial_resp else None,
        "turn-initial", manifest_sha,
        dict(extras, prompt_sha256=sha256_text(info["prompt"]),
             send_index=0, initial_send=True,
             row_measurement_source="turn-initial",
             next_request_kind="tool-followup", error=error)))


def fetch_rounds(cfg, fixture, arm, rep, run_id, t, manifest_sha, extras, messages, resp,
                 sent, budget, rounds_used, served=None, pinned=None, per_turn_cap=None,
                 may_request=None, gate=None, row_sink=None, root=None):
    """Run the bounded read_file channel after one model turn.

    Bounds (PROBE-CP3-V6): <= TOOL_CALLS_PER_TURN (2) calls per turn, at most
    `per_turn_cap` fetch rounds per turn (0 = unbounded, the pre-V6 behaviour), and
    <= fetch_rounds_per_arm(cfg) (default 48) BILLED rounds per arm.  One follow-up model request
    is bought per round, so `requests_sent = turn requests + follow-ups bought + digests`.

    (a) SERVE FROM THE PROMPT.  `pinned` is what the planner actually pinned into THIS
    turn's prompt (see pinned_views).  A call whose range lies wholly inside a pinned body
    is answered from that body: the record carries `served_from="prompt"`, the block
    carries the same lines, nothing is read from disk and NO ROUND IS BILLED.  It still
    rides the one follow-up request a round would have bought, because a result the model
    never sees is not a result — that request is drawn from the follow-up allowance
    (`may_request`), not from the round budget.

    (b) PER-TURN CAP.  `per_turn_cap` rounds per turn; the rest are refused host-side with
    `error="per_turn_round_cap"`, so one recon burst can no longer spend the cell.

    A duplicate fetch is never re-bought: an identical call (same path+range) later in
    the SAME turn, or one whose content is already in the conversation from an earlier
    turn (`served`, carried across turns by the caller), returns the same <tool_result>
    with `cached="true"` and spends neither a round nor a request.

    Returns (messages, resp, sent, rounds_used, turn_calls, followup_rows) — unchanged
    arity, so the V5 offline test still binds.  The per-turn counters are derived by the
    caller from the records (`served_from="prompt"` count) and from `len(followup_rows)`.
    """
    turn_calls: list[dict] = []
    followups: list[dict] = []
    cap = TOOL_FETCH_ROUNDS_PER_TURN if per_turn_cap is None else int(per_turn_cap)
    if not tools_enabled(cfg):
        return messages, resp, sent, rounds_used, turn_calls, followups
    # STAGE-2-ROOT: the root is the caller's (`--root`, default cwd), never a second
    # silent `os.getcwd()`: a frozen snapshot must be the ONLY tree a read can reach.
    root = root or os.getcwd()
    engine_root = os.path.join(root, ENGINE_ROOT_REL)
    if not os.path.isdir(engine_root):
        engine_root = None
    if served is None:
        served = {}
    pinned = list(pinned or [])
    content = resp.get("content") or ""
    # TOOL-CHANNEL-WIRE: structured tool_calls FIRST (a tools-on reply has content_len 0,
    # so the text scan below would find nothing); the text parser is the fallback only.
    # An unusable structured call is RECORDED on the row, never dropped and never a
    # silent no-op: the cell simply bills nothing for it.
    pending, refused_calls = calls_from_response(resp)
    turn_calls.extend(refused_calls)
    rounds_this_turn = 0
    prompt_serves = 0
    while pending:
        if cap > 0 and rounds_this_turn >= cap:
            # (b) This turn has already bought its rounds: refuse the rest, spend nothing.
            for call in pending:
                turn_calls.append({"path": call["path"], "start_line": call["start_line"],
                                   "end_line": call["end_line"], "executed": False,
                                   "truncated": False, "billed": False,
                                   "error": "per_turn_round_cap"})
            pending = []
            break
        batch, overflow = limit_calls(pending)
        turn_cache: dict = {}
        round_calls: list[dict] = []
        blocks: list[str] = []
        fresh = 0
        served_now = 0
        for call in batch:
            key = (call["path"], call["start_line"], call["end_line"])
            if key in turn_cache:
                res = _cached_result(turn_cache[key], "turn")
            elif key in served:
                res = _cached_result(served[key], "conversation")
            else:
                view = find_pinned_view(pinned, call) if TOOL_SERVE_FROM_PROMPT else None
                if view is not None:
                    res = serve_from_prompt(view, call)
                    served_now += 1
                    turn_cache[key] = res
                    served[key] = res
                elif rounds_used + fresh >= fetch_rounds_per_arm(cfg):
                    # The per-arm ROUND budget is spent.  This refusal is per CALL, not per
                    # turn: a range the prompt already carries still costs no round, so the
                    # T46 checkpoint read stays servable after the round budget is gone
                    # (the exact v5 starvation this unit exists to remove).
                    rec = {"path": call["path"], "start_line": call["start_line"],
                           "end_line": call["end_line"], "executed": False,
                           "truncated": False, "billed": False,
                           "error": "fetch_budget_exhausted"}
                    round_calls.append(rec)
                    blocks.append('<tool_result error="fetch_budget_exhausted"/>')
                    continue
                else:
                    res = execute_tool_call(call, root, engine_root)
                    fresh += 1
                    turn_cache[key] = res
                    if res["record"].get("executed"):
                        served[key] = res
            round_calls.append(res["record"])
            blocks.append(res["block"])
        for call in overflow:
            round_calls.append({"path": call["path"], "start_line": call["start_line"],
                                "end_line": call["end_line"], "executed": False,
                                "truncated": False, "error": "turn_call_cap"})
        turn_calls.extend(round_calls)
        if fresh == 0 and served_now == 0:
            # Everything asked for is already in the conversation: serve it, bill nothing.
            pending = []
            break
        if may_request is not None and not may_request():
            # The follow-up allowance is exhausted (or fully reserved for later declared
            # checkpoints).  Refusing gracefully keeps the cell intact; the served records
            # still say what the turn asked for.
            for rec in round_calls:
                if rec.get("served_from") == "prompt" or rec.get("executed") or rec.get("cached"):
                    rec["followup_suppressed"] = "request_allowance"
            pending = []
            break
        next_messages = messages + [
            {"role": "assistant", "content": content},
            {"role": "user", "content": "\n".join(blocks)
             + "\n\nUse the tool result above. Answer the QUESTION now, within the word budget."},
        ]
        if sent >= budget:
            # PAID-ROW-PERSISTENCE: the rounds already bought in this turn are on disk
            # before the abort unwinds past them.
            _flush_partial_followups(followups, resp, row_sink)
            raise BudgetExhausted(f"fetch at T{t} would exceed the request budget of {budget}")
        # WIRE-CAP-GATE: a follow-up is a REAL request and bills separately, so the brake
        # must see it too.  Reserved (and possibly refused) BEFORE the send.
        if gate is not None:
            try:
                gate.acquire(t, "tool-followup")
            except BaseException as exc:
                # PAID-ROW-PERSISTENCE (U-SPCC-42): a refusal here must not discard the
                # rows for the follow-ups already sent in this turn.  The last one is
                # left to the caller's turn row, which stands in its slot.
                _flush_partial_followups(followups, resp, row_sink, exc)
                raise
        try:
            resp = send_chat(cfg, next_messages)
        except BaseException as exc:
            # A transport failure keeps nothing back: the caller writes a failure row
            # for the send that failed, so every earlier follow-up needs its own row.
            _flush_partial_followups(followups, resp, row_sink, exc, keep_last=False)
            raise
        sent += 1
        rounds_this_turn += 1
        if fresh:
            rounds_used += 1
        else:
            prompt_serves += 1
        messages = next_messages
        content = resp.get("content") or ""
        followups.append(make_row(
            cfg, fixture, arm, rep, run_id, t, resp, content, "tool-followup", manifest_sha,
            # ROW-ATTRIBUTION: the 0-based position of THIS request inside the turn --
            # the initial send is send_index 0, the -th follow-up is send_index -.  A
            # later analysis can therefore address one HTTP request by (turn, send_index)
            # instead of guessing from row order.
            dict(extras, prompt_sha256=sha256_text(next_messages[-1]["content"]),
                 fetch_followup=True, tool_calls=round_calls,
                 billed_round=bool(fresh), prompt_served=int(served_now),
                 # FETCH-ROUNDS-ACCOUNTING (U-SPCC-50): the cumulative count AFTER this
                 # round, so a follow-up row states the spend it belongs to.
                 fetch_rounds_used=rounds_used,
                 send_index=int(rounds_this_turn),
                 fetch_rounds_cap_per_turn=cap)))
        # TOOL-CHANNEL-WIRE: the follow-up reply is read the same way (structured first,
        # text fallback).  A malformed call here is recorded on the turn row too.
        pending, refused_calls = calls_from_response(resp)
        turn_calls.extend(refused_calls)
    return messages, resp, sent, rounds_used, turn_calls, followups


# ------------------------------------------------------------------------ planner
def count_refetch(turn_calls, seen):
    """Count this turn's tool calls that re-read a range already read in this cell.

    E7's primary mechanism.  A fold drops the journal, so a fact the agent had
    already read has to be fetched again; ``refetch_count`` is what makes that
    cost visible per row.  ``seen`` is the per-cell set of
    ``(path, start_line, end_line)`` tuples, mutated in place: a hit is a
    re-fetch, a miss is added.  A call with no ``path`` (a refused or malformed
    call) is neither counted nor recorded.
    """
    refetch = 0
    for call in turn_calls or ():
        if not isinstance(call, dict):
            continue
        key = (call.get("path"), call.get("start_line"), call.get("end_line"))
        if key[0] is None:
            continue
        if key in seen:
            refetch += 1
        else:
            seen.add(key)
    return refetch


class Planner:
    """Builds the next prompt for one arm from the answers already recorded."""

    def __init__(self, arm: str, fixture: dict, dry_run: bool,
                 compact_every: int = COMPACT_EVERY,
                 window_turns: int = arm_cd.WINDOW_TURNS):
        self.arm = arm
        self.fixture = fixture
        self.dry_run = dry_run
        # E2's cell dimension: the fold distance this cell's spcc arm runs at.
        self.compact_every = int(compact_every)
        # E3's cell dimension: the masking window this cell's C/D arm runs at.
        self.window_turns = int(window_turns)
        self.answers: list[str] = []
        self.bpt = float(fixture["bytes_per_token"])
        self.wall_tokens = int(fixture["wall_tokens"])
        self.wall_bytes = self.wall_tokens * self.bpt
        # B state
        self.digest: str | None = None
        self.raw: list[str] = []
        self.arm_cd = (arm_cd.ArmCDState(fixture=fixture, window_turns=self.window_turns)
                       if arm in (arm_cd.ARM_C, arm_cd.ARM_D) else None)
        # spcc: stable-prefix compiler state (own journal, epoch and compaction count).
        self.spcc = (arm_cd.SpccArmState(fixture=fixture,
                                         compact_every=self.compact_every)
                     if arm in (arm_cd.ARM_SPCC, "spcc") else None)
        # E7 pin arms: the same compiler plus the PINS layer.  `recency` is the
        # ONLY difference between `pinned` and `pinned-recency` (the ACTIVE line).
        # `compact_every=None`: these arms fold on window pressure (70 % of the
        # fixture's window), not on E2's turn interval -- a fixed interval folds a
        # prompt that never needed to fold (docs/COMPACTION-CACHE-DESIGN.md §5.3).
        self.pinned = (arm_cd.PinnedArmState(
                           fixture=fixture, compact_every=None,
                           recency=(arm == arm_cd.ARM_PINNED_RECENCY),
                           fold_at_fraction=arm_cd.FOLD_AT_FRACTION)
                       if arm in arm_cd.PINNED_ARMS else None)
        # D state
        self.walls = list(fixture.get("lease_reopen_turns") or [])
        self.lease_state = ""
        self.lease = 1
        self.lease_start = 1
        # E7's primary mechanism: a tool call whose (path, start, end) was already
        # read in this cell is a RE-FETCH.  The set is per-cell (one Planner per
        # cell), so a re-read across a fold is counted, which is exactly the cost
        # a fold causes.
        self.seen_ranges = set()

    # -- helpers ---------------------------------------------------------
    def messages(self, user: str) -> list[dict]:
        return [{"role": "system", "content": self.fixture["system_prompt"]},
                {"role": "user", "content": user}]

    def record(self, t: int, answer: str) -> None:
        while len(self.answers) < t - 1:
            self.answers.append("")
        self.answers.append(answer)
        if self.arm == "transcript-compact":
            self.raw.append(turn_block(t, self.fixture["turns"][t - 1], answer))

    def _b_base(self) -> str:
        if self.digest:
            return f"DIGEST OF EARLIER TRANSCRIPT\n{self.digest}\n\n"
        return working_set_block(self.fixture) + "\n\n"

    def _distill(self, upto_turn: int) -> str:
        """Host-side state line (no request): pointers + the tail of this lease's answers."""
        lines = ["POINTERS: " + ", ".join(it["id"] for it in self.fixture["items"])]
        start = max(self.lease_start, upto_turn - 6)
        for i in range(start, upto_turn):
            text = (self.answers[i - 1] or "").replace("\n", " ")[:200] if i - 1 < len(self.answers) else ""
            if text:
                lines.append(f"T{i}: {text}")
        return "\n".join(lines).encode("utf-8")[:1800].decode("utf-8", "ignore")

    def replay(self, rows: list[dict]) -> None:
        """Rebuild prompt state from a partial cell (resume) — no requests."""
        for row in rows:
            t = int(row.get("turn") or 0)
            content = row.get("content") or ""
            if (self.arm == "lease-reopen" and t in self.walls and self.lease_start <= t):
                self.lease_state = self._distill(t)
                self.lease = 1 + sum(1 for w in self.walls if w <= t)
                self.lease_start = t
            if row.get("kind") == "digest":
                self.digest = content
                self.raw = self.raw[-4:]
            else:
                self.record(t, content)

    # -- build -----------------------------------------------------------
    def build(self, t: int) -> dict:
        turn = self.fixture["turns"][t - 1]
        arm = self.arm
        # EVICTED-ABSENT: `evicted` is the number of tool-output entries THIS turn's
        # prompt no longer carries that it otherwise would.  An arm that has no eviction
        # concept must leave it null: 0 asserts a measurement nobody made, and on the
        # masking arm 0 was stamped on the very turn its only fact was masked away.
        # Every arm that measures eviction assigns it below; the rest stay None.
        info: dict = {"t": t, "turn": turn, "digest_request": None, "evicted": None,
                      "lease": None, "prefix_sha256": None}
        if arm == "transcript-grow":
            parts = [working_set_block(self.fixture)]
            parts += [turn_block(i, self.fixture["turns"][i - 1], self.answers[i - 1])
                      for i in range(1, t) if i - 1 < len(self.answers)]
            current = turn_user(t, turn)
            evicted = 0
            # FIFO over HISTORY, never over the pinned working set.  `parts[0]` is the
            # fixture's pinned corpus; popping it (the pre-v8 `parts.pop(0)`) means the
            # first eviction of any firing grow cell deletes the corpus the checkpoints are
            # answered from, so the arm would measure amnesia, not eviction.  Index 0 is
            # therefore pinned and the oldest HISTORY block goes first.  This cannot alter
            # any row already on disk: `evicted > 0` on 0 rows of the pinned corpus.
            while len(parts) > 1 and est_tokens("\n\n".join(parts + [current]), self.bpt) > self.wall_tokens:
                parts.pop(1)
                evicted += 1
            text = "\n\n".join(parts + [current])
            if est_tokens(text, self.bpt) > self.wall_bytes:
                keep = int(self.wall_bytes)
                cut = text.encode("utf-8")[-keep:]
                text = cut.decode("utf-8", "ignore").split("\n", 1)[-1]
                evicted += 1
            info["evicted"] = evicted
            info["prompt"] = text
            return info

        if arm == "transcript-compact":
            current = turn_user(t, turn)
            base = self._b_base()
            window = base + "\n\n".join(self.raw + [current])
            if t > 1 and est_tokens(window, self.bpt) > self.wall_tokens:
                transcript = base + "\n\n".join(self.raw)
                instruction = (
                    "COMPRESS the transcript below into at most 700 tokens. Preserve every item id, "
                    "every audit/retention code, and every correction.\n\nTRANSCRIPT:\n" + transcript
                )
                info["digest_request"] = self.messages(instruction)
                if self.dry_run:
                    self.digest = "<<digest produced by the digest request at this turn (dry-run placeholder)>>"
                    self.raw = self.raw[-4:]
                    base = self._b_base()
            info["prompt"] = base + "\n\n".join(self.raw + [current])
            return info

        if arm == "pointer-stable":
            upto = min(t + 1, len(self.fixture["items"]))
            bodies = "\n".join(body_block(it) for it in self.fixture["items"][:upto])
            prefix = f"INDEX\n{index_lines(self.fixture)}\n{bodies}"
            info["prefix_sha256"] = sha256_text(prefix)
            tail = ["STATE"]
            for i in range(max(1, t - 3), t):
                ans = self.answers[i - 1] if i - 1 < len(self.answers) else ""
                tail.append(f"T{i}: {ans.replace(chr(10), ' ')[:120]}")
            if len(tail) == 1:
                tail.append("(no prior turns in this lease)")
            note = turn.get("note")
            if note:
                tail.append(f"[WORK NOTE {note.get('id', 'n' + str(t))}]\n{note['body']}")
            tail.append(f"QUESTION (T{t}): {turn['question']}")
            info["prompt"] = prefix + "\n\n" + "\n".join(tail)
            return info

        if arm == "lease-reopen":
            if t in self.walls and self.lease_start <= t:
                self.lease_state = self._distill(t)
                self.lease = 1 + sum(1 for w in self.walls if w <= t)
                self.lease_start = t
            info["lease"] = self.lease
            note = turn.get("note")
            text = f"INDEX\n{index_lines(self.fixture)}\n"
            if self.lease_state:
                closed = min([w for w in self.walls if w <= t], default=0)
                text += f"\nLEASE STATE (closed at T{closed})\n{self.lease_state}\n"
            text += "\n"
            if note:
                text += f"[WORK NOTE {note.get('id', 'n' + str(t))}]\n{note['body']}\n"
            text += f"QUESTION (T{t}): {turn['question']}"
            info["prompt"] = text
            return info

        if arm == arm_cd.ARM_SPCC:
            # spcc: stable-prefix compiler.  The question leads L3; any tool output
            # the FIXTURE delivers this turn follows it in arrival order, enters L3
            # now and rides the journal line so it persists in L2 until compaction.
            # Model-initiated fetches stay on add_fetch (L3 only, never L0/L1/L2).
            state = self.spcc
            question = turn_user(t, turn)
            for to in _turn_tool_outputs(turn):
                body = to.get("body")
                if body is not None:
                    state.add_delivery(str(body))
            prompt = state.build(t, question)
            info["prompt"] = str(prompt)
            info["prefix_sha256"] = prompt.prefix_sha256
            info["epoch"] = prompt.epoch
            info["compactions"] = prompt.compactions
            info["layer_tokens"] = dict(prompt.layer_tokens)
            return info

        if arm in arm_cd.PINNED_ARMS:
            # E7 pin arms: rendered by the layer compiler, with PINS carrying the
            # durable facts (the PLAN pin, the agent's pins, the fold record).
            # The question leads L3; fixture deliveries follow it and ride the
            # journal line; model-initiated fetches stay L3-only.  No body is
            # pinned, so every tool call is a real fetch -- which is what makes
            # `refetch_count` measurable on this arm.
            state = self.pinned
            question = turn_user(t, turn)
            for to in _turn_tool_outputs(turn):
                body = to.get("body")
                if body is not None:
                    state.add_delivery(str(body))
            prompt = state.build(t, question)
            info["prompt"] = str(prompt)
            info["prefix_sha256"] = prompt.prefix_sha256
            info["epoch"] = prompt.epoch
            info["compactions"] = prompt.compactions
            info["layer_tokens"] = dict(prompt.layer_tokens)
            return info

        if arm in (arm_cd.ARM_C, arm_cd.ARM_D):
            # C / D: masking of tool-output turns older than the window; D adds fetch.
            state = self.arm_cd
            masked_rows, masked_entry = state.mask_old_turns(t)
            # checkpoint only on forecast for D
            checkpoint_val = None
            if arm == arm_cd.ARM_D:
                # forecast: checkpoint when this turn is a declared checkpoint turn
                if t in checkpoint_turns(self.fixture):
                    checkpoint_val = next((c for c in (self.fixture.get("checkpoints") or [])
                                          if int(c.get("turn", -1)) == int(t)), None)
                    state.checkpoint_forecast = True
                else:
                    state.checkpoint_forecast = False
            # prompt: transcript of recent turns with masked markers for old ones
            parts = [working_set_block(self.fixture)]
            for i in range(1, t):
                if i in state.masked_turns:
                    turn_i = self.fixture["turns"][i - 1] if (i - 1 < len(self.fixture.get("turns", []))) else None
                    tos_i = _turn_tool_outputs(turn_i) if isinstance(turn_i, dict) else []
                    # marker in place of body. Derive markers from the turn's own
                    # tool_outputs so dedup across turns does not leave a body unmasked.
                    markers = []
                    for to in tos_i:
                        did = to.get("doc_id")
                        rev = to.get("revision")
                        if rev is None:
                            raise ValueError("tool_output missing required field: revision")
                        markers.append(f"[MASKED {make_ref(did, rev)}]")
                    if tos_i:
                        # Mask prior answers on masked turns so an earlier checkpoint's
                        # value cannot be copied without recovering the fact.
                        parts.append(turn_block(i, self.fixture["turns"][i - 1], "",
                                                masked=True, markers=markers))
                    elif i - 1 < len(self.answers):
                        parts.append(turn_block(i, self.fixture["turns"][i - 1], self.answers[i - 1]))
                elif i - 1 < len(self.answers):
                    parts.append(turn_block(i, self.fixture["turns"][i - 1], self.answers[i - 1]))
            current = turn_user(t, turn)
            # Render the current turn's tool outputs on their delivery turn (not only
            # when replaying earlier turns), so bodies declared on T1 appear in T1.
            tos_cur = _turn_tool_outputs(turn)
            if tos_cur:
                current = current + "\nTOOL OUTPUTS:\n" + "\n".join(
                    "TOOL_OUTPUT (%s@%s): %s" % (to.get("doc_id"), to.get("revision"), to.get("body"))
                    for to in tos_cur)
            text = "\n\n".join(parts + [current])
            info["masked_rows"] = masked_rows
            # EVICTED-ABSENT (rule 1): for the masking arm a masked entry IS the eviction:
            # the body the prompt used to carry is gone, replaced by a pointer marker.
            # The two fields are the same event, so they carry the same number -- and
            # `evicted` no longer stays at its (removed) 0 default, which reported
            # "nothing evicted" on the turn the arm's only fact was masked.
            info["evicted"] = masked_rows
            info["masked_entry"] = masked_entry
            info["checkpoint"] = checkpoint_val
            info["prompt"] = text
            return info

        raise ValueError(f"unknown arm {arm!r}")


# ---------------------------------------------------------------- activation predicates (gate 0.6)
# A cell failing its own predicate is INVALID-INSTRUMENT: computed from the stamp,
# never by name.  The five context arms (A-E) and their declared predicates.
ACTIVATION_PREDICATES = {
    "A": "evicted_turns",
    "B": "digest_rows",
    "C": "masked_rows",
    "D": "fetch_rows",
    "E": "oracle_injections",
}


def _activation_counts(rows):
    rows = list(rows or ())
    return {
        "evicted_turns": sum(1 for r in rows if (r.get("evicted") or 0) > 0
                             or (r.get("evicted_turns") or 0) > 0),
        "digest_rows": sum(1 for r in rows if r.get("kind") == "digest"
                           or (r.get("digest_rows") or 0) > 0),
        "masked_rows": sum(1 for r in rows if (r.get("masked_rows") or 0) > 0),
        "fetch_rows": sum(1 for r in rows if (r.get("fetch_rows") or 0) > 0
                          or (r.get("retrieval_attempts") or 0) > 0),
        "retrieval_outcomes": [o for r in rows for o in (r.get("retrieval_outcomes") or [])],
        "oracle_injections": sum(1 for r in rows if (r.get("oracle_injections") or 0) > 0),
    }


def activation_predicate(arm, rows) -> bool:
    """Computed predicate for one arm. A failing cell is INVALID-INSTRUMENT."""
    counts = _activation_counts(rows)
    arm = str(arm or "").strip().upper()
    # accept long names too
    name = str(arm).lower()
    if arm in ("A",) or "transcript" == name or "full-transcript" in name or "full_transcript" in name:
        return counts["evicted_turns"] > 0
    if arm in ("B",) or "compact" in name:
        return counts["digest_rows"] > 0
    if arm in ("C",) or "mask" in name:
        return counts["masked_rows"] > 0
    if arm in ("D",) or "bounded" in name or "recoverable" in name:
        return counts["fetch_rows"] > 0 and len(counts["retrieval_outcomes"]) > 0
    if arm in ("E",) or "oracle" in name:
        return counts["oracle_injections"] > 0
    # unknown arm: no predicate to pass -> not instrumented
    return False


def instrument_status(arm, rows) -> str:
    return "INVALID-INSTRUMENT" if not activation_predicate(arm, rows) else "VALID"


# aliases
arm_activation_predicate = activation_predicate
predicate_for_arm = activation_predicate
activation_predicates = ACTIVATION_PREDICATES

# ------------------------------------------------------------------------ treatments
# A treatment that cannot fire inside the frozen horizon is not a treatment: the cell then
# measures the control path and the arm label is a lie (measured: evicted>0 on 0 rows,
# lease>1 on 0 rows, digest rows 0 of 576).  The three predicates are quoted from this file:
#   grow    : evicted>0           (`while len(parts) > 1 and est_tokens(...) > wall_tokens`)
#   compact : digest_at is not None (a bottom-of-window digest request; no digest row needed)
#   reopen  : lease>1             (`t in self.walls`, self.walls = lease_reopen_turns)
# Everything below is OFFLINE and derived from the fixture alone -- zero inference requests.

def answer_padding_by_turn(fixture: dict) -> list[int]:
    """Per-turn ceiling on what a LEGAL answer adds to the window, in tokens.

    Taken from the fixture's own `answer_budget.words_per_turn_kind` (the declared per-kind
    ceiling), never from a measured slope: the measured slope conflates the treatment with
    answer verbosity (within grid G4 the grow cell's answers ran ~9x longer than the
    compact cell's), so the declared budget is the only estimate comparable across arms.
    """
    budget = fixture.get("answer_budget") or {}
    kinds = {str(k): int(v) for k, v in (budget.get("words_per_turn_kind") or {}).items()}
    if not kinds:
        kinds = {"work": 150, "checkpoint": 400, "verify": 400}
    tpw = float(budget.get("tokens_per_word_assumed") or 1.35)
    default = max(kinds.values())
    return [int(ceil(kinds.get(str(turn.get("kind") or "work"), default) * tpw))
            for turn in fixture["turns"]]


def answer_padding_tokens(fixture: dict) -> int:
    """The largest per-turn answer padding this fixture permits (the reported ceiling)."""
    return max(answer_padding_by_turn(fixture) or [0])


def wall_for_arm(fixture: dict, arm: str) -> int:
    """The wall this arm runs at: a per-arm value when the fixture declares one.

    One wall copied across arms measures verbosity as much as treatment, so a fixture may
    declare `wall_tokens_by_arm` (fixture field, not a CLI default) naming the wall each
    arm needs for its predicate to fire inside the horizon.
    """
    by_arm = fixture.get("wall_tokens_by_arm") or {}
    if by_arm:
        # A declared per-arm block is AUTHORITATIVE: an arm absent from it is a fixture
        # defect, never an invitation to run at the top-level wall. That fallback is the
        # trap this field closes — v8's top-level 3838 sits below its own first prompt
        # (3848), so a fallback fires the wall at ~turn 2 and erases the contrast between
        # transcript-grow and transcript-compact.
        if arm not in by_arm:
            raise FixtureError(
                f"fixture declares 'wall_tokens_by_arm' but has no wall for arm {arm!r} "
                f"(declared: {sorted(by_arm)}); refusing rather than falling back to "
                f"wall_tokens={fixture.get('wall_tokens')!r}")
        return int(by_arm[arm])
    if "wall_tokens" not in fixture:
        raise FixtureError(f"fixture declares no wall for arm {arm!r}: neither a "
                           "'wall_tokens_by_arm' entry nor a top-level 'wall_tokens'")
    return int(fixture["wall_tokens"])


def fixture_for_arm(fixture: dict, arm: str) -> dict:
    """The fixture as this arm must run it (per-arm wall substituted; same object if equal)."""
    wall = wall_for_arm(fixture, arm)
    if "wall_tokens" in fixture and wall == int(fixture["wall_tokens"]):
        return fixture
    fx = dict(fixture)
    fx["wall_tokens"] = wall
    return fx


def _padding_answers(fixture: dict, n_turns: int) -> list[str]:
    bpt = float(fixture["bytes_per_token"])
    pads = (answer_padding_by_turn(fixture) + [answer_padding_tokens(fixture)] * n_turns)
    return ["a" * max(1, int(pads[t - 1] * bpt)) for t in range(1, n_turns + 1)]


def _digest_filler(fixture: dict) -> str:
    return "d" * max(1, int(DIGEST_MAX_TOKENS * float(fixture["bytes_per_token"])))


def _simulate(fixture: dict, arm: str, n_turns: int):
    """Drive the REAL Planner offline with a LEGAL ceiling answer on every turn.

    Yields (turn, info) for every turn and keeps the planner state the production cell
    keeps: a digest replaces the window and drops the raw blocks to the last four.
    """
    fx = fixture_for_arm(fixture, arm)
    planner = Planner(arm, fx, dry_run=True)
    answers = _padding_answers(fx, n_turns)
    for t in range(1, n_turns + 1):
        info = planner.build(t)
        if info.get("digest_request") is not None:
            planner.digest = _digest_filler(fx)
            planner.raw = planner.raw[-4:]
        yield t, info
        planner.record(t, answers[t - 1])


def treatment_fire_turns(fixture: dict, arm: str, horizon: int = HORIZON_TURNS) -> dict:
    """First turn on which each treatment fires, computed offline from the fixture.

    `None` means "does not fire inside the horizon" and is a launch refusal, not a note.
    Because the padding is the fixture's own MAXIMUM legal answer, the estimate is an
    upper bound on the window and therefore a lower bound on the fire turn: conservative.
    """
    fx = fixture_for_arm(fixture, arm)
    fires = {"grow": None, "wall": None, "lease": None, "prefix": None,
             "prefix_first": None, "wall_tokens": int(fx["wall_tokens"]),
             "answer_padding_tokens": answer_padding_tokens(fx), "horizon": int(horizon)}
    for t, info in _simulate(fx, arm, int(horizon)):
        if fires["grow"] is None and int(info.get("evicted") or 0) > 0:
            fires["grow"] = t
        if fires["wall"] is None and info.get("digest_request") is not None:
            fires["wall"] = t
        if fires["lease"] is None and int(info.get("lease") or 1) > 1:
            fires["lease"] = t
        prefix = info.get("prefix_sha256")
        if prefix:
            if fires["prefix_first"] is None:
                fires["prefix_first"] = prefix
            elif fires["prefix"] is None and prefix != fires["prefix_first"]:
                fires["prefix"] = t
    fires["fires"] = {k: fires[k] for k in ("grow", "wall", "lease", "prefix")}
    fires["reasons"] = treatment_refusals(fx, arm, fires)
    fires["ok"] = not fires["reasons"]
    return fires


def treatment_refusals(fixture: dict, arm: str, fires: dict) -> list[str]:
    """Named reasons the launch must be refused (empty list == every treatment is live)."""
    horizon = int(fires.get("horizon") or HORIZON_TURNS)
    wall = int(fires.get("wall_tokens") or wall_for_arm(fixture, arm))
    out: list[str] = []
    if arm == "transcript-grow" and fires.get("grow") is None:
        out.append(f"first FIFO truncation > {horizon} turns at wall_tokens={wall} "
                   f"(grow never evicts: the prompt never exceeds the wall inside the horizon)")
    if arm == "transcript-compact" and fires.get("wall") is None:
        out.append(f"first wall > {horizon} turns at wall_tokens={wall} "
                   f"(compact never requests a digest inside the horizon)")
    if arm == "lease-reopen":
        if not (fixture.get("lease_reopen_turns") or []):
            out.append("missing fixture field 'lease_reopen_turns' — the lease can never "
                       "step, so the reopen arm is the pointer arm with a different label")
        elif fires.get("lease") is None:
            out.append(f"first lease step > {horizon} turns (declared lease_reopen_turns="
                       f"{fixture.get('lease_reopen_turns')} lie outside the horizon)")
    if arm == "pointer-stable" and fires.get("prefix") is None:
        out.append(f"the pinned prefix never changes inside {horizon} turns, so prefix "
                   f"stability has nothing to be stable against")
    return out


def treatment_report(fixture: dict, arm: str, horizon: int = HORIZON_TURNS) -> list[str]:
    """The three (four) facts a dry run must print before it may launch anything."""
    fires = treatment_fire_turns(fixture, arm, horizon)
    def _show(v):
        return f"T{v}" if v is not None else f"> {horizon} (NEVER inside the horizon)"
    lines = [f"  [{arm}] wall_tokens={fires['wall_tokens']} "
             f"answer_padding={fires['answer_padding_tokens']} tok/turn "
             f"horizon={horizon}",
             f"  [{arm}] first FIFO truncation at turn {_show(fires['grow'])}",
             f"  [{arm}] first wall at turn {_show(fires['wall'])}",
             f"  [{arm}] first lease step at turn {_show(fires['lease'])}"
             + ("" if arm == "lease-reopen" else f"  (declared {fixture.get('lease_reopen_turns')}"
                f", no lease in this arm)"),
             f"  [{arm}] first prefix change at turn {_show(fires['prefix'])}"
             + ("" if arm in ("pointer-stable",) + arm_cd.PINNED_ARMS
                else "  (pointer-stable's own treatment)")]
    for reason in fires["reasons"]:
        lines.append(f"  [{arm}] TREATMENT UNREACHABLE: {reason}")
    return lines


def check_treatments(fixture: dict, arm: str, horizon: int = HORIZON_TURNS) -> tuple[int, list[str]]:
    """Launch precondition: (0, lines) or (EXIT_TREATMENTS_UNREACHABLE, lines).

    Exposed as a callable so `cell.py` (owned elsewhere) can call the SAME assertion; the
    runner applies it in `--dry-run` AND at the top of `run_cell`, so no path reaches the
    wire with a treatment that cannot fire.
    """
    if not fixture.get("treatments"):
        # The contract is declared by the fixture (v8+).  The frozen v5/v6/v7 fixtures are
        # evidence, not cells to relabel, so they are not retro-armed; every fixture that
        # adopts `treatments` IS gated, and the red-case test proves it refuses.
        return 0, [f"  [{arm}] treatments contract not declared by this fixture — not gated"]
    fires = treatment_fire_turns(fixture, arm, horizon)
    lines = treatment_report(fixture, arm, horizon)
    return (0 if fires["ok"] else EXIT_TREATMENTS_UNREACHABLE), lines


def expected_digests(fixture: dict) -> int:
    """The digest-request CEILING for one transcript-compact cell, DERIVED from the fixture.

    A function of the declared turns, `wall_tokens` (per arm) and the fixture's own
    maximum legal answer — not the literal 2 that aborted a legal cell at exit 4 when a
    third digest fired.  A fixture whose wall is never reached inside the horizon projects
    0 digests and reserves 0 requests, so the projection and the dry run cannot disagree.
    """
    fx = fixture_for_arm(fixture, "transcript-compact")
    digests = 0
    for _t, info in _simulate(fx, "transcript-compact", int(fx["N"])):
        if info.get("digest_request") is not None:
            digests += 1
    return digests


# ----------------------------------------------------------------------- manifest
def build_manifest(cfg, fixture: dict, arm: str, rep: int, run_id: str, rows_path: str,
                   cap_gate: dict | None = None) -> dict:
    if getattr(cfg, "dry_run", False):
        _fingerprints = {
            "model": {"id": UNSOURCEABLE, "revision_quantisation_digest": UNSOURCEABLE,
                      "probe": "dry-run: network probe skipped"},
            "tokenizer": {"files_hash": UNSOURCEABLE, "chat_template_hash": UNSOURCEABLE,
                          "probe": "dry-run: network probe skipped"},
            "renderer": {"content_digest": UNSOURCEABLE,
                         "probe": "dry-run: network probe skipped"},
            "engine": {"image_digest": UNSOURCEABLE, "exact_argv": UNSOURCEABLE,
                       "probe": "dry-run: network probe skipped"},
            "endpoints": [],
            "completion_paths_touched": [],
            "completion_paths_avoided": [],
        }
    else:
        _fingerprints = probe_fingerprints(cfg)
    return {
        # WIRE-CAP-GATE: the declared allocation and the run-start spend are frozen in the
        # manifest BEFORE the first request; the running and final counts are added to this
        # same block at exit by _gate_finish (additive; no existing key changes meaning).
        **({"cap_gate": cap_gate} if cap_gate is not None else {}),
        "schema": "consonance.longrun-manifest/1",
        "run_id": run_id,
        "created_utc": iso(utc_now()),
        "dry_run": bool(cfg.dry_run),
        # Thinking switch (consonance.longrun-manifest/1, added RUNNER-THINKING-FLAG).
        # "auto" = the key is absent from the request body (byte-identical to pre-flag runs);
        # rows from different settings must never be pooled, so it is frozen here AND per row.
        "thinking": thinking_setting(cfg),
        # WIRE-CLIENT: the effective /metrics-scrape value, resolved by the client's own
        # precedence rule (CLI flag > PTR_METRICS_SCRAPE > default). Frozen here and
        # stamped on every row, because rows scraped with the counters and rows without
        # them must never be silently pooled.
        "metrics_scrape": client.resolve_metrics_scrape(cfg),
        "arm": arm,
        "rep": rep,
        "generation": getattr(cfg, "generation", "gen-7"),
        "N": int(fixture["N"]),
        "model": {
            "name": cfg.model,
            "endpoint": cfg.base_url.rstrip("/"),
            "engine": cfg.engine,
            "tokenizer": "server-reported (usage.prompt_tokens); no client tokenizer",
            "id": _fingerprints["model"]["id"],
            "revision_quantisation_digest": _fingerprints["model"]["revision_quantisation_digest"],
            "probe": _fingerprints["model"]["probe"],
        },
        "renderer": {
            "api": "POST /chat/completions",
            "stream": bool(cfg.stream),
            "include_usage": bool(cfg.stream),
            "temperature": getattr(cfg, "temperature", 0),
            "seed": getattr(cfg, "seed", 42),
            "max_tokens": int(cfg.max_tokens),
            "thinking": thinking_setting(cfg),
            "chat_template_kwargs": thinking_kwargs(thinking_setting(cfg)),
            "messages": "system + user; content is one user string per turn",
            "module_content_digest": _fingerprints["renderer"]["content_digest"],
        },
        "engine_flags": {
            "ctx_window": int(fixture.get("window_tokens", 131072)),
            "design_cap_tokens": int(fixture["wall_tokens"]),
            "cache_block_tokens": 64,
            "concurrency_B": 64,
            "source": "LONGRUN-PREREG §0/§2; RECORD.md C5 (cached = P1 - P1 mod 64)",
            "knowable": "ctx/cap/block from the prereg; server build flags are not exposed via /v1",
            "image_digest": _fingerprints["engine"]["image_digest"],
            "exact_argv": _fingerprints["engine"]["exact_argv"],
            "probe": _fingerprints["engine"]["probe"],
        },
        "fixture": {
            "path": fixture["_path"],
            "sha256": fixture["_sha256"],
            "schema": fixture["schema"],
            "task_id": fixture["task_id"],
            "bytes_per_token": float(fixture["bytes_per_token"]),
            "wall_tokens": int(fixture["wall_tokens"]),
        },
        "prereg": {
            "path": "experiments/ptr-engine/LONGRUN-PREREG.md",
            "sha256": sha256_file("experiments/ptr-engine/LONGRUN-PREREG.md")
            if os.path.exists("experiments/ptr-engine/LONGRUN-PREREG.md") else None,
        },
        "prediction": PREDICTIONS[arm],
        # ROW-PROVENANCE: the SAME nine-field block every row carries, published once per
        # cell, so a later reader can read a cell's provenance from the manifest instead
        # of re-deriving it row by row.  ``fixture_id`` is <task_id>.<fixture_version>,
        # ``harness_sha256`` is the digest cell.py would freeze for this tree.
        "provenance": provenance_for(cfg, fixture, arm),
        "fingerprints": _fingerprints,
        "rows_path": rows_path,
        # FETCH-CHANNEL: present only on a --tools run, so a tools-off manifest keeps
        # the exact bytes it had before this flag existed.
        **({"tools": {"names": tool_names(cfg), "max_calls_per_turn": TOOL_CALLS_PER_TURN,
                      "max_fetch_rounds_per_arm": fetch_rounds_per_arm(cfg),
                      # PROBE-CP3-V6 (b): a recon burst may not spend the cell.  Frozen here
                      # and stamped on every row as `fetch_rounds_cap_per_turn`.
                      "max_fetch_rounds_per_turn": fetch_rounds_per_turn(cfg),
                      "fetch_policy": getattr(cfg, "fetch_policy", "strict"),
                      # PROBE-CP3-V6 (a): a range already inside the pinned prompt bodies is
                      # served from the prompt and bills no round.
                      "serve_from_prompt": bool(TOOL_SERVE_FROM_PROMPT),
                      # the follow-up REQUEST allowance (rounds + prompt serves share it),
                      # with one request reserved for every not-yet-reached declared
                      # checkpoint so no earlier burst can starve T12/T24/T46.
                      "followup_request_pool": fetch_rounds_per_arm(cfg),
                      "followup_reserve_per_checkpoint": True,
                      # durable spend: frozen at creation, and on --resume the counter is
                      # max(this, rounds derived from the cell's own rows)
                      "fetch_rounds_used": 0,
                      "path_bases": ["workspace", ENGINE_ROOT_REL],
                      "duplicate_fetch": "cached, billed once per turn",
                      "read_cap_lines": TOOL_READ_CAP_LINES,
                      "read_cap_chars": TOOL_READ_CAP_CHARS,
                      "followups_are_requests": True}}
           if tools_enabled(cfg) else {}),
    }


def write_manifest(path: str, doc: dict) -> tuple[bytes, str]:
    """Write the frozen manifest atomically; fail loudly (never start a run without it)."""
    data = (json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return data, sha256_bytes(data)


# ------------------------------------------------------------------- HTTP / usage
# ONE streaming implementation, and it lives in client.py.
#
# WIRE-CLIENT deleted the inline SSE loop that used to sit here (:1033-1137) together with
# its latch on (piece_c or piece_r) -- a latched perf_counter delta guarded only by "ttft
# is None", i.e. TTFT was never recorded for a first delta carrying only ``tool_calls``.
# That latch was blind to a first delta carrying only ``tool_calls``, so a tool-call-first
# turn recorded no TTFT at all; the survey found exactly that contaminating the p95
# sample.  client.collect_stream latches on the first delta carrying content OR
# reasoning_content OR tool_calls, and reports ``ttft_source``/``first_token_kind`` so a
# null can never be mistaken for a wall-clock substitute.
#
# The names below are re-exported rather than re-implemented:
#   * the tool-channel tests monkeypatch ``run_longrun.send_chat``, so the adapter keeps
#     that single seam while performing no parsing, no timing and no scraping of its own;
#   * request_body/thinking_* stay module names because the manifest and the dry-run
#     preview hash request bodies through them (client.request_body is byte-identical:
#     model, messages, temperature 0, max_tokens, stream, include_usage, chat_template_kwargs).
#
# A second copy is how this defect happened.  tests/test_wire_client.py carries a
# source-level audit that fails if run_longrun.py ever grows its own perf_counter-delta
# TTFT again.
RequestFailure = client.RequestFailure
thinking_setting = client.thinking_setting
thinking_kwargs = client.thinking_kwargs
request_body = client.request_body
extract_usage = client.extract_usage


def send_chat(cfg, messages: list[dict]) -> dict:
    """Send one request through the single streaming implementation (client.send_chat).

    Deliberately a one-line delegation: every measured field on the returned dict —
    ttft_ms, ttft_source, first_token_kind, cached_tokens, cached_source,
    engine_metrics_before/_after, wall_ms — is produced by client.py and passed through
    to the row unchanged by make_row().
    """
    return client.send_chat(cfg, messages)



# ------------------------------------------------------------ reasoning policy
# occamy-1.0 is a reasoning model: it streams `delta.reasoning_content` before any
# `delta.content`, and it will spend an unbounded budget on the reasoning channel.
# Raising max_tokens alone therefore cannot deliver "0 truncated" (RUN-STAGE1-LR01:
# 4096 still truncated grow T3 with `content_source="reasoning"` and no answer).
# The policy below is explicit and is applied to EVERY row:
#   answer_source="content"            the content channel carries text (clean).
#   answer_source="reasoning-fallback" no content, but the reasoning channel either
#                                      completed (finish_reason != "length") or the
#                                      checkpoint's expected value appears in it
#                                      verbatim.  Marked, never mixed with clean rows.
#   answer_source="none"               no answer-bearing text: a failed turn.
#   failed_turn = truncated and the expected value is absent: the answer is
#   incomplete, so the row never enters a latency average as a success.
_REASONING_POLICY = "content-channel-first; reasoning-only accepted only when complete "\
                    "or carrying the checkpoint expected value verbatim; truncated rows "\
                    "without the expected value are failed turns"
_TOKENIZER = None
_TOKENIZER_METHOD = None


def count_channel_tokens(text: str, fallback_bpt: float = 4.0477) -> tuple[int, str]:
    """Token count for one channel. tiktoken cl100k_base when importable (the fixture's
    own estimator, see adapt_fixture.py), else bytes / fixture bytes_per_token."""
    global _TOKENIZER, _TOKENIZER_METHOD
    if not text:
        return 0, (_TOKENIZER_METHOD or "tiktoken:cl100k_base")
    if _TOKENIZER is None:
        try:
            import tiktoken  # type: ignore
            _TOKENIZER = tiktoken.get_encoding("cl100k_base")
            _TOKENIZER_METHOD = "tiktoken:cl100k_base"
        except (ImportError, OSError, RuntimeError, ValueError, AttributeError, TypeError, LookupError) as exc:
            _TOKENIZER = False
            _TOKENIZER_METHOD = f"bytes/{fallback_bpt:g} (fixture bytes_per_token) [{type(exc).__name__}]"
    if _TOKENIZER:
        return len(_TOKENIZER.encode(text, disallowed_special=())), _TOKENIZER_METHOD
    return int(ceil(len(text.encode("utf-8")) / float(fallback_bpt or 4.0))), _TOKENIZER_METHOD


def checkpoint_expected(fixture: dict, t: int) -> tuple[str | None, str | None]:
    for cp in fixture.get("checkpoints") or []:
        if int(cp.get("turn", -1)) == int(t):
            return cp.get("expected"), cp.get("question")
    return None, None


def _squash(text: str) -> str:
    return " ".join((text or "").split()).lower()


def contains_expected(text: str, expected: str | None) -> bool:
    if not expected:
        return False
    return _squash(expected) in _squash(text)


# EXPECTED-PRESENT-PROMPT: `expected_present` answers ONE question -- does the rendered
# prompt this checkpoint is answered from still carry the checkpoint's expected value?
# It used to be computed from the RESPONSE's reasoning channel, which is empty whenever
# thinking is off, so it read False on every checkpoint -- including the ones answered
# correctly -- and could not support any claim about absence.  ABSENT is not False:
# no checkpoint -> null; no retained prompt -> null, and the source says why.
_EXPECTED_NUMERIC_RE = re.compile(r"-?\d+")


def expected_value_in_prompt(prompt_text: str | None, expected: str | None):
    """``(present | None, source)`` for ``expected`` in THIS turn's rendered prompt."""
    if expected is None or str(expected).strip() == "":
        return None, "no-checkpoint"
    if prompt_text is None:
        return None, "no-prompt-retained"
    value = str(expected).strip()
    if not _EXPECTED_NUMERIC_RE.fullmatch(value):
        # A non-numeric expectation ("NONE" on the absence spine) is not a value a prompt
        # can carry: searching for that word would match the QUESTION, not an assertion.
        return None, "expected-non-numeric"
    # digit-boundary guard: 3001 must not match inside 13001 or 3001.5
    if re.search(r"(?<![\d.])%s(?![\d.])" % re.escape(value), prompt_text):
        return True, "prompt-digit-boundary"
    # the binding anchor: `VAL_A = 3001` survives any prose reformatting of the body
    if re.search(r"VAL_[A-Za-z0-9_]+\s*=\s*%s(?![\d.])" % re.escape(value), prompt_text):
        return True, "prompt-val-anchor"
    return False, "prompt-absent"


# ------------------------------------------------------------------ answer contract
# ANSWER-CONTRACT (v5): at a checkpoint turn the tools are OFF, the checkpoint
# question is injected, and the reply is parsed into a VALUE (NUM / CALL / NONE /
# TEXT) instead of being graded as prose. The contract text below is host-side
# only: it names no source, no file and no expected value.
CHECKPOINT_CONTRACT_LINE = (
    "\n\nCHECKPOINT TURN.\n"
    "Emit exactly one line and nothing else, in this contract:\n"
    "  ANSWER: NUM <integer>\n"
    "  ANSWER: CALL <callee>(<kw>=<value>, <kw>=<value>, ...)\n"
    "  ANSWER: NONE\n"
    "  ANSWER: TEXT <one line of prose>\n"
    "For CALL, put the keyword arguments in alphabetical order and give each value as "
    "the source text shows it. Anything written after that line is not read.")


def checkpoint_turns(fixture: dict) -> list[int]:
    """Turns that demand a contracted answer.

    `fixture["checkpoint_turns"]` is authoritative when present (v5); older fixtures
    declare only `checkpoints[].turn`, which is the same set - recognised either way.
    """
    declared = fixture.get("checkpoint_turns")
    if declared:
        return sorted(int(t) for t in declared)
    return sorted(int(c.get("turn", -1)) for c in (fixture.get("checkpoints") or []))


def checkpoint_prompt(fixture: dict, t: int, prompt: str, arm: str = None, fetch_policy: str = "strict") -> str:
    """The turn prompt with the checkpoint question (if absent) and the contract line.

    Host-side only: no request is made, no source is read, and only the checkpoint's
    QUESTION is copied - never its expected value.
    """
    cp = next((c for c in (fixture.get("checkpoints") or [])
               if int(c.get("turn", -1)) == int(t)), None)
    question = (cp or {}).get("question") or ""
    text = prompt
    if question and _squash(question) not in _squash(prompt):
        text = text + "\n\nCHECKPOINT QUESTION: " + question
    # Idempotent: do not append the contract line a second time if it is already
    # present (e.g. a prompt re-assembled through a tool-follow-up path).
    _already = "CHECKPOINT TURN." in text
    if arm == arm_cd.ARM_D:
        _policy_line = ""
        if (fetch_policy or "strict") == "instructed":
            _policy_line = ("POLICY: A value that is not visible in the current context "
                            "must be retrieved with the fetch tool before answering; "
                            "answering from memory when the value is not in view is not "
                            "acceptable.\n")
        contract = (
            "\n\nCHECKPOINT TURN.\n"
            + _policy_line +
            "Every fact you need may sit behind a marker of the form "
            "`[MASKED <ref>]`, where `<ref>` is exactly `doc-<name>@r<revision>` "
            "(for example `[MASKED doc-constants@r1]`).\n"
            "Two protocols, kept separate:\n"
            "(1) RETRIEVAL. When markers are present you MUST, in a single round, "
            "issue one fetch call for EVERY ref that appears as a `[MASKED <ref>]` "
            "marker, then answer from the returned bodies. Answering before fetching "
            "every marker is a protocol violation and is recorded as "
            "`retrieval_omitted`. Worked example (two calls in one round): "
            "fetch(ref=\"doc-config@r1\") and fetch(ref=\"doc-constants@r1\").\n"
            "(2) ANSWERING. While working a turn you MAY reply with a TOOL CALL "
            "instead of an `ANSWER:` line. A tool call is NOT an answer and must "
            "NOT carry the `ANSWER:` prefix. Use the structured shape the tool "
            "schema expects, e.g. "
            "{\"name\":\"fetch\",\"arguments\":{\"ref\":\"doc-config@r1\"}}. "
            "One round may contain several such calls, e.g. three: "
            "{\"name\":\"fetch\",\"arguments\":{\"ref\":\"doc-config@r1\"}}, "
            "{\"name\":\"fetch\",\"arguments\":{\"ref\":\"doc-constants@r1\"}}, "
            "{\"name\":\"fetch\",\"arguments\":{\"ref\":\"doc-errors@r1\"}}. "
            "After the tool results come back, reply with the `ANSWER:` line.\n"
            "`ANSWER: CALL <name>(...)` is reserved for an answer whose CONTENT is "
            "a call; it is never used for retrieval.\n"
            "Emit exactly one line and nothing else, in this contract (the answer "
            "line comes after retrieval, never wrapped around a fetch):\n"
            "  ANSWER: NUM <integer>\n"
            "  ANSWER: CALL <callee>(<kw>=<value>, <kw>=<value>, ...)\n"
            "  ANSWER: NONE\n"
            "  ANSWER: TEXT <one line of prose>\n"
            "For CALL, put the keyword arguments in alphabetical order and give each value as "
            "the source text shows it. Anything written after that line is not read.")
    elif arm == arm_cd.ARM_C:
        contract = (
            "\n\nCHECKPOINT TURN.\n"
            "Retrieval is unavailable; answer from context or ANSWER: NONE.\n"
            "Emit exactly one line and nothing else, in this contract:\n"
            "  ANSWER: NUM <integer>\n"
            "  ANSWER: CALL <callee>(<kw>=<value>, <kw>=<value>, ...)\n"
            "  ANSWER: NONE\n"
            "  ANSWER: TEXT <one line of prose>\n"
            "For CALL, put the keyword arguments in alphabetical order and give each value as "
            "the source text shows it. Anything written after that line is not read.")
    else:
        contract = CHECKPOINT_CONTRACT_LINE
    if _already:
        return text
    return text + contract


def protocol_violation(answer_raw) -> str | None:
    """Detect a tool call masquerading as an answer line.

    If an ``ANSWER:`` payload begins with ``CALL fetch(``, the model wrapped a
    retrieval call inside the answer contract; that is recorded as
    ``answer_wrapped_tool_call`` and counted separately from a genuine wrong
    answer. Returns the violation label or None.
    """
    if not isinstance(answer_raw, str):
        return None
    payload = answer_raw.strip()
    if payload.upper().startswith("ANSWER:"):
        payload = payload[len("ANSWER:"):].strip()
    if re.match(r"CALL\s+fetch\s*\(", payload, re.IGNORECASE):
        return "answer_wrapped_tool_call"
    if re.match(r"CALL\s*\(\s*fetch\b", payload, re.IGNORECASE):
        return "answer_wrapped_tool_call"
    return None


def _is_text_call_row(row):
    row = row or {}
    content = row.get("content")
    if content is None:
        content = row.get("answer_raw")
    try:
        import arm_cd as _acd
        calls = _acd.parse_text_call(content if content is not None else "")
    except Exception:
        calls = []
    return bool(calls)


def require_protocol_variant(row):
    row = row or {}
    if _is_text_call_row(row) and row.get("protocol_variant") != "text_call":
        raise ValueError("missing protocol_variant on text-call row")
    return True


def refuse_if_missing_protocol_variant(row):
    return require_protocol_variant(row)


def assert_protocol_variant(row):
    return require_protocol_variant(row)


def check_protocol_variant(row):
    return require_protocol_variant(row)


def validate_protocol_variant(row):
    return require_protocol_variant(row)


# aliases
refuse_missing_protocol_variant = require_protocol_variant


def checkpoint_answer_fields(resp) -> dict:
    """The five contracted row fields for one reply. Offline: parses text only."""
    if resp is None:
        return {"answer_turn": True, "answer_kind": None, "answer_value": None,
                "answer_raw": None, "answer_parse_error": "no_response",
                "protocol_violation": None}
    parsed = parse_answer_contract(resp.get("content") or "")
    raw = parsed["answer_raw"]
    return {"answer_turn": True,
            "answer_kind": parsed["answer_kind"],
            "answer_value": parsed["answer_value"],
            "answer_raw": raw,
            "answer_parse_error": parsed["answer_parse_error"],
            "protocol_violation": protocol_violation(raw)}


# --------------------------------------------------------------------------- rows
def stop_reason_for_row(resp, extra):
    """The closed-vocabulary reason ONE row's request ended (RECORD-STOP-REASON).

    Turn rows, follow-up rows and refused-follow-up rows all go through ``make_row``, so
    this single derivation covers every row the runner writes.  The harness's runaway
    abort marker on ``extra`` ("this turn is the one that tripped ``--runaway-turns``")
    wins over the client's partial fold, because both the wall cap and the ceiling
    signature reach the writer as a capped turn; only the run-ending one is a runaway.
    Otherwise the client's own ``stop_reason`` is authoritative when it is in the
    vocabulary; otherwise the harness error code on ``extra`` decides
    (``turn_wall_cap``/``runaway_turn`` -> that code, anything else -> ``http_error``
    when a status was recorded, else ``stream_error``).  Nothing is invented: a row that
    carries neither is ``unknown``.
    """
    extra = extra or {}
    if extra.get("runaway_abort"):
        return client.STOP_REASON_RUNAWAY_TURN
    if resp is not None:
        reason = resp.get("stop_reason")
        if reason in client.STOP_REASONS:
            return reason
    code = extra.get("error")
    if isinstance(code, str) and code:
        if code in (client.STOP_REASON_TURN_WALL_CAP, client.STOP_REASON_RUNAWAY_TURN):
            return code
        return (client.STOP_REASON_HTTP_ERROR if extra.get("http_status")
                else client.STOP_REASON_STREAM_ERROR)
    return client.STOP_REASON_UNKNOWN


_HARNESS_SHA_CACHE: dict = {}
_HARNESS_SHA_REASON: dict = {}


def harness_sha256_now(fixture) -> str:
    """The harness digest of THIS tree, frozen the same way cell.py freezes it.

    ROW-PROVENANCE: a row that does not say which harness produced it cannot be told
    apart from a row produced before a client/runner/grader change.  cell.py owns the
    file list (``cell.HARNESS_FILES``) and is READ here, never copied and never edited;
    the combine is cell.py's ``"<name>:<sha>\\n"`` over sorted names, with the fixture as
    the sixth measurement input.  Anything that cannot be computed (cell.py unimportable,
    a harness file missing) yields ``"unknown"``: a wrong digest is worse than a gap.
    """
    key = str((fixture or {}).get("_sha256") or "")
    if key and key in _HARNESS_SHA_CACHE:
        return _HARNESS_SHA_CACHE[key]
    digest = client.PROVENANCE_UNKNOWN
    try:
        import cell as _cell  # noqa: E402 - read-only: the harness file list lives there
        files = {}
        for path, name in _cell.HARNESS_FILES:
            if not os.path.exists(path):
                raise OSError("harness file is missing: %s" % path)
            files[name] = sha256_file(path)
        files["fixture"] = fixture["_sha256"]
        combined = hashlib.sha256()
        for name in sorted(files):
            combined.update(("%s:%s\n" % (name, files[name])).encode("utf-8"))
        digest = combined.hexdigest()
    except (ImportError, OSError, ValueError, TypeError, AttributeError, RuntimeError) as exc:
        _HARNESS_SHA_REASON[key] = "%s: %s" % (type(exc).__name__, exc)
    if key:
        _HARNESS_SHA_CACHE[key] = digest
    return digest


def provenance_for(cfg, fixture, arm=None) -> dict:
    """The provenance block for this run, from what the runner already holds.

    Nothing is invented: every value is read from ``cfg``, from the loaded fixture, or
    from the harness digest; whatever is genuinely absent becomes ``"unknown"`` and
    ``provenance_complete`` goes false.
    """
    return client.provenance_block(
        arm=arm,
        model=getattr(cfg, "model", None),
        endpoint=(str(getattr(cfg, "base_url", "") or "").rstrip("/") or None),
        fixture_id=client.fixture_label(fixture),
        fixture_sha256=(fixture or {}).get("_sha256"),
        harness_sha256=harness_sha256_now(fixture),
        max_tokens=getattr(cfg, "max_tokens", None),
        thinking=thinking_setting(cfg),
        tools_mode=client.tools_mode_label(tool_names(cfg)),
        # TOOL-CHANNEL-WIRE: the wire fact that the label above never carried, until now.
        tools_schema_sent=client.tools_enabled(cfg),
    )



# ---------------------------------------------------------------- fingerprints (gate 0.4)
# UNSOURCEABLE is the only honest value for a field the server does not expose: it
# names the probe that was attempted, so a gap is never mistaken for a measurement.
UNSOURCEABLE = "UNSOURCEABLE"


def _http_get_json(url: str, timeout: float = 2.0):
    """Best-effort GET -> (parsed_json, error_string). Never raises."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=float(timeout)) as resp:
            raw = resp.read().decode("utf-8", "replace")
        try:
            return json.loads(raw), None
        except (json.JSONDecodeError, ValueError, TypeError, RecursionError) as exc:
            return None, "unparseable: %s" % exc
    except (urllib.error.URLError, OSError, TimeoutError, ValueError, TypeError, UnicodeDecodeError, RuntimeError) as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)


def probe_fingerprints(cfg) -> dict:
    """Probe what the endpoint exposes; record UNSOURCEABLE + probe where it does not.

    No value is fabricated: a field the server does not expose stays UNSOURCEABLE
    and carries the exact probe that was attempted. Offline-safe: every probe is
    wrapped and never raises.
    """
    base = str(getattr(cfg, "base_url", "") or "").rstrip("/")
    # model id + revision/quantisation digest
    model_id = UNSOURCEABLE
    model_digest = UNSOURCEABLE
    model_probe = "GET %s/models" % base
    data, err = _http_get_json(base + "/models", timeout=2.0)
    if isinstance(data, dict):
        entries = data.get("data") or data.get("models") or []
        if entries and isinstance(entries[0], dict):
            first = entries[0]
            model_id = (first.get("id") or first.get("model") or first.get("name")
                        or model_id)
            model_digest = (first.get("revision") or first.get("digest")
                            or first.get("quantization") or first.get("quantisation")
                            or UNSOURCEABLE)
            model_probe = "GET %s/models -> id=%r digest=%r" % (base, model_id, model_digest)
        else:
            model_probe = "GET %s/models -> %s" % (base, err or "no model entries")
    else:
        model_probe = "GET %s/models -> %s" % (base, err or "no response")
    # tokenizer files hash + chat-template hash (rarely exposed)
    tok_probe = "GET %s/model_info (tokenizer files / chat template not exposed)" % base
    tok_files_hash = UNSOURCEABLE
    chat_template_hash = UNSOURCEABLE
    info, ierr = _http_get_json(base + "/model_info", timeout=2.0)
    if isinstance(info, dict):
        tok_files_hash = (info.get("tokenizer_files_hash") or info.get("tokenizer_hash")
                          or UNSOURCEABLE)
        chat_template_hash = (info.get("chat_template_hash") or info.get("chat_template")
                              or UNSOURCEABLE)
        tok_probe = "GET %s/model_info -> tokenizer_files_hash=%r chat_template_hash=%r" % (
            base, tok_files_hash, chat_template_hash)
    else:
        tok_probe = "GET %s/model_info -> %s" % (base, ierr or "no response")
    # renderer module content digest (local file, not a server value)
    try:
        renderer_digest = sha256_file(__file__)
        renderer_probe = "sha256_file(%s)" % os.path.basename(__file__)
    except (OSError, ValueError, TypeError, RuntimeError, AttributeError) as exc:
        renderer_digest = UNSOURCEABLE
        renderer_probe = "sha256_file(%s) -> %s" % (os.path.basename(__file__), exc)
    # engine image digest + exact argv (not exposed via /v1)
    engine_probe = ("GET %s/health (image digest / exact argv not exposed via /v1 or /health); "
                    "no process inspection performed") % base
    engine_image_digest = UNSOURCEABLE
    engine_exact_argv = UNSOURCEABLE
    health, herr = _http_get_json(base.replace("/v1", "") + "/health", timeout=2.0)
    if isinstance(health, dict):
        engine_image_digest = (health.get("image_digest") or health.get("image")
                               or UNSOURCEABLE)
        engine_exact_argv = (health.get("argv") or health.get("args") or UNSOURCEABLE)
        if engine_image_digest != UNSOURCEABLE or engine_exact_argv != UNSOURCEABLE:
            engine_probe = "GET %s/health -> image_digest=%r argv=%r" % (
                base, engine_image_digest, engine_exact_argv)
    return {
        "model": {
            "id": model_id,
            "revision_quantisation_digest": model_digest,
            "probe": model_probe,
        },
        "tokenizer": {
            "files_hash": tok_files_hash,
            "chat_template_hash": chat_template_hash,
            "probe": tok_probe,
        },
        "renderer": {
            "module": os.path.basename(__file__),
            "content_digest": renderer_digest,
            "probe": renderer_probe,
        },
        "engine": {
            "image_digest": engine_image_digest,
            "exact_argv": engine_exact_argv,
            "probe": engine_probe,
        },
    }


def assert_repeat_identity(run_id, rep, generation=None) -> bool:
    """Repeat-identity guard: rep must be present and non-degenerate in run_id.

    gen-7 runs assert hard. gen-6 and earlier are labelled LEGACY-NONCONFORMING and
    are NOT checked here (the old path, with the deficit printed by the row-count
    guard, is used for them) -- never silently skipped, always explicitly labelled.
    """
    gen = generation if generation is not None else "gen-7"
    if gen not in ("gen-7", 7, "7"):
        print("LEGACY-NONCONFORMING: repeat-identity guard skipped for generation=%r"
              % (gen,), file=__import__("sys").stderr)
        return True
    if rep is None:
        raise AssertionError("repeat-identity: rep is missing")
    if not run_id or str(rep) not in str(run_id):
        raise AssertionError(
            "repeat-identity: rep=%r not present in run_id=%r" % (rep, run_id))
    return True


repeat_identity_guard = assert_repeat_identity


def attribute_initial_send() -> bool:
    """ROW-ATTRIBUTION (docs/ROW-MODEL.md): does the turn's INITIAL send get its own row?

    ``True`` is the live contract: one row per HTTP request of a turn.  The test
    ``tests/test_row_attribution.py`` sets this to ``False`` IN MEMORY to reproduce the
    pre-fix writer (the rebinding at the old ``run_longrun.py:2106``) and prove the
    assertions are red without the attribution.  No file on disk is edited for that.
    """
    return True


def _scratch_rows(rows_path):
    """True when a run targets a caller-managed scratch row file, not the corpus.

    CLAIM-ROW-STAMP boundary: the analysis corpus must never be written by a run
    that did not declare a claim. A row file under the OS temp dir is a
    diagnostic (tests, smoke probes) -- it may run, stamped non-comparable --
    while a corpus target without --claim-mode is refused with exit 12.
    """
    try:
        root = os.path.realpath(tempfile.gettempdir())
    except OSError:
        return False
    target = os.path.realpath(os.path.abspath(rows_path))
    return target == root or target.startswith(root + os.sep)


def make_row(cfg, fixture, arm, rep, run_id, t, resp, content, kind, manifest_sha, extra):
    assert_repeat_identity(run_id, rep, getattr(cfg, 'generation', 'gen-7'))
    if resp is None:
        # A failed turn has no measurement: null, never a measured zero.
        cached, cached_normalized, prompt, uncached = None, None, None, None
    else:
        # The client's seam value is authoritative and is carried UNCHANGED: a measured
        # 0 stays 0, an unattributed None stays null (never imputed). The legacy
        # null-semantics reading is preserved beside it as ``cached_tokens_normalized``
        # so rows written before the wiring keep a comparable column.
        cached = resp.get("cached_tokens")
        cached_normalized = normalize_cached_tokens(resp.get("raw_cached"), cfg.engine)
        prompt = resp.get("prompt_tokens")
        uncached = None if (prompt is None or cached is None) else int(prompt) - int(cached)
    # BILLED-STAMP: `billed_tokens` is what the SERVER charged for, never the client's
    # token count and never the server's prefill report. Every prompt token the cache
    # did not serve was prefilled and billed, so billed = prompt - cached when the cache
    # counter is reported. ABSENT is not 0: a null counter PAST TURN 1 is unknown (there
    # is a prior prefix, so we cannot claim nothing was cached) and must not be billed
    # as the whole prompt. Turn 1 is the one exception and it rests on the cache
    # MECHANISM, not an assumption: the first request of a run has no prior prefix to
    # hit, so cached = 0 there. `uncached_tokens` stays the server's own prefill
    # observation beside it: the 557-token gap between the two on the 100-turn SGLang
    # billed proof is unexplained, so it is RECORDED in `reconcile_delta_tokens`, never
    # smoothed away by rewriting `uncached`.
    if prompt is None:
        billed, billed_source, reconcile_delta = None, "unknown", None
    elif cached is not None:
        billed = int(prompt) - int(cached)
        billed_source = "reported"
        reconcile_delta = (int(prompt) - int(cached) - int(uncached)
                           if uncached is not None else None)
    elif t == 1:
        billed, billed_source, reconcile_delta = int(prompt), "first-turn-no-cache", None
    else:
        billed, billed_source, reconcile_delta = None, "unknown", None
    expected, cp_question = checkpoint_expected(fixture, t)
    # RULE 2: the row field `expected_present` is about the PROMPT, never the response.
    expected_present, expected_present_source = expected_value_in_prompt(
        extra.get("prompt_text"), expected)
    # The response-side test keeps its own name: it still decides the reasoning fallback
    # and `answer_verified`, and must not be confused with the prompt field again.
    expected_in_reasoning = False
    # RECORD-STOP-REASON: WHY this ended, one closed-vocabulary word, and ``truncated``
    # derived FROM it so the two can never disagree.  null only when no response exists.
    stop_reason = stop_reason_for_row(resp, extra)
    truncated = None if resp is None else client.truncated_for(stop_reason)
    if resp is None:
        # A failed request is a failed turn with no channel measurement.
        content_raw = reasoning_raw = ""
        r_tok = c_tok = None
        tok_method = None
        answer_source = "none"
        failed_turn = True
        expected_in_reasoning = False
        answer_verified = None
    else:
        content_raw = resp.get("content_raw") or ""
        reasoning_raw = resp.get("reasoning") or ""
        bpt = float(fixture.get("bytes_per_token") or 4.0477)
        c_tok, tok_method = count_channel_tokens(content_raw, bpt)
        r_tok, _ = count_channel_tokens(reasoning_raw, bpt)
        expected_in_reasoning = bool(contains_expected(reasoning_raw, expected)) if expected else False
        content_has_expected = bool(contains_expected(content_raw, expected)) if expected else False
        if content_raw.strip():
            answer_source = "content"
        elif reasoning_raw.strip() and (not truncated or expected_in_reasoning):
            # Reasoning-only completion: usable ONLY when it finished, or when it
            # literally carries the checkpoint's expected value.  Marked, not clean.
            answer_source = "reasoning-fallback"
        else:
            answer_source = "none"
        # "length" without the expected value is an incomplete answer = failed turn,
        # on either channel; it must never enter a latency average as a success.
        failed_turn = bool(truncated and not (expected_in_reasoning or content_has_expected))
        answer_verified = (bool(content_has_expected or expected_in_reasoning)
                           if expected is not None else None)
    # RECORD-STOP-REASON item 3: when a ceiling/empty/HTTP stop left NO usable content,
    # the row carries the sha of whatever content it has (the EMPTY string's sha when
    # there is none) and a completion count, so an empty generation is self-evident
    # without cross-file arithmetic.  ``stop_evidence`` marks that reading.
    no_usable_content = not ((content_raw or "").strip() or (reasoning_raw or "").strip())
    stop_evidence = bool(no_usable_content and stop_reason in (
        client.STOP_REASON_LENGTH, client.STOP_REASON_EMPTY, client.STOP_REASON_HTTP_ERROR))
    if content is not None:
        recorded_content = content
    else:
        recorded_content = "" if stop_evidence else None
    completion_recorded = resp.get("completion_tokens") if resp else None
    if stop_evidence and completion_recorded is None:
        # no stream ever delivered a usage chunk: the count is what the CLIENT observed (0)
        completion_recorded = 0
    # CLAIM-ROW-STAMP: the claim decision reaches EVERY row literal built here --
    # turn-initial, turn, tool-followup and failure rows alike. A cfg without a
    # resolved claim (a direct make_row call) is stamped the conservative
    # non-comparable shape, never a comparable one.
    claim_fields = (claim_mode.row_fields(cfg.claim)
                    if getattr(cfg, "claim", None)
                    else {"claim": claim_mode.CLAIM_NONE,
                          "comparison_eligible": False})
    row = {
        "arm": arm, **claim_fields, "task_id": fixture["task_id"],
        "fixture_path": (fixture or {}).get("_path"), "rep": rep, "turn": t,
        "prompt_tokens": prompt,
        "cached_tokens": cached,
        "uncached_tokens": uncached,
        # billed at source (see BILLED-STAMP above): the charged prompt tokens, with
        # `reconcile_delta_tokens` keeping prompt/cached/uncached disagreement visible.
        "billed_tokens": billed,
        "billed_source": billed_source,
        "reconcile_delta_tokens": reconcile_delta,
        "ttft_s": round(resp["ttft_s"], 6) if resp and resp.get("ttft_s") is not None else None,
        "latency_s": round(resp["latency_s"], 6) if resp else None,
        "completion_tokens": completion_recorded,
        "content_sha256": (sha256_text(recorded_content)
                           if recorded_content is not None else None),
        # REQUEST-IDENTITY (docs/REQUEST-IDENTITY.md): what was SENT, beside the hash of
        # what came back.  ``request_sha256`` is the client's sha256 over the exact wire
        # bytes; a response that was recorded twice from ONE send carries the same value
        # on both rows.  A row whose body was not retained says ``unknown`` and false --
        # never a guess.  Deliberately absent from every rows file written before this
        # field existed; history is NOT backfilled.
        "request_sha256": (resp.get("request_sha256")
                           if resp and resp.get("request_sha256")
                           else client.REQUEST_SHA_UNKNOWN),
        "request_identity_complete": bool(resp and resp.get("request_identity_complete")),
        "content": content,
        "fixture_sha256": fixture["_sha256"],
        "run_manifest_sha256": manifest_sha,
        "token_source": resp.get("token_source") if resp else "absent",
        "ts": iso(utc_now()),
        # extras (analysis may use; never replace the contracted keys)
        # instrument-fix fields: TTFT per row, both channels, truncation provenance
        "ttft_ms": resp.get("ttft_ms") if resp else None,
        # WIRE-CLIENT seam v1: carried from the client unchanged, exact names. A null
        # ttft_ms with ttft_source="unavailable" must reach the row as null -- wall_ms is
        # reported separately and is NEVER substituted for it.
        "ttft_source": resp.get("ttft_source") if resp else None,
        "first_token_kind": resp.get("first_token_kind") if resp else None,
        "cached_source": resp.get("cached_source") if resp else None,
        "cached_tokens_normalized": cached_normalized,
        "engine_metrics_before": resp.get("engine_metrics_before") if resp else None,
        "engine_metrics_after": resp.get("engine_metrics_after") if resp else None,
        "wall_ms": resp.get("wall_ms") if resp else None,
        "metrics_scrape": client.resolve_metrics_scrape(cfg),
        "content_source": resp.get("content_source") if resp else None,
        "reasoning": resp.get("reasoning") if resp else None,
        "reasoning_sha256": sha256_text(resp["reasoning"]) if resp and resp.get("reasoning") else None,
        "finish_reason": resp.get("finish_reason") if resp else None,
        # RECORD-STOP-REASON: the closed vocabulary, the per-choice finish reasons, and the
        # ceiling AS SENT on the request -- a 128-token cap stop is now readable here.
        "finish_reasons": resp.get("finish_reasons") if resp else None,
        "stop_reason": stop_reason,
        "truncated": truncated,
        # STOP-REASON-HOLES: rule 3 must be computable from the row ALONE.  The ceiling
        # as sent wins; the configured cap is the only fallback, never None.
        "max_tokens": (resp.get("max_tokens")
                       if (resp is not None and resp.get("max_tokens") is not None)
                       else int(cfg.max_tokens)),
        "stop_evidence": stop_evidence,
        "completion_tokens_source": (
            "usage" if (resp is not None and resp.get("completion_tokens") is not None)
            else ("client_observed" if stop_evidence else None)),
        # reasoning-policy fields: per-channel split, the verdict, and its provenance
        "reasoning_tokens": r_tok,
        "content_tokens": c_tok,
        "channel_token_method": tok_method,
        "answer_source": answer_source,
        "failed_turn": bool(failed_turn),
        "timing_usable": bool(resp is not None and resp.get("ttft_ms") is not None
                              and not failed_turn),
        "expected": expected,
        "expected_question": cp_question,
        "expected_present": expected_present,
        # null is not False: the source says WHICH search produced the value, or why no
        # search was possible (no checkpoint / no retained prompt / non-numeric value).
        "expected_present_source": expected_present_source,
        "answer_verified": answer_verified,
        "reasoning_policy": _REASONING_POLICY,
        "stream": bool(cfg.stream),
        # thinking switch: rows from different settings must NEVER be pooled; a later
        # analysis must be able to read the setting from the row alone.
        "thinking": thinking_setting(cfg),
        "temperature": getattr(cfg, "temperature", 0),
        "seed": getattr(cfg, "seed", 42),
        "fetch_policy": getattr(cfg, "fetch_policy", "strict"),
        "run_id": run_id, "engine": cfg.engine, "kind": kind,
        "generation": getattr(cfg, "generation", "gen-7"),
        "is_checkpoint": bool(extra.get("is_checkpoint")), "checkpoint": extra.get("checkpoint"),
        "cached_reported": bool(resp and resp.get("raw_cached") is not None),
        "usage_missing": bool(resp and resp.get("usage_missing")),
        "lease": extra.get("lease"), "evicted": extra.get("evicted"),
        # TREATMENTS: the turn a digest was requested on (null on every other row), written
        # beside `evicted` so compaction is visible WITHOUT a `kind == "digest"` row.
        "digest_at": extra.get("digest_at"),
        "masked_rows": extra.get("masked_rows"),
        "masked_entry": extra.get("masked_entry"),
        "marker_refs": extra.get("marker_refs"),
        "fetch_rows": extra.get("fetch_rows"),
        "retrieval_attempt": extra.get("retrieval_attempt"),
        "retrieval_outcomes": extra.get("retrieval_outcomes"),
        "fetch_tokens": extra.get("fetch_tokens"),
        "tokenizer_calls": extra.get("tokenizer_calls"),
        "tokenizer_reused": extra.get("tokenizer_reused"),
        "tokenizer_cache_hit": extra.get("tokenizer_cache_hit"),
        "reused": extra.get("reused"),
        "fetch_budget_tokens": extra.get("fetch_budget_tokens"),
        "tool_call_id": extra.get("tool_call_id"),
        "tool_call_ids": extra.get("tool_call_ids"),
        "checkpoint": extra.get("checkpoint"),
        "prompt_sha256": extra.get("prompt_sha256"),
        "prefix_sha256": extra.get("prefix_sha256"),
        "epoch": extra.get("epoch"),
        "compactions": extra.get("compactions"),
        "layer_tokens": extra.get("layer_tokens"),
        "http_status": extra.get("http_status"), "error": extra.get("error"),
    }
    # ANSWER-CONTRACT (v5): the five contracted fields are ALWAYS present, so a
    # checkpoint cell is machine-decidable from the row alone (null on a non-answer turn).
    # FIX1: every row carries the contracted answer fields, produced by the grader's
    # own parser over the row's content (never re-derived, never trusted from extras).
    _parsed_answer = parse_answer_contract(content if content is not None else "")
    row["answer_turn"] = bool(extra.get("answer_turn"))
    row["answer_kind"] = _parsed_answer["answer_kind"]
    row["answer_value"] = _parsed_answer["answer_value"]
    row["answer_raw"] = _parsed_answer["answer_raw"]
    row["answer_parse_error"] = _parsed_answer["answer_parse_error"]
    # PROTOCOL-VIOLATION (TOOLCALLFIX): an ANSWER: payload that wraps a fetch
    # call is recorded distinctly and counted separately from a genuine wrong
    # answer. Never masks a real policy result.
    row["protocol_violation"] = protocol_violation(_parsed_answer["answer_raw"])
    # (protocol_violation already overridden above when extra provides it)
    row["protocol_violation"] = extra.get("protocol_violation") if extra.get("protocol_violation") is not None else row["protocol_violation"]
    # TEXT-CALL-PROTOCOL: stamp the transport variant when a row carries a
    # text-form fetch request, so the rows stay honest about how the call was framed.
    _text_calls = None
    try:
        import arm_cd as _acd
        _text_calls = _acd.parse_text_call(content if content is not None else "")
    except Exception:
        _text_calls = []
    if _text_calls:
        row["protocol_variant"] = extra.get("protocol_variant", "text_call")
        row["ref_as_emitted"] = extra.get("ref_as_emitted", _text_calls[0].get("ref_as_emitted"))
        row["ref_revision_normalised"] = extra.get("ref_revision_normalised", _text_calls[0].get("ref_revision_normalised"))
    else:
        row["protocol_variant"] = extra.get("protocol_variant")
        row["ref_as_emitted"] = extra.get("ref_as_emitted")
        row["ref_revision_normalised"] = extra.get("ref_revision_normalised")
    # FIX2: retrieval omission is a recorded protocol violation for arm D on a
    # marked turn where not every marker was fetched. Never set for arm C or
    # when all markers are fetched. Boolean on every row.
    row["retrieval_omitted"] = False
    _marker_refs = extra.get("marker_refs") or []
    _fetched_n = extra.get("fetch_rows")
    if _fetched_n is None:
        _fetched_n = 0
    try:
        _fetched_n = int(_fetched_n)
    except (TypeError, ValueError):
        _fetched_n = 0
    if (str(arm) == arm_cd.ARM_D
            and kind != "turn-initial"
            and len(_marker_refs) > 0
            and _fetched_n < len(_marker_refs)):
        row["retrieval_omitted"] = True
    if extra.get("fetch_followup"):
        # FETCH-CHANNEL: a follow-up model request served a tool result (real request).
        row["fetch_followup"] = True
    if extra.get("tool_calls") is not None:
        row["tool_calls"] = extra["tool_calls"]
    if extra.get("fetch_rounds_used") is not None:
        # FETCH-CHANNEL: durable round spend on a --tools row (absent on a tools-off row).
        row["fetch_rounds_used"] = extra["fetch_rounds_used"]
    # PROBE-CP3-V6: the (b) cap and the (a) no-bill split, readable from the row alone.
    for key in ("fetch_rounds_cap_per_turn", "fetch_rounds_this_turn", "fetch_prompt_serves",
                "billed_round", "prompt_served",
                # ROW-ATTRIBUTION: which HTTP request of the turn this row measured.
                "send_index", "initial_send", "row_measurement_source",
                "fetch_round_final", "final_round_billed", "final_round_prompt_served",
                "next_request_kind",
                # TOOL-CALL-CAPTURE (U-SPCC-49): the ids of the calls the fetch parser
                # did not consume, so a row's `tool_calls` can be joined to the wire.
                "unserviced_tool_call_ids"):
        if extra.get(key) is not None:
            row[key] = extra[key]
    if extra.get("runaway_abort"):
        # STOP-REASON-HOLES: this row is the one that tripped --runaway-turns and ended
        # the cell; the harness event (`error`) stays the wall cap/signature that fired.
        row["runaway_abort"] = True
    # ROW-PROVENANCE: this row names what produced it -- arm, model, endpoint, fixture
    # identity, the harness digest, the ceiling, the thinking switch and the tool mode --
    # so a later analysis READS the era instead of inferring it from file mtimes.  An
    # absent value is the string "unknown" plus provenance_complete=false, never null.
    row.update(provenance_for(cfg, fixture, arm))
    # TOOL-CHANNEL-WIRE: DECLARED vs ACTUALLY SENT, side by side on every row.
    # `tools_declared` is the run's --tools switch; `tools_schema_sent` is the WIRE fact
    # for THIS row's request, read from the response the client stamped.  A response with
    # no stamp (a failure row) falls back to the request body's own deterministic gate.
    sent = (resp or {}).get("tools_schema_sent") if isinstance(resp, dict) else None
    row["tools_declared"] = bool(client.tools_enabled(cfg))
    row["tools_schema_sent"] = (bool(sent) if sent is not None
                                else bool(client.tools_enabled(cfg)))
    # INTERIM MARKING: a checkpoint row that is not the final answer for its
    # checkpoint id (a fetch follow-up, a turn-initial attempt, or a row that
    # itself issues a fetch) is marked interim so the scorer grades it once.
    _cp = row.get("checkpoint")
    if (_cp is not None or extra.get("checkpoint") is not None
            or row.get("fetch_followup") is True
            or kind in ("turn-initial", "tool-followup")):
        if kind in ("turn-initial", "tool-followup"):
            row["interim"] = True
            row["interim_reason"] = "fetch_followup"
        else:
            _content = (content or row.get("content") or "")
            if "fetch(" in str(_content).lower() or "fetch " in str(_content).lower():
                row["interim"] = True
                row["interim_reason"] = "fetch_followup"
    return row


#: Monotonic per-file position, seeded from the file's own last ``row_seq``.
_ROW_SEQ: dict[str, int] = {}


def _row_seq_high_water(path: str) -> int:
    """Highest ``row_seq`` already in ``path`` (0 when the file is absent/unstamped)."""
    key = os.path.abspath(path)
    if key not in _ROW_SEQ:
        high = 0
        if os.path.exists(key):
            with open(key, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        seq = json.loads(line).get("row_seq")
                    except json.JSONDecodeError:
                        continue
                    if isinstance(seq, int) and seq > high:
                        high = seq
        _ROW_SEQ[key] = high
    return _ROW_SEQ[key]


def append_row(path: str, row: dict) -> None:
    # ROW-SEQ: one integer per WRITE POSITION in the file, assigned once per row object.
    # A double append of one request is visible as two lines sharing ``request_sha256``
    # AND ``row_seq``; a genuine re-send keeps the same request hash but is a NEW row and
    # takes the next integer.
    key = os.path.abspath(path)
    if "row_seq" in row:
        # The same row object written a second time: keep its seq (that is the evidence).
        _ROW_SEQ[key] = max(_row_seq_high_water(path), int(row["row_seq"]))
    else:
        row["row_seq"] = _row_seq_high_water(path) + 1
        _ROW_SEQ[key] = row["row_seq"]
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def read_cell_rows(rows_path: str, run_id: str, task_id: str, arm: str, rep: int) -> list[dict]:
    rows: list[dict] = []
    if not os.path.exists(rows_path):
        return rows
    with open(rows_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (row.get("run_id"), row.get("task_id"), row.get("arm"), row.get("rep")) == (
                    run_id, task_id, arm, rep):
                rows.append(row)
    return rows


def resume_start(rows: list[dict]) -> int:
    if not rows:
        return 0
    if any(row.get("error") for row in rows):
        raise SystemExit("RESUME REFUSED: this cell already holds a failed row; a failure is "
                         "recorded, not retried past the budget. Start a new --run-id.")
    return max(int(row.get("turn") or 0) for row in rows)


# ---------------------------------------------------------------------- dry-run
def preview_write(path: str, text: str) -> tuple[int, str]:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))
    return len(text.encode("utf-8")), sha256_text(text)


def preview_body(cfg, planner: Planner, prompt: str) -> str:
    return json.dumps(request_body(cfg, planner.messages(prompt)), sort_keys=True, indent=2,
                      ensure_ascii=False)


def preview_root(task_id: str) -> str:
    """Where a task's committed previews live (`state/previews/<task_id>`)."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "state", "previews", task_id)


_PREVIEW_TURN_RE = re.compile(r"-(\d+)")


def prune_stale_previews(arm_root: str, written: set[str], n_turns: int) -> list[str]:
    """Delete preview files of a re-rendered arm that this run's turn scope supersedes.

    PREVIEW-PRESERVATION: `state/previews/<task_id>` holds COMMITTED evidence — the
    request bodies each arm would send are tracked files.  A dry run therefore deletes
    nothing up front: it overwrites the files it renders and calls this only for the arm
    it just re-rendered.  Even there it removes a file only when the file's turn lies
    inside this run's scope (`<= n_turns`) and this run did not write it — i.e. a naming
    the previous config produced at a turn this one no longer produces.  Files belonging
    to arms this run does not render, and files beyond this run's turn scope, are never
    touched.  Invariant: a dry run never leaves the working tree with fewer tracked
    files than it found.
    """
    removed: list[str] = []
    if not os.path.isdir(arm_root):
        return removed
    for name in sorted(os.listdir(arm_root)):
        path = os.path.join(arm_root, name)
        if not os.path.isfile(path) or os.path.abspath(path) in written:
            continue
        match = _PREVIEW_TURN_RE.search(name)
        if match is None or int(match.group(1)) > n_turns:
            continue
        os.remove(path)
        removed.append(path)
    return removed


def run_dry(cfg, fixture: dict, cells: list[tuple[str, int, int]],
            root: Optional[str] = None) -> int:
    # PREVIEW-PRESERVATION: never clear the task directory.  See prune_stale_previews:
    # a read-only-sounding --dry-run that rmtree'd this tree deleted committed evidence
    # (LR-01/transcript-compact) twice.  `root` is injectable so tests can point a dry
    # run at a temp directory instead of the tracked tree.
    root = root or preview_root(fixture["task_id"])
    os.makedirs(root, exist_ok=True)
    order: list[str] = []
    reps_by_arm: dict[str, int] = {}
    # A variant label is the arm name for the default interval (so a run without
    # --compact-every writes the same preview paths as before) and ``arm@cN`` for
    # any other interval, so two variants of one arm never overwrite each other.
    variants: dict[str, tuple[str, int]] = {}
    for cell in cells:
        # A 2-tuple is the pre-change cell shape (arm, rep); the interval defaults
        # to COMPACT_EVERY, so an old caller previews exactly what it used to.
        arm, _rep = cell[0], cell[1]
        interval = cell[2] if len(cell) > 2 else COMPACT_EVERY
        label = arm if interval == COMPACT_EVERY else "%s@c%d" % (arm, interval)
        if label not in reps_by_arm:
            order.append(label)
            reps_by_arm[label] = 0
            variants[label] = (arm, interval)
        reps_by_arm[label] += 1
    previews: dict[str, list[str]] = {label: [] for label in order}
    counts: dict[str, dict] = {}
    # LAYER ACCOUNTING: the compiler's own view of each turn, so a dry run proves the
    # layer wiring (which blocks exist, and whether the prefix is stable) without a
    # request.  Only arms that render through ``compile_prompt`` report anything.
    layer_seen: dict[str, dict] = {}

    # TREATMENTS LAUNCH PRECONDITION — printed FIRST, before a single preview body is
    # rendered, and fatal.  A dry run that reaches no hook is not a preview of a cell; it
    # is the announcement that the cell would measure its control path for 48 turns.
    print("TREATMENT REACHABILITY AT THE FROZEN HORIZON (offline, from the fixture)")
    unreachable = 0
    for label in order:
        rc, lines = check_treatments(fixture, variants[label][0], HORIZON_TURNS)
        for line in lines:
            print(line)
        unreachable = unreachable or rc
    if unreachable:
        print(f"\nLAUNCH REFUSED (exit {EXIT_TREATMENTS_UNREACHABLE}): a treatment cannot fire "
              f"inside {HORIZON_TURNS} turns at this fixture's wall. Do not raise the horizon "
              "(PARM-1 line 137) and do not raise the wall until it fits: change the fixture's "
              "treatment inputs, or run an arm whose treatment does fire. No request was sent.",
              file=sys.stderr)
        return EXIT_TREATMENTS_UNREACHABLE
    print()

    # RUN-DRY-TURN-SCOPE: the preview loops over EXACTLY the turns the live cell would
    # execute — `cell_turns`, the same one definition `run_cell` and `projected_requests`
    # read.  It is not `fixture["N"]` and it is not a second `min()` here: a preview that
    # prices 48 turns for a `--max-turns 12` cell gates a cell that cannot exist.
    n_turns = cell_turns(cfg, fixture)

    for label in order:
        arm, interval = variants[label]
        fx = fixture_for_arm(fixture, arm)
        planner = Planner(arm, fx, dry_run=True, compact_every=interval,
                          window_turns=window_turns_setting(cfg))
        c = {"reps": reps_by_arm[label], "digest_requests": 0, "wall_turn": None,
             "trunc_turn": None, "post_wall": None}
        counts[label] = c
        acc = layer_seen.setdefault(label, {"keys": set(), "prefixes": []})
        written: set[str] = set()
        for t in range(1, n_turns + 1):
            info = planner.build(t)
            if info.get("layer_tokens"):
                acc["keys"].update(info["layer_tokens"])
                acc["prefixes"].append((t, info.get("prefix_sha256")))
            if t in checkpoint_turns(fixture):
                # ANSWER-CONTRACT (v5): identical injection to run_cell, so the preview
                # body is the body a checkpoint turn would really send.
                info["prompt"] = checkpoint_prompt(fixture, t, info["prompt"], arm=planner.arm, fetch_policy=getattr(cfg, "fetch_policy", "strict"))
            body = preview_body(cfg, planner, info["prompt"])
            digest_body = None
            if info["digest_request"] is not None:
                c["digest_requests"] += 1
                digest_body = json.dumps(request_body(cfg, info["digest_request"]), sort_keys=True,
                                         indent=2, ensure_ascii=False)
                if c["wall_turn"] is None:
                    c["wall_turn"] = t
                    dpath = os.path.join(root, label, f"wall-{t:02d}-digest-request.json")
                    dbytes, dsha = preview_write(dpath, digest_body)
                    written.add(os.path.abspath(dpath))
                    print(f"  [{label}] first wall at T{t}: digest request {dbytes} B sha256={dsha} ({dpath})")
            if len(previews[label]) < 3:
                previews[label].append(sha256_text(body))
                path = os.path.join(root, label, f"turn-{t:02d}.json")
                nbytes, digest = preview_write(path, body)
                written.add(os.path.abspath(path))
                user0 = info["prompt"].replace("\n", " ")[:100]
                print(f"  [{label}] T{t}: {nbytes} B sha256={digest} user=\"{user0}\"")
                if cfg.show_prompts:
                    print(body)
            if arm == "transcript-grow" and c["trunc_turn"] is None and info["evicted"]:
                c["trunc_turn"] = t
                print(f"  [{label}] first FIFO truncation at T{t}: evicted {info['evicted']} history block(s)")
            if arm == "transcript-compact" and c["wall_turn"] is not None and c["post_wall"] is None:
                c["post_wall"] = (t, sha256_text(body))
                ppath = os.path.join(root, label, f"post-wall-{t:02d}.json")
                pbytes, psha = preview_write(ppath, body)
                written.add(os.path.abspath(ppath))
                print(f"  [{label}] post-wall body at T{t}: {pbytes} B sha256={psha} "
                      "(digest text is a placeholder offline; the digest REQUEST above is exact)")
            # simulate the answer the model would have produced
            planner.record(t, f"<<answer from turn {t}: not produced in dry-run>>")
        # Only after rendering this arm: drop artefacts of THIS arm at turns this run
        # covers but no longer produces.  Other arms' previews are never considered.
        for gone in prune_stale_previews(os.path.join(root, label), written, n_turns):
            print(f"  [{label}] removed stale preview {gone} (superseded by this run)")

    print("\nLAYER ACCOUNTING (compiler view; no request sent)")
    for label in order:
        acc = layer_seen.get(label)
        if not acc or not acc["prefixes"]:
            print(f"  {label:19s} not rendered by the layer compiler")
            continue
        keys = sorted(acc["keys"])
        shas = [s for _t, s in acc["prefixes"]]
        distinct = len(set(shas))
        first_change = next((t for (t, s), prev in zip(acc["prefixes"][1:], shas)
                             if s != prev), None)
        print(f"  {label:19s} layers={keys} distinct_prefixes={distinct} "
              f"over T1..T{acc['prefixes'][-1][0]}"
              + (f" first_prefix_change=T{first_change}" if first_change else ""))

    print("\nREQUEST COUNTS (what --dry-run would send)")
    total = 0
    for label in order:
        c = counts[label]
        turns = n_turns * c["reps"]
        extra = c["digest_requests"] * c["reps"]
        cell_total = turns + extra
        total += cell_total
        assert turns == n_turns * c["reps"], "turn count must be the cell's turns x reps"
        # Full cell (n_turns == fixture N): the line is byte-identical to before this unit.
        scope = (f"N={fixture['N']} x reps={c['reps']}" if n_turns == int(fixture["N"])
                 else f"N={fixture['N']} --max-turns={n_turns} x reps={c['reps']}")
        print(f"  {label:19s} turn_requests={turns} ({scope})  "
              f"digest_requests={extra}  cell_total={cell_total}")
    print(f"  would_send_total={total}")
    if tools_enabled(cfg):
        # Offline there is no model turn, so no <tool_call> can be parsed and no fetch
        # is possible: the cap below is the ceiling, not a predicted spend.
        print(f"  tool_channel={','.join(tool_names(cfg))} fetch_rounds_cap="
              f"{fetch_rounds_per_arm(cfg)} (per arm) fetch_rounds_cap_per_turn="
              f"{fetch_rounds_per_turn(cfg)} serve_from_prompt={bool(TOOL_SERVE_FROM_PROMPT)} "
              f"max_calls_per_turn={TOOL_CALLS_PER_TURN} "
              f"fetch_requests_in_this_preview=0 (no model turn offline)")

    print("\nPREVIEW PAIRWISE (first three request bodies; 0/3 differ = identical)")
    for i, a in enumerate(order):
        for b in order[i + 1:]:
            diff = sum(1 for x, y in zip(previews[a], previews[b]) if x != y)
            note = ""
            if (a, b) == ("transcript-grow", "transcript-compact"):
                note = "  <- identical BY DESIGN before B's first wall"
            print(f"  {a} vs {b}: {diff}/3 differ{note}")
    return 0


# ---------------------------------------------------------------------- self-test
def self_test() -> int:
    sglang = normalize_cached_tokens(None, "sglang")
    vllm = normalize_cached_tokens(None, "vllm")
    line = inspect.getsourcelines(normalize_cached_tokens)[1]
    print("NULL SEMANTICS — normalize_cached_tokens(None, engine)")
    print(f"  sglang: None -> {sglang!r}")
    print(f"  vllm:   None -> {vllm!r}")
    print(f"  function: {normalize_cached_tokens.__module__}.{normalize_cached_tokens.__name__} "
          f"at {inspect.getsourcefile(normalize_cached_tokens)}:{line}")
    print(f"  reported 32: sglang -> {normalize_cached_tokens(32, 'sglang')!r}, "
          f"vllm -> {normalize_cached_tokens(32, 'vllm')!r}")
    assert sglang == 0 and isinstance(sglang, int), "SGLang null must be the integer 0"
    assert vllm is None, "vLLM null must stay null"
    print("  PASS: None -> 0 on the SGLang path; None -> null on the vLLM path")
    return 0


# --------------------------------------------------------------------------- cell
# ARM-REQUIRES-TOOLS (U-SPCC-46).  The D arm's treatment IS the fetch channel: its whole
# difference from C is that a masked body can be bought back with a `fetch` call.  With
# `--tools` absent the fetch service at the `arm == arm_cd.ARM_D` block never runs, so
# every checkpoint turn strands as an interim `fetch_followup` row with
# `protocol_violation=answer_wrapped_tool_call` and `send_index 0` -- a degenerate cell
# that still exits 0 and reports 0 failed turns.  E1 ran exactly that (43 of 48
# checkpoint turns stranded) and the arm looked like a real result.  A launch that cannot
# fire its treatment is refused BEFORE the first request, like the treatments gate: no
# row, no socket, exit 2 (the same code as the other malformed-launch refusals).
EXIT_ARM_REQUIRES_TOOLS = 2


def arm_requires_tools(arm: str) -> bool:
    """True for the arms whose treatment cannot fire without the tool channel.

    ``bounded-context-fetch`` (D) buys a masked body back with a ``fetch`` call,
    and the E7 pin arms (``pinned``, ``pinned-recency``) measure ``refetch_count``
    -- a tool call whose range the prompt already carries.  With ``--tools``
    absent neither mechanism can fire, so both are refused before the first
    request instead of producing a degenerate cell that exits 0.
    """
    return arm == arm_cd.ARM_D or arm in arm_cd.PINNED_ARMS


def refuse_arm_without_tools(cfg, arm: str) -> int:
    """``0`` when the arm may run, else the refusal exit code (nothing sent, no row).

    Only the fetch arm and the E7 pin arms are gated: ``masking-no-fetch`` (C) is
    DEFINED by having no tool channel -- ``run_cell`` clears ``cfg.tools`` for it
    -- and ``spcc`` never fetches, so both are unaffected by an absent ``--tools``.
    """
    if not arm_requires_tools(arm) or tools_enabled(cfg):
        return 0
    print(f"ARM REFUSED (exit {EXIT_ARM_REQUIRES_TOOLS}): arm {arm!r} is a tool-channel arm "
          f"and requires --tools (e.g. --tools read_file); --tools is absent, so tools_mode="
          f"{client.tools_mode_label(tool_names(cfg))!r} and the tool service would never "
          f"run. No row was written and no request was sent.", file=sys.stderr)
    return EXIT_ARM_REQUIRES_TOOLS


def run_cell(cfg, fixture: dict, arm: str, rep: int, run_id: str, rows_path: str,
             compact_every: int = COMPACT_EVERY,
             window_turns: int = arm_cd.WINDOW_TURNS) -> int:
    assert_repeat_identity(run_id, rep, getattr(cfg, 'generation', 'gen-7'))
    # BEFORE the ARM_C copy below clears cfg.tools: the guard reads the launch's own
    # --tools, and C is allowed to be tool-less while D is not.
    rc_tools = refuse_arm_without_tools(cfg, arm)
    if rc_tools != 0:
        return rc_tools
    import copy as _copy
    if arm == arm_cd.ARM_C:
        cfg = _copy.copy(cfg)
        cfg.tools = ""
    # real launch too — a cell that would spend 48 requests on its control path refuses
    # BEFORE the manifest is frozen and before any request is sent.
    rc_t, lines = check_treatments(fixture, arm, HORIZON_TURNS)
    for line in lines:
        print(line)
    if rc_t != 0:
        print(f"LAUNCH REFUSED (exit {rc_t}): the {arm} treatment cannot fire inside "
              f"{HORIZON_TURNS} turns at this fixture's wall; no request was sent.",
              file=sys.stderr)
        return rc_t
    fixture = fixture_for_arm(fixture, arm)
    manifest_path = cfg.manifest_path or os.path.join(cfg.manifest_dir, run_id + ".json")
    rows = read_cell_rows(rows_path, run_id, fixture["task_id"], arm, rep) if cfg.resume else []
    # WIRE-CAP-GATE: the gate exists BEFORE the frozen manifest is written, so the declared
    # allocation and the run-start spend are part of the manifest the cell is stamped with.
    try:
        gate = build_cap_gate(cfg, fixture, arm, rows_path)
    except CapUsageError as exc:
        print(f"CAP GATE USAGE: {exc} — the run did not start, no request was sent",
              file=sys.stderr)
        return 3
    except CapRowsUnreadable as exc:
        print(f"CAP GATE ROWS: {exc}", file=sys.stderr)
        print("CAP GATE ROWS: nothing counted — an unreadable row file makes the spent "
              "total unknowable; no request was sent", file=sys.stderr)
        return 5
    if cfg.resume and rows and os.path.exists(manifest_path):
        with open(manifest_path, "rb") as fh:
            data = fh.read()
        manifest_sha = sha256_bytes(data)
        # The cap-gate addendum written at exit names the sha the ROWS were stamped with,
        # so a resume after that addendum is still verifying the same frozen manifest.
        try:
            frozen_sha = (((json.loads(data.decode("utf-8")) or {}).get("cap_gate") or {})
                          .get("frozen_sha256"))
        except (ValueError, AttributeError):
            frozen_sha = None
        stamped = rows[0].get("run_manifest_sha256")
        if stamped != manifest_sha and stamped != frozen_sha:
            print(f"RESUME REFUSED: manifest {manifest_path} sha {manifest_sha} does not match the "
                  f"rows ({stamped})", file=sys.stderr)
            return 5
        print(f"resume: reusing frozen manifest {manifest_path} sha256={manifest_sha}")
    else:
        try:
            data, manifest_sha = write_manifest(
                manifest_path,
                build_manifest(cfg, fixture, arm, rep, run_id, rows_path,
                               cap_gate=gate.manifest_block()))
        except OSError as exc:
            print(f"MANIFEST ABORT: cannot write {manifest_path}: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            print("MANIFEST ABORT: the run did not start — no request was sent (Consonance: no "
                  "frozen manifest, no result).", file=sys.stderr)
            return 3
        print(f"manifest: {manifest_path} ({len(data)} B) sha256={manifest_sha}")
    print(f"cap-gate: allocation={gate.allocation} cap={gate.cap} reserve={gate.reserve} "
          f"spent_at_start={gate.spent_at_start} headroom={gate.headroom} "
          f"files={len(gate.paths)} (per-request brake armed before the first send)")

    planner = Planner(arm, fixture, dry_run=False, compact_every=compact_every,
                      window_turns=window_turns)
    start = 1
    if rows:
        start = resume_start(rows) + 1
        planner.replay(rows)
        print(f"resume: cell has turns 1..{start - 1}; continuing at {start}")
    n_turns = cell_turns(cfg, fixture)
    # The cell's structural request projection.  It is ALSO the default allocation, so the
    # in-memory brake and the old `sent >= budget` abort cannot disagree about the ceiling.
    budget = projected_requests(cfg, fixture, arm)
    sent = 0
    fetch_rounds_used = 0
    fetch_cache: dict = {}
    # PROBE-CP3-V6 (b): the per-turn cap, and the follow-up REQUEST allowance that funds
    # every round (billed or prompt-served) without letting a burst starve the checkpoints.
    per_turn_cap = fetch_rounds_per_turn(cfg)
    cp_turns = checkpoint_turns(fixture)
    followup_pool = fetch_rounds_per_arm(cfg)
    followups_bought = followups_spent(rows) if tools_enabled(cfg) else 0
    if tools_enabled(cfg) and rows:
        # DURABLE ROUND COUNTING.  `--resume` used to reset this to 0, so a resumed arm
        # executed 20 fetches while the counter reported 8/8.  Every follow-up row is
        # fsync'd, so the cell's own rows are the ledger; the frozen manifest's counter
        # is honoured too and the LARGER of the two wins, so neither a reset manifest
        # nor a short row file can re-open the round budget.
        derived = fetch_rounds_spent(rows)
        frozen = 0
        try:
            with open(manifest_path, "rb") as fh:
                frozen = int(((json.load(fh) or {}).get("tools") or {})
                             .get("fetch_rounds_used") or 0)
        except (OSError, ValueError, TypeError, AttributeError):
            frozen = 0
        fetch_rounds_used = max(frozen, derived)
        print(f"resume: fetch rounds already spent={fetch_rounds_used}/"
              f"{fetch_rounds_per_arm(cfg)} (manifest={frozen} derived_from_rows={derived}); "
              "--resume does not reset the counter")

    wall_cap = float(getattr(cfg, "turn_wall_cap", 0) or 0)
    runaway_turns = max(1, int(getattr(cfg, "runaway_turns", 2) or 2))
    # RUNAWAY-POLICY (docs/RUNAWAY-POLICY.md): two DIFFERENT events are counted
    # separately because they cost different things, and one former "runaway" is data.
    #   wall_runaways      -- a turn whose stream --turn-wall-cap CLOSED (client.py:530
    #                         raises TurnWallCap). This is the cost hazard the guard was
    #                         built for: the 16,384-token / 475,873 ms turn of
    #                         LIVE-SMOKE-CELL, now bounded per turn AND counted here.
    #   ceiling_violations -- a response that finished ABOVE --max-tokens, i.e. a server
    #                         that IGNORED the ceiling: unbounded tokens, no row-level
    #                         bound. Counted against the same limit.
    #   A `length` truncation AT the ceiling is NOT counted: it is bounded data
    #                         (measured: 2 turns of 27 in cell 1 of RUN-A*).
    wall_runaways = 0
    wall_runaway_turns = []
    ceiling_violations = 0
    ceiling_violation_turns = []

    def _runaway_detail():
        return ("wall-time runaways %d/%d [%s]; ceiling violations %d/%d [%s]"
                % (wall_runaways, runaway_turns,
                   "; ".join(wall_runaway_turns) or "none",
                   ceiling_violations, runaway_turns,
                   "; ".join(ceiling_violation_turns) or "none"))

    def _escalate(turn_no, exc, part, kind="turn"):
        # ONE loud line: the turn, its wall time, its completion tokens and the cap.
        print(f"RUNAWAY T{turn_no} ({kind}): wall={exc.wall_s:.1f}s "
              f"completion_tokens={part.get('completion_tokens')} "
              f"cap={wall_cap:.1f}s — stream CLOSED, turn ABORTED, row recorded "
              f"error=turn_wall_cap truncated=true "
              f"(wall-time runaways {wall_runaways}/{runaway_turns})",
              file=sys.stderr)

    def _ceiling_violation(row):
        """Predicate 2, NARROWED BY RUNAWAY-POLICY: a response ABOVE the ceiling.

        A `length` truncation AT the ceiling (`truncated` and completion_tokens ==
        cfg.max_tokens) is DATA, not a runaway: the turn finished inside
        --turn-wall-cap, spent exactly max_tokens, and the row records
        ``stop_reason=length`` so a grader marks that answer wrong or absent. The other
        47 turns are unaffected by it. Measured: 2 of 27 turns in cell 1 of RUN-A*.

        What STILL counts is the server IGNORING the ceiling (completion_tokens >
        cfg.max_tokens): unbounded tokens with no row-level bound on cost. See
        docs/RUNAWAY-POLICY.md, option B.
        """
        comp = int(row.get("completion_tokens") or 0)
        ceiling = int(cfg.max_tokens)
        if comp > ceiling:
            return ("completion_tokens %d EXCEEDED the max_tokens ceiling %d"
                    % (comp, ceiling))
        return None

    for t in range(start, n_turns + 1):
        info = planner.build(t)
        turn = info["turn"]
        # The fixture marks a checkpoint with kind == "checkpoint" and names it in
        # fixture["checkpoints"], not with a per-turn "checkpoint" key: reading only
        # turn.get("checkpoint") left is_checkpoint False on every row (found here at T12).
        declared = next((c for c in fixture.get("checkpoints") or []
                         if int(c.get("turn", -1)) == int(t)), None)
        is_answer_turn = int(t) in cp_turns
        if is_answer_turn:
            # ANSWER-CONTRACT (v5): the checkpoint question arrives now, and the turn
            # itself says the tools are off. The injected text carries no expected value.
            info["prompt_before_checkpoint"] = info["prompt"]
            info["prompt"] = checkpoint_prompt(fixture, t, info["prompt"], arm=planner.arm, fetch_policy=getattr(cfg, "fetch_policy", "strict"))
        extras = {"is_checkpoint": bool(turn.get("checkpoint")) or turn.get("kind") == "checkpoint"
                  or declared is not None,
                  "checkpoint": (info.get("checkpoint") if info.get("checkpoint") is not None
                                 else (turn.get("checkpoint") or declared)),
                  "answer_turn": is_answer_turn,
                  "lease": info.get("lease"), "evicted": info.get("evicted"),
                  # RULE 2 operand: the rendered prompt THIS row's checkpoint is answered
                  # from. Not a row field -- make_row consumes it and stamps the verdict.
                  "prompt_text": info.get("prompt"),
                  "masked_rows": info.get("masked_rows"),
                  "masked_entry": info.get("masked_entry"),
                  "marker_refs": (extract_marker_refs(info.get("prompt_before_checkpoint", info.get("prompt")))
                                  if arm == arm_cd.ARM_D else []),
                  # TREATMENTS: compaction is visible on the TURN row it happened on; the
                  # `kind == "digest"` rows stay exactly as they were (this adds, never
                  # replaces), so a reader filtering turn rows can still see the wall.
                  "digest_at": t if info["digest_request"] is not None else None,
                  "prefix_sha256": info.get("prefix_sha256"),
                  "epoch": info.get("epoch"),
                  "compactions": info.get("compactions"),
                  "layer_tokens": info.get("layer_tokens")}
        digest_attempts = 0
        while info["digest_request"] is not None and digest_attempts < 2:
            if sent >= budget:
                print(f"BUDGET ABORT at T{t}: {sent} requests already sent (budget {budget})",
                      file=sys.stderr)
                # BUDGET-RECONCILE (U-SPCC-43): a budget-exhausted exit spent requests,
                # so it reconciles like every other exit path.
                return _abort_stop(4, gate, manifest_path, manifest_sha, rows_path)
            msg = info["digest_request"]
            try:
                gate.acquire(t, "digest")
            except CapRefusal as exc:
                return _cap_stop(exc, gate, manifest_path, manifest_sha, rows_path)
            try:
                resp = send_chat(cfg, msg)
            except client.TurnWallCap as exc:
                sent += 1
                part = exc.as_response(cfg)
                wall_runaways += 1
                wall_runaway_turns.append("T%d (digest, wall %.1fs > cap %.1fs)"
                                          % (t, exc.wall_s, wall_cap))
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, part, part["content"], "digest",
                    manifest_sha,
                    dict(extras, error="turn_wall_cap", prompt_sha256=sha256_text(
                        msg[1]["content"]), turn_wall_cap_s=wall_cap,
                         runaway_abort=True)))
                _escalate(t, exc, part, "digest")
                print(f"RUNAWAY ABORT after T{t}: a planning request ran past the wall "
                      f"cap; {_runaway_detail()}; {t}/{n_turns} turns reached, partial "
                      f"rows kept at {rows_path}", file=sys.stderr)
                return _abort_stop(6, gate, manifest_path, manifest_sha,
                                   rows_path)
            except RequestFailure as exc:
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, None, None, "digest", manifest_sha,
                    dict(extras, http_status=exc.status, error=str(exc),
                         prompt_text=msg[1]["content"],
                         prompt_sha256=sha256_text(msg[1]["content"]))))
                print(f"TURN FAILED (digest) T{t}: {exc} — cell stopped, failure row recorded",
                      file=sys.stderr)
                return 4
            sent += 1
            append_row(rows_path, make_row(
                cfg, fixture, arm, rep, run_id, t, resp, resp["content"], "digest", manifest_sha,
                dict(extras, prompt_text=msg[1]["content"],
                     prompt_sha256=sha256_text(msg[1]["content"]))))
            print(f"  [T{t}] digest request sent (prompt_tokens={resp['prompt_tokens']})")
            planner.digest = resp["content"]
            planner.raw = planner.raw[-4:]
            digest_attempts += 1
            info = planner.build(t)

        if sent >= budget:
            print(f"BUDGET ABORT at T{t}: {sent} requests already sent (budget {budget})",
                  file=sys.stderr)
            # BUDGET-RECONCILE (U-SPCC-43): a budget-exhausted exit spent requests, so it
            # reconciles like every other exit path.
            return _abort_stop(4, gate, manifest_path, manifest_sha, rows_path)
        # WIRE-CAP-GATE: the per-request brake, immediately BEFORE the wire.  Not per-run:
        # a run-level preflight cannot see the mid-run divergence (6 vs 130 on dbed0e9d).
        try:
            gate.acquire(t, "turn")
        except CapRefusal as exc:
            return _cap_stop(exc, gate, manifest_path, manifest_sha, rows_path)
        try:
            resp = send_chat(cfg, planner.messages(info["prompt"]))
        except client.TurnWallCap as exc:
            # TASK 2: past --turn-wall-cap the stream is closed by the client's context
            # manager; the partial fold is recorded, the turn aborted, and the cell ends
            # with exit 6 once --runaway-turns WALL-TIME runaways have been seen.
            sent += 1
            part = exc.as_response(cfg)
            wall_runaways += 1
            wall_runaway_turns.append("T%d (wall %.1fs > cap %.1fs)"
                                      % (t, exc.wall_s, wall_cap))
            fail_extra = dict(extras, error="turn_wall_cap",
                              prompt_sha256=sha256_text(info["prompt"]),
                              turn_wall_cap_s=wall_cap)
            if wall_runaways >= runaway_turns:
                # STOP-REASON-HOLES: the row that ENDS the run on --runaway-turns is a
                # runaway abort; a capped turn that the run survives stays turn_wall_cap.
                fail_extra["runaway_abort"] = True
            if is_answer_turn:
                fail_extra.update(checkpoint_answer_fields(None))
            append_row(rows_path, make_row(
                cfg, fixture, arm, rep, run_id, t, part, part["content"], "turn",
                manifest_sha, fail_extra))
            _escalate(t, exc, part)
            if wall_runaways >= runaway_turns:
                print(f"RUNAWAY ABORT after T{t}: {_runaway_detail()}; "
                      f"{sent} request(s) sent, {t}/{n_turns} turns reached, partial "
                      f"rows kept at {rows_path}", file=sys.stderr)
                return _abort_stop(6, gate, manifest_path, manifest_sha,
                                   rows_path)
            continue
        except RequestFailure as exc:
            fail_extra = dict(extras, http_status=exc.status, error=str(exc),
                              prompt_sha256=sha256_text(info["prompt"]))
            if is_answer_turn:
                fail_extra.update(checkpoint_answer_fields(None))
            append_row(rows_path, make_row(
                cfg, fixture, arm, rep, run_id, t, None, None, "turn", manifest_sha,
                fail_extra))
            print(f"TURN FAILED T{t}: {exc} — cell stopped, failure row recorded", file=sys.stderr)
            return 4
        sent += 1
        # FETCH-CHANNEL: if the turn asked for the exact lines it needs, serve them.
        # The FINAL response of the turn is what the row records and what the planner
        # replays, so a checkpoint answer lives on the checkpoint turn's own row;
        # every follow-up request is appended BEFORE that row with kind="tool-followup"
        # and fetch_followup=true, so `by_turn[t]` still resolves to the real answer.
        turn_calls: list[dict] = []
        followup_rows: list[dict] = []
        rounds_this_turn = 0
        prompt_serves = 0
        # FETCH-ROUNDS-ACCOUNTING (U-SPCC-50): the cumulative round count as it stood
        # BEFORE this turn bought anything.  Every row of the turn inherits it from
        # `extras`; the follow-up rows and the turn row override it with their own
        # cumulative value, so the file order of a turn's rows (initial, follow-ups,
        # turn) is monotonically non-decreasing.  A tools-off run never stamps it: the
        # concept does not apply there, and `null` is the honest value.
        _rounds_before_turn = fetch_rounds_used
        if tools_enabled(cfg):
            extras["fetch_rounds_used"] = _rounds_before_turn
        # ROW-ATTRIBUTION (docs/ROW-MODEL.md): hold the INITIAL send's own response
        # object.  `fetch_rounds` rebinds `resp` to the last follow-up, so without this
        # reference the turn's first request would leave no measurement of its own --
        # the defect DEDUPE-ROOT-CAUSE proved.  Never reassigned.
        initial_resp = resp
        _retrieval_stamp = {}
        _d_fetch_done = False
        # FETCH-MULTI-ROUND (U-SPCC-54): the D arm's paid rows are written in WIRE ORDER
        # and each one BEFORE the next send.  `_d_initial_written` / `_d_flushed` make the
        # writer IDEMPOTENT, so the failure paths and the completed path can both call it
        # and no request's row is ever written twice.  Both stay 0/False on every other
        # arm, so the shared post-loop writer below is unchanged for them.
        _d_initial_written = False
        _d_flushed = 0

        def _flush_d_rows(final=False):
            """Persist the D turn's paid rows, once each, in wire order.

            ``final=True`` leaves the LAST follow-up row unwritten: the turn row stands in
            its slot (ROW-ATTRIBUTION), so the row count stays one per send.
            """
            nonlocal _d_initial_written, _d_flushed
            if not _d_initial_written:
                _ie = dict(extras, prompt_sha256=sha256_text(info["prompt"]),
                           send_index=0, initial_send=True,
                           row_measurement_source="turn-initial",
                           next_request_kind="tool-followup",
                           fetch_rounds_this_turn=rounds_this_turn)
                if is_answer_turn:
                    _ie.update(checkpoint_answer_fields(initial_resp))
                    # TOOL-CALL-CAPTURE (U-SPCC-49): same precedence as the turn row --
                    # the response-level violation survives the answer-field derivation.
                    if extras.get("protocol_violation") is not None:
                        _ie["protocol_violation"] = extras["protocol_violation"]
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, initial_resp,
                    initial_resp.get("content") if initial_resp else None,
                    "turn-initial", manifest_sha, _ie))
                _d_initial_written = True
            limit = len(followup_rows) - 1 if final else len(followup_rows)
            while _d_flushed < limit:
                append_row(rows_path, followup_rows[_d_flushed])
                _d_flushed += 1

        if arm == arm_cd.ARM_D and (fetch_tools_enabled(cfg) or tools_enabled(cfg)):
            _fetch_budget = arm_cd.resolve_fetch_budget(planner.arm_cd, fixture)
            extras["fetch_budget_tokens"] = _fetch_budget
            # FETCH-NAME-DRIFT (U-SPCC-52): hand the parser the names this run actually
            # DECLARED, so a `read_file` call -- the name the wire schema carries -- is
            # serviced exactly as a `fetch` call is, instead of being filtered out.
            _calls = arm_cd.parse_fetch_calls_from_response(
                resp, tool_names=fetch_call_tool_names(cfg))
            # TOOL-CALL-CAPTURE (U-SPCC-49): a structured call the parser did not consume
            # -- an UNDECLARED name, now that declared names are serviced -- is RECORDED
            # here, preserved verbatim on the row and labelled, instead of being dropped
            # into a bare `unparsed`.  Recording buys no request and spends no round, so
            # the answer contract, the scoring and the fetch budget are untouched; the
            # row simply stops lying about what the server signalled.
            _unserviced = unserviced_structured_calls(resp, _calls)
            if _unserviced:
                extras["tool_calls"] = _unserviced
                extras["unserviced_tool_call_ids"] = [c.get("id") for c in _unserviced]
                extras["protocol_violation"] = "tool_call_unserviced"
            if _calls and any(c.get("text_call") or c.get("protocol_variant") == "text_call" for c in _calls):
                _tc0 = next((c for c in _calls if c.get("text_call") or c.get("protocol_variant") == "text_call"), _calls[0])
                extras["protocol_variant"] = "text_call"
                extras["ref_as_emitted"] = _tc0.get("ref_as_emitted")
                extras["ref_revision_normalised"] = _tc0.get("ref_revision_normalised")
            # FETCH-MULTI-ROUND (U-SPCC-54): the per-turn loop services up to
            # `per_turn_cap` rounds, not exactly one.  Before this the D arm sent ONE
            # `_resp2` follow-up per turn and dropped any call that follow-up itself
            # emitted, so `fetch_rounds_cap_per_turn=3` was stamped on every row while
            # `max(fetch_rounds_this_turn)` never exceeded 1 across the whole arm
            # (measured on measure/rows-e1-parserfix-2026-11-10.jsonl: 125 fetch rows).
            # `cp.TX-03.f04.d8` (turn 32) is the last harness loss it caused: the fetch
            # succeeded and the follow-up's own tool call was never serviced.
            #
            # The loop stops on: no further declared calls, the per-turn cap, the
            # per-arm round pool, or a non-tool-call finish.  Every follow-up is a PAID
            # request and its row is appended BEFORE the next send (the 9a5b811/03e920e
            # guarantee), so rows == sends on every exit path.
            _convo = planner.messages(info["prompt"])
            _arm_pool = fetch_rounds_per_arm(cfg)
            while _calls:
                if per_turn_cap > 0 and rounds_this_turn >= per_turn_cap:
                    break
                if fetch_rounds_used >= _arm_pool:
                    break
                # PAID-ROW-PERSISTENCE: another round is definitely coming (both guards
                # above passed), so every request already sent this turn has its row on
                # disk BEFORE this one reaches the wire.  Flushing here rather than at the
                # end of the previous iteration is what keeps the row count equal to the
                # send count: a round that turns out to be the LAST one is never flushed
                # early, so the turn row can still stand in its slot.  Nothing is flushed
                # on the first round: the turn's own row is written by the failure paths
                # (with their error label) or by the post-loop writer, exactly as before.
                if followup_rows:
                    _flush_d_rows()
                # PAID-ROW-PERSISTENCE (U-SPCC-43): the turn's own request is already
                # paid for.  Anything that unwinds out of the fetch service before the
                # follow-up is sent writes that request's row and leaves through the
                # gate, so rows == sends and the exit reconciliation reports delta 0.
                try:
                    _results, _attempt, _outcomes = arm_cd.service_fetches(
                        planner.arm_cd, _calls, _fetch_budget, tokenizer=getattr(planner.arm_cd, "tokenizer", None))
                    extras["tool_call_id"] = (_results[0].tool_call_id if _results else None)
                    extras["tool_call_ids"] = list(extras.get("tool_call_ids") or []) + [
                        getattr(r, "tool_call_id", None) for r in _results]
                    _asst = {"role": "assistant", "content": resp.get("content") or ""}
                    _tc = resp.get("tool_calls") or []
                    if _tc:
                        _asst["tool_calls"] = [
                            {"id": c.get("id"), "type": c.get("type") or "function",
                             "function": {"name": c.get("name"),
                                          "arguments": c.get("arguments") or "{}"}}
                            for c in _tc
                        ]
                    _tool_msgs = [arm_cd.render_fetch_result(r) for r in _results]
                    _followup_msgs = _convo + [_asst] + _tool_msgs
                except Exception as exc:
                    _persist_d_turn_row(rows_path, cfg, fixture, arm, rep, run_id, t,
                                        manifest_sha, extras, info, initial_resp,
                                        "fetch_service_failed")
                    print(f"TURN FAILED (fetch service) T{t}: {exc} — cell stopped, "
                          f"failure row recorded", file=sys.stderr)
                    return _abort_stop(4, gate, manifest_path, manifest_sha, rows_path)
                try:
                    if sent >= budget:
                        raise BudgetExhausted("fetch follow-up at T%d would exceed the request budget of %d" % (t, budget))
                    if gate is not None:
                        gate.acquire(t, "tool-followup")
                    _resp2 = send_chat(cfg, _followup_msgs)
                except BudgetExhausted as exc:
                    _flush_d_rows()
                    print(f"BUDGET ABORT at T{t}: {exc}", file=sys.stderr)
                    # BUDGET-RECONCILE (U-SPCC-43): a budget-exhausted exit spent
                    # requests, so it reconciles like every other exit path.
                    return _abort_stop(4, gate, manifest_path, manifest_sha, rows_path)
                except CapRefusal as exc:
                    _flush_d_rows()
                    return _cap_stop(exc, gate, manifest_path, manifest_sha, rows_path)
                except RequestFailure as exc:
                    _flush_d_rows()
                    append_row(rows_path, make_row(
                        cfg, fixture, arm, rep, run_id, t, None, None, "tool-followup", manifest_sha,
                        dict(extras, http_status=exc.status, error=str(exc),
                             fetch_followup=True)))
                    print(f"TURN FAILED (fetch follow-up) T{t}: {exc} — cell stopped", file=sys.stderr)
                    return 4
                except client.TurnWallCap as exc:
                    sent += 1
                    part = exc.as_response(cfg)
                    wall_runaways += 1
                    wall_runaway_turns.append("T%d (tool-followup, wall %.1fs > cap %.1fs)"
                                              % (t, exc.wall_s, wall_cap))
                    _flush_d_rows()
                    append_row(rows_path, make_row(
                        cfg, fixture, arm, rep, run_id, t, part, part["content"],
                        "tool-followup", manifest_sha,
                        dict(extras, error="turn_wall_cap", fetch_followup=True,
                             turn_wall_cap_s=wall_cap)))
                    _escalate(t, exc, part, "tool-followup")
                    if wall_runaways >= runaway_turns:
                        return _abort_stop(6, gate, manifest_path, manifest_sha, rows_path)
                    print(f"TURN FAILED (fetch follow-up wall) T{t}", file=sys.stderr)
                    return 4
                sent += 1
                # FETCH-ROUNDS-ACCOUNTING (U-SPCC-50): the D arm's inline follow-up IS a
                # billed round -- it read fresh lines off disk -- so the cumulative
                # counter advances HERE.  Before this the counter was initialised and
                # never incremented on this path, so the arm stamped 0 on every turn row
                # while spending 18 of its 48-round pool.
                fetch_rounds_used += 1
                rounds_this_turn += 1
                resp = _resp2
                _retrieval_stamp = {
                    "fetch_rows": len(_calls),
                    "retrieval_attempt": _attempt,
                    "retrieval_outcomes": _outcomes,
                    "fetch_tokens": arm_cd.fetch_tokens_for(_results),
                    "tokenizer_calls": arm_cd.tokenizer_calls(),
                    "tokenizer_reused": any(getattr(r, "tokenizer_reused", False) for r in _results),
                    "tokenizer_cache_hit": any(getattr(r, "tokenizer_cache_hit", False) for r in _results),
                    "reused": any(getattr(r, "reused", False) for r in _results),
                }
                followup_rows.append(make_row(
                    cfg, fixture, arm, rep, run_id, t, _resp2, _resp2.get("content"), "tool-followup", manifest_sha,
                    dict(extras, prompt_sha256=sha256_text(_followup_msgs[-1]["content"]),
                         fetch_followup=True, tool_calls=[{"ref": c.get("ref")} for c in _calls],
                         fetch_rounds_used=fetch_rounds_used,
                         send_index=rounds_this_turn)))
                _d_fetch_done = True
                # FETCH-MULTI-ROUND (U-SPCC-54): the follow-up's OWN reply is read the
                # same way the turn's was.  A call it carries is serviced on the next
                # iteration instead of being dropped on the floor -- the exact loss that
                # stranded `cp.TX-03.f04.d8` at turn 32.
                _convo = _followup_msgs
                _calls = arm_cd.parse_fetch_calls_from_response(
                    resp, tool_names=fetch_call_tool_names(cfg))
                _unserviced = unserviced_structured_calls(resp, _calls)
                if _unserviced:
                    extras["tool_calls"] = _unserviced
                    extras["unserviced_tool_call_ids"] = [c.get("id") for c in _unserviced]
                    extras["protocol_violation"] = "tool_call_unserviced"

        if tools_enabled(cfg) and not is_answer_turn and arm not in (arm_cd.ARM_C, arm_cd.ARM_D, arm_cd.ARM_SPCC):
            # ANSWER-CONTRACT (v5): tools are unavailable on a checkpoint turn, so no
            # <tool_call> is executed and no follow-up request is bought.
            pinned = pinned_views(fixture, info["prompt"])

            def _may_request(_t=t):
                # Pool of follow-up requests, minus one held back for every declared
                # checkpoint this cell has not reached yet: a T3 recon burst may spend
                # the slack, never T46's last request.
                reserved = sum(1 for ct in cp_turns if ct > _t)
                return followups_bought + reserved < followup_pool

            try:
                (_m, resp, sent, fetch_rounds_used, turn_calls,
                 followup_rows) = fetch_rounds(
                    cfg, fixture, arm, rep, run_id, t, manifest_sha, extras,
                    planner.messages(info["prompt"]), resp, sent, budget, fetch_rounds_used,
                    fetch_cache, pinned, per_turn_cap, _may_request, gate,
                    row_sink=lambda _r: append_row(rows_path, _r),
                    root=getattr(cfg, "root", None))
                followups_bought += len(followup_rows)
                rounds_this_turn = len(followup_rows)
                prompt_serves = sum(1 for c in turn_calls
                                    if c.get("served_from") == "prompt")
            except CapRefusal as exc:
                # PAID-ROW-PERSISTENCE (U-SPCC-42): the refusal lands MID-turn.  The rows
                # for the follow-ups already sent were persisted by fetch_rounds before
                # the refusal unwound; the turn's own send and the last follow-up (whose
                # row IS the turn row) are written here, so rows == requests on the
                # refusal path and the exit reconciliation reports delta 0.
                partial = list(getattr(exc, "partial_followups", None) or [])
                last_resp = getattr(exc, "partial_resp", None) or resp
                if attribute_initial_send() and partial:
                    append_row(rows_path, make_row(
                        cfg, fixture, arm, rep, run_id, t, resp, resp.get("content"),
                        "turn-initial", manifest_sha,
                        dict(extras, prompt_sha256=sha256_text(info["prompt"]),
                             send_index=0, initial_send=True,
                             row_measurement_source="turn-initial",
                             fetch_rounds_this_turn=len(partial),
                             next_request_kind="tool-followup")))
                turn_extra = dict(extras, prompt_sha256=sha256_text(info["prompt"]),
                                  cap_refused_mid_turn=True)
                if partial:
                    # ROW-ATTRIBUTION: this row stands in the LAST follow-up's slot, so
                    # it carries that request's durable markers exactly as the completed
                    # path's turn row does.
                    turn_extra.update(
                        row_measurement_source="tool-followup",
                        send_index=len(partial), fetch_followup=True,
                        fetch_round_final=True,
                        final_round_billed=partial[-1].get("billed_round"),
                        final_round_prompt_served=partial[-1].get("prompt_served"))
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, last_resp,
                    last_resp.get("content") if last_resp else None, "turn",
                    manifest_sha, turn_extra))
                return _cap_stop(exc, gate, manifest_path, manifest_sha, rows_path)
            except BudgetExhausted as exc:
                # Same invariant as the refusal path: the rounds already bought are on
                # disk, and the turn's own send plus the last follow-up are written here.
                partial = list(getattr(exc, "partial_followups", None) or [])
                last_resp = getattr(exc, "partial_resp", None) or resp
                if attribute_initial_send() and partial:
                    append_row(rows_path, make_row(
                        cfg, fixture, arm, rep, run_id, t, resp, resp.get("content"),
                        "turn-initial", manifest_sha,
                        dict(extras, prompt_sha256=sha256_text(info["prompt"]),
                             send_index=0, initial_send=True,
                             row_measurement_source="turn-initial",
                             fetch_rounds_this_turn=len(partial),
                             next_request_kind="tool-followup")))
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, last_resp,
                    last_resp.get("content") if last_resp else None, "turn",
                    manifest_sha, dict(extras, prompt_sha256=sha256_text(info["prompt"]),
                                       error="budget_exhausted")))
                print(f"BUDGET ABORT at T{t}: {exc}", file=sys.stderr)
                # BUDGET-RECONCILE (U-SPCC-43): a budget-exhausted exit spent requests,
                # so it reconciles like every other exit path.
                return _abort_stop(4, gate, manifest_path, manifest_sha, rows_path)
            except client.TurnWallCap as exc:
                sent += 1
                part = exc.as_response(cfg)
                wall_runaways += 1
                wall_runaway_turns.append("T%d (tool-followup, wall %.1fs > cap %.1fs)"
                                          % (t, exc.wall_s, wall_cap))
                # ROW-ATTRIBUTION: the turn's initial send already reached the wire and
                # is measured on its own row ahead of the wall-capped follow-up's.
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, initial_resp,
                    initial_resp.get("content") if initial_resp else None,
                    "turn-initial", manifest_sha,
                    dict(extras, prompt_sha256=sha256_text(info["prompt"]),
                         send_index=0, initial_send=True,
                         row_measurement_source="turn-initial",
                         next_request_kind="tool-followup")))
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, part, part["content"],
                    "tool-followup", manifest_sha,
                    dict(extras, error="turn_wall_cap", fetch_followup=True,
                         turn_wall_cap_s=wall_cap,
                         **({"runaway_abort": True}
                            if wall_runaways >= runaway_turns else {}))))
                _escalate(t, exc, part, "tool-followup")
                if wall_runaways >= runaway_turns:
                    print(f"RUNAWAY ABORT after T{t}: {_runaway_detail()}; "
                          f"{t}/{n_turns} turns reached, partial rows kept at "
                          f"{rows_path}", file=sys.stderr)
                    return _abort_stop(6, gate, manifest_path, manifest_sha,
                                       rows_path)
                continue
            except RequestFailure as exc:
                # ROW-ATTRIBUTION: the initial send is measured even when the follow-up
                # that failed ended the cell; a failed follow-up has no measurement.
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, initial_resp,
                    initial_resp.get("content") if initial_resp else None,
                    "turn-initial", manifest_sha,
                    dict(extras, prompt_sha256=sha256_text(info["prompt"]),
                         send_index=0, initial_send=True,
                         row_measurement_source="turn-initial",
                         next_request_kind="tool-followup")))
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, None, None, "tool-followup", manifest_sha,
                    dict(extras, http_status=exc.status, error=str(exc),
                         fetch_followup=True)))
                print(f"TURN FAILED (fetch follow-up) T{t}: {exc} — cell stopped, failure row "
                      "recorded", file=sys.stderr)
                return 4
        row_extra = dict(extras, prompt_sha256=sha256_text(info["prompt"]))
        if _retrieval_stamp:
            row_extra.update(_retrieval_stamp)
        # ROW-ATTRIBUTION: ONE ROW PER SEND.  With k >= 1 follow-ups this turn made
        # k+1 requests: the initial send (row_initial, below), follow-ups 1..k-1
        # (their own ``kind="tool-followup"`` rows) and follow-up k, whose row IS this
        # turn row.  The row count is unchanged from the pre-fix writer (k+1), but no
        # two rows now share one measurement: the last follow-up is no longer written
        row_extra["row_measurement_source"] = (
            "tool-followup" if followup_rows else "turn-initial")
        row_extra["send_index"] = int(rounds_this_turn) if tools_enabled(cfg) else 0
        if attribute_initial_send() and followup_rows:
            # This row stands in the last follow-up request's slot, so the durable
            # markers that request carried ride here: fetch_rounds_spent counts
            # ``fetch_followup`` rows, and resume must not lose the last round.
            last = followup_rows[-1]
            row_extra["fetch_followup"] = True
            row_extra["fetch_round_final"] = True
            row_extra["final_round_billed"] = last.get("billed_round")
            row_extra["final_round_prompt_served"] = last.get("prompt_served")
        if is_answer_turn:
            row_extra.update(checkpoint_answer_fields(resp))
            # TOOL-CALL-CAPTURE (U-SPCC-49): the answer fields above are derived from the
            # (empty) content, so they would erase a violation the RESPONSE itself proved.
            # The response-level fact wins; the answer fields stay exactly as parsed.
            if extras.get("protocol_violation") is not None:
                row_extra["protocol_violation"] = extras["protocol_violation"]
        if tools_enabled(cfg) and not is_answer_turn:
            # TOOL-CALL-CAPTURE (U-SPCC-49): `turn_calls` is the SERVICED/refused list and
            # is empty on the D arm, whose calls are parsed by `arm_cd`.  Never let it
            # erase the unserviced calls the response itself carried.
            if turn_calls or row_extra.get("tool_calls") is None:
                row_extra["tool_calls"] = turn_calls
            row_extra["fetch_rounds_used"] = fetch_rounds_used
            row_extra["fetch_rounds_this_turn"] = rounds_this_turn
            # E7's primary mechanism, measured per row: a tool call whose
            # (path, start_line, end_line) was already read in this cell is a
            # RE-FETCH -- the cost a fold causes by dropping the journal.  The
            # set is per-cell, so a re-read after a fold is counted.
            _refetch = count_refetch(turn_calls, planner.seen_ranges)
            row_extra["refetch_count"] = _refetch
            row_extra["distinct_ranges_read"] = len(planner.seen_ranges)
            row_extra["fetch_prompt_serves"] = prompt_serves
            row_extra["fetch_rounds_cap_per_turn"] = per_turn_cap
            suppressed = sum(1 for c in turn_calls if c.get("followup_suppressed"))
            if suppressed:
                # RECORD-STOP-REASON: a follow-up request the allowance refused writes no
                # row of its own; the count rides the turn row, whose stop_reason is the
                # response that ended the turn.
                row_extra["fetch_suppressed"] = suppressed
        row = make_row(cfg, fixture, arm, rep, run_id, t, resp, resp["content"], "turn", manifest_sha,
                       row_extra)
        # STOP-REASON-HOLES: predicate 2 (the ceiling-consume signature) ends the cell on
        # --runaway-turns.  The row that ends it is a runaway abort, not a plain length
        # stop, so it is labelled before it is written (no historical row is touched).
        signature = _ceiling_violation(row)
        if signature and ceiling_violations + 1 >= runaway_turns:
            row["stop_reason"] = client.STOP_REASON_RUNAWAY_TURN
            row["truncated"] = client.truncated_for(row["stop_reason"])
            row["runaway_abort"] = True
        if attribute_initial_send() and followup_rows:
            # ROW-ATTRIBUTION: the initial send's own row, written in wire order ahead
            # of the follow-ups it triggered.  It is the ONLY row that measures the
            # turn's own request; ``kind="turn-initial"`` never existed before, so no
            # historical row is re-meant and no historical file is touched.
            # FETCH-MULTI-ROUND (U-SPCC-54): the D arm may already have written this row
            # (and the follow-ups before it) mid-turn, so the writer is idempotent.
            if not _d_initial_written:
                initial_extra = dict(
                    extras, prompt_sha256=sha256_text(info["prompt"]),
                    send_index=0, initial_send=True,
                    row_measurement_source="turn-initial",
                    fetch_rounds_this_turn=len(followup_rows),
                    next_request_kind="tool-followup")
                if is_answer_turn:
                    initial_extra.update(checkpoint_answer_fields(initial_resp))
                    # TOOL-CALL-CAPTURE (U-SPCC-49): same precedence as the turn row --
                    # the response-level violation survives the answer-field derivation.
                    if extras.get("protocol_violation") is not None:
                        initial_extra["protocol_violation"] = extras["protocol_violation"]
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, initial_resp,
                    initial_resp.get("content") if initial_resp else None,
                    "turn-initial", manifest_sha, initial_extra))
                _d_initial_written = True
        # follow-ups 1..k-1 get their own rows; follow-up k's row is the turn row below.
        for frow in (followup_rows[:-1] if attribute_initial_send() else followup_rows)[_d_flushed:]:
            append_row(rows_path, frow)
        append_row(rows_path, row)
        planner.record(t, resp["content"])
        # RUNAWAY-POLICY predicate 2: only a response ABOVE the ceiling counts. A
        # `length` truncation AT the ceiling is data and falls straight through.
        if signature:
            ceiling_violations += 1
            ceiling_violation_turns.append("T%d (%s)" % (t, signature))
            print(f"RUNAWAY T{t}: {signature} — a server that ignored the max_tokens "
                  f"ceiling (ceiling violations {ceiling_violations}/{runaway_turns})",
                  file=sys.stderr)
            if ceiling_violations >= runaway_turns:
                print(f"RUNAWAY ABORT after T{t}: {_runaway_detail()}; {sent} request(s) "
                      f"sent, {t}/{n_turns} turns reached, partial rows kept at "
                      f"{rows_path}", file=sys.stderr)
                return _abort_stop(6, gate, manifest_path, manifest_sha,
                                   rows_path)
        print(f"  [T{t}] prompt={row['prompt_tokens']} cached={row['cached_tokens']} "
              f"ttft_ms={row['ttft_ms']} src={row['content_source']} "
              f"finish={row['finish_reason']} stop={row['stop_reason']} "
              f"truncated={row['truncated']} "
              f"lat={row['latency_s']} comp={row['completion_tokens']}")
        if is_answer_turn:
            print(f"  [T{t}] answer_contract kind={row['answer_kind']} "
                  f"value={row['answer_value']!r} error={row['answer_parse_error']}")
        if tools_enabled(cfg) and turn_calls:
            done = sum(1 for c in turn_calls if c.get("executed"))
            print(f"  [T{t}] tool_calls={len(turn_calls)} executed={done} "
                  f"fetch_followups={len(followup_rows)} fetch_rounds_used={fetch_rounds_used}"
                  f"/{fetch_rounds_per_arm(cfg)} prompt_served={prompt_serves} "
                  f"rounds_this_turn={rounds_this_turn}/{per_turn_cap if per_turn_cap else 'inf'} "
                  f"requests_sent={sent} followups={followups_bought}/{followup_pool}")
    if tools_enabled(cfg):
        print(f"requests_sent={sent} (budget {budget}; fetch rounds "
              f"{fetch_rounds_used}/{fetch_rounds_per_arm(cfg)})")
    # WIRE-CAP-GATE: reconcile the run's own count against the rows the next run will read.
    _rec, cap_rc = _gate_finish(gate, manifest_path, manifest_sha, rows_path)
    return cap_rc


# ------------------------------------------------------------------------ summary
def rows_for_run(rows_path: str, run_base: str) -> list[dict]:
    out: list[dict] = []
    if not os.path.exists(rows_path):
        return out
    with open(rows_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("run_id", "")).startswith(run_base):
                out.append(row)
    return out


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, int(ceil(q * len(ordered))) - 1))
    return ordered[idx]


def token_distribution(rows: list[dict]) -> dict:
    """reasoning_tokens + content_tokens per answered turn (nearest-rank p95)."""
    totals = [float((r.get("reasoning_tokens") or 0) + (r.get("content_tokens") or 0))
              for r in rows if r.get("error") is None and r.get("reasoning_tokens") is not None]
    if not totals:
        return {"n": 0, "mean": None, "p95": None, "max": None}
    return {
        "n": len(totals),
        "mean": round(sum(totals) / len(totals), 1),
        "p95": percentile(totals, 0.95),
        "max": max(totals),
    }


def summarise_rows(rows: list[dict]) -> dict:
    """Counts the card requires: truncated rows, content_source mix, per-row TTFT,
    the reasoning-policy verdict per row, and the per-turn token distribution."""
    sources = {"content": 0, "reasoning": 0, "both": 0, "none": 0, None: 0}
    for r in rows:
        sources[r.get("content_source")] = sources.get(r.get("content_source"), 0) + 1
    answers = {"content": 0, "reasoning-fallback": 0, "none": 0}
    for r in rows:
        answers[r.get("answer_source") or "none"] = answers.get(r.get("answer_source") or "none", 0) + 1
    usable = [r["latency_s"] for r in rows
              if r.get("timing_usable") and r.get("latency_s") is not None]
    return {
        "rows": len(rows),
        "truncated": sum(1 for r in rows if r.get("truncated")),
        "ttft_n": sum(1 for r in rows if r.get("ttft_ms") is not None),
        "content_source_counts": {str(k): v for k, v in sources.items() if v},
        "answer_source_counts": answers,
        "finish_reasons": _count(r.get("finish_reason") for r in rows),
        # RECORD-STOP-REASON: the closed vocabulary, countable straight off the rows.
        "stop_reasons": _count(r.get("stop_reason") for r in rows),
        "requests_spent": sum(1 for r in rows if r.get("error") is None),
        "failed_rows": sum(1 for r in rows if r.get("error") is not None),
        "failed_turns": sum(1 for r in rows if r.get("failed_turn")),
        "reasoning_fallback_rows": sum(1 for r in rows
                                       if r.get("answer_source") == "reasoning-fallback"),
        "timing_usable_n": len(usable),
        "latency_usable_mean_s": round(sum(usable) / len(usable), 3) if usable else None,
        "token_distribution": token_distribution(rows),
        "channel_token_method": next((r.get("channel_token_method") for r in rows
                                      if r.get("channel_token_method")), None),
    }


def _count(values) -> dict:
    out: dict = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return out


def report_run(rows_path: str, run_base: str, cfg, smoke: bool = False) -> int:
    rows = rows_for_run(rows_path, run_base)
    if not rows:
        print("SUMMARY ABORT: no rows for this run base", file=sys.stderr)
        return 6
    s = summarise_rows(rows)
    print("\n=== SUMMARY ===")
    print(f"rows={s['rows']} requests={s['requests_spent']} truncated={s['truncated']} "
          f"ttft_n={s['ttft_n']} max_tokens={cfg.max_tokens}")
    print(f"content_source: {json.dumps(s['content_source_counts'], sort_keys=True)}")
    print(f"answer_source:  {json.dumps(s['answer_source_counts'], sort_keys=True)}")
    print(f"finish_reason:  {json.dumps(s['finish_reasons'], sort_keys=True)}")
    print(f"failed_turns={s['failed_turns']} reasoning_fallback={s['reasoning_fallback_rows']} "
          f"timing_usable={s['timing_usable_n']} token_dist={json.dumps(s['token_distribution'])} "
          f"tok_method={s['channel_token_method']}")
    if smoke:
        print("\nturn arm prompt_tokens cached_tokens ttft_ms r_tok c_tok answer_source "
              "finish_reason truncated")
        for r in rows:
            print(f"{r['turn']:>4} {r['arm']:<18} {str(r['prompt_tokens']):>6} "
                  f"{str(r['cached_tokens']):>6} {str(r['ttft_ms']):>10} "
                  f"{str(r.get('reasoning_tokens')):>6} {str(r.get('content_tokens')):>6} "
                  f"{str(r.get('answer_source')):>18} {str(r['finish_reason']):>13} "
                  f"{str(r['truncated']):>9}")
        bad = [r for r in rows if r.get("answer_source") == "none"]
        print(f"\nsmoke: {len(rows)} rows, {len(bad)} answer_source=none, "
              f"truncated={s['truncated']}, failed_turns={s['failed_turns']}, "
              f"ttft_n={s['ttft_n']}")
        if bad:
            print(f"SMOKE FAIL: {len(bad)} row(s) carry no answer on either channel",
                  file=sys.stderr)
            return 7
        # RUN-INSTRUMENT-FIX requirement: a smoke row that hits the cap is a truncated
        # measurement and must fail the smoke, not merely be annotated.
        if s["truncated"]:
            print(f"SMOKE FAIL: {s['truncated']} row(s) TRUNCATED at "
                  f"max_tokens={cfg.max_tokens}", file=sys.stderr)
            return 7
        print("SMOKE PASS: every row answer-bearing and none truncated "
              "(0 rows answer_source=none, 0 truncated)")
    if s["truncated"]:
        print(f"NOTE: {s['truncated']} row(s) TRUNCATED at max_tokens={cfg.max_tokens} — "
              f"failed_turn rows are excluded from latency averages.", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------- main
def build_parser():
    """The CLI. Exposed so a test builds a cfg WITHOUT re-deriving defaults."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fixture", default=None)
    ap.add_argument("--task", default=None)
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--compact-every", default=None, dest="compact_every", metavar="LIST",
                    help="E2's cell dimension: comma-separated compaction intervals "
                         "(e.g. 12,24,48). Each interval is one arm-variant of the "
                         "spcc arm inside the SAME cell, so G3's n = turns x variants "
                         "x reps. Omitted = the module default (%d), one variant, "
                         "byte-identical to a run without this flag." % COMPACT_EVERY)
    ap.add_argument("--window-turns", type=int, default=None, dest="window_turns",
                    metavar="N",
                    help="masking window for the C/D arms (default: the module constant, "
                         "4). A value above the fixture's turn count masks nothing, which "
                         "is how E3 forces retention with the body intact.")
    ap.add_argument("--generation", default="gen-7",
                    help="recorded validity generation of this run; gen-7 asserts hard, "
                         "gen-6 and earlier are labelled LEGACY-NONCONFORMING")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--manifest-dir",
                    default=os.path.join(_REPO_ROOT, "experiments/ptr-engine/longrun/manifests"))
    ap.add_argument("--manifest-path", default=None)
    ap.add_argument("--preview-root", default=None, dest="preview_root",
                    help="redirect the dry-run preview tree (default: the tracked "
                         "state/previews/<task_id> tree). Tests MUST pass a temp dir so a "
                         "dry run never overwrites committed evidence.")
    ap.add_argument("--rows", default=None)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--engine", default=DEFAULT_ENGINE, choices=("sglang", "vllm"))
    ap.add_argument("--stream", dest="stream", action="store_true", default=True)
    ap.add_argument("--no-stream", dest="stream", action="store_false")
    # Chat-template thinking switch (SGLang).  'auto' (default) sends NO chat_template_kwargs
    # key at all, so the body stays byte-identical to every run before this flag existed;
    # 'on'/'off' add {"enable_thinking": <bool>}.  The setting is frozen in the manifest and
    # stamped on every row, because rows from different settings must never be pooled.
    ap.add_argument("--temperature", type=float, default=None,
                    help="greedy-decoding temperature; MUST be stated per run (default 0). "
                         "A run without an explicit --temperature is refused at preflight.")
    ap.add_argument("--seed", type=int, default=42,
                    help="fixed seed recorded on every row (default 42)")
    ap.add_argument("--thinking", choices=("auto", "on", "off"), default="off",
                    help="HARNESS-GUARDS: cells default to thinking OFF; a run with "
                         "thinking on must opt in explicitly, and every row records the "
                         "effective setting")
    # HARNESS-GUARDS. The live cell on 2026-10-26T145758Z spent 7m56s and 16,384
    # completion tokens on one turn with nothing objecting; 16384 was the default that
    # let it. The ceiling is now a finite 4096 by default (see client.DEFAULT_MAX_TOKENS)
    # and `--turn-wall-cap` / `--runaway-turns` bound the turn and the run, not just one
    # request. A cell that needs more opts in explicitly and records the values per row.
    ap.add_argument("--max-tokens", type=int, default=4096,
                    help="completion ceiling sent on EVERY request (default 4096)")
    ap.add_argument("--turn-wall-cap", type=float, default=180.0,
                    help="seconds one turn may run; past it the stream is CLOSED, the "
                         "turn aborted, the row written with error='turn_wall_cap' and "
                         "truncated=true (default 180)")
    ap.add_argument("--runaway-turns", type=int, default=2,
                    help="how many WALL-TIME runaways end the cell with exit 6. A "
                         "wall-time runaway is a turn whose stream --turn-wall-cap "
                         "CLOSED (client.py TurnWallCap). A `length` truncation AT "
                         "--max-tokens is NOT a runaway and is never counted: it is "
                         "bounded data recorded as stop_reason=length. A response ABOVE "
                         "--max-tokens (a server that ignored the ceiling) counts "
                         "against the same limit. See docs/RUNAWAY-POLICY.md "
                         "(default 2)")
    # 16384 (was 128 -> 1024 -> 4096): Stage 1 (RUN-STAGE1-LR01) truncated 140/192 rows at
    # 128; at 1024 a measured 7/12 smoke rows still hit finish_reason="length"; at 4096 the
    # 4-row fix run still truncated transcript-grow T3 at 4096 completion tokens with
    # completion on the reasoning channel only and no answer.  HARNESS-GUARDS reverses the
    # drift: 4096 is the DEFAULT again because an unbounded ceiling is the runaway. A cell
    # that needs a larger ceiling opts in via --max-tokens, and the value it used is on
    # every row; the cap is NOT the policy on its own: see _REASONING_POLICY (reasoning-only
    # rows are marked, truncated-without-value rows are failed turns), and
    # `--turn-wall-cap` / `--runaway-turns` bound the turn and the run.
    ap.add_argument("--max-turns", type=int, default=0,
                    help="stop each cell after this many turns (0 = the fixture's N)")
    ap.add_argument("--smoke", action="store_true",
                    help="4 arms x 3 turns = 12 requests; per-row table with reasoning/content "
                         "token split and answer_source; non-zero exit if any row has "
                         "answer_source == 'none'")
    ap.add_argument("--claim-mode", default=None, dest="claim_mode",
                    metavar="smoke|plumbing|H1|H2|H3",
                    help="CLAIM-ROW-STAMP: the claim this run declares. `smoke` and "
                         "`plumbing` declare claim=none (rows are NOT "
                         "comparison_eligible); H1|H2|H3 declare a PARM-1 claim. The "
                         "spelling is resolved by claim_mode.resolve_claim ONCE and "
                         "stamped on EVERY row via make_row. There is NO default: an "
                         "absent flag is refused with exit 12 and the module's own "
                         "sentence -- silence is not a claim")
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--show-prompts", action="store_true")
    # FETCH-CHANNEL (opt-in). Default OFF: no tool code runs, no row/manifest key is
    # added, and request bodies are byte-identical to runs made before this flag.
    # With `read_file` on, a turn that emits `<tool_call>…read_file…` gets its lines
    # read back, bounded by 2 calls/turn, 1 follow-up request per fetch, 24 fetch
    # rounds per arm; every follow-up is a real request and is row-recorded.  A path
    # resolves under the workspace root, then the engine root (base reported).
    # PROBE-CP3-V6 (b): fetch rounds per turn (0 = unbounded, the pre-V6 behaviour).
    ap.add_argument("--fetch-rounds-per-turn", type=int, default=TOOL_FETCH_ROUNDS_PER_TURN,
                    metavar="N",
                    help="max fetch rounds bought in one turn (default 3; 0 = unbounded)")
    # RUNNER-ROUNDS-48: the per-ARM pool, settable beside the per-turn cap.  The value
    # prices the projection, caps the channel and is frozen in the manifest; a
    # non-positive value is refused by name in main() (never a silent fallback).
    ap.add_argument("--fetch-rounds-per-arm", type=int, default=TOOL_FETCH_ROUNDS_PER_ARM,
                    metavar="N",
                    help="fetch-round pool per arm (default 48; a positive integer)")
    # WIRE-CLIENT: --metrics-scrape / --no-metrics-scrape. Registered by the client so
    # the flag and the client's precedence rule (PTR_METRICS_SCRAPE) can never drift.
    client.add_metrics_scrape_argument(ap)
    ap.add_argument("--tools", default="", metavar="LIST",
                    help="comma-separated tool channel(s) to enable (default: none / off); "
                         "supported: read_file, grep")
    # STAGE-2-ROOT: every tool call resolves under ONE root.  Without a frozen root an
    # "agentic" read is a read of the live tree, so the task is not reproducible and a
    # re-run measures a different repository.  Default stays cwd, so every pre-existing
    # invocation is byte-identical.
    ap.add_argument("--root", default=None, metavar="DIR",
                    help="workspace root every tool call resolves under (default: cwd); "
                         "point it at a frozen snapshot for a reproducible episode")
    ap.add_argument("--snapshot-manifest", default=None, metavar="PATH",
                    help="manifest.json written by longrun/tools/build_snapshot.py; every "
                         "entry is re-hashed before the first request and the run aborts "
                         "with 'snapshot_manifest_mismatch: <relpath>' on any difference")
    ap.add_argument("--fetch-policy", choices=("strict", "instructed"), default="strict",
                    dest="fetch_policy",
                    help="FETCH-POLICY: 'strict' (default, reproducible) or 'instructed' "
                         "(checkpoint instruction states a not-in-view value must be "
                         "fetched before answering; answering from memory is not "
                         "acceptable). Recorded as fetch_policy on every row.")
    # WIRE-CAP-GATE.  A declared per-run request allocation, enforced PER REQUEST inside
    # the turn loop immediately before the send (the ledger's conductor_wiring): 'projection'
    # (the default) is the cell's structural request count (turns + digests + fetch pool); an
    # integer is an explicit budget.  Either way the global cap (spent rows + this run) is
    # enforced too, from an in-memory count, so a refusal happens BEFORE the wire.
    ap.add_argument("--request-allocation", default="projection", metavar="N|projection",
                    help="requests this run may send: an integer, or 'projection' for the "
                         "cell's structural request count (default: projection)")
    ap.add_argument("--budget-cap", type=int, default=None,
                    help="global request cap for all recorded runs (default: the ledger's, 4320)")
    ap.add_argument("--budget-reserve", type=int, default=0,
                    help="unspendable part of --budget-cap (default 0)")
    ap.add_argument("--budget-glob", default=None,
                    help="row files the cap gate counts at run start (default: "
                         "experiments/ptr-engine/measure/rows-*.jsonl); the run's own row file "
                         "is always included")
    return ap


def compact_intervals(cfg) -> list:
    """The cell's compaction intervals, in declared order.

    ``--compact-every`` is a comma list (``12,24,48``).  Omitted means the module
    default as a SINGLE variant, so a run without the flag is one variant at
    ``COMPACT_EVERY`` and its prompts are byte-identical to the pre-change run.
    Duplicates collapse (two identical variants would be the same cell twice).
    """
    cached = getattr(cfg, "compact_intervals", None)
    if cached is not None:
        return list(cached)
    raw = getattr(cfg, "compact_every", None)
    if raw is None or not str(raw).strip():
        return [COMPACT_EVERY]
    out: list = []
    for part in str(raw).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            value = int(part)
        except ValueError:
            raise ValueError("--compact-every %r is not an integer list" % (raw,))
        if value < 1:
            raise ValueError("--compact-every %r: intervals must be >= 1" % (raw,))
        if value not in out:
            out.append(value)
    if not out:
        raise ValueError("--compact-every %r names no interval" % (raw,))
    return out


def window_turns_setting(cfg) -> int:
    """The masking window this run uses (``--window-turns``, default ``WINDOW_TURNS``).

    Omitted means the module constant, so a run without the flag masks exactly as
    before and its prompts are byte-identical.  A value above the fixture's turn
    count masks nothing: the body is retained and the arm measures position, not
    eviction (PREREG-SPCC §E3).
    """
    raw = getattr(cfg, "window_turns", None)
    if raw is None:
        return arm_cd.WINDOW_TURNS
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError("--window-turns %r is not an integer" % (raw,))
    if value < 1:
        raise ValueError("--window-turns %r: the window must be >= 1" % (raw,))
    return value


def expand_cells(arms, reps, intervals) -> list:
    """One cell per ``(arm, rep, interval)`` -- the interval is a cell dimension.

    A single interval reproduces the pre-change cell list exactly (one variant
    per arm/rep), so a run without ``--compact-every`` is unchanged.  With three
    intervals the same cell carries three arm-variants, which is what makes G3's
    ``n = turns x variants x reps`` see 300 for a 100-turn E2 cell.
    """
    return [(arm, rep, int(interval))
            for arm in arms
            for rep in range(1, int(reps) + 1)
            for interval in intervals]


def prereg_gate_args(cfg, fixture: dict):
    """G3's operand surface, built from the runner's own flag names.

    ``cell.eval_gate_prereg`` reads ``args.hypothesis``, ``args.turns`` and ``args.reps``;
    the runner spells those ``--claim-mode``, ``--max-turns`` (0 = the fixture's N) and
    ``--reps``.  The adapter lives HERE, at the call site, so the gate keeps its own
    contract and is not weakened to fit the runner's spelling.  ``hypothesis`` is the
    ALREADY-RESOLVED claim (``cfg.claim``), so the gate adjudicates the same decision the
    rows will be stamped with -- never a second parse of the flag.
    """
    claim = getattr(cfg, "claim", None)
    if claim is not None and claim.get("mode") == claim_mode.MODE_SMOKE:
        hypothesis = claim_mode.MODE_SMOKE
    elif claim is not None:
        hypothesis = claim.get("claim")
    else:
        hypothesis = getattr(cfg, "claim_mode", None)
    # ARM-COUNT (U-SPCC-40): G3's n is turns x arms x reps -- the quantity the runner
    # prices per arm (run_longrun.py:3105) and sums into would_send_total (:3113).  The
    # adapter used to omit the arm term entirely, so a three-arm two-rep 100-turn cell
    # was admitted at n=200 while sending 600.  ``cfg.arms`` is the run's own arm list
    # (``--arms``, comma-separated), so the count is the number of arms this run will
    # actually execute -- never a default of 1.
    import cell as _cell  # noqa: E402 - ONE arms-count rule, never a second copy
    # E2's cell dimension: each compaction interval is one arm-variant of the same
    # arm inside the same cell, so the arm term G3 multiplies by is
    # (declared arms x interval variants).  With one interval this is exactly the
    # pre-change count, so a run without --compact-every gates as it always did.
    variants = len(compact_intervals(cfg))
    return argparse.Namespace(hypothesis=hypothesis,
                              turns=cell_turns(cfg, fixture),
                              reps=int(getattr(cfg, "reps", 1) or 1),
                              arms=_cell._arms_count(getattr(cfg, "arms", None)) * variants)


def enforce_prereg_gate(cfg, fixture: dict) -> int:
    """G3 before the first request: refuse a cell whose n cannot support its claim.

    Same shape as the cap gate -- the gate's own refusal text, verbatim, its own exit
    code (12), no row written and no request sent.  There is no bypass flag: the
    operands are the run's own ``--claim-mode`` / ``--max-turns`` / ``--reps`` and the
    fixture's checkpoint count, and the decision is ``cell.eval_gate_prereg``'s.
    """
    import cell as _cell  # noqa: E402 - the gate's own implementation, never a copy
    try:
        verdict = _cell.eval_gate_prereg(prereg_gate_args(cfg, fixture), fixture)
    except _cell.Abort as exc:
        print("%s" % (exc.message,), file=sys.stderr)
        print("PREREG REFUSED (exit %d): no row was written and no request was sent"
              % exc.code, file=sys.stderr)
        return exc.code
    if verdict.get("ok"):
        # PREREG-CEILING-ON-THE-BRAKE (U-SPCC-40): G3's n is a BASELINE (turns x arms x
        # reps).  Fetch follow-ups are real requests the baseline cannot see
        # (run_longrun.py:500-501), so an admitted baseline is not a promise about
        # sends.  The ceiling the claim was admitted under is handed to the per-request
        # brake, which counts ACTUAL sends before each one and stops the run at the
        # ceiling -- a fetch-heavy cell is refused at 500 real requests, not admitted on
        # a predicted 300.  The brake only ever gains a limit here; the global cap and
        # the run allocation keep their existing semantics.
        ceiling = (verdict.get("thresholds") or {}).get("request_ceiling")
        if (isinstance(ceiling, (list, tuple)) and len(ceiling) == 2
                and isinstance(ceiling[1], int)):
            cfg.prereg_request_ceiling = int(ceiling[1])
        return 0
    print("%s" % (_cell._gate_message(verdict),), file=sys.stderr)
    print("PREREG REFUSED (exit %d): no row was written and no request was sent"
          % verdict.get("exit", 12), file=sys.stderr)
    return verdict.get("exit", 12)


def main(argv=None) -> int:
    cfg = build_parser().parse_args(argv)

    # TEMPZERO: temperature must be stated per run, never inherited silently.
    if cfg.temperature is None:
        print("--temperature must be stated explicitly (got None); refusing run",
              file=sys.stderr)
        return 2

    # RUNNER-ROUNDS-48: the pool is priced and capped by the same number, so zero or a
    # negative value is a launch error with a name, not a silent fallback to 48.
    if cfg.fetch_rounds_per_arm is None or int(cfg.fetch_rounds_per_arm) <= 0:
        print(f"--fetch-rounds-per-arm must be a positive integer "
              f"(got {cfg.fetch_rounds_per_arm!r}); 0 and negative values are refused",
              file=sys.stderr)
        return 2

    # STAGE-2-ROOT: a named root must exist, and a named manifest must still describe
    # it.  Both checks run BEFORE the first request, so a moved snapshot costs nothing.
    if cfg.root is not None and not os.path.isdir(cfg.root):
        print(f"--root is not a directory: {cfg.root}", file=sys.stderr)
        return 2
    if cfg.snapshot_manifest:
        _root_sha, _refusal = verify_snapshot_manifest(cfg.snapshot_manifest)
        if _refusal:
            print(_refusal, file=sys.stderr)
            return 2
        _manifest_root = os.path.dirname(os.path.abspath(cfg.snapshot_manifest))
        if cfg.root is not None and os.path.realpath(cfg.root) != os.path.realpath(_manifest_root):
            print(f"snapshot_manifest_root_mismatch: --root {cfg.root} is not the "
                  f"manifest's directory {_manifest_root}", file=sys.stderr)
            return 2
        print(f"SNAPSHOT: root_sha256={_root_sha} manifest={cfg.snapshot_manifest}")

    if cfg.self_test:
        return self_test()

    if cfg.smoke:
        cfg.arms = ",".join(ARMS)
        cfg.reps = 1
        cfg.max_turns = 3
        cfg.stream = True
        if not cfg.rows or cfg.rows.endswith("rows-longrun-2026-10-26.jsonl"):
            cfg.rows = "experiments/ptr-engine/measure/rows-longrun-2026-10-26-policy.jsonl"
        cfg.run_id = cfg.run_id or f"smoke-{utc_now().strftime('%Y%m%dT%H%M%SZ')}"
        print(f"SMOKE: {len(ARMS)} arms x 3 turns = {len(ARMS) * 3} requests, max_tokens={cfg.max_tokens}")
        print(f"POLICY: {_REASONING_POLICY}")
    arms = [a.strip() for a in cfg.arms.split(",") if a.strip()]
    bad = [a for a in arms if a not in ARMS]
    if bad:
        print(f"unknown arm(s): {bad}; known: {list(ARMS)}", file=sys.stderr)
        return 2
    # ARM-REQUIRES-TOOLS (U-SPCC-46): checked for EVERY requested arm before the first
    # cell runs, so a multi-arm launch cannot spend the earlier arms' requests and then
    # discover the fetch arm was degenerate.  Same refusal, same code, no row, no socket.
    for _arm in arms:
        rc_tools = refuse_arm_without_tools(cfg, _arm)
        if rc_tools != 0:
            return rc_tools
    # FIXTURE/TASK GUARD: never silently default to LR-01.
    if cfg.fixture is None and cfg.task is None:
        print("no selector: neither --task nor --fixture given", file=sys.stderr)
        return 2
    if cfg.fixture is None and cfg.task is not None:
        resolved = resolve_fixture_path(cfg.task)
        if resolved is None:
            print(f"cannot resolve fixture for task {cfg.task}", file=sys.stderr)
            return 2
        cfg.fixture = resolved
    # task/fixture id cross-check BEFORE validation, so a mismatch is reported by id even
    # when the fixture is a stub or otherwise unlaunchable.
    if cfg.task and cfg.fixture:
        try:
            _raw = json.loads(open(cfg.fixture, encoding="utf-8").read())
            _fid = _raw.get("task_id") if isinstance(_raw, dict) else None
        except (OSError, json.JSONDecodeError):
            _fid = None
        if _fid is not None and cfg.task != _fid:
            print(f"task {cfg.task} != fixture task_id {_fid}", file=sys.stderr)
            return 2
    try:
        fixture = load_fixture(cfg.fixture)
    except FixtureError as exc:
        print(f"FIXTURE ERROR: {exc}", file=sys.stderr)
        return 2
    if cfg.task and cfg.task != fixture["task_id"]:
        print(f"task {cfg.task} != fixture task_id {fixture['task_id']}", file=sys.stderr)
        return 2
    date = utc_now().strftime("%Y-%m-%d")
    rows_path = cfg.rows or f"experiments/ptr-engine/measure/rows-longrun-{date}.jsonl"
    run_base = cfg.run_id or f"longrun-{date}T{utc_now().strftime('%H%M%S')}Z"
    # E2's cell dimension: one cell per (arm, rep, compaction interval).  A single
    # interval (the default) reproduces the pre-change cell list exactly.
    try:
        intervals = compact_intervals(cfg)
    except ValueError as exc:
        print("COMPACT-EVERY USAGE: %s" % (exc,), file=sys.stderr)
        return 2
    cfg.compact_intervals = intervals
    # E3's cell dimension: the masking window.  Resolved once, before any manifest is
    # frozen, so the preview and the live cell read the same number.
    try:
        window = window_turns_setting(cfg)
    except ValueError as exc:
        print("WINDOW-TURNS USAGE: %s" % (exc,), file=sys.stderr)
        return 2
    cfg.window_turns = window
    cells = expand_cells(arms, cfg.reps, intervals)
    # WALL-KEY PREFLIGHT: resolve every requested arm's wall BEFORE a manifest is frozen or
    # a body is rendered, so a fixture that declares `wall_tokens_by_arm` but omits an arm
    # refuses here (exit 2) instead of running that arm at the top-level wall.
    try:
        for _arm, _rep, _iv in cells:
            wall_for_arm(fixture, _arm)
    except FixtureError as exc:
        print(f"FIXTURE ERROR: {exc}", file=sys.stderr)
        return 2

    if cfg.dry_run:
        for arm, rep, interval in cells:
            rid = f"dryrun-{fixture['task_id']}-{arm}-r{rep}"
            if interval != COMPACT_EVERY:
                rid += f"-c{interval}"
            if window != arm_cd.WINDOW_TURNS:
                rid += f"-w{window}"
            mid = cfg.manifest_path or os.path.join(cfg.manifest_dir, rid + ".json")
            # the manifest freezes the wall the CELL runs at: per arm, never the top-level
            doc = build_manifest(cfg, fixture_for_arm(fixture, arm), arm, rep, rid, rows_path)
            try:
                data, msha = write_manifest(mid, doc)
            except OSError as exc:
                print(f"MANIFEST ABORT: cannot write {mid}: {type(exc).__name__}: {exc}",
                      file=sys.stderr)
                print("MANIFEST ABORT: dry-run stopped before printing any prompt or touching the "
                      "network (Consonance: no frozen manifest, no result).", file=sys.stderr)
                return 3
            print(f"manifest[{arm} r{rep}]: {mid} ({len(data)} B) sha256={msha}")
        print(f"\nDRY-RUN task={fixture['task_id']} N={fixture['N']} fixture={fixture['_path']} "
              f"sha256={fixture['_sha256']}")
        print("(offline: zero requests; exact request bodies under state/previews/)")
        print("\nFIRST THREE REQUEST BODIES PER ARM")
        return run_dry(cfg, fixture, cells, root=cfg.preview_root)

    # CLAIM-ROW-STAMP: ONE parse of the claim decision, BEFORE the first row is
    # written and before any request. The resolved record is threaded on cfg and
    # read by make_row -> claim_mode.row_fields(), so every row (turn-initial, turn,
    # tool-followup, refusal, failure) carries the same claim. No second parser.
    try:
        cfg.claim = claim_mode.resolve_claim(cfg.claim_mode)
    except claim_mode.ClaimRefusal as exc:
        if _scratch_rows(rows_path):
            # A caller-managed row target under the OS temp dir is a diagnostic,
            # not the analysis corpus: it may run, stamped non-comparable.
            cfg.claim = claim_mode.ClaimRecord(claim_mode.MODE_SMOKE,
                                               claim_mode.CLAIM_NONE, False)
            print("CLAIM: no --claim-mode and rows=%s is outside the analysis "
                  "corpus; stamping claim=none (non-comparable)" % rows_path,
                  file=sys.stderr)
        else:
            print("%s" % (exc,), file=sys.stderr)
            print("CLAIM REFUSED (exit %d): no row was written and no request was "
                  "sent" % exc.code, file=sys.stderr)
            return exc.code
    # G3 PREREG GATE: the cell's own n must support the claim it declares, and the
    # decision is made BEFORE the first request -- same shape as the cap gate: the
    # gate's own text, its own code (12), no row written, no request sent.
    rc = enforce_prereg_gate(cfg, fixture)
    if rc != 0:
        return rc
    print(f"rows: {rows_path}  run_id base: {run_base}")
    print(f"FIXTURE: {fixture['_path']}  task_id={fixture['task_id']}  sha256={fixture['_sha256']}")
    for arm, rep, interval in cells:
        rid = f"{run_base}-{arm}-r{rep}"
        if interval != COMPACT_EVERY:
            rid += f"-c{interval}"
        if window != arm_cd.WINDOW_TURNS:
            rid += f"-w{window}"
        rc = run_cell(cfg, fixture, arm, rep, rid, rows_path, compact_every=interval,
                      window_turns=window)
        if rc != 0:
            return rc
    return report_run(rows_path, run_base, cfg, smoke=bool(cfg.smoke))


if __name__ == "__main__":
    sys.exit(main())
