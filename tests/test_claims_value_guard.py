"""Guard the *text* of ``CLAIMS.md`` value cells, which no recompute run checks.

Why this exists (PAPER-FINAL-V2D): ``recompute.py`` and ``recompute_r2.py`` compare a value
re-derived from the raw rows against a hardcoded ``EXPECTED`` dict.  Neither ever reads a
value out of ``CLAIMS.md``; ``verify_package.py`` checks structure (claim-id mapping, row
existence), never numbers.  V2D therefore planted ``dense 19/20 -> 18/20`` ->
``dense 20/20 -> 20/20`` in C69 and ``all 12 arms`` -> ``11 of 12 arms`` at
``MANUSCRIPT.md:901`` and every checker stayed green.

This module is the missing link, in one direction only: a number a recompute pins must
still be legible in the value cell of the claim that pins it.  It adds checks; it loosens
nothing that already existed.

What is guarded (``CONTRACT``) is narrower than "every EXPECTED value" on purpose.  Some
pinned keys never appear verbatim in a cell: the recompute keeps six significant figures
where the prose quotes a rounded mean, or keeps a gcd, a per-cell count, or an 18-row table
the prose summarises.  Those legs are already covered by ``recompute.py all``, which
compares the re-derived value against the same dict.  The legs guarded here are the ones
that exist *only* as text in the claim:

* C64 -- the headline contrast and the padding arithmetic (``20.8429``, ``94.90``, ...).
* C65 -- the engine and model effects with their CIs (``549.33``, ``-400.02``, ``-803.65``).
* C69 (recompute alias ``SYSOPT``) -- the version-round means, deltas and quality pairs,
  written ``19/20 -> 18/20``, i.e. the pinned ``(before, after)`` mismatch counts over
  ``quality_n``.
* C62 -- the twelve-arm census that the manuscript's line 901 quotes.
* C63 -- the headline claim: the engine and model main effects with their CIs, the
  interaction, the two engine ratios and the four (model/engine, hit, unc/turn, hot gcd)
  cells.  Added by C63-CELL; before it C63 had no Value cell and was the one claim whose
  numbers existed only as prose in its cells.
* C66 (``TRACK``) -- the ``mamba_track_interval`` row: 355 rows and 0 non-200 per interval,
  the hot gcd 64 at all three intervals, and the arm means / paired turns-vs-256 deltas
  with their CIs.  Added by C66-C68-GUARD; before it the row was covered only by
  ``recompute_r2.py C66`` PASS, never by the cell contract.
* C67 (``R2PROMPT``) -- the prompt-layout round: the P1-P0 and P3-P1 deltas with their
  CIs (the C67a correction turns on O4's +23.5211), the four arm means per setup, and the
  284 rows / 4 arms / 0 non-200 census.  Added by C66-C68-GUARD.
* C68 (``DISTINCT``) -- the four-battery distinctness census: the per-cell config_sha256 and
  model, 284 distinct prompt digests, 0 rows repeating the P0 digest, the six cell pairs
  counted once (not twice), 4 distinct cells, and the six pairs' differing-cache-counter
  counts.  Added by C66-C68-GUARD.

The census check reads its arm count from ``recompute.EXPECTED["C62"]["arm_kinds"]`` -- the
number C62 actually measured -- so the sentence cannot claim more arms than were measured.

Two of the three batches added by C66-C68-GUARD carry a claim-specific STRUCTURAL leg
(``test_c67_intervals_and_c67a``, ``test_c68_pairs_are_counted_once``) that compares each
figure in the SLOT the cell put it in, at the precision the cell wrote it.  The generic
legible-in-cell check below was measured COSMETIC for both: planting ``[8.39, 53.48]`` ->
``[8.39, 58.48]`` in C67 and ``277 (O1 vs O3)`` -> ``271 (O1 vs O3)`` in C68 both stayed
green (exit 0), because a token matching ANY pinned figure in the cell satisfied it and
because the C67 interval keys were waived in favour of a leg that did not exist.  The
structural legs are also the comparators the falsifiability probe re-runs, so each one is
demonstrated to bite on a planted digit and to go green again once it is restored
(``orchestration/handoffs/C67-C68-GUARD-PROBE.json``).
"""
from __future__ import annotations

import contextlib
import importlib
import json
import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "papers" / "context-cache"
CLAIMS = PKG / "CLAIMS.md"
MANUSCRIPT = PKG / "MANUSCRIPT.md"

sys.path.insert(0, str(PKG))

import recompute  # noqa: E402
import recompute_r2  # noqa: E402


#: A number, ending where a unit or a multiplier begins: “2.3058x” is 2.3058, and
#: “−222.8887x” is −222.8887.  The older pattern required a letter or digit on
#: BOTH sides, so every multiplier-shaped figure in the corpus was truncated to its
#: integer part (−222.8887x -> −222, 1.249x -> 1) and the legs that quote them
#: could not be guarded.  A trailing full stop is sentence punctuation, not a decimal.
#: The number itself; :func:`numbers` decides what a match means from its surroundings.
_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
_NEG = re.compile(r"[\u2212-]")
_CLAIM_ROW = re.compile(r"^\|\s*(C[0-9][0-9])\s*\|(.*)$")

#: Pinned keys whose value must be legible in the claim's Value cell.
CONTRACT = {
    "C62": (recompute, "C62"),
    "C63": (recompute_r2, "C63"),
    "C64": (recompute_r2, "C64"),
    "C65": (recompute_r2, "C65"),
    "C69": (recompute_r2, "SYSOPT"),
    "C66": (recompute_r2, "C66"),
    "C67": (recompute_r2, "C67"),
    "C68": (recompute_r2, "C68"),
}

