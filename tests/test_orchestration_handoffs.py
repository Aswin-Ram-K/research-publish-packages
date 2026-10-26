"""Guard: every orchestration/handoffs/*.json must parse and carry its contracted shape.

Added by unit U8.15. The build lost a recovery cycle because
orchestration/handoffs/U0.22.json declared "status":"done" but was not valid JSON
("Expecting ',' delimiter: line 6 column 32"), so nothing could machine-read it.

Reconciled by unit U8.18 with the measured record
-------------------------------------------------
U8.15's sweep recorded that 45 of 137 parseable handoffs omitted >=1 of the 7 unit
contract keys, "almost all V* verifier handoffs use a verdict shape". U8.18 measured the
real files (148 handoffs, 0 parse failures, 43 of them V*-prefixed) and named the second
shape instead of demanding 45 rewrites. See AGENTS.md, unit contract rule 5.

Concurrent-write handling: a BOUNDED SETTLE LOOP (U8.35)
--------------------------------------------------------
A sibling unit may be writing its handoff while this test lists the directory.
A single write() of a few KB is not atomic, so a read can catch a torn prefix
(valid JSON prefix + missing tail, or truncated braces).

U8.25's guard re-read the file IMMEDIATELY on failure and treated "bytes differ"
as mid-write.  V8.29 measured that this is not enough: a file caught mid-flush can
present the SAME partial bytes to two back-to-back reads, so it looks settled, is
parsed, and its JSONDecodeError becomes a HARD failure for a state that was never a
defect.  That recurred live in one wave (V8.27.json 09:44, U8.28.json 09:47) and made
the full-file result irreproducible on the busy corpus (9 passed / 1 failed).

So the read is `_read_until_settled`, and it separates THREE outcomes:
  1. a document that parses to an OBJECT is accepted at once -- no pause is paid,
     which is why the 170+ healthy handoffs cost nothing;
  2. otherwise the file is re-read across up to SETTLE_MAX_ATTEMPTS pauses of
     SETTLE_DELAY_S.  If it becomes readable it is JUDGED ON ITS SETTLED BYTES;
  3. if it is still unreadable when the bound runs out, the bytes decide which
     thing it is: NEVER MOVED across the whole bound == a SETTLED defect, and it
     is still a HARD failure (the U0.22 class, unchanged in force); MOVED at any
     point during the watch (or still moving at the bound) == an unfinished write,
     recorded as UNSTABLE -- a skip with a reason (mid_write + skip_reason), never
     a parse failure, because an unfinished write is not a defect.

THE OVERSTATEMENT THIS CORRECTS (U8.35).  The old claim -- "a torn read is not
[stable], so the guard does not flicker" -- was too strong, for exactly V8.29's
reason: a torn file whose writer pauses for longer than the window presents the
same bytes to every read, looks settled, and is still reported as a defect.  The
loop does NOT remove that exposure and this docstring no longer says it does; no
finite window can outlast a writer that pauses longer than the window.  What IS now
true: the window is a real pause instead of two back-to-back syscalls, and a file
that MOVES at all during the watch can never become a hard failure.  SETTLE_DELAY_S
and SETTLE_MAX_ATTEMPTS are therefore a LATENCY budget, not a correctness one.

Recorded residual exposure (deliberate, not hidden): a tear that leaves a VALID but
incomplete JSON object (so it parses and is accepted on the first read) is not
caught by this loop.  It is not caught by the old one either, closing it would make
every known baseline-gap file pay the pause on every run, and a truncation of a JSON
document essentially never yields a parseable object.
We still do not use mtime windows (they would silently exempt a file that is old
but broken).

Two shapes, one guard (U8.18)
-----------------------------
Shape is decided per file by `classify()`: a filename starting with "V", or a document
carrying a "verdict"/"overall" key, is a **verifier verdict** judged against the verifier
contract; anything else is a **unit handoff** judged against CONTRACT (the identical 7
keys U8.15 froze).  Both contracts are asserted against FROZEN baselines of pre-existing
gaps: state/logs/U8.15/baseline_gaps.json for the unit shape (U8.15) and
state/logs/U8.18/verifier_shape_baseline.json for the verifier shape (U8.18).  Any NEW
file or any NEW missing required key fails; the historical gaps are recorded, not invented
away (the values were never fabricated to satisfy the contract).

One source of truth per baseline, hash-pinned (U8.25)
----------------------------------------------------
U8.15 and U8.18 each recorded their sweep in a JSON file AND inline in this test, and this
test asserted `inline == file`.  That is **copy == copy**: two derived artifacts that agree
perfectly even when BOTH are wrong.  U8.22 found V6E.json's recorded gap under-declared in
exactly that way, and the assertion could not see it -- it compared the two copies, never
either copy against the measurement.  A check that compares two derived artifacts cannot
detect a derivation error.

So the inline copies are GONE.  Each baseline JSON is now the SOLE source of its record,
and each is integrity-checked two ways:

  * (b) its sha256 is pinned by a constant below, so ANY edit -- a repair or a
    transcription slip -- fails the suite unless the pin is edited too.  A silent change
    to one place is impossible; a deliberate change is visible in two.  (This is the sha
    pattern this build already uses for release artifacts, e.g. run.py's 106661a2...)
  * (c-tightening) it is checked against the LIVE measurement, not against another copy:
    `test_no_baseline_entry_over_declares` fails when an exemption claims MORE than the
    current corpus needs.  That direction cannot be a tautology: the exemptions live in a
    pinned FILE while the measurement comes from the handoffs on disk, so the two can
    disagree -- and they did (V5.25.json, and U8.15's 41 dead V* entries).
    What is deliberately NOT done is re-deriving the baseline from live data: the record
    of PRE-EXISTING gaps must stay frozen or the known gaps would be re-absolved on every
    run.  Live gaps are still compared against the frozen baseline for NEW/WORSENED gaps
    (test_no_new_contract_key_gaps), which is what catches a newly incomplete handoff.

RED evidence captured by U8.18 (scratch fixtures, new classifier)
-----------------------------------------------------------------
  [A] broken JSON  ->
      {'U0.22.json': "JSONDecodeError: Expecting ',' delimiter: line 2 column 1 (char 96)"}
  [B] missing key (unit shape)  ->
      {'U0.22.json': {'shape': 'unit', 'missing': ['blocker', 'next_unit_hint', 'write_paths']}}
  [C] missing key (verifier shape)  ->
      {'V9.99.json': {'shape': 'verifier',
                      'missing': ['overall', 'next_unit_hint']}}
A broken handoff is a parse failure ([A]); a merely incomplete one is a key gap ([B],[C]).
Both are reported, neither is tolerated.
"""
import hashlib, json, pathlib, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
HANDOFFS = ROOT / "orchestration" / "handoffs"

