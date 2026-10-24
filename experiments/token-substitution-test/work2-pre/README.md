# `encoder-crossover-190-SANITISED` — the sanitised reproducibility subset (EXP#12 / paper #3)

**This directory is the publishable copy of `repro/encoder-crossover-190/`.** It exists because UTS1
(`strategy/TRADE_SECRET_AUDIT.md` §4.3, §5.2) found that the as-audited subset shipped kernel **mechanism** —
the complete `DecisionKind` union, the six kernel namespaces, and 335 mechanism-narrating lines of fixture
rationale — inside an already-announced release. The as-audited subset is preserved byte-for-byte next to it and
is **not** modified.

**Read [`REDACTION_REPORT.md`](REDACTION_REPORT.md) first.** It carries the leak inventory before/after, exactly
what was redacted, the acceptance test with verbatim commands and outputs, the reproducibility cost, the
`DecisionKind` trade (both variants), and the residual-term scan. This README is the operator's view.

**The measurement is unchanged.** All **nine** values in `papers/encoder-crossover-190/CLAIMS.md` — `0.3474`, `0.4526`,
`0.2911`, `0.6684`, `0.6789`, `0.3252`, `0.8837`, `0.9140`, `0.3526` — are accounted for: **eight** recomputed from
inside this tree and one (`0.6684`) a **quoted published constant**, not a recomputation (declared in §8 and in
`verify/recompute-claims.py`). The paired table `39 + 27 + 90 + 34 = 190` recomputes exactly. Nothing moved. Re-run
`python3 verify/recompute-claims.py` to see it.

---

## 1. Which variant is this?

**VARIANT A — the `DecisionKind` union is KEPT** (the paper's "typed single-label" claim is preserved), with its
mechanism comments stripped. A labelled alternative that removes the union is in
[`variants/no-union/`](variants/no-union/README.md); the trade is assessed in `REDACTION_REPORT.md` §6 and it is
**the author's call**, not this unit's.

## 2. What was withheld, and what it costs

| withheld | why | what a reviewer loses |
|---|---|---|
| every case `rationale` (value emptied, key kept) | review notes written to justify each label against the withheld system's semantics; the schema itself records *"used in review, not fed to the model"*, so they cannot affect a number | the stated reasoning behind each recorded label; the verbatim quotes behind four flags in `second-labeller/OWED_CORRECTIONS.md`; the case-by-case audit of the instrument's self-containment claim |
| every `namespaces` value (emptied, key kept) | the six kernel namespaces are the kernel's decision surface | the namespace dimension of each case |
| the fixture header comment and the inline union/interface comments | they named the kernel's internal type, policy and API vocabulary, two private `src/*.ts` paths, the namespace list and the enforcement rule — the term-by-term inventory is in `REDACTION_REPORT.md` §7 and [`RESIDUALS.md`](RESIDUALS.md) | the instrument's own account of *how it grows* and of its three 2026-10-01 errata |
| rationale text quoted verbatim in `second-labeller/{EVIDENCE.md,OWED_CORRECTIONS.md}` and kernel identifiers in `RUN.json` | those quotes reproduce the withheld text, defeating the redaction | the quoted evidence for the flags (the sanitised ledger says so in place) |
| the private-repo map in `harness/LEAD-WIRING.md` (141 → 42 lines) | the original carried the private `npm run suite` script list, the CI job matrix, repo-policy gate text and internal decision numbers — a map of the private tree, not of the measurement | nothing needed to reproduce EXP#12; the wiring recommendation survives in full |

**The cost is material to reviewability and immaterial to the claims** — `REDACTION_REPORT.md` §5 states it
without softening.

## 3. What is NOT fixed by this redaction — read this before release

The instrument's **`question` text names internal mechanism in 47 of the 190 cases** (the kernel's type and
policy-grant vocabulary, and 10 private `src/*.ts` path mentions), and two option labels name internal primitives
(an API-call fragment and an internal list reference). Those fields **are the model input**: editing them
would change what every arm saw and therefore every accuracy. **They are irreducible by redaction.** The rationales
were never the largest disclosure surface; the questions are. Removing *that* means re-authoring the instrument and
re-running every arm — a new experiment, not a redaction. `REDACTION_REPORT.md` §7 and [`RESIDUALS.md`](RESIDUALS.md)
classify every residual strict-mechanism line, each figure with its scope stated (instrument files vs the whole
shipped tree) instead of as one number.

