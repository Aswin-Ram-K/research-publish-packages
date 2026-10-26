# CASE_VARIANT_SETTLEMENT — UNEUTRAL10

Settles the survivors the independent verifier (`strategy/VERIFICATION_REPORT_32.md`) found in the
whole-class sweep. Tree worked on: `scratch/uneutral10/package/` (copy of `scratch/uneutral9/package/`,
29 files). Source tree untouched.

## 1. Re-derived survivor list, case-insensitive, 29 files (my own scanner, 33-token class)

| bucket | before | after |
|---|---|---|
| TOTAL occurrences | 1349 | 1339 |
| inside stimulus (`question`/`options`/`situation` values) | 939 (distinct 11) | 933 (distinct 10) |
| outside stimulus | 403 | 399 |
| JSON object keys | 7 | 7 |

Before, by token: STEP 728 (step,Step), GRANT 213 (grant), ANSWER 175 (Answer,answer,ANSWER),
ESCALATE 131, RETURN 24 (return,Return), SINGLE 20, DROP 14, MATERIALISE 14 (materialise),
REPLAY 8, SEQUENCE 8, broker 8 (`Broker`), CONTINUE 4, DISCARD 1 (`Discard`), PERSISTENT 1.
The verifier's smaller figures (step 471, grant 131, Answer 87, …) come from its narrower
stimulus scoping; mine are the wider lexical re-derivation and are the numbers used below.

Residual **census** with the earlier units' scanner (`scratch/census_*.py`, 184-id authority):
before **83** (inside **26** / distinct **2** / outside 57 / keys 0, 19 ids) →
after **75** (inside **20** / distinct **1** / outside 55 / keys 0, 18 ids).
The in-stimulus residual was genuinely **2 distinct**: `MATERIALISE` and `broker`.

## 2. Classification (quoted sentences the calls rest on)

**(a) system name — neutralised**
- `Broker` — "an in-process Broker" inside a `situation` value; title-case, and its lowercase twin
  `broker` is already a renamed role token. 8 occurrences / 4 files.

**(b) ordinary English — deliberately left**
- `materialise` — "the linkage does not materialise" / "materialised on the next call". English verb;
  the 20 census in-stimulus hits are `materialise|materialised|materialises` (my identifier-boundary
  count inside stimulus is 11). Ambiguous (also a system action name) — decided **leave**, because it
  is lowercase, grammatical in every sentence that carries it, and rewriting 11 stimulus sentences
  would change the meaning the route-A rule is scored on.
