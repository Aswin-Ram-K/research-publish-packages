#!/usr/bin/env python3
"""claim_mode.py - THE claim resolver: a run may start without a hypothesis, but only
by DECLARING that it makes no claim.

Why this module exists (unit HYPOTHESIS-SMOKE-MODE, measured)
------------------------------------------------------------
Fixing G3's silence hole made ``--hypothesis`` mandatory on every live path:
``cell.py``'s ``_declared_hypothesis`` (cell.py:848-860) no longer defaults to PARM-1's
``primary`` (H2), so an ABSENT flag reaches ``eval_gate_prereg`` as ``NONE`` and is
refused with exit 12. The fix was right and it has two measured costs:

  * ``GATE-CHAIN-FIX`` had to edit three test files OUTSIDE its own write paths
    (``test_guards.py``, ``test_projection_calibration.py``, ``test_projection_modes.py``)
    to add ``--hypothesis H2`` to runs that exercise PLUMBING, not a hypothesis; and
  * ``LIVE-SMOKE-8`` -- the first cell that would ever produce a ``cell-*.gates.json`` --
    cannot legally run claim-free. Declaring ``H2`` to get past G3 would write rows into
    the arm files ``analyze_stats.py`` groups by arm, contaminating an arm comparison
    with a run that never intended to be in one.

The missing spelling is not "no flag" (silence) and not a hypothesis id (a claim the
cell does not make). It is a DECLARATION OF NO CLAIM: ``smoke`` (alias ``plumbing``).
This module resolves the flag into exactly one of two records or a refusal, and gives
the stats layer a way to refuse a claim-free cell BY NAME instead of filtering it out
of a group-by-arm.

The three resolved shapes
-------------------------
    resolve_claim("smoke")     -> {"mode": "smoke",      "claim": "none", "comparison_eligible": False}
    resolve_claim("plumbing")  -> {"mode": "smoke",      "claim": "none", "comparison_eligible": False}
    resolve_claim("H2")        -> {"mode": "hypothesis", "claim": "H2",   "comparison_eligible": True}

Anything else -- absent, empty, whitespace, an unknown spelling, or an explicit
``none`` -- raises :class:`ClaimRefusal`. Silence is NOT a claim and ``none`` is not
accepted as shorthand for the smoke declaration: the declaration has to say what it is.

The refusal class is not a new exit path. G3's silence refusal is raised by
``cell.py``:875-905 as a refused verdict which ``_enforce`` (cell.py:735) turns into
``Abort(EXIT_PREREG, "3c/7 G3 prereg gate", ...)`` -- i.e. the class is ``cell.Abort``
with code 12 (``exit_codes.EXIT_PREREG``). :class:`ClaimRefusal` carries that same code
and stage and :func:`as_abort` builds the very same ``cell.Abort``, so when the wiring
note in the handoff is applied the exit-code behaviour is unchanged: still 12, still
``Abort``, still at the G3 stage.

Row contract (what the runner must write)
-----------------------------------------
Every per-turn row carries two top-level fields, written once from the resolved claim:

    "claim": "none" | "H1" | "H2" | "H3"
    "comparison_eligible": false | true

Placement: top level of the row literal, immediately after the existing
``"arm": arm,`` key (``run_longrun.py:1563-1564``). ``row_fields(record)`` returns
exactly those two fields, so the runner change is a mechanical ``**row_fields(claim)``
or two literal keys. Rows written before this exists are NOT backfilled: an absent
pair is the LEGACY state (see :func:`assert_comparable`), never a claim-free one.

Statistical-layer helper
-------------------------
:func:`assert_comparable` is a PURE helper: it takes rows and raises
:class:`IncomparableClaim` whose message starts ``incomparable_claim`` when any row
declares ``claim: "none"`` (or contradicts its own claim), naming the offending cell.
It is deliberately importable without ``analyze_stats.py`` so the stats owner can wire
it in one call -- the same pattern as ``require_comparable``'s
``incomparable_provenance``: a named refusal, not a silent filter.

The invariant this module establishes, in one sentence: a run may start without a
hypothesis only by declaring that it makes no claim, and its rows can never enter a
comparison.

Offline: stdlib only, no request, no I/O.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from types import MappingProxyType

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                 # imported by path (tests) as well as by name
    sys.path.insert(0, _HERE)

from exit_codes import EXIT_PREREG        # noqa: E402  the one exit-code table

__all__ = [
    "CLAIM_IDS", "SPCC_CLAIM_IDS", "ALL_CLAIM_IDS", "CLAIM_NONE", "MODE_HYPOTHESIS",
    "MODE_SMOKE", "SMOKE_SPELLINGS",
    "ROW_FIELDS", "INCOMPARABLE_CLAIM", "ClaimRecord", "ClaimRefusal",
    "IncomparableClaim", "resolve_claim", "refusal_message", "row_fields", "as_abort",
    "check_prereg_claim", "smoke_prereg_verdict", "assert_comparable",
]

MODE_SMOKE = "smoke"
MODE_HYPOTHESIS = "hypothesis"
CLAIM_NONE = "none"
#: The PARM-1 claim ids (``experiments/ptr-engine/measure/PREREG-ARM-RUN.json``).
CLAIM_IDS = ("H1", "H2", "H3")
#: The PREREG-SPCC experiment ids (``research-seed-concepts/PREREG-SPCC.md``). A cell
#: that declares one of these makes a claim of its own namespace, so it is
#: comparison_eligible exactly as an H id is -- but G3 validates it against the SPCC
#: document's own terms (request ceiling, checkpoint count), never against PARM-1's.
SPCC_CLAIM_IDS = ("E1", "E2", "E3", "E4", "E5", "E6")
#: Every id a cell may declare, in the order the refusal message names them.
ALL_CLAIM_IDS = CLAIM_IDS + SPCC_CLAIM_IDS
#: The three accepted forms, in the order the refusal message names them.
SMOKE_SPELLINGS = ("smoke", "plumbing")

#: The two fields every row must carry. Placement: top level, after ``arm``.
ROW_FIELDS = ("claim", "comparison_eligible")

#: The named refusal `assert_comparable` raises, mirroring ``incomparable_provenance``.
INCOMPARABLE_CLAIM = "incomparable_claim"

_LEGACY = object()        # no claim fields at all: written before this mechanism existed
_INCOMPLETE = object()    # exactly one of the two fields present: a half-landed runner


class ClaimRecord(Mapping):
    """A frozen claim record: exactly ``mode``, ``claim``, ``comparison_eligible``.

    A ``Mapping`` (so ``dict(rec)``/``rec["claim"]`` work and pytest compares it to the
    documented dict), but immutable: no setter, no ``update``, and the backing mapping
    is a ``MappingProxyType``. A claim that could be edited after it was resolved would
    be a claim that can be re-labelled to get past G3.
    """

    __slots__ = ("_fields",)

    def __init__(self, mode, claim, comparison_eligible):
        object.__setattr__(self, "_fields", MappingProxyType({
            "mode": str(mode),
            "claim": str(claim),
            "comparison_eligible": bool(comparison_eligible),
        }))

    def __getitem__(self, key):
        return self._fields[key]

    def __iter__(self):
        return iter(self._fields)

    def __len__(self):
        return len(self._fields)

    def __setattr__(self, name, value):       # noqa: D105 - frozen by construction
        raise AttributeError("ClaimRecord is frozen; resolve a new claim instead")

    @property
    def mode(self):
        return self._fields["mode"]

    @property
    def claim(self):
        return self._fields["claim"]

    @property
    def comparison_eligible(self):
        return self._fields["comparison_eligible"]

    @property
    def is_smoke(self):
        return self._fields["mode"] == MODE_SMOKE

    def as_dict(self):
        return dict(self._fields)

    def __repr__(self):
        return ("ClaimRecord(mode=%r, claim=%r, comparison_eligible=%r)"
                % (self.mode, self.claim, self.comparison_eligible))


def refusal_message(flag_value):
    """THE refusal text: names the three accepted forms and says silence is not a claim."""
    return (
        "claim REFUSED: --hypothesis=%r is not a declaration this run may make. "
        "The three accepted forms are (1) `--hypothesis smoke` and (2) "
        "`--hypothesis plumbing` -- both declare claim=none, so the cell is plumbing "
        "and its rows are NOT comparison_eligible -- and (3) a claim id: "
        "`--hypothesis H1`, `--hypothesis H2` or `--hypothesis H3` for a PARM-1 claim, "
        "or `--hypothesis E1` ... `--hypothesis E6` for a PREREG-SPCC experiment "
        "(experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md). "
        "Silence is not a claim: an absent or empty --hypothesis is refused here, and "
        "so is an explicit `none` -- a run may start without a hypothesis only by "
        "declaring that it makes no claim."
        % (flag_value,))


class ClaimRefusal(Exception):
    """The declared form is missing or unrecognised -- the same class/exit code as G3.

    Carries ``code = EXIT_PREREG`` (12) and ``stage`` = G3's stage string, and the
    refused-verdict body, so :func:`as_abort` reproduces exactly the ``cell.Abort``
    that G3's own silence branch is converted into by ``_enforce``. Nothing about the
    exit-code contract changes; the message is the only new thing.
    """

    code = EXIT_PREREG
    stage = "3c/7 G3 prereg gate"

    def __init__(self, flag_value, message=None):
        self.flag_value = flag_value
        self.verdict = {
            "gate": "G3", "what": "prereg", "ok": False,
            "hypothesis": "NONE", "hypothesis_source": "absent:--hypothesis",
            "claim": CLAIM_NONE, "comparison_eligible": False,
            "n": 0,
            "computed": "hypothesis=%r (not a declaration)" % (flag_value,),
            "limit": "smoke | plumbing | " + " | ".join(ALL_CLAIM_IDS),
            "flag": "--hypothesis",
            "consequence": ("a live cell spends requests on a claim it must name, or "
                            "declares that it makes no claim; silence is not a claim"),
        }
        super().__init__(message if message is not None
                         else refusal_message(flag_value))


def resolve_claim(flag_value):
    """Resolve ``--hypothesis`` into a frozen two-shape record, or refuse.

    ``smoke``/``plumbing`` -> ``{"mode": "smoke", "claim": "none",
    "comparison_eligible": False}``. A claim id (case-insensitive) ->
    ``{"mode": "hypothesis", "claim": "H#"|"E#", "comparison_eligible": True}``.
    ``H1``-``H3`` are PARM-1's claims; ``E1``-``E6`` are PREREG-SPCC's experiments --
    both are claims the cell makes, so both are comparison_eligible; which document
    adjudicates the claim is G3's decision, not this resolver's.
    Everything else -- ``None``, ``""``, whitespace, ``"none"``, an unknown spelling --
    raises :class:`ClaimRefusal`. There is no default: the only way to run without a
    hypothesis is to declare that you make no claim.
    """
    text = "" if flag_value is None else str(flag_value).strip().lower()
    if text in SMOKE_SPELLINGS:
        return ClaimRecord(MODE_SMOKE, CLAIM_NONE, False)
    upper = text.upper()
    if upper in ALL_CLAIM_IDS:
        return ClaimRecord(MODE_HYPOTHESIS, upper, True)
    raise ClaimRefusal(flag_value)


def row_fields(claim):
    """The two row fields for a resolved claim -- the mechanical runner change.

    ``resolve_claim("smoke")`` -> ``{"claim": "none", "comparison_eligible": False}``.
    """
    if not isinstance(claim, Mapping) or set(claim) != set(ROW_FIELDS + ("mode",)):
        raise TypeError("row_fields() takes a resolved ClaimRecord, got %r" % (claim,))
    return {"claim": claim["claim"],
            "comparison_eligible": bool(claim["comparison_eligible"])}


def as_abort(refusal, abort_class):
    """The SAME class G3 raises for silence: ``cell.Abort(code=12, stage, message, verdict)``.

    ``abort_class`` is REQUIRED and must be the caller's own ``Abort`` (in ``cell.py``,
    the module-level class the conductor's ``except Abort`` handles). This module
    deliberately does NOT import ``cell`` to find it: when ``cell.py`` runs as a script
    its module is ``__main__``, so ``import cell`` would execute the conductor a second
    time and hand back a DIFFERENT ``Abort`` class -- the exception would then escape
    ``main()``'s handler and exit 1 instead of 12. The wiring call therefore passes
    ``Abort`` explicitly: ``check_prereg_claim(args, Abort)``.
    """
    return abort_class(refusal.code, refusal.stage, str(refusal), refusal.verdict)


def check_prereg_claim(args, abort_class):
    """Resolve ``--hypothesis`` or raise the CALLER's ``Abort`` with G3's code (12).

    This is the one-call wiring helper for ``cell.eval_gate_prereg``: silence, an empty
    flag, an explicit ``none`` and an unknown spelling all become the same
    ``Abort(EXIT_PREREG, "3c/7 G3 prereg gate", ...)`` that G3's own silence branch
    produced, so no exit code changes.
    """
    try:
        return resolve_claim(getattr(args, "hypothesis", None))
    except ClaimRefusal as exc:
        raise as_abort(exc, abort_class) from None


def smoke_prereg_verdict(verdict, n):
    """The G3 verdict for a DECLARED smoke/plumbing cell: allowed, non-comparable.

    Returns a copy of the gate verdict with ``ok: True`` and the claim stamped on it.
    It deliberately carries no PARM-1 threshold: a cell that makes no claim cannot
    fail an admissibility test for a claim it does not make -- and its
    ``comparison_eligible: false`` is what keeps its rows out of every comparison.
    """
    if not isinstance(verdict, Mapping):
        raise TypeError("smoke_prereg_verdict() takes the G3 verdict dict")
    out = dict(verdict)
    out.update({
        "ok": True, "n": int(n or 0),
        "claim": CLAIM_NONE, "comparison_eligible": False,
        "computed": "claim=none declared (smoke/plumbing)",
        "limit": "no claim is made, so no PARM-1 n threshold applies",
        "short": "%s n=%d (smoke, non-comparable)" % (out.get("gate", "G3"), n),
        "consequence": ("this run declares that it makes no claim: it may start, and "
                        "its rows can never enter a comparison -- analyze_stats "
                        "refuses claim=none cells by name (incomparable_claim)"),
    })
    return out


class IncomparableClaim(Exception):
    """``incomparable_claim``: a claim-free cell was offered to a comparison.

    Mirrors ``IncomparableProvenance`` in ``analyze_stats.py``: the message begins with
    the named kind and identifies every offending cell (cell/arm/rep/turn), so the
    refusal cannot be mistaken for a missing row or a filtered group.
    """

    kind = INCOMPARABLE_CLAIM

    def __init__(self, message, offenders=None):
        self.offenders = list(offenders or ())
        super().__init__(message)


def _canonical_claim(value):
    if value is None:
        return None
    text = str(value).strip().lower()
    return text or None


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("true", "yes", "1"):
            return True
        if text in ("false", "no", "0"):
            return False
    return None


def _row_identity(row, index):
    """How a refusal names the offending cell: explicit cell id, else arm/rep/turn."""
    ident = {
        "row_index": index,
        "cell": row.get("cell") or row.get("cell_id") or row.get("task_id"),
        "arm": row.get("arm") or row.get("_arm") or "(unlabelled)",
        "rep": row.get("rep"),
        "turn": row.get("turn", row.get("turn_index")),
        "claim": row.get("claim"),
        "comparison_eligible": row.get("comparison_eligible"),
    }
    return ident


def _ident_label(ident):
    parts = []
    if ident.get("cell") not in (None, ""):
        parts.append("cell=%s" % ident["cell"])
    parts.append("arm=%s" % ident["arm"])
    if ident.get("rep") is not None:
        parts.append("rep=%s" % ident["rep"])
    if ident.get("turn") is not None:
        parts.append("turn=%s" % ident["turn"])
    return " ".join(parts)


def _row_claim_state(row):
    """``(claim_norm, eligible)`` or the sentinels for legacy / half-written rows."""
    has_claim = "claim" in row
    has_eligible = "comparison_eligible" in row
    if not has_claim and not has_eligible:
        return _LEGACY, None
    if has_claim != has_eligible:
        return _INCOMPLETE, None
    claim = _canonical_claim(row.get("claim"))
    if claim is None:
        return _INCOMPLETE, None
    return claim, _as_bool(row.get("comparison_eligible"))


def assert_comparable(rows, label=""):
    """Refuse (``incomparable_claim``) any comparison set containing a claim-free cell.

    ``rows`` is any iterable of row dicts -- one cell, several cells, or several arms.
    Returns ``{"comparable": True, "claims": {...counts...}, "legacy_rows": n,
    "legacy_arms": [...]}`` when every row either declares a hypothesis or predates
    this mechanism.

    Refused, all as ``IncomparableClaim``:

    * ``claim: "none"`` / ``comparison_eligible: false`` -- the smoke cell, named;
    * a hypothesis claim contradicted by ``comparison_eligible: false``;
    * an unrecognised claim value, or only one of the two fields present (a
      half-landed runner is a bug, not a licence to compare).

    Absent BOTH fields is the LEGACY state: rows written before this mechanism existed
    are not backfilled and are not claim-free declarations. They are counted and their
    arms reported, so a legacy row is visible rather than silently equal to a claim.
    """
    offenders = []
    claims = {}
    legacy = []
    for index, row in enumerate(rows or ()):
        if not isinstance(row, dict):
            continue
        claim, eligible = _row_claim_state(row)
        ident = _row_identity(row, index)
        if claim is _LEGACY:
            legacy.append(ident)
            continue
        claims[claim] = claims.get(claim, 0) + 1
        if claim is _INCOMPLETE:
            offenders.append(dict(ident, reason="claim_fields_incomplete"))
            continue
        if claim == CLAIM_NONE or eligible is False:
            offenders.append(dict(ident, reason="claim_free"))
            continue
        if claim.upper() not in ALL_CLAIM_IDS:
            offenders.append(dict(ident, reason="unknown_claim"))
            continue
        if eligible is None:
            offenders.append(dict(ident, reason="claim_fields_incomplete"))
    if offenders:
        named = "; ".join(_ident_label(o) for o in offenders)
        where = (" " + label) if label else ""
        kinds = sorted({o.get("reason") or "claim_free" for o in offenders})
        raise IncomparableClaim(
            "%s%s: refusing a comparison that includes %d cell row(s) which make no "
            "claim (%s): %s. A smoke/plumbing cell declares claim=%r with "
            "comparison_eligible=false, so its rows can never enter a comparison -- "
            "they are not filtered out silently, they stop the comparison. Compare "
            "only cells that declare %s, or report the smoke cell's numbers on "
            "their own with its claim named."
            % (INCOMPARABLE_CLAIM, where, len(offenders), ", ".join(kinds), named,
               "|".join(ALL_CLAIM_IDS), CLAIM_NONE),
            offenders)
    return {"comparable": True,
            "claims": claims,
            "legacy_rows": len(legacy),
            "legacy_arms": sorted({str(i.get("arm")) for i in legacy})}


if __name__ == "__main__":                # a reader can see the shapes without a test
    for value in ("smoke", "plumbing", "H1", "H3", None, "", "none", "H4"):
        try:
            print("%-10r -> %r" % (value, resolve_claim(value)))
        except ClaimRefusal as exc:
            print("%-10r -> REFUSED (exit %d): %s" % (value, exc.code, exc))
