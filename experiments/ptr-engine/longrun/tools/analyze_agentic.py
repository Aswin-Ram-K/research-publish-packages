#!/usr/bin/env python3
"""analyze_agentic.py - per-arm report and falsifiers for the stage-2 episode loop.

The stage-2 rows (`measure/rows-agentic-*.jsonl`) are one JSON object per request.  A
graded row carries `verified` and `expected_present`; the pair is what separates a fold
that destroyed a value from a model that simply answered wrongly:

  ok                  verified is true
  lost_then_failed    verified false, expected_present false  -> the fold's fault
  present_then_failed verified false, expected_present true   -> model error
  unclassified        verified false, expected_present null   -> never counted as a pass

`expected_present` is never defaulted: a null is "not evidence", not a success.

`refetch_count` is the recovery price: tool calls named `read_file` or `grep` made at or
after the first fold of an episode.  An episode that never folded contributes zero.

Two row shapes share a file.  A row carrying a `checkpoints` list is a per-episode row
(`task`, `arm`, `rep`, `solved`, `checkpoints`, `steps_used`, `requests`,
`refetch_count`, `compactions`, `evicted`, `billed_tokens`, `completion_tokens`); a row
carrying `step` is a per-request row.  The per-request block above is computed over the
per-request rows only; the episode block (`checkpoints_n`, `checkpoint_accuracy`,
`cost_units`, `mean_compactions`, ...) is computed over the per-episode rows only,
grouped by `(task, arm, rep)`.

An episode is VOID when no fold of any kind happened: `compactions == 0 and evicted == 0`.
`masking-no-fetch` folds by masking, so it records `compactions == 0` with `evicted > 0`
and is a live episode; `none` has neither and is void.  A void episode is not a data
point: it is excluded from every accuracy and cost number, and an arm whose episodes are
all void reports `void: true` with `cost_basis: "no_live_episodes"` instead of a number.
An 8-episode "solved %" resolves to roughly +-35 pp, so the table states that the solved
rate is NOT reported.

Five falsifiers, each printed with the numbers that fired it.  A fired falsifier is a
result, not an error: the process always exits 0.

Zero requests: reads row files only.
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

#: The five arms, in report order.  Declared here rather than imported: the bespoke
#: `agentic_contract` module lost the schema ruling and is being deleted.
ARMS = ("none", "masking-no-fetch", "pinned", "bounded-context-fetch", "compact")

#: What each arm DECLARES it does.  Voiding is judged against the declaration, not
#: against a single global rule: `none` declares no mechanism, so it can never fail
#: to fire one, and voiding it would delete the baseline every other arm is compared
#: against.
FOLD_MECHANISM = {
    "none": "none",
    "masking-no-fetch": "eviction",
    "pinned": "fold",
    "compact": "fold",
    "bounded-context-fetch": "fold",
}

REFETCH_TOOLS = ("read_file", "grep")

FALSIFIERS = (
    "instrument_failure",
    "null_model_error",
    "pin_premise_fails",
    "recovery_not_paid",
    "compaction_not_cheaper",
)


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


def _tri(value) -> bool | None:
    """Three-valued read of `expected_present`: True, False, or None (unknown)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    return None


def _num(row: dict, key: str) -> float:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def _step(row: dict) -> int:
    value = row.get("step")
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value


def _episode_key(row: dict) -> tuple:
    return (row.get("run_id"), row.get("arm"), row.get("task_id"), row.get("rep"))


def _is_episode_row(row: dict) -> bool:
    """A per-episode row carries a `checkpoints` list; a per-request row carries `step`."""
    return isinstance(row.get("checkpoints"), list)


def _void_reason(arm: str, row: dict) -> tuple[bool, str]:
    """(void, reason) for one episode under the arm's DECLARED mechanism.

    `none` declares no mechanism, so it can never fail to fire one: it is the
    baseline and is never void.  `masking-no-fetch` folds by eviction, so it is void
    only when nothing was evicted.  The fold arms are void only when no fold fired.
    """
    mechanism = FOLD_MECHANISM.get(arm, "fold")
    if mechanism == "none":
        return False, ""
    if mechanism == "eviction":
        if _num(row, "evicted") == 0:
            return True, "evicted_zero"
        return False, ""
    if _num(row, "compactions") == 0:
        return True, "compactions_zero"
    return False, ""


