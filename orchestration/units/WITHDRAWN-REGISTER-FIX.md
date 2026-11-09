# UNIT `WITHDRAWN-REGISTER-FIX` — the guard fires on withdrawn figures, not on correct ones

**Objective.** Narrow register entry `WI-011`'s quote so the guard stops firing on citable p50s
in the 198.7 ms range while still firing on the withdrawn prefix-cache claim; add an opt-in
`--strict` paragraph window for the published latency pages; audit the register for any other
quote short enough to fire on a correct number.

**Precondition read.** `WITHDRAWN-SCREEN` (`4cddec07`/`22052dfc`) measured 131 files, 7 with
hits, 2 corrected, and named this defect: *"WI-011's quote is the bare 3-char string `98.7`, so
the guard fires on every citable p50 in the 198.7 ms range (198.72, 198.7230, 198.74). It fired
on a correct number in 4 documents and on 6 lines of `docs/LATENCY-REPORT.md`."*

**Change 1 — the quote.** `experiments/ptr-engine/measure/WITHDRAWN.json` `WI-011.quote`:
`"98.7"` → `"98.7 % prefix"`, plus a `quote_note` recording why (the withdrawn claim is the
prefix-cache *mechanism*; measured share 0.871157, not 0.987). Six inline
`WI-011 guard note` HTML comments in `docs/LATENCY-REPORT.md` (:51, :90, :147, :153, :266, :313)
and four `no_correction_needed` rows in `WITHDRAWN-SCREEN.json` (`docs/LATENCY-ERA-CENSUS.md:123`,
`docs/ROW-MODEL.md:111`, `docs/TTFT-DEFINITION.md:59`, `docs/VERBOSITY.md:52`) were **removed** —
they existed only to silence the false positive. No withdrawn figure was deleted from any page.

**Change 2 — `--strict`.** `withdrawn_index.py`: `corrected(..., strict=False)` and
`paragraph_bounds()`; in strict mode the correction must sit in the enclosing blank-line-delimited
paragraph. Wired through `withdrawn_screen.py` `--file/--scan/--check`. Default mode calls the
same 400-character window as before and is byte-identical.

**Tests (13 in `experiments/ptr-engine/longrun/tests/test_withdrawn_screen.py`, 13 passed).**
The five the card requires:

| test | red (quoted) | green |
|---|---|---|
| `test_correct_p50_no_longer_fires` | old quote `98.7`: `WITHDRAWN WI-011 line 3: 98.7` exit 1 | narrowed quote: `CLEAN p50.md ... window=400` exit 0 |
| `test_real_cache_share_still_fires` | — | claim paragraph: `WITHDRAWN WI-011 line 3: 98.7 % prefix` exit 1 |
| `test_wi004_stands_remnant_fires_under_strict` | default window: `CLEAN reissue.md` exit 0 | `--strict`: `WITHDRAWN WI-004 line 6: 318.14` exit 1 |
| `test_non_strict_is_byte_identical` | — | `--check` exit 0; recorded 134-file count not dropped; both corrected docs clean; 0 artifact rows |
| `test_register_self_test` | — | `self-test: 15 entries, 0 problem(s)` exit 0 |

**Short-quote audit (all 15 entries, whole corpus, 135 files).** Fragments of a longer numeric
token: **0** for every entry. Entries under 5 characters, flagged not changed:

| entry | quote | len | hits | why it is not a defect |
|---|---|---:|---:|---|
| `WI-001` | `≈466` | 4 | 8 | every hit is a citation of the withdrawn request count; no longer-number fragment |
| `WI-006` | `217k` | 4 | 10 | every hit is the withdrawn endpoint claim; no longer-number fragment |
| `WI-014` | `3/27` | 4 | 9 | a ratio, not a substring of a citable value |

No second entry is proven to fire on a correct number in this corpus, so only `WI-011` was fixed.

**Observed, not caused.** The screened surface grew 131 → 135 while this card ran (later cards
added `docs/COLD-START-PROBE.md` and others), and `docs/REQUEST-LEDGER.md:145` (owned by another
card) was corrected by its owner, so it no longer trips. The frozen record now pins 135 scanned,
`corrected` 3 rows, `reported_only` 1 row (`docs/COLD-START-PROBE.md`, owned elsewhere).

**Known limit (stated, not hidden).** `--strict` does not flag the live `docs/LATENCY-REPORT.md:45`
"**stands**" sentence, because that paragraph's own closing clause reads "the **withdrawn** reading
is the one to quote" — an in-paragraph marker, which is exactly what strict demands. The strict
test proves the window hole closes for the shape where the stale sentence sits alone in its
paragraph (`/tmp` fixture: default exit 0, `--strict` exit 1).

**Hard bound.** 26 tool calls; used 20. **Containment.** Offline: 0 inference requests, 0 sockets,
0 network calls. Never edited `docs/REQUEST-LEDGER.md`, rows/grades, `cell.py`, `spawn_record.py`,
`exit_codes.py`, or a published latency/pv table's numbers.