# The UNIT shape is a SPECIFICATION, not a measurement: it appears exactly once, here and
# in AGENTS.md unit-contract rule 5.  There is no recorded copy of it to duplicate against,
# so it stays inline -- duplicating a value in two places is the hazard, not defining it.
CONTRACT = ["unit", "status", "artifacts", "evidence", "blocker", "next_unit_hint", "write_paths"]

# ---------------------------------------------------------------------------
# FROZEN BASELINES -- sole sources, each pinned by sha256 (U8.25)
# ---------------------------------------------------------------------------
BASELINE_GAPS_PATH = ROOT / "state" / "logs" / "U8.15" / "baseline_gaps.json"
BASELINE_GAPS_SHA256 = "d25e5bcc7659b50735136b20d37ac613d9884608c993ce57efe01af4b6a368d9"

VERIFIER_BASELINE_PATH = ROOT / "state" / "logs" / "U8.18" / "verifier_shape_baseline.json"
VERIFIER_BASELINE_SHA256 = "5f8bbd359fe922b55f7fc491ee7073742b52b5153d17bd5c52a690310154ae72"

# A handoff must declare its outcome; a verifier declares it with 'overall'.  U8.25 removed
# the 13-file BASELINE_NO_STATUSISH exemption: it was measured as protecting NOTHING (zero
# handoffs lack such a key) and its keeper assertion was a tautology
# (set(list) == set(frozenset(list)) always holds), so it would have silently tolerated one
# of those files losing its status.  Every handoff must now declare its outcome.
STATUSISH = ("status", "verdict", "result", "overall")