def _episode_report(rows: list[dict], arm: str) -> dict:
    """Per-episode block: void accounting, checkpoint accuracy, and cost.

    Grouped by `(task, rep)` inside the arm; a repeated key is one episode written twice,
    so the last row wins rather than being counted as a second episode.
    """
    groups: dict[tuple, dict] = {}
    for row in rows:
        groups[(row.get("task"), row.get("rep"))] = row

    void_episodes = 0
    reasons: set[str] = set()
    live: list[dict] = []
    for row in groups.values():
        is_void, reason = _void_reason(arm, row)
        if is_void:
            void_episodes += 1
            reasons.add(reason)
        else:
            live.append(row)

    checkpoints_n = 0
    checkpoints_ok = 0
    for row in live:
        for cp in row.get("checkpoints") or []:
            if not isinstance(cp, dict):
                continue
            checkpoints_n += 1
            if cp.get("ok"):
                checkpoints_ok += 1

    cost_units = None
    if live:
        cost_units = sum(_num(r, "billed_tokens") + 3.0 * _num(r, "completion_tokens")
                         for r in live)

    if not groups:
        void = True
        reasons.add("no_episode_rows")
    else:
        void = void_episodes == len(groups)
    if not groups:
        cost_basis = "no_episode_rows"
    elif void:
        cost_basis = "no_live_episodes"
    else:
        cost_basis = "billed_tokens_plus_3x_completion"

    return {
        "episode_rows": len(rows),
        "fold_mechanism": FOLD_MECHANISM.get(arm, "fold"),
        "void_episodes": void_episodes,
        "void_reasons": sorted(reasons),
        "checkpoints_n": checkpoints_n,
        "checkpoints_ok": checkpoints_ok,
        "checkpoint_accuracy": (checkpoints_ok / checkpoints_n) if checkpoints_n else None,
        "cost_units": cost_units,
        "cost_units_per_verified_success": (
            cost_units / checkpoints_ok
            if cost_units is not None and checkpoints_ok else None),
        "mean_refetch_count": (sum(_num(r, "refetch_count") for r in live) / len(live))
                              if live else None,
        "mean_compactions": (sum(_num(r, "compactions") for r in live) / len(live))
                            if live else None,
        "void": void,
        "cost_basis": cost_basis,
    }


def _tool_name(call) -> str | None:
    if isinstance(call, dict):
        return call.get("name")
    return None


def _first_fold_step(episode: list[dict]) -> int | None:
    steps = [_step(r) for r in episode if r.get("fold_event")]
    return min(steps) if steps else None


def _arm_order(arm: str) -> int:
    return ARMS.index(arm) if arm in ARMS else len(ARMS)


def _arm_report(rows: list[dict]) -> dict:
    episode_rows = [r for r in rows if _is_episode_row(r)]
    request_rows = [r for r in rows if not _is_episode_row(r)]

    episodes: dict[tuple, list[dict]] = {}
    for row in request_rows:
        episodes.setdefault(_episode_key(row), []).append(row)

    counts = {"ok": 0, "lost_then_failed": 0, "present_then_failed": 0,
              "unclassified": 0, "literal_disagreement": 0}
    graded = 0
    verified = 0
    for row in request_rows:
        if row.get("verified") is None:
            continue
        graded += 1
        # ``value_present`` is the literal test the instrument used to attribute with.
        # A disagreement is a checkpoint the old rule would have misattributed, so the
        # count is the size of the defect this run's presence rule repairs.
        if (row.get("value_present") is not None
                and _tri(row.get("value_present")) != _tri(row.get("expected_present"))):
            counts["literal_disagreement"] += 1
        if bool(row.get("verified")):
            verified += 1
            counts["ok"] += 1
            continue
        present = _tri(row.get("expected_present"))
        if present is False:
            counts["lost_then_failed"] += 1
        elif present is True:
            counts["present_then_failed"] += 1
        else:
            counts["unclassified"] += 1

    refetch = 0
    episodes_without_fold = 0
    for episode in episodes.values():
        fold_step = _first_fold_step(episode)
        if fold_step is None:
            episodes_without_fold += 1
            continue
        for row in episode:
            if _step(row) < fold_step:
                continue
            for call in row.get("tool_calls") or []:
                if _tool_name(call) in REFETCH_TOOLS:
                    refetch += 1

    n = len(request_rows)
    report = {
        "episodes": len(episode_rows) or len(episodes),
        "episodes_without_fold": episodes_without_fold,
        "requests": n,
        "graded": graded,
        "verified": verified,
        "accuracy": (verified / graded) if graded else None,
        "mean_prompt_tokens": (sum(_num(r, "prompt_tokens") for r in request_rows) / n)
                              if n else None,
        "mean_cached_tokens": (sum(_num(r, "cached_tokens") for r in request_rows) / n)
                              if n else None,
        "fold_events": sum(1 for r in request_rows if r.get("fold_event")),
        "dropped_turns": int(sum(_num(r, "dropped_turns") for r in request_rows)),
        "pinned_tokens": int(sum(_num(r, "pinned_tokens") for r in request_rows)),
        "refetch_count": refetch,
        "counts": counts,
    }
    report.update(_episode_report(episode_rows, rows[0].get("arm") if rows else None))
    return report


