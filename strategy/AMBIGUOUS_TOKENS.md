# AMBIGUOUS_TOKENS.md — adjudication of `no-union` and `LEAD`

**Unit:** UAMBIG1 (report only; no rename performed and no rename schedule proposed).
**Release tree examined:** `scratch/ubij3/tree-three-r2` (read-only).
**Read-only acceptance target examined:** `/home/zer0null/Duval` (plain file reads only; no writes, no git command of any kind).
**Source question:** `strategy/NONCENSUS_CLASSIFICATION.md` classified both tokens as **(d) ambiguous** and deliberately refused to rename on a guess. This unit supplies the missing evidence.

---

## Verdict summary

| token | occ / files (tree) | verdict | one-line reason |
|---|---|---|---|
| `no-union` | 14 / 3 | **NEUTRAL — may stay** | Not target vocabulary at all (0 hits in the target); names a release-side *ablation variant* whose referent (the enumerated S12 union) is already shipped and recorded as disclosed. |
| `LEAD` | 4 / 3 | **NEUTRAL — may stay** | All four occurrences are the filename `LEAD-WIRING.md`; in the source project `LEAD` denotes the **Lead role** (governance/operator), absent from the mechanism scheme, and the released paper package already names `LEAD-WIRING.md`. |

Neither token is a filename-bearing leak that needs neutralisation. Renaming either would *delete no leak* and would break published/committed cross-references (see "FileName warning" below).

---

## 1. `no-union` — NEUTRAL, may stay

### 1.1 The target's own vocabulary: absent
- `grep -rn -i -e 'no-union' -e 'no union' -e 'no_union' /home/zer0null/Duval` → **no matches**.
- `glob **/*no-union*` under `/home/zer0null/Duval` → **no files**.
- The target *does* use `union` 373 times, but 250 of those hits are generic TypeScript prose: e.g. `tools/selfbuild/dispatch.ts:86`, `tools/selfbuild/admission.ts:138` ("A closed union of the ABSENCES admission can report"), `tools/abstraction/compose.ts:81` (`export function unionOfGrants`), `evals/drift.ts:686` (`function unionValues(source, name)`), `src/state.ts:205`, `docs/DECISION_LOG.md:124`. The target never names anything `no-union`.

**Reading:** `no-union` is *not* recovered private-repo vocabulary. It is a name the release/sanitisation stage invented for a packaging variant.

### 1.2 What it actually is (in-tree definition)
`scratch/ubij3/tree-three-r2/variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts` (30 lines) defines it in its own header:
- `:8` `// VARIANT B (no union): the enumerated S12 union is removed; the type name is kept as an alias.`
- `:9` `// See variants/no-union/README.md for the trade.`
- `:10-:14` five `// [withheld: the enumerated S12 union — see variants/no-union/README.md]` markers
- `:15` `export type S12 = string;`
- `:17-:27` the `S02` interface re-exports the whole decision-case shape (id, kind: S12, question, options, correct, rationale, namespaces).

Its two members are the only files in the variant tree: `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts` and `variants/no-union/files/fixture/reflex-decisions.ts` (both headers read "Neutralised decision fixture (NEUTRAL-TAG/v1). Code-agnostic extraction: every project-level identifier has been replaced by an opaque tag…"). `variants/no-union/README.md` does **not** ship — it is listed as removed in `verify/redaction-log.json:12` and `:134`.

All 14 occurrences / 3 files:
- `MANIFEST.json:34` (amended_by prose: "…both `variants/no-union/files/fixture/*.ts` added"), `:411` path, `:412` source, `:419` path, `:420` source;
- `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts:8-14`;
- `verify/redaction-log.json:12`, `:116` (`"variant": "no-union"`), `:134`.