# ---------------------------------------------------------------------------
# The settle budget for a suspect (unreadable) handoff -- see the module docstring.
# ---------------------------------------------------------------------------
# 200 ms between the compared reads: three orders of magnitude longer than the time
# a few-KB write needs to become visible here (handoffs are 16-23 KB and a full
# rewrite lands well inside one scheduling slice), so a writer that has genuinely
# finished is seen to have finished, and "identical across reads" stops meaning
# "identical across one syscall gap".
# 4 pauses at most (~0.8 s watched) keeps the whole observation sub-second, because
# the cost only ever falls on SUSPECT files: a healthy or merely incomplete-but-
# parseable handoff takes the zero-delay fast path.  Lengthening the window does not
# buy safety -- exhaustion for a file that MOVED is already a skip, and a file that
# never moved is a settled defect at 0.8 s exactly as it was at 0 ms -- so the bound
# is spent on latency, not on correctness.
SETTLE_DELAY_S = 0.2
SETTLE_MAX_ATTEMPTS = 4


def _pinned_json(path, expected_sha256, label):
    """Read `path` as the SOLE source of `label`, refusing any byte drift from the pin.

    The failure is deliberate and verbatim: a changed baseline is not quietly accepted, and
    a transcription slip cannot masquerade as a legitimately recorded gap.
    """
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == expected_sha256, (
        "%s changed on disk: sha256 %s != pinned %s. This file is the SOLE source of its "
        "record; if the edit is deliberate, update the pin in this test too -- that second, "
        "visible edit is the point of the pin (a fix and a transcription slip are then the "
        "same kind of act). If it was NOT deliberate, restore the file."
        % (label, digest, expected_sha256))
    return json.loads(raw)


_BASELINES = {}


def frozen_baselines():
    """Return (unit_gaps, verifier_gaps, verifier_contract) from the two PINNED files.

    Nothing here is re-derived from the corpus: these are the frozen records of gaps that
    predate the guard, and re-deriving them would re-absolve every known gap.  What the
    corpus IS used for is the tightening direction (`test_no_baseline_entry_over_declares`)
    and the NEW/WORSENED direction (`test_no_new_contract_key_gaps`).
    """
    if not _BASELINES:
        unit = _pinned_json(BASELINE_GAPS_PATH, BASELINE_GAPS_SHA256, "U8.15 unit-shape baseline")
        ver = _pinned_json(VERIFIER_BASELINE_PATH, VERIFIER_BASELINE_SHA256, "U8.18 verifier-shape baseline")
        _BASELINES["unit_gaps"] = {k: list(v) for k, v in unit["gaps"].items()}
        _BASELINES["verifier_gaps"] = {k: list(v) for k, v in ver["gaps"].items()}
        # The verifier contract is a MEASUREMENT (keys carried by >=90% of the 43 V* files),
        # so its sole source is the pinned record -- an inline copy would be a second derived
        # artifact whose disagreement with the file proves nothing either way.
        _BASELINES["verifier_contract"] = list(ver["contract_verifier"])
    return _BASELINES["unit_gaps"], _BASELINES["verifier_gaps"], _BASELINES["verifier_contract"]