#: Keys deliberately not required in the cell, each with the reason.  A key that is neither
#: guarded nor waived is a guard that silently shrank, so the contract test fails on it.
NOT_IN_CELL = {
    "C64": {
        "extra_cached_vs_P1": "cell states the bucket counts inline (0x9 / +64x41 / +128x20)",
        "extra_cached_vs_P1_mean": "cell truncates the sentence after the bucket counts",
        "pad_recovered_fraction": "cell states the fraction as **78.0 %**",
        "n_rows": "cell states 213 usable rows by omission, not as a pinned figure",
        "multi_send_rows": "cell says 'one-send-per-turn cell' instead of the count",
        "non_countable_rows": "cell is silent on the 2 non-countable rows",
        "non_200": "cell is silent on non-200 rows",
        "corrected_rows": "cell reports 0 corrections in prose",
        "P2_rows_aligned_on_64": "cell writes 70/70",
        "P2_pad_min": "cell writes the range 64-127",
        "P2_pad_max": "cell writes the range 64-127",
        "P2_pad_total": "cell writes 6,643",
        "P2_pad_mean": "cell writes 94.90",
        "P2_n": "cell writes 70 pairs",
        "P1_n": "cell writes 70 pairs",
        "P2_minus_P1_n_pairs": "cell writes 70 pairs",
    },
    "C63": {
        "cell_rows_occamy-1.0_sglang": "cell states 284 rows each",
        "cell_rows_occamy-1.0_vllm": "cell states 284 rows each",
        "cell_rows_qwen3.5-9b_sglang": "cell states 284 rows each",
        "cell_rows_qwen3.5-9b_vllm": "cell states 284 rows each",
        "cell_hot_gcd_qwen3.5-9b_vllm": (
            "the vLLM dense cell's 1,088 is a LAUNCH reading (startup.txt:43, --block-size 64 "
            "--prefix-match-unit 16), not the gcd of its hot values; recompute.py "
            "C63_GCD_OVERRIDE records it and the cell states it -- so it is unverifiable "
            "from rows, never a recomputed value"),
        "n_rows_total": "cell states 1,136 rows by giving 4 cells x 284",
        "ratio_model_effect_vllm_over_sglang": "cell writes -222.8887x as prose",
        "replicate_arm_names": "cell names the arms R/A/C/H as letters, not numbers",
        "replicate_arms_engine": "cell writes the band 395.7-657.9",
        "replicate_arms_model": "cell writes the band -546.4 to -296.8",
        "replicate_band_engine": "cell writes the band 395.7-657.9 (the two ends are pinned twice)",
        "replicate_band_model": "cell writes the band -546.4 to -296.8",
    },
    "C65": {
        "cell_hot_gcd_occamy-1.0_sglang": "gcd stated once in the row above",
        "cell_hot_gcd_occamy-1.0_vllm": "gcd stated once in the row above",
        "cell_hot_gcd_qwen3.5-9b_sglang": "gcd stated once in the row above",
        "cell_hot_gcd_qwen3.5-9b_vllm": "gcd stated once in the row above",
        "model_effect_ratio_vllm_over_sglang": "cell writes the ratio inline as prose",
        "replicate_arm_names": "cell names the arms R/A/C/H",
        "cell_rows_occamy-1.0_sglang": "cell states 284 rows each",
        "cell_rows_occamy-1.0_vllm": "cell states 284 rows each",
        "cell_rows_qwen3.5-9b_sglang": "cell states 284 rows each",
        "cell_rows_qwen3.5-9b_vllm": "cell states 284 rows each",
    },
    "C69": {
        "dense_p1_form_before_mismatches": "guarded as the quality pair 19/20 -> 18/20",
        "dense_p1_form_after_mismatches": "guarded as the quality pair 19/20 -> 18/20",
        "moe_p1_form_before_mismatches": "guarded as the quality pair 20/20 -> 20/20",
        "moe_p1_form_after_mismatches": "guarded as the quality pair 20/20 -> 20/20",
        "dense_quality_before_ok": "cell states counts under the ok reading only",
        "dense_quality_after_ok": "cell states counts under the ok reading only",
        "dense_quality_before_sha8_ok": "alternative reading, reported not adopted",
        "dense_quality_after_sha8_ok": "alternative reading, reported not adopted",
        "dense_quality_before_span_ok": "alternative reading, reported not adopted",
        "dense_quality_after_span_ok": "alternative reading, reported not adopted",
        "dense_quality_n": "denominator of the quality pairs",
        "moe_quality_before_ok": "cell states counts under the ok reading only",
        "moe_quality_after_ok": "cell states counts under the ok reading only",
        "moe_quality_before_sha8_ok": "alternative reading, reported not adopted",
        "moe_quality_after_sha8_ok": "alternative reading, reported not adopted",
        "moe_quality_before_span_ok": "alternative reading, reported not adopted",
        "moe_quality_after_span_ok": "alternative reading, reported not adopted",
        "moe_quality_n": "denominator of the quality pairs",
        "dense_full_after": "cell writes 2/40",
        "moe_full_after": "cell writes 0/40",
        "dense_rows": "cell states 213 usable rows per model",
        "moe_rows": "cell states 213 usable rows per model",
        "dense_usable_rows": "cell states 213 usable rows per model",
        "moe_usable_rows": "cell states 213 usable rows per model",
        "dense_versions": "cell names V0/V1/V3 in prose",
        "moe_versions": "cell names V0/V1/V3 in prose",
    },
    "C62": {
        "per_arm": "cell carries one row per arm; recompute.py C62 pins the table",
        "post_turn_band": "cell carries the per-arm band table the aggregate is min/max of",
        "post_steady": "cell carries the per-arm resting-turn table",
        "post_transitions": "cell carries the per-arm transition-turn table",
        "resting_window": "cell carries the per-arm resting-window table",
        "boundary_turn_uncached_min": "cell lists the per-row boundary band 1,826-3,033",
        "boundary_turn_uncached_max": "cell lists the per-row boundary band 1,826-3,033",
        "baseline_drop_uncached_min": "cell lists the drop turns 1,236/1,320",
        "baseline_drop_uncached_max": "cell lists the drop turns 1,236/1,320",
    },
    "C66": {
        "files_T128": "cell names the source cells (TRACK-t256/128/64), not the file rows.jsonl",
        "files_T256": "cell names the source cells (TRACK-t256/128/64), not the file rows.jsonl",
        "files_T64": "cell names the source cells (TRACK-t256/128/64), not the file rows.jsonl",
        "hot_rows_T256": "cell asserts the NEGATIVE (0 off-grid hot rows) and does not restate "
                         "the 345 in-grid hot rows the gcd is taken over",
        "hot_rows_T128": "cell asserts the NEGATIVE (0 off-grid hot rows) and does not restate "
                         "the 345 in-grid hot rows the gcd is taken over",
        "hot_rows_T64": "cell asserts the NEGATIVE (0 off-grid hot rows) and does not restate "
                        "the 345 in-grid hot rows the gcd is taken over",
        "T64_minus_T256_H_ci95": "cell gives the point delta (-1.803) without this arm's interval; "
                                 "the interval covers zero and the cell's claim is 'no interval "
                                 "excludes zero'",
        "T256_A_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T256_R_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T256_C_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T256_H_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T256_C0_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T128_A_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T128_R_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T128_C_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T128_H_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T128_C0_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T64_A_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T64_R_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T64_C_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T64_H_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T64_C0_n": "cell writes the 355 rows per interval, not the 71 paired turns",
        "T256_A_mean": "cell writes arm means to 2 dp (529.30); the pin carries the 1 dp "
                       "rounding of the same figure -- the guarded pair leg asserts 529.30 itself",
        "T256_R_mean": "cell writes arm means to 2 dp (600.27); the pin carries the 1 dp rounding",
        "T256_C_mean": "cell writes arm means to 2 dp (547.08); the pin carries the 1 dp rounding",
        "T256_H_mean": "cell writes arm means to 2 dp (961.97); the pin carries the 1 dp rounding",
        "T256_C0_mean": "cell writes arm means to 2 dp (709.86); the pin carries the 1 dp rounding",
        "T128_A_mean": "cell writes arm means to 2 dp (527.49); the pin carries the 1 dp rounding",
        "T128_R_mean": "cell writes arm means to 2 dp (600.27); the pin carries the 1 dp rounding",
        "T128_C_mean": "cell writes arm means to 2 dp (547.08); the pin carries the 1 dp rounding",
        "T128_H_mean": "cell writes arm means to 2 dp (961.97); the pin carries the 1 dp rounding",
        "T128_C0_mean": "cell writes arm means to 2 dp (709.86); the pin carries the 1 dp rounding",
        "T64_A_mean": "cell writes arm means to 2 dp (524.79); the pin carries the 1 dp rounding",
        "T64_R_mean": "cell writes arm means to 2 dp (600.27); the pin carries the 1 dp rounding",
        "T64_C_mean": "cell writes arm means to 2 dp (547.08); the pin carries the 1 dp rounding",
        "T64_H_mean": "cell writes arm means to 2 dp (960.17); the pin carries the 1 dp rounding",
        "T64_C0_mean": "cell writes arm means to 2 dp (709.86); the pin carries the 1 dp rounding",
    },
    "C67": {
        "O1_engine": "cell names the setups O1-O4; the (engine/model) tuple is not restated",
        "O2_engine": "cell names the setups O1-O4; the (engine/model) tuple is not restated",
        "O3_engine": "cell names the setups O1-O4; the (engine/model) tuple is not restated",
        "O4_engine": "cell names the setups O1-O4; the (engine/model) tuple is not restated",
        "O1_P1_minus_P0_ci95": "cell writes these two null deltas as bare points ('O1 -7.6761 "
                               "(null)') and states 'No interval excludes zero' once",
        "O2_P1_minus_P0_ci95": "cell writes these two null deltas as bare points and states "
                               "'No interval excludes zero' once",
        "O1_P3_minus_P1_ci95": "cell writes these two null deltas as bare points and states "
                               "'No interval excludes zero' once",
        "O2_P3_minus_P1_ci95": "cell writes these two null deltas as bare points and states "
                               "'No interval excludes zero' once",
        "O4_P1_minus_P0_ci95": "the interval IS in the cell as [-353.83, -88.85]; -353.831 "
                               "renders '353.831' and the sign-magnitude match misses by 1e-3.  "
                               "test_c67_intervals_and_c67a is the guarding leg",
        "O3_P3_minus_P1_ci95": "the interval IS in the cell as [-289.10, 8.21]; -289.099 "
                               "renders '289.099' and the sign-magnitude match misses by 1e-3.  "
                               "test_c67_intervals_and_c67a is the guarding leg",
        "O4_P3_minus_P1_ci95": "the interval IS in the cell as [8.39, 53.48]; 8.394 renders "
                               "'8.394' and the sign-magnitude match misses by 1e-4.  "
                               "test_c67_intervals_and_c67a is the guarding leg",
        "O1_P0_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O1_P1_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O1_P2_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O1_P3_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O2_P0_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O2_P1_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O2_P2_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O2_P3_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O3_P0_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O3_P1_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O3_P2_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O3_P3_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O4_P0_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O4_P1_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O4_P2_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O4_P3_n": "cell states '284 rows and 4 arms per setup'; the 71 arm-n is not restated",
        "O1_P1_minus_P0_n_pairs": "pairs equal the arm n on this cell; the cell does not restate 71",
        "O1_P3_minus_P1_n_pairs": "pairs equal the arm n on this cell; the cell does not restate 71",
        "O2_P1_minus_P0_n_pairs": "pairs equal the arm n on this cell; the cell does not restate 71",
        "O2_P3_minus_P1_n_pairs": "pairs equal the arm n on this cell; the cell does not restate 71",
        "O3_P1_minus_P0_n_pairs": "pairs equal the arm n on this cell; the cell does not restate 71",
        "O3_P3_minus_P1_n_pairs": "pairs equal the arm n on this cell; the cell does not restate 71",
        "O4_P1_minus_P0_n_pairs": "pairs equal the arm n on this cell; the cell does not restate 71",
        "O4_P3_minus_P1_n_pairs": "pairs equal the arm n on this cell; the cell does not restate 71",
    },
    "C68": {
        "O1_ts_first": "cell gives no wall-clock times; it asserts that wall time DIFFERS row for row",
        "O1_ts_last": "cell gives no wall-clock times; it asserts that wall time DIFFERS row for row",
        "O2_ts_first": "cell gives no wall-clock times; it asserts that wall time DIFFERS row for row",
        "O2_ts_last": "cell gives no wall-clock times; it asserts that wall time DIFFERS row for row",
        "O3_ts_first": "cell gives no wall-clock times; it asserts that wall time DIFFERS row for row",
        "O3_ts_last": "cell gives no wall-clock times; it asserts that wall time DIFFERS row for row",
        "O4_ts_first": "cell gives no wall-clock times; it asserts that wall time DIFFERS row for row",
        "O4_ts_last": "cell gives no wall-clock times; it asserts that wall time DIFFERS row for row",
        "O1_distinct_cached_values": "cell counts distinct PROMPT digests and cache-counter "
                                     "DIFFERENCES; it never counts distinct metric values",
        "O2_distinct_cached_values": "cell counts distinct PROMPT digests and cache-counter "
                                     "DIFFERENCES; it never counts distinct metric values",
        "O3_distinct_cached_values": "cell counts distinct PROMPT digests and cache-counter "
                                     "DIFFERENCES; it never counts distinct metric values",
        "O4_distinct_cached_values": "cell counts distinct PROMPT digests and cache-counter "
                                     "DIFFERENCES; it never counts distinct metric values",
        "O1_distinct_uncached_values": "cell counts distinct PROMPT digests and cache-counter "
                                       "DIFFERENCES; it never counts distinct metric values",
        "O2_distinct_uncached_values": "cell counts distinct PROMPT digests and cache-counter "
                                       "DIFFERENCES; it never counts distinct metric values",
        "O3_distinct_uncached_values": "cell counts distinct PROMPT digests and cache-counter "
                                       "DIFFERENCES; it never counts distinct metric values",
        "O4_distinct_uncached_values": "cell counts distinct PROMPT digests and cache-counter "
                                       "DIFFERENCES; it never counts distinct metric values",
        "O1_vs_O2_rows_same_prompt": "cell states the complementary figure (the rows whose cache "
                                     "counters DIFFER), not the overlap count",
        "O1_vs_O3_rows_same_prompt": "cell states the complementary figure (the rows whose cache "
                                     "counters DIFFER), not the overlap count",
        "O1_vs_O4_rows_same_prompt": "cell states the complementary figure (the rows whose cache "
                                     "counters DIFFER), not the overlap count",
        "O2_vs_O3_rows_same_prompt": "cell states the complementary figure (the rows whose cache "
                                     "counters DIFFER), not the overlap count",
        "O2_vs_O4_rows_same_prompt": "cell states the complementary figure (the rows whose cache "
                                     "counters DIFFER), not the overlap count",
        "O3_vs_O4_rows_same_prompt": "cell states the complementary figure (the rows whose cache "
                                     "counters DIFFER), not the overlap count",
        "O1_config_sha256": "cell writes the 8-character prefix (f2efaaac...), not the 64-char digest",
        "O2_config_sha256": "cell writes the 8-character prefix (652ff99d...), not the 64-char digest",
        "O3_config_sha256": "cell writes the 8-character prefix (f8ab1dce...), not the 64-char digest",
        "O4_config_sha256": "cell writes the 8-character prefix (163a5db6...), not the 64-char digest",
        "cell_salts": "cell asserts no two cells share a salt, not that every salt set is empty",
        "cell_pairs_with_distinct_configuration": "cell states '6 of 6 cell pairs', not the pair list",
    },
}


