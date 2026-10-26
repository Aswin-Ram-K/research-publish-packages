# TRACE_PIN_REVERIFICATION — UTRACE1

Re-verification, against the **pinned** trace copy, of every trace-dependent claim in this workspace.
Commissioned from `orchestration/handoffs/UCONT1.json` `next_unit_hint` item (1).
Bound: 25 tool calls. No git run against `/home/zer0null/Duval`; no writes into `state/`.

## 1. The pinned artefact — CONFIRMED

| field | measured value |
|---|---|
| path | `dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl` |
| bytes | **866,816** (matches the 866,816 claim) |
| sha256 | **`431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb`** (matches) |
| lines / JSON records | 573 / 573, 0 unparseable |
| mtime | 2026-10-08 06:25:11 -0500 |

**23 byte-identical mirrors** of the pin exist under `state/` (866,816 B, same sha256), including
`state/U6.8/live/dockets/duval/duval-u55-pinned/material/data/…`,
`state/U5.12-work/duval-u55-pinned/material/data/…`,
`state/U5.10-fixture/real-copy/…`, `state/U5.11-live/real/duval__duval-u55-pinned/…`,
`state/U5.14-scratch/u55-pinned/…`, `state/U5.8-live/…`, `state/U5.8-repro/…`,
`state/U5.9-repro-before/dock/…`, `state/U5.9-repro/dock/…`, `state/backups/U5.12-…/tree/…`,
`state/backups/U5.18-…/tree/…`, `state/verify/U5.18/{bare,dry}/…`, `state/verify/U6.5/scratch/…`,
`state/verify/V5.20/{bare,bare2}/…`, `state/verify/V5B/u55-copy/…`, `state/verify/V5E/c2/pinned_{base,fixed,loss}/…`,
`state/verify/V6.22/live/…`, `state/verify/V6B/scratch/root/…`.

**`blob 94495930fbf0fd991b14c1e4de79d87a93fce9ae` is NOT in `/home/zer0null/Duval/.git/objects`** (probed
by zlib read, no git): `MISSING`. It is the *workspace* docket repo's blob for the pinned copy, not a Duval
object. This does not weaken the pin — the content sha256 matches — but the blob id is a workspace-repo
identity, not a target-repo one.

### Four distinct trace contents exist in this workspace — do not conflate them

| bytes | sha256 | where |
|---|---|---|
| 859,469 | `aaaffa23da9d611393d463c62ff89abfcfdf31c5d00b47ae2ef4ea93062631da` | `state/refresh-verify/duval/scn{A,B}/…/repo/traces/…`, `…/repo/.worktrees/engine-{a,gap}/traces/…`, `state/kg-refresh/duval/repo/…` (12 copies) |
| 866,816 | `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb` | the PIN (23 copies) |
| 869,151 | `37bdb77cb8606d183a6562c15fd8dc24e165a05fab1811d4c82a8a9904b50683` | `state/verify/U7.2/duval-copy/traces/…`, `state/verify/U7.2/live{,-rt}-state/kg-refresh/duval/repo/traces/…`, `state/verify/V5/live_dockets/duval/duval-u55-pinned/material/data/…` |
| 872,648 | `aa6f63a7565b89e4a59bfd60be2db6a00373751548a41ebcad295bb2559449b0` | `state/logs/U5.6-scratch/duval/u56-tree-first-live/material/data/…` |

## 2. The live path has moved AGAIN — UCONT1's "now" is already stale

| state | bytes | lines | sha256 | mtime |
|---|---|---|---|---|
| live, measured by UTRACE1 | **1,624,082** | 1087 | `35687221b1a19d540534ff601ee233f67b814f643243bc933107ce703bff075d` | 2026-10-15 21:02:05 |
| live, as UCONT1 recorded | 1,570,243 | 1031 | — | 18:50:03 |
| pinned | 866,816 | 573 | `431605e6…` | 2026-10-08 06:25:11 |

The live file grew **+53,839 B between UCONT1's measurement and this unit's** (1,570,243 → 1,624,082).
Any sentence of the form "…grew from 866816 to 1570243 **now**" is already false as written.

### Blob archaeology (zlib read of `/home/zer0null/Duval/.git/objects`, no git)

- `2ec22a6781240c3fd906d3692eeba432b9a8733d` = **1,570,243 B, 1031 lines**,
  sha256 `03fa52a68dbf6d296aab649c93f341ff3a0629d849d789d81282191d86a795c2`.
- `e25ac80fba75745909e8b1bc89f1cf2bab18e79c` = **1,567,661 B, 1029 lines**,
  sha256 `92a456579bc83db30031e626f683601b5cf23d4d826faece6eb564bc94b20c4c`.

**CONTRADICTED detail in UCONT1.** `UCONT1.md:30` records the growth as
"parent `d04afbb8` blob `e25ac80f…` → HEAD `ec1f06d9` blob `2ec22a67…`; file 866816 B at our pin → 1570243 B
live (+81 %)". The blob pair demonstrates a delta of **+2,582 B**, because `e25ac80f` is already 1,567,661 B.
The +703,427 B growth is **pin (866,816) → HEAD (1,570,243)**, which spans many commits, not the cited parent
link. The pair as cited cannot carry the stated growth.

## 3. Trace-dependent claims and per-claim verdicts

Three numbers side by side. "gate hits" is reported under **both** readings because the claims do not record
which method was used: **occurrences** (count of regex matches) and **gated lines** (lines containing ≥1
match). The pattern set is the one documented at `strategy/LEAD_PACKAGE.md:41-46`.