def classify(name, doc):
    """Return 'verifier' for a verifier verdict, else 'unit'.

    Discriminator: filename prefix "V" (the repo's verifier-unit naming, 43/43 V* files),
    corroborated by an explicit "verdict"/"overall" key so a verdict-shaped handoff that is
    not named V* is still read as a verdict.

    Failure mode (deliberate, fail-loud): an AMBIGUOUS file -- one classified as a verifier
    only because it carries "overall" while really being a unit report -- is then judged
    against the verifier contract, which requires `checks`.  A unit report normally has no
    `checks`, so it FAILS as a new gap rather than passing silently; the misclassification
    is loud, not quiet.  Conversely a V*-prefixed file is always judged as a verdict, even
    if it is really a unit report -- likewise loud (missing `overall`/`checks`).

    Consequence U8.25 acted on: a "V*" name can NEVER be judged as a unit handoff, so any
    V* entry in the unit baseline was unreachable text (41 of them were retired).
    """
    if name.startswith("V") or "overall" in doc:
        return "verifier"
    return "unit"


def required_keys(shape):
    if shape == "verifier":
        return frozen_baselines()[2]
    return CONTRACT


def _parse(raw):
    """Return (doc, error_string); error_string is None when raw is valid JSON."""
    try:
        return json.loads(raw), None
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)


def _read_until_settled(path, delay=SETTLE_DELAY_S, attempts=SETTLE_MAX_ATTEMPTS):
    """Read `path` until it is readable or stops moving.  Never raises.

    Replaces U8.25's immediate double-read, which skipped a file only when its bytes
    differed between two back-to-back reads; a mid-flush file can be byte-identical
    across those, look settled, and turn a transient state into a HARD failure
    (V8.29's measured defect).  The result is a small record:

      status 'settled'  -- the document parses to an object, OR the bytes never moved
                           across the whole bound (a genuinely settled defect, which
                           the caller still reports);
      status 'unstable' -- the bytes moved during the watch and the document never
                           became readable, or they were still moving at the bound.
                           The caller records a SKIP with a reason: an unfinished
                           write is not a defect.
    """
    def accepted(raw, doc, err, pauses, moved, quiet):
        return {"raw": raw, "doc": doc, "error": err, "status": "settled", "pauses": pauses,
                "moved": moved, "quiet": quiet, "delay": delay}

    raw = path.read_bytes()
    doc, err = _parse(raw)
    if err is None and isinstance(doc, dict):
        return accepted(raw, doc, None, 0, False, True)      # fast path: no pause paid
    moved, quiet = False, True
    for pause in range(attempts):
        time.sleep(delay)
        nxt = path.read_bytes()
        quiet = nxt == raw
        moved = moved or not quiet
        raw = nxt
        doc, err = _parse(raw)
        if err is None and isinstance(doc, dict):
            return accepted(raw, doc, None, pause + 1, moved, quiet)
    return {"raw": raw, "doc": doc, "error": err,
            "status": "unstable" if (moved or not quiet) else "settled",
            "pauses": attempts, "moved": moved, "quiet": quiet, "delay": delay}


def _skip_reason(record):
    """The verbatim reason a suspect file was SKIPPED rather than failed."""
    ms = int(record["delay"] * 1000)
    if not record["quiet"]:
        what = "still changing after %d pauses of %d ms" % (record["pauses"], ms)
    else:
        what = ("changed during the watch, then quiet but still unreadable after "
                "%d pauses of %d ms" % (record["pauses"], ms))
    return "%s (unfinished write, not a defect)" % what


def audit(directory=HANDOFFS):
    """Return the corpus audit.

    Keys: 'failures' (settled defects), 'gaps' ({name: missing keys}), 'shapes',
    'docs' (settled parsed objects, so no caller has to re-read a moving file),
    'mid_write' (the SKIP list: unfinished writes, torn or unstable) and
    'skip_reason' ({name: why it was skipped}).
    """
    failures, gaps, mid_write, shapes, reasons, retried, docs = [], {}, [], {}, {}, [], {}
    for path in sorted(pathlib.Path(directory).glob("*.json")):
        name = path.name
        record = _read_until_settled(path)
        if record["status"] == "unstable":
            mid_write.append(name)
            reasons[name] = "unstable: %s" % _skip_reason(record)
            continue
        if record["pauses"]:
            retried.append(name)
        if record["error"] is not None:
            failures.append({"file": name, "error": record["error"]})
            continue
        doc = record["doc"]
        if not isinstance(doc, dict):
            failures.append({"file": name, "error": "top-level is %s, not object" % type(doc).__name__})
            continue
        docs[name] = doc
        shape = classify(name, doc)
        shapes[name] = shape
        missing = [k for k in required_keys(shape) if k not in doc]
        if missing:
            gaps[name] = missing
    return {"failures": failures, "gaps": gaps, "mid_write": mid_write, "shapes": shapes,
            "skip_reason": reasons, "retried": retried, "docs": docs}


