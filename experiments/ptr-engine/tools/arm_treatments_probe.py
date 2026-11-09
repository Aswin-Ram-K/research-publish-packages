#!/usr/bin/env python3
"""arm_treatments_probe.py — ARM-TREATMENTS-FIRE. OFFLINE: zero inference requests.

    python3 experiments/ptr-engine/tools/arm_treatments_probe.py            # write json
    python3 experiments/ptr-engine/tools/arm_treatments_probe.py --check    # assert, no write

WHAT THIS ANSWERS, from rows on disk and from the runner's own code paths:

  A. ENVELOPE. The observed prompt-token curve per (grid, arm), the per-turn growth,
     and -- by inverting the growth -- the smallest ``wall_tokens`` at which each of the
     three treatments' predicates becomes true, and the turn it becomes true at. Also
     the inverse question: at the frozen 65536 wall, what N each arm would need.

  B. MARKERS. How many rows in the pinned corpus carry a non-zero treatment marker
     today: ``evicted > 0``, ``lease > 1``, ``kind == "digest"``.

  C. FORCED SIMULATION. Drive the REAL ``Planner`` (run_longrun.py) over a copy of the
     real fixture with only the three trigger inputs changed, and emit the row the
     runner's own writer (``make_row``) would write — so the markers are produced by
     production code, not by this probe. No fixture on disk is touched: the variant
     lives in memory, and the rows printed here are never appended to the corpus.

The three predicates, quoted from run_longrun.py:

  GROW    :1063  while len(parts) > 1 and est_tokens("\\n\\n".join(parts + [current]),
                                                    self.bpt) > self.wall_tokens:
  COMPACT :1080  if t > 1 and est_tokens(window, self.bpt) > self.wall_tokens:
  REOPEN  :1113  if t in self.walls and self.lease_start <= t:      # self.walls =
                                                                    # fixture["lease_reopen_turns"]
"""
import collections
import copy
import glob
import json
import math
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))          # experiments/ptr-engine/tools
PTR = os.path.dirname(HERE)                                # experiments/ptr-engine
LONG = os.path.join(PTR, "longrun")
MEASURE = os.path.join(PTR, "measure")
OUT = os.path.join(MEASURE, "ARM-TREATMENTS.json")
sys.path.insert(0, LONG)

import run_longrun as R  # noqa: E402

# The four CONTROLLED longrun grids (each is a full 4-arm or 2-arm cell batch).
GRIDS = collections.OrderedDict([
    ("stage1", "rows-longrun-2026-10-26.jsonl"),
    ("G4-RUN-C-V2", "rows-longrun-c-2026-10-26.jsonl"),
    ("v3", "rows-longrun-v3-2026-10-26.jsonl"),
    ("v4", "rows-longrun-v4-2026-10-26.jsonl"),
])
FIXTURE = os.path.join(LONG, "tasks-v5", "runtime-v5", "LR-01.v5.json")
HORIZON = 48          # PARM-1 frozen turn count
WALL_NOW = 65536      # the wall every fixture declares
FACTOR = 1.374532     # BUDGET-SCHEDULE.md:21 (1101 requests / 801 turn rows)
ASTAR = 792           # BUDGET-SCHEDULE.md:43 (4 arms x 48 turns x 3 reps x factor)


def _rows(path):
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


# ----------------------------------------------------------------- A. envelope
def envelope():
    per = collections.OrderedDict()
    markers = {"rows": 0, "evicted_gt0": 0, "lease_gt1": 0, "digest_rows": 0}
    best = None
    for grid, name in GRIDS.items():
        path = os.path.join(MEASURE, name)
        curve = collections.defaultdict(dict)
        for r in _rows(path):
            markers["rows"] += 1
            if r.get("kind") == "digest":
                markers["digest_rows"] += 1
                continue
            if isinstance(r.get("evicted"), int) and r["evicted"] > 0:
                markers["evicted_gt0"] += 1
            if isinstance(r.get("lease"), int) and r["lease"] > 1:
                markers["lease_gt1"] += 1
            t, p = r.get("turn"), r.get("prompt_tokens")
            if isinstance(t, int) and isinstance(p, int):
                curve[r.get("arm")][t] = p
                if best is None or p > best["prompt_tokens"]:
                    best = {"prompt_tokens": p, "file": "experiments/ptr-engine/measure/" + name,
                            "turn": t, "arm": r.get("arm"), "grid": grid,
                            "run_id": r.get("run_id")}
        for arm, pts in curve.items():
            ts = sorted(pts)
            t1, p1 = ts[0], pts[ts[0]]
            t2, p2 = ts[-1], pts[ts[-1]]
            slope = (p2 - p1) / float(t2 - t1) if t2 > t1 else 0.0
            per[(grid, arm)] = {"T_first": t1, "prompt_first": p1, "T_last": t2,
                                "prompt_last": p2, "slope_tok_per_turn": round(slope, 3),
                                "n": len(ts)}
    return per, markers, best


