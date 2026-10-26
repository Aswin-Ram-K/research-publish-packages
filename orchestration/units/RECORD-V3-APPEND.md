# RECORD-V3-APPEND
**Purpose.** Append four correction paragraphs to `experiments/ptr-engine/RECORD.md` (140 lines / 34,281 bytes / sha256
`2421f92e…`) from audit `orchestration/handoffs/V-RECORD-2.json`. Append only: each correction is a new paragraph naming
the sentence it corrects; no existing text edited.
**Bound.** 14 tool calls, append only, offline (no network, no endpoints, no git against `/home/zer0null/Duval`).
Kill: any failed proof -> restore backup, verify `2421f92e…`, report `failed`.
**Write paths.** `experiments/ptr-engine/RECORD.md`, `orchestration/handoffs/RECORD-V3-APPEND.json`, this card.

## Insertion point
Original line 136 (`**Checked and clear:**`, closing line of the contradiction block, section 5) — after the last closure
layer (C10 `Adjudicated 2026-10-25`, original 134) and before `## 6. How to use this record` (original 138).
Appended text = new lines **137-144**; first heading = new line **138**.

## Paragraphs (verbatim, in order)
1. `**C8 REOPENED 2026-10-26 — the "303 exact" count was never recomputed.**` — fit set 387 rows (all `role=measure`);
   `cached_reported` 304 (218 `sglang` + 86 `vllm`), 83 null; residual `cached − (P1 − P1 mod grid)`, grid 64 / 1056;
   distribution `{0: 160, −64: 51, −128: 6, −192: 2, −1056: 69, −2112: 16}`; strictly-zero 160 not 303; 60 `sglang` rows
   at −64/−128/−192; `vllm`/`Bprobe-400`/`rep 0` is residual 0 (`prompt_tokens 467, cached_tokens 0`), not off. C8 **OPEN**,
   bookkeeping reading withdrawn, 321 rows **UNSOURCEABLE**.
2. `**C7 — the law applied outside its declared scope. CLOSED 2026-10-26.**` — `LAW.md:206` scope quote; `PREREG.json:30`
   billed `"turns_per_rep": 4` (`:28`); scope statement `RESULTS.md:191-220`; two independent defects (`runner.py:490`
   comment / `:495` assignment: `L` = whole prefix); `runner_v2.py` never run against a server.
3. `**Engine size restated 2026-10-26 — the P0.1 count was frozen prose.**` — on disk 2026-10-26T02:10Z: `ptr_engine/` 10
   modules / 3,653 lines, `tests/` 13 files / 2,248 lines vs 1,896 / 1,222 earlier; a size figure carries its date.
4. `**Line citations are not evidence 2026-10-26 — three of them have already drifted.**` — `RESULTS.md` 49,594 and its
   32,401 correction now on the same line `:181`; "no avalanche" at `:164` not `:150`; `RESULTS.md:174-181` already carries
   32,401, the +17,193 residual and the 6-token completions. Rule: quoted sentence + file digest, never a bare line.

## Proof (measured)
before `2421f92e9b9b24ba8b20f027be13393264f20ac0fa61c3e2238d0992ce738c78` 140 lines / 34,281 bytes ->
after `bc592dec2fa34f64c6cc713bb54710d90c8288c4b569ca8e6a1986d686903aa6` 148 lines / 38,075 bytes.
`head -n 136` both sides: `ea44291a77311f0890c84e677b0987911a7a33d96e8dd8f3e41e15a0d3701027` — identical. Dropping new
lines 137-144 reproduces the original file exactly (140 lines / 34,281 bytes / `2421f92e…`).
New headings 1 / 1 / 1 / 1; `Adjudicated 2026-10-25` 5, `Partition withdrawn 2026-10-25` 1, `C8 closes 2026-10-25` 1 — all
unchanged; `Bprobe-400 rep 0` 2 (was 1; +1 is the mandated verbatim quote of the sentence paragraph 1 corrects).

**Status: done.** No blocker. Deviations in handoff `assumptions`: insertion-point reading; the unavoidable
`Bprobe-400 rep 0` rise; `/tmp` non-durability worked around by exact reconstruction of the original file.
