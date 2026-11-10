#!/usr/bin/env python3
"""verdict_semantics.py - classify an exit code as evidence about a card's work, or not.

WHY THIS FILE EXISTS (unit VERDICT-REFUSAL-SEMANTICS, measured): two cards in one sweep
settled `failed` without a single measurement of their own artefact --
RECORD-REFRESH (exec b0b2ccf1) settled `failed exit-4` while its handoff showed
insertions-only edits, prefix sha256 equality on both files, guard exit 0 before and
after, and a clean self-test; RECLAIM-ACCEPTANCE (exec 83f801aa) settled `failed
no-verdict` with `command: null`. Exit 4 is the ledger cap and pytest's usage error; exit
2 preflight and argparse; 3 budget; 8 projection; 12 prereg; 13 tree-moved; 14 the cell's
cap-gate reconciliation (the ledger and the rows disagree, so no artefact was measured).
None of them can be evidence that a card's artefact is wrong.

CONTRACT
  * the numbers are NOT copied here: `exit_codes.EXIT_TABLE` is the one table, imported,
    and a code the table carries but this module does not classify (or the reverse)
    raises at import, so drift is loud instead of silent.
  * `classify(code) -> "verified_pass" | "verified_fail" | "unstamped_refusal"`.
  * `is_refusal(code)` is true only for `unstamped_refusal`.

    python3 verdict_semantics.py         # print the partition

Stdlib only, no network, no requests. `VERDICT_SEMANTICS_EXIT_CODES_DIR` overrides the
directory `exit_codes` is imported from; it exists so a test can prove red on a copy with
a fake code, never so production can pick a different table.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXIT_CODES_DIR = os.path.normpath(os.path.join(HERE, os.pardir, "longrun"))
EXIT_CODES_DIR = os.environ.get("VERDICT_SEMANTICS_EXIT_CODES_DIR", DEFAULT_EXIT_CODES_DIR)
if EXIT_CODES_DIR not in sys.path:
    sys.path.insert(0, EXIT_CODES_DIR)

import exit_codes  # noqa: E402  (path set above: the one table)

VERIFIED_PASS = "verified_pass"
VERIFIED_FAIL = "verified_fail"
UNSTAMPED_REFUSAL = "unstamped_refusal"
VERDICTS = (VERIFIED_PASS, VERIFIED_FAIL, UNSTAMPED_REFUSAL)

# The partition. Keys only -- every name, meaning and raise site comes from exit_codes.
MEASURING = {
    0: VERIFIED_PASS,   # completed, gates wrote their verdicts
    1: VERIFIED_FAIL,   # crashed on the artefact's own code path
    5: VERIFIED_FAIL,   # runner crashed on the artefact
    6: VERIFIED_FAIL,   # the run's own length/behaviour failed
    9: VERIFIED_FAIL,   # grader and analyser disagree about the same rows
    10: VERIFIED_FAIL,  # grade stage ran and did not pass
    11: VERIFIED_FAIL,  # analyse stage ran and did not pass
}
# 14 is the cell-level cap-gate refusal (`capgate-unrecorded`): the runner's exit
# reconciliation found the ledger and the rows disagree, so the spend is untrustworthy and
# nothing about the artefact was measured. It is a refusal for the same reason 4 is.
REFUSING = frozenset({2, 3, 4, 7, 8, 12, 13, 14})

CLASSIFICATION = dict(MEASURING)
CLASSIFICATION.update({code: UNSTAMPED_REFUSAL for code in REFUSING})


class UnclassifiedExitCode(KeyError):
    """Raised for a code that is not in the partition -- never guessed."""


def table_codes():
    """The codes `exit_codes.EXIT_TABLE` actually carries, as ints."""
    return {int(code) for code in exit_codes.EXIT_TABLE}


def classified_codes():
    """The codes this module classifies."""
    return set(CLASSIFICATION)


def unclassified_in_table():
    """Codes the one table declares that this module does not classify."""
    return sorted(table_codes() - classified_codes())


def classified_but_absent():
    """Codes this module classifies that the one table does not declare."""
    return sorted(classified_codes() - table_codes())


def check_partition():
    """Raise unless the table and the partition cover exactly the same codes."""
    missing = unclassified_in_table()
    extra = classified_but_absent()
    if missing or extra:
        raise RuntimeError(
            "exit-code partition drift: unclassified in exit_codes.EXIT_TABLE=%s; "
            "classified but absent from EXIT_TABLE=%s. Add the code to MEASURING or "
            "REFUSING in %s and to docs/VERDICT-SEMANTICS.md." % (missing, extra, __file__)
        )


def classify(exit_code):
    """Classify one exit code. Never defaults: an unknown code raises."""
    try:
        code = int(exit_code)
    except (TypeError, ValueError):
        raise UnclassifiedExitCode("not an integer exit code: %r" % (exit_code,))
    try:
        return CLASSIFICATION[code]
    except KeyError:
        raise UnclassifiedExitCode(
            "exit code %d is not classified (table carries %s)"
            % (code, sorted(table_codes()))
        )


def is_refusal(exit_code):
    """True only when the code refused before anything was measured."""
    return classify(exit_code) == UNSTAMPED_REFUSAL


def describe(exit_code):
    """One line for a handoff or a log: code, table name, verdict."""
    code = int(exit_code)
    entry = exit_codes.EXIT_TABLE.get(code, {})
    return "%d %s -> %s" % (code, entry.get("name", "?"), classify(code))


def main(argv=None):
    check_partition()
    for code in sorted(CLASSIFICATION):
        print(describe(code))
    return 0


check_partition()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