def fire_turn(p1, slope, wall):
    """First turn t at which prompt(t) > wall, for prompt(t) = p1 + slope*(t-1)."""
    if slope <= 0:
        return None
    return 1 + math.ceil((wall + 1 - p1) / slope)


def envelope_arithmetic(per):
    """Per growth arm: the wall that makes its predicate fire by turn T, and the N
    the frozen 65536 wall would need."""
    out = {}
    for (grid, arm), s in per.items():
        if arm not in ("transcript-grow", "transcript-compact"):
            continue
        p1, slope = s["prompt_first"], s["slope_tok_per_turn"]
        if slope <= 0:
            continue
        row = {"grid": grid, "arm": arm, "prompt_T1": p1, "slope": slope,
               "wall_for_T24": int(p1 + slope * 23) - 1,
               "wall_for_T48": int(p1 + slope * 47) - 1,
               "turns_needed_at_wall_65536": fire_turn(p1, slope, WALL_NOW)}
        row["fires_within_48_at_current_wall"] = (
            row["turns_needed_at_wall_65536"] is not None
            and row["turns_needed_at_wall_65536"] <= HORIZON)
        out[f"{grid}/{arm}"] = row
    return out


# --------------------------------------------------- C. forced simulation (offline)
def _variant(wall, lease_turns):
    raw = open(FIXTURE, "rb").read()
    fx = json.loads(raw.decode("utf-8"))
    # the loader's own provenance fields (run_longrun.py:163-166), so make_row's
    # fixture_sha256/manifest path is exercised exactly as in a live cell
    fx["_path"] = os.path.abspath(FIXTURE)
    fx["_sha256"] = R.sha256_bytes(raw)
    fx["wall_tokens"] = int(wall)
    if lease_turns is not None:
        fx["lease_reopen_turns"] = list(lease_turns)
    else:
        fx.pop("lease_reopen_turns", None)
    return fx


def _fake_resp(prompt_tokens):
    """The shape client.py returns (dict.get everywhere downstream)."""
    return {"prompt_tokens": prompt_tokens, "completion_tokens": 8, "cached_tokens": 0,
            "raw_cached": 0, "ttft_ms": 1.0, "wall_ms": 2.0, "latency_s": 0.002,
            "stop_reason": "stop",
            "finish_reason": "stop", "max_tokens": 4096, "content_source": "fake",
            "reasoning": None, "finish_reasons": None, "usage_missing": False}


def _cfg():
    return SimpleNamespace(engine="sglang", max_tokens=4096, stream=True, metrics_scrape=False,
                           thinking="off", model="offline-fake", base_url="http://127.0.0.1:1/v1")


def _window_tokens(planner, info, fixture):
    return R.est_tokens(info["prompt"], planner.bpt)


ANS = "x" * 400  # the same recorded answer in the probe pass and the real pass


def force(arm, fire_at, wall=None, lease_turns=None):
    """Drive the REAL Planner turn by turn and return the first row with a live marker.

    The variant fixture differs from the on-disk one ONLY in the three trigger inputs
    (wall_tokens / lease_reopen_turns). Nothing is written to the corpus.
    """
    fx = _variant(wall if wall is not None else WALL_NOW, lease_turns)
    # For the token-predicate arms, discover the wall that makes the predicate true at
    # exactly `fire_at` from the planner's OWN window growth (probe pass, no rows).
    if wall is None and arm in ("transcript-grow", "transcript-compact"):
        probe = R.Planner(arm, _variant(10 ** 9, None), dry_run=True)
        for t in range(1, fire_at + 1):
            info = probe.build(t)
            probe.record(t, ANS)
        fx["wall_tokens"] = int(_window_tokens(probe, info, fx)) - 1
    planner = R.Planner(arm, fx, dry_run=True)   # dry_run == the repo's own offline prover
    cfg = _cfg()
    first = None
    for t in range(1, fire_at + 1):
        info = planner.build(t)
        tok = _window_tokens(planner, info, fx)
        extra = {"lease": info.get("lease"), "evicted": info.get("evicted")}
        kind = "turn"
        if info["digest_request"] is not None:
            kind = "digest"
        resp = _fake_resp(tok)
        row = R.make_row(cfg, fx, arm, 1, "arm-treatments-forced", t, resp,
                         "<offline fake answer>", kind, "off" * 20, extra)
        planner.record(t, ANS)
        if first is None:
            if arm == "transcript-grow" and row.get("evicted"):
                first = row
            elif arm == "transcript-compact" and kind == "digest":
                first = row
            elif arm == "lease-reopen" and (row.get("lease") or 0) > 1:
                first = row
    return fx, planner, first


def forced_proofs():
    proofs = {}
    fx, planner, row = force("transcript-grow", 12)
    proofs["transcript-grow"] = {
        "variant_wall_tokens": fx["wall_tokens"], "row": row,
        "marker": {"field": "evicted", "value": (row or {}).get("evicted")},
        "post_state": {"answers": len(planner.answers)},
    }
    fx, planner, row = force("transcript-compact", 12)
    proofs["transcript-compact"] = {
        "variant_wall_tokens": fx["wall_tokens"], "row": row,
        "marker": {"field": "kind", "value": (row or {}).get("kind")},
    }
    fx, planner, row = force("lease-reopen", 12, wall=WALL_NOW, lease_turns=[12])
    proofs["lease-reopen"] = {
        "variant_lease_reopen_turns": fx.get("lease_reopen_turns"), "row": row,
        "marker": {"field": "lease", "value": (row or {}).get("lease")},
    }
    return proofs


