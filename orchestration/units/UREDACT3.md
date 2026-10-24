# UREDACT3 — validate, run and prove `redact.py`

**Type:** re-delegation (UREDACT2 died 2026-10-15 ~18:55:57, no handoff, no card, no report).
**Workspace:** `/home/zer0null/reserach extarctor` · **Target:** `/home/zer0null/Duval` READ-ONLY (never opened).
**Write paths:** `repro/encoder-crossover-190-SANITISED/**`, `orchestration/units/UREDACT3.md`,
`orchestration/handoffs/UREDACT3.json`.
**Hard bound:** 50 tool calls. **Used: 28.** **Status: done.**

## Task
Establish whether `redact.py` (50,022 B, `db5c8272…`) actually reproduces the shipped sanitised tree,
whether its stages A–D are real, whether any number moves, and close the two open items UREDACT2 left.

## Verdict (measured)
| question | answer |
|---|---|
| stages A–D complete? | **yes** — all four parse (`ast.parse` OK) and mutate the tree; no stubs |
| `apply_editorial()` | **not a stage** — 3 die-on-no-match literal patches run between A and B (README sentence, LICENCE_TODO wholesale, MANIFEST UFIX10 provenance) |
| idempotent against **itself**? | **yes** — regen₁ vs regen₂: 44/44 byte-identical, stdout identical |
| idempotent against the **shipped tree**? | **NO** — 35/58 match · 9 differ · 14 unit-owned not regenerated · 0 extra |
| responsible stages | **C** (all observable content), **D** (`MANIFEST.json`), **B** (`redaction-log.json`) |
| root cause | every generated file is stamped 15:39:37 or 18:21:52; **only `redact.py` carries 18:55:57** — the 4-stage pipeline was never executed |
| `numbers_changed` | **0** — 10/10 values unchanged on both trees; `0.6789` = `0.6789473684210526` intact |
| projection digest | shipped bytes = `57a29b4e…` = as-audited = `INTEGRITY.md` §2. The card's `d52893f4…` is UTOK2's **post-substitution** value; `redact.py` stage C reaches a third value `b85e4585…` |
| tree intact | **yes** — 58/58 re-hash identical; the only post-run change is the card-ordered `INTEGRITY.md` row |
| gate (24 verbatim patterns) | shipped **394** distinct lines · regen **98**. UTOK2's 407→158 not reproducible (tree changed twice after its run) |
| `GrantPolicy` gap | **CLOSED** — 9 shipped occurrences → 0 regenerated; diff at `fixture/reflex-decisions.ts:288,798` shows `GrantPolicy`→`POLICY_A` |
| stale MANIFEST identity rows | **6 found** (card said 5) · **4 fixed by stage D** (EXCLUDED.md, LICENCE_TODO.md, harness/LEAD-WIRING.md, harness/collect.py) · **2 still open** (README.md, INTEGRITY.md — unit-owned, never regenerated; stage D writes the *source* digest and leaves the flag `true`) |

## The finding the parent most needs
`redact.py` is **newer than the tree it claims to produce**, and running it **in place would move the
published scoring-projection digest `57a29b4e…` → `b85e4585…`**, falsifying `INTEGRITY.md` §2. That is a
release decision (regenerate + re-declare the digest, or ship the pre-stage-C tree) — **not a bug to
patch**. `redact.py` was **not rewritten**. It is not the generator of record; it is a candidate
next-generation generator.

## Artifacts
- `repro/encoder-crossover-190-SANITISED/REDACT3_REPORT.md` (35,440 B, sha256 `2ef00dcd…`) — full account.
- `repro/encoder-crossover-190-SANITISED/INTEGRITY.md` — line 68 row corrected (`232f13ea`/23844 → `db5c8272`/50022) + a note; now `93a0fda8…`, 10,780 B.

## Safety
All generator runs targeted `.uredact3/**` (scratch). Byte-for-byte backup at `.uredact3/shipped-backup/`
(58 files) + hash tables `.uredact3/snapshot.sha256`, `snapshot.final.sha256`. `verify/VERIFICATION.txt`,
which the in-place acceptance run rewrote, was restored to its snapshotted bytes
(`ecde4996…`) from the backup.
