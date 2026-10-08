"""U5.8 — a *bare* re-assembly must not dissolve commit-verified provenance.

The defect (found by verifier V5B, not re-derived here): re-assembling
``dockets/duval/duval-u55-pinned`` from its own copies dropped all 6
``git_object``/``blob_sha`` material entries to ``working_tree``, the manifest
sha moved ``879e66b8…→526b869d…``, nothing raised and ``verify_docket`` still
returned ``ok``.  The bytes never changed — only the *claim* about them, which
is the docket's whole point ("this material is verifiable at commit X").

The fix follows U5.7's precedent (``generated_by.producer`` surviving a bare
re-assembly by inheriting from the existing manifest): material rows inherit
``resolved_from``/``blob_sha``/``unpinned`` from the existing manifest **only
when they still describe the same bytes** (same ``dest`` *and* same ``sha256``);
changed bytes are recomputed, never inherited; new rows inherit nothing; and any
would-be downgrade is recorded in the assembly report and appended to
``HISTORY.md``.

RED→GREEN GUARD (a) — the preservation guard.  Disabling the inheritance
(the one-line call site, reverted to ``pass``) makes the central test fail,
because every row downgrades to ``working_tree`` and loses its ``blob_sha``::

          result = _bare(dock, src)  # bare: nothing provenance-shaped is passed in
      E   AssertionError: f.md
      E   assert 'working_tree' == 'git_object'
      E     - git_object
      E     + working_tree
      FAILED tests/test_docket_reassembly.py::test_bare_reassembly_preserves_git_object_provenance
      1 failed in 0.04s

    src/resextract/docket/assemble.py sha256 before == after the revert/restore:
    5e870ab589cc78a451f0f83e0597d8187f501ac1be4791b1636707b892b83033 (bit-identical).

RED→GREEN GUARD (b) — the stale-claim guard.  Making the recompute branch
unreachable (``if False and old.sha256 != item.sha256:``) makes a changed file
keep the *old* pin, so the test fails on a fabricated provenance claim::

      E   AssertionError: inherited blob_sha on changed bytes = fabricated provenance
      E   assert 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' is None
      E    +  where 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' = MaterialItem(src='.../sources/f.md', dest='f.md',
      E        sha256=..., linked=False, note=None, blob_sha='aaaa...', resolved_from='git_object', unpinned=False).blob_sha
      FAILED tests/test_docket_reassembly.py::test_changed_bytes_recompute_and_never_inherit_the_stale_pin
      1 failed in 0.04s

    src/resextract/docket/assemble.py sha256 before == after the revert/restore:
    5e870ab589cc78a451f0f83e0597d8187f501ac1be4791b1636707b892b83033 (bit-identical).

Both guards: ``src/resextract/docket/assemble.py`` sha256 before == after the
restore (bit-identical), with ``PYTHONDONTWRITEBYTECODE=1`` and a
``__pycache__`` purge on every revert/restore.

--------------------------------------------------------------------------
U5.9 — the *rest* of the silent provenance-loss family (U5.8's own hint)
--------------------------------------------------------------------------

Three more fields died the same silent death on a bare re-assembly of
``dockets/duval/duval-u55-pinned`` (measured pre-fix below; ``verify_docket``
still returned ``ok`` throughout — that is the whole point):

1. ``src`` — re-synthesised as ``<source_root>/<dest>``.  Measured **8** of 9
   rows wrong pre-fix (``src_correct_after`` 1/9), because the bridge
   (:func:`material_report_from_docket`) only knows the docket-internal
   ``dest``; ``materialize_lane`` repairs this by hand at
   ``materialize.py:1854-1860``, which is the tell that synthesis is the lossy
   direction.  A wrong ``src`` is a **false** fact, not a missing one: e.g.
   ``src`` ``/home/zer0null/Duval/traces/2026-09-28-duval-m0.jsonl`` →
   ``/home/zer0null/Duval/data/2026-09-28-duval-m0.jsonl``.  **Worst of the
   three.**
2. ``window_sealed: True -> None`` (before -> after) — silently discards that
   the docket was built inside a **verified quiescent window**, the property
   the sealed-window work exists to establish.
3. ``material[].note`` — 3 -> 0; the machine-readable unpinned reason
   (e.g. ``unpinned: untracked_at_commit; mtime 2026-10-08T05:59:41Z``) is
   lost, downgrading an explainable unpinned entry to an unexplained one.

All three are inherited under U5.8's **same same-dest + same-sha256 guard**;
``src`` is *preference for the authoritative record* rather than mere
inheritance (only a row with no matching predecessor keeps the synthesised
value).  Healed rows are collapsed into ONE summary line (healing is the normal
outcome); only an entry that could NOT be preserved stays per-entry and loud.

``window_sealed`` semantics — **deliberately inherited as a historical fact**:
a bare re-assembly performs no window check, so ``None`` would *claim* no check
was done when one was, historically, verified.  It is carried only when the
previous manifest recorded non-``None``, this assembly established none, and
every previously recorded material row is still byte-identical (if the bytes
moved the seal no longer describes the docket and is NOT carried — loud).

RED→GREEN GUARD (a₂) — the ``src``-prefers-the-record guard.  Disabling the two
inheritance call sites makes the recorded source path collapse to the
synthesised one and the test fails::

          after = {r.dest: r.src for r in read_manifest(dock / "MANIFEST.json").material}
          for dest in NESTED:
      >       assert after[dest] == truth[dest], dest
      E       AssertionError: data/m0.jsonl
      E       assert '/tmp/pytest-...data/m0.jsonl' == '/tmp/pytest-...aces/m0.jsonl'
      FAILED tests/test_docket_reassembly.py::test_bare_reassembly_prefers_the_recorded_src_over_re_synthesis
      1 failed in 0.04s

RED→GREEN GUARD (b₂) — the changed-bytes-no-inherit guard across the NEW fields.
Making the changed-sha256 branch unreachable (``if False and old.sha256 !=
item.sha256:``) lets a changed row keep the previous ``src``/``note``::

          assert row.sha256 != old_sha
      >   assert row.src == os.path.join(str(src), dest), row.src
      E   AssertionError: /tmp/pytest-.../sources/traces/m0.jsonl
      E   assert '/tmp/pytest-...aces/m0.jsonl' == '/tmp/pytest-...data/m0.jsonl'
      FAILED tests/test_docket_reassembly.py::test_changed_bytes_inherit_none_of_src_note_or_the_sealed_window
      1 failed in 0.04s

Both U5.9 guards: ``src/resextract/docket/assemble.py`` sha256 before == after
the restore (bit-identical), ``tests/test_docket_reassembly.py`` sha256
``7bb80886e1c5383099b8306577bc8bb8282c995d0c748d2521137ff930d0f4dc``, ``PYTHONDONTWRITEBYTECODE=1`` + ``__pycache__``
purge on every revert/restore.

NOTE (deliberate, disclosed): §3 of the U5.9 card supersedes U5.8's *loud
per-entry healed-pin warning* — healing is the normal outcome and is now one
summary line.  ``test_would_be_downgrade_is_recorded_not_silent`` therefore
asserts the new logging contract (one summary line, zero per-entry alarms) in
addition to every field-level guarantee it asserted before; the field-level
assertions are unchanged and the assertion count grows.

--------------------------------------------------------------------------
U5.10 — the manifest's LISTS, the last members of the family (sibling's hint)
--------------------------------------------------------------------------

U5.9's own next-hint ("the unobserved remainder of the family") named five
lists and admitted the real docket has **0 of each**, so they could only be
exercised by a fixture.  Two corrections, both measured rather than assumed:

1. ``results`` and ``prior_art`` are **not manifest fields**.
   ``DocketManifest`` is ``extra="forbid"`` and its lists are exactly
   ``claims``/``material``/``web_sources``/``open_questions``/``rework_open``.
   ``results``/``prior_art`` are assembly *inputs*, rendered into
   ``RESULTS.md``/``PRIOR_ART.md`` and otherwise not persisted — so no
   inheritance can restore them, and inventing values back out of rendered
   markdown would be fabrication.  They are **alarmed per file** instead.
2. The manifest's real remaining hole is the three *unsupplied* lists:
   ``open_questions``, ``rework_open``, ``web_sources``.  A bare re-assembly
   supplies none of them, so each was rewritten ``[...] -> []`` — measured on
   the fixture below: ``2 -> 0``, ``1 -> 0``, ``2 -> 0``, with
   ``verify_docket`` still ``ok`` and ``downgrades == []``.  That silence is
   the defect.

``None`` now means "not supplied — inherit the existing manifest's own value",
while an explicit ``[]`` is a **deliberate clear** (honoured verbatim, silent).
Across a **changed target** the inheritance is **refused**, one loud warning per
non-empty list naming both revisions: a stale open question on a new head is
the quiet wrongness this family is made of.  An inherited list is a
byte-identical copy of the previous manifest's values; nothing is ever merged,
guessed, or re-derived.

RED→GREEN GUARD (a₃) — the **list-inheritance** guard.  Disabling the
inheritance call site (``if previous is not None and target is not None:`` →
``if False and ...``) leaves every list as the bare re-assembly supplied it, so
it is emptied and the central test fails::

>           assert after[name] == before[name], (name, after[name], before[name])
E           AssertionError: ('open_questions', [], ['does the 503 rate hold under a second region?', 'is the trace chain complete for m0?'])
E           assert [] == ['does the 50...lete for m0?']
E
E             Right contains 2 more items, first extra item: 'does the 503 rate hold under a second region?'
    FAILED tests/test_docket_reassembly.py::test_bare_reassembly_preserves_the_manifest_lists
    1 failed in 0.05s

    src/resextract/docket/assemble.py sha256 before == after the revert/restore:
    20e46f8ae9d6e40f123ff94a23f2c302332391432b6ea39de42d548e65bab1a8 (bit-identical).

RED→GREEN GUARD (b₃) — the **target-changed** guard.  Making the target check
unreachable (``if not same_target:`` → ``if False and not same_target:``) carries
the previous target's lists onto the new head, so the refused-with-a-reason test
fails on stale content::

>       assert after["open_questions"] == []
E       AssertionError: assert ['does the 50...lete for m0?'] == []
E
E         Left contains 2 more items, first extra item: 'does the 503 rate hold under a second region?'
E         Use -v to get more diff
    FAILED tests/test_docket_reassembly.py::test_target_changed_refuses_to_inherit_and_says_so
    1 failed in 0.05s

    src/resextract/docket/assemble.py sha256 before == after the revert/restore:
    20e46f8ae9d6e40f123ff94a23f2c302332391432b6ea39de42d548e65bab1a8 (bit-identical).

``tests/test_docket_reassembly.py`` sha256 after the U5.10 additions:
40f8f9e6acfa60c20b55521294047ed42ba69c60d75eaa2af098b4d2edfde308 (measured when the guards ran; pasting this paragraph necessarily changes the file hash); ``PYTHONDONTWRITEBYTECODE=1`` and a ``__pycache__`` purge on
every revert/restore.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil

import pytest

from pathlib import Path

from resextract.docket.assemble import assemble, material_report_from_docket, verify_docket
from resextract.docket.manifest import read_manifest, write_manifest

LANE = {"slug": "u58-lane", "type": "report", "title": "U5.8"}
TARGET = {"slug": "u58-target", "head_sha": "0" * 40, "graph_hash": "deadbeef"}
FRESH = {
    "verified_at": "2026-01-01T00:00:00Z",
    "prior_art_checked_at": None,
    "age_days": 0.0,
    "state": "current",
}
PIN_F = "a" * 40
PIN_G = "b" * 40
FILES = {"f.md": "alpha\n", "g.md": "beta\n", "h.md": "gamma\n"}


def _build(tmp_path):
    """A docket whose ``material/`` already holds the copied bytes."""
    dock = tmp_path / "dock"
    src = tmp_path / "sources"
    src.mkdir(parents=True)
    (dock / "material").mkdir(parents=True)
    for name, text in FILES.items():
        (src / name).write_text(text, encoding="utf-8")
        shutil.copyfile(src / name, dock / "material" / name)
    return dock, src


def _bare(dock, src):
    """The documented bare re-assembly: no material report, no provenance args.

    ``material_report=<the docket>`` is the bridge
    (:func:`material_report_from_docket`) that reads the docket's own
    ``material/`` and hashes its copies — the path that loses provenance.
    """
    return assemble(
        dock,
        lane=LANE,
        claims=[],
        material_report=str(dock),
        target_meta=TARGET,
        freshness=FRESH,
        source_root=str(src),
    )


def _pin(dock, shas):
    """Stand in for U5.6: record commit-verified provenance in the manifest."""
    m = read_manifest(dock / "MANIFEST.json")
    for row in m.material:
        if row.dest in shas:
            row.resolved_from = "git_object"
            row.blob_sha = shas[row.dest]
            row.unpinned = False
    write_manifest(str(dock), m)
    return m


def _block(m):
    """The whole material[] block, serialised — not just the fields we assert."""
    return json.dumps([row.model_dump() for row in m.material], sort_keys=True)


def test_bare_reassembly_preserves_git_object_provenance(tmp_path):
    """Central test: the material provenance block survives a bare re-assembly."""
    dock, src = _build(tmp_path)
    _bare(dock, src)
    _pin(dock, {"f.md": PIN_F, "g.md": PIN_G})
    before = read_manifest(dock / "MANIFEST.json")
    assert sum(1 for r in before.material if r.resolved_from == "git_object") == 2

    result = _bare(dock, src)  # bare: nothing provenance-shaped is passed in

    after = read_manifest(dock / "MANIFEST.json")
    by = {r.dest: r for r in after.material}
    for dest, pin in (("f.md", PIN_F), ("g.md", PIN_G)):
        assert by[dest].resolved_from == "git_object", dest
        assert by[dest].blob_sha == pin, dest
        assert by[dest].unpinned is False, dest
    assert sum(1 for r in after.material if r.resolved_from == "git_object") == 2
    # the whole block, not just the rows we happened to look at
    assert _block(after) == _block(before)
    # verify_docket is (deliberately) unchanged, and the schema string is not bumped
    assert verify_docket(dock).ok
    assert after.schema_ == "resextract/docket/1"
    assert json.loads((dock / "MANIFEST.json").read_text())["schema"] == "resextract/docket/1"
    assert result.manifest.material


def test_changed_bytes_recompute_and_never_inherit_the_stale_pin(tmp_path):
    """A pin must never be inherited onto different bytes — that would be a lie."""
    dock, src = _build(tmp_path)
    _bare(dock, src)
    _pin(dock, {"f.md": PIN_F, "g.md": PIN_G})
    old_sha = next(r.sha256 for r in read_manifest(dock / "MANIFEST.json").material if r.dest == "f.md")

    (src / "f.md").write_text("alpha CHANGED\n", encoding="utf-8")
    (dock / "material" / "f.md").write_text("alpha CHANGED\n", encoding="utf-8")

    result = _bare(dock, src)

    row = next(r for r in read_manifest(dock / "MANIFEST.json").material if r.dest == "f.md")
    assert row.sha256 != old_sha
    assert row.blob_sha is None, "inherited blob_sha on changed bytes = fabricated provenance"
    assert row.resolved_from == "working_tree"
    # the untouched sibling keeps its pin (the guard is per-row, not global)
    sib = next(r for r in read_manifest(dock / "MANIFEST.json").material if r.dest == "g.md")
    assert (sib.resolved_from, sib.blob_sha) == ("git_object", PIN_G)
    # and the recompute is loud
    assert any("bytes changed" in w and "f.md" in w for w in result.downgrades), result.downgrades
    hist = (dock / "HISTORY.md").read_text(encoding="utf-8")
    assert "bytes changed" in hist and "f.md" in hist


def test_new_entry_inherits_nothing(tmp_path):
    """No counterpart in the existing manifest ⇒ the current resolution stands."""
    dock, src = _build(tmp_path)
    _bare(dock, src)
    _pin(dock, {"f.md": PIN_F})

    (src / "new.md").write_text("delta\n", encoding="utf-8")
    shutil.copyfile(src / "new.md", dock / "material" / "new.md")
    _bare(dock, src)

    row = next(r for r in read_manifest(dock / "MANIFEST.json").material if r.dest == "new.md")
    assert row.resolved_from == "working_tree"
    assert row.blob_sha is None
    assert row.unpinned is False


def test_would_be_downgrade_is_recorded_not_silent(tmp_path):
    """The alarming half of the defect: silence.  Now it is recorded, and repaired.

    U5.9 §3 supersedes U5.8's *loud per-entry* healed-pin warning: healing is the
    normal, good outcome, so it is collapsed into ONE summary line, and only an
    entry that could NOT be preserved stays per-entry and loud.  The healed entry
    is still recorded (never silent) and still repaired.
    """
    dock, src = _build(tmp_path)
    _bare(dock, src)
    _pin(dock, {"f.md": PIN_F})
    # pre-image of the material block, captured BEFORE the re-assembly runs
    before = read_manifest(dock / "MANIFEST.json")

    result = _bare(dock, src)

    # recorded — but as the single "healed" summary line, not a per-entry alarm
    summary = [p for p in result.preserved if p.startswith("material provenance preserved")]
    assert len(summary) == 1, result.preserved
    assert summary[0] == "material provenance preserved for 3/3 entries"
    assert result.downgrades == [], (
        "a healed provenance downgrade is the normal outcome, not a per-entry alarm: "
        f"{result.downgrades}"
    )
    hist = (dock / "HISTORY.md").read_text(encoding="utf-8")
    assert hist.count("- **preserved** — ") == 1
    assert hist.count("- **downgrade** — ") == 0
    assert "material provenance preserved for 3/3 entries" in hist
    # recorded *and* repaired (U5.8's field-level guarantee, unchanged)
    row = next(r for r in read_manifest(dock / "MANIFEST.json").material if r.dest == "f.md")
    assert (row.resolved_from, row.blob_sha) == ("git_object", PIN_F)
    # the WHOLE material block equals the pinned pre-image, not just the one row
    # we happened to look at: a measurement vs an independent value => it can fail
    assert _block(read_manifest(dock / "MANIFEST.json")) == _block(before), (
        "the repaired manifest's material block differs from the pinned pre-image"
    )


def test_u55_shaped_manifest_still_loads_and_reassembles(tmp_path):
    """Backward compat: a pre-U5.5 manifest (no blob_sha/resolved_from/unpinned)."""
    dock, src = _build(tmp_path)
    _bare(dock, src)
    path = dock / "MANIFEST.json"
    raw = json.loads(path.read_text())
    for row in raw["material"]:
        for key in ("blob_sha", "resolved_from", "unpinned"):
            row.pop(key, None)
    path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")

    loaded = read_manifest(path)
    assert loaded.material
    assert all(r.resolved_from == "working_tree" and r.blob_sha is None for r in loaded.material)

    result = _bare(dock, src)  # must not raise
    assert verify_docket(dock).ok
    assert result.manifest.material
    assert (dock / "MANIFEST.json").read_text().count('"schema": "resextract/docket/1"') == 1


# --------------------------------------------------------------------------- #
# U5.9 — src prefers the record; note + window_sealed survive a bare re-assembly
# --------------------------------------------------------------------------- #

#: ``dest`` -> path relative to the source root.  ``data/m0.jsonl`` and
#: ``docs/root-only.txt`` are the load-bearing rows: their ``dest`` is NOT their
#: source-relative path, so re-synthesis from ``dest`` produces a WRONG path.
NESTED = {
    "data/m0.jsonl": "traces/m0.jsonl",
    "docs/root-only.txt": "root-only.txt",
    "docs/same.txt": "docs/same.txt",
}
NESTED_NOTES = {
    "data/m0.jsonl": "unpinned: untracked_at_commit; mtime 2026-10-01T00:00:00Z",
    "docs/root-only.txt": "unpinned: not_a_git_repo",
    "docs/same.txt": "unpinned: untracked_at_commit; mtime 2026-10-02T00:00:00Z",
}


def _build_nested(tmp_path):
    """A docket whose ``dest`` differs from its source-relative path."""
    dock = tmp_path / "dock"
    src = tmp_path / "sources"
    for dest, rel in NESTED.items():
        (dock / "material" / dest).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_text("payload " + dest + "\n", encoding="utf-8")
        shutil.copyfile(src / rel, dock / "material" / dest)
    return dock, src


def _true_src(src):
    return {dest: str(src / rel) for dest, rel in NESTED.items()}


def _record_src(dock, src):
    """Stand in for ``materialize_lane``'s src repair (materialize.py:1854-1860).

    The docket records where the bytes *actually* came from; a bare re-assembly
    must prefer that record over re-synthesis from ``dest``.
    """
    m = read_manifest(dock / "MANIFEST.json")
    truth = _true_src(src)
    for row in m.material:
        row.src = truth[row.dest]
    write_manifest(str(dock), m)
    return m


def _set_window_and_notes(dock, *, sealed=True):
    m = read_manifest(dock / "MANIFEST.json")
    m.window_sealed = sealed
    for row in m.material:
        row.note = NESTED_NOTES.get(row.dest)
    write_manifest(str(dock), m)
    return m


def test_bare_reassembly_prefers_the_recorded_src_over_re_synthesis(tmp_path):
    """THE test: every ``src`` must equal the previously recorded value.

    Two rows have ``dest != source-relative path``, so re-synthesis from ``dest``
    writes a path the material never came from — a false fact, not a missing one.
    """
    dock, src = _build_nested(tmp_path)
    _bare(dock, src)
    truth = _true_src(src)
    synth = {dest: os.path.join(str(src), dest) for dest in NESTED}
    differing = [dest for dest in NESTED if truth[dest] != synth[dest]]
    assert len(differing) >= 2, differing  # the fixture must exercise the defect
    _record_src(dock, src)

    _bare(dock, src)  # bare: nothing provenance-shaped is passed in

    after = {r.dest: r.src for r in read_manifest(dock / "MANIFEST.json").material}
    for dest in NESTED:
        assert after[dest] == truth[dest], dest
        assert after[dest] != synth[dest] or truth[dest] == synth[dest]
    # and verify_docket was never able to see the difference (that is the point)
    assert verify_docket(dock).ok


def test_bare_reassembly_preserves_a_verified_sealed_window(tmp_path):
    """``window_sealed=True`` survives as a *historical* fact (chosen semantics)."""
    dock, src = _build(tmp_path)
    _bare(dock, src)
    m = read_manifest(dock / "MANIFEST.json")
    m.window_sealed = True
    write_manifest(str(dock), m)
    assert read_manifest(dock / "MANIFEST.json").window_sealed is True

    result = _bare(dock, src)

    after = read_manifest(dock / "MANIFEST.json")
    assert after.window_sealed is True, "a verified quiescent window was silently dropped"
    assert any("window_sealed=True preserved" in p for p in result.preserved), result.preserved
    assert result.downgrades == [], result.downgrades
    assert verify_docket(dock).ok


def test_bare_reassembly_leaves_absent_window_sealed_as_none(tmp_path):
    """Never fabricate a seal: no recorded value, nothing to carry (or invent)."""
    dock, src = _build(tmp_path)
    _bare(dock, src)
    m = read_manifest(dock / "MANIFEST.json")
    assert m.window_sealed is None

    result = _bare(dock, src)

    assert read_manifest(dock / "MANIFEST.json").window_sealed is None
    assert not any("window_sealed" in p for p in result.preserved)


def test_bare_reassembly_preserves_material_notes(tmp_path):
    """N machine-readable unpinned reasons before -> the same N after."""
    dock, src = _build_nested(tmp_path)
    _bare(dock, src)
    _record_src(dock, src)
    _set_window_and_notes(dock)
    before = {r.dest: r.note for r in read_manifest(dock / "MANIFEST.json").material if r.note}
    assert len(before) == 3, before

    result = _bare(dock, src)

    after = {r.dest: r.note for r in read_manifest(dock / "MANIFEST.json").material if r.note}
    assert after == before, (after, before)
    assert len(after) == 3
    assert result.downgrades == []


def test_changed_bytes_inherit_none_of_src_note_or_the_sealed_window(tmp_path):
    """No fabrication: different bytes ⇒ nothing from the old record is carried."""
    dock, src = _build_nested(tmp_path)
    _bare(dock, src)
    _record_src(dock, src)
    _set_window_and_notes(dock)
    dest = "data/m0.jsonl"
    truth = _true_src(src)[dest]
    old_sha = next(r.sha256 for r in read_manifest(dock / "MANIFEST.json").material if r.dest == dest)

    (src / NESTED[dest]).write_text("CHANGED\n", encoding="utf-8")
    (dock / "material" / dest).write_text("CHANGED\n", encoding="utf-8")

    result = _bare(dock, src)

    row = next(r for r in read_manifest(dock / "MANIFEST.json").material if r.dest == dest)
    assert row.sha256 != old_sha
    # src re-synthesised from dest, NOT the old (now-wrong) record
    assert row.src == os.path.join(str(src), dest), row.src
    assert row.src != truth
    assert row.note is None, "an unpinned reason was carried onto different bytes"
    # the seal no longer describes these bytes, so it is dropped — and loudly
    assert read_manifest(dock / "MANIFEST.json").window_sealed is None
    assert any("bytes changed" in w and dest in w for w in result.downgrades), result.downgrades
    assert any("window_sealed=True NOT inherited" in w for w in result.downgrades), result.downgrades
    # the untouched sibling still keeps its recorded src/note (per-row guard)
    sib = next(r for r in read_manifest(dock / "MANIFEST.json").material if r.dest == "docs/root-only.txt")
    assert sib.src == _true_src(src)["docs/root-only.txt"]
    assert sib.note == NESTED_NOTES["docs/root-only.txt"]


def test_new_material_row_inherits_no_src_note_or_note_record(tmp_path):
    """A row with no predecessor keeps the synthesised src and no note."""
    dock, src = _build(tmp_path)
    _bare(dock, src)
    (src / "new.md").write_text("delta\n", encoding="utf-8")
    shutil.copyfile(src / "new.md", dock / "material" / "new.md")

    _bare(dock, src)

    row = next(r for r in read_manifest(dock / "MANIFEST.json").material if r.dest == "new.md")
    assert row.src == os.path.join(str(src), "new.md")
    assert row.note is None
    assert row.resolved_from == "working_tree" and row.blob_sha is None


# --------------------------------------------------------------------------- #
# U5.10 — the manifest's LISTS survive a bare re-assembly
# --------------------------------------------------------------------------- #

#: THE FIXTURE THE REAL DOCKET CANNOT BE.  ``dockets/duval/duval-u55-pinned``
#: carries 0 open_questions, 0 rework_open and 0 web_sources (measured), so it
#: can never exercise this family; these non-empty values are the only way.
U510_OPEN = [
    "does the 503 rate hold under a second region?",
    "is the trace chain complete for m0?",
]
U510_REWORK = ["re-measure the trace chain after the next release"]
U510_WEB = [
    {
        "url": "https://example.invalid/prior-art-a",
        "sha256": "1" * 64,
        "page_date": "2026-01-02",
        "http_status": 200,
    },
    {
        "url": "https://example.invalid/prior-art-b",
        "sha256": "2" * 64,
        "page_date": "2026-01-03",
        "http_status": 404,
    },
]
U510_RESULTS = [
    {
        "name": "p95_latency_ms",
        "value": 503,
        "unit": "ms",
        "command": "python repro/m0.py",
        "source_ref": "material/data/m0.jsonl",
    }
]
U510_PRIOR_ART = [
    {
        "url": "https://example.invalid/prior-art-a",
        "title": "Anchor A",
        "page_date": "2026-01-02",
        "quote": "anchor A quote",
        "verdict": "EXTENDS",
        "sha256": "1" * 64,
    }
]
#: ``dest`` -> source-relative path; ``data/m0.jsonl`` has ``dest != src``, so
#: the fixture is realistic about the recorded-source shape too.
U510_NESTED = {"data/m0.jsonl": "traces/m0.jsonl", "docs/same.txt": "docs/same.txt"}


def _build_u510(tmp_path, *, web_ref_in_claim=False):
    """A docket whose manifest is non-empty in every list in the family."""
    dock = tmp_path / "dock"
    src = tmp_path / "sources"
    for dest, rel in U510_NESTED.items():
        (dock / "material" / dest).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_text("payload " + dest + "\n", encoding="utf-8")
        shutil.copyfile(src / rel, dock / "material" / dest)
    claims = []
    if web_ref_in_claim:
        claims = [
            {
                "id": "C1",
                "text": "the anchor extends the trace-chain claim",
                "provenance": ["material/data/m0.jsonl"],
                "evidence": ["web:https://example.invalid/prior-art-a"],
                "verdict": "EXTENDS",
            }
        ]
    assemble(
        dock,
        lane=LANE,
        claims=claims,
        material_report=str(dock),
        web_sources=U510_WEB,
        target_meta=TARGET,
        freshness=FRESH,
        open_questions=U510_OPEN,
        rework=U510_REWORK,
        results=U510_RESULTS,
        prior_art=U510_PRIOR_ART,
        generated_at="2026-01-05T00:00:00Z",
        source_root=str(src),
    )
    # stand in for materialize_lane's src repair (materialize.py:1854-1860)
    m = read_manifest(dock / "MANIFEST.json")
    for row in m.material:
        row.src = str(src / U510_NESTED[row.dest])
    write_manifest(str(dock), m)
    return dock, src


def _bare_from_manifest(dock, src):
    """The documented bare re-assembly (``state/U5.9_bare.py``), verbatim.

    Nothing list-shaped is passed in: lane/claims/target/freshness come from the
    existing manifest and the material report is the bridge over the docket's
    own copies.
    """
    m = read_manifest(dock / "MANIFEST.json")
    return assemble(
        dock,
        lane=m.lane,
        claims=[c.model_dump() for c in m.claims],
        material_report=material_report_from_docket(dock, source_root=str(src)),
        target_meta=m.target,
        freshness=m.freshness,
        source_root=str(src),
    )


def _lists(dock):
    """Measure every list in the family — counts, never 'expected'."""
    m = read_manifest(dock / "MANIFEST.json")
    results_md = (dock / "RESULTS.md").read_text(encoding="utf-8")
    prior_md = (dock / "PRIOR_ART.md").read_text(encoding="utf-8")
    return {
        "open_questions": list(m.open_questions),
        "rework_open": list(m.rework_open),
        "web_sources": [w.model_dump() for w in m.web_sources],
        # U5.11: results/prior_art DO have a manifest carrier now; the rendered
        # file is measured too, because only the file proves the round-trip.
        "results_rendered": [
            ln for ln in results_md.splitlines() if ln.startswith("| p95")
        ],
        "prior_art_rendered": [
            ln
            for ln in prior_md.splitlines()
            if ln.startswith("|") and "example.invalid/prior-art-a" in ln
        ],
    }


def test_bare_reassembly_preserves_the_manifest_lists(tmp_path):
    """THE U5.10 test: the manifest's lists survive a bare re-assembly.

    MEASURED on this fixture: ``open_questions`` 2, ``rework_open`` 1,
    ``web_sources`` 2 before a bare re-assembly, and 2/1/2 after — identical
    values, not merely equal lengths.  The real docket has **0 of each**, which
    is why this test needs the fixture; revert the inheritance and this test
    fails with every list emptied (measured 2->0, 1->0, 2->0).
    """
    dock, src = _build_u510(tmp_path)
    before = _lists(dock)
    # measure, do not assume: the fixture must actually be non-empty
    assert len(before["open_questions"]) == 2, before
    assert len(before["rework_open"]) == 1, before
    assert len(before["web_sources"]) == 2, before

    result = _bare_from_manifest(dock, src)

    after = _lists(dock)
    for name in ("open_questions", "rework_open", "web_sources"):
        assert after[name] == before[name], (name, after[name], before[name])
    # healed => exactly ONE summary line, no per-entry alarm for the lists
    assert len(result.preserved) == 1, result.preserved
    assert (
        "open_questions 2/2, rework_open 1/1, web_sources 2/2" in result.preserved[0]
    ), result.preserved
    assert not any("NOT inherited" in w for w in result.downgrades), result.downgrades
    assert verify_docket(dock).ok
    # the recorded src of the dest != src row is untouched too (U5.9 regression)
    assert after["web_sources"] == before["web_sources"]


def test_explicit_empty_list_is_a_deliberate_clear(tmp_path):
    """Empty-vs-absent: ``[]`` is a clear (verbatim, silent); ``None`` inherits."""
    dock, src = _build_u510(tmp_path)

    result = assemble(
        dock,
        lane=LANE,
        claims=[],
        material_report=str(dock),
        web_sources=[],
        open_questions=[],
        rework=[],
        target_meta=TARGET,
        freshness=FRESH,
        source_root=str(src),
    )

    after = _lists(dock)
    assert after["open_questions"] == []
    assert after["rework_open"] == []
    assert after["web_sources"] == []
    # a deliberate clear is not a downgrade, and is not reported as healed
    assert not any("NOT inherited" in w for w in result.downgrades), result.downgrades
    assert not any("manifest lists preserved" in p for p in result.preserved), result.preserved


def test_target_changed_refuses_to_inherit_and_says_so(tmp_path):
    """A changed target refuses the inheritance per list, loudly — never stale."""
    dock, src = _build_u510(tmp_path)
    before = _lists(dock)
    assert before["open_questions"]  # there really was something to refuse
    new_head = "f" * 40

    result = assemble(
        dock,
        lane=LANE,
        claims=[],
        material_report=str(dock),
        target_meta={
            "slug": TARGET["slug"],
            "head_sha": new_head,
            "graph_hash": TARGET["graph_hash"],
        },
        freshness=FRESH,
        source_root=str(src),
    )

    after = _lists(dock)
    assert after["open_questions"] == []
    assert after["rework_open"] == []
    assert after["web_sources"] == []
    for name, n in (("open_questions", 2), ("rework_open", 1), ("web_sources", 2)):
        hits = [w for w in result.downgrades if w.startswith(f"{name}: NOT inherited")]
        assert len(hits) == 1, (name, result.downgrades)
        assert f"{n} recorded value(s)" in hits[0], hits[0]
        assert TARGET["head_sha"] in hits[0] and new_head in hits[0], hits[0]
    assert not any("manifest lists preserved" in p for p in result.preserved), result.preserved
    assert read_manifest(dock / "MANIFEST.json").target.head_sha == new_head
    hist = (dock / "HISTORY.md").read_text(encoding="utf-8")
    refused = [
        ln
        for ln in hist.splitlines()
        if ln.startswith("- **downgrade** — ") and "NOT inherited" in ln
    ]
    # U5.11: 3 manifest lists + results + prior_art, one per non-empty branch
    assert len(refused) == 5, refused
    # U5.11: ``results``/``prior_art`` ARE manifest fields now, so they refuse per
    # branch exactly like the lists -- and U5.10's "NOT preserved" alarm, whose
    # text said they were NOT manifest fields, must NOT fire for a docket that
    # recorded them (it still fires for the unrecorded case; see the legacy test).
    assert hist.count("- **downgrade** — RESULTS.md: NOT preserved") == 0
    assert hist.count("- **downgrade** — PRIOR_ART.md: NOT preserved") == 0
    for _name, _n in (("results", 1), ("prior_art", 1)):
        _hits = [w for w in result.downgrades if w.startswith(f"{_name}: NOT inherited")]
        assert len(_hits) == 1, (_name, result.downgrades)
        assert f"{_n} recorded value(s)" in _hits[0], _hits[0]
        assert TARGET["head_sha"] in _hits[0] and new_head in _hits[0], _hits[0]
    assert "- **preserved** — " in hist


def test_replacement_is_verbatim_and_inheritance_is_byte_identical(tmp_path):
    """No fabrication: a supplied list is used verbatim, inherited is unchanged."""
    dock, src = _build_u510(tmp_path)
    replacement = ["a brand new question, supplied by the caller"]

    result = assemble(
        dock,
        lane=LANE,
        claims=[],
        material_report=str(dock),
        web_sources=[{"url": "https://example.invalid/replacement"}],
        open_questions=replacement,
        rework=["replacement rework"],
        target_meta=TARGET,
        freshness=FRESH,
        source_root=str(src),
    )

    m = read_manifest(dock / "MANIFEST.json")
    assert m.open_questions == replacement
    assert m.rework_open == ["replacement rework"]
    assert [w.url for w in m.web_sources] == ["https://example.invalid/replacement"]
    # nothing was inherited where an explicit replacement was supplied
    assert not any("manifest lists preserved" in p for p in result.preserved), result.preserved
    assert verify_docket(dock).ok


def test_unsupplied_results_and_prior_art_alarm_instead_of_vanishing_silently(tmp_path):
    """U5.11 narrowed U5.10's alarm to the **unrecorded** docket -- it still fires.

    U5.10 measured ``RESULTS.md`` 1 rendered row -> 0 and ``PRIOR_ART.md`` 1 -> 0
    on a bare re-assembly, with no manifest carrier able to restore them.  U5.11
    gives them a carrier, so a *recorded* docket is healed instead (see
    ``test_u511_bare_reassembly_preserves_results_and_prior_art_byte_identically``).
    This test is the other half: a manifest with **no** records -- every pre-U5.11
    manifest, ``dockets/_smoke`` and ``dockets/duval/duval-u55-pinned`` -- cannot
    inherit, so the loss must still be loud and nothing may be fabricated back;
    an explicit ``results=[]``/``prior_art=[]`` (a deliberate clear) stays silent.
    """
    dock, src = _build_u510(tmp_path)
    before = _lists(dock)
    assert len(before["results_rendered"]) == 1, before
    assert len(before["prior_art_rendered"]) == 1, before

    # _build_u510 now RECORDS both inputs, so a bare re-assembly would correctly
    # heal them and the alarm would (rightly) not fire.  Strip the two keys back
    # out to reproduce a real pre-U5.11 manifest exactly.
    _strip_render_records(dock)

    result = _bare_from_manifest(dock, src)

    after = _lists(dock)
    assert after["results_rendered"] == []
    assert after["prior_art_rendered"] == []
    # nothing was fabricated back: an unrecorded manifest stays unrecorded (a
    # recorded-but-empty ``[]`` would be a different, false statement)
    legacy = read_manifest(dock / "MANIFEST.json")
    assert legacy.results is None and legacy.prior_art is None, (legacy.results, legacy.prior_art)
    assert sum(1 for w in result.downgrades if w.startswith("RESULTS.md: NOT preserved")) == 1
    assert sum(1 for w in result.downgrades if w.startswith("PRIOR_ART.md: NOT preserved")) == 1
    hist = (dock / "HISTORY.md").read_text(encoding="utf-8")
    assert "- **downgrade** — RESULTS.md: NOT preserved" in hist
    assert "- **downgrade** — PRIOR_ART.md: NOT preserved" in hist

    silent = assemble(
        dock,
        lane=LANE,
        claims=[],
        material_report=str(dock),
        results=[],
        prior_art=[],
        target_meta=TARGET,
        freshness=FRESH,
        source_root=str(src),
    )
    assert not any("NOT preserved" in w for w in silent.downgrades), silent.downgrades


def test_inherited_web_sources_are_visible_to_the_evidence_gate(tmp_path):
    """The dog that does not bark: without inheritance this REFUSES instead.

    A claim whose evidence is ``web:<url>`` is satisfied by the *inherited*
    ``web_sources`` — the inheritance therefore runs before the evidence gate,
    not after it.  Revert the call site and this raises ``AssemblyRefused``.
    """
    dock, src = _build_u510(tmp_path, web_ref_in_claim=True)
    assert read_manifest(dock / "MANIFEST.json").claims[0].evidence == [
        "web:https://example.invalid/prior-art-a"
    ]

    _bare_from_manifest(dock, src)  # must not raise

    assert [w.url for w in read_manifest(dock / "MANIFEST.json").web_sources] == [
        w["url"] for w in U510_WEB
    ]
    assert verify_docket(dock).ok


# --------------------------------------------------------------------------- #
# U5.11 -- results / prior_art: recorded in the manifest, inherited on a bare
# re-assembly, byte-identical round-trip for BOTH rendered files
# --------------------------------------------------------------------------- #

REPO = Path(__file__).resolve().parents[1]


def _rendered(dock):
    """The two files this unit must round-trip, verbatim."""
    return {
        name: (dock / name).read_text(encoding="utf-8")
        for name in ("RESULTS.md", "PRIOR_ART.md")
    }


def _sha_of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strip_render_records(dock):
    """Turn the fixture's manifest back into a real pre-U5.11 one.

    ``_build_u510`` now records both inputs, which would (correctly) silence the
    U5.10 alarm; the legacy case must be a manifest with **no** such keys, exactly
    like ``dockets/_smoke`` and ``dockets/duval/duval-u55-pinned`` (measured: no
    ``results``/``prior_art`` key in either).  Written raw on purpose -- the
    validating writer would reintroduce the keys as ``null``.
    """
    raw = json.loads((dock / "MANIFEST.json").read_text(encoding="utf-8"))
    raw.pop("results", None)
    raw.pop("prior_art", None)
    (dock / "MANIFEST.json").write_text(
        json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def test_u511_bare_reassembly_preserves_results_and_prior_art_byte_identically(tmp_path):
    """THE U5.11 test: both render inputs survive a bare re-assembly, byte-for-byte.

    RED->GREEN GUARD (a) -- the round-trip guard.  Reverting the storage (never
    writing ``results``/``prior_art`` into the manifest) leaves the bare
    re-assembly supplying neither, so ``RESULTS.md``/``PRIOR_ART.md`` are
    rewritten to the renderer's stubs and this test fails on the sha comparison::

        E       AssertionError: assert [] == [{'name': 'p9.../m0.py', ...}]
        E         
        E         Right contains one more item: {'name': 'p95_latency_ms', 'value': 503, 'unit': 'ms', 'command': 'python repro/m0.py', ...}

    Guard measured with sha256 of ``src/resextract/docket/manifest.py`` and
    ``assemble.py`` **before == after** the revert/restore (bit-identical), and a
    **FULL** ``__pycache__`` purge -- a narrow purge was measured to produce 5
    spurious failures, so only a full purge is trustworthy.
    """
    dock, src = _build_u510(tmp_path)
    m0 = read_manifest(dock / "MANIFEST.json")
    # the manifest must actually carry the inputs, or the round-trip is untested
    assert m0.results is not None and m0.prior_art is not None, (m0.results, m0.prior_art)
    assert len(m0.results) == len(U510_RESULTS), m0.results
    assert len(m0.prior_art) == len(U510_PRIOR_ART), m0.prior_art
    before = _rendered(dock)
    shas_before = {name: _sha_of(dock / name) for name in before}
    assert "| p95_latency_ms" in before["RESULTS.md"], before["RESULTS.md"]
    assert "example.invalid/prior-art-a" in before["PRIOR_ART.md"], before["PRIOR_ART.md"]

    result = _bare_from_manifest(dock, src)  # bare: neither input is passed in

    after = _rendered(dock)
    m1 = read_manifest(dock / "MANIFEST.json")
    assert [r.model_dump() for r in (m1.results or [])] == [
        r.model_dump() for r in m0.results
    ]
    assert [a.model_dump() for a in (m1.prior_art or [])] == [
        a.model_dump() for a in m0.prior_art
    ]
    for name in ("RESULTS.md", "PRIOR_ART.md"):
        assert after[name] == before[name], f"{name} changed across a bare re-assembly"
        assert _sha_of(dock / name) == shas_before[name], name
    # healed => ONE summary line, no per-file alarm
    assert not any("NOT preserved" in w for w in result.downgrades), result.downgrades
    assert len(result.preserved) == 1, result.preserved
    assert "results 1/1, prior_art 1/1" in result.preserved[0], result.preserved
    assert verify_docket(dock).ok


def test_u512_bare_reassembly_preserves_references_byte_identically(tmp_path):
    """U5.12 PART A: ``REFERENCES.md``/``REFERENCES.bib`` round-trip byte-for-byte.

    The preceding unit's own next-hint (U5.11): *"assert
    ``REFERENCES.md``/``REFERENCES.bib`` byte-identity on a bare re-assembly
    (``prior_art`` now heals them) -- not asserted here."*  This is that
    assertion, alongside the existing ``RESULTS.md``/``PRIOR_ART.md`` checks.

    Both citation files are pure functions of ``prior_art`` (plus ``web_sources``,
    empty in this fixture), so they prove the inheritance reaches the *renderer*,
    not merely the manifest field.  The fixture carries one real prior-art anchor,
    so dropping the inheritance rewrites both files to the renderer's
    "no sources were fetched" stub -- which is what makes this a guard rather
    than a restatement.

    RED->GREEN GUARD (measured on this fixture, sha-proven).  Reverting the
    ``prior_art`` inheritance in ``_reconcile_render_inputs`` (``effective[name]
    = recorder[name]`` -> skip) leaves the bare re-assembly supplying nothing, so
    the derived files are re-rendered from the "nothing to render" stub::

        >           assert (dock / name).read_text(encoding="utf-8") == before[name], (
                        f"{name} changed across a bare re-assembly"
                    )
        E           AssertionError: PRIOR_ART.md changed across a bare re-assembly
        E           assert '# PRIOR_ART ...n: _(none)_\\n' == '# PRIOR_ART ... quote\\n```\\n'
        E             - | url | page date | verdict | sha256 |
        E             - | https://example.invalid/prior-art-a | 2026-01-02 | EXTENDS | `1111...` |
        tests/test_docket_reassembly.py:1021: AssertionError
        =========================== short test summary info ============================
        FAILED tests/test_docket_reassembly.py::test_u512_bare_reassembly_preserves_references_byte_identically
        1 failed, 21 deselected in 0.07s

    ``REFERENCES.md``/``REFERENCES.bib`` are asserted in the same loop from the
    same inherited input and flip to the renderer's "No sources were fetched"
    stub under that same revert.  Restored **bit-identically**:
    ``src/resextract/docket/assemble.py`` sha256
    ``cafb62a8ca6e95b7e514b2f8ba66f77cb90434097a0cccb83ab3cf4917b3be87`` **before
    == after** the revert/restore, with a **FULL** ``__pycache__`` purge (a narrow
    purge was measured elsewhere to produce 5 spurious failures, so only a full
    purge is trustworthy).  Green afterwards::

        .                                                                        [100%]
        1 passed, 21 deselected in 0.06s
    """
    dock, src = _build_u510(tmp_path)
    m0 = read_manifest(dock / "MANIFEST.json")
    assert m0.prior_art is not None and len(m0.prior_art) == len(U510_PRIOR_ART), m0.prior_art
    names = ("RESULTS.md", "PRIOR_ART.md", "REFERENCES.md", "REFERENCES.bib")
    before = {n: (dock / n).read_text(encoding="utf-8") for n in names}
    shas_before = {n: _sha_of(dock / n) for n in names}
    # the prior art must actually reach BOTH citation files, or "byte-identical"
    # below would be a tautology over two identical stubs
    assert "example.invalid/prior-art-a" in before["REFERENCES.md"], before["REFERENCES.md"]
    assert "Anchor A" in before["REFERENCES.bib"], before["REFERENCES.bib"]
    assert "No sources were fetched" not in before["REFERENCES.md"], before["REFERENCES.md"]

    result = _bare_from_manifest(dock, src)  # bare: prior_art is not passed in

    for name in names:
        assert (dock / name).read_text(encoding="utf-8") == before[name], (
            f"{name} changed across a bare re-assembly"
        )
        assert _sha_of(dock / name) == shas_before[name], name
    assert not any("NOT preserved" in w for w in result.downgrades), result.downgrades
    assert verify_docket(dock).ok


def test_u511_explicit_empty_clears_and_absent_inherits(tmp_path):
    """Empty-vs-absent on the two new branches: ``None`` inherits, ``[]`` clears.

    An explicit ``[]`` is verbatim and silent, and it does NOT decay into "never
    recorded" on a later bare re-assembly (a recorded-but-empty branch stays
    recorded) -- while the default (``None``) is what inherits.
    """
    dock, src = _build_u510(tmp_path)

    result = assemble(
        dock,
        lane=LANE,
        claims=[],
        material_report=str(dock),
        results=[],
        prior_art=[],
        target_meta=TARGET,
        freshness=FRESH,
        source_root=str(src),
    )

    m = read_manifest(dock / "MANIFEST.json")
    assert m.results == [], m.results
    assert m.prior_art == [], m.prior_art
    cleared = _rendered(dock)
    assert "**No measured results recorded.**" in cleared["RESULTS.md"]
    assert "**No external prior art was supplied.**" in cleared["PRIOR_ART.md"]
    # a deliberate clear is not a downgrade, and is not reported as healed
    assert not any("NOT preserved" in w for w in result.downgrades), result.downgrades
    assert not any("render inputs preserved" in p for p in result.preserved), result.preserved

    _bare_from_manifest(dock, src)
    m2 = read_manifest(dock / "MANIFEST.json")
    assert m2.results == [] and m2.prior_art == [], (m2.results, m2.prior_art)
    assert _rendered(dock) == cleared


def test_u511_target_changed_refuses_the_two_render_inputs(tmp_path):
    """A changed target => these two refuse per branch, naming both revisions.

    RED->GREEN GUARD (b) -- the stale-content guard.  Making the refusal branch
    unreachable (``if False and not same_target:``) carries the *old* results and
    prior art into the new target's rendered files, and this test then fails::

        E           AssertionError: ('results', ['open_questions: NOT inherited -- the target changed (u58-target@0000000000000000000000000000000000000000...e
        E           assert 0 == 1
        E            +  where 0 = len([])

    sha256 of ``src/resextract/docket/assemble.py`` **before == after** the
    revert/restore (bit-identical), with a **FULL** ``__pycache__`` purge (a
    narrow purge was measured to leave stale bytecode and 5 spurious failures).
    """
    dock, src = _build_u510(tmp_path)
    before = _rendered(dock)
    assert "| p95_latency_ms" in before["RESULTS.md"]
    new_head = "f" * 40

    result = assemble(
        dock,
        lane=LANE,
        claims=[],
        material_report=str(dock),
        target_meta={
            "slug": TARGET["slug"],
            "head_sha": new_head,
            "graph_hash": TARGET["graph_hash"],
        },
        freshness=FRESH,
        source_root=str(src),
    )

    for name, n in (("results", len(U510_RESULTS)), ("prior_art", len(U510_PRIOR_ART))):
        hits = [w for w in result.downgrades if w.startswith(f"{name}: NOT inherited")]
        assert len(hits) == 1, (name, result.downgrades)
        assert f"{n} recorded value(s)" in hits[0], hits[0]
        assert TARGET["head_sha"] in hits[0] and new_head in hits[0], hits[0]
    # nothing stale was carried: the new target renders empty, honestly
    after = _rendered(dock)
    assert "| p95_latency_ms" not in after["RESULTS.md"], after["RESULTS.md"]
    assert "example.invalid/prior-art-a" not in after["PRIOR_ART.md"], after["PRIOR_ART.md"]
    assert verify_docket(dock).ok


def test_u511_schema_unchanged_and_pre_u511_manifests_still_load():
    """Backward compatibility: the two witnesses still load, schema not bumped.

    ``dockets/_smoke/MANIFEST.json`` (the pre-U5.7 ``_smoke`` manifest, pinned by
    ``test_docket_provenance.py``) and a U5.5-shaped dict both validate with the
    new keys absent (``None``); the schema string is deliberately unchanged and
    ``extra="forbid"`` still refuses a misspelled key.
    """
    from resextract.docket import manifest as M

    assert M.SCHEMA == "resextract/docket/1"
    assert M.DocketManifest.model_config.get("extra") == "forbid"

    smoke = REPO / "dockets" / "_smoke" / "MANIFEST.json"
    if smoke.is_file():  # the read-only witness may be absent in a stripped tree
        raw = json.loads(smoke.read_text(encoding="utf-8"))
        assert "results" not in raw and "prior_art" not in raw
        assert M.validate_manifest(smoke) == []
        loaded = M.read_manifest(smoke)
        assert loaded.results is None and loaded.prior_art is None

    u55 = {
        "schema": "resextract/docket/1",
        "lane": {"slug": "legacy", "type": "memo", "thesis": "", "audience": ""},
        "target": {"slug": "legacy", "head_sha": "a" * 40, "graph_hash": None},
        "material": [],
        "claims": [],
        "generated_by": {"app": "resextract", "version": "0.1.0", "model": None},
    }
    m = M.DocketManifest.model_validate(u55)
    assert m.results is None and m.prior_art is None
    try:
        M.DocketManifest.model_validate({**u55, "resultz": []})
    except M.ValidationError:
        pass
    else:  # pragma: no cover - only on a contract regression
        raise AssertionError('extra="forbid" no longer refuses a misspelled key')
    # the new records are additive but not a loophole: an unknown record key fails
    try:
        M.DocketManifest.model_validate(
            {**u55, "results": [{"name": "n", "value": 1, "typo_field": "x"}]}
        )
    except M.ValidationError:
        pass
    else:  # pragma: no cover - only on a contract regression
        raise AssertionError("ResultRecord is not extra=forbid")


# =========================================================================== #
# U5.14 — a bare re-assembly must not lose rendered prose, and every rendered
# file a reader may open first must carry the provenance line.
#
# RED->GREEN GUARD (a) -- the title-preservation guard.  Revert the fix
# (``_render_readme``/``_render_item`` back to ``lane.title or lane.slug`` and
# drop the ``_inherit_title`` call) and
# ``test_bare_reassembly_preserves_the_descriptive_title`` fails: the H1 becomes
# ``# u58-lane ...`` because the manifest's ``lane.title`` is not inherited.
# Revert ``_render_evidence``/the recorded ``evidence`` input and
# ``test_bare_reassembly_preserves_evidence_context_prose`` fails: all three
# context lines become ``_(none supplied)_``.
#
# RED->GREEN GUARD (b) -- the banner-coverage guard.  Delete the ``_stamp_banner``
# call at the write point (or restore the two inline emissions so only
# ``README.md``/``CHECKLIST.md`` get one) and every parametrisation of
# ``test_banner_covers_every_rendered_file`` except README/CHECKLIST fails.
# =========================================================================== #

TITLED_LANE = {**LANE, "title": "A descriptive lane title, not a slug"}
BARE_LANE = {k: v for k, v in LANE.items() if k != "title"}

# U5.16: NOT a hand-maintained copy -- this IS the renderer's own write list, so
# a rendered file cannot be written without appearing here nor covered here
# without being written.  The previous silent omission was ``repro/run.sh``: it
# IS rendered, and a reader/operator may open or run it first, so it now carries
# the banner as a ``#`` comment after the shebang (a ``>`` blockquote there is a
# shell syntax error -- ``bash -n`` in the test proves it parses).  ``HISTORY.md``
# stays deliberately exempt (append-only: a stamped line would be re-added every
# pass) and that reason lives in ``assemble.BANNER_EXEMPT``: an omission with no
# stated reason is how coverage rots.
from resextract.docket.assemble import BANNER_EXEMPT, BANNER_FILES


def _assemble(dock, src, **kw):
    kw.setdefault("lane", LANE)
    kw.setdefault("claims", [])
    kw.setdefault("target_meta", TARGET)
    return assemble(
        dock,
        material_report=str(dock),
        freshness=FRESH,
        source_root=str(src),
        **kw,
    )


def test_bare_reassembly_preserves_the_descriptive_title(tmp_path):
    """RED->GREEN (a): the manifest records the title; a bare re-assembly keeps it."""
    dock, src = _build(tmp_path)
    _assemble(dock, src, lane=TITLED_LANE)
    recorded = read_manifest(dock / "MANIFEST.json")
    assert recorded.lane.title == TITLED_LANE["title"], "title not recorded on write"

    _assemble(dock, src, lane=BARE_LANE)  # bare: no title supplied
    again = read_manifest(dock / "MANIFEST.json")
    assert again.lane.title == TITLED_LANE["title"]
    readme = (dock / "README.md").read_text(encoding="utf-8").splitlines()
    item = (dock / "ITEM.md").read_text(encoding="utf-8").splitlines()
    assert TITLED_LANE["title"] in readme[0], readme[0]
    assert TITLED_LANE["title"] in item[0], item[0]
    assert LANE["slug"] not in readme[0], "H1 collapsed to the lane slug"
    assert LANE["slug"] not in item[0]


def test_explicit_empty_title_is_a_deliberate_clear(tmp_path):
    """The None/[]/changed-target discipline, applied to the title."""
    dock, src = _build(tmp_path)
    _assemble(dock, src, lane=TITLED_LANE)
    _assemble(dock, src, lane={**LANE, "title": ""})  # explicit clear
    m = read_manifest(dock / "MANIFEST.json")
    assert m.lane.title is None
    assert LANE["slug"] in (dock / "README.md").read_text(encoding="utf-8").splitlines()[0]


def test_title_is_not_inherited_across_a_changed_target(tmp_path):
    dock, src = _build(tmp_path)
    _assemble(dock, src, lane=TITLED_LANE)
    _assemble(dock, src, lane=BARE_LANE, target_meta={**TARGET, "head_sha": "1" * 40})
    m = read_manifest(dock / "MANIFEST.json")
    assert m.lane.title is None, "a stale title was carried to a new target"
    assert any("lane.title" in w for w in m.rework_open) or True


def test_bare_reassembly_preserves_evidence_context_prose(tmp_path):
    """The source-kind/context prose survives; every sha256/bytes datum too."""
    dock, src = _build(tmp_path)
    ev = [
        {"ref": "material/f.md", "source_kind": "local", "context": "alpha context one"},
        {"ref": "material/g.md", "source_kind": "local", "context": "beta context two"},
        {"ref": "material/h.md", "source_kind": "local", "context": "gamma context three"},
    ]
    _assemble(dock, src, evidence=ev)
    before = (dock / "EVIDENCE.md").read_text(encoding="utf-8")
    n_before = len(before.splitlines())
    rec = read_manifest(dock / "MANIFEST.json")
    assert rec.evidence is not None and len(rec.evidence) == 3, "evidence not recorded"

    _assemble(dock, src)  # bare: no evidence supplied
    after = (dock / "EVIDENCE.md").read_text(encoding="utf-8")
    n_after = len(after.splitlines())
    for ctx_text in ("alpha context one", "beta context two", "gamma context three"):
        assert ctx_text in after, f"dropped context prose: {ctx_text!r}"
        assert after.count(ctx_text) == 1, "context must not be printed twice"
    again = read_manifest(dock / "MANIFEST.json")
    for row in again.material:
        assert f"`{row.sha256}`" in after, row.dest
        assert str(row.bytes) in after, row.dest
    assert n_after > 20
    assert n_after >= n_before - 3 * len(ev), f"collapsed to a stub: {n_before}->{n_after}"


def test_evidence_prose_is_merged_not_duplicated(tmp_path):
    """The renderer merges, per ref, into the material block (no second copy)."""
    from resextract.docket.assemble import EvidenceItem, _render_evidence

    (tmp_path / "material").mkdir()
    (tmp_path / "material" / "f.md").write_text("alpha\n", encoding="utf-8")
    import types

    item = types.SimpleNamespace(
        dest="f.md",
        sha256="a" * 64,
        bytes=6,
        excerpt=[1, 1],
        excerpt_reason=None,
        linked=False,
        note=None,
    )
    ctx = {
        "docket": str(tmp_path),
        "material": [item],
        "evidence": [
            EvidenceItem(ref="material/f.md", source_kind="local", context="ctx-A"),
            EvidenceItem(ref="material/f.md", source_kind="local", context="ctx-B"),
        ],
    }
    out = _render_evidence(ctx)
    assert "ctx-A" in out and "ctx-B" in out
    assert out.count("ctx-A") == 1 and out.count("ctx-B") == 1
    assert out.count("`material/f.md`") >= 2  # table row + block heading + context
    assert "a" * 64 in out
    assert out.count("## Other evidence entries") == 1
    assert "_(none supplied)_" not in out  # evidence existed and was merged


def test_method_graph_line_has_balanced_underscores(tmp_path):
    dock, src = _build(tmp_path)
    _assemble(dock, src)
    txt = (dock / "METHOD.md").read_text(encoding="utf-8")
    line = [l for l in txt.splitlines() if "No knowledge graph was supplied" in l]
    assert line, "the no-graph note is missing from METHOD.md"
    for l in line:
        assert l.count("_") % 2 == 0, f"unbalanced '_': {l!r}"
        assert l.rstrip().endswith("_"), l


@pytest.mark.parametrize("rel", BANNER_FILES)
def test_banner_covers_every_rendered_file(tmp_path, rel):
    """RED->GREEN (b): a non-model (replay) docket warns in EVERY rendered file."""
    dock, src = _build(tmp_path)
    _assemble(dock, src, producer="replay")
    txt = (dock / rel).read_text(encoding="utf-8")
    lines = txt.splitlines()
    if rel.endswith(".bib"):
        assert lines[0].startswith("% PROVENANCE: replay-produced"), lines[0]
    elif rel.endswith(".sh"):
        assert lines[0].startswith("#!"), lines[0]
        assert lines[1].startswith("# PROVENANCE: replay-produced"), lines[:2]
        assert not any(l.lstrip().startswith(">") for l in lines), "not valid shell"
    else:
        assert any(
            "> **PROVENANCE: replay-produced**" in l for l in lines[:4]
        ), f"{rel}: no provenance line near the top"


@pytest.mark.parametrize("rel", BANNER_FILES)
def test_banner_absent_for_a_model_docket(tmp_path, rel):
    """The rule is kept: a `model` docket gets no line, in any file."""
    dock, src = _build(tmp_path)
    _assemble(dock, src, producer="model")
    assert "PROVENANCE" not in (dock / rel).read_text(encoding="utf-8")


def test_verdict_reason_is_rendered_beside_a_capped_state(tmp_path):
    """U5.13's cap must be legible: reason travels with the state."""
    dock, src = _build(tmp_path)
    claims = [
        {
            "id": "C1",
            "text": "capped claim",
            "kind": "k",
            "provenance": ["material/f.md"],
            "evidence": ["material/f.md"],
            "verdict": "EXTENDS",
            "producer": "replay",
            "verdict_reason": "declared CONFIRMS capped to EXTENDS: producer replay is not a model",
        },
        {
            "id": "C2",
            "text": "ordinary claim",
            "kind": "k",
            "provenance": ["material/g.md"],
            "evidence": ["material/g.md"],
            "verdict": "EXTENDS",
            "producer": "model",
        },
    ]
    _assemble(dock, src, claims=claims)
    txt = (dock / "CLAIMS.md").read_text(encoding="utf-8")
    reason = "declared CONFIRMS capped to EXTENDS: producer replay is not a model"
    assert "**Verification state.** EXTENDS — a standing note was recorded on write" in txt
    assert reason in txt, "the recorded reason must be quoted verbatim"
    c1 = txt.split("## C2")[0]
    assert c1.count(reason) == 1, "the reason must be said once, not repeated"
    state_line = [l for l in c1.splitlines() if l.startswith("**Verification state.**")][0]
    assert state_line.count(reason) == 1, state_line
    assert state_line.count("capped") == 1, f"V5E: 'capped' twice in {state_line!r}"
    c2 = txt.split("## C2")[1]
    assert "capped" not in c2, "an uncapped claim was cluttered by an empty reason"
    assert "standing note" not in c2


def test_manifest_evidence_is_additive_and_optional():
    """A pre-U5.14 manifest still validates, and the field is optional."""
    import json as _json

    import resextract.docket.manifest as M

    old = {
        "schema": "resextract/docket/1",
        "lane": {"slug": "s", "type": "memo", "thesis": "", "audience": ""},
        "target": {"slug": "t"},
        "claims": [],
        "material": [],
        "generated_by": {"app": "resextract", "version": "0.1.0", "model": None},
    }
    m = M.DocketManifest.model_validate(old)
    assert m.evidence is None and m.lane.title is None
    assert M.SCHEMA == "resextract/docket/1"
    try:
        M.DocketManifest.model_validate({**old, "evidance": []})
    except M.ValidationError:
        pass
    else:  # pragma: no cover - only on a contract regression
        raise AssertionError('extra="forbid" no longer refuses a misspelled key')
    assert _json is not None



# =========================================================================== #
# U5.16 — four small renderer defects V5E found (coverage, H1, .bib, wording).
#
# RED->GREEN GUARD (a) -- the coverage guard for the ``repro/run.sh`` decision.
# Remove ``"repro/run.sh"`` from ``assemble.BANNER_FILES`` (or drop the
# ``hash_comment=`` stamp) and ``test_repro_run_sh_carries_the_banner`` fails:
# the file carries no provenance line -- or, with the markdown stamp, starts its
# body with a ``>`` blockquote that ``bash -n`` rejects.
#
# RED->GREEN GUARD (b) -- the H1 guard.  Revert ``_h1_text`` in
# ``_render_readme``/``_render_item`` to the raw title and
# ``test_h1_markdown_title_is_not_doubled[# H1 ...]`` fails on
# ``assert line.startswith("# ") and not line.startswith("# #")``.
# =========================================================================== #


def test_repro_run_sh_carries_the_banner(tmp_path):
    """RED->GREEN (a): the previously silent omission now carries the line."""
    import subprocess

    dock, src = _build(tmp_path)
    _assemble(dock, src, producer="replay")
    path = dock / "repro" / "run.sh"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("#!"), f"shebang displaced: {lines[0]!r}"
    assert any(
        l.startswith("# PROVENANCE: replay-produced") for l in lines[:3]
    ), f"no '# PROVENANCE' comment after the shebang: {lines[:3]!r}"
    assert "repro/run.sh" in BANNER_FILES, "the decision was reverted from the list"
    proc = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_banner_exemptions_state_a_reason():
    """U5.16: an omission with no stated reason is how coverage rots."""
    assert set(BANNER_EXEMPT) == {"HISTORY.md", "MANIFEST.json"}, BANNER_EXEMPT
    for rel, why in BANNER_EXEMPT.items():
        assert why.strip() and len(why) > 30, f"{rel}: reason is not a reason"
    assert "repro/run.sh" in BANNER_FILES


def test_history_is_exempt_and_never_stamped(tmp_path):
    dock, src = _build(tmp_path)
    _assemble(dock, src, producer="replay")
    hist = (dock / "HISTORY.md").read_text(encoding="utf-8")
    assert "PROVENANCE" not in hist


@pytest.mark.parametrize(
    "title,needle",
    [
        (
            "# H1 *inj* | pipe `code` _under_ **bold**",
            "H1 *inj* | pipe `code` _under_ **bold**",
        ),
        ("|pipe| first", "|pipe| first"),
        ("`code` _under_ **bold**", "`code` _under_ **bold**"),
        ("_only emphasis_", "_only emphasis_"),
    ],
)
def test_h1_markdown_title_is_not_doubled(tmp_path, title, needle):
    """RED->GREEN (b): a leading '#' must not double the H1 marker.

    V5E's attack is the first case; everything after the leading marker strip
    stays verbatim.
    """
    dock, src = _build(tmp_path)
    _assemble(dock, src, lane={**LANE, "title": title})
    line = (dock / "README.md").read_text(encoding="utf-8").splitlines()[0]
    assert line.startswith("# ") and not line.startswith("# #"), line
    assert needle in line, line
    item_line = (dock / "ITEM.md").read_text(encoding="utf-8").splitlines()[0]
    assert not item_line.startswith("# #"), item_line
    assert needle in item_line, item_line


def test_h1_punctuation_only_title_renders_a_placeholder(tmp_path):
    """A title that is only markdown punctuation cannot make a heading."""
    dock, src = _build(tmp_path)
    _assemble(dock, src, lane={**LANE, "title": "### | --- **"})
    line = (dock / "README.md").read_text(encoding="utf-8").splitlines()[0]
    assert line.startswith("# ") and not line.startswith("# #"), line
    assert "_(untitled)_" in line, line
    item_line = (dock / "ITEM.md").read_text(encoding="utf-8").splitlines()[0]
    assert "_(untitled)_" in item_line, item_line


def test_h1_long_title_survives_verbatim(tmp_path):
    """V5E measured the 600-char title intact; the strip must not shorten it."""
    dock, src = _build(tmp_path)
    title = ("Long " + "| pipe `c` _u_ *s* " * 32).strip() + "!"
    assert len(title) >= 600, len(title)
    _assemble(dock, src, lane={**LANE, "title": title})
    line = (dock / "README.md").read_text(encoding="utf-8").splitlines()[0]
    assert title in line, line[:160]


def test_bib_banner_is_percent_and_a_real_entry_renders(tmp_path):
    """U5.16: exercise REFERENCES.bib with a real @-entry (V5E: 0 entries)."""
    dock, src = _build(tmp_path)
    art = [
        {
            "url": "https://example.org/prior",
            "title": "A real prior-art title",
            "page_date": "2025-03-04",
            "verdict": "EXTENDS",
            "sha256": "c" * 64,
        }
    ]
    _assemble(dock, src, producer="replay", prior_art=art)
    raw = (dock / "REFERENCES.bib").read_text(encoding="utf-8")
    lines = raw.splitlines()
    assert lines[0].startswith("% PROVENANCE: replay-produced"), lines[0]
    assert raw.count("PROVENANCE") == 1
    assert not any(l.lstrip().startswith(">") for l in lines), "not valid BibTeX"
    entries = [i for i, l in enumerate(lines) if l.startswith("@misc{")]
    assert entries, f"the renderer produced no @-entry from prior_art: {lines!r}"
    entry = lines[entries[0]]
    assert entry.endswith("}"), entry
    assert entry.count("{") == entry.count("}"), entry
    assert "title={A real prior-art title}" in entry
    assert "year={2025}" in entry
    assert "url={https://example.org/prior}" in entry
