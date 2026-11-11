#!/usr/bin/env python3
"""build_mismatch_fixture.py - deterministic sibling of TX-04 with delivery/ask MISMATCHES.

WHY THIS EXISTS. U-SPCC-67 diagnosed the E3 masking-arm gap as ANSWER-SLOT BINDING: the
masking arm's flat transcript replays blocks as

    QUESTION (Tt): ... / TOOL OUTPUTS: / TOOL_OUTPUT (doc@rev): body / ANSWER (Tt): value

so an answer inherits its value from the block immediately above it.  On the 5 TX-04
checkpoint turns whose prompt delivers a body for a DIFFERENT document than the one asked,
the masking arm echoed the delivered body's value on 4 of 5 (rows-e3-retain-2026-11-10).
TX-04 carries only 5 such turns, and each one is incidental: its delivery schedule is
built for position/eviction, not for binding.  This builder emits `TX-04S`, a sibling that
keeps TX-04's document/value universe, question grammar, distances, system prompt and
contract, and pushes the delivery/ask mismatch count from 5 to 14 so a live run can test
the binding hypothesis with contrast instead of anecdote.

THE SCHEDULE (all of it a function of the constants below; nothing is random):

  * doc-fact-01..10 are introduced at turns 1..10, one delivery each.  Docs 01-05 carry
    checkpoints at distances (2, 8, 20, 32); docs 06-10 at (8, 20, 32, 64), VAL_A..VAL_D
    in that order.  The two groups are what keeps all 40 checkpoint turns distinct:
    within a group every doc uses the same distance set (distinct intros => distinct
    turns), and across groups the distance differences (<= 62 when equal, else 6/12/18/
    24/30/44/56/62) cannot be formed by the intro gaps (1..9), so no cross-group turn
    collides either.  The builder asserts the uniqueness rather than trusting the algebra.
  * doc-fact-11 is the SAME-DOCUMENT control: delivered at turn 19 and asked at turn 19
    (distance 0), so the block immediately above the answer slot is a delivery of the
    ASKED document.  A predictor that fires on "a delivery sits above the slot" is wrong
    here; only "a delivery of a DIFFERENT document" is the binding condition.
  * doc-fact-12 is the DECOY: delivered verbatim on 7 checkpoint turns (13, 17, 24, 29,
    36, 41, 73), never checkpointed itself, so none of its values is an expected answer
    and it can be re-delivered as often as the design likes without leaking a truth.
  * 7 further mismatch turns are inherited from the schedule itself: turns 3-7, 9 and 10
    are both a document's introduction turn and an earlier document's checkpoint, which
    is exactly TX-04's own T10/T12/T30/T31/T39 shape.

  14 mismatch turns = 7 schedule-inherent + 7 decoy.  The remaining 26 checkpoints have no
  delivery above the slot, and 1 has the asked document's own body.

EVERYTHING ELSE IS INHERITED from `tasks-v7/TX-04.v1.json` (read-only): documents,
revision_schedule, fetch_scenarios, outcomes_reachable, system_prompt, items,
window_tokens, bytes_per_token, fetch budget and `lease_reopen_turns`.  The wall is
re-derived from the new fixture's own bytes with TX-04's own formula
(`round((sum of question chars + tool-output body chars + system_prompt chars) /
bytes_per_token)`), so the declared wall stays traceable instead of copied.

VERIFICATION BEFORE WRITING.  The builder refuses to leave a file it cannot vouch for:
it loads the result through `run_longrun.load_fixture` (the single schema gate), runs
`check_pointer_fixtures.validate` (gen-7 domain rules), cross-checks every `expected`
against `grade_v5.derive_truth`'s AST derivation, and re-renders the masking arm's prompt
for every checkpoint with the REAL `run_longrun.Planner` to confirm the predictor's own
block-above rule classifies exactly the 14 declared mismatch turns as BOUND and every
other checkpoint as FREE.  A disagreement deletes the emitted file and exits non-zero.

    python3 experiments/ptr-engine/longrun/tools/build_mismatch_fixture.py
    python3 experiments/ptr-engine/longrun/tools/build_mismatch_fixture.py --check

Offline.  Stdlib only.  Writes exactly one file (and nothing with --check).
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

import check_pointer_fixtures as CPF  # noqa: E402
import grade_v5  # noqa: E402
import predict_answer_slot as PAS  # noqa: E402
import run_longrun as R  # noqa: E402

SOURCE = "experiments/ptr-engine/longrun/tasks-v7/TX-04.v1.json"
OUT = "experiments/ptr-engine/longrun/tasks-v7/TX-04S.v1.json"
TASK_ID = "TX-04S"
FIXTURE_VERSION = "TX-04S.v1"
N_TURNS = 100

SYMBOLS = ("VAL_A", "VAL_B", "VAL_C", "VAL_D")
DISTANCES_GROUP_A = (2, 8, 20, 32)   # doc-fact-01..05
DISTANCES_GROUP_B = (8, 20, 32, 64)  # doc-fact-06..10
GROUP_SPLIT = 5

CONTROL_DOC = "doc-fact-11"
CONTROL_TURN = 19
DECOY_DOC = "doc-fact-12"
DECOY_TURNS = (13, 17, 24, 29, 36, 41, 73)

ARM = "masking-no-fetch"
# The cell parameters the classification is checked at: the E3 cell's own (nothing is
# masked inside 100 turns).  The acceptance dry run uses the runner's defaults instead;
# that changes which PRIOR bodies survive, never which body sits above the slot.
WINDOW_TURNS = 200
COMPACT_EVERY = 200
MIN_MISMATCH = 12


def _abs(rel: str) -> str:
    return rel if os.path.isabs(rel) else os.path.join(REPO, rel)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


# ------------------------------------------------------------------ the schedule
def subject_docs() -> list[str]:
    return ["doc-fact-%02d" % n for n in range(1, 2 * GROUP_SPLIT + 1)]


def schedule() -> list[dict]:
    """Every checkpoint, as (doc, symbol, intro turn, distance, turn) in turn order."""
    out: list[dict] = []
    for idx, doc in enumerate(subject_docs()):
        dists = DISTANCES_GROUP_A if idx < GROUP_SPLIT else DISTANCES_GROUP_B
        intro = idx + 1
        for symbol, dist in zip(SYMBOLS, dists):
            out.append({"doc": doc, "symbol": symbol, "intro": intro,
                        "distance": dist, "turn": intro + dist})
    out.append({"doc": CONTROL_DOC, "symbol": SYMBOLS[0], "intro": CONTROL_TURN,
                "distance": 0, "turn": CONTROL_TURN})
    out.sort(key=lambda c: c["turn"])
    turns = [c["turn"] for c in out]
    if len(set(turns)) != len(turns):
        dupes = sorted({t for t in turns if turns.count(t) > 1})
        raise SystemExit(f"schedule defect: duplicate checkpoint turns {dupes}")
    return out


def deliveries() -> dict[int, str]:
    """turn -> doc_id of the body that turn delivers (one delivery per turn)."""
    out: dict[int, str] = {}
    for idx, doc in enumerate(subject_docs()):
        out[idx + 1] = doc
    if CONTROL_TURN in out:
        raise SystemExit(f"schedule defect: control turn {CONTROL_TURN} already a delivery")
    out[CONTROL_TURN] = CONTROL_DOC
    for t in DECOY_TURNS:
        if t in out:
            raise SystemExit(f"schedule defect: decoy turn {t} already delivers {out[t]}")
        out[t] = DECOY_DOC
    return dict(sorted(out.items()))


def mismatch_turns(cps: list[dict], deliver: dict[int, str]) -> list[int]:
    """Checkpoint turns whose immediately-preceding delivery is a DIFFERENT document."""
    return [c["turn"] for c in cps
            if c["turn"] in deliver and deliver[c["turn"]] != c["doc"]]


# ------------------------------------------------------------------ the fixture
def _revision_body(documents: list[dict], doc_id: str, revision: int = 1) -> str:
    for doc in documents:
        if doc.get("doc_id") != doc_id:
            continue
        for rev in doc.get("revisions") or []:
            if int(rev.get("revision")) == revision:
                return str(rev.get("value"))
        raise SystemExit(f"{doc_id} has no revision {revision}")
    raise SystemExit(f"source fixture has no document {doc_id!r}")


def _constant_value(body: str, symbol: str) -> int:
    for line in body.splitlines():
        key, _, value = line.partition("=")
        if key.strip() == symbol:
            return int(value.strip())
    raise SystemExit(f"body has no {symbol}: {body!r}")


def _wall_tokens(fixture: dict) -> int:
    chars = (len(fixture["system_prompt"])
             + sum(len(t["question"]) for t in fixture["turns"])
             + sum(len(to["body"]) for t in fixture["turns"]
                   for to in (t.get("tool_outputs") or [])))
    return round(chars / float(fixture["bytes_per_token"]))


def build(src_path: str = SOURCE) -> dict:
    with open(_abs(src_path), "rb") as fh:
        raw = fh.read()
    src = json.loads(raw)
    if src.get("task_id") == TASK_ID:
        raise SystemExit(f"{src_path} is already {TASK_ID}; the source must be TX-04")
    documents = src["documents"]
    cps = schedule()
    deliver = deliveries()
    body_of = {doc: _revision_body(documents, doc) for doc in set(deliver.values())}
    value_of = {doc: {sym: _constant_value(body, sym) for sym in SYMBOLS}
                for doc, body in body_of.items()}

    question_of = {c["turn"]: "What is %s of %s?" % (c["symbol"], c["doc"]) for c in cps}
    if len(question_of) != len(cps):
        raise SystemExit("schedule defect: two checkpoints share a turn")

    turns: list[dict] = []
    for t in range(1, N_TURNS + 1):
        turn = {"kind": "work", "question": question_of.get(t, "Work turn %d." % t),
                "turn": t}
        if t in deliver:
            doc = deliver[t]
            turn["tool_outputs"] = [{"body": body_of[doc], "doc_id": doc, "revision": 1}]
        turns.append(turn)

    checkpoints: list[dict] = []
    for c in cps:
        doc, symbol = c["doc"], c["symbol"]
        expected = value_of[doc][symbol]
        num = int(doc.rsplit("-", 1)[1])
        checkpoints.append({
            "answer_form": "ANSWER: NUM %d" % expected,
            "answer_spec": {
                "derive": {"file": "experiments/ptr-engine/ptr_engine/tx04_constants.py",
                           "rule": "constant_value",
                           "symbol": "F%02d_%s" % (num, symbol)},
                "kind": "NUM",
            },
            "distance": c["distance"],
            "expected": str(expected),
            "fact_id": "fact-%02d" % num,
            "fact_introduction_turn": c["intro"],
            "ground_truth": {"doc": doc, "revision": 1, "value": body_of[doc]},
            "id": "cp.%s.f%02d.d%d" % (TASK_ID, num, c["distance"]),
            "intro_turn": c["intro"],
            "introduction_turn": c["intro"],
            "match": "exact",
            "question": question_of[c["turn"]],
            "source": "tool_output:%s@r1" % doc,
            "stale_value": "stale-sentinel-value",
            "turn": c["turn"],
        })

    facts = []
    for idx, doc in enumerate(subject_docs()):
        facts.append({"doc_id": doc, "fact_id": "fact-%02d" % (idx + 1),
                      "introduction_turn": idx + 1})
    facts.append({"doc_id": CONTROL_DOC, "fact_id": "fact-11",
                  "introduction_turn": CONTROL_TURN})
    facts.append({"doc_id": DECOY_DOC, "fact_id": "fact-12",
                  "introduction_turn": min(DECOY_TURNS)})

    mism = mismatch_turns(cps, deliver)
    no_delivery = [c["turn"] for c in cps
                   if c["turn"] not in deliver]
    same_doc = [c["turn"] for c in cps
                if c["turn"] in deliver and deliver[c["turn"]] == c["doc"]]
    dist_counts: dict[str, int] = {}
    for c in cps:
        key = str(c["distance"])
        dist_counts[key] = dist_counts.get(key, 0) + 1

    fixture = {
        "schema": src["schema"],
        "task_id": TASK_ID,
        "generation": src["generation"],
        "N": N_TURNS,
        "turns": turns,
        "wall_tokens": None,          # replaced below, once the bytes exist
        "wall_tokens_basis": {
            "basis": "DERIVED_FROM_PT_OWN_BYTES",
            "note": ("round((sum of turn question chars + tool-output body chars + "
                     "system_prompt chars) / bytes_per_token); no model was run. TX-04's "
                     "own formula, recomputed for this fixture's schedule"),
        },
        "window_tokens": src["window_tokens"],
        "documents": documents,
        "revision_schedule": src["revision_schedule"],
        "checkpoints": checkpoints,
        "fetch_scenarios": src["fetch_scenarios"],
        "outcomes_reachable": src["outcomes_reachable"],
        "bytes_per_token": src["bytes_per_token"],
        "system_prompt": src["system_prompt"],
        "items": src["items"],
        "fetch_budget_tokens": src["fetch_budget_tokens"],
        "fetch_budget_tokens_basis": src["fetch_budget_tokens_basis"],
        "lease_reopen_turns": src.get("lease_reopen_turns") or [],
        "checkpoint_turns": sorted(c["turn"] for c in cps),
        "fixture_version": FIXTURE_VERSION,
        "sources": src.get("sources") or [],
        "facts": facts,
        "answer_slot_design": {
            "derived_from": {"path": SOURCE, "sha256": _sha256_bytes(raw)},
            "hypothesis": ("the E3 masking-arm gap is answer-slot binding: a checkpoint "
                           "whose prompt delivers a different document's body immediately "
                           "above the answer slot copies that body's value, whatever the "
                           "question asked"),
            "rule": ("BOUND iff the block immediately above the answer slot (after the "
                     "host checkpoint contract is stripped) is a TOOL_OUTPUT delivery of "
                     "a document other than the asked one and carries the asked symbol"),
            "checkpoints": len(cps),
            "distances": sorted({c["distance"] for c in cps}),
            "distribution": dict(sorted(dist_counts.items())),
            "schedule": ("doc-fact-01..10 introduced at turns 1..10, 4 checkpoints each "
                         "at distances 2/8/20/32 (docs 01-05) and 8/20/32/64 (docs 06-10); "
                         "doc-fact-11 is the same-document control at turn %d; doc-fact-12 "
                         "is the decoy delivered at turns %s"
                         % (CONTROL_TURN, list(DECOY_TURNS))),
            "mismatch_turns": mism,
            "mismatch_count": len(mism),
            "schedule_inherent_mismatch_turns": [t for t in mism if t not in DECOY_TURNS],
            "decoy_mismatch_turns": [t for t in mism if t in DECOY_TURNS],
            "same_document_control_turns": same_doc,
            "no_delivery_turns": no_delivery,
            "predicted_classes": {"BOUND": len(mism),
                                  "FREE": len(cps) - len(mism)},
            "inherited": ("documents, revision_schedule, fetch_scenarios, "
                          "outcomes_reachable, system_prompt, items, window_tokens, "
                          "bytes_per_token, fetch budget and lease_reopen_turns are "
                          "copied verbatim from %s; the turn plan, deliveries, "
                          "checkpoints, facts and checkpoint_turns are new" % SOURCE),
        },
    }
    fixture["wall_tokens"] = _wall_tokens(fixture)
    return fixture


def serialise(fixture: dict) -> bytes:
    """TX-04's own byte shape: indent 1, sorted keys, no trailing newline."""
    return json.dumps(fixture, indent=1, sort_keys=True).encode("utf-8")