def scan_handoffs(directory=HANDOFFS):
    """Return (parse_failures, missing_key_gaps, mid_write_skips) for *.json in directory."""
    a = audit(directory)
    return a["failures"], a["gaps"], a["mid_write"]


def _regressions(gaps, baseline):
    """Gaps that are NOT frozen in `baseline`, per shape-appropriate contract.

    U8.35 retired the `shapes` parameter: it was never read (the caller had already
    filtered `gaps` by shape), so it invited the reader to believe a shape filter
    happened here when it did not.
    """
    new = {f: m for f, m in gaps.items() if f not in baseline}
    worsened = {f: sorted(set(m) - set(baseline.get(f, []))) for f, m in gaps.items()
                if f in baseline and set(m) - set(baseline.get(f, []))}
    return new, worsened


def test_every_handoff_parses_and_declares_a_unit():
    """Assert against the documents `audit()` already settled (U8.35).

    This used to re-read every non-skipped file with `json.loads(path.read_bytes())`
    AFTER the guard had settled it -- an unguarded second read that could raise for
    exactly the transient reason this unit exists to remove.  A file is now read once,
    deliberately, and judged on the bytes the guard actually settled on.
    """
    a = audit()
    assert a["failures"] == [], "unparseable handoff(s): %s (mid-write/unstable skipped: %s)" % (
        a["failures"], a["mid_write"])
    for name, doc in sorted(a["docs"].items()):
        assert "unit" in doc, "%s has no 'unit' key" % name
        assert any(k in doc for k in STATUSISH), (
            "%s carries no status/verdict/result/overall key (U8.25 removed the stale 13-file "
            "exemption: measured ZERO handoffs lacked one)" % name)


def test_no_new_contract_key_gaps():
    a = audit()
    unit_gaps = {f: m for f, m in a["gaps"].items() if a["shapes"][f] == "unit"}
    ver_gaps = {f: m for f, m in a["gaps"].items() if a["shapes"][f] == "verifier"}
    unit_baseline, verifier_baseline, _contract = frozen_baselines()
    new_u, worse_u = _regressions(unit_gaps, unit_baseline)
    new_v, worse_v = _regressions(ver_gaps, verifier_baseline)
    assert new_u == {} and worse_u == {} and new_v == {} and worse_v == {}, (
        "NEW unit-shape handoff contract gaps: %s %s ; NEW verifier-shape gaps: %s %s"
        % (new_u, worse_u, new_v, worse_v))


def test_broken_fixture_is_rejected(tmp_path):
    """RED case: a U0.22-class defect must be reported, not tolerated."""
    bad = tmp_path / "U0.22.json"
    bad.write_text('{"unit":"U0.22","status":"done","artifacts":[],'
                   '"evidence":{"tests":{"assertions_changed_detail":["a"],"n":1,'
                   '"assert_statement_count_now":120}]}\n')
    failures, _g, mid = scan_handoffs(tmp_path)
    assert mid == []
    assert len(failures) == 1 and failures[0]["file"] == "U0.22.json", failures
    assert "JSONDecodeError" in failures[0]["error"]


