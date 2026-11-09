# V-LEDGER-REBUILD — independent recompute of LEDGER-REBUILD-27

**Verdict: pass.** My count, computed before running their builder, is identical to theirs on every
published figure: **requests_raw 1128 · requests 1128 · requests_deduplicated 1098 · duplicate_excess 30 ·
remaining 3192 · files 15 · rows 1128 · 12 deduped / 3 not applicable · diagnostic.deducted false**.

## 1. My rule, my number

A request is one row that represents an inference call that reached the server.

- `kind: "turn"` — counts.
- `kind: "tool-followup"` — counts; it hits the server and is billed like any turn.
- Suppression is licensed only by `billed: false`, truthy `followup_suppressed`, or `served_from == "prompt"`.
- A row with no recognised kind counts and is flagged (conservative).
- A row carrying an HTTP error counts: a rejected request still took a wire slot.

Corpus census of the six markers: `billed` 0 rows, `followup_suppressed` 0, `served_from` 0,
`billed_round` 24, `fetch_followup` 68, `prompt_served` 0 — **no licensed suppression marker exists at row
level**, so my rule and their rule cannot diverge on the raw count. 14 rows carry errors; all count.

**My number: 1128 requests over 15 files.** Their builder: 1128. **Difference 0, cause: none.**
De-duplicated diagnostic 1098 (30 excess), which the builder publishes and does **not** deduct.

## 2. Reproducing the 27

`1128 − 27 = 1101`, and the other fourteen files sum to exactly 1101. The 27-row file
`rows-cell-pointer-stable-20261026T182535Z.jsonl` is the newest in the directory (mtime
2026-10-26 13:31:25 −0500); the frozen baseline was captured 13:24:48 −0500, 6m37s earlier. **No other file moved.**

| file | rows | raw | dedup | dup | rule | sha256 |
|---|---|---|---|---|---|---|
| `rows-baseline-2026-10-26.jsonl` | 105 | 105 | 105 | 0 | not_applicable | `638c84942e3bcdba4b416cceda9214f3fdcc99c42171639bf5c52736f40e032d` |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | 6 | 6 | 6 | 0 | decided | `5ac9dd992f5d8715696925f56c225024e172cb98b4b9a937a0ee63bd099e9800` |
| `rows-cell-pointer-stable-20261026T182535Z.jsonl` | 27 | 27 | 27 | 0 | decided | `46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1` |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | 100 | 100 | 0 | not_applicable | `c01c7b4a477fe24bc55370ceddf26d885a1fe827e7135023cdde48b271e8c934` |
| `rows-live-2026-10-26.jsonl` | 27 | 27 | 27 | 0 | not_applicable | `3d02b4d473304f0012b34024cc517c70d7f23b60de1103c1ca1b93a7e2752e5b` |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | 29 | 29 | 0 | decided | `9d4ad90ce34cb781c04e9f73fba50ffb47d5b35d6d1491389d22a49044516405` |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | 40 | 40 | 0 | decided | `9b1097234bf8d2464a4d24ec48cf0cccc1ecd64bd853815fc6643b1ad3da3368` |
| `rows-longrun-2026-10-26.jsonl` | 192 | 192 | 192 | 0 | decided | `bc61d38192d4e4316021ec8d3d0e21dcb8e6153f463260a0138da21969d0b21e` |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | 192 | 192 | 0 | decided | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | 96 | 96 | 0 | decided | `80d85fe0e977af164a5ffeca8b2f95350c6614d2112455c3ace93765530ff921` |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | 96 | 96 | 0 | decided | `999f298dac8b83569c4059946e7789b76ec485b24a5c9a39d6c1616f0501c28e` |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | 68 | 51 | 17 | decided | `f11391aa2989949f904b8092074cb7b85b65dfe5b8c89431930fe921b28de77f` |
| `rows-longrun-v5-tools.jsonl` | 72 | 72 | 70 | 2 | decided | `586b66f27939bd05e09d8b48dad745a5fa268c3f31103695746df3e3f8443cb5` |
| `rows-longrun-v6-tools.jsonl` | 72 | 72 | 61 | 11 | decided | `1e78d75f259afbe0406643825941a65b4773b4342b847698005ad5908b3e531e` |
| `rows-pilot-thinking-2026-10-26.jsonl` | 6 | 6 | 6 | 0 | decided | `6b81a6281ce0b266f45ab1b95fc3834e446bea5708e5466988b28e133a0e9e10` |

## 3. Attacks (all in `/tmp/vledger`, never the workspace)

| attack | exit | outcome |
|---|---|---|
| **A** delete the stopped cell's file | **0** | TOTAL 1101 raw / 1071 dedup / 14 files / remaining 3219, "within budget". **No guard fires** — no test pins 1128 and `ledger_delta.py` reads the `REQUEST-LEDGER.json` snapshot, not the corpus. |
| **B** byte-identical duplicate file | **0** | TOTAL 1197 raw / 1167 dedup / excess still 30 / 15 files. De-dup is **per file only** (`request_ledger.py:455-482`): an external duplicate adds +96 with no diagnostic. |
| **C1** truncate last line mid-JSON | **5** | `unparseable row: Unterminated string ...`, "nothing counted: an unreadable row file makes the total unknowable". Refuses, correctly. |
| **C2** drop the last whole line | **0** | TOTAL **1100**, silently, no warning. |

## 4. Deduction discipline

`diagnostic.deducted` is `false`, the budget figure is the **raw** one (1128 / 3192). No code path deducts
`requests_deduplicated` or spends against `remaining_deduplicated`. Two soft findings:

- **`request_ledger.py:629`** — `diagnostic.deducted` is the literal `False`, not `bool(deduct)`; if a sound
  rule were ever enabled, `requests` could be reduced while the diagnostic still reported "not deducted".
- The newest cell rows carry `request_sha256` and `request_identity_complete` — the evidence key
  `deduction_permitted()` demands — but that gate is **global** (one flag + any non-empty hash name unlocks
  subtracting 30), while the identity hash exists on only some rows and on none of the 3 legacy files.

## 5. `LEDGER-GRID-BASELINE.json`

Still claims **spent 1101 / remaining 3219** (dedup 1071) at sha `6b6dff44…`. `ledger_delta.py` compares
against it and exits 0 with `delta 27, deficit none`. **The baseline is stale by exactly the stopped cell: it
was pinned at 18:24:48Z, the stopped cell wrote its 27 rows at 18:31:25Z, so the grid's 27 delta measures that
rebuild, not grid spend.**

## Is 1,128 / 3,192 the defensible figure?

**Yes** — raw, with 1,098 de-duplicated carried as a non-deducted diagnostic — **and yes, the grid path still
reads the stale 1,101 baseline, so its 27 delta currently measures the stopped cell's rebuild rather than grid spend.**
