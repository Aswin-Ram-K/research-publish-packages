# ARMS-PARITY-WITHDRAW

**Objective.** Close the loop `CACHED-AUDIT` left open: mark `ARMS-PARITY`'s verdict **withdrawn** so its
falsified conclusion and its *inverted* prescription cannot be read as live, and check whether any published
surface still states the falsified figures. Offline; **0 live requests**.

**Card derived from, not given.** This card's board prompt named the unit and required a handoff stub; it did
not state an objective. The objective was taken from `orchestration/handoffs/CACHED-AUDIT.json`
`next_unit_hint` — *"The ARMS-PARITY verdict in `state/logs/arms-parity.json` is falsified by
GROUND-TRUTH-PROMPT; a unit should mark it withdrawn and check whether `papers/context-cache/CLAIMS.md` still
cites A-R…"*. Recorded as an assumption, not presented as an instruction.

**Bound.** 25 tool calls stated; **actual 46 (+21 over)** — disclosed rather than quietly re-based: one
annotation script failed on an unterminated string and was re-run, and the corpus red proof was executed
twice (once after the CLI path-tolerance fix). No change of scope; the overrun is mechanical. **Writes.** `state/logs/arms-parity.json`, `state/logs/arms-parity-withdraw.json`,
`orchestration/units/ARMS-PARITY.md`, `orchestration/handoffs/ARMS-PARITY.json`, this card,
`orchestration/handoffs/ARMS-PARITY-WITHDRAW.json`, `tools/audit/arms_parity_status.py`,
`tests/test_arms_parity_status.py`. No `cells/**` data touched; no published surface rewritten (none carried
the figure).

## What is withdrawn

`ARMS-PARITY` held that PROMPT-O1's arm-R `cached_tokens` were a `(prompt_tokens, cached_tokens)` dedupe
artefact, that `R = 583.14` was therefore corrupt, and that the publishable figure was
**A − R = +133.3 / +138.5 ("A costlier, pointer layout HELPS")**. It prescribed withdrawing `-53.8`.

Falsified three ways, none of them new measurements by this unit:

| Falsifier | Evidence |
|---|---|
| `GROUND-TRUTH-R` | fresh arm-R re-measurement within **−0.08 %** of the published value |
| `GROUND-TRUTH-PROMPT` | fresh salt `63564242b54d8609`: **589.2029** uncached/turn, n=69, 0 non-200 → **+1.04 %** vs restored 583.14, **+50.51 %** vs repaired 391.48 |
| `CACHED-AUDIT` | the duplicate-value signature fires **37/69** on that fresh ground truth → not discriminating; the only impossible corpus is the repair (**40** cached values off the 64-token grid, gcd 1) |

**The prescription is inverted.** The standing figure is **A − R = −53.8451 [−96.6197, −10.4085]**
(*A cheaper*); `+133.3` / `+138.5` are not publishable. Only the unit's *renderer* observation survives (both
cells import the same renderer, same two arms, salt-only difference).

## What was done

1. `state/logs/arms-parity.json` — `status: WITHDRAWN`, a `withdrawn` block naming the falsifiers and the
   inversion, and `verdict_status`. The original `verdict`, `per_cell` and `evidence` are **preserved
   verbatim**; only the two actively misleading strings were prefixed, with their pre-withdrawal text kept
   under `corrected_headline.as_recorded`. Nothing deleted.
2. `state/logs/arms-parity-withdraw.json` — the withdrawal record: falsified figures with their sites, the
   standing figure and its corpus digest, the sweep of published surfaces, and the guard's red/green lines.
3. `orchestration/units/ARMS-PARITY.md` — withdrawal banner above the original card (body kept).
4. `orchestration/handoffs/ARMS-PARITY.json` — `withdrawn` block; `next_unit_hint` replaced (its original
   text is kept inside the block, because it told the reader to publish `+133.3`).
5. **Guard** `tools/audit/arms_parity_status.py` + `tests/test_arms_parity_status.py` (C1 record, C2 corpus,
   C3 basis digest, C4 artefact, C5 claim surfaces).

## Sweep result (this is the useful negative)

**No published surface ever carried the falsified figure.** 31 claim-bearing surfaces scanned
(`papers/context-cache/*.md` 9, `docs/*.md`, `submission-kit/**/*.md`): **0 hits** for `+133.3`, `+138.5`,
`+138.68`, `+137.82`, "pointer layout helps", "bookkeeping artifact". The `+133.3` premise never reached the
paper or a packaged preprint, so the withdrawal is a **record-integrity** action, not a manuscript erratum.
`orchestration/VERDICTS.md` never held an ARMS-PARITY verdict entry, so there was nothing to withdraw there.

`state/logs/R2-P1-O1-progress.log:18` still states `A-R=+133.32` as an ACCEPTED line. It is an append-only run
log and was **not** edited — a log that can be rewritten is not a log; the withdrawal record supersedes it.

## Red → green

```
# RED — before the mark was written
ARMS-PARITY WITHDRAWAL GUARD FAIL  surfaces=31 standing A-R=-53.8451
  C1_record: 3 problem(s)
  ! state/logs/arms-parity.json: status='<absent>', expected 'WITHDRAWN' …
  ! state/logs/arms-parity-withdraw.json: missing withdrawal record                       [exit=1]

# GREEN — after
ARMS-PARITY WITHDRAWAL GUARD PASS  surfaces=31 standing A-R=-53.8451
  C1_record: ok   C2_corpus: ok   C5_surfaces: ok                                        [exit=0]

# RED — the re-apply-the-repair mutation (repaired corpus swapped in as rows.jsonl)
ARMS-PARITY WITHDRAWAL GUARD FAIL  C2_corpus: 6 problem(s)
  ! …/rows.jsonl: A - R = +137.8169 != -53.8451 [positive (ARMS-PARITY's falsified sign)]
  ! …/rows.jsonl: 40 cached_tokens off the 64-token grid (e.g. ('R', 5, 1409))           [exit=1]
```

`tests/test_arms_parity_status.py` — **10 passed** (green on disk, plus four independent red fixtures:
un-marked record, altered standing figure, repaired corpus swapped in, surface resurrecting `+133.3`, and the
allow-case where a surface quotes it *and* marks it withdrawn).

## Note on a pre-existing red (not this unit's)

`tests/test_orchestration_handoffs.py::test_no_new_contract_key_gaps` fails on `R2-A2`, `R2-A3`, `R2-B2`,
`R2-C`, `R2-SGL-CAP`, `V-R2VLLM-TRIAGE`, `VLLM-CELL` — files dated 2026-10-23 20:1x, i.e. **before** this
unit, with gaps against the frozen baseline. Neither this unit's handoff nor `ARMS-PARITY.json` appears in
that list (12 other tests in the file pass). Left alone: the baseline is not in this unit's write paths.

**Live requests: 0.** No endpoint contacted, no lock held, no GX10 access, `cells/**` unmodified.
