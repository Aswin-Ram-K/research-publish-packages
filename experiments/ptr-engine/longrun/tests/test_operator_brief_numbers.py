#!/usr/bin/env python3
"""Guard: every figure printed in docs/OPERATOR-BRIEF.md must be re-derivable from a
named artefact, on the same line, today.

Rule enforced here:
  * a figure is a decimal (``NN.NN``) or a fraction (``N/N``) after paths, dates and
    clock stamps are masked out of the line;
  * every figure-carrying line must name at least one artefact path on that same line;
  * that path must exist on disk;
  * the figure must appear literally in the artefact's bytes (commas normalised), so a
    hand-edited number in the prose goes RED instead of silently publishing.

Integers are deliberately out of scope: this test polices the two shapes the brief's
contract names (``NN.NN`` / ``N/N``), not every numeral.

Run:      python3 -m pytest experiments/ptr-engine/longrun/tests/test_operator_brief_numbers.py -q
Red proof: OB4_BRIEF=/tmp/ob4/OPERATOR-BRIEF.md python3 -m pytest ... -q   (expect failure)
"""
import json
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_BRIEF = ROOT / "docs" / "OPERATOR-BRIEF.md"
BRIEF = Path(os.environ.get("OB4_BRIEF", DEFAULT_BRIEF))

# An artefact path as the brief writes it: a workspace-relative path with a known suffix.
PATH_RE = re.compile(r"(?:docs|experiments|orchestration)/[A-Za-z0-9_./-]*\.(?:json|jsonl|md|py|sh)")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
CLOCK_RE = re.compile(r"\d{2}:\d{2}(?::\d{2})?Z?")
FIGURE_RE = re.compile(r"\d+\.\d+|\d+/\d+")

TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".py", ".sh"}


def lines_of_brief() -> list[str]:
    if not BRIEF.exists():
        pytest.fail(f"brief not found: {BRIEF}")
    return BRIEF.read_text(encoding="utf-8").splitlines()


def mask(line: str) -> str:
    """Blank out paths, dates and clock stamps so their digits are not read as figures."""
    out = PATH_RE.sub(" ", line)
    out = DATE_RE.sub(" ", out)
    out = CLOCK_RE.sub(" ", out)
    return out


def figures(line: str) -> list[str]:
    return FIGURE_RE.findall(mask(line))


def blocks(lines: list[str]) -> list[tuple[int, list[str]]]:
    """Markdown block = run of non-blank lines. A wrapped bullet is one block, so the path
    a figure leans on may sit on the bullet's continuation line."""
    out, cur, start = [], [], 1
    for i, line in enumerate(lines, start=1):
        if line.strip():
            if not cur:
                start = i
            cur.append(line)
        elif cur:
            out.append((start, cur))
            cur = []
    if cur:
        out.append((start, cur))
    return out


def normalise(text: str) -> str:
    return text.replace(",", "").replace("\u2009", "").replace("\u00a0", "")


def artefact_text(path: Path) -> str:
    return normalise(path.read_text(encoding="utf-8", errors="replace"))


def test_brief_exists_and_states_the_verdict():
    body = "\n".join(lines_of_brief())
    assert body.strip(), "brief is empty"
    assert "Overall: not adjudicable" in body, (
        "the brief must open its verdict with 'Overall: not adjudicable' unless an "
        "artefact genuinely supports an H1/H2/H3 'has evidence' cell"
    )


def test_every_figure_has_an_adjacent_path():
    """No figure may stand without an artefact in its own Markdown block."""
    missing = []
    for start, block in blocks(lines_of_brief()):
        joined = "\n".join(block)
        if not PATH_RE.findall(joined):
            for lineno, line in enumerate(block, start=start):
                for fig in figures(line):
                    missing.append((lineno, fig, line.strip()[:110]))
    assert not missing, "figures with no artefact path adjacent to them:\n" + "\n".join(
        f"  line {ln}: {fig!r} in {text!r}" for ln, fig, text in missing
    )


def test_every_referenced_path_exists():
    absent = []
    for lineno, line in enumerate(lines_of_brief(), start=1):
        for rel in PATH_RE.findall(line):
            if not (ROOT / rel).exists():
                absent.append((lineno, rel))
    assert not absent, "paths named in the brief that do not exist:\n" + "\n".join(
        f"  line {ln}: {rel}" for ln, rel in absent
    )


def test_every_figure_appears_in_a_named_artefact():
    """The number must be *in* the file, not merely next to its name."""
    bad = []
    for start, block in blocks(lines_of_brief()):
        joined = "\n".join(block)
        paths = list(dict.fromkeys(PATH_RE.findall(joined)))
        texts = {}
        for rel in paths:
            p = ROOT / rel
            if p.exists() and p.suffix in TEXT_SUFFIXES:
                texts[rel] = artefact_text(p)
        for lineno, line in enumerate(block, start=start):
            for fig in figures(line):
                if not any(fig in t for t in texts.values()):
                    bad.append((lineno, fig, paths))
    assert not bad, "figures that do not appear in any artefact named beside them:\n" + "\n".join(
        f"  line {ln}: {fig!r} not found in {paths}" for ln, fig, paths in bad
    )


def test_superseded_figures_appear_only_inside_the_withdrawal_table():
    """A withdrawn number may be named only where the page says it is withdrawn."""
    forbidden = {"0.8594": "55/64 row-denominator accuracy", "318.14": "withdrawn G7 p95"}
    offences = []
    for lineno, line in enumerate(lines_of_brief(), start=1):
        low = line.lower()
        for fig, why in forbidden.items():
            if fig in line and not any(k in low for k in ("withdraw", "superseded", "do not cite", "no replacement")):
                offences.append((lineno, fig, why))
    assert not offences, "withdrawn figures quoted without a withdrawal marker:\n" + "\n".join(
        f"  line {ln}: {fig} ({why})" for ln, fig, why in offences
    )


def test_json_companion_matches_brief_verdict():
    comp = ROOT / "experiments" / "ptr-engine" / "measure" / "OPERATOR-BRIEF.json"
    assert comp.exists(), f"missing machine companion: {comp}"
    doc = json.loads(comp.read_text(encoding="utf-8"))
    assert doc["unit"] == "OPERATOR-BRIEF-4"
    assert doc["verdict"]["overall"] == "not adjudicable"
    assert doc["cost"]["p95_comparisons_between_two_arms"] == 0
    assert doc["cost"]["tvs"]["events"] == 3
    assert doc["cost"]["tvs"]["censored"] == 20
    assert doc["plan"]["tranche_1"]["requests"] == 660
    assert doc["plan"]["tranche_1"]["remaining_after"] == 2559