# ------------------------------------------------------------------ verification
def render_prompts(fixture: dict, arm: str = ARM,
                   window_turns: int = WINDOW_TURNS,
                   compact_every: int = COMPACT_EVERY) -> dict[int, str]:
    """The exact prompt this arm would send at every turn, from the real Planner."""
    planner = R.Planner(arm, R.fixture_for_arm(fixture, arm), True,
                        compact_every=compact_every, window_turns=window_turns)
    prompts: dict[int, str] = {}
    for t in range(1, int(fixture["N"]) + 1):
        info = planner.build(t)
        prompts[t] = R.checkpoint_prompt(fixture, t, info["prompt"], arm)
        planner.record(t, "ANSWER: NUM 0")
    return prompts


def predicted_classes(fixture: dict, prompts: dict[int, str]) -> dict[int, dict]:
    out = {}
    for cp in fixture["checkpoints"]:
        t = int(cp["turn"])
        shape = PAS.answer_slot_shape(prompts[t], t)
        out[t] = PAS.classify(shape, cp)
    return out


def verify(fixture: dict, path: str) -> list[str]:
    """Every gate the fixture must pass.  Returns a list of failures (empty = green)."""
    errors: list[str] = []

    loaded = R.load_fixture(path)
    if loaded.get("task_id") != TASK_ID:
        errors.append(f"load_fixture task_id {loaded.get('task_id')!r} != {TASK_ID!r}")

    for err in CPF.validate(fixture):
        errors.append("validate: " + err)

    truth = grade_v5.derive_truth(grade_v5.load_fixture(path))
    derived = {str(cell["id"]): cell for cell in truth}
    for cp in fixture["checkpoints"]:
        cell = derived.get(str(cp["id"]))
        if cell is None:
            errors.append(f"derive_truth has no cell for {cp['id']}")
            continue
        if int(cell["expected"]) != int(cp["expected"]):
            errors.append(f"{cp['id']}: derived expected {cell['expected']!r} != "
                          f"fixture expected {cp['expected']!r}")
        if "derivation" not in cell:
            errors.append(f"{cp['id']}: derive_truth produced no derivation")

    design = fixture["answer_slot_design"]
    declared = list(design["mismatch_turns"])
    if len(declared) < MIN_MISMATCH:
        errors.append(f"mismatch turns {len(declared)} < {MIN_MISMATCH}")

    prompts = render_prompts(fixture)
    classes = predicted_classes(fixture, prompts)
    bound = sorted(t for t, c in classes.items() if c["prediction"] == "BOUND")
    if bound != sorted(declared):
        errors.append(f"predicted BOUND turns {bound} != declared mismatch turns "
                      f"{sorted(declared)}")
    for t, pred in sorted(classes.items()):
        if t in declared and pred["predicted_value"] is None:
            errors.append(f"T{t}: BOUND without a predicted value")
        if t not in declared and pred["prediction"] != "FREE":
            errors.append(f"T{t}: predicted {pred['prediction']} but no mismatched "
                          f"delivery is declared above it")
        if t in design["same_document_control_turns"] and pred["reason"] != "same_document":
            errors.append(f"T{t}: same-document control predicted "
                          f"{pred['reason']!r}, not 'same_document'")
        if t in design["no_delivery_turns"] and pred["reason"] != "no_delivery_above":
            errors.append(f"T{t}: expected 'no_delivery_above', got {pred['reason']!r}")
    return errors