## 4. The one check that had to change, and the check that replaces it

```bash
# (A') the invariant that survives a value-level redaction — run from this directory
cd repro/encoder-crossover-190-SANITISED
sha256sum fixture/reflex-decisions.ts
# 751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae   <- sanitised bytes
# the as-audited bytes were 076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796
python3 verify/recompute-claims.py     # prints the scoring-projection digest and every CLAIMS number
# scoring projection (id,kind,question,options,correct) ==
#   57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300   (identical to the as-audited tree)
```

`076164ac…` is the **pre-registration's** digest and it cannot match: it is the digest of bytes that necessarily
changed. `export-fixture.ts` / `lint.ts` assert it and will refuse on a sanitised checkout — recorded as a
reproducibility cost, not hidden (`REDACTION_REPORT.md` §5, item 4). The authoritative replacement is the
**scoring-projection digest** above, which is identical before and after.

## 5. Reproducing this redaction and its verification

```bash
cd repro/encoder-crossover-190-SANITISED
python3 redact.py                    # rebuilds the sanitised tree from the as-audited original; refuses rather
                                     # than redacting blind; writes verify/redaction-log.json
bash verify/run-verification.sh      # copies both trees to /tmp, runs the same shipped commands in each, diffs
python3 verify/recompute-claims.py   # every CLAIMS number, recomputed from inside this tree
```

`run-verification.sh` never executes anything inside the as-audited directory — it works on `/tmp` copies — and it
covers: instrument digests, the scoring projection, `prepare.py` (stdout identical, `train.jsonl`/`dev.jsonl`
byte-identical), the second-labeller `parse_fixture.py` + `compare.py` re-run, the chance floor, `metrics.json`
equality, the `disagreements.jsonl` delta (only `recorded_rationale` differs, now empty), and the residual scan.

## 6. OPERATIONAL RULE — release by fresh export, never by pushing an existing tree

**Verified, not assumed.** In the target repo the branch the harness was recovered from is **closed and unmerged**
(`git merge-base --is-ancestor … HEAD` → not an ancestor), yet its commit and blobs are fully present in the object
store, and `git hash-object` of this subset's `harness/{analyze,tccommon,train}.py` **equals** that branch's blob
hashes at `tools/typed-channel/…`. The released bytes *are* those historical blobs. **The commit id itself is withheld
from this release** — the branch is private and force-rewritten, so a commit id would leak private-history structure
and could not be resolved by any reader outside the private repository anyway. What stands in its place is per-file
content identity: the sha256 of every file as shipped ([`INTEGRITY.md`](INTEGRITY.md) §1) and the `source_sha256`
recorded for each recovered harness file in `MANIFEST.json`. See `REDACTION_REPORT.md` §8.1 for the trade-off.

> **Release this subset as a fresh export into a brand-new repository.** `cp -r` (or `git archive`) from
> `repro/encoder-crossover-190-SANITISED/` into a new directory, `git init`, one commit. **No** `git clone`, **no**
> `git push`, **no** `.git` carried over, **no** shallow clone of the private repo, **no** subtree/submodule. The
> release repository's history must contain nothing reachable from that branch or any other private branch.
> **Corollary:** do not commit this sanitised tree into the private repository and export from there — that puts the
> sanitised files into the private object store and invites exporting the private history instead.

There is **no `.git` directory, no packfile, no `.idx`, no bundle and no `packed-refs`/`ORIG_HEAD` in this tree** —
verify with `find repro/encoder-crossover-190-SANITISED \( -name .git -o -name '*.pack' -o -name '*.idx' -o -name
'*.bundle' \)` (no output). Nothing here is a copy of a repository; it is a tree. **Correction (UFIX10):** this
paragraph previously read flatly "no history", which was wrong in one respect — `MANIFEST.json` shipped the private
branch's commit id as provenance (19 citations). That is not a history *object*, but it is history *information*, and
it has now been removed (see `MANIFEST.json` → `harness_revision`, and `REDACTION_REPORT.md` §8.1).

