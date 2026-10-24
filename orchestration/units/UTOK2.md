# UTOK2 — re-baseline the token substitution and extend it to the un-cleared residuals

**Status: done.** Deliverable: [`experiments/token-substitution-test/REPORT2.md`](../experiments/token-substitution-test/REPORT2.md).

## Card (as received)
Unit **UTOK2** of the Research Extractor workspace. WORKSPACE (write only)
`/home/zer0null/reserach extarctor`; TARGET `/home/zer0null/Duval` **READ ONLY** (never write, never run
git there). Only unit running. Must not edit `repro/encoder-crossover-190-SANITISED/**`, `papers/**`,
`experiments/second-labeller-190/**` — work on own copies. `/tmp` and `/dev/shm` are per-call tmpfs; work
inside the workspace; retry a failed call ≤3×; write incrementally. **Hard bound: 45 tool calls** (stop and
report `partial` if exceeded).

**Purpose (one):** re-baseline the substitution against the *current* tree and extend it to the residuals
UTOK1 deliberately protected, so the author knows exactly what a clean released fixture would cost.
Steps: (1) copy the current `repro/encoder-crossover-190-SANITISED/` to `work2/` + `work2-orig/` and record
hashes of the files to be changed; (2) apply the full substitution — UTOK1's `mapping.json` plus
(a) the 2 protected `expanded[]` option labels, (b) the frozen `results/*.json` lines, (c) the 3
`harness/data/manifest.json:5,10,15` hits, (d) every remaining `/home/zer0null`/`duval` line;
(3) re-run `verify/run-verification.sh` + `verify/recompute-claims.py` on the substituted copy, report the
ten CLAIMS values and the projection/train/dev/fixture digests, and run the **verbatim** gate hard-fail list
with per-pattern before/after counts; (4) state what remains that substitution cannot fix (curation:
`code/verify/**`, `EXCLUDED.md`, `LICENCE_TODO.md`, `REDACTION_REPORT`, `RESIDUALS.md`, and the
`907fa39`/`ad301ae` anchors — kept deliberately as the read-only proof, not removed).
Rules: never edit the source; never write to `/home/zer0null/Duval`; do **not** tune a substitution until it
passes — report the first honest measurement; do not invent a pattern or a digest (transcribe the gate list,
measure the digests).

**Declared write paths:** `experiments/token-substitution-test/**`, `orchestration/units/UTOK2.md`,
`orchestration/handoffs/UTOK2.json`.

## Result

* Baseline reproducible against the present bytes: source == `work2-orig` byte-for-byte (58/58 files,
  per-file sha256 lists diff-clean; tree digest `6bda08858d521691d677e931449cde0ac7f3e5be0ec909b196b5145fc1b789d6`).
* Extended substitution: 21/58 files changed, 0 guard aborts, identity keys (`id`/`kind`/`correct`) and all
  instrumentation byte-identical; only `question` (46) and `options` (2) fields of the fixture changed.
* Ten CLAIMS values: **10/10 unchanged**; `recompute-claims.py` → `ALL CLAIM NUMBERS PRESERVED: True`.
* Digests: projection **moved** `57a29b4e…` → `d52893f4c6d5502b906d679203e321dfb652ac98e07196b5baa06f9533d66676`
  (declared); train `24c39afa…` and dev `d311a99f…` and fixture `8dd05ce6…` **unchanged**.
* Option labels (a): **partial** — all ten values hold, but substituting the 2 labels alone changes
  `/routeA/ties` 120 → 119 in the regenerated `second-labeller/metrics.json`, so the shipped metrics stops
  regenerating byte-identically (the only content difference; `run-verification.sh` §5 `True/True` → `False/False`).
* Frozen `results/*.json` (b): **yes** — display/evidence only, nothing reads their label strings.
* Manifest (c): **3/3** neutralised, still valid JSON; not durable (`prepare.py` regenerates local paths).
* `/home/zer0null` + `duval` (d): **0 hits tree-wide**.
* Gate: **407 → 158** lines. Reaching zero: `/home/zer0null`, `duval`, `src/scope`, `src/layer`, `admit(`
  (+8 never present). Remaining: `publish-present-compete` 1, `EXCLUDED.md` 27, `REDACTION_REPORT` 96,
  `RESIDUALS.md` 35, `LICENCE_TODO` 17, `TRADE_SECRET` 3, `VERIFICATION_REPORT` 13, `StateClass` 5,
  `grantPolicy` 12, `src/broker` 3, `expanded[` 2.
* Cannot fix by substitution: the curation set above, plus the **2 `grantPolicy` question strings**
  (`fixture/reflex-decisions.ts:288,798` / `harness/data/fixture-190.json:234,851`) — a UTOK1-mapping gap
  that, if fixed, moves the projection digest again — and the `.py`/`.sh` tooling and its logs.

Full evidence: `REPORT2.md`; logs under `experiments/token-substitution-test/logs2/`
(`before2.txt`, `after2.txt`, `labels-only.txt`, `gate-table.txt`, `tree-hashes-*.txt`, `substitution2.txt`).
No files outside the declared write paths were written; `/home/zer0null/Duval` was never written.