def test_u0_22_pre_repair_bytes_would_have_been_caught(tmp_path):
    """Proves the guard catches the ACTUAL U0.22 defect U8.14 found."""
    before = ROOT / "state" / "logs" / "U8.15" / "repairs" / "U0.22.before.json"
    if not before.exists():
        import pytest; pytest.skip("U8.15 pre-repair copy absent")
    (tmp_path / "U0.22.json").write_bytes(before.read_bytes())
    failures, _g, mid = scan_handoffs(tmp_path)
    assert mid == [] and len(failures) == 1, failures
    # Tightened by U8.35.  The old form was
    #   assert "line 6 column 32" in err or "delimiter" in err
    # which accepted EITHER a position literal that CPython renumbers between
    # releases (so it was the brittle half) OR a bare substring (so it was the weak
    # half: any unrelated message that merely contained "delimiter" passed, and the
    # "line 6 column 32" evidence could be silently absent).  Both facts are now
    # required, and the version-fragile literal is no longer load-bearing.
    err = failures[0]["error"]
    assert err.startswith("JSONDecodeError: "), err
    assert "delimiter" in err, err


def test_missing_required_key_fixture_is_rejected(tmp_path):
    """RED case (unit shape): a parseable handoff missing required keys is a reported gap."""
    (tmp_path / "U0.22.json").write_text(json.dumps(
        {"unit": "U0.22", "status": "done", "artifacts": [], "evidence": {}}))
    failures, gaps, mid = scan_handoffs(tmp_path)
    assert failures == [] and mid == []
    assert gaps == {"U0.22.json": ["blocker", "next_unit_hint", "write_paths"]}, gaps


def test_missing_required_key_fixture_is_rejected_for_verifier_shape(tmp_path):
    """RED case (verifier shape): a verdict missing 'overall'/'next_unit_hint' is a reported gap."""
    (tmp_path / "V9.99.json").write_text(json.dumps(
        {"unit": "V9.99", "checks": [], "blocker": "", "write_paths": []}))
    failures, gaps, mid = scan_handoffs(tmp_path)
    assert failures == [] and mid == []
    assert gaps == {"V9.99.json": ["overall", "next_unit_hint"]}, gaps


def test_new_gap_is_flagged_not_silently_accepted(tmp_path, monkeypatch):
    """Proves the baseline is a record, not a loophole: dropping an entry surfaces the gap."""
    (tmp_path / "V9.98.json").write_text(json.dumps(
        {"unit": "V9.98", "overall": "pass", "checks": [], "blocker": "", "next_unit_hint": "", "write_paths": []}))
    a = audit(tmp_path)
    assert a["gaps"] == {}                                    # complete verdict -> clean
    (tmp_path / "V9.98.json").write_text(json.dumps({"unit": "V9.98", "checks": []}))
    a = audit(tmp_path)
    assert a["shapes"]["V9.98.json"] == "verifier"
    assert a["gaps"] == {"V9.98.json": ["overall", "blocker", "next_unit_hint", "write_paths"]}, a["gaps"]


def test_unit_shape_baseline_still_catches_new_gaps(tmp_path):
    """Non-vacuity after U8.25 retired 41 dead V* entries from the unit baseline.

    A retained baseline is only useful if it still flags (i) an unknown unit handoff and
    (ii) a frozen gap that got WIDER.  Both are exercised directly against the pinned file.
    """
    unit_baseline, _v, _c = frozen_baselines()
    (tmp_path / "U9.99.json").write_text(json.dumps({"unit": "U9.99", "status": "done"}))
    # wider than the frozen U0.22 entry (blocker, next_unit_hint, write_paths): it also
    # lacks artifacts+evidence, which the baseline never exempted.
    (tmp_path / "U0.22.json").write_text(json.dumps({"unit": "U0.22", "status": "done"}))
    a = audit(tmp_path)
    new, worsened = _regressions(a["gaps"], unit_baseline)
    assert new == {"U9.99.json": ["artifacts", "evidence", "blocker", "next_unit_hint", "write_paths"]}, new
    assert worsened == {"U0.22.json": ["artifacts", "evidence"]}, worsened