| claim | where | claim says | **PINNED** gives | LIVE gives | verdict |
|---|---|---|---|---|---|
| T1 byte size | `strategy/NC1_UNBLOCK.md:134`, `strategy/NC1_FIX_PROPOSAL.md:118`, `strategy/AUTHOR_DECISIONS.md:94`, `orchestration/handoffs/UDECIDE1.json:15`, `orchestration/handoffs/UNC1A.json:56`, `orchestration/units/UNC1A.md:45` | 1,570,243 B | **866,816 B** | 1,624,082 B | `holds-only-on-live` |
| T2 gate hits | `strategy/NC1_UNBLOCK.md:134-135`, `:189`; `strategy/NC1_FIX_PROPOSAL.md:118`; `strategy/AUTHOR_DECISIONS.md:94-95` | 1031 | **573 gated lines / 712 occurrences** | 1087 gated lines / 1262 occurrences | `holds-only-on-live` |
| T3 "1.5 MB corpus" | `strategy/NC1_UNBLOCK.md:189` | 1.5 MB | **0.83 MB** | 1.62 MB | `holds-only-on-live` |
| T4 "grew 866816 → 1570243 now" | `strategy/CONTAINMENT_CHECK.md:261-262`; `AGENTS.md` (new trace-pin clause) | 866816→1570243 | start half **holds** (866,816 ✓); "now" half **broken** | 1,624,082 | start `holds`, "now" `broken` |
| T5 "working `431605e6` (866816 B)" | `docs/LIVE_TARGET_NOTES.md:50` | working = `431605e6` / 866,816 B | pinned leg ✓ | **`35687221` / 1,624,082 B** | `contradicted` against current live |
| T6 `e25ac80f` as the pre-growth blob | `orchestration/units/UCONT1.md:30`, `strategy/CONTAINMENT_CHECK.md:151` | implies 866,816 B parent | **1,567,661 B** | — | `contradicted` |

### T2 detail — what 1031 actually is

Under the documented pattern set, `2ec22a67` yields **1205 occurrences**, not 1031. The number 1031 is
exactly that blob's **line count**, and exactly its **gated-line count** — because the file has 1031 lines
and *every one* carries a gate token. The token is the record's own `session` field,
`"session": "2026-09-28-duval-m0"`, which matches `duval` on every record.

**Correction to the framing**: the pinned corpus is *not* clean either. `strategy/NC1_UNBLOCK.md:135`'s
"it is the most disclosure-dirty artifact in the package" survives — but at 866,816 B the pin is
**573 gated lines out of 573** (712 token occurrences), not 1031. The claim is quantitatively a
live-path measurement (44 % larger than the pin on the relevant count).

## 4. Containment wording still in the stronger form

`strategy/CONTAINMENT_CHECK.md:266-268` already records the corrected form ("*no write by this workspace's
units*", not "*no writes*"). These places still state the stronger form and were **not edited** (a follow-up
unit applies the correction):

- `strategy/NC1_FIX_PROPOSAL.md:169` — "Containment: target repo untouched (git status + mtime sweep), nothing written outside the workspace."
- `strategy/VERIFICATION_REPORT_10.md:10` — "Target `/home/zer0null/Duval` untouched (no writes, no `git`). `papers/**` not edited."
- `strategy/VERIFICATION_REPORT_11.md:10` — "**Read-only honoured:** `/home/zer0null/Duval` and every registered target untouched; no `git`"
- `strategy/NC1_UNBLOCK.md:257` — "Target sources of interest are older and untouched: `evals/prevention.ts` 2026-10-14 20:03, …" (narrower — scoped to named files whose mtimes do antedate the foreign writes; weaker finding, still cited in the stronger idiom.)

## 5. Red→green on this unit's own method

Control: pinned copy counts **712** occurrences. Injecting one line containing gate tokens
(`duval`, `StateClass`, `admit(`, `expanded[`, `TRADE_SECRET`) into `scratch/utrace1/redgreen.jsonl`
raises the count to **717** — the method notices. It also **discriminates copies** (712 pinned vs 1205 for
`2ec22a67` vs 1262 live), so it is not a constant. A method that cannot fail is not evidence; this one can.

## 6. Not reproduced / unverified

- `94495930…` **not present** in `/home/zer0null/Duval/.git/objects` — cannot be confirmed as a Duval blob.
- `ba6128bf` (`docs/LIVE_TARGET_NOTES.md:50`, pinned@`3982f26`, 864,384 B) — not checked; `unverified`.
- Which gate-hit method produced 1031 is **not recorded** in any claim site; both readings reported.
- The 859,469 / 869,151 / 872,648 B copies were hashed but not traced to their producing units — `unverified`.
- Whether `1031` was ever a correct occurrence-count under some other pattern set — `not_reproduced` here.

## 7. Evidence commands

```
sha256sum dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl   # 431605e6… 866816
stat -c '%y | %s | %n' dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl
sha256sum /home/zer0null/Duval/traces/2026-09-28-duval-m0.jsonl                    # 35687221… 1624082
python3 -c 'zlib read of /home/zer0null/Duval/.git/objects/**'                     # 2ec22a67=1570243/1031
find . -name '*duval-m0*.jsonl' | xargs sha256sum                                  # 23×431605e6 + 3 stray contents
python3 scratch/utrace1/gatecount.txt                                              # pattern-set counts + red->green
```

No git command was run against `/home/zer0null/Duval`. Nothing was written to `state/`.
