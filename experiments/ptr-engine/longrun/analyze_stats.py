#!/usr/bin/env python3
"""analyze_stats.py - EVAL-STATS: every reported number carries its n and an interval.

Why this module exists
----------------------
The repo's long-run reporting printed a bare p95 (and a bare accuracy). Two
defects follow from that, both measured in `docs/EXTERNAL-EVAL-PRACTICE.md`:

  * an order statistic at n=48 has a distribution-free 95 % interval spanning
    ranks 43-48, i.e. p89.6-p100.0 - a "p95" there rests on about three
    observations, so an arm gap quoted from it is not evidence;
  * a bare proportion hides its own width: 3/48 is 6 % +/- 7 %.

So this module refuses to print a point estimate without (a) the n it came
from and (b) a two-sided interval. The refusal is enforced in ONE function,
`render_estimate()`, which every number in the CLI output passes through. It is
not a style convention: a caller that tries to print a bare p95 gets
`BareMetricError` and a non-zero exit.

Estimability rule (single place: `quantile_ci`)
-----------------------------------------------
A q-quantile is estimable only when

    n >= 20                         (minimum sample for ANY reported quantile)
    n * (1 - q) >= TAIL_MIN (== 3)  (at least 3 observations above q)

The second clause is the standard admissibility rule for a tail quantile; it is
what makes n=48 unusable for p95 (48 * 0.05 = 2.4 < 3) and what fixes the first
admissible p95 at n=60. Refusal raises `InsufficientSamples` with the message
stating the n, the quantile, and the exact rank span that *would* have been used
(the span is computed with the same binomial order-statistic arithmetic that
produces the reference interval, so the message cannot drift from the code).

Paired comparison rule
----------------------
McNemar is exact and two-sided, on paired ITEM-level outcomes only, and refuses
when b + c < 6 - with fewer than six discordant pairs the exact two-sided p
cannot fall below 0.05, so running the test would only manufacture a
false-negative dressed as a measurement. No chi-square substitution.

Provenance refusal (the guard on comparisons)
---------------------------------------------
Every CROSS-CELL number this module produces goes through `compare()`, and
`compare()` calls `require_comparable()` -- `same_provenance` from ROW-PROVENANCE --
before it looks at which statistic was requested. The four load-bearing fields are
`fixture_sha256`, `model`, `thinking`, `tools_mode`; `arm` is deliberately NOT one
of them (the arm is what a comparison is FOR). A mismatch raises
`IncomparableProvenance`, whose message begins `incomparable_provenance` and names
the differing fields: no interval and no verdict is computed. `--assume-comparable`
is the only door through it, and it is loud by construction -- the run records
`provenance_override: true` plus the differing field list in stdout and in `--json`.
There is no environment variable and no default-on.

An unknown is never evidence of agreement: two cells that both fail to name
`model` are `unknown` vs `unknown`, which refuses. `row_provenance.aggregate()`'s
`"mixed"` -- a field on which one file's own rows disagree -- is likewise treated as
unknown here, because a cell with no single provenance has no known provenance.

Offline: this module reads row files and computes. It never issues a request.

Usage
-----
    python3 analyze_stats.py --rows ROWFILE [ROWFILE ...] [--json OUT]
    python3 analyze_stats.py --rows ROWFILE --assume-comparable --json OUT

Row contract tolerance: every field this module reads may be absent or null in
older row files (`ttft_ms`, `ttft_source`, `answer_kind`, `answer_value`,
`cached_tokens`, `engine_metrics_*`, ...). Absence is never an exception; a
null `ttft_ms` is DROPPED AND COUNTED, never coerced to 0.0.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from statistics import NormalDist

# `same_provenance` lives in `tools/row_provenance.py` (the ROW-PROVENANCE unit's
# public surface, which re-exports `client.same_provenance` so the row writer and
# this analyser can never disagree about what "same provenance" means). The import
# is at module scope and deliberately NOT wrapped in try/except: a guard that
# silently vanishes when its dependency moves is documentation, not a guard.
_HERE = os.path.dirname(os.path.abspath(__file__))
_TOOLS = os.path.join(os.path.dirname(_HERE), "tools")
for _p in (_HERE, _TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from row_provenance import same_provenance                    # noqa: E402
import row_provenance as _row_provenance                      # noqa: E402
# The accuracy population's ONLY owner. Deliberately a hard import for the same
# reason as the guard above: a shared rule that silently falls back to a private
# copy is how the two sides drifted apart in the first place.
import grade_v5                                               # noqa: E402

__all__ = [
    "BareMetricError", "InsufficientSamples", "RefusedTest",
    "IncomparableProvenance", "INCOMPARABLE_PROVENANCE",
    "wilson_ci", "quantile_ci", "rank_span", "mcnemar_exact", "mcnemar_p",
    "pass_hat_k", "paired_by_turn", "ttft_values", "row_outcome",
    "turn_latency_rows", "definition_violations", "TTFT_DEFINITION",
    "TTFT_DEFINITION_VERSION",
    "render_estimate", "cell_provenance", "require_comparable", "compare",
    "provenance_cells", "provenance_line", "analyze", "main",
]

# --- frozen constants -------------------------------------------------------
LEVEL = 0.95           # two-sided coverage for every interval in this module
TAIL_MIN = 3           # observations required above a tail quantile
MIN_N = 20             # minimum n for ANY reported quantile
RESAMPLES = 10000      # percentile-bootstrap resamples
SEED = 20261020        # fixed so a rerun reproduces the same interval


class BareMetricError(Exception):
    """Raised when a point estimate would be printed without n and interval."""


class InsufficientSamples(Exception):
    """Raised when n is too small for the requested statistic to mean anything."""


class RefusedTest(Exception):
    """Raised when a significance test is not licensed by the data."""


# --- the provenance refusal (WIRE-PROVENANCE-INTO-STATS) --------------------
#: The refusal KIND, quoted verbatim in every message and in every artefact row.
INCOMPARABLE_PROVENANCE = "incomparable_provenance"

#: The four load-bearing provenance fields a comparison must agree on. This is
#: `client.PROVENANCE_LOAD_BEARING`, restated here only so this module can build a
#: cell without importing a second copy of the semantics: the DECISION is always
#: `same_provenance`'s, never this tuple.
PROVENANCE_LOAD_BEARING = ("fixture_sha256", "model", "thinking", "tools_mode")

#: `row_provenance.aggregate()` reports a field on which a file's own rows disagree
#: as the string "mixed". `client.is_provenance_known("mixed")` is True, so
#: `same_provenance("mixed", "mixed")` calls two mixed cells EQUAL -- a file whose
#: rows cannot agree with itself would pass the gate. This module therefore maps
#: "mixed" to "unknown" when it builds a cell: a cell with no single provenance has
#: no known provenance, and unknown-vs-unknown refuses. (Reported upstream rather
#: than fixed here -- `client.py` / `row_provenance.py` are read-only for this unit.)
_PROV_MIXED = "mixed"
PROVENANCE_UNKNOWN = "unknown"


class IncomparableProvenance(RefusedTest):
    """Named refusal: two cells do not share load-bearing provenance.

    Carries its own arithmetic the way `RefusedTest` does -- `kind`, `differing`
    (the field names), `a` / `b` (both coerced cells), `overridden` -- because a
    refusal that hides the fields it refused on is the defect this module exists
    to remove. `str(exc)` always starts with ``incomparable_provenance``.
    """

    kind = INCOMPARABLE_PROVENANCE

    def __init__(self, message, differing, a, b, overridden=False):
        super().__init__(message)
        self.differing = list(differing)
        self.a = dict(a)
        self.b = dict(b)
        self.overridden = bool(overridden)


# --- proportions ------------------------------------------------------------
# --- the claim refusal (WIRE-CLAIM-MODE) ------------------------------------
#: The refusal KIND, quoted verbatim: `claim_mode.INCOMPARABLE_CLAIM`, restated here
#: only because this module may not import the resolver at module scope (script entry).
INCOMPARABLE_CLAIM = "incomparable_claim"


class IncomparableClaim(RefusedTest):
    """Named refusal: a comparison set contains a cell that declares claim=none.

    A smoke/plumbing cell is allowed to RUN -- it declares that it makes no claim -- and
    is never allowed to be POOLED. The DECISION is `claim_mode.assert_comparable`'s; this
    class only carries it into the report, so there is one resolver and no second
    opinion. `str(exc)` always starts with ``incomparable_claim``.
    """

    kind = INCOMPARABLE_CLAIM

    def __init__(self, message, offenders=None):
        super().__init__(message)
        self.offenders = list(offenders or ())


def _claim_module():
    """THE claim resolver, imported by path (this module runs as a script too)."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import claim_mode  # noqa: E402
    return claim_mode


def claim_sidecar_path(rows_path):
    """Where `cell.py`'s run stage writes the resolved claim: beside the rows file."""
    return str(rows_path) + ".claim.json"


