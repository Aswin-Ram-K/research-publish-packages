# VERIFICATION REPORT — REL7 (verifier unit UVEREL7)

**Artifact verified:** `strategy/GATED_READ_RELEASE_CUT.md` (244 lines, unit URELEASE7) and its handoff
`orchestration/handoffs/URELEASE7.json`. I did not write the artifact.

**Verdict: `partial`.** The release decision survives intact (cut3 is exactly 5 files / 28,233 B with all
five §4 md5s reproduced and exits 0 with 143 PASS / 5 NOTE; cut4 breaks exactly at `per_task`), but three
of §2's four byte totals and both §2 byte deltas are contradicted by measurement, and two absolute
§5/§6 statements are overstated.

## Commands run

```
for c in cut1 cut2 cut3 cut4; do python3 scratch/urelease7/$c/verify_claims.py scratch/urelease7/$c; echo "$c exit=$?"; done
find scratch/urelease7/<cut> -type f -printf '%s\t%p\n'   # and du -sb <cut>
md5sum scratch/urelease7/cut3/*
python3 -c "json.load(...) key diff cut3 vs cut4"          # see check 3
grep -rIlnE '<handoff pattern>' scratch/urelease7/cut{1,2,3,4}          # exact handoff command
grep -rIlnE '<derived F-01/F-02/X-*/N-06/P-13 pattern>' scratch/urelease7/cut{1,2,3,4}
cp cut3/verify_claims.py scratch/uverel7/verify_claims_redgreen.py      # red→green, see check 7
```

## Check 1 — re-run the ladder: CONFIRMED

| cut | literal exit | PASS | NOTE | FAIL | final line |
|---|---|---|---|---|---|
| cut1 | **0** | 143 | 5 | 0 | `RESULT pass exit=0 claims=143 failed=0 []` |
| cut2 | **0** | 143 | 5 | 0 | `RESULT pass exit=0 claims=143 failed=0 []` |
| cut3 | **0** | 143 | 5 | 0 | `RESULT pass exit=0 claims=143 failed=0 []` |
| cut4 | **3** | 0 | 0 | 0 | `RESULT fail exit=3 missing=['per_task']` |

cut4's full output is byte-for-byte what §3 quotes, including
`MISSING section 'per_task' required by claims ['R5-UNION-MATRIX-1..6', 'R5-SIGN-1', 'R5-SIGN-2', 'R5-SIGN-3', 'R6-CLEAN']`.
Every number in §2's "Literal exit"/"Diagnostics" columns is confirmed.

*Precision note (not a contradiction):* §3 calls the five `UNVERIFIABLE` lines "the five claims"; they are
five claim **groups** — `R5-UNION-MATRIX-1..6` expands to 6 claims, so 10 individual claims are named.

## Check 2 — inventory and md5: cut3 CONFIRMED, cut1/cut2/cut4 sizes CONTRADICTED

Every cut is 5 files, and cut1/cut2 use `record.jsonl` while cut3/cut4 use `record.json` — as documented.
cut3 is exactly the §4 list and all five md5s recompute:

| file | bytes | md5 measured = §4 |
|---|---|---|
| `record.json` | 5,008 | `34e27ccbc09e586f57362196b726f0da` ✓ |
| `verify_claims.py` | 16,808 | `f0855d9e41b09df895e974feb7597856` ✓ |
| `METHOD.md` | 5,866 | `a78e827a0546cbef248befb89b8fa428` ✓ |
| `sealed.json` | 380 | `ce18156c126b530970b3f2f62dd3d2c4` ✓ |
| `provenance.json` | 171 | `97b3dd3224f4b628288fa984b2793970` ✓ |
| **total** | **28,233** | **= §4 exactly** |

The other three totals do **not** reproduce (`find -printf '%s'` and `du -sb` agree; all 20 cut files share
one build mtime, `2026-10-16 16:43:47`, so the disk is the built artifact):

| cut | measured total | §2 claims | delta |
|---|---|---|---|
| cut1 | **1,572,249** | 1,572,498 | −249 |
| cut2 | **1,148,742** | 1,148,991 | −249 |
| cut3 | **28,233** | 28,233 | 0 ✓ |
| cut4 | **27,200** | 27,447 | −247 |

**`contradicted`.** §8's claim "Every number in §1–§6 above is from the run that produced the md5s in §4"
does not hold for these three §2 totals.

