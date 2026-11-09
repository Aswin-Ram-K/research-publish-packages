"""Tests for the journal rule added to experiments/ptr-engine/tools/handoff_lint.py.

JOURNAL-LINT turns the "journal first" prose obligation into a check:

  E_JOURNAL_MISSING   a unit's handoff exists but orchestration/journals/<UNIT>.jsonl has
                      no usable last record (absent, empty, unparseable, or carrying no
                      step number and no timestamp). FORWARD-ONLY: a miss already frozen
                      in state/logs/journal-lint-baseline.json is exempt.
  W_JOURNAL_STALE     the journal exists but is older than the handoff it should describe.

Every synthetic case runs in its own tmp dir; the real-corpus case only reads.

Run: python3 -m pytest experiments/ptr-engine/longrun/tests/test_journal_lint.py -q
"""

import glob as glob_mod
import importlib.util
import json
import os
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DEFAULT_TOOL = os.path.join(REPO, "experiments", "ptr-engine", "tools", "handoff_lint.py")
# Override to reproduce the red state by pointing the suite at a pre-rule copy of the
# linter (same mechanism as test_unit_journal.py's UNIT_JOURNAL_TOOL).
TOOL = os.environ.get("HANDOFF_LINT_TOOL", DEFAULT_TOOL)
BASELINE = os.path.join(REPO, "state", "logs", "journal-lint-baseline.json")


def load_tool():
    spec = importlib.util.spec_from_file_location("handoff_lint", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hl = load_tool()

UNIT_HANDOFF = {
    "unit": "U-J", "status": "partial", "artifacts": ["docs/REAL.md"],
    "evidence": {"count": "1", "commands": ["true"]},
    "blocker": "", "next_unit_hint": "n", "write_paths": ["docs/REAL.md"],
}


def make_ws(tmp_path, journals=True):
    root = tmp_path
    (root / "orchestration" / "handoffs").mkdir(parents=True, exist_ok=True)
    (root / "orchestration" / "units").mkdir(parents=True, exist_ok=True)
    if journals:
        (root / "orchestration" / "journals").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "REAL.md").write_text("real\n", encoding="utf-8")
    return root


def write_handoff(root, unit="U-J", name=None, mtime=None):
    p = root / "orchestration" / "handoffs" / ((name or unit) + ".json")
    d = dict(UNIT_HANDOFF)
    d["unit"] = unit
    p.write_text(json.dumps(d, indent=1), encoding="utf-8")
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return str(p)


def write_journal(root, unit="U-J", lines=(), mtime=None):
    p = root / "orchestration" / "journals" / (unit + ".jsonl")
    with open(p, "w", encoding="utf-8") as fh:
        for rec in lines:
            fh.write(json.dumps(rec) + "\n")
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return str(p)


def codes(rec, bucket="errors"):
    return [e["code"] for e in rec[bucket]]


# --- the census itself ---------------------------------------------------------------

def test_frozen_baseline_exists_and_is_forward_only():
    """The baseline is a real frozen file with a timestamp and a miss count."""
    assert os.path.exists(BASELINE), BASELINE
    doc = json.load(open(BASELINE, encoding="utf-8"))
    assert doc["frozen_by"] == "JOURNAL-LINT"
    assert isinstance(doc["frozen_at"], (int, float)) and doc["frozen_at"] > 0
    assert doc["counts"]["entries"] == len(doc["units"]) > 0
    assert "forward-only" in doc["rule"].lower() or "Forward-only" in doc["rule"]
    print("frozen baseline: %d entries, frozen_at=%s, census=%s"
          % (len(doc["units"]), doc["frozen_at_iso"], doc["counts"]["journal_census"]))


def test_census_over_the_live_corpus_is_reported():
    """Census first: every handoff's journal state, counted, with the miss count that the
    frozen baseline must cover. Fails when a live miss is not in the baseline."""
    files = sorted(glob_mod.glob(os.path.join(REPO, "orchestration", "handoffs", "*.json")))
    files += sorted(glob_mod.glob(os.path.join(REPO, "orchestration", "handoffs", "recovered", "*.json")))
    base = hl.load_journal_baseline(BASELINE)
    rows = [hl.lint_file(f, REPO, strict=False, baseline=base) for f in files]
    new_misses = [r["file"] for r in rows if "E_JOURNAL_MISSING" in codes(r)]
    census = hl.summarize(rows)["journal_census"]
    print("handoffs=%d present=%d missing=%d empty=%d unparseable=%d no_step=%d no_ts=%d "
          "stale=%d exempt_frozen=%d new_misses=%d"
          % (len(rows), census["journal_present"], census["journal_missing"],
             census["journal_empty"], census["journal_unparseable"],
             census["journal_no_step"], census["journal_no_ts"], census["journal_stale"],
             census["exempt_frozen"], len(new_misses)))
    assert not new_misses, "new journal misses outside the frozen baseline: %s" % new_misses[:5]


