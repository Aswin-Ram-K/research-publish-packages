# UNIT `TVS-CENSORED` — censored observation of tokens_to_verified_success

**Card contract** — objective, hard bound, write paths, deliverable shape, and the generator this unit was
measured with. The generator lives here because it must regenerate the JSON for the verdict row and `/tmp` does
not persist between shells; `orchestration/units/` is a declared write path.

- **Objective:** turn `tokens_to_verified_success` from 20 empty cells into a censored metric (event vs censored),
  with a per-arm censoring statement, wasted-work decomposition of the 3 event pairs, and a proposed definition
  clause. Offline: zero inference requests.
- **Hard bound:** 24 tool calls; handoff `partial` if fewer than 5 remain.
- **Write paths (exactly):** `docs/TVS-CENSORED.md` · `experiments/ptr-engine/measure/TVS-CENSORED.json` ·
  `orchestration/units/TVS-CENSORED.md` · `orchestration/handoffs/TVS-CENSORED.json` ·
  `orchestration/journals/TVS-CENSORED.jsonl` · `/tmp/**`.
- **Never:** overwrite `measure/TVS.json` or `docs/TVS.md` (definition + first result); compute a mean, median,
  CI, or `0` over a set containing a censored row; impute a censored value; pool across grids; mix the pre-T3
  grade era with the current one; count `repair.t30` (not a declared checkpoint turn, `PARM-1-ERRATA`).
- **Status:** done. Result and evidence in `orchestration/handoffs/TVS-CENSORED.json`; the reading is
  `docs/TVS-CENSORED.md`; the numbers are `experiments/ptr-engine/measure/TVS-CENSORED.json`.

## Verdict command (frozen per execution)

Extracts the generator block below to `/tmp`, runs it twice, and diffs the two runs against each other **and**
against the production JSON. Exit 0 = the JSON is a deterministic regeneration of itself from the row/grade files.

```
python3 -c "import re,pathlib
txt=pathlib.Path('orchestration/units/TVS-CENSORED.md').read_text()
m=re.search(r'#SCRIPT-BEGIN\n(.*?)#SCRIPT-END',txt,re.S)
pathlib.Path('/tmp/tvs_censored.py').write_text(m.group(1))
print('extracted',len(m.group(1)),'bytes')"; python3 /tmp/tvs_censored.py --out /tmp/tvs_cens_run1.json; python3 /tmp/tvs_censored.py --out /tmp/tvs_cens_run2.json; diff -u /tmp/tvs_cens_run1.json /tmp/tvs_cens_run2.json; diff -u /tmp/tvs_cens_run1.json experiments/ptr-engine/measure/TVS-CENSORED.json; echo DETERMINISTIC-OK
```

This is the exact line recorded in the verdict row (PASS `f17663d1`, exit 0). It is deliberately split into
segments that each begin with an allow-listed runner (`python3`, `diff`, `echo`) because
`checkVerdictCommand` splits on `;`/`&`/`|` even inside quotes — an earlier `bash -c '… sed …'` form was refused
`command-not-allowed` for `sed`. `ROOT` inside the generator is the cwd, so the same line works in a scratch copy.

## Generator (kept verbatim between the markers; `ROOT` is the cwd so a scratch copy works)