## 7. Layout, and what is deliberately absent

```
fixture/       reflex-decisions.ts           190-case instrument, rationale+namespaces values emptied
                                              (VARIANT A: DecisionKind union kept, comments stripped)
               DECISION_CASE_SCHEMA.ts       the same, mechanism comments stripped
harness/       tccommon.py, tcmodel.py       one renderer + shared metrics (`rationale`/`namespaces` never read)
               export-fixture.ts, lint.ts    steps 1-2 (TypeScript; need a repo-shaped checkout + runner)
               prepare.py, train.py, evaluate.py, analyze.py, defect-probe.py, collect.py
               README.md, LEAD-WIRING.md     harness docs (LEAD-WIRING sanitised — see §2)
               data/                         corpus.json, train.jsonl, dev.jsonl, fixture-190.json,
                                             lint-report.json, manifest.json — the run's frozen inputs
preregistration/ EXP12-…-prereg.md           EXP#12 §1–§9, the frozen pre-registered protocol (untouched)
results/       eval-{modernbert-base,deberta-v3-base,setfit-mpnet,majority-class,shuffled-label}.json,
               baselines.json, REPORT.md, DEFECT-EVIDENCE.json
second-labeller/ RUN.json, EVIDENCE.md, metrics.json, disagreements.jsonl (regenerated, rationales emptied),
               PREREGISTRATION.md, parse_fixture.py, compare.py, labelsB.json, OWED_CORRECTIONS.md (sanitised)
variants/no-union/  VARIANT B — the union removed; apply instructions inside
verify/        the acceptance test and its verbatim logs
EXCLUDED.md, LICENCE_TODO.md, MANIFEST.json, INTEGRITY.md, REDACTION_REPORT.md, RESIDUALS.md, README.md, redact.py
```

**Still withheld, unchanged from the as-audited boundary** (`EXCLUDED.md`): the agent-state kernel / runtime
implementation (`src/**`, `kernel/**`), all model weights (the three arms are re-fetched from their **public**
Hugging Face repos by `harness/tcmodel.py`), the target's own `LICENSE`, `traces/`, `runs/`, `tmp/`, `scratch/`,
`archive/`, and `node_modules/`. **Additionally withheld by this unit:** the rationale and namespace values, the
mechanism comments, the verbatim rationale quotations in the second-labeller documents, and the private-repo
wiring map in `LEAD-WIRING.md`.

## 8. Limits a reviewer should carry

- `evaluate.py` / `analyze.py` are **not runnable in this subset** (their `harness/out/manifest-*.json` are excluded
  by `EXCLUDED.md` E12). Their outputs ship frozen and are byte-identical between the two trees; the McNemar table
  is recomputed from the shipped per-case records by `verify/recompute-claims.py`. `0.6684` is a **quoted published
  constant**, not a recomputation.
- Steps 1–2 (`export-fixture.ts`, `lint.ts`) need a repo-shaped checkout, a TypeScript runner and the as-audited
  digest; their outputs ship frozen and `prepare.py` re-verifies them.
- Bit-exactness of the sealed scores depends on torch/transformers versions and device; the shipped records are the
  run of record.
- The redaction removes reviewers' access to the per-case reasoning. That is the price, stated in §2.

## 9. Licence

**Decided:** extracted pieces ship under **PolyForm Noncommercial 1.0.0**; the main the source repository repository stays
proprietary; the papers are CC BY 4.0. The authoritative text lives in `strategy/licence-templates/` and the
placement steps are recorded in [`LICENCE_TODO.md`](LICENCE_TODO.md) — take the text from the template, do not
restate it here. Note UTS1 §5.3: publishing source under *any* licence discloses it; PolyForm Noncommercial
restricts commercial *use of the copyright*, it does not maintain secrecy in published text, and it does not
address the residual disclosure in `REDACTION_REPORT.md` §7.

**Byte-integrity of every file here is in [`INTEGRITY.md`](INTEGRITY.md)**, including the sha256 of the fixture
before and after, the scoring-projection digest, and the evidence that the as-audited subset (42/42 manifest
entries) and the target repository (HEAD `907fa39…`, same four pre-existing untracked paths) are unmodified.