def test_unit_cards_without_handoffs_are_named_not_silently_dropped():
    """The rule is keyed off handoffs, so a unit card with no handoff is invisible to it.
    Count those, so the blind spot is a number rather than a silence."""
    cards = {os.path.basename(p)[:-3]
             for p in glob_mod.glob(os.path.join(REPO, "orchestration", "units", "*.md"))}
    handoffs = set()
    base = hl.load_journal_baseline(BASELINE)
    for p in glob_mod.glob(os.path.join(REPO, "orchestration", "handoffs", "*.json")):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and isinstance(d.get("unit"), str):
            handoffs.add(d["unit"].strip())
    only_cards = sorted(cards - handoffs)
    print("unit cards=%d handoff units=%d cards-without-handoff=%d (invisible to E_JOURNAL_MISSING)"
          % (len(cards), len(handoffs), len(only_cards)))
    assert len(cards) > 0 and len(handoffs) > 0


# --- (a) red: handoff with no journal ------------------------------------------------

def test_a_handoff_with_no_journal_is_reported(tmp_path):
    root = make_ws(tmp_path)
    p = write_handoff(root)
    rec = hl.lint_file(p, str(root), strict=False,
                       baseline={"units": {}, "frozen_at": None})
    assert "E_JOURNAL_MISSING" in codes(rec)
    assert "absent" in [e["detail"] for e in rec["errors"] if e["code"] == "E_JOURNAL_MISSING"][0]
    assert rec["journal"]["exists"] is False
    assert rec["ok"] is False
    rc = hl.main([os.path.join(str(root), "orchestration", "handoffs"), "--quiet",
                  "--root", str(root), "--journal-baseline", os.path.join(str(root), "nope.json")])
    print("(a) no journal -> exit=%s codes=%s detail=%s"
          % (rc, codes(rec), [e["detail"] for e in rec["errors"] if e["code"] == "E_JOURNAL_MISSING"]))
    assert rc == 1


def test_a2_empty_journal_file_is_still_missing(tmp_path):
    """An empty file is not a journal: zero bytes cannot reconstruct anything."""
    root = make_ws(tmp_path)
    p = write_handoff(root)
    write_journal(root, lines=())
    rec = hl.lint_file(p, str(root), strict=False, baseline={"units": {}, "frozen_at": None})
    assert "E_JOURNAL_MISSING" in codes(rec)
    assert any("empty" in e["detail"] for e in rec["errors"] if e["code"] == "E_JOURNAL_MISSING")


# --- (b) green: the same unit with one valid line ------------------------------------

def test_b_one_valid_journal_line_is_clean(tmp_path):
    root = make_ws(tmp_path)
    p = write_handoff(root)
    journal = write_journal(root, lines=[{"t": "2026-10-26T17:00:00Z", "step": 1,
                                          "kind": "header", "note": "start"}],
                            mtime=time.time() + 5)
    rec = hl.lint_file(p, str(root), strict=False, baseline={"units": {}, "frozen_at": None})
    assert rec["errors"] == []
    assert rec["warnings"] == []
    assert rec["journal"]["exists"] is True and rec["journal"]["last_has_step"] is True
    rc = hl.main([os.path.join(str(root), "orchestration", "handoffs"), "--quiet",
                  "--root", str(root), "--journal-baseline", os.path.join(str(root), "nope.json")])
    print("(b) one valid line -> exit=%s errors=%s journal=%s" % (rc, codes(rec), journal and rec["journal"]["bytes"]))
    assert rc == 0


# --- (c) red: a last line with no step number ---------------------------------------

def test_c_last_line_without_step_number_is_reported(tmp_path):
    root = make_ws(tmp_path)
    p = write_handoff(root)
    write_journal(root, lines=[{"ts": "2026-10-26T17:00:00Z", "event": "scan",
                                "note": "found 14 files"}])
    rec = hl.lint_file(p, str(root), strict=False, baseline={"units": {}, "frozen_at": None})
    assert "E_JOURNAL_MISSING" in codes(rec)
    detail = [e["detail"] for e in rec["errors"] if e["code"] == "E_JOURNAL_MISSING"][0]
    print("(c) no step number -> codes=%s detail=%s" % (codes(rec), detail))
    assert "no step number" in detail
    assert rec["journal"]["last_has_step"] is False


def test_c2_last_line_without_timestamp_is_reported(tmp_path):
    root = make_ws(tmp_path)
    p = write_handoff(root)
    write_journal(root, lines=[{"step": 1, "kind": "header"}])
    rec = hl.lint_file(p, str(root), strict=False, baseline={"units": {}, "frozen_at": None})
    assert "E_JOURNAL_MISSING" in codes(rec)
    assert any("no timestamp" in e["detail"] for e in rec["errors"] if e["code"] == "E_JOURNAL_MISSING")


# --- torn final line: tolerated exactly as tools/unit_journal.py tolerates it --------

