# RECORD_REPAIR.md — orchestration record repair

**Unit:** UREC1 · **Date:** 2026-10-15 · **Scope:** repair the `ULIC` orchestration record and sweep for
the same class of defect (missing or broken records). Report only for everything except `ULIC.json`.

**Write paths touched (nothing else):** `orchestration/handoffs/ULIC.json`,
`orchestration/RECORD_REPAIR.md`, `orchestration/units/UREC1.md`, `orchestration/handoffs/UREC1.json`.

---

## 1. `ULIC.json` — the defect, diagnosed

Measured on disk before repair:

| property | value |
|---|---|
| size | **4021 bytes** |
| mtime | `2026-10-15 15:05:39.051182354 -0500` |
| md5 | `5000652a8bd33908c37442b15a5eb8e8` |
| stability | identical md5 across two reads 1 s apart → **stable, not a mid-write artifact** |
| `json.load` | `JSONDecodeError: Expecting ',' delimiter: line 3 column 1 (char 4021)` |

**Delimiter census of the original bytes:** `{` = 2, `}` = **1**, `[` = 17, `]` = 17, `"` = 98.
The brackets balance; **exactly one `}` is missing.**

**Depth trace (strings skipped):** `"evidence"` opens at depth 1; `"blocker"`, `"next_unit_hint"` and
`"write_paths"` each sit at **depth 2**, i.e. *inside* `evidence`. The file's single trailing `}` (at
char 4019) is therefore consumed closing `evidence`, and the **outer object is never terminated** —
which is why the parser still wants a `,` at char 4021 = EOF.

**Raw tail, on the record** (last 130 chars of the original):

```
CHECKLIST.md","papers/encoder-crossover-190/OPEN_QUESTIONS.md","orchestration/units/ULIC.md","orchestration/handoffs/ULIC.json"]}\n
```

### The repair

Insert one `}` immediately after the `commands` array closes, i.e. at the unique occurrence of the
literal `"],"blocker":` → `"]},"blocker":`.

- after: **4022 bytes**, md5 `86e2f2a9306a8bc67d436ddb32d1bf31`, `json.load` succeeds
- top-level keys are exactly the seven contracted: `unit`, `status`, `artifacts`, `evidence`,
  `blocker`, `next_unit_hint`, `write_paths`
- the edit is **one delimiter and nothing else**: verified by
  `fixed[:i] + fixed[i+1:] == original` (strip the inserted char → byte-identical original)

### Why that position, and not an append at EOF

Two insert positions restore brace balance:

1. **before `,"blocker":`** — closes `evidence`; the trailing `}` then closes the outer object. Yields
   the contracted 7-key unit handoff. *(chosen)*
2. **appended at EOF** — the trailing `}` closes `evidence` and the new one closes the outer object,
   but `blocker`, `next_unit_hint` and `write_paths` stay nested inside `evidence`: the record would be
   **missing three required top-level keys**, i.e. a *new* shape gap manufactured by the repair.

The bytes alone cannot distinguish the two readings — both reproduce the observed input. The
disambiguator is the shape contract in `AGENTS.md`, which fixes those three keys at top level. Reading 1
is the only one that recovers the record **without inventing any value**; reading 2 is recorded here
rather than hidden. No field value was altered, added or guessed.

---

## 2. Salvage account — what was recovered

Every contracted field and every evidence member was intact in the malformed bytes and was recovered
**verbatim**:

| field | recovered value |
|---|---|
| `unit` | `"ULIC"` |
| `status` | `"done"` |
| `artifacts` | `["papers/encoder-crossover-190/LICENSE_ANALYSIS.md"]` |
| `evidence` | 9 members, all present (below) |
| `blocker` | `""` |
| `next_unit_hint` | the MANUSCRIPT.md reframe + minimal-reproducibility-subset hint (verbatim) |
| `write_paths` | 5 paths (LICENSE_ANALYSIS.md, CHECKLIST.md, OPEN_QUESTIONS.md, ULIC.md, ULIC.json) |

`evidence` members recovered: `arxiv_options_confirmed` = `"6"`, `irrevocable_confirmed` = `"yes"`,
`tmlr_ccby_confirmed` = `"yes"`, `tmlr_conflict` = `"yes"`, `lab_papers_checked` = `"5"`,
`lab_licences_observed` (5 entries), `agpl_confirmed` = `"yes"`, `unverified` = `"9"`, and `commands`
(**11 command records**, all verbatim).

**`fields_unrecoverable`: `[]` — zero.** Nothing in this record needed to be marked unrecoverable; the
failure was structural, not informational. Recorded explicitly so the gap set is auditable:
`"fields_unrecoverable":[]`, `"ulic_fields_unrecoverable":"0"`.

*Note (not a gap):* `artifacts` names the one deliverable while `write_paths` names five paths. That
asymmetry is ULIC's own writing and is preserved as-is; the array is properly closed in the original
bytes, so nothing was lost there.