- `Answer` — "Answer or escalate?" sentence-initial common noun, 116 hits, all English. Left.
- `step` 728, `grant` 213, `escalate` 131, `return` 24, `single` 20, `drop` 14, `replay` 8,
  `sequence` 8, `continue` 4, `Discard` 1, `persistent` 1 — read in their sentences ("one step at a
  time", "grant access", "escalate to a human", "single label", "drop the frame"); ordinary English
  in every instance. Removing any would rewrite the paper's meaning.
- `Step` / `Return` title-case forms are sentence-initial or heading-initial English, not names.

**(c) the package's own harness names — left**
`EXP#12`, `reflex-decisions(.ts)`, `fixture-190.json`, `parse_fixture.py`, `analyze.py`,
`evaluate.py`, `typed-channel`, `tools/typed-channel`, `DECISION_CASE_SCHEMA.ts`, `DecisionCase`,
`DecisionKind`, `nKind`, `EXCLUDED.md`, `INTEGRITY.md`,
`EXP12-typed-channel-comparison-prereg.md` — filenames/identifiers of the shipped generic harness,
not the author's parameter space.

## 3. Rename scheme (held in memory only, never written/logged/shipped)

One consistent injective mapping, derived by UNEUTRAL9's own deterministic rule
(`sorted(set(ROLES+ENUMS+FRAGS), key=(-len, token))` → `G01…G31`), longest-first, **case-sensitive**:
`Broker` was folded onto the **existing** tag its lowercase twin already used. 8 occurrences in
4 files (`fixture-190.json` 2, `cases.json` 2, `blinded_cases.json` 2, `reflex-decisions.ts` 2).
Surviving `ANSWER` at `verify/recompute-claims.py:117` was in a **comment**, so it was reworded, not
tagged: `e.g. ANSWER/answer and changes` → `e.g. an upper/lower-case pair and changes`.

## 4. Trap check — did any published number move?

Measured, not assumed. `verify/recompute-claims.py` (exit 0), `second-labeller/parse_fixture.py`
(exit 0, output byte-identical before/after) and `second-labeller/compare.py` (exit 0, metrics
byte-identical) — **no diagnostic moved**. `compare.py` re-derives route A from the `question`/
`options` text with `TOKEN = [a-z0-9]+` over `s.lower()` (`compare.py:16,21,27,31`), so the case
fold was exercised: the two stimulus sentences containing `Broker` did change tokens, and no label,
tie or κ moved.

All diagnostics, identical before and after:
route A `kappa=0.3248813212427869`, `agreement=0.34210526315789475`, `pe=0.025512465373961218`,
`exact_index_matches=65`, `ties=141`, `zero_score_cases=89`;
route B (`.passes["labelsB.json"]`) `kappa=0.9013584840356494`, `agreement=0.9052631578947369`,
`pe=0.03958448753462604`, `exact_index_matches=172`, `n_disagreements=18`,
`AB_mutual_agreement=0.3684210526315789`, `disagreements_where_routeA_backs_record=4`;
closed-vocabulary κ `0.8837023738280471` (106 cases), roster-and-bespoke κ `0.9139973672663448`
(84 cases); parse `cases=190`, `options_total=721`, failures 0;
fixture-correctness digest `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`.

**No value moved, so UNEUTRAL10 creates no new paper delta.** Standing (pre-existing, declared)
deltas remain, and are cited in the paper directory **including `submission/main.tex`**:
- A/B mutual agreement published `0.3526` vs tree `0.3684210526315789` (`reproduced=False`) —
  `CLAIMS.md:109`, `submission/main.tex:335`, `MANUSCRIPT.md:633`, `LIMITATIONS_UPDATE.md:245`,
  `VERIFIER_CORRECTIONS.md:139`, `EVIDENCE_NOTES.md:279`, `DISCLOSURE_CHANGES.md:143`.
- route-A κ published `0.3252` vs tree `0.3248813212427869` (within 5e-4) — `CLAIMS.md:108`,
  `submission/main.tex:195` and `:335`, `MANUSCRIPT.md:381,633`, `GAPS.md:19`,
  `EVIDENCE_NOTES.md:280`, `LIMITATIONS_UPDATE.md:245`, `VERIFIER_CORRECTIONS.md:139`.
Paper files were **not** edited; these are reported, not applied.

## 5. MANIFEST regeneration and proof

Regenerated from disk with the package's own procedure (`scratch/urecut1/build.py:94-137`). The
procedure was first validated: run against the *unmodified* copy it reproduced the shipped
`manifest_self` and `counts.bytes_total = 829435` exactly. After this unit's edits:
`counts.files = 29`, `bytes_total = 829422`,
`manifest_self = 5acbb952a4deff080509e4b8edf0a48901a68737c09b8e7d85d515af05466d84`.
Self-exemption convention: `MANIFEST.json` excludes itself from the per-file entries and from
`bytes_total`, while `counts.files` counts it (28 listed + manifest = 29).

Independent re-hash checker (`scratch/uneutral10/mfcheck.py`, written for this unit):
`missing=0 hash_mismatch=0 size_mismatch=0 listed_but_absent=0 unlisted=0`,
`manifest_self_recomputes=True` under the convention *blank `generated_utc`, drop `manifest_self`,
`json.dumps(sort_keys=True, indent=2)`, sha256 hex*.
Idempotence: built twice, byte-identical apart from `generated_utc` — **True**.

## 6. What remains

Under a case-insensitive scan the tree is **not** at zero: my broad-class scanner still counts 1339
occurrences (933 in-stimulus), the census 75 (inside 20 / distinct 1). Reasons are in §2 — the only
in-stimulus survivor is the ordinary English verb `materialise`; everything else is lowercase
English or the harness's own filenames. **Plainly:** the package no longer contains any of the
author's system *names* — no title-case branded component, no `ANSWER` enum form, no
parameter-space vocabulary in the stimulus — but it is **not** literally free of case-insensitive
hits, and the residue (`materialise`, plus `step`/`grant`/`escalate`/`answer`/`sequence`/`replay`/
`drop`/`return`/`single` and the harness filenames) is deliberately retained because removing it
would rewrite the paper's meaning.

## 7. Author decision — deliberate residue, retained as an easter egg (2026-10-16)

**Author decision, recorded 2026-10-16.** The author was asked whether the residual lowercase
ordinary-English words surviving in the stimulus should also be absorbed. He answered, verbatim:

> "leave it there - might eb small easter egg for whats to come and i want it recorded on our side as notes that we left in it as an easter egg"

(Reproduced exactly as given, including `eb` and `whats`; attributed to the author, dated
2026-10-16.)

**Ruling.** The residual words are **deliberately retained, not an oversight**. The author frames
them as a small signature of what is to come — an "easter egg" — and asked that our side record
that we left them in on purpose.

**What is left** (counts as measured by UNEUTRAL10 — quoted here, not re-derived):

| residual | count |
|---|---|
| `step` | 728 |
| `grant` | 213 |
| `escalate` | 131 |
| `Answer` | 116 |
| `return` | 24 |
| `single` | 20 |
| `drop` | 14 |
| `replay` | 8 |
| `sequence` | 8 |
| `continue` | 4 |
| `Discard` | 1 |
| `persistent` | 1 |
| `materialise` (verb) | the sole in-stimulus survivor |

`Answer` 116 is **sentence-initial English** — the stimulus sentence "Answer or escalate?" — and is
**not** the `ANSWER` enum form. Under the census class, `materialise` is the only in-stimulus
survivor.

**What was NOT left.** Every branded / title-case name, kind, role, state and record field name has
been removed from the package by units UNEUTRAL6/8/9/10.

**FINAL numbers — nobody re-opens the question.** route A κ `0.3248813212427869`; route A agreement
`0.34210526315789475`; A/B mutual agreement `0.3684210526315789`;
`disagreements_where_routeA_backs_record` 4; route B κ `0.9013584840356494` **unchanged**;
fixture-correctness digest `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`
**unchanged**.

**Cross-references:** `strategy/WHOLE_CLASS_NEUTRALISATION.md`,
`strategy/STIMULUS_NEUTRALISATION.md`, `strategy/VERIFICATION_REPORT_32.md`.

**Effect.** This decision is what makes the release numbers final and unblocks the paper alignment.
