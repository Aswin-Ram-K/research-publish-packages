#!/usr/bin/env python3
"""analyze_chain.py - classify the TX-05C chain breaks by cause.

A chain break is evidence about the fold ONLY when the value was absent from the prompt
at the carry turn.  When it was present, the break is a model error and is reported as
such -- it is not the signal.  That distinction is the whole reason this tool exists:
without it, "the fold broke the chain" and "the model answered wrongly earlier" are the
same number.

Classes per (arm, rep, pair):
  ok                  the carry answer is right
  lost_then_failed    wrong, and expected_present is False  -> the fold's fault (signal)
  present_then_failed wrong, and expected_present is True   -> model error (not signal)
  unclassified        wrong, and expected_present is null   -> never counted as signal

Zero requests: reads row files and the fixture only.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE = os.path.dirname(LONGRUN)
REPO = os.path.dirname(os.path.dirname(ENGINE))
for _p in (LONGRUN, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_longrun as R  # noqa: E402

ARMS = ("masking-no-fetch", "spcc", "pinned", "bounded-context-fetch")


def load_rows(pattern: str) -> list[dict]:
    rows = []
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows


def _row_at(rows: list[dict], arm: str, rep: int, turn: int) -> dict | None:
    for r in rows:
        if r.get("arm") != arm or int(r.get("rep", -1)) != rep:
            continue
        if int(r.get("turn", -1)) != turn:
            continue
        if r.get("checkpoint"):
            return r
    return None


def _is_fetch(row: dict) -> bool:
    return row.get("kind") == "tool-followup" or row.get("fetch_followup") is True


def _present(row: dict, fixture: dict, arm: str, rep: int, turn: int,
             rows_path: str, workdir: str) -> tuple[bool | None, str]:
    """(present, source).  Never defaults to True: an unknown is null."""
    val = row.get("expected_present")
    if isinstance(val, bool):
        return val, row.get("expected_present_source") or "row"
    expected = row.get("expected")
    if expected is None:
        return None, "no-expected"
    try:
        import prompt_at_turn as PAT
        settled = PAT.load_settled(rows_path)
        got = PAT.drive(fixture, settled, arm, rep, turn, workdir)
        present, source = R.expected_value_in_prompt(got["prompt"], expected)
        return present, f"recomputed:{source}"
    except Exception as exc:  # noqa: BLE001 - a failed recompute is an unknown, not a True
        return None, f"recompute_failed:{type(exc).__name__}"


def analyse(rows: list[dict], fixture: dict, rows_path: str, workdir: str) -> dict:
    chain = fixture.get("chain") or {}
    pairs = chain.get("pairs") or []
    arms = sorted({r.get("arm") for r in rows if r.get("arm")})
    reps = sorted({int(r.get("rep", 1)) for r in rows})
    out = {"fixture_sha256": fixture.get("_sha256"), "chain": {
        "fold_turn": chain.get("fold_turn"),
        "projected_tokens_at_fold": chain.get("projected_tokens_at_fold"),
        "window_turns": chain.get("window_turns"),
    }, "arms": {}}

    for arm in arms:
        per_pair = []
        counts = {"ok": 0, "lost_then_failed": 0, "present_then_failed": 0,
                  "unclassified": 0}
        refetch = 0
        compactions = 0
        for rep in reps:
            for pair in pairs:
                rt, ut = int(pair["ref_turn"]), int(pair["use_turn"])
                ref_row = _row_at(rows, arm, rep, rt)
                use_row = _row_at(rows, arm, rep, ut)
                if use_row is None:
                    per_pair.append({"rep": rep, "ref_turn": rt, "use_turn": ut,
                                     "class": "missing_row"})
                    continue
                present, source = _present(use_row, fixture, arm, rep, ut,
                                           rows_path, workdir)
                ok = bool(use_row.get("answer_verified"))
                if ok:
                    cls = "ok"
                elif present is False:
                    cls = "lost_then_failed"
                elif present is True:
                    cls = "present_then_failed"
                else:
                    cls = "unclassified"
                counts[cls] = counts.get(cls, 0) + 1
                refetch += sum(1 for r in rows
                               if r.get("arm") == arm and int(r.get("rep", -1)) == rep
                               and rt < int(r.get("turn", -1)) <= ut and _is_fetch(r))
                compactions = max(compactions, int(use_row.get("compactions") or 0))
                masked = max(int(r.get("masked_rows") or 0) for r in rows
                             if r.get("arm") == arm and int(r.get("rep", -1)) == rep)
                per_pair.append({
                    "rep": rep, "ref_turn": rt, "use_turn": ut,
                    "ref_ok": bool((ref_row or {}).get("answer_verified")),
                    "expected": use_row.get("expected"),
                    "answer": use_row.get("answer_value"),
                    "expected_present": present,
                    "expected_present_source": source,
                    "class": cls,
                })
        out["arms"][arm] = {"pairs": per_pair, "counts": counts,
                            "refetch_count": refetch, "compactions": compactions,
                            "masked_rows": masked,
                            "fold_events": compactions if compactions else masked}

    out["verdict"] = verdict(out["arms"])
    return out


def verdict(arms: dict) -> dict:
    def total(key):
        return sum(a["counts"].get(key, 0) for a in arms.values())

    lost, present = total("lost_then_failed"), total("present_then_failed")
    unclassified = total("unclassified")
    void = [a for a, v in arms.items() if v.get("fold_events", 0) == 0]
    fired = []
    if lost == 0:
        fired.append("falsifier_1_instrument_failure")
    if present > lost:
        fired.append("falsifier_2_null_model_error")
    pin = arms.get("pinned", {}).get("counts", {}).get("lost_then_failed")
    bcf = arms.get("bounded-context-fetch", {}).get("counts", {}).get("lost_then_failed")
    if pin is not None and bcf is not None and pin >= bcf:
        fired.append("falsifier_3_pin_premise_fails")
    m_ref = arms.get("masking-no-fetch", {}).get("refetch_count")
    p_ref = arms.get("pinned", {}).get("refetch_count")
    if m_ref is not None and p_ref is not None and m_ref == p_ref:
        fired.append("falsifier_4_recovery_not_paid")
    return {
        "lost_then_failed": lost,
        "present_then_failed": present,
        "unclassified": unclassified,
        "void_arms_no_fold": void,
        "fired": fired,
        "instrument_ok": not fired and not void and unclassified == 0,
    }


def table(result: dict) -> list[str]:
    lines = ["arm                     ok  lost  present  unclass  refetch  compactions"]
    for arm, v in sorted(result["arms"].items()):
        c = v["counts"]
        lines.append(f"{arm:<22} {c.get('ok', 0):>3} {c.get('lost_then_failed', 0):>5} "
                     f"{c.get('present_then_failed', 0):>8} {c.get('unclassified', 0):>8} "
                     f"{v['refetch_count']:>8} {v['compactions']:>12}")
    v = result["verdict"]
    lines.append("")
    lines.append(f"verdict: instrument_ok={v['instrument_ok']} fired={v['fired'] or 'none'} "
                 f"void_arms={v['void_arms_no_fold'] or 'none'}")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--rows", required=True, help="glob of row files")
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--workdir", default=None, help="scratch dir for prompt recompute")
    args = ap.parse_args(argv)

    fixture = R.load_fixture(args.fixture)
    rows = load_rows(args.rows)
    if not rows:
        print(f"no rows matched {args.rows}")
        return 2
    workdir = args.workdir or os.path.join(REPO, "state", "chain-recompute")
    os.makedirs(workdir, exist_ok=True)
    result = analyse(rows, fixture, args.rows, workdir)
    for line in table(result):
        print(line)
    if args.out:
        path = args.out if os.path.isabs(args.out) else os.path.join(REPO, args.out)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print(f"wrote {args.out}")
    return 0 if result["verdict"]["instrument_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