### 1.3 The thing it names is already shipped and already public
- The **non-variant** copy `fixture/DECISION_CASE_SCHEMA.ts` ships the enumerated `export type S12 =` union; the 184-identifier census locates the seven member literals in that file at `:9`–`:15` (`worker.class`, `context.package`, `capability.family`, `memory.admission`, `escalation`, `topology`, `acquisition`).
- `strategy/WITHHELD.md:107` records the register row for it: `| M11 | Decision taxonomy and kernel namespaces (DecisionKind union; the six namespaces) | withhold — and already partially in the release set …` with the corrected disclosure status settled at `:213,:320,:375,:452` ("M11 is **disclosed** (§8.9)").
- So `no-union` names the ablation of an **already-disclosed** union; the token carries no mechanism content the release does not already state in shipped bytes.

### 1.4 Withheld-mechanism scheme membership: none
`strategy/CODE_AGNOSTIC_RELEASE_POLICY.md` enumerates the mechanism scheme. `no-union` appears in **none** of: §A.2.1 `kind` values, §A.2.3 capabilities, §A.2.4 roles, §A.2.5 "Mechanism symbols and API fragments (30 identifiers — StateClass, grantPolicy, broker, LintSideSpec, DecisionKind, DecisionCase, ToolCallIR, …)", §A.2.7 project-specific file names. Its only workspace appearances are `strategy/COHERENT_BIJECTION_EXTENSION_2.md:268` ("`no-union` ablation label") and the shipped `MANIFEST.json` / `verify/redaction-log.json` records.

### 1.5 Released paper
`grep -rn -i -e 'no-union' -e 'no union' -e 'no_union' papers/` → **0 occurrences anywhere under `papers/`**, and 0 in `papers/encoder-crossover-190/MANUSCRIPT.md`. (Neither public nor leaked by the paper.)

---

## 2. `LEAD` — NEUTRAL, may stay

### 2.1 All four tree occurrences are one filename
`grep -rn 'LEAD' scratch/ubij3/tree-three-r2` → exactly **4 occurrences / 3 files**, and every one is the filename `LEAD-WIRING.md`:
- `harness/collect.py:372` — "believe they are committed when they are not. See `LEAD-WIRING.md` §4."
- `MANIFEST.json:86` — `"path": "harness/LEAD-WIRING.md"`
- `MANIFEST.json:87` — `"source": "git:an unmerged development branch commit (id withheld):tools/typed-channel/LEAD-WIRING.md"`
- `verify/redaction-log.json:64` — `"file": "harness/LEAD-WIRING.md"`

The shipped file `harness/LEAD-WIRING.md` is 42 lines; its body **never contains the string `LEAD`**. Its title is `:1` `# D38 — wiring notes (sanitised)`, with a UREDACT1 withheld-by-policy note at `:3-:8`, `:21` `## 3. `D09` is subsumed by the lint`, `:34` `## 5. … (D08; digests recorded in `../D63`)`, `:42` `See `../D43` section 4`. So there is no in-tree *definition* of `LEAD`; the only in-tree evidence bearing on it is `MANIFEST.json:87`, which shows the private path it was recovered from: `tools/typed-channel/LEAD-WIRING.md`.

### 2.2 What the prefix denotes in the source project: a role, not a mechanism concept
The read-only target holds the same document by the same name: `/home/zer0null/Duval/docs/research/EXP#12-evidence/LEAD-WIRING.md` (141 lines):
- `:1` `# EXP#12 — what the Lead must wire, and what must NOT be wired`
- `:3` `The build lane does not edit `package.json` or `.github/workflows/` (Lead-owned).`
- `:8` `**Wire the OFFLINE lint only** (`exp12`). **Do NOT wire the training or evaluation**`
- `:19` `"exp12": "./scripts/run.sh tools/typed-channel/lint.ts --demo",`

