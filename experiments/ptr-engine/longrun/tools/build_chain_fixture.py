#!/usr/bin/env python3
"""build_chain_fixture.py - TX-05C: a pointer-only chain reference across a fold.

The instrument this fixture exists for: a value is learned at turn *j*, the arm folds
the journal at ``chain.fold_turn``, and a later turn asks for a *different* value that
was defined beside it, naming only the step ("using the symbol you identified at step
j -- do not restate it").  The value is never in the question, so recovering it
requires the journal; the arms then differ by construction.

Why the second value and not the first: ``duplicate_expected`` forbids the same
``expected`` twice, and the reference checkpoint already grades the base constant.  The
carry checkpoint grades the override that sits in the same body, so both are learned at
the same turn and only the carry one is asked after the fold.

``window_tokens`` is 4096, not TX-04S's 65536.  ``PinnedArmState`` folds at
``FOLD_AT_FRACTION * window_tokens`` (arm_cd.py:722-728), so 4096 puts the fold at
~3028 tokens, which a 100-turn transcript crosses.  At 65536 the fold never fires --
that is why the E3 cell recorded ``compactions 0, evicted 0``.

Deterministic: no clock, no randomness, no network.  Re-running produces identical
bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE = os.path.dirname(LONGRUN)
REPO = os.path.dirname(os.path.dirname(ENGINE))
for _p in (LONGRUN, os.path.join(ENGINE, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arm_cd  # noqa: E402
import check_pointer_fixtures as CPF  # noqa: E402
import grade_v5  # noqa: E402
import run_longrun as R  # noqa: E402

OUT = "experiments/ptr-engine/longrun/tasks-v7/TX-05C.v1.json"
TASK_ID = "TX-05C"
FIXTURE_VERSION = "TX-05C.v1"
N_TURNS = 100
WINDOW_TOKENS = 4096
WINDOW_TURNS = 20          # the masking arm's --window-turns for this cell
BYTES_PER_TOKEN = 4.0914
SOURCE_FILE = "experiments/ptr-engine/ptr_engine/tx05_constants.py"

# pair k: base constant and the override defined in the same body
PAIRS = (
    ("SYM_01", 4011, 4017),
    ("SYM_02", 4021, 4027),
    ("SYM_03", 4031, 4037),
    ("SYM_04", 4041, 4047),
    ("SYM_05", 4051, 4057),
    ("SYM_06", 4061, 4067),
)
DECOYS = (5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008)

def system_prompt(task_id: str) -> str:
    return (
        f"You are a long-horizon coding agent working on {task_id}. Work only from tool "
        "outputs; never restate a fact you did not read.\n\n"
        "TOOLS: you have one tool, `fetch(ref)`. The WORKING SET INDEX lists every "
        "retrievable body as `doc-<name>@r<rev>`. When a value you need is not visible "
        "in the current context, fetch its ref instead of answering NONE. A value you "
        "read earlier may have been folded out of the transcript; if so, fetch it "
        "again.\n\n"
        "ANSWER BUDGET: answer with exactly one of these forms, on one line:\n"
        "  ANSWER: NUM <integer>\n"
        "  ANSWER: CALL <callee>(<kw>=<value>, ...)\n"
        "  ANSWER: NONE\n"
        "  ANSWER: TEXT <one line of prose>\n"
    )


def _abs(rel: str) -> str:
    return rel if os.path.isabs(rel) else os.path.join(REPO, rel)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


# ------------------------------------------------------------------ documents
def chain_body(symbol: str, base: int, override: int) -> str:
    return (
        f"# {symbol.lower()}_module.py\n"
        f"{symbol} = {base}\n"
        f"{symbol}_LIMIT = {base + 2}\n"
        f"\n"
        f"def use_{symbol.lower()}():\n"
        f"    # the caller rebinds the module constant for this path\n"
        f"    {symbol} = {override}\n"
        f"    return {symbol}\n"
    )


def filler_body(n: int) -> str:
    a = DECOYS[n % len(DECOYS)]
    b = DECOYS[(n + 3) % len(DECOYS)]
    return (
        f"# filler_{n:02d}.py\n"
        f"# unrelated working set, kept large enough that the transcript crosses the\n"
        f"# fold threshold before the first carry checkpoint.\n"
        f"FILLER_{n:02d}_A = {a}\n"
        f"FILLER_{n:02d}_B = {b}\n"
        f"\n"
        f"def helper_{n:02d}(value):\n"
        f"    \"\"\"Return the value unchanged; exists to give the body real shape.\"\"\"\n"
        f"    if value is None:\n"
        f"        return {a}\n"
        f"    return value\n"
        f"\n"
        f"def helper_{n:02d}_twice(value):\n"
        f"    return helper_{n:02d}(helper_{n:02d}(value))\n"
    )


def documents() -> list[dict]:
    docs = []
    for k, (symbol, base, override) in enumerate(PAIRS, start=1):
        docs.append({
            "doc_id": f"doc-chain-{k:02d}",
            "revisions": [{"revision": 1, "value": chain_body(symbol, base, override),
                           "live_from_turn": 1}],
            "revoked": False,
            "revoked_at_turn": None,
            "scope": "granted",
        })
    for n in range(1, 9):
        docs.append({
            "doc_id": f"doc-filler-{n:02d}",
            "revisions": [{"revision": 1, "value": filler_body(n), "live_from_turn": 1}],
            "revoked": False,
            "revoked_at_turn": None,
            "scope": "granted",
        })
    docs.append({
        "doc_id": "doc-revoked",
        "revisions": [{"revision": 1, "value": "# revoked.py\nOLD_FLAG = 6001\n",
                       "live_from_turn": 1}],
        "revoked": True,
        "revoked_at_turn": 5,
        "scope": "granted",
    })
    docs.append({
        "doc_id": "doc-ungranted",
        "revisions": [{"revision": 1, "value": "# ungranted.py\nSECRET_FLAG = 6002\n",
                       "live_from_turn": 1}],
        "revoked": False,
        "revoked_at_turn": None,
        "scope": "ungranted",
    })
    docs.append({
        "doc_id": "doc-multirev",
        "revisions": [
            {"revision": 1, "value": "# multirev.py\nMODE = 6003\n", "live_from_turn": 1},
            {"revision": 2, "value": "# multirev.py\nMODE = 6004\n", "live_from_turn": 50},
        ],
        "revoked": False,
        "revoked_at_turn": None,
        "scope": "granted",
    })
    return docs


# ------------------------------------------------------------------ schedule
def _turn_text(t: int, turn: dict) -> str:
    """The text one turn contributes to the transcript (question + tool output)."""
    parts = [R.turn_user(t, turn)]
    for to in turn.get("tool_outputs") or []:
        parts.append(f"TOOL_OUTPUT ({to['doc_id']}@{to['revision']}): {to['body']}")
    return "\n".join(parts)


def projected_fold_turn(turns: list[dict]) -> tuple[int, int]:
    """(fold_turn, tokens_at_fold) from the cumulative transcript, zero requests.

    The pinned arm folds when the prompt exceeds ``FOLD_AT_FRACTION * window_tokens``;
    the transcript is the dominant term, so the cumulative turn text is the projection.
    """
    threshold = arm_cd.FOLD_AT_FRACTION * WINDOW_TOKENS
    acc = 0
    for t in range(1, len(turns) + 1):
        acc += arm_cd._estimate_tokens(_turn_text(t, turns[t - 1]))
        if acc > threshold:
            return t, acc
    return len(turns), acc


def schedule() -> tuple[list[dict], int, int]:
    """Turns, fold turn, and the tokens at that fold."""
    turns = []
    for t in range(1, N_TURNS + 1):
        turns.append({"turn": t, "kind": "work", "question": f"Work turn {t}.",
                      "tool_outputs": []})

    # reference turns: before the fold, spaced; carry turns: after fold + mask window
    ref_turns = [3, 5, 7, 9, 11, 13]
    use_turns = [36, 46, 56, 66, 76, 86]

    # one delivery per turn: chain docs at the reference turns, fillers elsewhere.
    # Deliveries are assigned BEFORE the projection: the fold is a property of the
    # transcript, and a projection over bare questions would never cross it.
    chain_at = {rt: f"doc-chain-{k:02d}" for k, rt in enumerate(ref_turns, start=1)}
    filler_cycle = [f"doc-filler-{n:02d}" for n in range(1, 9)]
    doc_map = {d["doc_id"]: d for d in documents()}
    filler_i = 0
    for t in range(1, N_TURNS + 1):
        turn = turns[t - 1]
        if t in chain_at:
            did, rev = chain_at[t], 1
        elif t == 5:
            did, rev = "doc-revoked", 1
        elif t == 7:
            did, rev = "doc-ungranted", 1
        elif t == 50:
            did, rev = "doc-multirev", 2
        else:
            did = filler_cycle[filler_i % len(filler_cycle)]
            filler_i += 1
            rev = 1
        value = next(r["value"] for r in doc_map[did]["revisions"] if r["revision"] == rev)
        turn["tool_outputs"] = [{"doc_id": did, "revision": rev, "body": value}]

    fold_turn, tokens_at_fold = projected_fold_turn(turns)
    if not (max(ref_turns) < fold_turn < min(use_turns)):
        raise SystemExit(
            f"fold_turn {fold_turn} does not sit between ref turns {ref_turns} and "
            f"carry turns {use_turns}; adjust body sizes")
    if min(use_turns) - WINDOW_TURNS <= max(ref_turns):
        raise SystemExit("masking window does not cover the reference turns")
    return turns, fold_turn, tokens_at_fold


# ------------------------------------------------------------------ checkpoints
def pointer_text(ref_turn: int) -> str:
    return (f"Using the symbol you identified at step {ref_turn} — do not restate it — "
            f"find the caller that overrides it.")


def checkpoints(turns: list[dict], ref_turns: list[int], use_turns: list[int]) -> list[dict]:
    cps = []
    for k, ((symbol, base, override), rt, ut) in enumerate(
            zip(PAIRS, ref_turns, use_turns), start=1):
        doc = f"doc-chain-{k:02d}"
        ref_q = f"What is the value of {symbol}?"
        turns[rt - 1]["question"] = ref_q
        cps.append({
            "id": f"cp-{k:02d}-ref",
            "turn": rt,
            "question": ref_q,
            "expected": str(base),
            "answer_form": f"ANSWER: NUM {base}",
            "answer_spec": {"kind": "NUM",
                            "derive": {"file": SOURCE_FILE, "rule": "constant_value",
                                       "symbol": symbol}},
            "ground_truth": {"doc": doc, "revision": 1, "value": str(base)},
            "stale_value": str(base + 1),
            "fact_id": f"fact-{k:02d}",
            "fact_introduction_turn": rt,
            "distance": 0,
        })
        carry_q = pointer_text(rt)
        turns[ut - 1]["question"] = carry_q
        cps.append({
            "id": f"cp-{k:02d}-carry",
            "turn": ut,
            "question": carry_q,
            "expected": str(override),
            "answer_form": f"ANSWER: NUM {override}",
            "answer_spec": {"kind": "NUM",
                            "derive": {"file": SOURCE_FILE, "rule": "constant_value",
                                       "symbol": f"{symbol}_OVERRIDE"}},
            "ground_truth": {"doc": doc, "revision": 1, "value": str(override)},
            "stale_value": str(override + 1),
            "fact_id": f"fact-{k:02d}-carry",
            "fact_introduction_turn": rt,
            "distance": ut - rt,
        })
    return cps


# ------------------------------------------------------------------ fixture
def build(task_id: str = TASK_ID, version: str = FIXTURE_VERSION) -> dict:
    turns, fold_turn, tokens_at_fold = schedule()
    ref_turns = [3, 5, 7, 9, 11, 13]
    use_turns = [36, 46, 56, 66, 76, 86]
    cps = checkpoints(turns, ref_turns, use_turns)
    docs = documents()
    prompt = system_prompt(task_id)
    chars = len(prompt) + sum(len(_turn_text(t["turn"], t)) for t in turns)
    fixture = {
        "schema": "consonance.longrun-fixture/2",
        "fixture_version": version,
        "task_id": task_id,
        "generation": "gen-7",
        "N": N_TURNS,
        "window_tokens": WINDOW_TOKENS,
        "bytes_per_token": BYTES_PER_TOKEN,
        "wall_tokens": round(chars / BYTES_PER_TOKEN),
        "wall_tokens_basis": {
            "basis": "measured",
            "note": "chars/bytes_per_token over the rendered transcript; same recipe as TX-04S",
        },
        "fetch_budget_tokens": 1024,
        "fetch_budget_tokens_basis": "arm D bounded-recoverable fetch channel per-fetch body cap 1024 tokens",
        "system_prompt": prompt,
        "items": [{"id": "item-1", "body": "unrelated working set placeholder"}],
        "documents": docs,
        "revision_schedule": [
            {"doc": "doc-revoked", "new_revision": None, "note": "doc-revoked revoked", "turn": 5},
            {"doc": "doc-multirev", "new_revision": 2, "note": "doc-multirev r2 live", "turn": 50},
        ],
        "lease_reopen_turns": [23],
        "fetch_scenarios": [
            {"ref": "doc-chain-01@r1", "expected_outcome": "OK"},
            {"ref": "doc-missing@r1", "expected_outcome": "NOT_FOUND"},
            {"ref": "doc-revoked@r1", "expected_outcome": "STALE_OR_REVOKED"},
            {"ref": "doc-ungranted@r1", "expected_outcome": "SCOPE_UNGRANTED"},
        ],
        "outcomes_reachable": ["OK", "NOT_FOUND", "STALE_OR_REVOKED", "SCOPE_UNGRANTED"],
        "turns": turns,
        "checkpoints": cps,
        "checkpoint_turns": sorted(int(c["turn"]) for c in cps),
        "facts": [{"doc_id": f"doc-chain-{k:02d}", "fact_id": f"fact-{k:02d}",
                   "introduction_turn": rt}
                  for k, rt in enumerate(ref_turns, start=1)],
        "chain": {
            "rule": "pointer-only",
            "fold_turn": fold_turn,
            "projected_tokens_at_fold": tokens_at_fold,
            "window_turns": WINDOW_TURNS,
            "pairs": [
                {"ref_turn": rt, "ref_checkpoint": f"cp-{k:02d}-ref", "use_turn": ut,
                 "carry_checkpoint": f"cp-{k:02d}-carry", "pointer_text": pointer_text(rt)}
                for k, (rt, ut) in enumerate(zip(ref_turns, use_turns), start=1)
            ],
        },
    }
    return fixture


def serialise(fixture: dict) -> bytes:
    return json.dumps(fixture, indent=1, sort_keys=True).encode("utf-8")


def verify(fixture: dict) -> list[str]:
    errs = list(CPF.validate(fixture))
    # the truth derivation must agree with every documented expected value
    try:
        truth = grade_v5.derive_truth(fixture)
    except SystemExit as exc:
        errs.append(f"derive_truth: {exc}")
        truth = []
    by_turn = {int(c["turn"]): c for c in truth}
    for cp in fixture["checkpoints"]:
        cell = by_turn.get(int(cp["turn"]))
        if cell is None:
            errs.append(f"checkpoint {cp['id']} has no derived truth")
            continue
        if str(cell.get("expected")) != str(cp["expected"]):
            errs.append(f"checkpoint {cp['id']} derived {cell.get('expected')!r} != "
                        f"documented {cp['expected']!r}")
    return errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--task-id", default=TASK_ID)
    ap.add_argument("--version", default=FIXTURE_VERSION)
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    args = ap.parse_args(argv)

    fixture = build(task_id=args.task_id, version=args.version)
    errs = verify(fixture)
    if errs:
        print(f"{args.task_id}: FAIL")
        for e in errs:
            print(f"  - {e}")
        return 1
    raw = serialise(fixture)
    if args.check:
        print(f"{args.task_id}: OK (not written)")
        return 0
    path = _abs(args.out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(raw)
    print(f"{args.task_id}: OK -> {args.out}")
    print(f"  sha256 {_sha256(raw)}")
    print(f"  N={fixture['N']} checkpoints={len(fixture['checkpoints'])} "
          f"fold_turn={fixture['chain']['fold_turn']} "
          f"tokens_at_fold={fixture['chain']['projected_tokens_at_fold']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