def analyse(rows: list[dict]) -> dict:
    by_arm: dict[str, list[dict]] = {}
    for row in rows:
        arm = row.get("arm")
        if not arm:
            continue
        by_arm.setdefault(arm, []).append(row)
    arms = {arm: _arm_report(by_arm[arm])
            for arm in sorted(by_arm, key=_arm_order)}
    return {"row_count": len(rows), "arms": arms, "verdict": verdict(arms)}


def verdict(arms: dict) -> dict:
    """Evaluate the five falsifiers.  Each entry carries the numbers that decided it."""
    checks: dict[str, dict] = {}

    lost_total = sum(a["counts"]["lost_then_failed"] for a in arms.values())
    checks["instrument_failure"] = {
        "fired": lost_total == 0,
        "lost_then_failed_total": lost_total,
        "arms": sorted(arms),
    }

    per_arm = {arm: {"present_then_failed": a["counts"]["present_then_failed"],
                     "lost_then_failed": a["counts"]["lost_then_failed"]}
               for arm, a in arms.items()}
    checks["null_model_error"] = {
        "fired": bool(arms) and all(
            v["present_then_failed"] > v["lost_then_failed"] for v in per_arm.values()),
        "per_arm": per_arm,
    }

    pinned = arms.get("pinned")
    none = arms.get("none")
    pin_acc = pinned["accuracy"] if pinned else None
    none_acc = none["accuracy"] if none else None
    # PIN-PREMISE: pinning is dead only when it does not beat the control.  Two perfect
    # arms are not a failure of pinning -- nothing was lost, so there was nothing to
    # recover -- and firing there would report a healthy instrument as broken.
    pin_fired = (pin_acc is not None and none_acc is not None
                 and (pin_acc < none_acc
                      or (pin_acc == none_acc and none_acc < 1.0)))
    checks["pin_premise_fails"] = {
        "fired": pin_fired,
        "pinned_accuracy": pin_acc,
        "none_accuracy": none_acc,
        "note": ("both arms perfect: nothing was lost, so the premise is untested"
                 if (pin_acc == 1.0 and none_acc == 1.0) else ""),
    }

    bcf = arms.get("bounded-context-fetch")
    mnf = arms.get("masking-no-fetch")
    bcf_ref = bcf["refetch_count"] if bcf else None
    mnf_ref = mnf["refetch_count"] if mnf else None
    checks["recovery_not_paid"] = {
        "fired": (bcf_ref is not None and mnf_ref is not None
                  and bcf_ref == mnf_ref),
        "bounded_context_fetch_refetch": bcf_ref,
        "masking_no_fetch_refetch": mnf_ref,
    }

    compact = arms.get("compact")
    compact_prompt = compact["mean_prompt_tokens"] if compact else None
    none_prompt = none["mean_prompt_tokens"] if none else None
    checks["compaction_not_cheaper"] = {
        "fired": (compact_prompt is not None and none_prompt is not None
                  and not (compact_prompt < none_prompt)),
        "compact_mean_prompt_tokens": compact_prompt,
        "none_mean_prompt_tokens": none_prompt,
    }

    fired = [name for name in FALSIFIERS if checks[name]["fired"]]
    return {"instrument_ok": not fired, "fired": fired, "falsifiers": checks}


