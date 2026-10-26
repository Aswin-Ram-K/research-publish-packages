# CACHED-AUDIT — detector for duplicated / stale `cached_tokens` credit

**Purpose.** Decide whether the ARMS-PARITY "PROMPT-O1 arm R is corrupt" claim is real, and
build a detector that can tell a cache plateau from a corrupted duplicate. Offline; 0 requests.

**Signature chosen.** Candidate (c), quantum-relative: `gap = prompt - cached`, `base = p25(gap)`,
`q = median positive advance of cached`; fires when `base + 0.9q <= gap <= base + 1.6q`, the
prompt grew, and the gap returns to `<= base + 0.5q` within 3 credit rows (transient, not
saturation). (a) 2-cycle fires on 0 rows of the bad file; (b) fires on 33-34 rows of a clean control.

**Finding — the card's premise is stale.** `rows.jsonl` is byte-identical to
`rows.pre-correction.jsonl` (sha256 `dc0774d8…`): RESTORE-O1 restored it at 03:03 after the
repair was falsified. "Fires on pre-correction" and "silent on rows.jsonl" cannot both hold.

**Finding — the signature is not discriminating.** It fires 39/71 on pre-correction, 0/71 on
R2-P1-O1 (as the card requires), but also 37/69 on the fresh independent GROUND-TRUTH-PROMPT
(mean 589.20) and 39/71 on PROMPT-O2-EXTRA and R2-P1-O2. The 64-block stall-then-catch-up
rhythm is normal cache physics, so pattern fires are never verdict-bearing.

**Verdict.** The only physically impossible artefact is `rows.repaired-DO-NOT-USE.jsonl`:
no consistent cache quantum (arm quantum = None), 40 cached values off the 64 grid, and each
one equals `prompt − R2-P1-O1's gap` turn for turn — arithmetic, not a measurement.

**Artifacts.** `tools/audit/cached_dedupe.py` (`--json`), `tests/test_cached_dedupe.py`,
`state/logs/cached-dedupe-audit.json`, this card, `orchestration/handoffs/CACHED-AUDIT.json`.

**Write paths.** Only the five above. `cells/**` and `papers/**` untouched.
