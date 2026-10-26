# NONCENSUS_LEAKS — adjudicating the invisible class (`imajev` + neighbours)

**Unit:** UNONCENSUS1 · **Status:** done (classification) / partial (no neutralised tree — gated) ·
**Hard bound:** 25 tool calls · **Used:** 17.
**Workspace:** `/home/zer0null/reserach extarctor` (quoted — the directory name contains a space).

## 1. Classification of `imajev` — **(a) third-party public model name. It is a citation; it must STAY.**

`imajev` in `scratch/ubij3/tree-three-r2` (42 occurrences / 10 files) names **a public third-party
HuggingFace model**, not the project's own corpus, fixture, component or evaluation.

Evidence, in order of strength:

1. **Live fetch, HTTP 200** — `https://huggingface.co/mohit67890/imajev-4b` (unit ran `web_fetch`):
   `License: apache-2.0`; pipeline `Image-Text-to-Text`; libraries `PEFT`, `Safetensors`, `MLX`;
   tags `typed-decisions`, `jev`, `decision-model`, `vision-language`, `calibrated-probabilities`, `lora`,
   `Eval Results`; 106 likes; 2 community threads. The model exists, publicly, right now.
2. **The read-only target cites it as an external contender, with the card's own figures** —
   `/home/zer0null/Duval/.worktrees/GATE-score/docs/BOARD.md:286`:
   `[`mohit67890/imajev-4b`](https://huggingface.co/mohit67890/imajev-4b)` — **Apache-2.0**; a PEFT **LoRA
   adapter**, rank 64 / alpha 128, **122,552,320** trainable params (121,896,960 LoRA + 655,360 readout);
   base **`Qwen/Qwen3.5-4B` revision `851bf6e8`**; **siblings `imajev-2b` and `imajev-9b` exist**.
3. `/home/zer0null/Duval/.worktrees/GATE-score/docs/VISIT_LOG.md:833`: "**a real inference box brought
   up:** `imajev-4b` (Apache-2.0, Jev contract on `/v1/systemone`) was installed on the GX10 and bound to
   the LAN at `192.168.2.168:8765`".
4. `/home/zer0null/Duval/.worktrees/GATE-score/docs/DECISION_LOG.md:5043-5044`: "**A related but different
   9B result exists on the box and is NOT ours.** `~/imajev/results/imajev-9b/` reports base-9B accuracy
   **74.7 %** on the *imajev* fixture (a Qwen3.5-9B + LoRA decision model, MLX-served). It is a
   **different instrument on a different task**".
5. The 42 in-tree occurrences are all of the form `imajev-4b`, `imajev-rows.jsonl`, `imajev's`,
   "3,590 imajev rows" — references to **that public model's measured rows**
   (`docs/research/D35-evidence/imajev-rows.jsonl`), i.e. the project *evaluated* the public model.

**Consequence.** Neutralising `imajev` would erase a citation of a public third-party model and replace it
with a meaningless tag. It is out of scope for NEUTRAL-TAG/v1. **No tree was emitted** (step 3 is gated on
classification (b), which this is not).

## 2. The rest of the invisible class

Counted with the earlier units' convention: raw case-insensitive occurrence counts over the same file set
`grep -ro` uses, on the frozen 184-id list `scratch/uagnostic1/census.tsv` as exclusion set, with
`scratch/ubij1/census_one.py` as the decoded-walk scanner. **My rule reproduces UBIJ3's numbers exactly
where the tree is stable**: `imajev` 42 occ / 10 files (UBIJ3: 42/10), `second-labeller-190` 36 occ
(UBIJ3: 36).