So `LEAD` denotes **the Lead** — the orchestration/operator role that owns `package.json` and CI. It is not an acronym, not a pipeline stage, and not a mechanism concept. Consistently, the target uses `LEAD` 135 times as exactly that role: `docs/PAUSE_STATE.md:32` ("LEAD — plans, delegates, verifies, runs `npm run ci`, merges, pushes"), `docs/BOARD.md:78` ("THE LEAD"), `docs/DECISION_LOG.md:6499` (D-130 "THE LEAD HANDOVER: a new session drives the build"), `tools/selfbuild/controller.ts:46` ("A LEAD RULING, BINDING HERE"), `docs/LEAD_SESSION_REGISTRY.md`. The target's own decision register is the `D-0NN`-padded register; no entry names `LEAD` as a mechanism object.

### 2.3 Withheld-mechanism scheme membership: none
The mechanism's roles (census §A.2.4) are `verifier`, `editor`, `reasoner`, `attached`, `detached`, `output-only`, `code-inspector`, `memory-curator`, `researcher`, `critic`, `code-review`. The **Lead** is the build-lane operator that governs the project, not one of the mechanism's roles; `LEAD` is likewise absent from §A.2.1 kinds, §A.2.3 capabilities and §A.2.5 mechanism symbols. `strategy/WITHHELD.md` has no row for it.

### 2.4 The released paper package already names it
- `papers/encoder-crossover-190/AVAILABILITY.md:22` — "[evaluation harness + frozen inputs] `harness/` — 18 files, including `tccommon.py`, `tcmodel.py`, the six Python steps, the two TypeScript steps, `data/`, `README.md`, `LEAD-WIRING.md`". The same file declares at `:3` "This paper is public under **CC BY 4.0** (author decision, 2026-10-15)" and at `:33-:35` that the harness was "recovered from an unmerged development branch (name and commit withheld), and `tools/typed-channel/` does not exist on trunk".
- **Precision:** `papers/encoder-crossover-190/MANUSCRIPT.md` itself contains **0** occurrences of `LEAD` (grep over the file returned nothing). The name is published by the paper's companion availability statement, not by the manuscript body. That is still the released package, and it is the same rule that exonerated `H-A`/`typed-channel` (named by `MANUSCRIPT.md`).
- The only other `LEAD` hits under `papers/` are `papers/gated-read-batching/GAPS.md:105`, `:134`, `:181` — `ULEAD1`, a workspace unit name, i.e. a different referent.

### 2.5 Workspace treatment
`strategy/SHIP_SET_INTEGRITY.md:120-124` already records it among "The genuinely un-renameable shipped names named in §5 — the preregistration, the two `tc*` modules, `variants/no-union/`, `LEAD-WIRING.md` — are unaffected and remain visible as names." `strategy/NONCENSUS_CLASSIFICATION.md` (the report that refused to guess) likewise notes it as un-renameable.

---

## FileName warning (both tokens appear in paths)
Neither token needs renaming, but if a later owner were to neutralise either, each is a **path** change with these consequences:

- `harness/LEAD-WIRING.md` — cited by `harness/collect.py:372`, `MANIFEST.json:86` and `:87`, `verify/redaction-log.json:64`; published by `papers/encoder-crossover-190/AVAILABILITY.md:22`. Renaming breaks the paper's published availability table and the harness manifest.
- `variants/no-union/` (4 directory entries: `variants/`, `variants/no-union/`, `variants/no-union/files/`, `variants/no-union/files/fixture/`) — cited by `MANIFEST.json:34`, `:411`, `:412`, `:419`, `:420`, `verify/redaction-log.json:12`, `:116`, `:134`, and by the five comment lines `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts:10-14` that point at `variants/no-union/README.md`. `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md` §A.2.7 already files the tree's file names as incidental project references.

## Blockers
None. Both questions are answerable from shipped bytes plus plain file reads of the read-only target.

## Residual (recorded, not a verdict change)
If the redaction owner's rule is "no shipped byte may gesture at the withheld kernel at all", then the offending bytes for `no-union` are the *sentence* at `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts:8` and the five `[withheld: …]` markers at `:10-:14` — plus the very existence of the variant — not the token name. That is a disclosure-policy decision already recorded in `strategy/WITHHELD.md:107` as M11 "disclosed (§8.9)", and it is outside this unit's remit (report only).