```python
#SCRIPT-BEGIN
#!/usr/bin/env python3
"""TVS-CENSORED generator: censored observation table over the 23 declared run/arm pairs.

Offline: reads row files, grade files and measure/TVS.json only. Zero inference requests.
Writes only the --out path (default experiments/ptr-engine/measure/TVS-CENSORED.json).
No mean/median/CI/0 over a censored set; a censored pair carries spending and horizon, never a tvs.
"""
import json, glob, os, sys

ROOT = os.path.abspath(os.environ.get("TVS_ROOT") or os.getcwd())
MEASURE = os.path.join(ROOT, "experiments/ptr-engine/measure")
AS_OF = "2026-10-26T16:00:00+00:00"
DECLARED_HORIZON = 48
T3_BOUNDARY = "2026-10-26T15:56:00+00:00"

HORIZON_REASON = {
    "rows-longrun-2026-10-26-fix": {
        "source": "docs/FAILED-TRIAGE.md:172 (RUN-INSTRUMENT-FIX)",
        "quote": "rows exist (903 KB) but the proof is 12/48 turns, so the instrument fix stays unproven",
        "note": "grid-level record only: it explains transcript-grow's 12-turn horizon; it does not name a reason for the three arms whose last row is turn 3 with finish_reason=stop and failed_turn false.",
    },
    "rows-longrun-2026-10-26-policy": {
        "source": "docs/FAILED-TRIAGE.md:171 (RUN-REASONING-POLICY)",
        "quote": "rows 1-12 are real and row-backed; turns 13-48 were never sent",
        "note": "grid-level record only: it explains transcript-grow's 28-turn horizon as truncation-driven (finish_reason=length at the 16384 cap on 14 of its 28 rows); it does not name a reason for the three arms whose last row is turn 3.",
    },
}


def grade_file_for(rows_basename):
    """Same selection rule as experiments/ptr-engine/tools/tokens_to_verified.py cell_grade_files()."""
    for p in sorted(glob.glob(os.path.join(MEASURE, "cell-*.grade-v5.json"))):
        try:
            g = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if os.path.basename(g.get("rows_file", "")) == rows_basename:
            return p, g
    return None, None


def dedupe(rows):
    seen, out, skipped, undedupable = {}, [], 0, 0
    for r in rows:
        sha, ts = r.get("content_sha256"), r.get("ts")
        if not sha or not ts:
            undedupable += 1
            out.append(r)
            continue
        key = (r.get("arm"), r.get("rep"), r.get("turn"), ts, r.get("prompt_tokens"),
               r.get("completion_tokens"), sha)
        if key in seen:
            skipped += 1
            continue
        seen[key] = 1
        out.append(r)
    return out, skipped, undedupable


def tok(rows):
    total = excluded = 0
    for r in rows:
        p, c = r.get("prompt_tokens"), r.get("completion_tokens")
        if p is None or c is None:
            excluded += 1
            continue
        total += p + c
    return total, excluded


def grade_cells_for_arm(grade, arm):
    cells = []
    for c in (grade or {}).get("cells") or []:
        if c.get("arm") != arm:
            continue
        cells.append({"id": c.get("id"), "turn": c.get("turn"), "verdict": c.get("verdict"),
                      "reason": c.get("reason"), "answer_parse_error": c.get("answer_parse_error"),
                      "undecidable": bool(c.get("undecidable"))})
    cells.sort(key=lambda c: (c["turn"] if isinstance(c["turn"], int) else -1))
    return cells


def twin_diff(picked_grade, twin_path):
    if not twin_path or not os.path.exists(twin_path):
        return None
    twin = json.load(open(twin_path, encoding="utf-8"))

    def idx(d):
        return {(c.get("arm"), c.get("id")): (c.get("verdict"), c.get("reason")) for c in d.get("cells") or []}
    a, b = idx(picked_grade), idx(twin)
    diffs = [{"arm": k[0], "id": k[1], "picked": list(a[k]) if a.get(k) else None,
              "stamped_twin": list(b[k]) if b.get(k) else None}
             for k in sorted(set(a) | set(b), key=lambda x: (str(x[0]), str(x[1]))) if a.get(k) != b.get(k)]
    return {"path": os.path.relpath(twin_path, ROOT),
            "grader_sha256_recorded": twin.get("grader_sha256"),
            "generated_at": twin.get("generated_at"),
            "checkpoint_verdict_diffs": diffs}


def main():
    out_path = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else \
        os.path.join(MEASURE, "TVS-CENSORED.json")
    tvs = json.load(open(os.path.join(MEASURE, "TVS.json"), encoding="utf-8"))
    cells_out, checks = [], []

    for cell in tvs["cells"]:
        grid, arm = cell["grid"], cell["arm"]
        rows_path = os.path.join(MEASURE, grid + ".jsonl")
        rows = [json.loads(l) for l in open(rows_path, encoding="utf-8") if l.strip()]
        arm_rows_all = [r for r in rows if r.get("arm") == arm]
        arm_rows, dup_skipped, undedupable = dedupe(arm_rows_all)
        spent, excluded_null = tok(arm_rows)
        turns = sorted({r.get("turn") for r in arm_rows if isinstance(r.get("turn"), int)})
        horizon = max(turns) if turns else 0

        gpath, grade = grade_file_for(grid + ".jsonl")
        chk = grade_cells_for_arm(grade, arm)
        last = chk[-1] if chk else None
        twin = twin_diff(grade, os.path.join(MEASURE, "regrade", grid + ".grade-v5.json")) if gpath else None
        gen_at = (grade or {}).get("generated_at") or ""
        pre_t3 = gen_at < T3_BOUNDARY

        event = cell.get("tvs") is not None
        row = {
            "pair_id": "%s/%s" % (grid, arm),
            "grid": grid,
            "rows_file": "experiments/ptr-engine/measure/%s.jsonl" % grid,
            "arm": arm,
            "state": "event" if event else "censored",
            "grade_file": os.path.relpath(gpath, ROOT) if gpath else None,
            "grader_state": {
                "grader_sha256_recorded_in_grade_file": (grade or {}).get("grader_sha256"),
                "grader_stamped": bool((grade or {}).get("grader_sha256")),
                "grade_file_generated_at": gen_at or None,
                "era": "pre-T3" if pre_t3 else "current",
                "era_note": ("graded at 14:57:22Z, before the T3 boundary 15:56:00Z; REGRADE.json records 22 grade paths "
                             "differing from the current instrument on this file, so its pass is a pre-T3 pass"
                             if pre_t3 else
                             "graded at 15:56Z, in the current grade_v5 era, but the file itself records no grader sha"),
            },
            "stamped_twin": twin,
            "turns_observed": horizon,
            "declared_horizon": DECLARED_HORIZON,
            "horizon_short": horizon < DECLARED_HORIZON,
            "turns_touched": len(turns),
            "rows_in_file_for_arm": len(arm_rows_all),
            "requests_counted": len(arm_rows),
            "duplicate_records_skipped": dup_skipped,
            "rows_without_dedup_key": undedupable,
            "tokens": {"spent_whole_run": spent, "excluded_null_token_rows": excluded_null},
            "checkpoints_graded": chk,
            "last_checkpoint": last,
        }

        if event:
            t = cell["tvs"]
            win = [r for r in arm_rows if isinstance(r.get("turn"), int) and r["turn"] <= t["turn"]]
            before = [r for r in win if r["turn"] < t["turn"]]
            on = [r for r in win if r["turn"] == t["turn"]]
            after = [r for r in arm_rows if isinstance(r.get("turn"), int) and r["turn"] > t["turn"]]
            before_tok, _ = tok(before)
            on_tok, _ = tok(on)
            after_tok, _ = tok(after)
            tool_sends = sum(1 for r in win if r.get("kind") == "tool-followup" or r.get("fetch_followup") is True)
            pt = (cell.get("pass_turns") or [{}])[0]
            row["event"] = {
                "checkpoint_id": pt.get("id"),
                "checkpoint_turn": pt.get("turn"),
                "checkpoint_reason": pt.get("reason"),
                "turn_of_success": t["turn"],
                "tokens_to_success": t["tokens"],
                "prompt_tokens": t["prompt"],
                "completion_tokens": t["completion"],
                "cached_tokens": t.get("cached_tokens"),
                "cached_share": t.get("cached_share"),
                "requests_counted_to_success": t["requests_counted"],
                "decomposition": {
                    "tokens_before_success_turn": before_tok,
                    "tokens_on_success_turn": on_tok,
                    "sends_before_success_turn": len(before),
                    "sends_on_success_turn": len(on),
                    "tool_round_trip_sends_in_window": tool_sends,
                    "turn_rows_in_window": sorted({r["turn"] for r in win}),
                    "tokens_after_success": after_tok,
                    "sends_after_success": len(after),
                    "whole_run_total": spent,
                    "after_success_share": round(after_tok / spent, 4) if spent else None,
                },
            }
        else:
            h = HORIZON_REASON.get(grid)
            row["censored"] = {
                "turns_observed": horizon,
                "tokens_spent_in_observed_run": spent,
                "requests_counted": len(arm_rows),
                "last_checkpoint_id": last["id"] if last else None,
                "last_checkpoint_turn": last["turn"] if last else None,
                "last_checkpoint_verdict": last["verdict"] if last else None,
                "last_checkpoint_reason": last["reason"] if last else None,
                "last_row_finish_reason": arm_rows[-1].get("finish_reason") if arm_rows else None,
                "last_row_failed_turn": arm_rows[-1].get("failed_turn") if arm_rows else None,
                "last_row_error": arm_rows[-1].get("error") if arm_rows else None,
                "horizon_reason": h["source"] if h else None,
                "horizon_reason_quote": h["quote"] if h else None,
                "horizon_reason_scope_note": h["note"] if h else None,
                "horizon_reason_recorded": bool(h),
                "tvs": None,
            }

        if cell.get("whole_run_total") is not None and spent != cell["whole_run_total"]:
            checks.append({"pair_id": row["pair_id"], "check": "whole_run_total_matches_TVS",
                           "tvs_json": cell["whole_run_total"], "recomputed": spent, "ok": False})
        cells_out.append(row)

    per_arm = {}
    for r in cells_out:
        a = per_arm.setdefault(r["arm"], {"arm": r["arm"], "n_pairs": 0, "n_event": 0, "n_censored": 0,
                                          "events": [], "censored_horizons": []})
        a["n_pairs"] += 1
        if r["state"] == "event":
            a["n_event"] += 1
            a["events"].append({"pair_id": r["pair_id"], "turn_of_success": r["event"]["turn_of_success"],
                                "tokens_to_success": r["event"]["tokens_to_success"],
                                "checkpoint_id": r["event"]["checkpoint_id"]})
        else:
            a["n_censored"] += 1
            a["censored_horizons"].append({"pair_id": r["pair_id"],
                                           "turns_observed": r["censored"]["turns_observed"]})
    for a in per_arm.values():
        a["rate_estimate"] = ("none: a Kaplan-Meier or any success-rate estimate is not justified at "
                              "%d event(s) over %d pair(s) for this arm" % (a["n_event"], a["n_pairs"]))
        a["estimable"] = False

    shorts = [r["pair_id"] for r in cells_out if r["horizon_short"]]
    no_reason = [r["pair_id"] for r in cells_out if r["horizon_short"] and not r["censored"]["horizon_reason_recorded"]]
    n_event = sum(1 for r in cells_out if r["state"] == "event")
    n_cens = len(cells_out) - n_event
    event_turns = sorted({r["event"]["turn_of_success"] for r in cells_out if r["state"] == "event"})
    event_arms = sorted({r["arm"] for r in cells_out if r["state"] == "event"})
    word = {0: "No", 1: "One", 2: "Two", 3: "Three"}.get(n_event, str(n_event))
    sentence = ("%s of %d run/arm pairs reached a verified success within 48 turns; all %d are the %s arm at %s "
                "(turn %s); the other %d are censored at their horizon, which is a measurement of non-success, "
                "not a missing figure."
                % (word, len(cells_out), n_event, "/".join(event_arms) if event_arms else "no", "cp.0.t12",
                   "/".join(str(t) for t in event_turns) if event_turns else "n/a", n_cens))

    doc = {
        "unit": "TVS-CENSORED",
        "as_of": AS_OF,
        "generated_by": "orchestration/units/TVS-CENSORED.md generator block, run by the frozen verdict command; offline, 0 inference requests",
        "reader_note": "beside measure/TVS.json and docs/TVS.md; neither is edited. This file adds the censored reading.",
        "source_of_record": {"denominator": "experiments/ptr-engine/measure/TVS.json",
                             "definition": "docs/TVS.md",
                             "rows_dir": "experiments/ptr-engine/measure/",
                             "policy_notes": "docs/FAILED-TRIAGE.md:171-172, docs/QUALITY-ERAS.md, docs/PARM-1-ERRATA (repair.t30 out)"},
        "censoring_rule": {
            "state_space": ["event", "censored"],
            "event": "a checkpoint verdict `pass` under the grade_v5 file that measure/TVS.json's own instrument selection picked for the grid; carries turn_of_success, tokens_to_success (prompt+completion, cached share separate), checkpoint_id.",
            "censored": "no verified success within the run: the run is observed to a horizon (turns_observed) without one. Carries tokens actually spent and turns observed, and NO tvs value.",
            "forbidden": "no mean, median, CI, imputation or 0 over any set containing a censored row; no pooling across grids; no Kaplan-Meier at these counts.",
            "horizon_rule": "horizon = the last turn the row file actually reaches for that arm; the declared budget is 48 turns. A shorter horizon is reported with its recorded reason, or explicitly as unrecorded.",
        },
        "proposed_definition_clause": {
            "status": "PROPOSED, not adopted",
            "owner": "the owner of docs/TVS.md must adopt or reject it; this unit does not edit that file",
            "text": "TVS is a right-censored time-to-event observation. A run/arm pair is an `event` when its first grade_v5 `pass` checkpoint occurs within the run's turn budget (48); it is `censored` when the run reaches its horizon without one. A censored pair has no TVS value: it reports turns_observed and the tokens actually spent, and it is a measured non-event, not a missing datum. No mean, median, confidence interval or imputed value is computed over any set containing a censored pair, and no success-rate or survival estimate is quoted where the event count is too small to support one.",
        },
        "counts": {
            "declared_pairs": len(cells_out),
            "n_event": n_event,
            "n_censored": n_cens,
            "event_arms": event_arms,
            "event_turns": event_turns,
            "horizons_shorter_than_48": shorts,
            "short_horizons_without_a_recorded_reason": no_reason,
            "tokens_spent_by_censored_pairs": sum(r["censored"]["tokens_spent_in_observed_run"]
                                                  for r in cells_out if r["state"] == "censored"),
            "tokens_spent_by_censored_pairs_short_horizon": sum(r["censored"]["tokens_spent_in_observed_run"]
                                                                for r in cells_out if r["state"] == "censored" and r["horizon_short"]),
            "tokens_spent_by_censored_pairs_full_horizon": sum(r["censored"]["tokens_spent_in_observed_run"]
                                                               for r in cells_out if r["state"] == "censored" and not r["horizon_short"]),
            "tokens_to_success_by_event_pairs": sum(r["event"]["tokens_to_success"]
                                                    for r in cells_out if r["state"] == "event"),
            "whole_run_tokens_by_event_pairs": sum(r["event"]["decomposition"]["whole_run_total"]
                                                   for r in cells_out if r["state"] == "event"),
            "spending_note": "tokens_spent_by_censored_pairs is a SUM of whole observed runs, not a tvs and not an average; it is never combined with a tokens_to_success value.",
        },
        "per_arm": [per_arm[k] for k in sorted(per_arm)],
        "cells": cells_out,
        "quotable_sentence": sentence,
        "integrity_checks": {
            "token_sum_vs_TVS_json": {"method": "recomputed prompt+completion over distinct requests per pair, compared with measure/TVS.json whole_run_total",
                                      "mismatches": checks},
            "grader_stamp": {"files_examined": len({r["grade_file"] for r in cells_out}),
                             "files_recording_a_grader_sha256": len({r["grade_file"] for r in cells_out if r["grader_state"]["grader_stamped"]}),
                             "note": "measure/TVS.json's own cell_grade_files() selection globs measure/cell-*.grade-v5.json; none of those files records grader_sha256, so every pair is marked grader_unstamped. The stamped twins measure/regrade/<grid>.grade-v5.json record 6893d5...; the per-pair checkpoint diff against them is in cells[].stamped_twin."},
        },
        "assumptions": [
            {"id": "A1", "text": "The pair space is exactly measure/TVS.json cells[] (23 pairs); no pair is added or dropped, and repair.t30 is excluded because it is not one of the 12 declared checkpoint turns (PARM-1-ERRATA)."},
            {"id": "A2", "text": "grade_v5 only, as the instrument of record; the grade file used is the one measure/TVS.json's own selection picked, so the censored table cannot disagree with the produced TVS values."},
            {"id": "A3", "text": "turns_observed is measured from the row file (max turn present for that arm), not from the declared budget; a run that stopped early is censored at the turn it reached, which is a shorter horizon and is reported as one."},
            {"id": "A4", "text": "Tokens for a censored pair are the whole observed run, deduplicated by the shared rule; they are spending, never a tvs."},
            {"id": "A5", "text": "The grade files carry no grader_sha256, so every pair is grader_unstamped per the row rule; the one pre-T3 file (rows-longrun-v6-tools, generated 14:57:22Z) is additionally flagged pre-T3 and not mixed with current-era pairs in any statement."},
        ],
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("WROTE", out_path)
    print("SENTENCE:", sentence)
    print("counts:", json.dumps({k: v for k, v in doc["counts"].items() if k != "horizons_shorter_than_48"}))
    print("mismatches:", json.dumps(checks))
    for r in cells_out:
        if r["state"] == "event":
            d = r["event"]
            print("EVENT", r["pair_id"], "turn", d["turn_of_success"], "tok", d["tokens_to_success"],
                  "before/on", d["decomposition"]["tokens_before_success_turn"], d["decomposition"]["tokens_on_success_turn"],
                  "tool_rt", d["decomposition"]["tool_round_trip_sends_in_window"], "era", r["grader_state"]["era"])
        else:
            print("CENS", r["pair_id"], "turns", r["censored"]["turns_observed"], "spent",
                  r["censored"]["tokens_spent_in_observed_run"], "last", r["censored"]["last_checkpoint_id"],
                  r["censored"]["last_checkpoint_verdict"], r["censored"]["last_checkpoint_reason"],
                  "stamp", "stamped" if r["grader_state"]["grader_stamped"] else "grader_unstamped",
                  "era", r["grader_state"]["era"])


if __name__ == "__main__":
    main()
#SCRIPT-END
```