| string | occ | files | class | note |
|---|---|---|---|---|
| `imajev` (`imajev-4b`, `imajev-rows`) | 42 | 10 | **third-party-public** | HF `mohit67890/imajev-4b`, Apache-2.0 — STAY |
| `second-labeller-190` | 36 | 6 | **internal** | project's own second-labeller eval dir; 9 of 36 in `MANIFEST.json` |
| `instrument190` | 48 | 7 | **internal** | the project's 190-case instrument label |
| `decider-4b` | 43 | 8 | **internal** | the project's own decider model (census carries `DECIDER_TIER.md`, `DECIDER_STACK_DECISION.md`, not this compound) |
| `H-A` / `H-B` | 319 / 300 | 13 / 20 | **internal** | project stratum labels |
| `typed-channel` | 21 in `MANIFEST.json` + 31 in `harness/` | 8 | **internal** | component/experiment name (`tools/typed-channel/`, `EXP12-typed-channel-comparison-prereg.md`) |
| `EXP#12` / `EXP12` | 39 | 10 | **internal** | private-repo experiment id |
| `EXP#11` / `EXP11` | 15 | 4 | **internal** | private-repo experiment id |
| `D35` | 31 | 9 | **internal** | private-repo doc reference (`docs/research/D35-evidence/…`) |
| `D44` | 6 | 3 | **internal** | private-repo register line (`D44:47`) |
| `D09` | 7 | 4 | ambiguous | UBIJ3 held `D09/D15/D25` to be *already-substituted neutral tags* |
| `no-union` | 14 | 3 | **internal** | ablation variant label (+ its 2 fixture copies) |
| `encoder-crossover-190` | 9 | 5 | **internal** | project experiment/directory name |
| `LEAD` (`LEAD-WIRING.md`) | 4 | 3 | **ambiguous** | project role vs generic pipeline stage — author decision |
| `tccommon.py` / `tcmodel.py` | 13 / 9 refs | 9 / 8 | **internal** | `tc` = typed channel, in shipped file names |
| `deberta-v3-base` | 37 | 12 | **third-party-public** | HF model, eval baseline — STAY |
| `modernbert-base` | 39 | 11 | **third-party-public** | HF model, eval baseline — STAY |
| `setfit-mpnet` | 40 | 12 | **third-party-public** | HF model, eval baseline — STAY |
| `famr00xx` / `famb00xx`, `F54Index` | thousands / 1015 | 2 / 6 | already-substituted neutral tags | out of scope |

**Counts are state-dependent — pinned.** `no-union` measures **14** here vs UBIJ3's **9**, and
`encoder-crossover-190` **9** vs **4**: in both cases the extra **5** are *entirely* in `MANIFEST.json`,
which the owning unit is editing concurrently. Excluding `MANIFEST.json`, my counts are exactly UBIJ3's
(9 and 4). The tree grew **1,741 bytes** (3,006,637 → 3,008,378) between UBIJ3's 21:23 measurement and
mine. My measurement is pinned to the roll-up hash in §4.

Also found, in no census class (`MANIFEST.json`'s `source` fields leak **private-repo paths and digests of
unreleased files**): `"source": "experiments/second-labeller-190/…"`,
`"source": "git:an unmerged development branch commit (id withheld):tools/typed-channel/analyze.py"`,
`"source": "…docs/research/EXP#12-evidence/…"` plus `source_sha256` values. This is a *reference* leak, not
a name leak — but it is not touched by any identifier census.

## 3. Census before / after — no tree emitted

Step 3 is gated on `imajev` = (b); it is (a), so **no neutralised tree was built and no edit was made**.
Before equals after by construction.

Frozen 184-id census, `python3 scratch/ubij1/census_one.py scratch/ubij3/tree-three-r2`:

```
files scanned: 45
distinct identifiers hit: 74 of 184
TOTAL OCCURRENCES (decoded walk): 3354
  inside stimulus (question/options/situation values): 2171  distinct=30
  outside stimulus (all other values + non-JSON text): 1105
  JSON object keys: 78
```

`imajev` occurs **0** times in that census output — it is outside the 184-id vocabulary entirely, which is
exactly the 81 %-invisible class. UBIJ3's 21:23 line for the same tree read `3348 / 2171 / 1099 / 78 /
74 of 184`; my `3354 / 2171 / 1105 / 78` differs only by +6 outside-stimulus occurrences introduced by the
concurrent `MANIFEST.json` edits — **inside-stimulus is unchanged at 2,171 in both**.

## 4. Diagnostics, idempotence, roll-up

**No diagnostics were re-run, because no tree was emitted and nothing was edited.** Per the card's step 4
I do not assert any diagnostic "should be unchanged" — I make **no claim** about `compare.py`'s route A/B,
the arms or the 2×2; those values belong to whichever tree is actually built. There is likewise no
idempotence build to prove.

Dated roll-up of the tree under study (so my measurement is pinnable):

```
495ecf614d5b417b0aee0e12f957c3af7ad9e99c5439e5b2bf3975a4be05a616   # sha256 over sorted sha256sum lines
45 files, 3,008,378 bytes
MANIFEST.json sha256 f3e4a22c49261ca937311b1d4edf2e8e52d347faed5d1a4f70d93e41b71fc614  # moving
```

`MANIFEST.json` is owned and being edited by another unit; its digest is reported, not relied on.

## 5. Recommendation

`imajev` **stays** — it is a public model citation. The genuinely internal neighbours in §2
(`second-labeller-190`, `instrument190`, `decider-4b`, `H-A/H-B`, `typed-channel`, `EXP#11/#12`, `D35`,
`D44`, `no-union`, `encoder-crossover-190`, `tccommon/tcmodel`) were **not** neutralised, because the card
gates neutralisation on `imajev` = (b). A follow-up unit should neutralise those (and decide `LEAD` and
`D09/D15/D25`), and decide separately whether `MANIFEST.json` may publish digests and paths of unreleased
files.