# ------------------------------------------------------------------ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", default=SOURCE)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true",
                    help="rebuild in memory and compare with the file on disk; write nothing")
    args = ap.parse_args(argv)

    fixture = build(args.source)
    raw = serialise(fixture)
    out_abs = _abs(args.out)

    if args.check:
        if not os.path.exists(out_abs):
            print(f"MISSING: {args.out} — run the builder without --check")
            return 2
        with open(out_abs, "rb") as fh:
            on_disk = fh.read()
        if on_disk != raw:
            print(f"STALE: {args.out} differs from a fresh build "
                  f"(on disk {_sha256_bytes(on_disk)[:16]}, fresh {_sha256_bytes(raw)[:16]})")
            return 3
        errors = verify(fixture, out_abs)
        for err in errors:
            print("  - " + err)
        print(f"CHECK {args.out}: {'OK' if not errors else 'FAIL'} "
              f"sha256={_sha256_bytes(on_disk)}")
        return 0 if not errors else 1

    with open(out_abs, "wb") as fh:
        fh.write(raw)

    try:
        errors = verify(fixture, out_abs)
    except SystemExit as exc:                 # derive_truth refuses loudly
        errors = [f"verify raised: {exc}"]
    if errors:
        os.remove(out_abs)                    # never leave a file we cannot vouch for
        print(f"REFUSED: {args.out} failed verification and was removed", file=sys.stderr)
        for err in errors:
            print("  - " + err, file=sys.stderr)
        return 1

    design = fixture["answer_slot_design"]
    print(f"wrote {args.out} sha256={_sha256_bytes(raw)}")
    print(f"  task_id={TASK_ID} N={N_TURNS} checkpoints={len(fixture['checkpoints'])} "
          f"wall_tokens={fixture['wall_tokens']}")
    print(f"  distances={design['distribution']} ")
    print(f"  mismatch_turns={design['mismatch_count']} {design['mismatch_turns']}")
    print(f"    schedule-inherent={design['schedule_inherent_mismatch_turns']} "
          f"decoy={design['decoy_mismatch_turns']}")
    print(f"  same_document_control={design['same_document_control_turns']} "
          f"no_delivery={len(design['no_delivery_turns'])}")
    print(f"  predicted={design['predicted_classes']} "
          f"(re-rendered with run_longrun.Planner at window_turns={WINDOW_TURNS})")
    print("  gates: load_fixture OK, check_pointer_fixtures.validate OK, "
          "grade_v5.derive_truth OK, block-above classification OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