def table(result: dict) -> list[str]:
    lines = ["arm                   eps  req  graded  verif  acc    prompt  cached  "
             "folds  drop   pin  refetch"]
    for arm, v in result["arms"].items():
        acc = "-" if v["accuracy"] is None else f"{v['accuracy']:.3f}"
        prompt = "-" if v["mean_prompt_tokens"] is None else f"{v['mean_prompt_tokens']:.1f}"
        cached = "-" if v["mean_cached_tokens"] is None else f"{v['mean_cached_tokens']:.1f}"
        lines.append(f"{arm:<20} {v['episodes']:>4} {v['requests']:>4} "
                     f"{v['graded']:>7} {v['verified']:>6} {acc:>6} {prompt:>7} "
                     f"{cached:>7} {v['fold_events']:>6} {v['dropped_turns']:>5} "
                     f"{v['pinned_tokens']:>5} {v['refetch_count']:>8}")

    lines.append("")
    lines.append("episode summary (per-episode rows only; solved rate is NOT reported)")
    lines.append("arm                   eps  void  ckpt_n  ckpt_ok  ckpt_acc  cost_units  "
                 "cost/ok  refetch  compact")
    for arm, v in result["arms"].items():
        if v["void"]:
            acc = "VOID"
        elif v["checkpoint_accuracy"] is None:
            acc = "-"
        else:
            acc = f"{v['checkpoint_accuracy']:.3f}"
        cost = "-" if v["cost_units"] is None else f"{v['cost_units']:.0f}"
        per_ok = ("-" if v["cost_units_per_verified_success"] is None
                  else f"{v['cost_units_per_verified_success']:.1f}")
        refetch = ("-" if v["mean_refetch_count"] is None
                   else f"{v['mean_refetch_count']:.2f}")
        compact = ("-" if v["mean_compactions"] is None
                   else f"{v['mean_compactions']:.2f}")
        lines.append(f"{arm:<20} {v['episode_rows']:>4} {v['void_episodes']:>5} "
                     f"{v['checkpoints_n']:>7} {v['checkpoints_ok']:>8} {acc:>9} "
                     f"{cost:>11} {per_ok:>8} {refetch:>8} {compact:>8}")

    lines.append("")
    for name in FALSIFIERS:
        check = result["verdict"]["falsifiers"][name]
        numbers = {k: val for k, val in check.items() if k != "fired"}
        lines.append(f"falsifier {name}: fired={check['fired']} "
                     f"numbers={json.dumps(numbers, sort_keys=True)}")
    v = result["verdict"]
    lines.append("")
    lines.append(f"verdict: instrument_ok={v['instrument_ok']} fired={v['fired']}")
    return lines


def markdown(result: dict) -> str:
    lines = ["| arm | episodes | requests | graded | verified | accuracy | "
             "mean prompt | mean cached | folds | dropped | pinned | refetch |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm, v in result["arms"].items():
        acc = "-" if v["accuracy"] is None else f"{v['accuracy']:.3f}"
        prompt = "-" if v["mean_prompt_tokens"] is None else f"{v['mean_prompt_tokens']:.1f}"
        cached = "-" if v["mean_cached_tokens"] is None else f"{v['mean_cached_tokens']:.1f}"
        lines.append(f"| {arm} | {v['episodes']} | {v['requests']} | {v['graded']} | "
                     f"{v['verified']} | {acc} | {prompt} | {cached} | "
                     f"{v['fold_events']} | {v['dropped_turns']} | "
                     f"{v['pinned_tokens']} | {v['refetch_count']} |")
    lines.append("")
    lines.append("Per-episode rows only; solved rate is NOT reported.")
    lines.append("")
    lines.append("| arm | episodes | void | checkpoints | ok | checkpoint accuracy | "
                 "cost units | cost/ok | mean refetch | mean compactions |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for arm, v in result["arms"].items():
        if v["void"]:
            acc = "VOID"
        elif v["checkpoint_accuracy"] is None:
            acc = "-"
        else:
            acc = f"{v['checkpoint_accuracy']:.3f}"
        cost = "-" if v["cost_units"] is None else f"{v['cost_units']:.0f}"
        per_ok = ("-" if v["cost_units_per_verified_success"] is None
                  else f"{v['cost_units_per_verified_success']:.1f}")
        refetch = ("-" if v["mean_refetch_count"] is None
                   else f"{v['mean_refetch_count']:.2f}")
        compact = ("-" if v["mean_compactions"] is None
                   else f"{v['mean_compactions']:.2f}")
        lines.append(f"| {arm} | {v['episode_rows']} | {v['void_episodes']} | "
                     f"{v['checkpoints_n']} | {v['checkpoints_ok']} | {acc} | "
                     f"{cost} | {per_ok} | {refetch} | {compact} |")
    v = result["verdict"]
    lines.append("")
    lines.append(f"`verdict: instrument_ok={v['instrument_ok']} fired={v['fired']}`")
    return "\n".join(lines) + "\n"


def _resolve(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--rows", required=True, help="glob of rows-agentic-*.jsonl")
    ap.add_argument("--out", default=None, help="JSON report path")
    ap.add_argument("--md", default=None, help="markdown table path")
    args = ap.parse_args(argv)

    rows = load_rows(args.rows)
    if not rows:
        print(f"no rows matched {args.rows}")
    result = analyse(rows)
    result["rows_glob"] = args.rows
    for line in table(result):
        print(line)

    if args.out:
        path = _resolve(args.out)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print(f"wrote {args.out}")
    if args.md:
        path = _resolve(args.md)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(markdown(result))
        print(f"wrote {args.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