def claim_sidecar_claim(rows_path):
    """The sidecar document, or None (absent/unreadable = LEGACY, never claim-free)."""
    try:
        with open(claim_sidecar_path(rows_path), encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def require_comparable_claim(rows, label="", rows_path=None):
    """Refuse a claim=none cell BY NAME; never filter it out of a comparison.

    ``rows`` is a list of row dicts; ``rows_path`` (optional) adds the run stage's claim
    sidecar, so a smoke cell whose rows carry no claim fields yet is still refused by
    name instead of being read as legacy. Returns the resolver's comparable summary.
    """
    mod = _claim_module()
    try:
        result = mod.assert_comparable(rows or (), label)
    except mod.IncomparableClaim as exc:
        raise IncomparableClaim(str(exc), getattr(exc, "offenders", ())) from None
    sidecar = claim_sidecar_claim(rows_path) if rows_path else None
    if sidecar and str(sidecar.get("claim", "")).strip().lower() == mod.CLAIM_NONE:
        raise IncomparableClaim(
            "%s%s: the run stage declared claim=%r (comparison_eligible=%s) for %s -- a "
            "cell that makes no claim can never enter a comparison; report its numbers "
            "on their own with its claim named"
            % (INCOMPARABLE_CLAIM, (" " + label) if label else "", mod.CLAIM_NONE,
               sidecar.get("comparison_eligible"),
               claim_sidecar_path(rows_path)),
            [{"rows_path": str(rows_path), "claim": sidecar.get("claim"),
              "comparison_eligible": sidecar.get("comparison_eligible")}])
    return result


def _claim_refusal_record(exc, statistic, label):
    """The record kept when the CLAIM gate (not provenance) refused the comparison."""
    return {"statistic": statistic, "label": label, "a": {}, "b": {},
            "provenance": {"comparable": False, "differing": [], "overridden": False,
                           "a": {}, "b": {}},
            "provenance_override": False,
            "incomparable_provenance": None,
            "incomparable_claim": {"offenders": list(getattr(exc, "offenders", ()))},
            "refused": str(exc), "refused_kind": INCOMPARABLE_CLAIM}


def wilson_ci(k, n, level=LEVEL):
    """Wilson score interval for k successes in n trials -> (point, lo, hi).

    Never degenerate: at k=0 the lower bound is 0 and the upper bound is
    z^2/(n+z^2) > 0; at k=n the upper bound is 1 and the lower bound is
    n/(n+z^2) < 1. Both endpoints stay inside [0, 1].
    """
    if n is None or n <= 0:
        raise InsufficientSamples("wilson_ci needs n >= 1 (got n=%r)" % (n,))
    if not (0 <= k <= n):
        raise ValueError("wilson_ci: k=%r outside 0..n=%r" % (k, n))
    if not (0.0 < level < 1.0):
        raise ValueError("wilson_ci: level must be in (0,1), got %r" % (level,))
    z = NormalDist().inv_cdf(1.0 - (1.0 - level) / 2.0)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = (z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


# --- quantiles --------------------------------------------------------------
def _quantile_sorted(xs, q):
    """Linear-interpolated quantile of an already-sorted sequence."""
    n = len(xs)
    if n == 0:
        raise InsufficientSamples("no values to take a quantile of")
    if n == 1:
        return float(xs[0])
    h = (n - 1) * q
    i = int(math.floor(h))
    if i >= n - 1:
        return float(xs[-1])
    frac = h - i
    return float(xs[i]) + (float(xs[i + 1]) - float(xs[i])) * frac


def _binom_cdf(k, n, q):
    """P(B <= k) for B ~ Binomial(n, q). Exact, stdlib only."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    total = 0.0
    for i in range(0, k + 1):
        total += math.comb(n, i) * (q ** i) * ((1.0 - q) ** (n - i))
    return total


def rank_span(n, q, level=LEVEL):
    """Distribution-free order-statistic interval ranks for the q-quantile.

    Returns (lo_rank, hi_rank), 1-based. The interval [X_(lo), X_(hi)] has
    coverage >= `level`. This is the REFERENCE interval printed alongside the
    bootstrap one, and the span quoted by every refusal message.
    """
    if n <= 0:
        raise ValueError("rank_span needs n >= 1")
    if not (0.0 < q < 1.0):
        raise ValueError("rank_span: q must be in (0,1), got %r" % (q,))
    alpha = (1.0 - level) / 2.0
    lo = 1
    for t in range(0, n + 1):
        if _binom_cdf(t - 1, n, q) <= alpha:
            lo = t + 1
    hi = n
    for t in range(0, n + 1):
        if _binom_cdf(t - 1, n, q) >= 1.0 - alpha:
            hi = t
            break
    return max(1, min(lo, n)), max(1, min(hi, n))


def _q_label(q):
    return "p%g" % (q * 100.0)


def min_n_for(q, level=LEVEL):
    """Smallest n at which the q-quantile is admissible (see module docstring)."""
    if not (0.0 < q < 1.0):
        raise ValueError("min_n_for: q must be in (0,1), got %r" % (q,))
    tail = int(math.ceil(TAIL_MIN / (1.0 - q)))
    return max(MIN_N, tail)


def _insufficient_message(n, q, level=LEVEL):
    lo_r, hi_r = rank_span(n, q, level) if n > 0 else (0, 0)
    lo_pct = (lo_r / n * 100.0) if n > 0 else 0.0
    hi_pct = (hi_r / n * 100.0) if n > 0 else 0.0
    return (
        "refusing %s at n=%d: the %d%% order-statistic span is ranks %d-%d "
        "(p%.1f-p%.1f) and n*(1-q)=%.1f < %d; minimum n for %s is %d"
        % (_q_label(q), n, int(round(level * 100)), lo_r, hi_r,
           lo_pct, hi_pct, n * (1.0 - q), TAIL_MIN, _q_label(q), min_n_for(q))
    )


def quantile_ci(values, q, resamples=RESAMPLES, seed=SEED, stats=None):
    """Percentile-bootstrap interval for a quantile -> (point, lo, hi, n).

    `values` may contain None / NaN / inf (an unavailable first stream delta is
    NOT a zero): such entries are dropped, and the count is reported. Pass a
    dict as `stats` to receive it (and the rank span) without changing the
    4-tuple return:

        stats["dropped_null"]      number of null/non-finite entries dropped
        stats["input"]             entries supplied
        stats["used"]              n actually used (== returned n)
        stats["rank_span"]         (lo_rank, hi_rank) reference interval
        stats["rank_span_pct"]     the same span as percentages
        stats["resamples"]         bootstrap resamples drawn

    Raises `InsufficientSamples` when n < 20 or n*(1-q) < 3.
    """
    if not (0.0 < q < 1.0):
        raise ValueError("quantile_ci: q must be in (0,1), got %r" % (q,))
    raw = list(values or ())
    vals = []
    dropped = 0
    for v in raw:
        if v is None or isinstance(v, bool):
            dropped += 1
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            dropped += 1
            continue
        if not math.isfinite(f):
            dropped += 1
            continue
        vals.append(f)
    n = len(vals)
    if n < MIN_N or n * (1.0 - q) < TAIL_MIN:
        raise InsufficientSamples(_insufficient_message(n, q))
    vals.sort()
    point = _quantile_sorted(vals, q)
    rng = random.Random(seed)
    boot = []
    for _ in range(int(resamples)):
        sample = rng.choices(vals, k=n)
        sample.sort()
        boot.append(_quantile_sorted(sample, q))
    boot.sort()
    alpha = (1.0 - LEVEL) / 2.0
    lo = _quantile_sorted(boot, alpha)
    hi = _quantile_sorted(boot, 1.0 - alpha)
    # the percentile interval always brackets the point; clamp defensively
    lo, hi = min(lo, point), max(hi, point)
    if stats is not None:
        lo_r, hi_r = rank_span(n, q)
        stats.update({
            "input": len(raw), "used": n, "dropped_null": dropped,
            "rank_span": (lo_r, hi_r),
            "rank_span_pct": (lo_r / n * 100.0, hi_r / n * 100.0),
            "resamples": int(resamples),
        })
    return point, lo, hi, n


# --- paired tests -----------------------------------------------------------
def mcnemar_p(b, c):
    """Exact two-sided McNemar p-value from the discordant cells alone.

    Pure arithmetic, no licensing gate - this is the function to call when the
    p itself (not a verdict) is the object of interest. For b=3, c=0 it is
    2 * C(3,0) / 2^3 = 0.25, the arithmetic the external survey quotes.
    """
    if b < 0 or c < 0:
        raise ValueError("mcnemar_p: b and c must be non-negative")
    disc = b + c
    if disc == 0:
        return 1.0
    tail = sum(math.comb(disc, i) for i in range(0, min(b, c) + 1)) * (0.5 ** disc)
    return min(1.0, 2.0 * tail)


def mcnemar_exact(pairs):
    """Exact two-sided McNemar over paired item-level outcomes -> (b, c, p).

    `pairs` yields (outcome_a, outcome_b) with truthiness meaning "correct".
    b counts A-wrong/B-right, c counts A-right/B-wrong (the discordant cells).
    The p-value is the exact two-sided binomial tail (`mcnemar_p`): no
    chi-square, no continuity correction.

    Refuses with `RefusedTest` when b + c < 6, because the smallest attainable
    two-sided exact p with five discordant pairs is 0.0625, so no test at that
    size can reach 0.05. The refusal still carries the computed arithmetic:
    `exception.b`, `exception.c` and `exception.p` are set, and the message
    names the discordant count - a refusal that hides its own numbers would be
    the same defect this module exists to remove. b=3, c=0 therefore raises
    with p=0.25 rather than returning it.
    """
    b = c = 0
    for pair in pairs or ():
        try:
            a_out, b_out = pair
        except (TypeError, ValueError):
            raise ValueError("mcnemar_exact expects (outcome_a, outcome_b) pairs")
        if not a_out and b_out:
            b += 1
        elif a_out and not b_out:
            c += 1
    disc = b + c
    p = mcnemar_p(b, c)
    if disc < 6:
        exc = RefusedTest(
            "refusing McNemar: only %d discordant pairs (b=%d, c=%d), and b+c < 6; "
            "the exact two-sided p is %.5f and the smallest attainable p at %d "
            "discordant pairs is %.5f, so the test cannot reach 0.05" %
            (disc, b, c, p, disc, min(1.0, 2.0 * 0.5 ** disc))
        )
        exc.b, exc.c, exc.p, exc.discordant = b, c, p, disc
        raise exc
    return b, c, p


def pass_hat_k(n, c, k):
    """Unbiased pass@k estimator: 1 - C(n-c, k) / C(n, k).

    Guarded at both edges: k < 1 or c outside 0..n is a ValueError, and when
    n - c < k (fewer than k incorrect samples exist) the estimator is 1.0 by
    definition - every k-subset that could be drawn from the incorrect pool is
    empty, so no draw can fail. Returning 1.0 there, rather than dividing by a
    degenerate binomial, is what keeps the guard from manufacturing an error.
    """
    if n is None or n <= 0:
        raise InsufficientSamples("pass_hat_k needs n >= 1 (got n=%r)" % (n,))
    if not (0 <= c <= n):
        raise ValueError("pass_hat_k: c=%r outside 0..n=%r" % (c, n))
    if k < 1:
        raise ValueError("pass_hat_k: k must be >= 1 (got %r)" % (k,))
    if n - c < k:
        return 1.0
    return 1.0 - (math.comb(n - c, k) / math.comb(n, k))


def paired_by_turn(rows_a, rows_b, select=None):
    """Pair two arms' rows on `turn_index` (falling back to `turn`).

    Both sides pass through the SAME per-turn selector `turn_latency_rows` before
    pairing (unless `select` is supplied), so the paired population and the
    p50/p95 population are defined identically: one row per TURN. Without it a
    tools-on cell offers k+1 rows per turn and the first row seen wins, which is a
    `tool-followup` -- a request inside the turn, not the turn.

    Returns (pairs, stats) where pairs is a list of (turn_index, row_a, row_b)
    and stats reports how many pairs were formed and every reason a row was
    dropped, so a short paired denominator can never be silent:

        formed, dropped_missing_key, dropped_duplicate, dropped_unpaired
    plus `definition`/`definition_fallback_a`/`definition_fallback_b` and the
    follow-up accounting contributed by the selector.
    """
    selector = turn_latency_rows if select is None else select
    meta_a, meta_b = {}, {}
    rows_a, _ = selector(rows_a or (), meta_a)
    rows_b, _ = selector(rows_b or (), meta_b)

    def _index(rows):
        out, missing, dup = {}, 0, 0
        for row in rows or ():
            if not isinstance(row, dict):
                missing += 1
                continue
            key = row.get("turn_index", row.get("turn"))
            if key is None:
                missing += 1
                continue
            if key in out:
                dup += 1
                continue
            out[key] = row
        return out, missing, dup

    idx_a, miss_a, dup_a = _index(rows_a)
    idx_b, miss_b, dup_b = _index(rows_b)
    common = sorted(set(idx_a) & set(idx_b), key=lambda x: (str(type(x)), x))
    pairs = [(k, idx_a[k], idx_b[k]) for k in common]
    stats = {
        "formed": len(pairs),
        "dropped_missing_key": miss_a + miss_b,
        "dropped_duplicate": dup_a + dup_b,
        "dropped_unpaired": (len(idx_a) - len(common)) + (len(idx_b) - len(common)),
        "n_a": len(idx_a), "n_b": len(idx_b),
        "definition": TTFT_DEFINITION,
        "definition_fallback_a": bool(meta_a.get("definition_fallback")),
        "definition_fallback_b": bool(meta_b.get("definition_fallback")),
        "dropped_followup_a": meta_a.get("dropped_followup", 0),
        "dropped_followup_b": meta_b.get("dropped_followup", 0),
    }
    return pairs, stats


# --- row readers (contract fields may all be absent) ------------------------
def ttft_values(rows):
    """-> (values, dropped_null, dropped_unavailable) from long-run rows.

    A row whose `ttft_ms` is absent, null or non-finite contributes nothing and
    is COUNTED, never treated as 0 ms. A row flagged
    `ttft_source == "unavailable"` is likewise dropped even if it carries a
    number, because that number is a wall-clock fallback rather than a
    first-delta measurement.
    """
    vals, nulls, unavailable = [], 0, 0
    for row in rows or ():
        if not isinstance(row, dict):
            nulls += 1
            continue
        v = row.get("ttft_ms")
        src = row.get("ttft_source")
        if src == "unavailable":
            unavailable += 1
            continue
        if v is None:
            nulls += 1
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            nulls += 1
            continue
        if not math.isfinite(f):
            nulls += 1
            continue
        vals.append(f)
    return vals, nulls, unavailable


# --- THE per-turn TTFT definition: one selector, every latency path ---------
# TURN-ROW-ATTRIBUTION changed the row model to one row per SEND: a turn with k
# follow-ups now has k+1 rows (one `turn-initial` with send_index=0, k
# `tool-followup`, and the last follow-up is the `turn` row). A tools-on cell
# therefore has two candidate latency rows per turn, and they answer DIFFERENT
# questions. The operator's metric is p95 TTFT over a long run -- "how long does
# the system take to start answering THIS turn" -- which is a statement about the
# turn's own initial request, not about the last fetch inside the turn. So:
#
#   per-turn TTFT = the TTFT of the turn's own initial request: the
#   `kind="turn-initial"` row when present; otherwise the legacy `kind="turn"`
#   row, recorded as `definition_fallback: true`. A `kind="tool-followup"` row is
#   a request INSIDE a turn and is never a turn's latency.
#
# The rejected alternative is "last follow-up defines the turn": it measures a
# mid-turn re-query, it makes the metric depend on how often the arm chose to
# call a tool (an arm that fetches more would report more/lower samples), and in
# the legacy files it double-counts the last send (once as a follow-up row, once
# as the mirrored turn row), which is how a 48-turn cell produced a published
# p95 at n=70.
TTFT_DEFINITION_VERSION = "ttft-definition/1"
TTFT_DEFINITION = (
    "per-turn TTFT = the TTFT of the turn's own initial request: "
    "kind='turn-initial' when present, else the legacy kind='turn' row with "
    "definition_fallback=true; a kind='tool-followup' row is a request inside a "
    "turn and is never a turn's latency")
TURN_ROW_KINDS = ("turn-initial", "turn")
FOLLOWUP_ROW_KIND = "tool-followup"


# ---------------------------------------------------------------------------
# usable_for: the grid's per-cell usability stamp, CONSUMED by this analyser
# ---------------------------------------------------------------------------
# RUN-A-STAR-2 says "exclude by name anything GRID-CELL-SANITY marks
# usable_for: []". Nothing consumed that field until now: one producer, test
# readers only, so an abandoned cell entered the tranche silently. The stamp
# travels in the CELL MANIFEST (the grid writes one per cell and it already
# carries `rows_path`, the only field that joins a manifest to its rows file
# without guessing by filename), with the grid census
# (`measure/GRID-CELL-SANITY.json`) as the fallback for cells written before
# this card. Resolution order, first hit wins:
#   1. an explicit --manifest PATH
#   2. longrun/manifests/*.json whose `rows_path` resolves to the rows file
#   3. measure/GRID-CELL-SANITY.json cells[].path
# A cell with no stamp at all is INCLUDED and REPORTED `usable_for: unstamped`
# -- it is not silently certified either.
USABLE_FOR_FIELD = "usable_for"
USABLE_FOR_REASON_FIELD = "usable_for_reason"
USABLE_FOR_UNSTAMPED = "unstamped"

_HERE = os.path.dirname(os.path.abspath(__file__))
PTR_ROOT = os.path.dirname(_HERE)
REPO_ROOT = os.path.dirname(os.path.dirname(PTR_ROOT))
MANIFEST_DIR = os.path.join(_HERE, "manifests")
SANITY_DOC = os.path.join(PTR_ROOT, "measure", "GRID-CELL-SANITY.json")


class NoUsableCells(RefusedTest):
    """Every input cell is stamped usable_for: [] -- there is nothing to analyse."""


def _norm_path(path):
    """One comparable identity for a rows path, whatever cwd wrote it."""
    if not path:
        return ""
    tries = [path] if os.path.isabs(path) else [
        os.path.join(REPO_ROOT, path), os.path.join(PTR_ROOT, path), path]
    for cand in tries:
        if os.path.exists(cand):
            return os.path.realpath(cand)
    return os.path.normpath(tries[0])


def load_cell_manifests(paths=None, manifest_dir=None):
    """-> list of manifest dicts, each carrying `_manifest_path`."""
    out, seen = [], set()
    for path in list(paths or ()):
        try:
            with open(path, encoding="utf-8") as fh:
                man = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(man, dict) and man.get("rows_path") and path not in seen:
            man = dict(man)
            man["_manifest_path"] = path
            seen.add(path)
            out.append(man)
    directory = MANIFEST_DIR if manifest_dir is None else manifest_dir
    if directory and os.path.isdir(directory):
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(directory, name)
            if path in seen:
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    man = json.load(fh)
            except (OSError, ValueError):
                continue
            if isinstance(man, dict) and man.get("rows_path"):
                man = dict(man)
                man["_manifest_path"] = path
                seen.add(path)
                out.append(man)
    return out


def load_sanity_cells(path=None):
    """The grid census cells, or [] when it is absent/disabled."""
    if path is False:
        return []
    path = SANITY_DOC if path is None else path
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return []
    cells = doc.get("cells") if isinstance(doc, dict) else None
    return [c for c in (cells or ()) if isinstance(c, dict)]


def _usable_list(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        return [value] if value else []
    return None


def usable_for_for_path(rows_path, manifests=None, sanity=None):
    """-> {usable_for, reason, source, manifest_path} for one rows file.

    `usable_for` is None when no document stamps the cell (the caller reports it
    unstamped rather than inventing a permission).
    """
    target = _norm_path(rows_path)
    for man in manifests or ():
        if _norm_path(man.get("rows_path")) == target and USABLE_FOR_FIELD in man:
            return {"usable_for": _usable_list(man.get(USABLE_FOR_FIELD)),
                    "reason": man.get(USABLE_FOR_REASON_FIELD) or "",
                    "source": "manifest",
                    "manifest_path": man.get("_manifest_path")}
    for cell in load_sanity_cells(sanity):
        if _norm_path(cell.get("path")) == target and USABLE_FOR_FIELD in cell:
            return {"usable_for": _usable_list(cell.get(USABLE_FOR_FIELD)),
                    "reason": cell.get(USABLE_FOR_REASON_FIELD) or "",
                    "source": "sanity",
                    "manifest_path": None}
    return {"usable_for": None, "reason": "", "source": USABLE_FOR_UNSTAMPED,
            "manifest_path": None}


def select_usable_cells(files, manifests=None, sanity=None):
    """Drop every cell stamped unusable BEFORE any statistic is computed.

    A cell stamped `usable_for: []` is EXCLUDED BY NAME: it is removed here, its
    name and reason are printed, and the record travels into the `--json`
    document, so the exclusion is visible in the artefact and not only on
    stdout. A cell with no stamp is kept and reported `unstamped`.
    """
    kept, records = [], []
    for path, count, rows in files:
        rec = usable_for_for_path(path, manifests=manifests, sanity=sanity)
        analyses = _usable_list(rec["usable_for"])
        excluded = analyses is not None and len(analyses) == 0
        records.append({"path": path, "name": os.path.basename(path),
                        "rows": count, "usable_for": rec["usable_for"],
                        "reason": rec["reason"], "source": rec["source"],
                        "analyses": analyses, "excluded": bool(excluded)})
        if not excluded:
            kept.append((path, count, rows))
    return kept, records


def stamp_usable_for(manifest_path, usable_for, reason=None, dry_run=False):
    """Write the usability stamp into a CELL MANIFEST (atomic replace)."""
    with open(manifest_path, encoding="utf-8") as fh:
        man = json.load(fh)
    if not isinstance(man, dict):
        raise ValueError("manifest %s is not an object" % manifest_path)
    man[USABLE_FOR_FIELD] = [str(x) for x in (usable_for or ())]
    if reason is not None:
        man[USABLE_FOR_REASON_FIELD] = str(reason)
    if not dry_run:
        tmp = manifest_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(man, fh, indent=1, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, manifest_path)
    return man


def write_cell_manifest_usable_for(rows_path, usable_for, reason=None,
                                   manifest_path=None, dry_run=False):
    """The grid's write-time entry point for `usable_for`.

    `cell.py` is frozen by ANALYSIS-CONSUMER-FIX, so the writer lives beside the
    consumer it feeds: cell.py's next revision calls this once per finished cell
    (`rows_path` -> that cell's manifest), making the stamp part of the cell
    rather than of the analyser.
    """
    target = manifest_path
    if target is None:
        for man in load_cell_manifests():
            if _norm_path(man.get("rows_path")) == _norm_path(rows_path):
                target = man["_manifest_path"]
                break
    if target is None:
        raise FileNotFoundError("no cell manifest carries rows_path=%s" % rows_path)
    return stamp_usable_for(target, usable_for, reason=reason, dry_run=dry_run)


def _turn_key(row):
    """The identity a turn is counted under, or None when the row has none."""
    key = row.get("turn_index", row.get("turn"))
    if key is None or key == "":
        return None
    return (_arm_of(row), row.get("rep"), key)


def turn_latency_rows(rows, meta_out=None):
    """THE per-turn TTFT selector -> (selected_rows, meta). Every latency path uses it.

    One row per TURN, never per send: `kind="turn-initial"` wins when the row
    model provides it; otherwise the legacy `kind="turn"` row is selected and the
    figure is labelled `definition_fallback: true`. `kind="tool-followup"` rows
    are always dropped (and counted), so a k-follow-up turn contributes exactly
    one sample rather than k+1.

    The meta record is what makes the definition machine-checkable:
        definition, definition_version, mode, definition_fallback,
        n_input, n_selected, explicit_initial_rows, fallback_rows,
        mirrored_rows, dropped_followup, dropped_turn_followup,
        dropped_duplicate, turns_without_turn_row, dropped_not_a_row,
        dropped_foreign_kind

    `mirrored_rows` is the subset of fallback rows that belong to a turn which
    ALSO has follow-up rows: those are the rows where the fallback is not merely
    unproven but known to quote the last this-turn send. A cell can therefore be
    fallback=TRUE with mirrored_rows=0 (a tools-off cell, unaffected in value).
    """
    meta = {
        "definition": TTFT_DEFINITION,
        "definition_version": TTFT_DEFINITION_VERSION,
        "mode": "empty",
        "definition_fallback": False,
        "n_input": 0, "n_selected": 0,
        "explicit_initial_rows": 0, "fallback_rows": 0, "mirrored_rows": 0,
        "dropped_followup": 0, "dropped_turn_followup": 0,
        "dropped_duplicate": 0,
        "turns_without_turn_row": 0, "dropped_not_a_row": 0,
        "dropped_foreign_kind": 0,
    }
    followup_turns = set()
    groups = {}          # key -> {"turn-initial": [rows], "turn": [rows]}
    unkeyed = []         # no turn identity: never merged with a keyed turn
    for row in rows or ():
        if not isinstance(row, dict):
            meta["dropped_not_a_row"] += 1
            continue
        meta["n_input"] += 1
        kind = row.get("kind")
        key = _turn_key(row)
        if kind == FOLLOWUP_ROW_KIND:
            meta["dropped_followup"] += 1
            if key is not None:
                followup_turns.add(key)
            continue
        if kind is not None and kind not in TURN_ROW_KINDS:
            meta["dropped_foreign_kind"] += 1
            continue
        if key is None:
            unkeyed.append(row)
            continue
        if kind == "turn" and row.get("send_index") not in (None, 0):
            # The one-row-per-send model writes the LAST follow-up as kind='turn'.
            meta["dropped_turn_followup"] += 1
        slot = groups.setdefault(key, {"turn-initial": [], "turn": []})
        slot["turn-initial" if kind == "turn-initial" else "turn"].append(row)

    selected = []
    for key, slot in groups.items():
        bucket = slot["turn-initial"] or slot["turn"]
        if not bucket:
            meta["turns_without_turn_row"] += 1
            continue
        meta["dropped_duplicate"] += len(bucket) - 1
        chosen = bucket[0]
        # The OTHER kind's row for this turn is a second send, not a duplicate
        # measurement: the last follow-up is written as kind='turn' in the
        # one-row-per-send model.
        for other in (slot["turn"] if slot["turn-initial"] else slot["turn-initial"]):
            if other.get("send_index") in (None, 0):
                meta["dropped_duplicate"] += 1
        selected.append(chosen)
        if slot["turn-initial"]:
            meta["explicit_initial_rows"] += 1
        else:
            meta["fallback_rows"] += 1
            if key in followup_turns:
                meta["mirrored_rows"] += 1
    # Rows with no turn identity cannot be attributed to a turn; they are kept
    # (a legacy single-send file may not carry `turn`) and counted as fallback,
    # because nothing proves they are a turn's own initial request.
    for row in unkeyed:
        selected.append(row)
        if row.get("kind") == "turn-initial":
            meta["explicit_initial_rows"] += 1
        else:
            meta["fallback_rows"] += 1

    meta["n_selected"] = len(selected)
    meta["definition_fallback"] = meta["fallback_rows"] > 0
    if not selected:
        meta["mode"] = "empty"
    elif meta["fallback_rows"] == 0:
        meta["mode"] = "turn-initial"
    elif meta["explicit_initial_rows"] == 0:
        meta["mode"] = "fallback-turn"
    else:
        meta["mode"] = "mixed"
    if meta_out is not None:
        meta_out.update(meta)
    return selected, meta


# ---------------------------------------------------------------------------
# truncated turns -- RUNAWAY-POLICY option B, as a measurement rule
# ---------------------------------------------------------------------------
# A turn that ended on the completion cap is not a latency observation of the
# intended task: the model failed to answer. Including it makes p50/p95 measure
# the failure rather than the treatment, so it leaves the latency quantiles and
# is COUNTED per arm (the 2-in-27 rate is recorded in
# measure/RUNAWAY-POLICY.json). Latency only: the row/ledger/accuracy paths see
# the untouched selection, and no threshold is touched.
TRUNCATED_STOP_REASONS = ("length",)
TRUNCATED_RULE_VERSION = "truncated-turns/1"
TRUNCATED_RULE = (
    "a turn whose completion ended on the cap (stop_reason='length' or "
    "truncated=true) is excluded from the latency quantiles and counted per "
    "arm: a cap-length turn is not a latency observation of the intended task")


def is_truncated(row):
    """True when this row is a cap-length turn rather than a completed one."""
    if not isinstance(row, dict):
        return False
    if row.get("truncated") is True:
        return True
    return row.get("stop_reason") in TRUNCATED_STOP_REASONS


def split_truncated(rows):
    """-> (latency_rows, meta). The ONE place the truncated-turn rule is applied."""
    kept = []
    meta = {"rule": TRUNCATED_RULE, "rule_version": TRUNCATED_RULE_VERSION,
            "excluded": 0, "total": 0, "fraction": None,
            "by_stop_reason": {}, "keys": []}
    for row in rows or ():
        meta["total"] += 1
        if not is_truncated(row):
            kept.append(row)
            continue
        meta["excluded"] += 1
        reason = row.get("stop_reason") if isinstance(row, dict) else None
        if not reason:
            reason = "truncated"
        meta["by_stop_reason"][reason] = meta["by_stop_reason"].get(reason, 0) + 1
        meta["keys"].append(_turn_key(row) if isinstance(row, dict) else None)
    meta["fraction"] = (float(meta["excluded"]) / meta["total"]) if meta["total"] else None
    return kept, meta


def definition_violations(rows):
    """Every way a row set can violate the TTFT definition contract -> list.

    Machine-checkable complement of `turn_latency_rows`: an empty list means the
    rows can be selected exactly as the definition says. Used by the test and by
    `--check-definition`. Nothing here repairs anything -- a violation is
    REPORTED, and the caller decides.
    """
    out = []
    seen = {}   # turn key -> {"kinds": set, "turn_send_index": int|None}
    for row in rows or ():
        if not isinstance(row, dict):
            out.append("non-dict row")
            continue
        kind = row.get("kind")
        key = _turn_key(row)
        if kind == FOLLOWUP_ROW_KIND:
            if row.get("send_index") == 0:
                out.append("tool-followup row carries send_index=0 (turn %r)"
                           % (key,))
            continue
        if kind not in TURN_ROW_KINDS and kind is not None:
            out.append("unexpected kind %r on turn %r" % (kind, key))
            continue
        slot = seen.setdefault(key, {"kinds": set(), "turn_send_index": None})
        if kind in slot["kinds"]:
            out.append("two %r rows for turn %r" % (kind, key))
        slot["kinds"].add(kind)
        if kind == "turn":
            slot["turn_send_index"] = row.get("send_index")
    for key, slot in seen.items():
        if ("turn" in slot["kinds"] and "turn-initial" not in slot["kinds"]
                and slot["turn_send_index"] not in (None, 0)):
            out.append(
                "turn %r has no kind='turn-initial' row and its kind='turn' row "
                "is send_index=%r - the only turn row in this cell is a follow-up "
                "request, so no row can define the turn's own initial TTFT"
                % (key, slot["turn_send_index"]))
    return out


def row_outcome(row):
    """True/False when the row is decidable, None when it is not.

    Priority: an explicit boolean `passed` (then `ok`, then `correct`); else a
    NUM answer compared to `expected`. Everything else - including TEXT and
    NONE answers - is UNDECIDABLE and leaves the denominator, rather than being
    silently charged as a failure.
    """
    if not isinstance(row, dict):
        return None
    for key in ("passed", "ok", "correct"):
        v = row.get(key)
        if isinstance(v, bool):
            return v
    if row.get("answer_kind") != "NUM":
        return None
    got, exp = row.get("answer_value"), row.get("expected")
    if got is None or exp is None:
        return None
    if row.get("answer_parse_error"):
        return False
    try:
        return abs(float(got) - float(exp)) <= 1e-9 * max(1.0, abs(float(exp)))
    except (TypeError, ValueError):
        return str(got).strip() == str(exp).strip()


GRADED_N_SOURCE = "analyze_stats.py:accuracy_from_grade"


def accuracy_from_grade(grade, arm):
    """Accuracy population = the grader's checkpoint cells, NEVER re-derived rows.

    `grade_v5.py` emits exactly one cell per (arm, truth checkpoint). Counting
    `row_outcome()` over the row file is a DIFFERENT population: the v6 rows
    carry `answer_kind = null` (the runner grades from `content`, see
    `grade_v5.py:_parsed_from_row`), and the file also carries `tool-followup`
    rows, so a row-derived denominator is both empty and the wrong size. The
    grader's cells are therefore the only accuracy input.

    The counts are NOT computed here. They are `grade_v5.decidable_population`'s,
    called and passed through, because this function used to carry its own copy
    of the rule and the copy had already drifted from the grader's:
    it excluded `turn_missing` from `failed`, so every arm with unanswered
    checkpoints reported a SMALLER denominator than the grade document for the
    same cells (5/8 here vs 5/19 in `measure/MATRIX-*.json`). One function owns
    the number; this is a caller.

    The populations, per that owner:
      pass        verdict == "pass"
      fail        verdict == "fail", INCLUDING reason == "turn_missing"
      undecidable verdict == "undecidable" (a non-answer) or a cell with no
                  verdict at all (`pass: null`) - it decides nothing
      text        verdict == "text" (structurally accepted, never a truth pass)
      missing     reason == "turn_missing": a SUBSET of `fail`, printed beside it
      decidable   pass + fail; text and undecidable are outside the denominator
    """
    cells = [c for c in (grade.get("cells") or [])
             if (c.get("arm") or "default") == arm]
    pop = grade_v5.decidable_population(cells)
    arms = grade.get("arms") or {}
    garm = arms.get(arm) or {}
    return {"source": "grade_v5", "graded_n": pop["cells"],
            "passed": pop["passed"], "failed": pop["failed"],
            "undecidable": pop["undecidable"], "missing": pop["missing"],
            "decidable": pop["decidable"],
            "decidable_source": pop["source"],
            # the grader's own counter, kept beside ours so future drift is visible
            "grade_decidable": int(garm.get("decidable") or 0),
            "grade_accuracy": garm.get("checkpoint_accuracy")}


# --- THE enforcement point --------------------------------------------------
def render_estimate(label, point, lo, hi, n, unit="", digits=2):
    """The ONLY printer of a point estimate in this module.

    Refuses (raises `BareMetricError`) when n is missing/non-positive, when
    either interval endpoint is missing, or when the interval does not contain
    the point. Callers cannot produce a bare p95 by forgetting to pass the
    interval: there is no other formatting path.
    """
    if n is None or n <= 0:
        raise BareMetricError(
            "%s: refusing to print %r with n=%r - a point estimate needs its n"
            % (label, point, n))
    if point is None:
        raise BareMetricError("%s: no point estimate (n=%d)" % (label, n))
    if lo is None or hi is None:
        raise BareMetricError(
            "%s: refusing to print the bare value %r at n=%d - an interval is "
            "required" % (label, point, n))
    if lo > hi:
        raise BareMetricError("%s: inverted interval [%r, %r]" % (label, lo, hi))
    if not (lo - 1e-12 <= point <= hi + 1e-12):
        raise BareMetricError(
            "%s: point %r outside its interval [%r, %r]" % (label, point, lo, hi))
    return "%s n=%d  %.*f%s [%.*f, %.*f]" % (
        label, n, digits, point, unit, digits, lo, digits, hi)


# --- the provenance gate: ONE entry point every comparison goes through ------
def _canon(value):
    """One provenance value, canonical: missing/blank/"mixed" -> "unknown"."""
    if value is None:
        return PROVENANCE_UNKNOWN
    if isinstance(value, str):
        text = value.strip()
        if not text or text == _PROV_MIXED:
            return PROVENANCE_UNKNOWN
        return text
    return value


def cell_provenance(cell):
    """Coerce a row / `row_provenance.aggregate()` record / plain dict into a cell.

    Accepts all three shapes the project uses for "a cell": a raw row dict, an
    aggregate record (which nests the values under ``"fields"``), or a plain dict
    of the nine provenance fields. Only the four load-bearing fields survive, so a
    caller cannot hand `compare()` an `arm`-only dict and have it pass by omission:
    everything missing becomes ``"unknown"``, and unknown-vs-unknown refuses.
    """
    if isinstance(cell, dict) and isinstance(cell.get("fields"), dict):
        cell = cell["fields"]
    if not isinstance(cell, dict):
        cell = {}
    return {name: _canon(cell.get(name)) for name in PROVENANCE_LOAD_BEARING}


def provenance_short(value, width=12):
    """The short form printed beside an interval: the first `width` hex chars."""
    text = str(_canon(value))
    return text[:width]


def provenance_line(label, cell):
    """One line naming the provenance an interval/verdict was computed under."""
    p = cell_provenance(cell)
    return ("provenance %s: fixture_sha256=%s model=%s thinking=%s tools_mode=%s"
            % (label, provenance_short(p["fixture_sha256"]), p["model"],
               p["thinking"], p["tools_mode"]))


def provenance_pair_line(gate):
    """Both sides of a comparison, so each verdict carries both fixture shorts."""
    a, b = gate["a"], gate["b"]
    tail = ""
    if gate["overridden"]:
        tail = ("  PROVENANCE OVERRIDE (assumed comparable over %s)"
                % ", ".join(gate["differing"]))
    return ("provenance: fixture_sha256=%s vs %s  thinking=%s vs %s  "
            "tools_mode=%s vs %s  model=%s vs %s%s"
            % (provenance_short(a["fixture_sha256"]),
               provenance_short(b["fixture_sha256"]),
               a["thinking"], b["thinking"], a["tools_mode"], b["tools_mode"],
               a["model"], b["model"], tail))


def require_comparable(cell_a, cell_b, assume_comparable=False, label=""):
    """THE provenance gate. ``same_provenance`` decides; this raises or annotates.

    Returns a gate record ``{comparable, differing, overridden, a, b}``. Raises
    `IncomparableProvenance` whose message starts with ``incomparable_provenance``
    and names every differing field, unless `assume_comparable` is set -- in which
    case the record carries ``overridden: True`` and the differing fields so the
    override is visible in the artefact, not just in a transcript.
    """
    a = cell_provenance(cell_a)
    b = cell_provenance(cell_b)
    ok, differing = same_provenance(a, b)
    where = (" " + label) if label else ""
    if ok:
        return {"comparable": True, "differing": [], "overridden": False,
                "a": a, "b": b}
    detail = ", ".join("%s (%r vs %r)" % (f, a.get(f), b.get(f)) for f in differing)
    if not assume_comparable:
        raise IncomparableProvenance(
            "%s%s: refusing to compare two cells whose load-bearing provenance "
            "differs on %s -- %s. No interval and no verdict is computed. "
            "Re-run with --assume-comparable to override LOUDLY (the artefact then "
            "records provenance_override: true and these fields)."
            % (INCOMPARABLE_PROVENANCE, where, ", ".join(differing), detail),
            differing, a, b)
    return {"comparable": False, "differing": differing, "overridden": True,
            "a": a, "b": b}


def compare(cell_a, cell_b, *, statistic="quantile", values_a=None, values_b=None,
            q=0.95, pairs=None, resamples=RESAMPLES, seed=SEED,
            assume_comparable=False, label=""):
    """Compare two cells. The provenance gate runs FIRST, for every statistic.

    This is the only comparison entry point: the quantile path (H1's p50/p95) and
    the McNemar path (H3) both dispatch from here, and the gate is inspected before
    `statistic` is even looked at -- so choosing McNemar cannot route around the
    refusal that the quantile path would have raised.

    ``statistic="quantile"`` computes each arm's interval with the existing
    `quantile_ci` (thresholds untouched: n>=20 and n*(1-q)>=3) and reports whether
    the two intervals overlap. It adds NO estimator of its own.
    ``statistic="mcnemar"`` calls the existing `mcnemar_exact` (b+c>=6 untouched).
    """
    gate = require_comparable(cell_a, cell_b,
                              assume_comparable=assume_comparable, label=label)
    rec = {"statistic": statistic, "label": label,
           "a": gate["a"], "b": gate["b"],
           "provenance": {"comparable": gate["comparable"],
                          "differing": list(gate["differing"]),
                          "overridden": gate["overridden"],
                          "a": gate["a"], "b": gate["b"]},
           "provenance_override": bool(gate["overridden"]),
           "incomparable_provenance": None,
           "refused": None, "refused_kind": None}
    if not gate["comparable"]:
        rec["incomparable_provenance"] = {"differing": list(gate["differing"]),
                                          "a": gate["a"], "b": gate["b"]}

    if statistic == "quantile":
        if not (0.0 < q < 1.0):
            raise ValueError("compare: q must be in (0,1), got %r" % (q,))
        for side, vals in (("a", values_a), ("b", values_b)):
            try:
                point, lo, hi, n = quantile_ci(vals or (), q,
                                               resamples=resamples, seed=seed)
                rec[side] = {"point": point, "lo": lo, "hi": hi, "n": n}
            except InsufficientSamples as exc:
                rec[side] = {"refused": str(exc), "n": len(list(vals or ()))}
                rec["refused"] = str(exc)
                rec["refused_kind"] = "insufficient_samples"
        if rec["refused"] is None:
            rec["intervals_overlap"] = not (rec["a"]["hi"] < rec["b"]["lo"]
                                            or rec["b"]["hi"] < rec["a"]["lo"])
        return rec

    if statistic == "mcnemar":
        try:
            nb, nc, p = mcnemar_exact(pairs or ())
            rec["mcnemar"] = {"b": nb, "c": nc, "p": p}
        except RefusedTest as exc:      # b + c < 6: unchanged licensing floor
            rec["mcnemar"] = None
            rec["refused"] = str(exc)
            rec["refused_kind"] = "refused_test"
        return rec

    raise ValueError("compare: unknown statistic %r" % (statistic,))


def provenance_cells(rows, path=None):
    """arm -> coerced provenance cell, using the SAME ladder `row_provenance.py` uses.

    With `path`, each row is resolved through ``row->manifest->cell`` exactly as
    ROW-PROVENANCE's retrofit report resolves it, then collapsed per arm with
    `row_provenance.aggregate` (a field the arm's own rows disagree on becomes
    "mixed" there and "unknown" here). Without `path`, only the fields the rows
    themselves carry are known -- honest, and it refuses pairs whose `model` /
    `tools_mode` no row ever named, rather than assuming them.
    """
    rows = [r for r in (rows or ()) if isinstance(r, dict)]
    if path:
        manifests = _row_provenance.load_manifests()
        cells = _row_provenance.load_cells()
        index = _row_provenance.fixture_index()
        base = os.path.basename(path)
        man = _row_provenance.match_manifest(manifests, base)
        cell = _row_provenance.match_cell(cells, base)
        blocks = {}
        for row in rows:
            blocks.setdefault(_arm_of(row), []).append(
                _row_provenance.row_provenance(row, man, cell, index))
        return {arm: cell_provenance(_row_provenance.aggregate(bl))
                for arm, bl in blocks.items()}

    acc = {}
    for row in rows:
        slot = acc.setdefault(_arm_of(row),
                              {n: [] for n in PROVENANCE_LOAD_BEARING})
        for name in PROVENANCE_LOAD_BEARING:
            v = _canon(row.get(name))
            if v not in slot[name]:
                slot[name].append(v)
    return {arm: {n: (vals[0] if len(vals) == 1 else PROVENANCE_UNKNOWN)
                  for n, vals in slot.items()}
            for arm, slot in acc.items()}


def _refusal_record(exc, statistic, label):
    """The record `analyze()` keeps when `compare()` refused to compute anything.

    The library-level `compare()` still RAISES (`IncomparableProvenance`) -- that is
    the named refusal, and a caller that wants a number cannot get one. The report
    builder catches it here so ONE refused pair does not abort the whole report: it
    records the refusal, the kind and the differing fields in the artefact instead.
    """
    return {"statistic": statistic, "label": label,
            "a": {"provenance": dict(exc.a)},
            "b": {"provenance": dict(exc.b)},
            "provenance": {"comparable": False, "differing": list(exc.differing),
                           "overridden": False,
                           "a": dict(exc.a), "b": dict(exc.b)},
            "provenance_override": False,
            "incomparable_provenance": {"differing": list(exc.differing),
                                        "a": dict(exc.a), "b": dict(exc.b)},
            "refused": str(exc), "refused_kind": INCOMPARABLE_PROVENANCE}


# --- analysis ---------------------------------------------------------------
def _arm_of(row):
    arm = row.get("arm")
    return str(arm) if arm not in (None, "") else "(unlabelled)"


def analyze(rows, resamples=RESAMPLES, seed=SEED, grade=None, provenance=None,
            assume_comparable=False, selector=None, claim_refusal=None,
            rows_path=None):
    """Compute every reported statistic for a list of rows -> dict.

    Pure: no I/O, no printing. The CLI renders this dict through
    `render_estimate`, so the refusal rules bind the output, not this function.

    `selector` is the per-turn TTFT selector; it defaults to
    `turn_latency_rows` and exists only so a test can prove what the definition
    changes (pass the identity to reproduce the pre-definition behaviour). Every
    per-turn latency number in the result -- the arm p50/p95 AND the values the
    quantile comparisons are handed -- comes from ONE call to it per arm, so the
    definition cannot be half-applied.

    `grade` is the parsed `grade_v5.py` output document. When present, the
    accuracy block comes from its checkpoint cells (`accuracy_from_grade`) and
    is never re-derived from rows; `timing_n` and `graded_n` are then printed
    separately because TTFT and accuracy cover different populations.

    `provenance` maps arm -> cell (a row, an aggregate record, or a nine-field
    dict). When omitted every arm's cell is derived from the rows themselves, so
    an arm whose rows never named `model`/`tools_mode` has an UNKNOWN cell and its
    comparisons are refused rather than assumed. Every cross-arm number in the
    result -- the McNemar pair AND the quantile comparisons -- is produced by
    `compare()`, so none of them can be computed without passing the gate.
    """
    selector = turn_latency_rows if selector is None else selector
    arms = {}
    for row in rows or ():
        if isinstance(row, dict):
            arms.setdefault(_arm_of(row), []).append(row)

    prov = dict(provenance) if provenance is not None else provenance_cells(rows)

    if claim_refusal is None:
        try:
            require_comparable_claim(rows, "analyze()", rows_path)
        except IncomparableClaim as exc:
            claim_refusal = exc
    report = {"arms": {}, "pairs": [], "quantile_comparisons": [],
              "incomparable_claim": (None if claim_refusal is None else
                                     {"refused": str(claim_refusal),
                                      "offenders": list(claim_refusal.offenders)}),
              "n_rows": len(rows or ()), "provenance_override": bool(assume_comparable),
              "assume_comparable": bool(assume_comparable),
              "definition": {"definition": TTFT_DEFINITION,
                             "version": TTFT_DEFINITION_VERSION,
                             "fallback_arms": [], "mirrored_rows": {}}}
    for arm, arm_rows in sorted(arms.items()):
        selected, sel_meta = selector(arm_rows)
        # The truncated-turn rule is applied HERE, to the ONE selection the
        # definition produced, so p50 and p95 are handed the same population and
        # the rule cannot be half-applied. `selected` itself is untouched: the
        # McNemar pairs and the accuracy/ledger accounting keep every row.
        latency_selected, trunc_meta = split_truncated(selected)
        vals, nulls, unavailable = ttft_values(latency_selected)
        outcomes = [row_outcome(r) for r in arm_rows]
        decidable = [o for o in outcomes if o is not None]
        passed = sum(1 for o in decidable if o)
        entry = {
            "arm": arm,
            "n_rows": len(arm_rows),
            "provenance": cell_provenance(prov.get(arm)),
            "definition": sel_meta.get("definition", TTFT_DEFINITION),
            "definition_fallback": bool(sel_meta.get("definition_fallback")),
            "truncated_turns": trunc_meta,
            "ttft": {
                "input": len(arm_rows), "used": len(vals),
                "selected": len(selected),
                "selected_for_latency": len(latency_selected),
                "dropped_null": nulls, "dropped_unavailable": unavailable,
                "definition": sel_meta,
                "values": vals,
            },
            "accuracy": None,
        }
        if entry["definition_fallback"]:
            report["definition"]["fallback_arms"].append(arm)
        report["definition"]["mirrored_rows"][arm] = sel_meta.get("mirrored_rows", 0)
        if grade is not None:
            entry["accuracy"] = accuracy_from_grade(grade, arm)
        else:
            entry["accuracy"] = {
                "source": "rows", "graded_n": 0,
                "passed": passed, "failed": len(decidable) - passed,
                "decidable": len(decidable),
                "undecidable": len(outcomes) - len(decidable),
                "missing": 0, "grade_decidable": None, "grade_accuracy": None,
            }
        entry["accuracy"]["timing_n"] = len(arm_rows)
        for q, key in ((0.50, "p50"), (0.95, "p95")):
            st = {}
            try:
                point, lo, hi, n = quantile_ci(vals, q, resamples=resamples,
                                               seed=seed, stats=st)
                entry[key] = {"point": point, "lo": lo, "hi": hi, "n": n,
                              "stats": st}
            except InsufficientSamples as exc:
                entry[key] = {"refused": str(exc), "n": len(vals), "stats": st}
        report["arms"][arm] = entry

    labels = sorted(report["arms"])
    for i, a in enumerate(labels):
        for j in range(i + 1, len(labels)):
            b = labels[j]
            cell_a, cell_b = prov.get(a), prov.get(b)
            # (1) H3 path: exact McNemar over paired turn outcomes ---------------
            pairs, pstats = paired_by_turn(arms[a], arms[b], select=selector)
            trial = []
            for _k, ra, rb in pairs:
                oa, ob = row_outcome(ra), row_outcome(rb)
                if oa is None or ob is None:
                    continue
                trial.append((oa, ob))
            rec = {"arm_a": a, "arm_b": b, "pairs": pstats,
                   "scored": len(trial)}
            if claim_refusal is not None:
                # A claim=none cell is REFUSED BY NAME here, not dropped from the group:
                # the pair and both quantile comparisons carry the refusal instead of a
                # number, so no reader can pool a smoke cell with an H1/H2/H3 arm.
                for statistic, key in (("mcnemar", None), ("quantile", "p50"),
                                       ("quantile", "p95")):
                    crec = _claim_refusal_record(claim_refusal, statistic,
                                                 "%s vs %s" % (a, b))
                    if key is None:
                        crec.update({"mcnemar": None, "arm_a": a, "arm_b": b,
                                     "pairs": pstats, "scored": len(trial)})
                        report["pairs"].append(crec)
                    else:
                        crec["quantile"] = key
                        crec["arm_a"], crec["arm_b"] = a, b
                        report["quantile_comparisons"].append(crec)
                continue
            try:
                cmp = compare(cell_a, cell_b, statistic="mcnemar", pairs=trial,
                              assume_comparable=assume_comparable,
                              label="%s vs %s" % (a, b))
            except IncomparableProvenance as exc:
                cmp = _refusal_record(exc, "mcnemar", "%s vs %s" % (a, b))
            rec["mcnemar"] = cmp.get("mcnemar")
            rec["refused"] = cmp["refused"]
            rec["refused_kind"] = cmp["refused_kind"]
            rec["provenance"] = cmp["provenance"]
            rec["provenance_override"] = cmp["provenance_override"]
            rec["incomparable_provenance"] = cmp["incomparable_provenance"]
            report["pairs"].append(rec)

            # (2) H1 path: the p50/p95 comparison, through the SAME gate --------
            for q, key in ((0.50, "p50"), (0.95, "p95")):
                try:
                    qrec = compare(cell_a, cell_b, statistic="quantile", q=q,
                                   values_a=report["arms"][a]["ttft"]["values"],
                                   values_b=report["arms"][b]["ttft"]["values"],
                                   resamples=resamples, seed=seed,
                                   assume_comparable=assume_comparable,
                                   label="%s vs %s" % (a, b))
                except IncomparableProvenance as exc:
                    qrec = _refusal_record(exc, "quantile", "%s vs %s" % (a, b))
                qrec["quantile"] = key
                qrec["arm_a"], qrec["arm_b"] = a, b
                report["quantile_comparisons"].append(qrec)
    return report


def _format_arm(entry):
    lines = []
    t = entry["ttft"]
    lines.append("arm %s  (rows n=%d)" % (entry["arm"], entry["n_rows"]))
    # The definition every per-turn figure on this block is computed over, with
    # the selector's own counts, so no figure is bare of its denominator.
    dm = t.get("definition") or {}
    lines.append("  definition: per-turn TTFT = the turn's own initial request "
                 "(kind=turn-initial, else legacy kind=turn)  version=%s  "
                 "turns selected=%d of %d rows  follow-up rows dropped=%d  "
                 "mode=%s  definition_fallback=%s%s"
                 % (dm.get("definition_version"),
                    t["selected"], t["input"], dm.get("dropped_followup", 0),
                    dm.get("mode"), str(bool(entry.get("definition_fallback"))).lower(),
                    ("  mirrored_turns=%d (fallback rows whose turn also has "
                     "follow-up rows: these quote the last send of the turn, not "
                     "its initial request)" % dm["mirrored_rows"])
                    if dm.get("mirrored_rows") else ""))
    tt = entry.get("truncated_turns") or {}
    if tt.get("excluded"):
        frac = tt.get("fraction")
        lines.append("  truncated_turns  excluded=%d of %d selected turn(s)%s  "
                     "from the latency quantiles (p50 and p95)  surviving n=%d  "
                     "[%s]"
                     % (tt.get("excluded", 0), tt.get("total"),
                        ("  fraction=%.1f%%" % (100.0 * frac))
                        if frac is not None else "",
                        t.get("used", 0), tt.get("rule_version")))
    # Every interval below carries the provenance it was computed under.
    lines.append("  " + provenance_line(entry["arm"], entry.get("provenance")))
    drop_note = "(ttft dropped: %d null, %d unavailable)" % (
        t["dropped_null"], t["dropped_unavailable"])
    for key in ("p50", "p95"):
        est = entry[key]
        st = est.get("stats") or {}
        span = st.get("rank_span_pct")
        span_note = ""
        if span:
            span_note = "  order-stat span p%.1f-p%.1f" % span
        if est.get("refused"):
            lines.append("  ttft_%s  REFUSED at n=%d  %s"
                         % (key, st.get("used", t["used"]), est["refused"]))
            continue
        lines.append("  " + render_estimate(
            "ttft_%s" % key, est["point"], est["lo"], est["hi"], est["n"],
            unit="ms") + "  " + drop_note + span_note)
    acc = entry["accuracy"]
    # TWO populations, each named on its own line. TTFT covers every row with a
    # usable timing column; accuracy covers the grader's checkpoint cells. They
    # are allowed to differ - what is forbidden is one headline whose numerator
    # and denominator come from different populations.
    lines.append("  timing_n = %d  (rows with a usable ttft_ms)" % acc["timing_n"])
    lines.append("  graded_n = %d  (checkpoint cells graded by %s)" %
                 (acc["graded_n"], acc["source"]))
    if acc["decidable"] == 0:
        if acc["graded_n"] == 0:
            lines.append("  accuracy = UNDECIDABLE (pass 0, fail 0, undecidable %d, "
                         "missing %d)" % (acc["undecidable"], acc["missing"]))
        else:
            # Graded cells exist but none carries a truth value (all TEXT or
            # missing): the population is NAMED, and the estimate is refused.
            lines.append("  accuracy = 0/0 (pass 0, fail 0, undecidable %d, "
                         "missing %d)" % (acc["undecidable"], acc["missing"]))
            lines.append("  accuracy wilson95 REFUSED at n=0 (no decided checkpoint)")
    else:
        p, lo, hi = wilson_ci(acc["passed"], acc["decidable"])
        lines.append("  accuracy = %d/%d (pass %d, fail %d, undecidable %d, "
                     "missing %d)" % (acc["passed"], acc["decidable"],
                                      acc["passed"], acc["failed"],
                                      acc["undecidable"], acc["missing"]))
        lines.append("  " + render_estimate("accuracy wilson95", p, lo, hi,
                                            acc["decidable"], digits=4))
    return lines


def _format_pair(rec):
    head = "pair %s vs %s" % (rec["arm_a"], rec["arm_b"])
    ps = rec["pairs"]
    count = ("  (pairs formed=%d, missing-key dropped=%d, unpaired=%d, "
             "follow-up rows dropped=%d+%d, definition_fallback=%s/%s)"
             % (ps["formed"], ps["dropped_missing_key"],
                ps["dropped_unpaired"], ps.get("dropped_followup_a", 0),
                ps.get("dropped_followup_b", 0),
                str(ps.get("definition_fallback_a")).lower(),
                str(ps.get("definition_fallback_b")).lower()))
    lines = ["  " + head, "    " + provenance_pair_line(rec["provenance"])]
    if rec.get("refused"):
        kind = rec.get("refused_kind")
        tag = "REFUSED (%s)" % kind if kind else "REFUSED"
        lines.append("    %s  %s%s" % (tag, rec["refused"], count))
        return lines
    m = rec["mcnemar"]
    lines.append("    McNemar exact: b=%d c=%d p=%.5f  (scored turns=%d)%s"
                 % (m["b"], m["c"], m["p"], rec["scored"], count))
    return lines


def _format_quantile_comparison(rec):
    """One H1 comparison line: both arms' intervals, both provenance cells."""
    head = "compare %s %s vs %s" % (rec.get("quantile", "?"),
                                    rec.get("arm_a"), rec.get("arm_b"))
    lines = ["  " + head, "    " + provenance_pair_line(rec["provenance"])]
    kind = rec.get("refused_kind")
    if kind == INCOMPARABLE_PROVENANCE:
        # The named refusal: no interval is printed anywhere on this line.
        lines.append("    REFUSED (%s)  %s" % (kind, rec["refused"]))
        return lines
    if rec.get("refused"):
        side = "a" if rec["a"].get("refused") else "b"
        lines.append("    REFUSED (%s) at n=%d  %s"
                     % (kind, rec[side].get("n", 0), rec["refused"]))
        return lines
    for side, arm in (("a", rec["arm_a"]), ("b", rec["arm_b"])):
        s = rec[side]
        lines.append("    " + render_estimate(
            "%s %s" % (arm, rec.get("quantile")), s["point"], s["lo"], s["hi"],
            s["n"], unit="ms"))
    lines.append("    intervals_overlap = %s"
                 % ("yes" if rec["intervals_overlap"] else "no"))
    return lines


def is_derived_rows(path):
    """True when this JSONL is a DERIVED artefact (pooled view), not a measurement.

    POOL-REPS-TOOL writes `measure/pooled/pooled-*.jsonl` with `derived: true` on
    every row. Such a file is a view over measured cells, not a cell: reading it
    without saying so would let a derived number wear a measurement's authority.
    One marker check on the first readable row; a file that cannot be read is not
    claimed to be derived.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                return (isinstance(obj, dict)
                        and (obj.get("derived") is True or bool(obj.get("pooled_arm"))))
    except (OSError, ValueError):
        return False
    return False



# ---------------------------------------------------------------- row-count assertion (gate 0.5)
class RowCountAssertionError(ValueError):
    """Raised when row_count != cells * turns * reps or keys are not unique."""


def _row_cell(row):
    for key in ("cell", "cell_id", "task_id", "fixture_id"):
        val = row.get(key)
        if val is not None:
            return val
    return None


def _row_turn(row):
    for key in ("turn_index", "turn", "step"):
        val = row.get(key)
        if val is not None:
            return val
    return None


def assert_row_count(rows, cells=None, turns=None, reps=None, generation=None) -> bool:
    """Pre-analysis assertion: row_count == cells * turns * reps, unique key.

    The unique key is (arm, rep, cell, turn_index). On mismatch refuses to
    analyse and names the deficit. Returns True on success.
    """
    rows = [r for r in (rows or ()) if isinstance(r, dict)]
    # LEGACY-NONCONFORMING: generation recorded on the row wins; an explicit
    # argument overrides it. gen-7 (and later) assert hard; gen-6 and earlier are
    # labelled and analysed under the old path with the deficit printed.
    if generation is None:
        gens = { (r.get("generation") if isinstance(r, dict) else None) for r in rows }
        if gens and gens <= {"gen-7", 7, "7"} and None not in gens:
            generation = "gen-7"
        else:
            generation = "gen-6"
    is_legacy = str(generation) not in ("gen-7", "7", "7.0") and generation not in (7,)
    cells_u = { _row_cell(r) for r in rows }
    turns_u = { _row_turn(r) for r in rows }
    reps_u = { r.get("rep") for r in rows }
    if cells is None:
        cells = len(cells_u)
    if turns is None:
        turns = len(turns_u)
    if reps is None:
        reps = len(reps_u)
    expected = int(cells) * int(turns) * int(reps)
    keys = []
    seen = set()
    duplicates = []
    for r in rows:
        key = (r.get("arm"), r.get("rep"), _row_cell(r), _row_turn(r))
        keys.append(key)
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    problems = []
    if len(rows) != expected:
        problems.append(
            "row_count=%d != cells(%d)*turns(%d)*reps(%d)=%d (deficit=%d)"
            % (len(rows), cells, turns, reps, expected, expected - len(rows)))
    if duplicates:
        problems.append("duplicate keys: %s" % (duplicates[:10],))
    if len(seen) != len(rows):
        problems.append("non-unique keys: %d unique of %d rows" % (len(seen), len(rows)))
    if problems:
        msg = "; ".join(problems)
        if is_legacy:
            print("LEGACY-NONCONFORMING: " + msg)
            return False
        raise RowCountAssertionError(msg)
    return True


row_count_assertion = assert_row_count
check_row_count = assert_row_count
assert_row_identity = assert_row_count


# ---------------------------------------------------------------- activation predicates (gate 0.6)
def _activation_counts(rows):
    rows = [r for r in (rows or ()) if isinstance(r, dict)]
    retrieval_outcomes = [o for r in rows for o in (r.get("retrieval_outcomes") or [])]
    return {
        "evicted_turns": sum(1 for r in rows if (r.get("evicted") or 0) > 0
                             or (r.get("evicted_turns") or 0) > 0),
        "digest_rows": sum(1 for r in rows if r.get("kind") == "digest"
                           or (r.get("digest_rows") or 0) > 0),
        "masked_rows": sum(1 for r in rows if (r.get("masked_rows") or 0) > 0),
        "fetch_rows": sum(1 for r in rows if (r.get("fetch_rows") or 0) > 0
                          or (r.get("retrieval_attempts") or 0) > 0),
        "retrieval_outcomes": retrieval_outcomes,
        "oracle_injections": sum(1 for r in rows if (r.get("oracle_injections") or 0) > 0),
    }


def activation_predicate(arm, rows) -> bool:
    counts = _activation_counts(rows)
    arm = str(arm or "").strip()
    upper = arm.upper()
    name = arm.lower()
    if upper == "A" or "transcript" in name or "full" in name:
        return counts["evicted_turns"] > 0
    if upper == "B" or "compact" in name:
        return counts["digest_rows"] > 0
    if upper == "C" or "mask" in name:
        return counts["masked_rows"] > 0
    if upper == "D" or "bounded" in name or "recover" in name:
        return counts["fetch_rows"] > 0 and len(counts["retrieval_outcomes"]) > 0
    if upper == "E" or "oracle" in name:
        return counts["oracle_injections"] > 0
    return False


activation_predicates = {
    "A": "evicted_turns",
    "B": "digest_rows",
    "C": "masked_rows",
    "D": "fetch_rows",
    "E": "oracle_injections",
}
arm_activation_predicate = activation_predicate
predicate_for_arm = activation_predicate


def instrument_status(arm, rows) -> str:
    return "INVALID-INSTRUMENT" if not activation_predicate(arm, rows) else "VALID"

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Per-arm n / p50 / p95-with-CI / accuracy-with-Wilson CI / "
                    "exact McNemar. Refuses to print a bare point estimate.")
    ap.add_argument("--rows", nargs="+", default=None,
                    help="one or more row JSONL files")
    ap.add_argument("--json", default=None, help="write the analysis as JSON here")
    ap.add_argument("--grade", default=None,
                    help="grade_v5.py output JSON: accuracy population comes from "
                         "its checkpoint cells, never re-derived from rows")
    ap.add_argument("--resamples", type=int, default=RESAMPLES)
    ap.add_argument("--assume-comparable", action="store_true",
                    help="OVERRIDE LOUDLY: compare cells whose load-bearing "
                         "provenance differs. The run records provenance_override: "
                         "true and the differing fields in stdout AND in --json, so "
                         "the override is visible in the artefact. There is no "
                         "environment variable and no default-on.")
    ap.add_argument("--check-definition", action="store_true",
                    help="report (and exit 3 on) any row set that violates the "
                         "per-turn TTFT definition contract; exits 0 when every "
                         "cell can be selected exactly as defined")
    ap.add_argument("--manifest", action="append", default=None,
                    help="cell manifest carrying usable_for (repeatable); the "
                         "primary carrier, and it outranks the census")
    ap.add_argument("--no-census", action="store_true",
                    help="do not consult measure/GRID-CELL-SANITY.json for an "
                         "unstamped cell's usable_for")
    ap.add_argument("--stamp-rows", default=None,
                    help="write this cell's usable_for into its manifest and exit")
    ap.add_argument("--usable-for", default=None,
                    help="comma-separated analyses for --stamp-rows; empty string "
                         "stamps usable_for: [] (cell is excluded by name)")
    ap.add_argument("--usable-for-reason", default=None)
    ap.add_argument("--manifest-out", default=None,
                    help="manifest to stamp; default: the one whose rows_path "
                         "matches --stamp-rows")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cells", type=int, default=None)
    ap.add_argument("--turns", type=int, default=None)
    ap.add_argument("--reps", type=int, default=None)
    ap.add_argument("--pooled", action="store_true",
                    help="READ A DERIVED ARTEFACT: pool_reps.py writes pooled-*.jsonl "
                         "with derived: true; without this flag such a file is refused "
                         "so a derived view is never read as a measured cell")
    args = ap.parse_args(argv)

    if args.stamp_rows:
        uf = [x.strip() for x in (args.usable_for or "").split(",") if x.strip()]
        man = write_cell_manifest_usable_for(
            args.stamp_rows, uf, reason=args.usable_for_reason,
            manifest_path=args.manifest_out, dry_run=args.dry_run)
        print("stamped usable_for=%r into %s%s"
              % (man.get(USABLE_FOR_FIELD),
                 os.path.basename(man.get("_manifest_path") or args.manifest_out
                                  or args.stamp_rows),
                 "  (dry-run, nothing written)" if args.dry_run else ""))
        return 0
    if not args.rows:
        raise SystemExit("--rows is required (or --stamp-rows)")

    # HONESTY RULE (POOL-REPS-TOOL): a derived pooled artefact is not a measurement.
    # It is readable only when the caller says, explicitly, that it wants the derived
    # view -- otherwise a derived n=144 would silently outrank the measured cells it
    # was built from.
    if not args.pooled:
        for path in args.rows:
            if is_derived_rows(path):
                raise SystemExit(
                    "refused: %s is a DERIVED artefact (derived=true, "
                    "purpose=%r), not a measured cell; pass --pooled to analyse the "
                    "pooled view explicitly" % (os.path.basename(path), "H1 pooled R-all"))

    grade = None
    if args.grade:
        with open(args.grade, encoding="utf-8") as fh:
            grade = json.load(fh)
        if not isinstance(grade, dict) or "cells" not in grade:
            raise SystemExit("--grade %s is not a grade_v5 document (no `cells`)"
                             % args.grade)

    rows, files = [], []
    for path in args.rows:
        per_file = []
        with open(path, "rb") as fh:
            blob = fh.read()
        for line in blob.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue  # half-written tail: never fatal
            if isinstance(obj, dict):
                per_file.append(obj)
        files.append((path, len(per_file), per_file))
        rows.extend(per_file)

    print("analyze_stats  rows=%d  files=%d" % (len(rows), len(files)))
    print("  definition[%s]: %s" % (TTFT_DEFINITION_VERSION, TTFT_DEFINITION))
    for path, count, _per_file in files:
        print("  %s  rows=%d" % (os.path.basename(path), count))

    if args.check_definition:
        bad = 0
        for path, _count, file_rows in files:
            violations = definition_violations(file_rows)
            if violations:
                bad += 1
                print("  DEFINITION VIOLATION  %s  %d finding(s)"
                      % (os.path.basename(path), len(violations)))
                for v in violations:
                    print("    - %s" % v)
            else:
                print("  definition ok  %s" % os.path.basename(path))
        if bad:
            print("  %d file(s) violate the per-turn TTFT definition" % bad)
            return 3
        print("  every file satisfies the per-turn TTFT definition")
        return 0

    # Per-arm provenance, resolved through the SAME row->manifest->cell ladder
    # `row_provenance.py` uses. An arm fed by two files whose provenance differs
    # gets an UNKNOWN cell for the differing fields: the merged arm genuinely has
    # no single provenance, and refusing is the honest answer.
    # --- usable_for: exclude unusable cells BY NAME before any statistic ------
    manifests = load_cell_manifests(args.manifest)
    files, cell_usability = select_usable_cells(
        files, manifests=manifests, sanity=(False if args.no_census else None))
    for rec in cell_usability:
        if rec["excluded"]:
            print("  usable_for EXCLUDED  %s  %d row(s) NOT analysed  source=%s  "
                  "usable_for=[]  reason=%s"
                  % (rec["name"], rec["rows"], rec["source"],
                     rec["reason"] or "(none recorded)"))
        elif rec["usable_for"] is None:
            print("  usable_for unstamped  %s  (included: no usability stamp on "
                  "disk -- not a certification)" % rec["name"])
        else:
            print("  usable_for %s  %s  source=%s" %
                  (rec["usable_for"], rec["name"], rec["source"]))
    if not files:
        names = ", ".join(r["name"] for r in cell_usability) or "(none)"
        print("  usable_for EXCLUDED every cell: no usable cells (%s)" % names)
        raise SystemExit("no usable cells: every input cell is stamped "
                         "usable_for: [] -- refusing rather than printing an "
                         "empty table as success (%s)" % names)
    if getattr(args, 'cells', None) is not None and getattr(args, 'turns', None) is not None and getattr(args, 'reps', None) is not None:
        _gen = None
        for _r in rows:
            if isinstance(_r, dict) and _r.get("generation"):
                _gen = _r.get("generation")
                break
        try:
            assert_row_count(rows, args.cells, args.turns, args.reps, generation=_gen)
        except RowCountAssertionError as exc:
            print('  ROW-COUNT ASSERTION FAILED: %s' % exc)
            raise SystemExit(2)
    rows = [row for _p, _c, file_rows in files for row in file_rows]

    provenance = {}
    for path, _count, file_rows in files:
        for arm, cell in provenance_cells(file_rows, path).items():
            if arm not in provenance:
                provenance[arm] = dict(cell)
                continue
            prev = provenance[arm]
            provenance[arm] = {
                n: (prev[n] if prev[n] == cell[n] else PROVENANCE_UNKNOWN)
                for n in PROVENANCE_LOAD_BEARING}

    if args.assume_comparable:
        print("  !! PROVENANCE OVERRIDE: --assume-comparable is ON; every "
              "comparison below whose load-bearing provenance differs is computed "
              "ANYWAY and records provenance_override: true + the differing fields.")

    claim_refusal = None
    for path, _count, file_rows in files:
        try:
            require_comparable_claim(file_rows, os.path.basename(path), path)
        except IncomparableClaim as exc:
            if claim_refusal is None:
                claim_refusal = exc
            print("  CLAIM REFUSAL  %s" % exc)
    report = analyze(rows, resamples=args.resamples, grade=grade,
                     provenance=provenance,
                     assume_comparable=args.assume_comparable,
                     claim_refusal=claim_refusal, rows_path=None)
    for arm in sorted(report["arms"]):
        print("")
        for line in _format_arm(report["arms"][arm]):
            print(line)
    if report["pairs"]:
        print("")
        for rec in report["pairs"]:
            for line in _format_pair(rec):
                print(line)
    if report["quantile_comparisons"]:
        print("")
        for rec in report["quantile_comparisons"]:
            for line in _format_quantile_comparison(rec):
                print(line)

    incomparable = sum(1 for r in report["quantile_comparisons"] + report["pairs"]
                       if r.get("refused_kind") == INCOMPARABLE_PROVENANCE)
    if incomparable:
        print("")
        print("  %d comparison(s) REFUSED as %s: no interval, no verdict"
              % (incomparable, INCOMPARABLE_PROVENANCE))

    serialisable = {"n_rows": report["n_rows"], "arms": {}, "pairs": [],
                    "quantile_comparisons": report["quantile_comparisons"],
                    "incomparable_provenance_count": incomparable,
                    "definition": report["definition"],
                    "provenance_override": bool(args.assume_comparable),
                    "assume_comparable": bool(args.assume_comparable),
                     "cell_usability": cell_usability}
    if args.assume_comparable:
        serialisable["provenance_override_differing"] = sorted({
            f for rec in report["quantile_comparisons"] + report["pairs"]
            if rec.get("provenance_override")
            for f in (rec.get("provenance") or {}).get("differing") or []})
    for arm, e in report["arms"].items():
        serialisable["arms"][arm] = {
            "n_rows": e["n_rows"],
            "provenance": e["provenance"],
            "definition_fallback": e["definition_fallback"],
            "ttft": {k: v for k, v in e["ttft"].items() if k != "values"},
            "p50": {k: v for k, v in e["p50"].items() if k != "values"},
            "p95": {k: v for k, v in e["p95"].items() if k != "values"},
            "accuracy": e["accuracy"],
        }
    serialisable["pairs"] = report["pairs"]
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(serialisable, fh, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
