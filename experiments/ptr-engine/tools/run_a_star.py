#!/usr/bin/env python3
"""RUN-A* driver: 16 sequential cells on LR-01.v8, H2 claim, all four treatments.

LAUNCHER-GEN5-WIRE
------------------
Three numbers used to be literals inside this file while a record said otherwise.
Each now has ONE owner -- a record under measure/ -- and the launcher obeys it:

  pin        measure/HARNESS-PIN.json      generation + harness_sha256, read at import
  cells      measure/GRID-PARAMS.json      shape.arms (6/6/2/2 = 16)
  price      measure/GRID-PARAMS.json      price.total (1,056), printed beside remaining
  remaining  measure/LEDGER-GRID-BASELINE-2.json / REQUEST-LEDGER.json  `remaining`

A record that disagrees with this launcher's own signed-off expectation is a
REFUSAL, not a silent follow: a launcher that quietly accepts any pin is the same
defect in the other direction. See docs/LAUNCHER-WIRING.md.

One rows file per cell via the frozen cell.py; a journal line after every cell; stop
rules 1/3/4/7 and PRE-CONDITION 10 (per-arm mechanism marker) checked between cells;
projected (advisory) vs actual wall recorded per cell. Progress goes to stdout (the
managed background job's stream) and to measure/run-a-star.json.

GRID-SHAPE (tools-on era, docs/GRID-SHAPE.md)
--------------------------------------------
The frozen cell.py has NO `--tools` argument and its runner argv
(cell.py:1502-1521) never emits one, so a tools-on cell cannot be started through
it as-is. cell.py DOES honour `CELL_RUNNER_PATH` (cell.py:122) and launches
`[sys.executable, RUNNER, ...]` (cell.py:1502), so `--tools read_file` is carried
by a shim: a two-line python file that re-executes the frozen run_longrun.py BY
BYTES (runpy over its path) with `--tools read_file` appended. cell.py's
HARNESS_FILES digest (cell.py:130-138) digests run_longrun.py itself, which the
shim never modifies, so the harness pin still matches -- the dry run prints it.

    python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --dry-run
    python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --cell 1

`--tools` absent keeps the historical tools-off launch byte-identical (no shim, no
CELL_RUNNER_PATH, no --fetch-followup-allowance).
"""
import argparse, datetime, glob as globmod, hashlib, json, os, re, subprocess, sys
import tempfile, time, urllib.request
from math import comb

# Absolute on purpose: the red→green test copies this launcher into tmp_path and
# still needs it to price the REAL cell.py (tests/test_launcher_dryrun_refusal.py,
# test_red_reverting_the_detection_reports_green_again). The literal is therefore
# kept, but it is a single declared root that must exist -- tests/test_agent_context.py
# fails if it does not -- and RUN_A_STAR_ROOT overrides it for a relocated checkout.
# History: the literal used to spell "reserach extarctor", and after the directory
# was renamed every launch died on a missing cwd while the pin still looked valid.
ROOT = os.environ.get("RUN_A_STAR_ROOT") or "/home/zer0null/research extractor"
ENG = os.path.join(ROOT, "experiments/ptr-engine")
MEAS = os.path.join(ENG, "measure")
FIX = "experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json"
RUNNER = os.path.join(ENG, "longrun/run_longrun.py")
CELL = "experiments/ptr-engine/longrun/cell.py"
JOURNAL = os.path.join(ROOT, "orchestration/journals/RUN-A-STAR.jsonl")
RESULT = os.path.join(MEAS, "run-a-star.json")
LOGDIR = os.path.join(tempfile.gettempdir(), "run-a-star-logs")
ENDPOINT = "http://192.168.2.168:8012/v1"
CAP_WALL = 10616
# Tools-on: 48 fetch rounds per arm (run_longrun.py:230, RUNNER-ROUNDS-48) is the
# structural ceiling on follow-up requests in one 48-turn cell -- one round per turn --
# so cell.py is told to price exactly that many extra requests in G1 instead of its
# pooled 68/801 ratio.
FETCH_ALLOWANCE = 48

# HARNESS-PIN: the generation and digest are READ from measure/HARNESS-PIN.json at
# import time. They used to be a constant copied out of the record, which is how this
# launcher came to hold generation 4 while the record said generation 5 -- it then
# aborted every cell with "HARNESS-PIN record disagrees with the launcher".
# The two values below are the launcher's SIGNED-OFF EXPECTATION: a record that moves
# without them moving is refused, because a launcher that follows any pin silently is
# the same defect in the other direction. Advance BOTH pairs in the card that freezes
# a new generation; RUN_A_STAR_PIN points the read at another record (test hook).
# Generation 6 (LAUNCHER-GEN6-WIRE): TOOL-CHANNEL-WIRE moved client.py 5aa23bb5...
# -> 9b12b2ea... and run_longrun.py 30dfa9e9... -> 4f40dde1..., so the record's
# generation 6 digest is efefd885... (measure/HARNESS-PIN.json). Generation 5's
# 35ff41b7... stays on the record as the canary's epoch; it no longer launches.
# Generation 11 (U-SPCC-80): the grep tool joined the replay runner, so run_longrun.py
# moved again and the record's generation 11 digest is a668491a... . Generation 9's
# 32463261... and generation 8's 64e69e49... stay on the record under their own labels;
# neither launches any more.
PIN_EXPECTED_GENERATION = 11
PIN_EXPECTED_DIGEST = "a668491a55a4e2714b6e58dc8168919ee163bd2b5e3bb733b54fd9e38263bf73"
PIN_RECORD = os.environ.get("RUN_A_STAR_PIN") or os.path.join(MEAS, "HARNESS-PIN.json")

# GRID-STAMP-WIRING: every finished cell must carry its own `usable_for` stamp, or
# the analyser INCLUDES it in every comparison -- analyze_stats.py:749
# (`excluded = analyses is not None and len(analyses) == 0`) is False when the key is
# ABSENT, and analyze_stats.py:1753 prints `usable_for unstamped ... (included)`.
# The writer already lives beside the consumer (analyze_stats.py:777,
# `write_cell_manifest_usable_for`); this launcher CALLS it and never reimplements
# it, so exactly one function in the tree constructs the `usable_for` key.
GRID_USABLE_ANALYSES = ("h1", "h2", "h3")
# A turn that ended on these is a launch-shape failure, not a measurement
# (tranche_canary.py:164, DEGENERATE_STOP_REASONS).
DEGENERATE_STOP_REASONS = frozenset({"runaway_turn", "turn_wall_cap"})
# Distinct from cell.py's 2 (preflight/G3) and the launcher's 1 (a dry run that saw
# a refused cell): 4 means "the previous cell's manifest cannot show a usable_for
# stamp, so the grid refuses to spend a request on the next cell".
EXIT_UNSTAMPED_CELL = 4


def _read_pin(path):
    """(generation, digest, refusal-or-None) from one HARNESS-PIN record."""
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, None, ("HARNESS-PIN record unreadable at %s: %s" % (path, exc))
    gen = rec.get("generation")
    got = rec.get("harness_sha256")
    if gen != PIN_EXPECTED_GENERATION or got != PIN_EXPECTED_DIGEST:
        return gen, got, (
            "HARNESS-PIN record disagrees with the launcher: record generation=%r "
            "digest=%r, launcher signed-off generation=%r digest=%r (the record at "
            "%s moved; advance PIN_EXPECTED_GENERATION/PIN_EXPECTED_DIGEST in the "
            "same card that froze the new generation)"
            % (gen, got, PIN_EXPECTED_GENERATION, PIN_EXPECTED_DIGEST, path))
    return gen, got, None