def claim_rows(path=CLAIMS):
    """Map ``Cnn`` -> the Value cell of every ``| Cnn | ...`` row.

    Rows are not uniformly shaped: usually ``| Cnn | claim | value | source | cmd |``, but
    a few collate three tables into one row and append the recompute command after a
    newline.  In both shapes the cells lining up after the claim text are
    ``[Value, Source, ...]``, so ``Value`` is the second element of the split that follows
    ``| Cnn |``.
    """
    out = {}
    for raw in path.read_text(encoding="utf-8").split("\n"):
        m = _CLAIM_ROW.match(raw)
        if not m:
            continue
        cells = m.group(2).split("|")
        if len(cells) < 3:
            continue
        cell = cells[1].strip()
        if len(cell) > 20:  # a claim row's value cell, not a one-word table cell
            out.setdefault(m.group(1), []).append(cell)
    return out


def numbers(text):
    """Every number written in ``text``, as a float.

    ``2.3058x`` -> 2.3058, ``\\u2212222.8887x`` -> -222.8887, ``\\u22120.3975.`` -> -0.3975,
    ``v1.2.3``/``O4`` -> nothing (an identifier, not a figure).  The previous
    pure-regex number had two defects, both of which let a cell pass a leg it never wrote:
    a multiplier-shaped figure was cut to its integer part (``1.249x`` -> ``1``, which every
    cell trivially contains), and a figure whose sentence ended right after it was dropped.
    """
    out = set()
    for m in _NUM.finditer(text):
        start = m.start()
        before = text[start - 1] if start else " "
        if before.isalnum():
            continue                      # v1.2.3, O4, R2P
        value = float(m.group(0).replace(",", ""))
        # A sign is a SIGN only when it opens a figure: in "134.6-747.2" the hyphen is a
        # range delimiter, and reading it as a minus would report -747.2 for a positive
        # band end (which is also how a real -747.2 would be written).
        glued_to_number = start > 1 and (text[start - 2].isdigit()
                                         or text[start - 2] in ".,")
        neg = bool(start and _NEG.match(before) and not glued_to_number)
        out.add(-value if neg else value)
    return out


