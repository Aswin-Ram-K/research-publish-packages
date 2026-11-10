# Findings Ledger — Serving × Context Programme

One row per finding so the two programmes (Consonance and the context×serving experiment) stop telling two stories. Priced in **billed** tokens from the server's own cache report, never in payload size.

Rules:
- A row may not cite a live path for a value that changes — pin the digest instead.
- ABSENT ≠ 0
- DERIVED ≠ MEASURED
- No cross-build comparison.

| Finding | Number | Units | Source | Generation | Replicates on :8012 / :8014 | Status |
|---|---|---|---|---|---|---|
| Masking past eviction | 12/48 on :8012 (TX-02, all 12 at d=2); 8/48 on :8014 (TX-03, all 8 at d=2) (corrected from "0/48 on both stacks" — see RESULTS-TX02-CELL1.md line 20 and RESULTS-STACK-8014.md line 24) | score out of 48 checkpoints | `RESULTS-TX02-CELL1.md` (line 20: masking rep 1 12/48, d=2 12/12, d=8/20/32 0/12 each; line 82 boundary statement); `RESULTS-STACK-8014.md` (line 24: TX-03 masking r1 8/48) | TX-02 cell 1; TX-03 stack check | :8012 masking 12/48 (TX-02, line 20); :8014 masking 8/48 (TX-03, line 24) | VERIFIED (masking scores 12/48 on :8012 and 8/48 on :8014, both entirely from the d=2 bucket; "0/48 on both stacks" was unsupported) |
| Bounded fetch, single-fact recall | 41/48 (`:8012`), 42/48 (`:8014`) | score out of 48 checkpoints | `RESULTS-TX02-CELL1.md`, `RESULTS-STACK-8014.md` (line 38) | TX-03 | :8012 41/48; :8014 42/48 | VERIFIED (`RESULTS-STACK-8014.md:38` and `:61`) |
| Bounded fetch, aggregation | 4/48 (`:8012`), 0/48 with 243 fetch calls (`:8014`) | score out of 48 checkpoints; fetch calls | `RESULTS-KINDS-2-agg-abs.md` (line 35: 0/48 and 4/48; line 112 activation gate) | TX-AGG | :8012 4/48; :8014 0/48 (243 calls, line 26 of STACK-8014) | VERIFIED (`RESULTS-KINDS-2-agg-abs.md:35`; `RESULTS-STACK-8014.md:26`) |
| Bounded fetch, two-fact chain | 9/48 both stacks | score out of 48 checkpoints | `RESULTS-KINDS-2-agg-abs.md`, `RESULTS-STACK-8014.md` (line 62) | TX-HOP | :8012 9/48; :8014 9/48 | VERIFIED (`RESULTS-STACK-8014.md:57,62`) |
| Payload cut vs billed cut | −24.2% payload, −2.4% billed | % of tokens | Consonance `EXP#43` — `handoff from consonance/MEASURED_FACTS.md` (F1, line 12); `handoff from consonance/DO_NOT_REDO.md` (line 7) | EXP#43 | n/a (Consonance single build) | VERIFIED (`MEASURED_FACTS.md:12`; `DO_NOT_REDO.md:7`) |
| Append-only cache hit climb | 0 → 0.489 | cached fraction | `handoff from consonance/MEASURED_FACTS.md` (F2, line 13) | EXP#43 | n/a (Consonance single build) | VERIFIED (`MEASURED_FACTS.md:13`) |
| Rewrite cost per 48/72-byte handle | D-086 repayment step cost (48 of 72 prefix bytes moved) | prefix bytes moved | `handoff from consonance/MEASURED_FACTS.md` (F3, line 14); `handoff from consonance/DO_NOT_REDO.md` (D-086) | D-086 | n/a | VERIFIED (`MEASURED_FACTS.md:14` — "48 of 72 prefix bytes"; DO_NOT_REDO.md cites D-086) |
| Pinned fixture overwritten in place | 278 rows across six `rows-agg-*` files pin `2b416d827c36ec958aa50e54db4ec5d52f72f061e7c39e9a417b5f0b2078370c`; the sole on-disk `TX-AGG.v1.json` hashes `178042c254f7b732f57603985de35adf8e3722f80507219103c0f7b259e81b03`; 0 of 56,431 workspace files and no git ref carry the pinned bytes | rows pinned (278/278) / digest copies found on disk (0) | `measure/FIXTURE-MAP-MT36.note` (143 lines: pin inventory, 56,431-file scan, re-serialization probe, `git log --all`); pins in `experiments/ptr-engine/measure/rows-agg-{fetch-mt36,fetch-mt50,fetch-test,fetch-test2,fetch-r1,masking-r1}.jsonl` | gen-7 (identifiers preserved across the rewrite: same `TX-AGG.v1`, N=100, `wall_tokens` 4312) | not comparable — every one of the 278 rows carries `claim: none`, `comparison_eligible: false` | VERIFIED (pin absent, rewrite timestamped; provenance unverifiable) |

### What those 278 rows may and may not support

Timeline, exactly: `experiments/ptr-engine/longrun/tasks-v7/TX-AGG.v1.json` was rewritten **in place** at `2026-11-09T08:57:28Z` (mtime = ctime, a real write), about eight minutes after the last run that consumed the old bytes — `longrun-2026-11-09T084942Z-bounded-context-fetch-r1`, at `08:49:43Z`; the 20 manifests recording `fixture.sha256 = 2b416d82…` for that path run `08:21:44Z` → `08:49:43Z`. The only commit touching that path, `9fadcc9` ("preserve context x serving instrument, fixtures and measurements"), **already carries the rewritten bytes**, so no pre-rewrite blob exists in any ref, and no deletion of the path is recorded anywhere. Identifiers survived the rewrite — same `gen-7`, same `TX-AGG.v1`, same N=100, same `wall_tokens 4312` — while the ground truths changed: `cp.TX-AGG.g00.d2` expected 20786 in the rows versus 156145 on disk, `g01.d2` 60786 vs 210513, `g00.d6` 10131 vs 51443, `g02.d2` 100786 vs 269767, `g01.d6` 30131 vs 84932, `g03.d2` 140786 vs 268509 — 26 of 26 rows embedding a checkpoint agree on id/turn/question/source and disagree on `expected`, 0 identical.

These rows **may** support:

- the per-row measurements they recorded (billed/total/wall tokens, ttft, latency, `content_sha256`, `request_sha256`, arm, rep, turn, run id);
- that a run carrying the row's run id loaded a TX-AGG document hashing `2b416d82…` at that moment;
- grading of the answers actually emitted, against each row's **own** recorded `expected`.

These rows **may not** support:

- **reproducibility** — the prompt prefix cannot be rebuilt, so no derived token count can be re-checked;
- **substitution** of the current on-disk fixture's numbers (different document, different ground truths);
- **cross-arm comparability** — all rows carry `claim: none` and `comparison_eligible: false`;
- any **`ABSENT = 0`** reading of the missing fixture.

The procedural rule this produced — a fixture is identified by path **and** digest, so regeneration that changes any byte writes a new versioned path — is recorded in `experiments/ptr-engine/tools/build_fixture.py` (module docstring) and `docs/FIXTURE-GENERATIONS.md` §8.

## Open questions this ledger does not answer

- Is the distance cliff a matter of presence or position (E3)?
- Whether bounded fetch's aggregation ceiling can be lifted above 4/48.
- Whether a fork of SGLang is justified (per-range eviction, non-prefix reuse, per-range attribution).
- Whether Nemotron Nano can hold the answer contract at or above occamy.
- Whether HiCache pays for itself in billed tokens (E5).