def test_no_baseline_entry_over_declares():
    """An exemption that claims MORE than the live measurement HIDES a fixed handoff.

    This is the measurement half of the U8.25 design, and it is NOT a tautology: the
    exemptions come from a pinned FILE and the measurement comes from the handoffs on disk,
    so the two can disagree.  U8.22 handed up V5.25.json as exactly this (declared
    [next_unit_hint], measured []), and U8.15's 41 V* entries were the same shape in bulk.
    A re-derived baseline would always agree and catch nothing; here the baseline stays
    frozen while the corpus is re-measured, so the check can only ever TIGHTEN.
    """
    a = audit()
    unit_baseline, verifier_baseline, _c = frozen_baselines()
    live_unit = {f: m for f, m in a["gaps"].items() if a["shapes"][f] == "unit"}
    live_verifier = {f: m for f, m in a["gaps"].items() if a["shapes"][f] == "verifier"}
    mid = set(a["mid_write"])
    over = {}
    for label, baseline, live in (("unit", unit_baseline, live_unit),
                                  ("verifier", verifier_baseline, live_verifier)):
        for name, exempted in baseline.items():
            if name in mid:                      # torn read: not evidence of a repair
                continue
            measured = set(live.get(name, []))
            if set(exempted) - measured:
                over["%s:%s" % (label, name)] = {"exempted": exempted, "measured": sorted(measured)}
    assert over == {}, (
        "baseline exemption(s) now over-declare the live measurement (the handoff was "
        "repaired, so the exemption would silently tolerate the key being lost again): %s. "
        "REMEDY: delete this entry and update BASELINE_GAPS_SHA256 \u2014 do NOT loosen and do "
        "NOT re-derive from live data. (For a verifier-shape entry the pin to update is "
        "VERIFIER_BASELINE_SHA256. Re-deriving from the corpus would re-absolve every known "
        "gap, and loosening the check would stop it catching the next one.)"
        % over)