### Why `status: "done"` is justified (recovered, not assigned)

`orchestration/units/ULIC.md` states **Status: done** with **Blockers: none**, and all three named
artifacts exist on disk:

| artifact | size |
|---|---|
| `papers/encoder-crossover-190/LICENSE_ANALYSIS.md` | 42249 bytes |
| `papers/encoder-crossover-190/CHECKLIST.md` | 15136 bytes |
| `papers/encoder-crossover-190/OPEN_QUESTIONS.md` | 11412 bytes |

---

## 3. Re-parse sweep of every `orchestration/handoffs/*.json`

| pass | files | parsed OK | invalid |
|---|---|---|---|
| before repair | 271 | 270 | **1** (`ULIC.json`, stable) |
| after repair | 271 | **271** | **0** |

The orchestrator's measurement is **confirmed exactly**: `ULIC.json` was the only invalid handoff, and
no second silently-broken record exists.

**Guard test (green):**

```
PYTHONPATH=src python3 -m pytest tests/test_orchestration_handoffs.py -q
13 passed in 2.46s
```

(An initial run without `PYTHONPATH=src` failed at collection with
`ModuleNotFoundError: No module named 'resextract'` — a harness path issue, not a handoff defect;
the guard itself passes.)

---

## 4. Missing records of the same class (report only — nothing reconstructed here)

### 4a. Unit cards with **no** matching handoff — "died without handoff": **1**

| unit | card | status in card | artifacts that exist | disposition |
|---|---|---|---|---|
| **U1.7** | `orchestration/units/U1.7.md` | *in progress* | `src/resextract/kg/policy.py` (24920), `tests/test_kg_policy.py` (14384), `config/targets.toml` (2540), `docs/TARGET_POLICY.md` (6299), `state/logs/U1.7-policy.py.bak`, `state/logs/U1.7-red-green-A.txt`, `state/logs/U1.7-red-green-B.txt` | **superseded** by `U1.7R`, whose handoff exists and carries a `supersedes` key — the record likely closes by supersession rather than needing reconstruction |

**This is the only card-without-handoff in the workspace** (258 cards, 271 handoffs).

### 4b. The four previously-dead units named in this unit's brief

| unit | card | handoff | note |
|---|---|---|---|
| `UPIPE` | yes | **yes** (valid, unit shape) | record present |
| `UCORR2` | yes | **yes** (valid, unit shape) | record present |
| `UCONS2` | yes | **yes** (valid) | self-declares reconstruction (UFINAL2) |
| `JOB7b` | **no** | **no** | **still has no record of either kind** — the brief's claim that UFINAL2 reconstructed it does not hold on disk: there is no `JOB7b.json` and no `JOB7b.md`. It is referenced as “failed twice and delivered nothing” in `jobs/MASTER_SHORTLIST.md:323` and `:395–429`, which also notes the disk disagrees and that the coverage repair “is still owed”. |

### 4c. The reverse gap — handoffs with **no** card: **14**

`U0.14`, `U0.19`, `U0.1b`, `U2.5`, `U6.10`, `U6.14`, `U6.19`, `U8.49`, `U8.50`, `V2T`, `V5F`, `V6E`,
`V6F`, `V8D`.

**Nothing in this section was written.** Reconstruction of `U1.7` / `JOB7b` is a separate unit's job.

---

## 5. Shape confirmation (step 5)

Across the 271 handoffs: **206 unit-shaped** (`status`, no `overall`), **64 verdict-shaped** (`overall`,
no `status`); 29 carry both keys. **Zero verdict-shaped handoffs are missing a core key.**

**Flagged, deliberately NOT rewritten** (per `AGENTS.md`: a verdict-shaped handoff is not a defective
unit report, and rewriting it would mean inventing values nobody wrote):

- **`UVER1`–`UVER7`, `U8.72`** — verdict-shaped but carrying a non-`V` unit name. The *shape* is correct
  for verifier work; only the naming convention differs. Flagged for classification, not repair.
- **`V4R`, `V5F`** — `V`-named yet **unit-shaped** (no `overall`). A genuine name/shape mismatch,
  flagged rather than converted into either shape.

**Pre-existing recorded gaps (frozen baselines, report only — not touched):** unit-shaped handoffs
missing contracted keys — `U0.22` (`blocker`, `next_unit_hint`, `write_paths`), `U6.16` (same three),
`U3.2` (`write_paths`), `U6.17` (`write_paths`), `V4R` (`evidence`), `V5F` (`artifacts`, `evidence`).
These predate this unit and are not part of the defect class repaired here.

---

## 6. Verdict of this unit

`ULIC.json` is **valid**, in the contracted unit shape, with **zero invented values** and **zero
unrecoverable fields**. The sweep found **no other invalid handoff**. One card still lacks a handoff
(`U1.7`, superseded) and one named dead unit has no record at all (`JOB7b`).