PIN_GENERATION, HARNESS_PIN, PIN_ABORT = _read_pin(PIN_RECORD)


def pinned_digest(pin_record=None):
    """The record's digest, refused unless it is the signed-off one.

    The import-time read is what cell_argv carries. `pin_record` re-reads another
    file (the /tmp mismatch proof), so the refusal is reproducible without editing
    the tree.
    """
    if pin_record is not None:
        _gen, got, refusal = _read_pin(pin_record)
        if refusal:
            raise SystemExit(refusal)
        return got
    if PIN_ABORT:
        raise SystemExit(PIN_ABORT)
    return HARNESS_PIN


# CANARY-ARMS-WIRING: the priced canary is ONE 12-turn cell per arm, so the canary
# turns = CANARY_ARMS * 12 = 48 requests, not 12. The arms are named once, here.
CANARY_ARMS = ("pointer-stable", "transcript-grow", "transcript-compact", "lease-reopen")


# GRID-PARAMS is the record the launcher OBEYS: shape.arms is the cell plan and
# price.total is the launch price. It used to hold a 10-cell literal here while the
# record said 16 cells / 1,056 requests -- the "two artefacts, one number" class, with
# the launcher on the wrong side of it. RUN_A_STAR_GRID points at another record.
GRID_RECORD = os.environ.get("RUN_A_STAR_GRID") or os.path.join(MEAS, "GRID-PARAMS.json")
# The signed-off promotion (POWER-UNDER-TURN-N: n_eff 62.73 clears the floor of 60 at
# 6 runs per pair arm, where the old 10-cell shape measured 31.36). The record's
# shape.arms must equal this; a promotion is a DATA edit to both, in one card.
SHAPE_EXPECTATION = (("pointer-stable", 6), ("transcript-grow", 6),
                     ("transcript-compact", 2), ("lease-reopen", 2))


def _grid_record(path=None):
    path = path or GRID_RECORD
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
    except (OSError, ValueError) as exc:
        raise SystemExit("GRID-PARAMS record unreadable at %s: %s" % (path, exc))
    price = rec.get("price") or {}
    if price.get("total") is None:
        raise SystemExit("GRID-PARAMS price.total MISSING at %s: the launcher will "
                         "not print a blank price line" % path)
    shape = rec.get("shape") or {}
    arms = shape.get("arms")
    if not isinstance(arms, dict) or not arms:
        raise SystemExit("GRID-PARAMS shape.arms MISSING at %s: the cell plan has no "
                         "data source" % path)
    got = [(arm, int(arms.get(arm) or 0)) for arm, _ in SHAPE_EXPECTATION]
    if got != list(SHAPE_EXPECTATION) or set(arms) != {a for a, _ in SHAPE_EXPECTATION}:
        raise SystemExit("GRID-PARAMS shape disagrees with the launcher's signed-off "
                         "promotion: record=%r launcher=%r"
                         % (arms, dict(SHAPE_EXPECTATION)))
    if int(shape.get("cells") or len(plan_cells(rec))) != len(plan_cells(rec)):
        raise SystemExit("GRID-PARAMS shape.cells=%r disagrees with shape.arms=%r"
                         % (shape.get("cells"), arms))
    return rec


def grid_record(path=None):
    """The record, refused (named) when it is unreadable or disagrees."""
    if path is None and GRID_ABORT:
        raise SystemExit(GRID_ABORT)
    return _grid_record(path)


def plan_cells(rec):
    """The cell plan as DATA: one (arm, rep) per cell, in arm order.

    Derived, never a literal: promoting the shape is an edit to shape.arms (the
    record) and to SHAPE_EXPECTATION (this launcher's signed-off copy), not to a
    tuple buried in a loop.
    """
    arms = rec["shape"]["arms"]
    return tuple((arm, rep) for arm, _n in SHAPE_EXPECTATION
                 for rep in range(1, int(arms[arm]) + 1))


try:
    GRID_PARAMS = _grid_record()
    CELLS = plan_cells(GRID_PARAMS)
    GRID_ABORT = None
except SystemExit as _exc:                       # a refusal, carried to the gate
    GRID_PARAMS, CELLS, GRID_ABORT = None, (), str(_exc.code)


# The ledger is the ONLY source of the remaining figure. 3,219 was the pre-rebuild
# total baked into four arithmetic sites; the records now say 3,144 (cap 4,320).
#
# LEDGER-RECONCILE-DELTA: a frozen baseline and a ledger that is REBUILT from rows can
# never be compared as bare numbers -- the ledger moves with every billed cell, so
# equality refuses forever after the first post-freeze cell (CANARY-ERA-B-4 was refused
# at gate 2 with zero requests spent: 3,192 vs 3,144, a 48-row gap). The comparison is
# `live == baseline + attributed_delta`, the delta counted from the row files stamped
# after the baseline's `as_of`. An unexplained gap is STILL a hard refusal: that rule
# protects the budget and is not weakened here.
# LEDGER-KIND-RULE: the default photograph is baseline-4 (1321 / 2999), re-cut on the
# reconciled total. baseline-3 (1176 / 3144) stays on disk, unreachable by default and
# unmutated: obeying a stale freeze is how RUN-A-STAR-2 died at gate 2 with zero sent.
LEDGER_FROZEN = os.environ.get("RUN_A_STAR_LEDGER_BASELINE") or os.path.join(
    MEAS, "LEDGER-GRID-BASELINE-4.json")
LEDGER_LIVE = os.environ.get("RUN_A_STAR_LEDGER_LIVE") or os.path.join(
    MEAS, "REQUEST-LEDGER.json")
LEDGER_ROWS_GLOB = os.environ.get("RUN_A_STAR_LEDGER_ROWS") or os.path.join(
    MEAS, "rows-*.jsonl")