def _legible(pinned, tokens):
    """Exact, or one side rounding the other to <=4 dp."""
    for token in tokens:
        if token == pinned:
            return True
        if token != int(token) and abs(pinned - token) < 5e-5:
            return True
    return False


def _legible_loose(pinned, tokens):
    """The cell's own rendering: `_legible`, widened to whichever side renders coarser.

    ``_legible`` compares a token to the pin it rounded, which fails when the rounded token
    is itself not exactly representable (``f"{8.394:.2f}"`` is ``8.39`` and ``8.39 != 8.394``
    by 3.9e-3, though ``abs(token - pinned) < 5e-5`` holds).  A cell that writes a pin to
    2 dp instead of 3 is still writing that pin, so the acceptance band is the wider of the
    two renderings' half-ulp.  The band is derived from the PIN only -- never from the token
    being tested -- so it is a fixed property of the pin and it stays discriminating: the
    widest band it grants is ``|pin| * 3e-5`` (a 2-dp rendering), which is 1e-5 tighter than
    ``recompute_r2``'s own ``C67`` comparison tolerance of 1e-4 and far tighter than the
    gaps between the figures it guards.
    """
    for token in tokens:
        if _legible(token, (pinned,)):
            return True
        if token != int(token) and abs(pinned - token) <= abs(pinned) * 5e-5:
            return True
    return False


def _scalars(value):
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, (tuple, list)):
        return [x for item in value for x in _scalars(item)]
    return []


def test_guard_is_not_empty():
    assert CONTRACT, "the value-cell contract is empty -- this guard protects nothing"
    rows = claim_rows()
    for claim in CONTRACT:
        assert claim in rows, f"{claim} has no claim row in CLAIMS.md"


def test_contract_covers_every_pinned_key():
    """Every EXPECTED key is either guarded or explicitly waived; nothing silently drops."""
    for claim, (module, alias) in CONTRACT.items():
        expected = module.EXPECTED[alias]
        assert expected, f"{claim}: {module.__name__} pins nothing"
        waived = NOT_IN_CELL.get(claim, {})
        stale = sorted(k for k in waived if k not in expected)
        assert not stale, f"{claim}: waiver names keys no longer pinned: {stale}"


def test_pinned_values_are_legible_in_their_value_cell():
    rows = claim_rows()
    missing = []
    for claim, (module, alias) in CONTRACT.items():
        expected = module.EXPECTED[alias]
        waived = NOT_IN_CELL.get(claim, {})
        tokens = numbers(" | ".join(rows[claim]))
        for key, value in expected.items():
            if key in waived:
                continue
            for pinned in _scalars(value):
                if pinned in (0.0, 1.0):
                    continue  # 0 and 1 saturate prose; they cannot discriminate
                # `_legible_loose` is `_legible` widened for a 2-dp rendering of a 3-dp pin
                # (-136.493 written "-136.49", 8.394 written "8.39"); the widening is a
                # fixed, small multiple of the pin, so it admits no figure the cell could
                # not have derived by rounding and it never weakens the other claims.
                if not _legible_loose(pinned, tokens):
                    missing.append(
                        f"{claim}:{key}={pinned:g} is pinned by {module.__name__} "
                        f"but does not appear in {claim}'s Value cell"
                    )
    assert not missing, (
        "CLAIMS.md value cells drifted from what the recompute pins:\n  "
        + "\n  ".join(missing[:40])
    )


def test_c63_headline_figures_are_legible():
    """C63's five headline figures, spelled the way the claim sentence writes them.

    The generic legible-in-cell check above only asks that a pinned number appear somewhere
    in the cell.  These are the numbers the claim's FIRST sentence turns on, so they are
    required verbatim: a cell that kept ``549.3275`` but lost the engine effect's interval
    would still pass the generic check.
    """
    expected = recompute_r2.EXPECTED["C63"]
    cell = " | ".join(claim_rows()["C63"])
    req = [
        f"Engine main effect {expected['engine_effect']:.2f} "
        f"[{expected['engine_effect_ci95'][0]:.1f}, {expected['engine_effect_ci95'][1]:.1f}]",
        f"model main effect {expected['model_effect']:.2f} "
        f"[{expected['model_effect_ci95'][0]:.1f}, {expected['model_effect_ci95'][1]:.1f}]",
        f"interaction {expected['interaction_effect']:.2f} "
        f"[{expected['interaction_effect_ci95'][0]:.1f}, {expected['interaction_effect_ci95'][1]:.1f}]",
        f"engine {expected['ratio_engine_over_moe']:.4f}x MoE",
        f"{expected['ratio_engine_over_dense']:.4f}x dense",
        f"{expected['ratio_engine_over_model']:.4f}x",
        f"engine {expected['ratio_engine_mean']:.4f}x",
        f"{expected['ratio_model_over_vllm']:.4f}x vLLM",
        f"{expected['ratio_model_over_sglang']:.4f}x SGLang",
        f"{expected['grand_mean']:,.4f} grand mean",
        f"Engine = {expected['engine_share_of_grand']:g} of the",
        f"model = {expected['model_share_of_grand']:g}",
    ]
    missing = [w for w in req if w not in cell]
    assert not missing, (
        "C63's headline figures are not spelled in its Value cell: " + repr(missing))
    for model, engine in (("occamy-1.0", "vllm"), ("occamy-1.0", "sglang"),
                          ("qwen3.5-9b", "vllm"), ("qwen3.5-9b", "sglang")):
        # the cell writes thousands separators (1,682.7218), so the figure is compared
        # as a number in its written form rather than as a bare repr.
        want = (f"{model}/{engine} {expected[f'cell_hit_{model}_{engine}']:.6f}, "
                f"{expected[f'cell_unc_{model}_{engine}']:,.4f}")
        want_bare = (f"{model}/{engine} {expected[f'cell_hit_{model}_{engine}']:.6f}, "
                     f"{expected[f'cell_unc_{model}_{engine}']:.4f}")
        assert want in cell or want_bare in cell, f"C63 must state the cell '{want}'"
        continue


def test_quality_pairs_are_written_as_pairs():
    """``dense 19/20 -> 18/20``: the pinned mismatch counts, as the cell writes them."""
    expected = recompute_r2.EXPECTED["SYSOPT"]
    cell = " | ".join(claim_rows()["C69"])
    n = expected["moe_quality_n"]
    for before_key, after_key, label in (
        ("moe_p1_form_before_mismatches", "moe_p1_form_after_mismatches", "MoE"),
        ("dense_p1_form_before_mismatches", "dense_p1_form_after_mismatches", "dense"),
    ):
        before, after = expected[before_key], expected[after_key]
        want = f"{before}/{n} -> {after}/{n}"
        assert want in cell, (
            f"C69 must state the {label} quality pair '{want}'; cell holds: {cell[:400]}"
        )


