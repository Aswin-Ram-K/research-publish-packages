# UVER3 — independent verifier of `second-labeller-190` (UEXP)

**Role:** verifier, not author. **Verdict: `pass-with-corrections`.**
**Bound:** 55 tool calls; used 24 (21 investigative + 3 writes). No blocker.
**Write paths:** `strategy/VERIFICATION_REPORT_3.md`, `orchestration/units/UVER3.md`,
`orchestration/handoffs/UVER3.json`. Nothing else touched; `/home/zer0null/Duval` read-only.

## What was checked

Re-ran UEXP's pipeline in a `/tmp/uver3b` **copy** (so UEXP's artifacts were never rewritten):
`parse_fixture.py`, `characterise.py`, `compare.py`. All six regenerated artifacts are byte-identical
to UEXP's originals. Re-hashed the target fixture and `cmp`-ed it to UEXP's sandbox copy. Wrote my own
**independent** parser (TypeScript object-literal → JSON transform, **no bracket regex**), compared its
190 records field-for-field against `cases.json`, reproduced the D-P1 naive-regex defect, and
recomputed pooled + per-kind agreement/κ from `labelsB.json` with independent code. Opened all four
flagged fixture cases and the owed documentation correction in the raw text (target + corpus).
Re-read target HEAD / porcelain / reflog and swept mtimes for target writes.

## Results

- Hash, copy identity, target immutability, parser counts (190/721, arity 2–5), ESCALATE = 28 vs the
  header's independent 28 (regression **not** fitted to the header), 0/190 answer-outside-option-set,
  0 dup ids, 0 malformed, κ = 0.901358484035649 / po = 0.905263… / pe = 0.039584…, all **7** stratified
  κ, and all five flagged items → **verified**.
- D-P1 verified in the strong sense: the naive regex produces **exactly one** false hit
  (`context.package-014`), and the final 0/190 survives a parser with no bracket regex at all.
- **No claim contradicted.**
- `overstated` (3): the "corroborates `F-EXP11-11`" wording (fixture authoring vs EXP#11 model
  answers — different referents); `metrics.json` carrying κ with no limitation, contrary to
  `PREREGISTRATION.md:12–16`; the "191st `id:` match" ordinal slip (it is the first by line order).
- `not_reproduced` (2): the **14:28:31** timestamp on the 8 `.git/objects/` writes (I see the same
  shape at **14:38:30**, post-window — misreport and post-observation rewrite both remain open); the
  `_before` half of the read-only proof (not re-observable; after-side + reflog + 12-day-old fixture
  mtime corroborate it instead).
- `unverified` (2): Route B's *blindness* (its result is checkable, its "opened no other file"
  self-report is not — no transcript in the artifact set); the stood-down second model pass (no file).

## Rulings

- **§6 adjudication:** unblinded judgement, correctly disclosed as *"a reasoned reading, not a
  measurement"* (`EVIDENCE.md:199–201`); no artifact presents it as measurement (`metrics.json`
  contains no adjudication field; `disagreements.jsonl` rows carry none). Pass.
- **Read-only proof:** HEAD `907fa39…` unchanged; reflog shows no HEAD move since 12:51:58; porcelain
  identical. UEXP's *"attribution by exclusion, not a direct proof of the writer's identity"*
  (`EVIDENCE.md:360`) is correct and endorsed — attribution by exclusion cannot identify the writer.
- **Limitation coverage:** present in `EVIDENCE.md`, `RUN.json`, `PREREGISTRATION.md`; **absent from
  `metrics.json`**, the one artifact carrying κ bare.
