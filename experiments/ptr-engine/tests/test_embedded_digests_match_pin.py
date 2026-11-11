"""GUARD — no artefact may quote a harness digest that is not the pin's current one.

The defect class (HARNESS-PIN-GEN5): a page, a cached copy or a record keeps a digest
that *used to be* the pin.  It reads as authority, a launcher copies it, and the cell
dies at ``cell.py`` stage 2/7 with "harness changed mid-cell".  Every individual page is
internally consistent; the tree is not.

THE PREDECESSOR LOOPHOLE — the reason the last attempt at this guard did not work.  A
guard that asks only *"is this digest somewhere in the supersedes chain?"* is satisfied
by **every past generation**, because the chain records all of them by design.  So an
artefact that regressed from generation 5 back to generation 4 stayed green: the
regressed value was found in the supersedes chain and accepted as a legitimate
predecessor.  That guard could never redden on the defect it was written for.

This guard asks two separate questions, and the separation is the fix:

  Q1  POSITIONAL — each **live declaration** must equal the pin's current
      ``harness_sha256``: the pin's own top-level field, the cached copy's
      ``harness_pin.harness_sha256`` / ``launch_must_pass`` / ``generation``, and every
      ``--expect-harness <64-hex>`` a covered page tells a launcher to pass.  A value
      that also appears inside a supersedes block does **not** satisfy Q1 at the place
      where it is being *used*.

  Q2  EMBEDDED — every full 64-hex string in a covered file is either the pin's current
      value, or it sits in a slot that explicitly records a predecessor:
        * JSON: an ancestor key matching ``SUPERSEDED_SLOT`` (supersed / previous /
          predecessor / pending_advance / old_block / preserved_verbatim);
        * markdown: the same line carries the marker ``<!-- predecessor -->``;
        * a ``DATED_RECORD`` file (an audit snapshot that names its own audit time) may
          quote any digest the pin record already names — reporting what was recorded at
          audit time is its job — but never in a Q1 position.

Covered files: the pin, the cached copy, the launch/runbook pages a launcher reads, and
the dated audit twins.  NOT covered, deliberately: per-run transcripts
(``measure/cell-*.json``, ``measure/run-a-star.json``, ``measure/*/manifests/*``) — a
record of what a finished run passed is a dated observation, not a claim about what to
pass now, and policing it would paint the guard red forever.

RED PROOF (recorded in ``orchestration/handoffs/HARNESS-PIN-GEN5.json``): point
``EMBED_DIGEST_ROOT`` at a copy whose ``measure/GRID-PARAMS.json`` has
``harness_pin.harness_sha256`` set back to generation 4's digest — a *non-supersedes*
position — and Q1 reddens naming the file, the embedded value and the pinned value,
even though that same value is still inside the copy's ``supersedes`` block.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

PIN_REL = "experiments/ptr-engine/measure/HARNESS-PIN.json"
GRID_PARAMS_REL = "experiments/ptr-engine/measure/GRID-PARAMS.json"

#: Files a launcher or a reader takes the launch digest from.  Q1 and Q2 both apply.
CURRENT_ONLY = (
    PIN_REL,
    GRID_PARAMS_REL,
    "docs/GRID-PARAMS.md",
    "docs/GRID-RUNBOOK.md",
    "docs/GRID-SHAPE.md",
)

#: Audit snapshots: they name their own audit time and report what they read.  Q2 is
#: relaxed to "any digest the pin record knows"; Q1 still applies.
DATED_RECORD = (
    "experiments/ptr-engine/measure/LAUNCH-PACKAGE.json",
    "docs/LAUNCH-PACKAGE.md",
    "experiments/ptr-engine/measure/LAUNCH-CONTRACT-DIFF.json",
    "docs/LAUNCH-CONTRACT-DIFF.md",
    "measure/LAUNCH-CONTRACT-DIFF.json",
)

#: A JSON path segment that marks its whole subtree as RECORDED (not live) provenance.
SUPERSEDED_SLOT = re.compile(
    r"supersed|previous|predecessor|pending_advance|old_block|preserved_verbatim|"
    r"observed_intermediate", re.I)

MARKDOWN_PREDECESSOR_MARKER = "<!-- predecessor -->"

HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
EXPECT_HARNESS = re.compile(r"--expect-harness[`\s]+([0-9a-f]{64})")

#: In a DATED_RECORD, only a digest presented as a HARNESS/pin value is this guard's
#: business; the same file legitimately quotes ledger/row/artefact shas as well.
HARNESS_CONTEXT = re.compile(r"harness|\bpin\b|pinned", re.I)

#: The recipe's names come from cell.py ITSELF, so adding a measurement input cannot
#: silently desync this guard from the thing that computes the digest.  The literal
#: below is the other half of the same guard: a REMOVAL still fails, because a
#: derivation that follows cell.py would happily follow a file out of the list.
EXPECTED_RECIPE_NAMES = ("analyze_stats.py", "arm_cd.py", "client.py", "fixture",
                         "grade_v5.py", "ptr_engine/layers.py", "run_longrun.py",
                         "tools/det_verify.py")


def _cell_module():
    """cell.py by path -- the owner of HARNESS_FILES and of the digest recipe."""
    import importlib.util

    path = Path(__file__).resolve().parents[1] / "longrun" / "cell.py"
    spec = importlib.util.spec_from_file_location("_pin_cell", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _recipe_names() -> tuple:
    """cell.HARNESS_FILES names + 'fixture'; cell.py is NOT in its own list."""
    return tuple(sorted([name for _path, name in _cell_module().HARNESS_FILES] + ["fixture"]))


def _root() -> Path:
    """The tree to judge.  ``EMBED_DIGEST_ROOT`` exists so a /tmp copy can be red-proved."""
    env = os.environ.get("EMBED_DIGEST_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[3]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _pin(root: Path) -> dict:
    return json.loads(_read(root, PIN_REL))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _combined(per_file: dict) -> str:
    """cell.py:329-341 — sha256 over sorted 'name:sha256\\n'."""
    h = hashlib.sha256()
    for name in sorted(per_file):
        h.update(("%s:%s\n" % (name, per_file[name])).encode("utf-8"))
    return h.hexdigest()


def _walk(obj, path=()):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from _walk(value, path + (str(key),))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk(value, path + (str(index),))
    else:
        yield path, obj


def _json_digests(root: Path, rel: str):
    """Yield (path_tuple, digest) for every full 64-hex string value in a JSON file."""
    doc = json.loads(_read(root, rel))
    for path, value in _walk(doc):
        if isinstance(value, str):
            for hit in HEX64.findall(value):
                yield path, hit


def _markdown_digests(root: Path, rel: str):
    """Yield (lineno, digest, line) for every full 64-hex on a covered page."""
    for lineno, line in enumerate(_read(root, rel).splitlines(), start=1):
        for hit in HEX64.findall(line):
            yield lineno, hit, line


def _known_digests(pin: dict) -> set:
    """Every digest the pin record itself names: current, superseded, and per-file."""
    known = set()
    for _path, value in _walk(pin):
        if isinstance(value, str):
            known.update(HEX64.findall(value))
    return known


# ----------------------------------------------------------------- Q1: live positions
def _live_declarations(root: Path):
    """Yield (where, declared_value) for every position a launcher READS a value from."""
    pin = _pin(root)
    yield (f"{PIN_REL}::harness_sha256", pin.get("harness_sha256"))

    gp = json.loads(_read(root, GRID_PARAMS_REL))
    block = gp.get("harness_pin", {})
    yield (f"{GRID_PARAMS_REL}::harness_pin.harness_sha256", block.get("harness_sha256"))
    must_pass = block.get("launch_must_pass", "") or ""
    hit = HEX64.search(must_pass)
    yield (f"{GRID_PARAMS_REL}::harness_pin.launch_must_pass", hit.group(0) if hit else must_pass)

    for rel in CURRENT_ONLY:
        if not rel.endswith(".md") or not (root / rel).exists():
            continue
        for lineno, line in enumerate(_read(root, rel).splitlines(), start=1):
            for value in EXPECT_HARNESS.findall(line):
                yield (f"{rel}:{lineno}", value)


def test_pin_matches_the_bytes_on_disk():
    """The authority must describe the tree it is in: same recipe, recomputed now."""
    root = _root()
    pin = _pin(root)
    names = {entry["name"] for entry in pin["files"]}
    assert names == set(_recipe_names()), (
        "the pin must name exactly cell.py's HARNESS_FILES + fixture; got %r, cell.py says %r"
        % (sorted(names), list(_recipe_names())))
    per_file = {entry["name"]: _sha256_file(root / entry["path"]) for entry in pin["files"]}
    recomputed = _combined(per_file)
    assert recomputed == pin["harness_sha256"], (
        "%s embeds harness_sha256 %s but the bytes on disk hash to %s (per-file: %s)"
        % (PIN_REL, pin["harness_sha256"], recomputed,
           ", ".join("%s=%s" % (n, per_file[n]) for n in sorted(per_file))))
    for entry in pin["files"]:
        assert entry["sha256"] == per_file[entry["name"]], (
            "%s::files[%s].sha256 %s does not match the file (now %s)"
            % (PIN_REL, entry["name"], entry["sha256"], per_file[entry["name"]]))


def test_the_recipe_names_are_the_literal_this_guard_pins():
    """A silent REMOVAL from HARNESS_FILES must fail, not be followed by the derivation."""
    assert _recipe_names() == EXPECTED_RECIPE_NAMES, (
        "cell.py's HARNESS_FILES + fixture is %r but this guard is pinned to %r: if the "
        "list really changed, re-cut the pin and update EXPECTED_RECIPE_NAMES in the same "
        "commit; if it did not, a measurement input was dropped"
        % (list(_recipe_names()), list(EXPECTED_RECIPE_NAMES)))


def test_the_pin_covers_the_compiler_and_the_window_layers():
    """PREREG-COMPACTION.md instrument requirement 6: E7 edits both, so both are pinned."""
    names = {name for _path, name in _cell_module().HARNESS_FILES}
    assert {"arm_cd.py", "ptr_engine/layers.py"} <= names, (
        "E7 changes experiments/ptr-engine/longrun/arm_cd.py and "
        "experiments/ptr-engine/ptr_engine/layers.py, so a digest that does not cover them "
        "cannot invalidate a run; cell.HARNESS_FILES names %r" % sorted(names))
    pin_names = [entry["name"] for entry in _pin(_root())["files"]]
    assert sorted(pin_names) == sorted(names | {"fixture"}), (
        "%s::files must name exactly cell.HARNESS_FILES + fixture; pin=%r cell=%r"
        % (PIN_REL, sorted(pin_names), sorted(names | {"fixture"})))


def test_the_baseline_tool_mirrors_the_recipe():
    """harness_baseline.py keeps its own copy of the list; a copy that drifts is a blind spot."""
    import importlib.util

    path = Path(__file__).resolve().parents[1] / "tools" / "harness_baseline.py"
    spec = importlib.util.spec_from_file_location("_pin_baseline", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mirrored = tuple(sorted(name for name, _rel in mod.HARNESS_FILES))
    owned = tuple(sorted(name for _path, name in _cell_module().HARNESS_FILES))
    assert mirrored == owned, (
        "experiments/ptr-engine/tools/harness_baseline.py::HARNESS_FILES is %r but "
        "cell.py's is %r: a baseline taken over the short list cannot see the files it "
        "omits" % (list(mirrored), list(owned)))


def test_live_declarations_equal_the_pinned_digest():
    """Q1 — the predecessor loophole: being in the chain does not make a value current."""
    root = _root()
    pinned = _pin(root)["harness_sha256"]
    bad = []
    for where, declared in _live_declarations(root):
        if declared != pinned:
            bad.append("%s declares %s but the pin is %s" % (where, declared, pinned))
    assert not bad, (
        "a LIVE digest position disagrees with %s::harness_sha256 (%s):\n  %s\n"
        "(a value that also appears inside a supersedes block is still wrong HERE: this "
        "is the position a launcher reads)" % (PIN_REL, pinned, "\n  ".join(bad)))


# ------------------------------------------------- Q2: embedded digests, by provenance
def test_no_foreign_digest_in_current_only_files():
    """Q2 — current-only surfaces may quote the pin, and nothing else, outside a supersedes slot."""
    root = _root()
    pinned = _pin(root)["harness_sha256"]
    bad = []

    pin = _pin(root)
    current_files = {entry["sha256"] for entry in pin["files"]}
    for path, value in _json_digests(root, PIN_REL):
        if any(SUPERSEDED_SLOT.search(seg) for seg in path):
            continue
        if value == pinned:
            continue
        # the pin's own per-file shas: recorded hashes of the six inputs, not the
        # combined harness digest, and they are re-verified against the bytes inside
        # tests[test_pin_matches_the_bytes_on_disk].
        if len(path) == 3 and path[0] == "files" and path[2] == "sha256" and value in current_files:
            continue
        bad.append("%s::%s embeds %s but the pin is %s"
                   % (PIN_REL, ".".join(path), value, pinned))

    for rel in CURRENT_ONLY:
        if rel == PIN_REL or not (root / rel).exists():
            continue
        if rel.endswith(".json"):
            for path, value in _json_digests(root, rel):
                if any(SUPERSEDED_SLOT.search(seg) for seg in path):
                    continue
                if value == pinned:
                    continue
                bad.append("%s::%s embeds %s but the pin is %s"
                           % (rel, ".".join(path), value, pinned))
        else:
            for lineno, value, line in _markdown_digests(root, rel):
                # a page prints several shas; this guard judges the ones it presents as a
                # HARNESS value (a pin row, a --expect-harness line).  A current per-file
                # sha (fixture, ledger, projection) is a pinned value, not a defect.
                if not HARNESS_CONTEXT.search(line):
                    continue
                if value == pinned or value in current_files or MARKDOWN_PREDECESSOR_MARKER in line:
                    continue
                bad.append("%s:%d embeds %s but the pin is %s :: %s"
                           % (rel, lineno, value, pinned, line.strip()[:160]))
    assert not bad, "embedded digests that are not the pin's current one:\n  " + "\n  ".join(bad)


def test_dated_records_quote_only_digests_the_pin_chain_knows():
    """Q2 for audit snapshots: they may quote history, never an invented digest."""
    root = _root()
    pinned = _pin(root)["harness_sha256"]
    known = _known_digests(_pin(root)) | {pinned}
    bad = []
    for rel in DATED_RECORD:
        if not (root / rel).exists():
            continue
        if rel.endswith(".json"):
            for path, value in _json_digests(root, rel):
                if value in known or not HARNESS_CONTEXT.search(".".join(path)):
                    continue
                bad.append("%s::%s embeds %s, which no generation of %s records (current %s)"
                           % (rel, ".".join(path), value, PIN_REL, pinned))
        else:
            for lineno, value, line in _markdown_digests(root, rel):
                if value in known or not HARNESS_CONTEXT.search(line):
                    continue
                bad.append("%s:%d embeds %s, which no generation of %s records (current %s)"
                           % (rel, lineno, value, PIN_REL, pinned))
    assert not bad, "dated records quoting digests the pin chain does not know:\n  " + "\n  ".join(bad)