## Check 3 — two-sided minimality: direction CONFIRMED, byte deltas CONTRADICTED

- **cut2→cut3 removes 1,120,509 B** (measured `1,148,742 − 28,233`; §2 records 1,120,758 — off by 249).
  Claim count unchanged: both exit 0 with 143 PASS / 5 NOTE / 0 FAIL. The zero-claims-lost half is confirmed.
  Bytes removed are the per-unit `record.jsonl` (1,125,517 B in cut2) replaced by the aggregate `record.json`
  (5,008 B); `verify_claims.py`, `METHOD.md`, `sealed.json`, `provenance.json` are the same size in every cut.
- **cut3→cut4 removes 1,033 B** (measured `28,233 − 27,200`; §2 records **1,035**, and §2's own cut sizes give
  `28,233 − 27,447 = 786`, so §2 is internally inconsistent as well). A `json.load` key diff shows cut4 is
  cut3 with **only** the `per_task` key removed — `only cut3: ['per_task']`, `only cut4: []`, all eight shared
  top-level keys (`configs`, `end_to_end`, `gold_derivation`, `inventory`, `provenance`, `schema`, `sealed`,
  `selection`) byte-identical. The all-claims-lost half is confirmed: cut4 verifies 0 of 143 (143 PASS → 0 PASS)
  and exits 3.

**`contradicted`** for the two deltas. The two-sided *shape* of the minimality argument is unaffected.

## Check 4 — the two sealed figures: CONFIRMED not reproducible

Derived directly from the shipped `selection["[MODE-7]"]` rows in `scratch/urelease7/cut3/record.json`:

- `ok_cheapest = 18` → **0.150**; `ok_cheapest_alt = 27` → **0.225**. Published `0.575` corresponds to no
  count in the rows (`0.575 × 120 = 69`). `sealed.json` carries `"router_cheapest_sufficient": 0.575` as a
  literal and the verifier prints `NOTE R4-CHEAPEST-OK-RECOMPUTED` showing both recomputed values. **Confirmed.**
- Router: rows carry `n = 120` single-pick decisions, `picked_dist = {"[EXTRACT-2]": 120}` (120/120 the same
  extractor), `ok_chosen = 84` → **0.700** chosen-sufficient. `sealed.json` carries
  `"router_decisions_total": 207`; the other 87 decisions are in no record. **Confirmed.**
- Caveat I record: `R4-CHEAPEST-OK-REC` and `R4-ROUTER-207-REC` compare the published literal against
  `sealed.json` — self-consistent, not a reproduction. The `-REC` ids and the accompanying `NOTE` lines
  disclose this; the artifact does not claim otherwise.

## Check 5 — withheld-surface grep: CONFIRMED for the report's categories; §5/§6 overstated

- The **exact handoff pattern** (private paths, `bench.py`, `tasks.json`, `gated-read`, `.dsh`,
  `credentials`, `KEYRING`, `okr_`, `8790`, `PWNED`, `measure/`, `deepseek`, `mimo`, `Duval`, `broker`,
  the method names, `outline`, constants, tag-legend shapes) over all four cut dirs → **0 matching files**. ✓
- An **independently derived** pattern from `strategy/GATED_READ_DISCLOSURE.md` (X-01/X-02/X-03/X-04/X-08/
  X-09/X-10/X-11, N-06 `measure/gated-read`, P-13 `127.0.0.1:8790`, F-01/F-02 row/summary schema keys)
  returns 10 matching files — but every hit is a token collision, not a leak:
  - `n_files` (28×) is a substring of the release's own neutral field `payload_in_files`;
  - `ptok` (in `scratch/urelease7/cut3/verify_claims.py:244`) is a **loop-local variable name**
    (`for a, hits, units, ctxk, ptok in zip(...)`), not a row/schema identifier;
  - `unparsed` (in `scratch/urelease7/cut3/METHOD.md:38`, prose "call errors, unparsed decisions") is the
    generic English word; the actual field is `gate_preds_nonbool`.
  No private path, model id, payload token, module/method name, branch label, broker/credential shape,
  `src/**` name or tag legend was found.
- Because those three F-01/F-02-listed tokens do survive as strings, §5's "no private schema identifier
  survives the reduction" and §6's "the only strings the release carries are the published values and the
  uniform tags" are **`overstated`** (field names, prose and claim ids are obviously also carried). This is a
  wording defect, not a disclosure.