# ------------------------------------------------------------------ price
def price():
    turns = 4 * HORIZON * 3          # 4 arms x 48 turns x 3 reps (BUDGET-SCHEDULE.md:43)
    a_star = int(math.ceil(turns * FACTOR))
    digests_at_48 = 2 * 3            # 2 walls x 3 reps, transcript-compact only
    firing_48 = a_star + digests_at_48
    N56 = 4 * 56 * 3
    firing_56 = int(math.ceil(N56 * FACTOR)) + digests_at_48
    return {"turn_requests_48": turns, "factor": FACTOR,
            "a_star_published": ASTAR, "a_star_recomputed": a_star,
            "firing_grid_48": firing_48, "delta_48": firing_48 - ASTAR,
            "turn_requests_56": N56, "firing_grid_56": firing_56, "delta_56": firing_56 - ASTAR,
            "ledger_remaining": 3219,
            "grids_affordable_48_firing": 3219 // firing_48,
            "grids_affordable_a_star": 3219 // ASTAR}


def build():
    per, markers, best = envelope()
    env = envelope_arithmetic(per)
    proofs = forced_proofs()
    blockers = []
    for key, e in env.items():
        if not e["fires_within_48_at_current_wall"]:
            blockers.append(f"{key}: at wall_tokens={WALL_NOW} the predicate needs "
                            f"T{e['turns_needed_at_wall_65536']} ( > {HORIZON})")
    if markers["lease_gt1"] == 0:
        blockers.append("all arms/lease-reopen: lease_reopen_turns absent from every runtime "
                        "fixture -> self.walls == [] -> unreachable at ANY N")
    return {
        "unit": "ARM-TREATMENTS-FIRE",
        "generated_by": "experiments/ptr-engine/tools/arm_treatments_probe.py",
        "requests_spent": 0,
        "predicates": {
            "grow_eviction": {
                "code": "experiments/ptr-engine/longrun/run_longrun.py:1063-1072",
                "quoted": "while len(parts) > 1 and est_tokens(\"\\n\\n\".join(parts + [current]), self.bpt) > self.wall_tokens: parts.pop(0); evicted += 1",
                "row_field": "evicted",
                "written_at": "experiments/ptr-engine/longrun/run_longrun.py:1641 (extras from :2008)",
            },
            "compact_digest": {
                "code": "experiments/ptr-engine/longrun/run_longrun.py:1080-1088",
                "quoted": "if t > 1 and est_tokens(window, self.bpt) > self.wall_tokens: info[\"digest_request\"] = self.messages(instruction)",
                "row_field": "NONE on the turn row — only a separate row with kind == \"digest\" (written at run_longrun.py:2027)",
                "finding": "the turn that triggers compaction carries no marker of its own; the marker is a new row, joinable on `turn`",
            },
            "lease_reopen": {
                "code": "experiments/ptr-engine/longrun/run_longrun.py:1112-1117",
                "quoted": "if t in self.walls and self.lease_start <= t: self.lease = 1 + sum(1 for w in self.walls if w <= t)",
                "row_field": "lease",
                "finding": "NOT a token predicate: self.walls = fixture.get(\"lease_reopen_turns\") (run_longrun.py:1004). The 64k wall is irrelevant to it; all 12 fixtures omit the key.",
            },
        },
        "envelope": {"per_arm": {f"{g}/{a}": v for (g, a), v in per.items()},
                     "wall_arithmetic": env,
                     "observed_max_prompt": best,
                     "wall_tokens_every_fixture": WALL_NOW,
                     "horizon_turns": HORIZON},
        "markers_today": markers,
        "forced_proofs": proofs,
        "price": price(),
        "blockers": blockers,
        "unreachable_at_48": [k for k, e in env.items() if not e["fires_within_48_at_current_wall"]]
                              + (["all/lease-reopen (key absent, any N)"] if markers["lease_gt1"] == 0 else []),
    }


def main(argv):
    doc = build()
    ok = True
    for name, p in doc["forced_proofs"].items():
        v = p["marker"]["value"]
        live = bool(v) if name != "lease-reopen" else (v or 0) > 1
        if name == "transcript-compact":
            live = v == "digest"
        print(f"FORCED {name:19s} marker {p['marker']['field']}={v!r} live={live}")
        ok = ok and live
    if not ok:
        print("FAIL: a forced simulation did not produce a live marker", file=sys.stderr)
        return 1
    if "--check" not in argv:
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {os.path.relpath(OUT, os.getcwd())}")
    print(f"markers today: {json.dumps(doc['markers_today'])}")
    print(f"max prompt: {doc['envelope']['observed_max_prompt']}")
    print(f"price: {json.dumps(doc['price'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