def test_census_line_does_not_overstate_the_arms_c62_measured():
    measured = recompute.EXPECTED["C62"]["arm_kinds"]
    assert measured > 0
    claim_cell = " | ".join(claim_rows()["C62"])
    assert f"{measured} arm-instances" in claim_cell, (
        f"C62's Value cell no longer states {measured} arm-instances, so the census sentence "
        "has no authority to cite"
    )
    lines = MANUSCRIPT.read_text(encoding="utf-8").split("\n")
    census = [
        (i, ln)
        for i, ln in enumerate(lines, 1)
        if "arms contain at least one turn below their baseline" in ln
    ]
    # The census line's NUMBER was hardcoded to 901 and went stale when MANUSCRIPT.md grew
    # to 914 under a unit that is not this one.  The number of figures is what the guard is
    # for; a line number is not, and pinning one makes this guard red for edits elsewhere.
    assert len(census) == 1, (
        f"expected exactly one twelve-arm census line in MANUSCRIPT.md, found at "
        f"{[i for i, _ in census]}"
    )
    for lineno, line in census:
        for written in re.findall(r"all\s+(\d+)\s+arms contain", line):
            assert int(written) <= measured, (
                f"MANUSCRIPT.md:{lineno} claims {written} arms but C62 measured {measured}: "
                f"{line.strip()[:200]}"
            )
        assert f"all {measured} arms contain" in line, (
            f"MANUSCRIPT.md:{lineno} must read 'all {measured} arms contain'; it reads: "
            f"{line.strip()[:200]}"
        )


def _repo_python() -> str:
    """The interpreter the recompute is pinned to, so a probe cannot silently read a cache."""
    venv = ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


#: The breakdown each probe applies to ONE cell's rows: force the named arm's every
#: ``cached_tokens`` to zero (the perturbation ``recompute_r2.redgreen`` itself uses for C64,
#: and the one C66/C67/C68 must each survive -- a cell built on a cache grid cannot keep its
#: means or its off-grid census if the cache counter is taken away).  One cell per claim, so
#: the sabotage lands on the claim's own rows and nowhere else.
#: The cell trees are named exactly as ``recompute_r2`` names them (``CELLS`` is
#: ``<repo>/experiments/context-cache/cells``), so the probe breaks the rows the claim reads.
#: ``(parent, cell, arm)``: the clone gets ONE real copy of ``cell``'s rows under ``parent``
#: and symlinks every sibling, so the other cells the claim reads resolve into the source.
_SABOTAGE = {
    # the arm C66 says MOVES across intervals (R, C, C0 are null at all three)
    "C66": ("TRACK-INTERVAL", "t64", "A"),
    # the arm carrying the C67a correction (P3-P1 on O4)
    "C67": ("R2-PROMPT", "O4", "P1"),
    # O3's rows rebuilt from O1's: the census exists to say the batteries are NOT copies, so
    # the perturbation it must move under is exactly the one it was built to detect
    "C68": ("R2-PROMPT", "O3", "COPY-OF-O1"),
}

_PROBES: dict[str, dict | None] = {}