## Check 6 — neutralisation honesty: CONFIRMED

`scratch/urelease7/cut3/record.json` uses `[MODE-1]`…`[MODE-8]` (inventory config counts, incl. `[MODE-6]`
shortlist / `[MODE-7]` single-pick / `[MODE-8]` end-to-end), `[ARM-1]`…`[ARM-6]`, `[EXTRACT-1]`…`[EXTRACT-4]`,
and unit keys `U0001`, `U0046`, `U0058`, `U0060`, `U0082` (in `gold_derivation.stored_only_by_unit`).
`[TASK-01]`…`[TASK-20]` and `[MODEL-1]`/`[MODEL-2]` do **not** occur in cut3's aggregate `record.json`;
they occur only in the per-unit `record.jsonl` of the superseded cut1/cut2 (verified in row 1:
`"task":"[TASK-01]" … "mdl":"[MODEL-1]"`). The full `U0001..U0090` range likewise appears only in that
per-unit file. `METHOD.md` declares all six tag ranges.

**No legend ships.** `verify_claims.py`'s docstring states "ships no legend"; the file contains only tag
lists and claim ids; `record.json`'s `schema` block is the single string `"reduced-neutralised"`; the derived
grep found no tag→identifier map. ✓

## Check 7 — red→green on a copy: CONFIRMED

Copy (real artifact untouched): `scratch/uverel7/verify_claims_redgreen.py`.

| step | result |
|---|---|
| copy as-is vs cut3 | exit **0**, `RESULT pass exit=0 claims=143 failed=0 []` |
| tamper `chk("R4-CHOSEN-OK", 0.700` → `0.999` | exit **1**, `FAIL R4-CHOSEN-OK expected=0.999 got=0.7`, `RESULT fail exit=1 claims=143 failed=1 ['R4-CHOSEN-OK']` |
| restore | exit **0**, `RESULT pass exit=0 claims=143 failed=0 []` |

`md5(scratch/uverel7/verify_claims_redgreen.py) = f0855d9e41b09df895e974feb7597856 =
md5(scratch/urelease7/cut3/verify_claims.py)` after restore — the shipped artifact was not modified.

## Check 8 — what I could not verify (`unverified`)

1. **The provenance pin.** `provenance.json` / `record.json[provenance]` assert the withheld raw input is
   2,267,742 B, 9,260 lines, md5 `3aad1ae29e472ef9f5f54e179510faf5`, sha256 `5732766d…`. The raw record is
   withheld, so the `PROV-BYTES`/`PROV-LINES`/`PROV-MD5` checks only prove internal agreement between the
   record and hard-coded literals in the verifier — not that the withheld file has that digest.
2. **Published values vs the source note.** I re-derived all 143 values arithmetically from the shipped
   record; I did not re-read `GATED_READ_2026.md`/`GATED_READ_REVERIFY.md` to confirm the hard-coded
   "published" expectations are the manuscript's.
3. **§8's process disclosure** ("34 tool calls against a stated bound of 30") is not re-measurable.
4. **`gold_derivation`** counts are internally consistent (pinned `10+1+1 = 12 = stored_only`; live
   `10+1+1+1+1 = 14 = stored_only`) but the derivation script is withheld, so the outcome cannot be re-run.

## Disagreements, classified

- `contradicted`: §2 cut1 `1,572,498` → measured **1,572,249**; §2 cut2 `1,148,991` → **1,148,742**; §2 cut4
  `27,447` → **27,200**; §2/§3 delta cut3→cut4 `1,035 B` → measured **1,033 B** (and §2's own table gives
  786); §2/§3 delta cut2→cut3 `1,120,758 B` → measured **1,120,509 B**; §8 "every number §1–§6 from the run
  that produced §4's md5s" for those three totals.
- `overstated`: §5 "no private schema identifier survives the reduction"; §6 "the only strings … are the
  published values and the uniform tags".
- `not_reproduced`: none — the two sealed figures not reproducing from the rows is the verified claim.
- `unverified`: items 1–4 above.

## Effect on the release decision

None. `scratch/urelease7/cut3/` is exactly the 5-file / 28,233 B set with all five §4 md5s matching, exits 0
with 143 PASS / 5 NOTE / 0 FAIL, and removing `per_task` — and nothing else — flips it to exit 3. The defects
are §2 byte bookkeeping and two over-broad wording claims, not a wrong minimal set.
