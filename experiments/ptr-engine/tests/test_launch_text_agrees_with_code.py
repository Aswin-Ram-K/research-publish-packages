"""CONTRACT-DIFF-RESIDUAL: launch TEXT must carry the same integer as the CODE it describes.

Two launch numbers are set by code but quoted by prose, and prose drifts silently while the
launch keeps working off the code:

  * ``--budget``      — the launcher's ``default=`` is what a bare run uses; its help string is
                        what an operator reads.  ``run_a_star.py:366`` said ``default=108`` while
                        its help on ``:367`` said ``67``.
  * ``per-arm rounds`` — the pool is ``TOOL_FETCH_ROUNDS_PER_ARM`` in the runner, overridable by
                        ``--fetch-rounds-per-arm``.  ``docs/GRID-PARAMS.md`` still asserted the
                        generation-1 constant (24) "with no override" after RUNNER-ROUNDS-48
                        landed the flag — and a stale sentence is what makes an operator *not
                        pass a flag that exists*.

Each test here must be able to FAIL.  Set ``LTA_ROOT`` to a mutated copy of the tree to prove it:
``LTA_ROOT=/tmp/lta-red/tree pytest <this file>``.

Offline by construction: reads three files, opens no socket, launches nothing.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ROOT = Path(os.environ.get("LTA_ROOT") or REPO)

LAUNCHER = "experiments/ptr-engine/tools/run_a_star.py"
RUNNER = "experiments/ptr-engine/longrun/run_longrun.py"
DOC = "docs/GRID-PARAMS.md"

BUDGET_ARG_RE = re.compile(r'ap\.add_argument\("--budget",\s*type=int,\s*default=(\d+)')
BUDGET_HELP_RE = re.compile(r"ledger allocation handed to cell\.py \(default (\d+)\)")
POOL_CONST_RE = re.compile(r"^TOOL_FETCH_ROUNDS_PER_ARM = (\d+)", re.M)
POOL_DOC_RE = re.compile(r"TOOL_FETCH_ROUNDS_PER_ARM = (\d+)")


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _launcher_budget_default() -> int:
    m = BUDGET_ARG_RE.search(_text(LAUNCHER))
    assert m, "--budget add_argument with an integer default= not found in %s" % LAUNCHER
    return int(m.group(1))


def _launcher_budget_help_int() -> int:
    m = BUDGET_HELP_RE.search(_text(LAUNCHER))
    assert m, ("the --budget help no longer says 'ledger allocation handed to cell.py "
               "(default N)' in %s" % LAUNCHER)
    return int(m.group(1))


def test_budget_help_integer_equals_default_choice():
    """The help string must name the number a bare launch actually uses."""
    default = _launcher_budget_default()
    quoted = _launcher_budget_help_int()
    assert quoted == default, (
        "--budget help says 'default %d' but default= is %d: an operator reading --help "
        "would launch the wrong allocation" % (quoted, default))


def test_budget_help_says_what_the_flag_is():
    """It is a per-cell ledger allocation, not a ceiling on requests sent."""
    launcher = _text(LAUNCHER)
    assert "ledger allocation handed to cell.py" in launcher
    assert "not a request ceiling" in launcher, (
        "the --budget help must say this is a ledger allocation, not a request ceiling")


def test_doc_per_arm_pool_equals_runner_constant():
    """docs/GRID-PARAMS.md must quote the constant that is actually in the runner."""
    m = POOL_CONST_RE.search(_text(RUNNER))
    assert m, "TOOL_FETCH_ROUNDS_PER_ARM not found in %s" % RUNNER
    constant = int(m.group(1))

    doc = _text(DOC)
    hits = [int(x) for x in POOL_DOC_RE.findall(doc)]
    assert hits, ("%s no longer quotes TOOL_FETCH_ROUNDS_PER_ARM at all: the per-arm pool is "
                  "then asserted only by code, with no human-facing figure" % DOC)
    assert hits[0] == constant, (
        "%s's first TOOL_FETCH_ROUNDS_PER_ARM figure is %d but the runner's constant is %d"
        % (DOC, hits[0], constant))


def test_doc_names_the_override_and_cites_the_source_lines():
    """The doc must point at the flag and at the lines that carry the pool."""
    doc = _text(DOC)
    assert "--fetch-rounds-per-arm" in doc, (
        "docs/GRID-PARAMS.md must name --fetch-rounds-per-arm as the override; without it the "
        "page reads as if the pool had no flag")
    assert "run_longrun.py:230" in doc, "docs/GRID-PARAMS.md must cite run_longrun.py:230"
    assert re.search(r"generation 1", doc, re.I), (
        "the superseded generation-1 value must stay recorded as a dated line, not be deleted")


def test_runner_override_flag_exists_by_name():
    """The doc's override is only honest while the flag is really registered."""
    runner = _text(RUNNER)
    assert re.search(r'ap\.add_argument\("--fetch-rounds-per-arm",\s*type=int,\s*'
                     r'default=TOOL_FETCH_ROUNDS_PER_ARM', runner), (
        "--fetch-rounds-per-arm is no longer registered against TOOL_FETCH_ROUNDS_PER_ARM")
    assert re.search(r"--fetch-rounds-per-arm must be a positive integer", runner), (
        "the non-positive refusal for --fetch-rounds-per-arm is gone")