# LEDGER-KIND-RULE: ONE rule, ONE implementation. The attribution imports the recount's
# own function (`request_ledger.row_bills`) instead of restating it. The two restatements
# diverged -- this file's copy billed {turn, tool-followup} and *silently unbilled* every
# other kind, while the ledger counted an unknown kind and flagged it -- so 30
# `turn-initial` rows were invisible to attributed_delta and RUN-A-STAR-2 was refused at
# gate 2 with 0 requests sent (1176 + 115 == 1291 vs live 1321). No copied constant, no
# second tally; `COUNTED_KINDS` is an alias of the one vocabulary.
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(_TOOLS_DIR, "request_ledger.py")):
    # A COPY of this launcher (the red->green revert test writes one into tmp_path)
    # imports the recount from the workspace, not from its own directory.
    _TOOLS_DIR = os.path.join(ENG, "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
import request_ledger as _ledger          # noqa: E402  (path set above)
COUNTED_KINDS = _ledger.COUNTED_KINDS
UnrecognisedKind = _ledger.UnrecognisedKind
# What the last remaining_basis() compared, for the proof and for the journal.
LAST_RECONCILE = {}


def _epoch(ts):
    """ISO-8601 (`Z` or `+00:00`, second or millisecond) -> epoch seconds, else None."""
    if ts is None:
        return None
    text = str(ts).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def _row_counts(row):
    """Does this row cost one request? DELEGATES to request_ledger.row_bills().

    The previous body restated the rule and diverged three ways from the recount:
    `billed is False` missed `"false"`, and any kind outside {turn, tool-followup} --
    `turn-initial`, `digest` -- was dropped silently. An unrecognised kind now refuses,
    because silent unbilling is how the 30-row gap happened.
    """
    try:
        return _ledger.row_bills(row)
    except _ledger.UnrecognisedKind as exc:
        raise SystemExit(
            "REFUSED (LEDGER-KIND-RULE): %s. A row the rule cannot classify must not be "
            "dropped from the budget; fix the writer or extend COUNTED_KINDS with a "
            "make_row call site as evidence." % exc)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def attributed_delta(as_of_epoch, rows_glob=None):
    """(delta, files) counted from rows BILLED AFTER `as_of_epoch`.

    The baseline is a photograph; the ledger is rebuilt from rows. The delta is the
    only bridge between them that is a measurement rather than an assumption, so it
    is counted from the row files themselves and returned WITH the files that
    produced it (name, rows, sha256) -- the next reader does not re-derive them.
    """
    pattern = LEDGER_ROWS_GLOB if rows_glob is None else rows_glob
    delta, files = 0, []
    for path in sorted(globmod.glob(pattern), key=os.path.basename):
        counted = 0
        try:
            fh = open(path, encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(row, dict) or not _row_counts(row):
                    continue
                when = _epoch(row.get("ts") or row.get("ts_utc"))
                if when is None or when <= as_of_epoch:
                    continue
                counted += 1
        if counted:
            files.append({"file": os.path.basename(path), "rows": counted,
                          "sha256": _sha256(path)})
            delta += counted
    return delta, files


def remaining_basis():
    """(remaining, basis, cap) -- delta-aware, and a NAMED refusal when it cannot close.

    remaining_basis=ledger: the live ledger's own `remaining`, accepted only when the
    live ledger equals the frozen baseline PLUS the rows billed after the baseline's
    `as_of`. The gap must be exactly attributable to rows files on disk; a gap that
    is NOT explained is still a refusal, because the delta rule exists to protect the
    budget, not to let an arithmetic hole through. The three numbers compared --
    `baseline`, `attributed_delta`, `live` -- and the files that produced the delta
    are printed on every call, so no reader has to re-derive them.
    """
    def load(p):
        try:
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None

    def number(doc, *keys):
        for key in keys:
            v = (doc or {}).get(key) if isinstance(doc, dict) else None
            if v is not None:
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return None
        return None

    frozen, live = load(LEDGER_FROZEN), load(LEDGER_LIVE)
    live_remaining = number(live, "remaining")
    live_requests = number(live, "requests", "requests_raw")
    if live_requests is None:
        live_requests = number(live.get("budget") if isinstance(live, dict) else None,
                               "spent", "spent_raw")
    if live_remaining is None or live_requests is None:
        raise SystemExit("REFUSED: no ledger figure -- %s carries no "
                         "`remaining`/`requests`, so the launcher has no basis to print "
                         "(baseline: %s)" % (LEDGER_LIVE, LEDGER_FROZEN))
    base_remaining = number(frozen, "remaining")
    base_requests = number(frozen, "requests", "requests_raw")
    if base_requests is None:
        base_requests = number(frozen.get("budget") if isinstance(frozen, dict) else None,
                               "spent", "spent_raw")
    if base_remaining is None:
        raise SystemExit("REFUSED: ledger baseline %s is missing or carries no `remaining`, "
                         "so no delta can be attributed; live ledger is %d requests / "
                         "%d remaining" % (LEDGER_FROZEN, live_requests, live_remaining))
    as_of = None
    if isinstance(frozen, dict):
        as_of = frozen.get("as_of") or frozen.get("frozen_at") or frozen.get("captured_utc")
    as_of_epoch = _epoch(as_of)
    if base_requests is None or as_of_epoch is None:
        raise SystemExit("REFUSED: ledger baseline %s carries no usable `as_of`/`requests` "
                         "(%r / %r), so no delta can be attributed to a rows file; records "
                         "disagree on `remaining`: {baseline: %r, live: %r}"
                         % (LEDGER_FROZEN, as_of, base_requests, base_remaining,
                            live_remaining))
    delta, files = attributed_delta(as_of_epoch)
    explained = base_requests + delta
    LAST_RECONCILE.clear()
    LAST_RECONCILE.update({"baseline": base_requests, "attributed_delta": delta,
                           "live": live_requests, "as_of": as_of, "explained": explained,
                           "files": [dict(f) for f in files]})
    say("RECONCILE baseline=%d attributed_delta=%d live=%d explained=%d gap=%d "
        "as_of=%s files=%s"
        % (base_requests, delta, live_requests, explained, live_requests - explained,
           as_of,
           ", ".join("%s(+%d %s)" % (f["file"], f["rows"], f["sha256"][:12])
                     for f in files) or "none"))
    if explained != live_requests:
        gap = live_requests - explained
        raise SystemExit(
            "REFUSED: %d request(s) of ledger gap cannot be attributed to any rows file "
            "billed after %s -- baseline=%d + attributed_delta=%d = %d, live=%d, "
            "unexplained=%d; attributed rows files=%r; scanned %s"
            % (abs(gap), as_of, base_requests, delta, explained, live_requests, gap,
               [f["file"] for f in files], LEDGER_ROWS_GLOB))
    if base_remaining - delta != live_remaining:
        raise SystemExit(
            "REFUSED: `remaining` does not follow the same delta -- baseline=%d - "
            "attributed_delta=%d = %d, live=%d, unexplained=%d; records disagree on "
            "`remaining`: {baseline: %r, live: %r}; attributed rows files=%r"
            % (base_remaining, delta, base_remaining - delta, live_remaining,
               live_remaining - (base_remaining - delta), base_remaining, live_remaining,
               [f["file"] for f in files]))
    cap = number(frozen, "cap")
    if cap is None:
        cap = number(frozen.get("budget") if isinstance(frozen, dict) else None, "cap")
    if cap is None:
        cap = number(live, "cap")
    if cap is None:
        cap = number(live.get("budget") if isinstance(live, dict) else None, "cap")
    # LEDGER-KIND-RULE: the label names the baseline ACTUALLY in force, derived from its
    # path -- it was a hard-coded "baseline-3" string, which is a second, silently stale
    # statement of which photograph the launcher obeyed.
    _bnum = os.path.basename(LEDGER_FROZEN)
    if _bnum.startswith("LEDGER-GRID-BASELINE-") and _bnum.endswith(".json"):
        _bnum = "baseline-" + _bnum[len("LEDGER-GRID-BASELINE-"):-len(".json")]
    else:
        _bnum = _bnum or "baseline"
    basis = "ledger:%s+attributed-delta" % _bnum
    return live_remaining, basis, (int(cap) if cap is not None else None)


def price_line(remaining, basis, cap, cells=None):
    """The record's price, printed BESIDE the remaining figure it is drawn from.

    price.total is read, never computed here: a price the launcher invents is a
    second artefact, and the record and the dry run would disagree in opposite
    directions.
    """
    rec = grid_record()
    price = rec["price"]
    cells = len(CELLS) if cells is None else cells
    status = str(price.get("spend_status") or "unstated")
    approved = "false" if status.startswith("NOT approved") else "unknown"
    return ("PRICE source=%s price_total=%d price_remaining_after=%s "
            "remaining=%d remaining_basis=%s cap=%s cells=%d price_approved=%s"
            % (os.path.relpath(GRID_RECORD, ROOT), int(price["total"]),
               price.get("remaining_after"), remaining, basis, cap, cells,
               approved))

SHIM_BODY = '''#!/usr/bin/env python3
"""CELL_RUNNER_PATH shim: the frozen runner, with --tools read_file appended.

cell.py:122 honours CELL_RUNNER_PATH and launches [sys.executable, RUNNER, ...]
(cell.py:1502); cell.py has no --tools argument of its own, so this hop is the only
way to reach run_longrun.py's --tools (run_longrun.py:2798) without patching it.
run_longrun.py runs byte-for-byte unchanged (runpy), so cell.py's HARNESS_FILES
digest over run_longrun.py still matches.
"""
import runpy, sys
REAL = __REAL_RUNNER__
assert sys.argv[1:2] == ["--dry-run"] or True
sys.argv = [REAL] + sys.argv[1:] + ["--tools", "read_file"]
runpy.run_path(REAL, run_name="__main__")
'''

os.makedirs(LOGDIR, exist_ok=True)


def jline(**o):
    o["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(JOURNAL, "a") as fh:
        fh.write(json.dumps(o, sort_keys=True) + "\n")
    print("JOURNAL " + json.dumps(o, sort_keys=True), flush=True)


def say(msg):
    print("RUN-A " + msg, flush=True)


def save(results, extra=None):
    doc = {"unit": "RUN-A*", "cells": results}
    if extra:
        doc.update(extra)
    with open(RESULT, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")


def ensure_shim():
    """Write (idempotently) the CELL_RUNNER_PATH shim and prove it is readable."""
    d = os.path.join(tempfile.gettempdir(), "grid-shape-shim")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "runner_read_file.py")
    body = SHIM_BODY.replace("__REAL_RUNNER__", repr(RUNNER))
    with open(p, "w") as fh:
        fh.write(body)
    if not os.path.exists(p):
        raise SystemExit("shim not writable at %s" % p)
    return p


def warmup(arm):
    body = json.dumps({"model": "occamy-1.0", "messages": [
        {"role": "user", "content": "Reply with the single word: ok"}],
        "max_tokens": 8, "temperature": 0}).encode()
    req = urllib.request.Request(ENDPOINT + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=120)
        usage = (json.loads(r.read()).get("usage") or {})
        ms = round((time.time() - t0) * 1000, 1)
        say("warmup %s ok ms=%s usage=%s" % (arm, ms, json.dumps(usage)[:120]))
        return ms
    except Exception as exc:                                    # noqa: BLE001
        say("warmup %s FAILED %r" % (arm, exc))
        return None


def spend():
    n = 0
    for name in os.listdir(MEAS):
        if name.startswith("rows-") and name.endswith(".jsonl"):
            with open(os.path.join(MEAS, name)) as fh:
                n += sum(1 for line in fh if line.strip())
    return n


def pct(vals, q):
    if not vals:
        return None
    v = sorted(vals)
    k = max(0, min(len(v) - 1, int(round(q * (len(v) - 1)))))
    return v[k]


def rows_stats(path):
    wall, ttft, prompts = [], [], []
    markers = {"evicted_turns": 0, "digest_rows": 0, "lease_ge2_turns": 0,
               "prompt_identity_turns": 0, "prompt_change_turns": 0,
               "masked_rows": 0, "fetch_rows": 0, "oracle_injections": 0,
               "retrieval_outcomes": 0}
    turns = []
    degenerate_stop_turns = 0
    prev_sha = None
    with open(path) as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("kind") == "digest":
                markers["digest_rows"] += 1
                continue
            if (r.get("masked_rows") or 0) > 0:
                markers["masked_rows"] += 1
            if (r.get("fetch_rows") or 0) > 0 or (r.get("retrieval_attempts") or 0) > 0:
                markers["fetch_rows"] += 1
            if (r.get("oracle_injections") or 0) > 0:
                markers["oracle_injections"] += 1
            if r.get("retrieval_outcomes"):
                markers["retrieval_outcomes"] += 1
            if r.get("kind") != "turn":
                continue
            turns.append(r.get("turn"))
            if r.get("stop_reason") in DEGENERATE_STOP_REASONS:
                degenerate_stop_turns += 1
            if r.get("wall_ms") is not None:
                wall.append(float(r["wall_ms"]))
            if r.get("ttft_ms") is not None:
                ttft.append(float(r["ttft_ms"]))
            prompts.append(r.get("prompt_tokens") or 0)
            if (r.get("evicted") or 0) > 0:
                markers["evicted_turns"] += 1
            if (r.get("lease") or 0) >= 2:
                markers["lease_ge2_turns"] += 1
            # PRECONDITION-10-SCOPE: pointer-stable's own witness. The runner computes
            # prefix_sha256 (run_longrun.py:1165) but make_row never emits it
            # (ARM-INTEGRITY.md section 3: 0 of 788 rows), so the prompt identity the row
            # DOES carry is the witness: a cell whose prompt identity never changes has no
            # prefix dynamics to be stable against.
            sha = r.get("prompt_sha256")
            if sha:
                markers["prompt_identity_turns"] += 1
                if prev_sha is not None and sha != prev_sha:
                    markers["prompt_change_turns"] += 1
                prev_sha = sha
    return {
        "turn_rows": len(turns), "turn_first": min(turns) if turns else None,
        "turn_last": max(turns) if turns else None,
        "prompt_tokens_max": max(prompts) if prompts else None,
        "wall_ms_mean": round(sum(wall) / len(wall), 1) if wall else None,
        "wall_ms_p50": pct(wall, .5), "wall_ms_p90": pct(wall, .9),
        "wall_ms_max": max(wall) if wall else None,
        "turns_over_180s": sum(1 for w in wall if w > 180000),
        "ttft_ms_p50": pct(ttft, .5), "ttft_ms_p95": pct(ttft, .95),
        "ttft_n": len(ttft),
        "prompt_tokens_first": prompts[0] if prompts else None,
        "prompt_tokens_last": prompts[-1] if prompts else None,
        "degenerate_stop_turns": degenerate_stop_turns,
        "markers": markers,
    }


# PRECONDITION-10-SCOPE: ONE data table, ONE rule. Each arm is judged ONLY on its own
# treatment. `marker` is the row-counted witness, `threshold` how many of the cell's own
# turns must show it. `due` names the witness that says the treatment COULD have fired
# inside THIS cell's horizon: an absence the horizon makes impossible (a 12-turn cell
# cannot reach a wall declared for turn 23) proves nothing about the arm's label, so it
# is NOT-DUE, not a stop. A cell whose own treatment was due and did not fire still
# STOPS. A new arm is a row here, not another `if`.
ARM_TREATMENT = {
    "pointer-stable": {
        "marker": "prompt_change_turns", "threshold": 1,
        "due": "prompt_identity",
        "why": "pointer-stable is a stable prefix against a prefix change; a cell whose "
               "prompt identity never changed has no prefix dynamics to be stable against",
    },
    "transcript-grow": {
        "marker": "evicted_turns", "threshold": 1,
        "due": "wall",
        "why": "the grow treatment is FIFO eviction at the arm's wall",
    },
    "transcript-compact": {
        "marker": "digest_rows", "threshold": 1,
        "due": "wall",
        "why": "the compact treatment is the digest request at the arm's wall",
    },
    "lease-reopen": {
        "marker": "lease_ge2_turns", "threshold": 2,
        "due": "lease_turn",
        "why": "the lease treatment is the reopen step (>=2 occurrences)",
    },
    "A": {"marker": "evicted_turns", "threshold": 1, "due": "wall",
          "why": "A: evicted_turns > 0"},
    "B": {"marker": "digest_rows", "threshold": 1, "due": "wall",
          "why": "B: digest_rows > 0"},
    "C": {"marker": "masked_rows", "threshold": 1, "due": "wall",
          "why": "C: masked_rows > 0"},
    "D": {"marker": "fetch_rows", "threshold": 1, "due": "wall",
          "why": "D: fetch_rows > 0 and retrieval_outcomes non-empty"},
    "E": {"marker": "oracle_injections", "threshold": 1, "due": "wall",
          "why": "E: oracle_injections > 0"},
}


def _fixture_limits():
    """(wall_tokens_by_arm, lease_reopen_turns) read from the declared fixture.

    Never invents: an unreadable fixture returns ({}, []) and every `due` check then
    fails CLOSED (treated as due), so the guard can never be talked out of stopping by
    a missing fixture. Offline: reads one JSON file, sends nothing.
    """
    try:
        sys.path.insert(0, os.path.join(ENG, "longrun"))
        import run_longrun  # the planner that owns the per-arm wall (fixture_for_arm)
        path = FIX if os.path.isabs(FIX) else os.path.join(ROOT, FIX)
        with open(path) as fh:
            fx = json.load(fh)
        walls, lease = {}, []
        for arm in ARM_TREATMENT:
            arm_fx = run_longrun.fixture_for_arm(fx, arm)
            walls[arm] = int(arm_fx.get("wall_tokens") or 0)
        lease = [int(t) for t in (fx.get("lease_reopen_turns") or [])]
        return walls, lease
    except Exception:
        return {}, []


def treatment_due(arm, stats):
    """Could this arm's own treatment have fired INSIDE this cell? Fail closed (True)."""
    spec = ARM_TREATMENT.get(arm)
    if not spec:
        return True
    kind = spec["due"]
    markers = stats.get("markers") or {}
    if kind == "prompt_identity":
        return (markers.get("prompt_identity_turns") or 0) >= 2
    walls, lease = _fixture_limits()
    if kind == "wall":
        wall = walls.get(arm) or 0
        if not wall:
            return True
        return (stats.get("prompt_tokens_max") or 0) >= wall
    if kind == "lease_turn":
        if not lease:
            return True
        return (stats.get("turn_last") or 0) >= min(lease)
    return True


def precondition10(arm, stats):
    """-> (verdict, detail): 'fired' | 'not-due' | 'missing' for ONE cell, per arm.

    Data-driven by ARM_TREATMENT. `missing` is the ONLY stop: the arm's own treatment
    was due inside this cell and its own marker is below its own threshold. Other arms'
    markers are reported in `detail` but never consulted.
    """
    spec = ARM_TREATMENT.get(arm)
    markers = stats.get("markers") or {}
    if not spec:
        return "missing", {"arm": arm, "marker": None, "count": 0, "threshold": None,
                           "reason": "no ARM_TREATMENT row for this arm", "markers": markers}
    n = markers.get(spec["marker"], 0) or 0
    detail = {"arm": arm, "marker": spec["marker"], "count": n,
              "threshold": int(spec["threshold"]), "due": spec["due"],
              "markers": markers}
    if n >= int(spec["threshold"]):
        return "fired", detail
    if not treatment_due(arm, stats):
        return "not-due", detail
    return "missing", detail


def _analyze_stats_module():
    """The consumer module that owns the stamp writer (import, never reimplement)."""
    sys.path.insert(0, os.path.join(ENG, "longrun"))
    import analyze_stats
    return analyze_stats


def cell_stamp(rec):
    """-> (usable_for, reason) for one finished cell. The DECISION only, no write.

    Complete cell -> the declared analyses (h1, h2, h3) and a reason naming the
    evidence. Abandoned / zero-marker / stop_reason-degenerate -> `[]` PLUS the
    condition that fired, so an empty stamp is never confusable with an absent one.
    The `usable_for` KEY is created by analyze_stats.write_cell_manifest_usable_for;
    this function returns a tuple and constructs no manifest field of its own.
    """
    st = rec.get("stats") or {}
    markers = st.get("markers") or {}
    turns = st.get("turn_rows") or 0
    expected = rec.get("turns")
    if rec.get("rc") != 0:
        return [], "abandoned: cell.py exited rc=%s" % rec.get("rc")
    if not turns or (expected and turns < expected):
        return [], ("abandoned: %s of %s turn rows written"
                    % (turns, expected))
    degen = st.get("degenerate_stop_turns") or 0
    if degen:
        return [], ("stop_reason-degenerate: %d turn(s) ended runaway_turn/turn_wall_cap"
                    % degen)
    need = {"transcript-grow": "evicted_turns",
            "transcript-compact": "digest_rows",
            "lease-reopen": "lease_ge2_turns"}.get(rec.get("arm"))
    if need and not (markers.get(need) or 0):
        return [], "zero-marker: %s=0 for arm %s" % (need, rec.get("arm"))
    return list(GRID_USABLE_ANALYSES), (
        "complete: %d/%d turn rows, markers=%s"
        % (turns, expected, json.dumps(markers, sort_keys=True)))


def stamp_cell(rec):
    """Stamp one finished cell through analyze_stats' writer. -> stamp record.

    Called once per cell after the run, before the journal line, so the manifest on
    disk carries the stamp before the launcher can consider the next cell.
    """
    rows_file = rec.get("rows_file")
    manifest_path = rec.get("manifest_path")
    if not rows_file or not manifest_path:
        return None
    usable_for, reason = cell_stamp(rec)
    analyze_stats = _analyze_stats_module()
    analyze_stats.write_cell_manifest_usable_for(
        os.path.join(ROOT, rows_file), usable_for, reason=reason,
        manifest_path=manifest_path)
    return {"usable_for": usable_for, "reason": reason,
            "manifest_path": manifest_path}


def check_previous_stamp(rec, next_cell):
    """Refuse to start `next_cell` when the previous cell's manifest shows no stamp.

    The stamp must be ON DISK, not merely in the launcher's record: a grid that
    trusts its own memory cannot prove the analyser will exclude an unusable cell.
    Exit 4 names the manifest path, so the refusal survives this process.
    """
    manifest_path = rec.get("manifest_path")
    if not manifest_path:
        message = (
            "REFUSED to start cell %s: previous cell %s (%s r%s) produced no rows "
            "file and no cell manifest, so an unstamped cell cannot be shown to be "
            "excluded" % (next_cell, rec.get("cell"), rec.get("arm"), rec.get("rep")))
    else:
        path = manifest_path if os.path.isabs(manifest_path) \
            else os.path.join(ROOT, manifest_path)
        if not os.path.exists(path):
            message = (
                "REFUSED to start cell %s: previous cell's manifest %s does not "
                "exist, so its usable_for stamp cannot be shown" % (next_cell, path))
        else:
            with open(path, encoding="utf-8") as fh:
                man = json.load(fh)
            if "usable_for" in man:
                return None
            message = (
                "REFUSED to start cell %s: previous cell's manifest %s lacks the "
                "usable_for key -- an unstamped cell is INCLUDED by analyze_stats.py:749, "
                "so the grid stops rather than spend a request that could enter H1/H2/H3"
                % (next_cell, path))
    sys.stderr.write(message + "\n")
    raise SystemExit(EXIT_UNSTAMPED_CELL)


# LAUNCH-CANARY-WALL: the canary's wall must clear its own projection. G2 bills
# projected_requests x projected_turn_wall = 12 x 60.0 s = 720 s at the artefact-mode
# calibration (PROJECTION.json, thinking=off), so the historical 600 s default
# WOULD-REFUSED before request 1 (orchestration/handoffs/CANARY-GATE-DRYRUN.json).
# 900 s = the 720 s floor + 25% headroom (75 s/turn), still far below the grid's
# 2880 s and below 12 x 180 s worst case. The projection and the 60.0 s calibration
# are NOT touched and the grid keeps its own 2880 s default byte-identically.
CANARY_MAX_WALL = 900

# DRYRUN-REFUSAL: only a gate VERDICT line is a refusal. cell.py's closing line
# mentions the words "WOULD-REFUSE verdict lines" while allowing, so matching the
# bare token would make every dry run look refused.
_GATE_WOULD_REFUSE = re.compile(r"dry-run G[123] WOULD-REFUSE\b")


def cell_argv(arm, rep, hypothesis="H2", turns=48, max_wall=2880):
    """The exact frozen cell.py argv for one cell. `tools` rides the env, not here.

    CANARY-ARGV-WIRING: the claim is a PARAMETER, not a literal. ``hypothesis`` is the
    single value ``cell.py`` resolves through ``claim_mode.resolve_claim``
    (cell.py:1311-1325) and forwards to the runner as ``--claim-mode``
    (cell.py:1590-1594), so:

      * a grid cell (the default ``"H2"``) is byte-identical to the pre-wiring argv;
      * a canary passes ``"smoke"`` -> every row is written ``claim: "none"`` /
        ``comparison_eligible: false`` and ``analyze_stats.py`` refuses it BY NAME
        (``incomparable_claim``) instead of pooling it into an arm.

    ``turns`` / ``max_wall`` are parameters for the same reason: a 12-turn canary
    cannot borrow the grid's 48-turn / 2880 s shape without ceasing to be a canary.
    """
    return [sys.executable, CELL, "--arm", arm, "--fixture", FIX,
            "--turns", str(turns),
            "--reps", "1", "--thinking", "off", "--max-wall", str(max_wall),
            "--turn-wall-cap", "180", "--runaway-turns", "2", "--budget", "108",
            "--hypothesis", hypothesis,
            # HARNESS-PIN-WIRING: without this flag cell.py:336-349 refuses nothing,
            # so the 1,016-request launch would run against bytes nobody pinned.
            "--expect-harness", pinned_digest(),
            "--no-cell-handoff",
            "--out-dir", "experiments/ptr-engine/measure",
            "--endpoint", ENDPOINT]


def claim_mode_of(hypothesis):
    """The claim this cell will DECLARE, named from its own argv value.

    CANARY-ARGV-WIRING: one reader for the launcher's record, so a canary cannot be
    logged as an H2 cell. The decision itself stays ``claim_mode.resolve_claim``'s.
    """
    sys.path.insert(0, os.path.join(ENG, "longrun"))
    import claim_mode
    rec = claim_mode.resolve_claim(hypothesis)
    return {"mode": rec.mode, "claim": rec.claim,
            "comparison_eligible": rec.comparison_eligible}


def child_env(tools):
    env = os.environ.copy()
    if tools:
        env["CELL_RUNNER_PATH"] = ensure_shim()
    else:
        env.pop("CELL_RUNNER_PATH", None)
    return env


def run_cell(arm, rep, n, tools="", budget=108, hypothesis="H2", dry_run=False,
             turns=48, max_wall=2880):
    before = set(os.listdir(MEAS))
    log = os.path.join(LOGDIR, "cell%02d-%s-r%d.log" % (n, arm, rep))
    argv = cell_argv(arm, rep, hypothesis, turns, max_wall)
    if tools:
        # G1 must price the fetch channel: at most 48 follow-up requests per arm.
        argv += ["--fetch-followup-allowance", str(FETCH_ALLOWANCE)]
    if dry_run:
        argv += ["--dry-run"]
    t0 = time.time()
    proc = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, env=child_env(tools))
    dur = round(time.time() - t0, 1)
    out = (proc.stdout or "")
    with open(log, "w") as fh:
        fh.write(out)
    new = sorted(set(os.listdir(MEAS)) - before)
    rows = [x for x in new if x.startswith("rows-") and x.endswith(".jsonl")]
    rec = {"cell": n, "arm": arm, "rep": rep, "rc": proc.returncode, "dur_s": dur,
           "tools": tools or "off", "budget": budget, "hypothesis": hypothesis,
           "turns": turns, "max_wall": max_wall,
           "claim_mode": claim_mode_of(hypothesis),
           "argv": " ".join(argv),
           "rows_file": rows[0] if len(rows) == 1 else None,
           "new_files": new,
           "gates": [ln.strip() for ln in out.splitlines()
                     if " G1 " in ln or " G2 " in ln or " G3 " in ln],
           # LAUNCH-CANARY-WALL: a gate's WOULD-REFUSE verdict needs its own key
           # because cell.py's dry run exits 0 on it by design (cell.py:1964-1975:
           # "exit 0 means the PREVIEW ran, not that the gates allow"), so rc alone
           # can never carry a refusal.
           "would_refuse": [ln.strip() for ln in out.splitlines()
                            if _GATE_WOULD_REFUSE.search(ln)],
           "stdout_tail": out.strip().splitlines()[-8:]}
    if len(rows) == 1:
        rows_path = os.path.join(MEAS, rows[0])
        rec["stats"] = rows_stats(rows_path)
        stamp = rows[0].replace("rows-cell-", "").replace(".jsonl", "")
        man = os.path.join(MEAS, "cell-%s.json" % stamp)
        rec["manifest_path"] = "experiments/ptr-engine/measure/cell-%s.json" % stamp
        if os.path.exists(man):
            m = json.load(open(man))
            rec["record_path"] = "experiments/ptr-engine/measure/cell-%s.json" % stamp
            ef = m.get("engine_flags") or (m.get("run") or {}).get("engine_flags") or {}
            rec["design_cap_tokens"] = ef.get("design_cap_tokens")
            rec["tools_in_manifest"] = (m.get("tools") or {}).get("names")
            # GRID-STAMP-WIRING: the stamp lands on disk HERE, before the journal
            # line and before the next cell can start. A dry run never writes.
            if not dry_run:
                rec["usable_for_stamp"] = stamp_cell(rec)
        an = os.path.join(MEAS, "cell-%s.analysis.json" % stamp)
        if os.path.exists(an):
            a = json.load(open(an))
            arms = a.get("arms") or {}
            if arms:
                one = list(arms.values())[0]
                rec["analysis"] = {"p50": one.get("p50"), "p95": one.get("p95"),
                                   "accuracy": one.get("accuracy"),
                                   "n_rows": one.get("n_rows")}
        gr = os.path.join(MEAS, "cell-%s.grade-v5.json" % stamp)
        if os.path.exists(gr):
            rec["grade_path"] = "experiments/ptr-engine/measure/cell-%s.grade-v5.json" % stamp
    rec["treatment_preflight"] = [
        ln.strip() for ln in out.splitlines()
        if ("prefix change at turn" in ln or "FIFO truncation" in ln
            or "first wall" in ln or "lease step" in ln)]
    return rec


def h3_veto(grade_a, grade_b):
    def load(p):
        d = json.load(open(p))
        return {c["id"]: c.get("verdict") for c in d.get("cells", [])}
    A, B = load(grade_a), load(grade_b)
    ids = sorted(set(A) & set(B))
    b = sum(1 for i in ids if A[i] != "pass" and B[i] == "pass")
    c = sum(1 for i in ids if A[i] == "pass" and B[i] != "pass")
    n = b + c
    p = 0.0
    if n:
        p = min(1.0, 2 * sum(comb(n, i) for i in range(0, min(b, c) + 1)) / (2 ** n))
    return {"paired": len(ids), "b": b, "c": c, "p": round(p, 6),
            "transcript_worse": c > b,
            "veto": bool(n >= 6 and p < 0.05 and c > b)}


def main():
    global FIX
    ap = argparse.ArgumentParser(description="RUN-A* / GRID-SHAPE driver")
    ap.add_argument("--tools", default="", metavar="LIST",
                    help="tool channel(s) to enable through the shim; '' (default) = "
                         "the historical tools-off launch, unchanged; 'read_file' = "
                         "the GRID-SHAPE corrected shape")
    ap.add_argument("--cell", type=int, default=0,
                    help="run only cell N (1..%d); 0 = the whole grid in order"
                         % len(CELLS))
    ap.add_argument("--dry-run", action="store_true",
                    help="pass --dry-run to every cell.py launch and send nothing")
    ap.add_argument("--budget", type=int, default=108,
                    help="per-cell ledger allocation handed to cell.py (default 108); the stage 3/7 gate compares ceil(would_send_total x 1.10) against it, so this is a ledger allocation, not a request ceiling")
    ap.add_argument("--hypothesis", default=None,
                    metavar="H1|H2|H3|smoke|plumbing",
                    help="the claim every cell declares (default H2; the canary spells "
                         "smoke, which makes no claim and can never be pooled)")
    ap.add_argument("--canary", action="store_true",
                    help="the 12-turn era-B canary: ONE 12-turn cell per arm "
                         f"(4 arms = 48 requests), --hypothesis smoke, --max-wall {CANARY_MAX_WALL} "
                         "(RUN-A-STAR-2's gate before the grid)")
    ap.add_argument("--max-wall", type=float, default=None,
                    help="per-cell wall ceiling handed to cell.py "
                         f"(default 2880; {CANARY_MAX_WALL} when --canary)")
    ap.add_argument("--fixture", default=FIX,
                    help="fixture path, repo-relative (default: the v8 LR-01 grid fixture)")
    a = ap.parse_args()
    FIX = a.fixture
    # LAUNCHER-GEN5-WIRE: both records are GATES and they fire before any plan is
    # built, so a launcher that cannot read (or does not agree with) its records
    # never reaches the cell loop -- and never prints a plan as if it could.
    pinned_digest()
    grid_record()
    # CANARY-ARGV-WIRING: the claim is resolved ONCE, here, and lands in the argv.
    if a.canary:
        a.hypothesis = a.hypothesis or "smoke"
        a.max_wall = CANARY_MAX_WALL if a.max_wall is None else a.max_wall
        a.turns = 12
        # CANARY-ARMS-WIRING: one 12-turn cell per arm. The priced component is
        # 4 x 12 = 48 requests. The canary used to be `a.cell = a.cell or 1` -- ONE
        # arm -- so pointer-stable was gated and the other three reached the grid
        # ungated. --cell no longer narrows the canary; it is ignored with a note.
        cells = [(n, arm, rep) for n, (arm, rep) in enumerate(CELLS, 1) if rep == 1]
        if a.cell:
            say("canary ignores --cell %d: the canary is one 12-turn cell per arm "
                "(arms=%d cells=%s turns=%d requests=%d)"
                % (a.cell, len(cells), ",".join(str(c[0]) for c in cells),
                   a.turns, len(cells) * a.turns))
    else:
        a.hypothesis = a.hypothesis or "H2"
        a.max_wall = 2880 if a.max_wall is None else a.max_wall
        a.turns = 48
        cells = [(n, arm, rep) for n, (arm, rep) in enumerate(CELLS, 1)
                 if not a.cell or n == a.cell]
    if a.tools and a.tools != "read_file":
        raise SystemExit("unsupported --tools %r; run_longrun.py supports read_file "
                         "only (run_longrun.py:2798)" % a.tools)
    if not cells:
        raise SystemExit("--cell must be 1..%d" % len(CELLS))
    canary_requests = len(cells) * a.turns if a.canary else 0
    if a.canary:
        say("canary arms=%d cells=%s turns=%d requests=%d claim=%s"
            % (len(cells), ",".join(str(c[0]) for c in cells), a.turns,
               canary_requests, a.hypothesis))
    if a.tools:
        say("tools=%s shim=%s" % (a.tools, ensure_shim()))
    if a.dry_run:
        # OFFLINE: cell.py --dry-run prints G1/G2/G3 and sends nothing.
        # DRYRUN-REFUSAL (LAUNCH-CANARY-WALL): cell.py's dry run always exits 0 --
        # its own documented contract is that "exit 0 means the PREVIEW ran, not that
        # the gates allow" (cell.py:1964-1975, docs/GATE-CHAIN.md §7). Counting `rc`
        # alone therefore printed `refused=0` for a canary whose G2 line said
        # `WOULD-REFUSE`, i.e. a blocked launch reported green. A gate's WOULD-REFUSE
        # verdict is the refusal: it counts, and it makes the launcher exit non-zero.
        # Exit 1 is the code this launcher already uses for a dry run that saw a cell
        # fail (`return 0 if not bad else 1`); 2 stays cell.py's preflight/G3 code
        # (cell.py:14-15, exit_codes.EXIT_TABLE) and is not the launcher's to reuse.
        bad = 0
        # LAUNCHER-GEN5-WIRE: the price comes from the record and is printed BEFORE
        # any cell is previewed, beside the remaining figure it is drawn from, so the
        # dry run and the record cannot disagree in opposite directions. A record
        # without price.total refuses by name (grid_record), never a blank line.
        _rem, _basis, _cap = remaining_basis()
        say(price_line(_rem, _basis, _cap, cells=len(cells)))
        for n, arm, rep in cells:
            rec = run_cell(arm, rep, n, a.tools, a.budget, a.hypothesis,
                           dry_run=True, turns=a.turns, max_wall=a.max_wall)
            refused = bool(rec["would_refuse"])
            say("DRY cell %d %s r%d rc=%s%s %s"
                % (n, arm, rep, rec["rc"],
                   " WOULD-REFUSE=%d" % len(rec["would_refuse"]) if refused else "",
                   " | ".join(rec["gates"]) or "no gate line"))
            bad += 1 if (rec["rc"] != 0 or refused) else 0
        say("DRY END cells=%d refused=%d requests=0 claim=%s turns=%d max_wall=%s "
            "canary_arms=%d canary_requests=%d" %
            (len(cells), bad, a.hypothesis, a.turns, a.max_wall, len(cells),
             canary_requests))
        return 0 if not bad else 1
    spent0 = spend()
    base_remaining, rem_basis, rem_cap = remaining_basis()
    say(price_line(base_remaining, rem_basis, rem_cap, cells=len(cells)))
    results, warm, stops = [], {}, []
    say("start spent_rows=%d cells=%d fixture=%s tools=%s canary=%s claim=%s "
        "turns=%d max_wall=%s remaining_basis=%s" %
        (spent0, len(cells), FIX, a.tools or "off", a.canary, a.hypothesis,
         a.turns, a.max_wall, rem_basis))
    jline(event="grid_start", spent_rows=spent0, cells=len(cells),
          budget_per_cell=a.budget, hypothesis=a.hypothesis, tools=a.tools or "off",
          canary=a.canary, turns_per_cell=a.turns, max_wall=a.max_wall,
          canary_requests=canary_requests,
          wall_cap_expected=CAP_WALL, fetch_allowance=FETCH_ALLOWANCE if a.tools else 0)
    for n, arm, rep in cells:
        remaining = base_remaining - (spend() - spent0)
        if remaining < 264:
            stops.append({"rule": 1, "remaining": remaining, "before_cell": n})
            say("STOP rule 1: remaining=%d" % remaining)
            jline(event="stop_rule_1", remaining=remaining, before_cell=n)
            break
        # GRID-STAMP-WIRING: the previous cell must SHOW its stamp before this cell
        # is allowed to spend a request (exit 4, naming the manifest path).
        if results:
            check_previous_stamp(results[-1], n)
        if rep == 1 and arm not in warm:
            warm[arm] = warmup(arm)
        rec = run_cell(arm, rep, n, a.tools, a.budget, a.hypothesis,
                       turns=a.turns, max_wall=a.max_wall)
        rec["remaining_after"] = base_remaining - (spend() - spent0)
        rec["warmup_ms"] = warm.get(arm)
        results.append(rec)
        jline(event="cell", **{k: rec.get(k) for k in
                               ("cell", "arm", "rep", "rc", "dur_s", "rows_file",
                                "design_cap_tokens", "tools_in_manifest", "stats",
                                "analysis", "treatment_preflight", "remaining_after",
                                "usable_for_stamp")})
        save(results, {"spent_rows_before": spent0, "warmups": warm, "stops": stops,
                       "tools": a.tools or "off", "budget_per_cell": a.budget,
                       "hypothesis": a.hypothesis})
        ar = rec.get("analysis") or {}
        say("CELL %d %s r%d rc=%s dur=%ss remaining=%s p95=%s acc=%s markers=%s" % (
            n, arm, rep, rec["rc"], rec["dur_s"], rec["remaining_after"],
            (ar.get("p95") or {}).get("point"), ar.get("accuracy"),
            (rec.get("stats") or {}).get("markers")))
        if rec["rc"] != 0:
            stops.append({"rule": 7, "cell": n, "rc": rec["rc"]})
            say("STOP rule 7: cell %d exited %s" % (n, rec["rc"]))
            jline(event="stop_rule_7", cell=n, rc=rec["rc"], tail=rec["stdout_tail"])
            break
        if rec.get("design_cap_tokens") not in (None, CAP_WALL):
            stops.append({"rule": "wall-source", "cell": n,
                          "design_cap_tokens": rec.get("design_cap_tokens")})
            say("STOP wall source: %r" % rec.get("design_cap_tokens"))
            break
        if a.tools and rec.get("tools_in_manifest") not in (None, ["read_file"]):
            stops.append({"rule": "tools-not-on-the-wire", "cell": n,
                          "tools_in_manifest": rec.get("tools_in_manifest")})
            say("STOP tools not on the wire: %r" % rec.get("tools_in_manifest"))
            jline(event="stop_tools_missing", cell=n,
                  tools_in_manifest=rec.get("tools_in_manifest"))
            break
        if rep == 1:
            m = (rec.get("stats") or {}).get("markers") or {}
            # PRECONDITION-10-SCOPE: judged ONLY on this arm's own treatment (data table
            # ARM_TREATMENT). Other arms' markers appear in the detail, never in the rule.
            verdict, detail = precondition10(arm, rec.get("stats") or {})
            if verdict == "missing":
                stops.append({"rule": "precondition-10", **detail})
                say("STOP precondition 10: %s cell 1 own treatment %s=%s < %s %s"
                    % (arm, detail["marker"], detail["count"],
                       detail["threshold"], m))
                jline(event="stop_mislabel", **detail)
                break
            if verdict == "not-due":
                say("PRECONDITION 10 not due: %s own marker %s is outside this cell's "
                    "horizon (cell continues)" % (arm, detail["marker"]))
                jline(event="precondition10_not_due", **detail)
        if n == 4:
            ga = [x for x in results if x["arm"] == "pointer-stable" and x["rep"] == 1][0]
            gb = [x for x in results if x["arm"] == "transcript-grow" and x["rep"] == 1][0]
            if ga.get("grade_path") and gb.get("grade_path"):
                v = h3_veto(os.path.join(ROOT, ga["grade_path"]),
                            os.path.join(ROOT, gb["grade_path"]))
                say("H3 rep-1 %s" % json.dumps(v))
                jline(event="h3_rep1", **v)
                if v["veto"]:
                    stops.append({"rule": 4, **v})
                    say("STOP rule 4: H3 veto at rep 1")
                    break
    spent1 = spend()
    save(results, {"spent_rows_before": spent0, "spent_rows_after": spent1,
                   "new_requests": spent1 - spent0,
                   "remaining": base_remaining - (spent1 - spent0),
                   "remaining_basis": rem_basis, "remaining_cap": rem_cap,
                   "warmups": warm,
                   "stops": stops, "cells_planned": len(cells),
                   "tools": a.tools or "off", "budget_per_cell": a.budget,
                   "hypothesis": a.hypothesis})
    jline(event="grid_end", cells_run=len(results), spent_rows_before=spent0,
          spent_rows_after=spent1, new_requests=spent1 - spent0,
          remaining=base_remaining - (spent1 - spent0), remaining_basis=rem_basis,
          remaining_cap=rem_cap, warmups=warm, stops=stops)
    say("END cells=%d new_requests=%d remaining=%d remaining_basis=%s cap=%s "
        "stops=%s" % (len(results), spent1 - spent0,
                    base_remaining - (spent1 - spent0), rem_basis, rem_cap, stops))
    return 0


if __name__ == "__main__":
    sys.exit(main())


# Activation predicates (gate 0.6) for the five context arms.
ACTIVATION_PREDICATES = {
    "A": "evicted_turns > 0",
    "B": "digest_rows > 0",
    "C": "masked_rows > 0",
    "D": "fetch_rows > 0 and retrieval_outcomes non-empty",
    "E": "oracle_injections > 0",
}


def activation_predicate(arm, stats):
    markers = (stats or {}).get("markers") or {}
    arm = str(arm or "").strip().upper()
    if arm == "A":
        return (markers.get("evicted_turns") or 0) > 0
    if arm == "B":
        return (markers.get("digest_rows") or 0) > 0
    if arm == "C":
        return (markers.get("masked_rows") or 0) > 0
    if arm == "D":
        return ((markers.get("fetch_rows") or 0) > 0
                and (markers.get("retrieval_outcomes") or 0) > 0)
    if arm == "E":
        return (markers.get("oracle_injections") or 0) > 0
    return False