def test_frozen_baselines_are_untouched_and_recorded():
    """Both frozen baselines are hash-pinned; a silent edit fails here.

    This is the integrity half of the U8.25 design.  There is deliberately no longer an
    inline copy of either record to compare the files against: that comparison was
    copy==copy and could never detect a transcription error in either copy.  What is left
    to prove is that the bytes on disk are the bytes the guard was written against, and
    that the records are well-formed enough to be the sole source.
    """
    for path, pinned, label in ((BASELINE_GAPS_PATH, BASELINE_GAPS_SHA256, "U8.15 unit-shape baseline"),
                                (VERIFIER_BASELINE_PATH, VERIFIER_BASELINE_SHA256, "U8.18 verifier-shape baseline")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == pinned, "%s changed: %s != pinned %s" % (label, digest, pinned)
    unit_gaps, verifier_gaps, verifier_contract = frozen_baselines()
    assert unit_gaps and verifier_gaps, (unit_gaps, verifier_gaps)
    # Deliberately NO self-comparison here: `verifier_contract == required_keys("verifier")`
    # would be a tautology (the loader hands back that very list), i.e. exactly the flaw this
    # unit removed.  What IS checkable is that the contract is well-formed and that no
    # exemption names a key the contract never requires -- a dead exemption is the same trap
    # as U8.15's 41 dead V* entries, in miniature.
    assert len(CONTRACT) == 7 and len(set(CONTRACT)) == 7 and "unit" in CONTRACT, CONTRACT
    assert verifier_contract and len(set(verifier_contract)) == len(verifier_contract), verifier_contract
    for label, baseline, contract in (("unit", unit_gaps, CONTRACT),
                                      ("verifier", verifier_gaps, verifier_contract)):
        for name, missing in baseline.items():
            assert name.endswith(".json"), "%s baseline key is not a handoff name: %r" % (label, name)
            assert isinstance(missing, list) and all(isinstance(k, str) for k in missing), (label, name, missing)
            assert all(k in contract for k in missing), (
                "%s baseline exempts key(s) the contract never requires (a DEAD exemption, "
                "which no reader can ever consult): %s -> %s" % (label, name, missing))
    # The U8.15 record must keep the account of what U8.25 retired: a reader who remembers
    # the 41 V* entries has to be able to find out where they went.
    u8_15_record = json.loads(BASELINE_GAPS_PATH.read_text())
    assert "retired_dead_v_entries" in u8_15_record and "retired_exemption_list" in u8_15_record
    assert all(not k.startswith("V") for k in unit_gaps), (
        "a V* name can never be judged as a unit handoff (see classify()); unit baseline: %s"
        % sorted(k for k in unit_gaps if k.startswith("V")))


# ---------------------------------------------------------------------------
# U8.35 RED/GREEN: the settle loop must not weaken the guard, in either direction
# ---------------------------------------------------------------------------
def _complete_unit_doc(unit="U9.95"):
    return json.dumps({"unit": unit, "status": "done", "artifacts": [], "evidence": {},
                       "blocker": "", "next_unit_hint": "", "write_paths": []})


def test_settled_invalid_file_still_fails_after_the_settle_loop(tmp_path):
    """Direction 1 (U8.35): a file that NEVER MOVES and is unparseable is STILL a hard failure.

    The loop must not become a way to excuse a committed defect.  These bytes are
    identical across the whole bound, so `_read_until_settled` returns 'settled' and
    the JSONDecodeError is reported exactly as the old guard reported it -- the pause
    only makes the report later, never quieter.
    """
    (tmp_path / "U9.96.json").write_bytes(b'{"unit":"U9.96","status":"done","artifacts":[]')
    a = audit(tmp_path)
    assert a["retried"] == ["U9.96.json"], a["retried"]        # the loop really did re-read
    assert a["mid_write"] == [] and a["skip_reason"] == {}, (a["mid_write"], a["skip_reason"])
    assert len(a["failures"]) == 1 and a["failures"][0]["file"] == "U9.96.json", a["failures"]
    assert "JSONDecodeError" in a["failures"][0]["error"], a["failures"]


def test_torn_then_complete_write_is_judged_not_failed(tmp_path, monkeypatch):
    """Direction 2 (U8.35): V8.29's field failure -- the writer finishes during the watch.

    The write is left as a torn prefix and only completed when the guard pauses, i.e.
    strictly later than the old immediate double-read window.  The old guard saw the
    same torn bytes twice and HARD-failed; the loop sees the completion and judges the
    settled document, so the outcome is neither a failure nor a gap.
    """
    target = tmp_path / "U9.95.json"
    full = _complete_unit_doc().encode()
    target.write_bytes(full[: len(full) // 2])                 # torn prefix, flushed
    real_sleep = time.sleep
    done = []

    def finish_during_pause(_seconds):
        if not done:
            done.append(True)
            target.write_bytes(full)                           # the sibling writer finishes
        real_sleep(0)                                          # no real delay in this test

    monkeypatch.setattr(time, "sleep", finish_during_pause)
    a = audit(tmp_path)
    assert a["failures"] == [], a["failures"]
    assert a["gaps"] == {}, a["gaps"]
    assert a["mid_write"] == [] and a["skip_reason"] == {}, (a["mid_write"], a["skip_reason"])
    assert a["retried"] == ["U9.95.json"], a["retried"]        # it was caught mid-write


def test_still_changing_file_is_skipped_with_a_reason(tmp_path, monkeypatch):
    """The bound does not manufacture a defect: exhaustion while MOVING is a SKIP.

    A file that is still being appended to can never be judged, and treating it as a
    settled parse error is exactly the harm V8.29 measured.  It is reported as an
    unfinished write with a quotable reason instead.
    """
    target = tmp_path / "U9.94.json"
    target.write_bytes(b'{"unit":"U9.94"')
    real_sleep = time.sleep

    def grow_during_pause(_seconds):
        with open(target, "ab") as fh:
            fh.write(b" ")                                     # still being written
        real_sleep(0)

    monkeypatch.setattr(time, "sleep", grow_during_pause)
    a = audit(tmp_path)
    assert a["failures"] == [], a["failures"]
    assert a["mid_write"] == ["U9.94.json"], a["mid_write"]
    reason = a["skip_reason"]["U9.94.json"]
    assert "still changing" in reason, reason
    assert reason.endswith("(unfinished write, not a defect)"), reason