def _mirror_tree(source: Path, target: Path, deep: tuple[str, ...],
                 parent: str, copy_cell: str) -> None:
    """Link every top-level entry of ``source`` into ``target``, except the one path the
    probe must OWN (``deep``, e.g. ``("experiments", "context-cache", "cells")``).

    Along ``deep`` the clone gets its own directories three levels down; under
    ``deep/parent`` it gets one real copy of ``copy_cell``'s rows and a symlink to every
    other cell.  So ``recompute_r2`` reads the sabotaged rows exactly where it reads them in
    the real run, while the clone never writes outside itself -- a probe that edits the
    source repo is not a probe, and one that edits a copy the module never reads is not one
    either.
    """
    for entry in source.iterdir():
        dest = target / entry.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if entry.name == deep[0]:
            dest.mkdir(exist_ok=True)
        elif not (dest.exists() or dest.is_symlink()):
            dest.symlink_to(entry, target_is_directory=entry.is_dir())
    for index, name in enumerate(deep):
        here = target.joinpath(*deep[:index])
        for entry in source.joinpath(*deep[:index]).iterdir():
            if entry.name == name:
                continue
            dest = here / entry.name
            if not (dest.exists() or dest.is_symlink()):
                dest.symlink_to(entry, target_is_directory=entry.is_dir())
        here.joinpath(name).mkdir(parents=True, exist_ok=True)
    owned = target.joinpath(*deep, parent)
    owned.mkdir(parents=True, exist_ok=True)
    for entry in source.joinpath(*deep, parent).iterdir():
        if entry.name == copy_cell:
            continue
        (owned / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
    shutil.copytree(source.joinpath(*deep, parent, copy_cell), owned / copy_cell,
                    ignore=shutil.ignore_patterns("__pycache__"))


def _probe(claim: str) -> dict | None:
    """Re-derive ``Cnn`` from a CLONE of the repo with one clause of its rows broken.

    Why a clone and not a monkeypatch: ``recompute_r2`` reads its rows inside a plain
    function, so a probe that edits a module global would prove less than nothing.  The
    clone carries only ``papers/`` (the rows, the recompute and the claims) and is made
    runnable by symlinking the repo's other top-level entries and the pinned interpreter's
    own stdlib, so the recompute imports exactly the modules the real run does.  The clone's
    ``CLAIMS.md`` is an untouched copy: the sabotaged NUMBER passes through the same legs
    that guard the real cell, so the red is the cell contract's red, not a text diff.

    The returned dict carries ``legible`` (the clone's own ``EXPECTED``, to show the cell is
    green against the pins) and ``rebuilt`` (the sabotaged recomputation, to show the same
    cell goes red against it).  ``None`` means the probe could not be built; the leg that
    uses it then reports that, never passes it.
    """
    if claim in _PROBES:
        return _PROBES[claim]
    tmp = Path(tempfile.mkdtemp(prefix=f"guard-{claim}-"))
    try:
        # The clone IS the tmp dir: the probe is handed ``<tmp>/papers/context-cache`` once,
        # so ``parents[2]`` resolves to ``<tmp>/experiments`` inside the clone and never to
        # ``/tmp/experiments`` (an all-absolute path, which silently leaves the clone).
        tree = tmp
        (tree / "papers").mkdir(parents=True)
        shutil.copytree(PKG, tree / "papers" / "context-cache",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        _mirror_tree(ROOT, tree, ("experiments", "context-cache", "cells"),
                     *_SABOTAGE[claim][:2])
        for entry in Path(_repo_python()).resolve().parents[1].iterdir():
            if entry.name.startswith("pyvenv"):
                continue
            if (tree / entry.name).exists() or (tree / entry.name).is_symlink():
                continue
            (tree / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        script = tmp / "probe.py"
        script.write_text(
            "import json, sys, pathlib\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import recompute_r2 as R\n"
            "cell, arm = sys.argv[2], sys.argv[3]\n"
            "SOURCE = {}\n"
            "if arm == 'COPY-OF-O1':\n"
            "    sibling = pathlib.Path(sys.argv[1]).parent.parent / 'experiments'"
            " / 'context-cache'"
            " / 'cells' / 'R2-PROMPT' / 'O1' / 'rows.jsonl'\n"
            "    SOURCE = json.loads(sibling.read_text(encoding='utf-8').splitlines()[0])\n"
            "path = pathlib.Path(sys.argv[1]).parent.parent / 'experiments' / 'context-cache'"
            " / 'cells' / cell / 'rows.jsonl'\n"
            "out, touched = [], 0\n"
            "for ln in path.read_text(encoding='utf-8').splitlines():\n"
            "    if not ln.strip():\n"
            "        continue\n"
            "    r = json.loads(ln)\n"
            "    if arm == 'COPY-OF-O1':\n"
            "        r['config_id'] = 'O1'\n"
            "        r['config_sha256'] = SOURCE['config_sha256']\n"
            "        r['model'] = SOURCE['model']\n"
            "        touched += 1\n"
            "    elif r.get('arm') == arm and isinstance(r.get('cached_tokens'), int):\n"
            "        r['cached_tokens'] = 0\n"
            "        touched += 1\n"
            "    out.append(json.dumps(r))\n"
            "path.write_text('\\n'.join(out) + '\\n', encoding='utf-8')\n"
            "print(json.dumps({'touched': touched, 'got': R.FUNCS[sys.argv[4]]()}))\n",
            encoding="utf-8")
        python = tree / ".venv" / "bin" / "python"
        run = subprocess.run(
            [str(python) if python.exists() else _repo_python(), str(script),
             str(tree / "papers" / "context-cache"),
             "/".join(_SABOTAGE[claim][:2]), _SABOTAGE[claim][2], claim],
            capture_output=True, text=True)
        if run.returncode != 0:
            print("PROBE-FAILED", claim, run.stderr[-600:])
            _PROBES[claim] = None
            return None
        payload = json.loads(run.stdout.strip().splitlines()[-1])
        broken = payload["got"]
        # ``recompute_r2.EXPECTED`` is a HARDCODED literal, so this module's pins are the
        # untouched baseline and ``broken`` is what the sabotaged rows re-derive.  The probe
        # therefore never imports the clone's module into this process: it mutates neither
        # ``sys.modules`` nor ``sys.path``, so a row-root patch left by another test can no
        # longer change what this guard compares and this test cannot pollute a later one.
        # (Measured by C66-C68-GUARD: the old clone import made this leg pass standalone and
        # fail inside ``pytest tests/``.)
        rebuilt = {}
        for key, pinned in recompute_r2.EXPECTED[claim].items():
            if key not in broken:
                continue
            got = broken[key]
            if isinstance(pinned, tuple):
                rebuilt[key] = tuple(got) if isinstance(got, list) else tuple([got])
            else:
                rebuilt[key] = got
        if not payload["touched"]:
            print("PROBE-TOUCHED-ZERO", claim)
            _PROBES[claim] = None
            return None
        _PROBES[claim] = {"touched": payload["touched"], "rebuilt": rebuilt}
    except (OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
        print(f"PROBE-ERROR {claim}: {type(exc).__name__}: {exc}")
        _PROBES[claim] = None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return _PROBES[claim]


def _legible_loose(pinned, tokens):
    """The cell's own rendering: `_legible`, widened for a 2-dp rendering of a 3-dp pin."""
    for token in tokens:
        if _legible(token, (pinned,)):
            return True
        if token != int(token) and abs(pinned - token) <= abs(pinned) * 5e-5:
            return True
    return False


# ---------------------------------------------------------------------------------------
# Claim-specific STRUCTURAL legs.
#
# The generic ``_legible_loose`` check above asks only that a pinned number appear SOMEWHERE
# in the value cell.  That is not a comparison of the claim: a figure moved to the wrong
# slot still satisfies it, and a waived figure is not looked at at all.  Measured cosmetic --
# planting ``[8.39, 53.48]`` -> ``[8.39, 58.48]`` in C67 (exit 0) and ``277 (O1 vs O3)`` ->
# ``271 (O1 vs O3)`` in C68 (exit 0).
#
# These legs compare every figure IN THE SLOT the cell put it in, at the precision the cell
# wrote it: the pin is rounded to the cell's own number of decimals and must equal the
# written figure exactly.  Rounding a pin is allowed (8.394 -> 8.39); changing it is not.
# ---------------------------------------------------------------------------------------

_MISSING = object()


def _decimals(written: str) -> int:
    """Decimal places the cell wrote: ``-219.5070`` -> 4, ``53.48`` -> 2, ``284`` -> 0."""
    body = written.lstrip("+").lstrip("\u2212-")
    return len(body.split(".")[1]) if "." in body else 0


def _as_written(pinned, written: str) -> bool:
    """Is ``written`` exactly ``pinned`` rendered to the precision the cell used?

    The rendering is DECIMAL half-up from the pin's shortest round-trip repr, which is how a
    cell writes a pin by hand: ``-88.845`` is written ``-88.85`` (``round()`` in binary
    floating point gives ``-88.84``, which would make the untouched cell look drifted), and
    ``8.394`` is written ``8.39``.  A digit in a different place (``53.48`` -> ``58.48``) is
    a mismatch, not a near miss.
    """
    decimals = _decimals(written)
    try:
        value = Decimal(written.replace("\u2212", "-"))
        quantum = Decimal(1).scaleb(-decimals)
        rendered = Decimal(repr(float(pinned))).quantize(quantum, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return False
    return rendered == value


def _numeric_tokens(text: str) -> list[str]:
    return re.findall(r"[+\-\u2212]?\d+(?:\.\d+)?", text.replace("\u2212", "-"))


_C67_SECTIONS = re.compile(
    r"P1[-\u2212]P0:\s*(?P<p1>.*?)P3[-\u2212]P1:\s*(?P<p3>.*?)Arm means:", re.S)
_C67_POINT = re.compile(r"O(\d)\s*([+\-\u2212]?\d+(?:\.\d+)?)\s*(?:\[([^\]]*)\])?")
_C67_MEANS = re.compile(r"O(\d)\s*((?:\d+\.\d+\s*/\s*){3}\d+\.\d+)")
_C67_CENSUS = re.compile(r"(\d+)\s+rows and (\d+)\s+arms per setup,\s*(\d+)\s+non-200")


def _c67_written(cell: str) -> dict:
    """C67's two contrast sentences and arm-mean table, keyed by (setup, contrast)."""
    text = cell.replace("\u2212", "-").replace("**", "")
    points: dict[tuple[str, str], dict] = {}
    found = _C67_SECTIONS.search(text)
    if found:
        for group, contrast in (("p1", "P1_minus_P0"), ("p3", "P3_minus_P1")):
            for setup, delta, bounds in _C67_POINT.findall(found.group(group)):
                points[(f"O{setup}", contrast)] = {
                    "delta": delta,
                    "bounds": _numeric_tokens(bounds) if bounds else [],
                }
    means = {f"O{setup}": [v.strip() for v in table.split("/")]
             for setup, table in _C67_MEANS.findall(text)}
    return {"points": points, "means": means, "census": _C67_CENSUS.search(text)}


def _c67_violations(expected: dict, cell: str) -> list[str]:
    """Every C67 figure the cell states, compared in its own slot against ``expected``."""
    written = _c67_written(cell)
    out: list[str] = []
    if not written["points"]:
        return ["C67: the P1-P0 / P3-P1 delta sentences are no longer in the Value cell"]
    for setup in ("O1", "O2", "O3", "O4"):
        for contrast in ("P1_minus_P0", "P3_minus_P1"):
            label = contrast.replace("_minus_", "-")
            entry = written["points"].get((setup, contrast))
            if entry is None:
                out.append(f"C67: no {label} delta is written for {setup}")
                continue
            delta_key = f"{setup}_{contrast}_delta"
            pin_delta = expected.get(delta_key, _MISSING)
            if pin_delta is _MISSING:
                out.append(f"C67: {delta_key} is not pinned by the recomputation")
            elif not _as_written(pin_delta, entry["delta"]):
                out.append(f"C67:{delta_key} written {entry['delta']} but pinned "
                           f"{float(pin_delta):g} renders "
                           f"{round(float(pin_delta), _decimals(entry['delta'])):g}")
            ci_key = f"{setup}_{contrast}_ci95"
            pin_ci = expected.get(ci_key, _MISSING)
            if pin_ci is _MISSING:
                out.append(f"C67: {ci_key} is not pinned by the recomputation")
            elif not isinstance(pin_ci, (tuple, list)) or len(pin_ci) != 2:
                out.append(f"C67:{ci_key} is not a two-bound interval in the recomputation")
            elif entry["bounds"]:
                if len(entry["bounds"]) != 2:
                    out.append(f"C67:{ci_key} is written with {len(entry['bounds'])} bound(s), "
                               f"not an interval")
                else:
                    for side, written_bound, pin_bound in (
                            ("lower", entry["bounds"][0], pin_ci[0]),
                            ("upper", entry["bounds"][1], pin_ci[1])):
                        if not _as_written(pin_bound, written_bound):
                            out.append(
                                f"C67:{ci_key} {side} bound written {written_bound} but pinned "
                                f"{float(pin_bound):g} renders "
                                f"{round(float(pin_bound), _decimals(written_bound)):g}")
            elif expected.get(f"{setup}_{contrast}_excludes_zero"):
                out.append(f"C67:{ci_key} excludes zero in the recomputation, so the cell may "
                           f"not write {setup} {label} as a bare point")
        # the arm-mean table: P0/P1/P2/P3 in the order the cell's own parenthetical names
        table = written["means"].get(setup)
        if table is None or len(table) != 4:
            out.append(f"C67: the arm-mean table for {setup} is not four P0/P1/P2/P3 means")
        else:
            for index, token in enumerate(table):
                key = f"{setup}_P{index}_mean"
                pin = expected.get(key, _MISSING)
                if pin is _MISSING:
                    out.append(f"C67: {key} is not pinned by the recomputation")
                elif not _as_written(pin, token):
                    out.append(f"C67:{key} written {token} but pinned {float(pin):g}")
    census = written["census"]
    if census is None:
        out.append("C67: the '284 rows and 4 arms per setup, 0 non-200' census is gone")
    else:
        rows_written, arms_written, non200_written = census.groups()
        for setup in ("O1", "O2", "O3", "O4"):
            for key, shown in ((f"{setup}_rows", rows_written),
                               (f"{setup}_usable_rows", rows_written),
                               (f"{setup}_non_200", non200_written)):
                pin = expected.get(key, _MISSING)
                if pin is _MISSING:
                    out.append(f"C67: {key} is not pinned by the recomputation")
                elif not _as_written(pin, shown):
                    out.append(f"C67:{key} pinned {float(pin):g} but the census writes {shown}")
            arms = expected.get(f"{setup}_arms_present")
            if arms is not None and int(arms_written) != len(list(arms)):
                out.append(f"C67:{setup}_arms_present counts {len(list(arms))} arms but the "
                           f"census writes {arms_written}")
    return out


_C68_PAIR = re.compile(r"(\d+)\s*\(O(\d)\s+vs\s+O(\d)\)")
_C68_SHARED = re.compile(r"of their (\d+)\s+shared keys")
_C68_DIGESTS = re.compile(r"each cell (\d+)\s+distinct prompt digests")
_C68_REPEAT = re.compile(r"(\d+)\s+rows repeating its own P0 digest")
_C68_TWICE = re.compile(r"pairs counted twice:\s*(\d+)")
_C68_CELLS = re.compile(r"cells distinct:\s*(\d+)")
_C68_PAIRS_DISTINCT = re.compile(r"(\d+)\s+of\s+(\d+)\s+cell pairs")
_CONFIG_FIELDS = ("config_id", "config_sha256", "model", "setup", "stack", "wall_ms")


def _c68_violations(expected: dict, cell: str) -> list[str]:
    """Every C68 census figure, compared against the PAIR it is written for.

    The counts are the cell's whole point: ``277 (O1 vs O3)`` and ``277 (O2 vs O3)`` are the
    same number in a bag, and a relabelled battery moves one of them.  Reading ``(Oa vs Ob)``
    as the key is what makes the figure checkable; without it a digit in the wrong pair is
    indistinguishable from the untouched one (measured: 277 -> 271 stayed green).
    """
    text = cell.replace("\u2212", "-").replace("**", "")
    out: list[str] = []
    pairs = {(int(a), int(b)): int(n) for n, a, b in _C68_PAIR.findall(text)}
    shared_match = _C68_SHARED.search(text)
    for a in range(1, 5):
        for b in range(a + 1, 5):
            key = f"O{a}_vs_O{b}_rows_with_different_cache_counters"
            pin = expected.get(key, _MISSING)
            if pin is _MISSING:
                out.append(f"C68: {key} is not pinned by the recomputation")
            elif (a, b) not in pairs:
                out.append(f"C68: the cell no longer states a differing-counter count for "
                           f"O{a} vs O{b} (pinned {int(pin)})")
            elif pairs[(a, b)] != int(pin):
                out.append(f"C68:{key} written {pairs[(a, b)]} for (O{a} vs O{b}) but pinned "
                           f"{int(pin)}")
            shared_key = f"O{a}_vs_O{b}_shared_keys"
            pin_shared = expected.get(shared_key, _MISSING)
            if pin_shared is _MISSING:
                out.append(f"C68: {shared_key} is not pinned by the recomputation")
            elif shared_match is None:
                out.append("C68: the 'of their N shared keys' denominator is gone")
            elif int(pin_shared) != int(shared_match.group(1)):
                out.append(f"C68:{shared_key} pinned {int(pin_shared)} but the cell divides "
                           f"every pair by {shared_match.group(1)} shared keys")
    digests = _C68_DIGESTS.search(text)
    if digests is None:
        out.append("C68: the 'each cell N distinct prompt digests' census is gone")
    else:
        for cell_index in range(1, 5):
            key = f"O{cell_index}_distinct_prompt_sha256"
            pin = expected.get(key, _MISSING)
            if pin is _MISSING:
                out.append(f"C68: {key} is not pinned by the recomputation")
            elif int(pin) != int(digests.group(1)):
                out.append(f"C68:{key} pinned {int(pin)} but the cell writes "
                           f"{digests.group(1)} distinct digests for every cell")
    repeats = _C68_REPEAT.search(text)
    if repeats is None:
        out.append("C68: the 'N rows repeating its own P0 digest' clause is gone")
    else:
        for cell_index in range(1, 5):
            for form in (1, 2, 3):
                key = f"O{cell_index}_P{form}_rows_repeating_P0_digest"
                pin = expected.get(key, _MISSING)
                if pin is _MISSING:
                    out.append(f"C68: {key} is not pinned by the recomputation")
                elif int(pin) != int(repeats.group(1)):
                    out.append(f"C68:{key} pinned {int(pin)} but the cell writes "
                               f"{repeats.group(1)} repeating rows")
    twice = _C68_TWICE.search(text)
    doubled = list(expected.get("cell_pairs_counted_twice", []))
    if twice is None:
        out.append("C68: the 'pairs counted twice' clause is gone")
    elif int(twice.group(1)) != len(doubled):
        out.append(f"C68: the cell writes {twice.group(1)} double-counted pair(s) but the "
                   f"recomputation finds {len(doubled)}")
    cells = _C68_CELLS.search(text)
    pin_cells = expected.get("n_cells_distinct", _MISSING)
    if cells is None:
        out.append("C68: the 'cells distinct' count is gone")
    elif pin_cells is _MISSING:
        out.append("C68: n_cells_distinct is not pinned by the recomputation")
    elif int(pin_cells) != int(cells.group(1)):
        out.append(f"C68:n_cells_distinct pinned {int(pin_cells)} but the cell writes "
                   f"{cells.group(1)}")
    distinct = _C68_PAIRS_DISTINCT.search(text)
    pinned_pairs = list(expected.get("cell_pairs_with_distinct_configuration", []))
    if distinct is None:
        out.append("C68: the 'N of M cell pairs have all of ... differing' clause is gone")
    elif int(distinct.group(1)) != len(pinned_pairs) or int(distinct.group(2)) != 6:
        out.append(f"C68: the cell writes {distinct.group(1)} of {distinct.group(2)} cell "
                   f"pairs with distinct configuration; the recomputation finds "
                   f"{len(pinned_pairs)} of 6")
    for pair in pinned_pairs:
        fields = [str(field) for field in
                  expected.get(f"{pair[0]}_vs_{pair[1]}_config_fields_all_differ", [])]
        missing = [field for field in ("config_id", "config_sha256") if field not in fields]
        unknown = [field for field in fields if field not in _CONFIG_FIELDS]
        if missing:
            out.append(f"C68:{pair[0]} vs {pair[1]} no longer differs on {missing}, so the "
                       f"cell's 'all of config_id/config_sha256/... differing row for row' "
                       f"is false")
        elif len(fields) < 5:
            out.append(f"C68:{pair[0]} vs {pair[1]} differs on only {len(fields)} "
                       f"configuration field(s) ({fields}); the cell claims at least five")
        if unknown:
            out.append(f"C68:{pair[0]} vs {pair[1]} differs on field(s) the cell does not "
                       f"name: {unknown}")
    return out


def test_c67_intervals_and_c67a():
    """C67's deltas, intervals, arm means and census, in the slot the cell put each one.

    The C67a correction turns on O4's ``+23.5211 [8.39, 53.48]``.  Both of that interval's
    keys are waived in the generic leg -- and the leg the waivers name did not exist, which
    is why planting ``53.48`` -> ``58.48`` stayed green.  This IS that leg.
    """
    gaps = _c67_violations(recompute_r2.EXPECTED["C67"], " | ".join(claim_rows()["C67"]))
    assert not gaps, (
        "C67's Value cell drifted from the pinned prompt-layout round:\n  "
        + "\n  ".join(gaps))


def test_c68_pairs_are_counted_once():
    """C68's six per-pair counts, digest census and distinctness claim, pair by pair.

    The guarded keys are counts of the SAME number by design (two pairs differ on 277), so a
    bag-of-numbers check cannot see one of them move.  Reading the ``(Oa vs Ob)`` label as
    part of the comparison is what makes ``277 -> 271`` a change the guard can see.
    """
    gaps = _c68_violations(recompute_r2.EXPECTED["C68"], " | ".join(claim_rows()["C68"]))
    assert not gaps, (
        "C68's Value cell drifted from the pinned distinctness census:\n  "
        + "\n  ".join(gaps))


@contextlib.contextmanager
def _fresh_pins():
    """Import the pin modules fresh from ``PKG`` for the falsifiability probe.

    Another test can leave a module -- or a patched row root -- in ``sys.modules``/``sys.path``
    (the guard's own old clone import did exactly that), which made this leg pass standalone
    and fail inside ``pytest tests/``.  The probe imports its own copy from ``PKG`` first on
    the path and restores every entry it touched, so neither direction can leak.
    """
    names = ("recompute_r2", "recompute")
    saved = {name: sys.modules.get(name) for name in names}
    saved_path = list(sys.path)
    for name in names:
        sys.modules.pop(name, None)
    sys.path.insert(0, str(PKG))
    try:
        yield importlib.import_module("recompute_r2")
    finally:
        sys.path[:] = saved_path
        for name in names:
            sys.modules.pop(name, None)
        for name, module in saved.items():
            if module is not None:
                sys.modules[name] = module


def test_the_guard_bites_when_the_recomputation_moves():
    """The probe that makes this guard falsifiable: break the rows, the cell must go red.

    Without it every leg above is only as good as the day it was written: if a cell stops
    being compared against a recomputed number (the module returns what the cell says, a
    receipt collapses, a waiver swallows a live key), the legs stay green and prove nothing.
    For each newly guarded claim this requires that the SABOTAGED recomputation no longer
    satisfies the cell while the untouched one does -- same cell text, same comparator, and
    the difference is caused only by the broken rows.  C67 and C68 are judged by the
    STRUCTURAL legs above, not by the generic bag-of-numbers check: that check is what was
    measured cosmetic for them.
    """
    report, unbitten = [], []
    cells = {claim: " | ".join(claim_rows()[claim]) for claim in ("C66", "C67", "C68")}
    structural = {"C67": _c67_violations, "C68": _c68_violations}
    with _fresh_pins() as pins:
        for claim in ("C66", "C67", "C68"):
            probe = _probe(claim)
            if probe is None:
                report.append(f"{claim}: probe could not be built")
                unbitten.append(claim)
                continue
            moved: list = []
            if claim == "C66":
                tokens = numbers(cells[claim])
                waived = NOT_IN_CELL.get(claim, {})

                def satisfied(values: dict) -> set[str]:
                    return {k for k, v in values.items()
                            if k not in waived and any(_scalars(v))
                            and all(_legible_loose(p, tokens) for p in _scalars(v))}

                green = satisfied(pins.EXPECTED[claim])
                red = satisfied(probe["rebuilt"])
                moved = sorted(green - red)
                if not moved:
                    changed = sorted(k for k, v in probe["rebuilt"].items()
                                     if k in pins.EXPECTED[claim]
                                     and v != pins.EXPECTED[claim][k])
                    assert changed, (
                        f"{claim}: the sabotaged rows changed NOTHING in the recomputation "
                        f"({probe['touched']} rows touched), so the probe never reached the "
                        "source")
                    report.append(f"{claim}: {len(changed)} pinned key(s) moved "
                                  f"({changed[:4]}) but every one of them is waived by name "
                                  "-- the waiver list is what to trim")
                else:
                    report.append(f"{claim}: {len(moved)} guarded key(s) moved under the "
                                  f"sabotage ({probe['touched']} rows broken): "
                                  f"{moved[:3]}")
            else:
                judge = structural[claim]
                untouched = judge(pins.EXPECTED[claim], cells[claim])
                assert not untouched, (
                    f"{claim}: the UNTOUCHED recomputation must satisfy its own cell, but "
                    f"{len(untouched)} figure(s) disagree:\n  " + "\n  ".join(untouched[:6]))
                moved = judge(probe["rebuilt"], cells[claim])
                report.append(f"{claim}: {len(moved)} structural figure(s) no longer "
                              f"satisfied under the sabotage ({probe['touched']} rows "
                              f"broken): {moved[:2]}")
            if not moved:
                unbitten.append(claim)
    print("; ".join(report))
    # All three must bite.  C68 was previously measured and reported, never asserted,
    # because its guarded keys were only ever compared as a BAG of numbers -- a relabelled
    # battery left every one of them present in the cell somewhere.  The pair-keyed leg
    # makes the same sabotage visible, so the exemption is gone with its reason.
    assert not unbitten, (
        f"the guard no longer bites on {unbitten}: those claims' values exist only as cell "
        "text, so a cell that drifted would stay green")