def test_torn_final_line_is_tolerated_when_an_earlier_record_is_usable(tmp_path):
    root = make_ws(tmp_path)
    p = write_handoff(root)
    jp = write_journal(root, lines=[{"t": "2026-10-26T17:00:00Z", "step": 1, "kind": "header"}],
                       mtime=time.time() + 5)
    with open(jp, "a", encoding="utf-8") as fh:
        fh.write('{"t":"2026-10-26T17:01:00Z","step":2,"ki')
    rec = hl.lint_file(p, str(root), strict=False, baseline={"units": {}, "frozen_at": None})
    assert rec["errors"] == []
    assert rec["journal"]["unparseable_lines"] == 1
    assert rec["journal"]["last_has_step"] is True


# --- W_JOURNAL_STALE -----------------------------------------------------------------

def test_journal_older_than_handoff_warns_not_fails(tmp_path):
    root = make_ws(tmp_path)
    now = time.time()
    p = write_handoff(root, mtime=now)
    write_journal(root, lines=[{"t": "2026-10-26T17:00:00Z", "step": 1, "kind": "header"}],
                  mtime=now - 600)
    rec = hl.lint_file(p, str(root), strict=False, baseline={"units": {}, "frozen_at": None})
    assert rec["errors"] == []
    assert codes(rec, "warnings") == ["W_JOURNAL_STALE"]
    print("stale -> warnings=%s errors=%s" % (codes(rec, "warnings"), codes(rec)))
    assert hl.main([os.path.join(str(root), "orchestration", "handoffs"), "--quiet",
                    "--root", str(root), "--journal-baseline", os.path.join(str(root), "nope.json")]) == 0


# --- forward-only baseline ------------------------------------------------------------

def test_forward_only_baseline_exempts_frozen_and_catches_new(tmp_path):
    root = make_ws(tmp_path)
    now = time.time()
    frozen = {"units": {"OLD.json": {"unit": "OLD", "reason": "frozen"}},
              "frozen_at": now - 7200, "grace_seconds": 0, "loaded": True}
    old = write_handoff(root, unit="OLD", mtime=now - 60)
    rec_old = hl.lint_file(old, str(root), strict=False, baseline=frozen)
    assert "E_JOURNAL_MISSING" not in codes(rec_old)
    assert rec_old["journal"]["exempt"] == "frozen-baseline"

    new = write_handoff(root, unit="NEW", mtime=now - 10)
    rec_new = hl.lint_file(new, str(root), strict=False, baseline=frozen)
    assert "E_JOURNAL_MISSING" in codes(rec_new)
    assert rec_new["journal"]["exempt"] is None
    print("forward-only: frozen=%s new=%s" % (rec_old["journal"]["exempt"], codes(rec_new)))

    # a pre-existing miss never listed explicitly is still exempt by timestamp
    pre = write_handoff(root, unit="PRE", mtime=now - 9000)
    rec_pre = hl.lint_file(pre, str(root), strict=False, baseline=frozen)
    assert "E_JOURNAL_MISSING" not in codes(rec_pre)
    assert rec_pre["journal"]["exempt"] == "pre-baseline-timestamp"


def test_grace_window_protects_a_just_written_handoff(tmp_path):
    root = make_ws(tmp_path)
    now = time.time()
    frozen = {"units": {}, "frozen_at": now - 7200, "grace_seconds": 180, "loaded": True}
    p = write_handoff(root, unit="INFLIGHT", mtime=now)
    rec = hl.lint_file(p, str(root), strict=False, baseline=frozen)
    assert "E_JOURNAL_MISSING" not in codes(rec)
    assert rec["journal"]["exempt"] == "in-flight-grace"


# --- additive proof: pre-existing behaviour is unchanged -----------------------------

def test_no_journal_convention_means_no_new_codes(tmp_path):
    """A workspace with no orchestration/journals has no journal convention to police:
    every pre-existing code behaves exactly as before."""
    root = make_ws(tmp_path, journals=False)
    p = write_handoff(root)
    rec = hl.lint_file(p, str(root), strict=False)
    assert "E_JOURNAL_MISSING" not in codes(rec) and "W_JOURNAL_STALE" not in codes(rec)
    assert rec["journal"]["applicable"] is False


def test_existing_codes_are_byte_identical_with_and_without_a_valid_journal(tmp_path):
    """The new rule adds codes; it must not alter what the other codes say."""
    root = make_ws(tmp_path)
    p = write_handoff(root)
    write_journal(root, lines=[{"t": "2026-10-26T17:00:00Z", "step": 1, "kind": "header"}],
                  mtime=time.time() + 600)
    rec = hl.lint_file(p, str(root), strict=False, baseline={"units": {}, "frozen_at": None})
    assert rec["errors"] == [] and rec["warnings"] == []

    # same document, judged by lint_doc alone: unchanged code path
    doc = json.load(open(p, encoding="utf-8"))
    bare = hl.lint_doc(doc, str(root))
    assert bare["errors"] == [] and bare["warnings"] == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
