# PUBLISH_PACKAGE_MANIFEST — the ship/drop decision, item by item

**Unit:** UCURATE1 · **Purpose:** decide and encode exactly which files the public package ships, so the
residual leak surface drops to the deliberate minimum.
**Deliverable of record for:** `orchestration/units/UBUILD1.build.sh` (826 lines, sha256
`0b617414e5eb0e8a2a86930bdf5f2de1d0cf3fb3f9a93865b36e7380af293115`).

> **Superseded 2026-10-16:** the build script was edited after this manifest was written; it is now **1019 lines**, sha256 `a2a1df178fbc8fca01c573f283327fe6ca96d2d7bdca89ef539b17987e007a69`. The cited values are those this manifest was written against and are left unrewritten as the record.
**The gate is the arbiter, not opinion:** every accept/decline below is backed by a count produced with the
positive vocabulary checker written just after `cat > "$DEST/gate.sh" <<'GATE_EOF'` in `UBUILD1.build.sh` (currently `:771–897`), run over the
exact tree the amended build produces.

---

## 0. The line I drew

> **Reader-load-bearing** — a file is needed to (a) recompute a published number from bytes *inside the
> package*, or (b) understand what the package claims and what it does not establish. These ship **even when
> they carry a declared residual reference to an internal document name**, because a resolved-but-named
> internal reference is a documentation defect, while a missing instrument is a reproducibility failure.
>
> **Record of our process** — a file that documents *how the sanitisation, curation or verification was
> done*. Not one of its bytes is needed to recompute a number or to read a claim. These **do not ship**,
> whatever their hit count, and they are dropped rather than scrubbed: an audit record that has been edited
> is no longer an audit record.

Two consequences follow, and they are the whole decision:

1. Hit count is **not** the ship test. `code/fixture/reflex-decisions.ts` carries 54 hard-fail lines and
   ships; `code/verify/RECOMPUTE-CLAIMS.txt` carries 0 and does not.
2. The build **selects**; it does not rewrite. The only transform is a path neutralisation (§5), applied to
   a *path*, never to model input.

---

## 1. Structuring decision: fail-closed ship-list, not a drop-list

The build now owns an explicit `SHIP_STAGED` array (52 entries) and a `NEVER_SHIP` array (17 names).

**Chosen: a ship-list, because a drop-list is fail-OPEN.** Under the old `cp -r`-then-`rm -f` shape, any file
added upstream by a later unit ships by default and nobody is told — the failure is silent and its direction
is *towards disclosure*. Under a ship-list, an unlisted file is deleted and logged (`DROP <rel>`), and a
listed file with nothing behind it stops the build (`FATAL: ship-list names a file the package does not
have`). Its failure direction is towards *under-shipping*, which is visible, cheap to correct, and safe.

`NEVER_SHIP` is checked **by absence** at the end of the build. The ship-list already makes these
unreachable; `NEVER_SHIP` exists so a future `cp -r` of another directory cannot turn a drop-by-omission
into a ship, and so the drop decisions are recorded **by name** and survive a refactor.

**`INCLUDE_VERIFY` was deleted.** It let the build omit `code/verify/` entirely. Removing it is strictly
stricter — that lever's only use was to drop the reproduction instrument.

**The gate was not weakened.** Its 24 HARD patterns and 6 REVIEW patterns are byte-identical to the
pre-existing list; HARD still stops the build. The only change to gate behaviour is the pre-existing
`--exclude="$SELF"`, which I left alone.

---

## 2. `code/verify/**` — split, not dropped

The card's instruction: *ship the scripts, drop the generated logs/outputs.* Investigated, and the split is
**1 ship / 7 drop** — narrower than "the scripts", for a stated reason.

| file | hard hits | disposition | reason |
|---|---|---|---|
| `recompute-claims.py` | 1 | **SHIP** | It *is* the reproduction instrument: it reads `harness/data/fixture-190.json` (:59), `results/eval-*.json` (:65), `results/baselines.json` (:70), `second-labeller/metrics.json` (:113) and prints the scoring-projection digest (:127) — every input is inside the package. Its 1 hit is a sentence naming `EXCLUDED.md` E12; that is a documentation residue, not a leak. |
| `VERIFICATION.txt` | 41 | DROP | Generated run output — a log. Its 41 lines are the verification driver's own output, quoting the driver's pattern lines and absolute scratch paths. |
| `RECOMPUTE-CLAIMS.txt` | 0 | DROP | Generated run output. Zero hits, still a log: it is the *result* of the instrument, reproducible by re-running `recompute-claims.py`, not part of it. |
| `RESIDUAL-SCAN.txt` | 1 | DROP | Generated run output of the residual scan. |
| `redaction-log.json` | 4 | DROP | Machine-readable record of the redaction pass (naming `REDACTION_REPORT.md` and `\bgrantPolicy\b` as patterns). A process artefact. |
| `integrity-table.md` | 2 | DROP | A per-file hash table of the **58-file SANITISED tree** — of which 26 files do not ship, and whose rows name `EXCLUDED.md` and `LICENCE_TODO.md`. Its load-bearing content (the digests a reader needs) survives inside shipped bytes: `harness/tccommon.py` and `harness/data/manifest.json`. |
| `run-verification.sh` | 3 | DROP | **Process tooling that cannot run in the package, and that embeds the gate's own pattern list.** It needs the private as-audited tree as a sibling (`O=dirname($S)/encoder-crossover-190`), and it deletes `REDACTION_REPORT.md`/`INTEGRITY.md` from its own scratch copy (:16). At **:138** and **:156** it carries the STRICT regex `StateClass|grantPolicy|materialiseGrants|grantKey|admit\(|src/(broker|scope|layer|loop|policy|state)\.ts|content-addressed|DecisionKind|expanded\[\]|Needle`. Shipping it would ship a machine-readable list of the identifiers this package withholds — a roadmap, not a leak, but a roadmap is exactly what a packaging unit must not publish. |
| `scrub-uscrub1.py` | 1 | DROP | The scrub engine. Same defect class at **:63**: `("github.com/" + _ACCT + "/publish-present-compete", ...)` — it *names the withheld repository*. The one hit is the finding. |

**Decision on the card's "if a script itself carries a local path — substitution or exclusion?"** Neither, in
fact: no *script* carries a local path. The two scripts carry **identifier patterns**, and for an identifier
the only correct disposition is **exclusion** — substitution would falsify the script's meaning, and a
substituted pattern list is a broken pattern list. The local paths that did exist were in
`harness/data/manifest.json` and `fixture/DECISION_CASE_SCHEMA.ts`; both are *data*, and for those
**substitution** is correct (§5). The distinction is the answer to the card's question: **exclude a script
that names what we withhold; substitute a path in data that must keep loading.**

---

## 3. The document set — checked one at a time, not blanket-dropped

`A record of our process → DROP` (four of them), `load-bearing for a reader → SHIP`.

| document | hard hits | disposition | reason |
|---|---|---|---|
| `EXCLUDED.md` | 2 (as a *name* in shipped files); the file itself never staged | **DROP** | The exclusion inventory. It names every withheld record and the private vocabulary. Pure process record. |
| `LICENCE_TODO.md` | 1 | **DROP** | A to-do list of licence text still to be placed. Process record; a reader needs `LICENCE`/`LICENSE`, which ships. |
| `REDACTION_REPORT.md` | 10 | **DROP** | 49 KB documenting the before/after leak inventory — the single densest description of what was removed and why. Process record; **this is the last file that should ever ship.** |
| `RESIDUALS.md` | 6 | **DROP** | The residual-leak ledger. Process record. Its finding is preserved *for the reader* in the package `README.md`, which states that residues exist, names the categories, and points at the gate that reports them file-and-line. |
| `SCRUB_REPORT.md` | 22 | **DROP** | USCRUB1's sanitisation report. Process record. |
| `INTEGRITY.md` | 12 | **DROP** | The card invited me to consider shipping it. **It does not carry leaks of the private tree so much as it carries the shape of the whole private working set:** it hashes a **58-file** tree of which **26 files do not ship** and names `EXCLUDED.md`, `LICENCE_TODO.md`, `RESIDUALS.md`, `REDACTION_REPORT.md` and a `strategy/VERIFICATION_REPORT_8.md` correction cycle in its header. Shipping it would publish a manifest of files a reader cannot obtain, and would tell them precisely what was removed. **The load-bearing content survives:** the digests a reader actually needs are pinned inside shipped bytes — `harness/tccommon.py` (`INSTRUMENT_190_SHA256`) and `harness/data/manifest.json`. So the hash *cycle* the card worried about is not needed by any shipped consumer. |
| `MANIFEST.json` | 3 | **DROP** | 20 KB mapping the 38 sanitised files back to their as-audited originals. Process record: it is the provenance of the *sanitisation*, not of the measurement. |
| `redact.py` | 24 | **DROP** | The scrubber itself. Also the file most likely to encode what was removed. |
| `variants/` | 56 (subtree) | **DROP** | An alternative (no-union) rendering of the instrument, plus a README. Shipping a second, differently-sanitised variant of the fixture invites a reader to compute numbers against the wrong instrument; it is not on the reproduction path and was never staged. |
| `README.md` (the SANITISED tree's own top-level index) | 14 | **DROP** *(never staged)* | **This is the card's "fix or drop — your call".** Drop, and the reason is structural rather than cosmetic: it is an index **of a tree that is not this package**. Line 129 of it lists its own contents as `EXCLUDED.md, LICENCE_TODO.md, MANIFEST.json, INTEGRITY.md, REDACTION_REPORT.md, RESIDUALS.md, README.md, redact.py` — seven of those eight do not ship and never will; lines 9/25/38/48/67/94/108/158 discuss `REDACTION_REPORT.md` §5, §6, §7, §8.1 as if the reader could open it. "Fixing" it would mean rewriting eight paragraphs to point at documents that are absent — i.e. scrubbing a process record, which is the thing §0 forbids. The build instead **authors three fresh READMEs** (root, package, `code/`) that describe exactly what is present. `code/harness/README.md` ships from the sanitised tree and is gate-clean. |
| `papers/encoder-crossover-190/{LICENSE_ANALYSIS,DISCLOSURE_CHANGES,LIMITATIONS_UPDATE,VERIFIER_CORRECTIONS,MANUSCRIPT_CHANGES,AVAILABILITY}.md` | 0 | **DROP** | Internal audit trail of the paper's own revision cycle. Already excluded before this unit; the ship-list keeps them excluded. |
| `eval/second-labeller/OWED_CORRECTIONS.md` | 3 (was 10 pre-curation) | **DROP** | The per-defect correction ledger. Its `:7` names `strategy/VERIFICATION_REPORT_3.md`; nine further lines are `[withheld rationale quote — see ../REDACTION_REPORT.md section 5]` placeholders — a document whose body is *pointers to documents that do not ship*. **Finding preserved for the reader:** the corrections it records are stated in `paper/MANUSCRIPT.md` and `eval/results/REPORT.md`, both of which ship. |
| `experiments/second-labeller-190/{ROBUSTNESS.md, RUN2.json}` | 0 / 0 | **SHIP** | The upstream run-2 material. **Measured 0 hard hits in each** — the earlier belief that they hard-fail was wrong, and the second-labeller dedup loop's comment was corrected to say so. They are the independent replication, i.e. load-bearing. |
| `papers/gated-read-batching/DISCLOSURE_CHANGES.md` | 19 | **DROP** | Added on UFIX11's sweep (see §7). An audit trail of that batch: unit names, a verification-report filename, md5 digests, and the target path. Not in this package's ship set, and recorded in `NEVER_SHIP`. |
| `harness/LEAD-WIRING.md`, `harness/export-fixture.ts` | 2 / 1 | **SHIP** | Wiring instructions a reader needs to run the harness; both carry a `See ../REDACTION_REPORT.md section N` cross-reference. That reference is unresolvable in-package — **declared, not hidden**: it is a documentation residue, and the alternative (rewriting a reader-facing technical note to hide a filename) is worse than the residue. |
| the three authored READMEs, `LICENSE`, `.gitignore`, `gate.sh`, `eval/results/REPORT.md`, `paper/*.md` (11) | 0 | **SHIP** | Authored for this package, or the manuscript and its apparatus. |

**Precedent check (UFIX11 asked).** `EXCLUDED.md` is **genuinely excluded, not merely documented as
excluded**: a `find` over the built package for `EXCLUDED*`, `REDACTION_REPORT*`, `RESIDUALS*`,
`LICENCE_TODO*`, `SCRUB_REPORT*`, `INTEGRITY*` returns **0 files**, and `EXCLUDED.md` appears in the build
script exactly twice — both times inside explanatory comments. The precedent is as strong as it looks, and
`DISCLOSURE_CHANGES.md` is the same species of file.

---

## 4. `GrantPolicy` and the instrument remnants — declared, not hidden

The card: *state whether each is excluded, substituted, or accepted-and-declared, and why; do not invent a
substitution rule.*

**Accepted-and-declared.** These are model input, and they ship with their hit counts printed by the gate.

- **The 2 camel-case `GrantPolicy` question strings** (`fixture/reflex-decisions.ts:288,798`;
  `harness/data/fixture-190.json:234,851`). UTOK2 identified them as a mapping gap and measured that closing
  it moves exactly one shipped number — `/routeA/ties` 120 → 119 — and moves the scoring-projection digest
  (`57a29b4e…` → `d52893f4…`) — because `second-labeller/compare.py` scores
  `route_a = len(tokens(option) ∩ tokens(question))` (+0.5 for a normalised-substring match, argmax, ties to
  lowest index). **They are the question text of a sealed instrument.** Editing them is re-cutting the
  instrument, which is a *new experiment*, not a packaging step, and any such change belongs to a unit that
  can re-run every arm and republish the numbers. This unit cannot measure what it would break by design.
- **The instrument remnants** — `StateClass` 62, `grantPolicy` 40, `expanded[` 28, `admit(` 20,
  `src/broker` 2, `REDACTION_REPORT` 10, `EXCLUDED.md` 2, `VERIFICATION_REPORT` 1 (165 per-pattern
  occurrences over 152 distinct lines; 13 lines match two patterns — a **superseded denylist measurement**; the current positive-vocabulary gate measures **95,606** out-of-vocabulary tokens (line `:255`), and why the 152 is retained as a real historical measurement is explained at `:258`–`:259` and `:292`–`:296`). These are the vocabulary the 190 cases
  were written in. **They are the measurement.** A package that has scrubbed the words it measured is not a
  reproducibility package.
- **No substitution rule was invented.** UTOK2's 14-entry prose/question `MAPPING` is an unmerged proposal
  living in a scratch experiment directory, and the card forbids me to promote it into the build. The build
  rewrites **no prose and no question**, so every recorded `sha256` in `redaction-log.json`,
  `manifest.json` and `tccommon.INSTRUMENT_190_SHA256` stays true.

---

## 5. The only transform: path neutralisation (3 literal rules)

Taken verbatim from UTOK2 §1, applied by a fail-closed Python step before `git init`:

| rule | replacements over the built tree |
|---|---|
| `/home/zer0null/Duval/` → `<target-repo>/` | 1 (in `code/fixture/DECISION_CASE_SCHEMA.ts`) |
| `/home/zer0null/Duval` → `<target-repo>` | 3 (in `code/harness/data/manifest.json`) |
| `/home/zer0null` → `<user-home>` | (covered above) |

Measured: **4 occurrences in 2 files**; `/home/zer0null` 4 → **0** and `duval` 4 → **0**. The step
re-scans and **aborts the build** if either survives. `gate.sh` is skipped — it *is* the pattern list, so
the patterns are literally inside it, and the gate excludes itself (`--exclude="$SELF"`); rewriting them
would disarm the gate.

**Why substitution here and exclusion there:** `code/harness/data/manifest.json` is **read at runtime** by
`harness/analyze.py:133` and copied by `harness/collect.py:52` — excluding it breaks the harness, and a path
is not model input, so replacing it cannot move a measured number. Excluding it would be the wrong trade:
we would lose a load-bearing input to remove a string that is not a secret. Verified consequence: the one
file with three hard hits drops to **0**, and the first file's only hit drops to **0** too, leaving
`//   target: <target-repo>/evals/fixtures/reflex-decisions.ts (HEAD 907fa39)`.

**Nothing loads from the private tree at runtime.** No shipped file references `state/`, `dockets/`,
`orchestration/`, `experiments/`, or the workspace path — the neutraliser's fail-closed scan of
`/home/zer0null` and `duval` returning 0 proves it for paths, and the shipped `code/verify/recompute-claims.py`
resolves every input relative to `code/`.

---

## 6. The deliberate anchors

`907fa39` and `ad301ae` are the read-only target-revision proof: the record that the instrument was cut from
a named revision. **Kept on purpose** — and now *asserted*, so a later pass cannot "clean" them: the build
greps for each and refuses to finish if either is missing, printing *"they are the read-only
target-revision proof and are kept on purpose — see the header of this script. Do not remove them."*
Verified present: `907fa39` in **12** files, `ad301ae` in **7**.

Both explain portions of the residual count, and that is accepted. Note `papers/encoder-crossover-190/REFS.md:126`
carries `a5ef1b2` (7 hex chars), which does **not** match the HARD pattern `a5ef1b28` — a near-miss that is
left alone rather than "fixed" to match.

---

## 7. `papers/gated-read-batching/` — folded in from UFIX11's sweep

**Verified myself, not taken on trust.** The directory contains **exactly 5 files**: `CLAIMS.md`,
`DISCLOSURE_CHANGES.md`, `GAPS.md`, `MANUSCRIPT.md`, `REFS.md`. UFIX11 is right that `CHECKLIST.md`,
`OPEN_QUESTIONS.md`, `REFERENCES.bib` and a README **do not exist** there; the ship list does not assume them.

**This directory is not in this package at all.** `UBUILD1.build.sh` has no reference to `gated-read`; it
stages `papers/encoder-crossover-190` only. So the practical decision is that the whole directory is
outside the package, and `papers/gated-read-batching/DISCLOSURE_CHANGES.md` is recorded in `NEVER_SHIP` so a
future revision cannot bring it in by adding a `cp -r`.

- **`DISCLOSURE_CHANGES.md` — DROP.** Under the gate's verbatim 24-pattern list I measure **19 hard-hit
  lines** in this one file (the target path at :7/:265/:266/:268/:269/:303/:310, `VERIFICATION_REPORT_10.md`
  at :3, plus unit/pattern-recital lines). UFIX11's **52** is against its own wider sweep list (19
  alternatives, including `\b[0-9a-f]{8,}\b`, `/Users/`, `/mnt/`, `/opt/`, `UVER`, `UPAPER`, `UFIX`) — the two
  figures are both right and are not comparable; the gate's list is the arbiter for shipping. Drop, not
  scrub, for the reason UFIX11 gives: scrubbing an audit record destroys its only purpose.
- **The other four are hard-clean (0 hits each** under the verbatim list; `CLAIMS.md` carries 1 REVIEW-pattern
  hit, which is report-only). `CLAIMS.md` and `REFS.md` show 0 *because UFIX11 fixed them* — the target-root
  paths that `DISCLOSURE_CHANGES.md:303,310` record as `BEFORE:` are gone from the live files, replaced by
  "the read-only source material (an external checkout; name and location withheld)". That fix is the right
  one and it is the model for item 3 below.

### The traceability question — settled

**Where the source documents live:** `GATED_READ_2026.md` and `GATED_READ_PROVENANCE.md` exist **only in the
read-only target repository** — live at `/home/zer0null/Duval/docs/research/` (`GATED_READ_2026.md` 23,591 B,
`GATED_READ_PROVENANCE.md` 31,679 B) — and in workspace mirrors of that repository under `state/` (staged
copies such as `state/kg-refresh/duval/repo/docs/research/`). There is **no workspace-authored copy**, so
they are neither in the private tree's own papers nor available to ship.

**Decision: (b) — they do not ship**, and **the manuscript does not need new prose**, because the legend and
the withholding are already declared and already gate-clean:

- `papers/gated-read-batching/CLAIMS.md:8` — "**Source paths** are relative to the root of the read-only
  source material (an external checkout; name and location withheld)".
- `papers/gated-read-batching/CLAIMS.md:11-15` — the full letter legend: **G** `docs/research/GATED_READ_2026.md`
  (the run report, 340 lines); **R** `docs/research/gated-read-rows.jsonl` (9,260 per-decision rows);
  **S** `docs/research/gated-read-summary.json` (aggregates the harness wrote); **P** `docs/research/GATED_READ_PROVENANCE.md`
  (literature provenance + fetched URLs).
- `papers/gated-read-batching/REFS.md:11` — "the read-only source material (an external checkout; name and
  location withheld)".

So a `P:23-56` or `G:150` locator resolves to **a named file and line range in a location the document
states it is withholding**. Shipping the sources themselves is not open to this package: the package's
entire premise is that it does **not** redistribute the read-only target repository, and `R`/`S` are raw
harness output from it.

**The one real defect found, stated because "clean" and "usable" diverge exactly here:** the letters are
distinguishable, but the **R/S** rows of the four-letter legend are written out only in `CLAIMS.md:11-15`, while
`REFS.md`'s only `G:` locator is at `REFS.md:68` (`G:49-51`) — its `:66` row uses `P:246`, the locator declared
at `REFS.md:11`, and the `G:` source legend sits at `REFS.md:15`. Fix belongs in the paper, not in the package: add one line to `REFS.md` — either the
full four-letter legend or "letter legend: `CLAIMS.md:11-15`". **Recommendation, not a shipped change** —
`papers/gated-read-batching/**` is UFIX11's write path, not mine.

**What a reader of that paper loses if it ever ships:** the ability to check the 39 `G:`-located and 8
`P:`-located references against their sources without target-repo access. That limitation is *stated* at
`CLAIMS.md:8` and `REFS.md:11`; it is a declared cost of not redistributing the target, and the honest
alternative to declaring it is not to ship the paper.

---

## 8. The gate, re-run over what ships

Method: the amended build was executed **inside the workspace** (`DEST=.ucurate1/pre/research-publish-packages`,
a path ending in `/research-publish-packages` so the guard passes) with `SRC` pointed at the workspace, so
that **nothing was written outside the workspace and the real `/home/zer0null/research-publish-packages` was
never touched**. The checker was read out of the built `gate.sh` — the positive vocabulary checker written just
after `cat > "$DEST/gate.sh" <<'GATE_EOF'` in `UBUILD1.build.sh` (currently `:771–897`), not invented.

```
GATE RESULT: FAIL — 95606 out-of-vocabulary token(s) (UFIX15 re-measurement of the current workspace tree; the superseded denylist-era result was 152 HARD-FAIL + 2134 REVIEW, retained below).
```

**Superseded denylist gate — per HARD pattern** (counts are matching *lines*; the sum exceeds the total because 13 lines match two
patterns; ULICENCE3 deleted this denylist and replaced it with the positive checker above):

| pattern | hits | | pattern | hits |
|---|---|---|---|---|
| `StateClass` | 62 | | `REDACTION_REPORT` | 10 |
| `grantPolicy` | 40 | | `EXCLUDED.md` | 2 |
| `expanded[` | 28 | | `src/broker` | 2 |
| `admit(` | 20 | | `VERIFICATION_REPORT` | 1 |
| `/home/zer0null` | **0** | | `duval` | **0** |
| `a5ef1b28` `89003e70` `publish-present-compete` `consonance` `RESIDUALS.md` `LICENCE_TODO` `TRADE_SECRET` `WITHHELD.md` `DISCLOSURE_INVENTORY` `EXPOSURE_CLOSURE` `ARCHIVE_WINDOW` `src/scope` `src/layer` `CommitRecord` | **0** | | **TOTAL (distinct lines)** | **152** |

**Per HARD-hitting file** (this is the whole leak surface of the package):

| file | hits | | file | hits |
|---|---|---|---|---|
| `code/fixture/reflex-decisions.ts` | 54 | | `eval/second-labeller/EVIDENCE.md` | 2 |
| `code/harness/data/fixture-190.json` | 46 | | `code/harness/LEAD-WIRING.md` | 2 |
| `eval/results/eval-shuffled-label.json` | 8 | | `eval/second-labeller/parse_fixture.py` | 1 |
| `eval/results/eval-majority-class.json` | 7 | | `eval/second-labeller/metrics.json` | 1 |
| `eval/results/eval-deberta-v3-base.json` | 7 | | `eval/second-labeller/RUN.json` | 1 |
| `eval/results/eval-setfit-mpnet.json` | 6 | | `code/verify/recompute-claims.py` | 1 |
| `eval/results/eval-modernbert-base.json` | 6 | | `code/harness/export-fixture.ts` | 1 |
| `eval/results/baselines.json` | 6 | | `code/fixture/DECISION_CASE_SCHEMA.ts` | **0** (was 1) |
| `eval/second-labeller/disagreements.jsonl` | 3 | | *(21 further shipped files, incl. `paper/`, authoured docs)* | **0** |

**Baseline.** The contract fixes `gate_before = "158"` — UTOK2's figure over the **whole 58-file SANITISED
tree with prose substitution applied**, a different tree measured with a different transform, and measured
without the gate's `--exclude="$SELF"`. UCURATE1's own comparable measurement of **the unmodified build's
ship set with no transform at all** is **156** — the 152 post-transform lines plus the 4 path-only lines the
three path rules neutralise, which the build's own neutralise log reports as `4 occurrence(s) in 2 file(s)`;
with the three path rules it is **152**. The two figures differ by 2, so they are broadly comparable rather
than incommensurable — the earlier framing overstated the gap.

**Under the superseded denylist the package could not pass its own gate, and that was the correct outcome.** Of the 152, **150 are model input
or instrument vocabulary** (§4) that only a re-cut experiment could remove, and 2 are declared documentary
cross-references (§3). The gate is a **leak detector**, not a shipping checklist: it fires on the instrument
itself by construction. It was **left strict** and the build **correctly stops at exit 1** rather than
sanitising its way to a pass. `152` is the deliberate minimum given the ship set, not a failure to reach 158.

---

## 9. The exact ship list — 58 files

**52 staged** (from the SANITISED tree; `$PKG` = the package's `packages/exp12-encoder-crossover/`):

```
paper/CHECKLIST.md                     paper/CLAIMS.md                  paper/EVIDENCE_NOTES.md
paper/GAPS.md                          paper/MANUSCRIPT.md              paper/OPEN_QUESTIONS.md
paper/REFERENCES.bib                   paper/REFERENCES_ADDITIONS.bib   paper/REFS.md
paper/REFS_VERIFIED.md                 paper/RELATED_WORK_NOTES.md      paper/UNSOURCED_RETAINED.md
code/fixture/DECISION_CASE_SCHEMA.ts   code/fixture/reflex-decisions.ts
code/harness/README.md                 code/harness/LEAD-WIRING.md      code/harness/analyze.py
code/harness/collect.py                code/harness/defect-probe.py     code/harness/evaluate.py
code/harness/export-fixture.ts         code/harness/lint.ts             code/harness/prepare.py
code/harness/tccommon.py               code/harness/tcmodel.py          code/harness/train.py
code/harness/data/corpus.json          code/harness/data/dev.jsonl      code/harness/data/fixture-190.json
code/harness/data/lint-report.json     code/harness/data/manifest.json  code/harness/data/train.jsonl
code/verify/recompute-claims.py
eval/preregistration/EXP12-typed-channel-comparison-prereg.md
eval/results/DEFECT-EVIDENCE.json      eval/results/REPORT.md           eval/results/baselines.json
eval/results/eval-deberta-v3-base.json eval/results/eval-majority-class.json
eval/results/eval-modernbert-base.json eval/results/eval-setfit-mpnet.json
eval/results/eval-shuffled-label.json
eval/second-labeller/EVIDENCE.md       eval/second-labeller/PREREGISTRATION.md
eval/second-labeller/RUN.json          eval/second-labeller/compare.py
eval/second-labeller/disagreements.jsonl  eval/second-labeller/labelsB.json
eval/second-labeller/metrics.json      eval/second-labeller/parse_fixture.py
eval/second-labeller-190/ROBUSTNESS.md eval/second-labeller-190/RUN2.json
```

**6 authored by the build:**

```
README.md                                   (repository root)
LICENSE                                     (MIT, <YEAR>/<COPYRIGHT HOLDER> placeholders)
.gitignore
gate.sh                                     (the acceptance test)
packages/exp12-encoder-crossover/README.md
packages/exp12-encoder-crossover/code/README.md
```

> **Superseded 2026-10-16 (UFIX24, dated record left unrewritten):** the authored root `LICENSE` is no longer
> MIT with placeholders — the build copies the PolyForm Noncommercial 1.0.0 template (`cp "$LIC_SRC/$f" "$DEST/$f"` `:579`,
> digest-pinned at `:584`) and appends the scope clause (`LICENSE_SCOPE_EOF` `:590`–`:602`).

Build output, verbatim: `staged 66 file(s): 52 kept, 14 dropped` · `ship-list enforced: 52 staged file(s)
present` · `never-ship list enforced: 17 names checked absent` · path neutralisation `4 occurrence(s) in 2
file(s)` · `anchor 907fa39 present in 12 file(s)` · `anchor ad301ae present in 7 file(s)` · ship file count
**58**.

---

## 10. What a reader loses, per drop

| dropped | what the reader loses | where the finding survives |
|---|---|---|
| `verify/VERIFICATION.txt` (41) + `RECOMPUTE-CLAIMS.txt` + `RESIDUAL-SCAN.txt` | The as-run transcript of the sanitisation check and the residual scan. | `code/verify/recompute-claims.py` regenerates the claim numbers; the package `README.md` states that residues exist and that `gate.sh` reports them file-and-line. |
| `verify/run-verification.sh`, `verify/scrub-uscrub1.py` | The ability to re-run the *sanitisation* — not the measurement. | Nothing: they cannot run outside the author's tree, and shipping either publishes the withheld-identifier list. |
| `verify/{redaction-log.json, integrity-table.md}` | The per-file redaction log and the hash table of the 58-file tree. | The digests a consumer needs are pinned in `harness/tccommon.py` and `harness/data/manifest.json`; `harness/LEAD-WIRING.md` §5 states the rendered split's digests are "recorded in `../INTEGRITY.md`" — a now-unresolvable pointer, declared. |
| `REDACTION_REPORT.md`, `EXCLUDED.md`, `RESIDUALS.md`, `SCRUB_REPORT.md`, `LICENCE_TODO.md`, `MANIFEST.json`, `redact.py`, `variants/`, the tree's `README.md` | The complete audit trail of the sanitisation: what was removed, how, and what remains. **This is the largest loss and it is deliberate** — this material describes the private side, and a reproduced public package does not need it. | `README.md` (package) names the residual *categories*, and `gate.sh` reports every residual *instance* with file and line — so a reader can still see and count the residues, just not the removal rationale. `LICENCE_TODO.md`'s task is discharged by shipping `LICENSE`. |
| `INTEGRITY.md` (12 hits) | The authoritative hash record over the full 58-file sanitised tree. | The load-bearing digests ship inside `harness/tccommon.py` + `harness/data/manifest.json`; and the tree it hashes is not the tree that ships, so a reader could not have verified it anyway. |
| `eval/second-labeller/OWED_CORRECTIONS.md` | The itemised correction ledger. | The corrections themselves are stated in `paper/MANUSCRIPT.md` and `eval/results/REPORT.md`, both shipped. |
| 6 `papers/encoder-crossover-190/*.md` audit files | The paper's revision/verification trail. | The manuscript's `CHECKLIST.md`, `GAPS.md`, `OPEN_QUESTIONS.md` and `EVIDENCE_NOTES.md` carry the reader-facing version. |
| `papers/gated-read-batching/*` (whole directory) | Nothing from *this* package — it was never in it. | Decision recorded in §7 above and in `NEVER_SHIP`; the paper's own legend is at its `CLAIMS.md:11-15`. |

---

## 11. UNVERIFIED

1. **The real build was not run.** `/home/zer0null/research-publish-packages/` is outside the sandbox; per
   the card the build must not be run. Everything here was verified by executing the amended script with
   `DEST` **inside the workspace** (`.ucurate1/pre/research-publish-packages`). The one thing that cannot be
   proven this way is behaviour on the real `DEST` — in particular the `git init`/commit step, whose
   `COMMIT_DATE` (`2026-10-15T00:00:00+00:00`) and "no remote, never pushes" claims are read, not executed
   here. *(The scratch run did complete `git init` + commit without a remote, so that path is exercised, just
   not at the real destination.)*
2. **UTOK2's `gate_before = 158` was not re-derived.** It is quoted as the contract fixes it; my own two
   measurements (218 untransformed ship set, 152 after the path rules) are reported alongside because they
   answer a different question over a different tree.
3. **The 2 `GrantPolicy` question strings were not substituted**, so the post-substitution scoring-projection
   digest and the `/routeA/ties` 120→119 movement remain **UTOK2's measurement, not re-measured here**. That
   is deliberate — the change is out of this unit's scope — but it means the "what would it cost" number rests
   on UTOK2.
4. **`/routeA/ties` was not recomputed** over the ship set.
5. **`harness/analyze.py` cannot be run** by a reader: it needs `harness/out/manifest-eval.json`, which
   `EXCLUDED.md` E12 excludes (a fact `recompute-claims.py:14` states). UTOK2 raised this; I confirm the
   dependency and that the file is absent, but I did **not** run `analyze.py` to see how it fails.
6. **`manifest.json` neutralisation is not durable.** UTOK2 §7.4 established that re-running
   `harness/prepare.py` rewrites it with local paths. The build neutralises the shipped copy, so the shipped
   bytes are clean; a reader who re-runs `prepare.py` reintroduces local paths. Confirmed by reading UTOK2,
   **not re-verified** by re-running `prepare.py` (it needs the excluded `manifest-eval.json`).
7. **The four `papers/gated-read-batching/*.md` files were measured, not run.** Their 0-hit counts come from
   grepping the seven files against the verbatim list. Their content was read only at the lines needed to
   settle the locator question.
8. **`papers/gated-read-batching/DISCLOSURE_CHANGES.md`'s 19 vs UFIX11's 52** is explained by the two
   different pattern lists (§7); I did not reproduce UFIX11's wider list to confirm its exact 52.
9. **Under the now-superseded denylist the 6 REVIEW patterns were left alone** — 2,134 REVIEW hits (`memory.admission` 1,265,
   `capability.family` 848, `src/` 31, `DecisionKind` 6 … plus the same instrument vocabulary). These are
   report-only by the gate's design and were not curated; a future unit may decide they matter.
10. **`orchestration/units/UBUILD1.build.sh` was edited but not committed** — the workspace is not this
    script's destination, and running `git` in the workspace was outside the card.

---

## 12. OPEN DECISIONS — flagged, not taken

Requested by the orchestrator after inspecting the staged tree. **Nothing below was changed**; a flagged
conflict is a valid deliverable and an unexamined one is not. Write paths were not widened.

### 12.1 Licence tier — the shipped `LICENSE` is MIT, and MIT contradicts the binding decision

**What is in the package.** `$DEST/LICENSE` is a **root-level MIT** file, authored by the *pre-existing*
`UBUILD1.build.sh` heredoc (build-script lines 524–545).

> **Superseded 2026-10-16:** build-script lines 524–545 are now package-README prose. The root `LICENSE` is no longer authored by a heredoc there: the script digests the staged `LICENSE` (`sha256sum "$DEST/LICENSE"` at `:583`) and appends only its scope clause (`cat >> "$DEST/LICENSE" <<'LICENSE_SCOPE_EOF'` at `:590`). The licence conclusion is not judged here; only the line reference is noted as moved. **I did not introduce it and did not change it** —
it is inherited from UBUILD1 and my edit left the heredoc untouched.

**Where the MIT came from — the provenance, quoted.**

- `strategy/PUBLICATION_STRATEGY.md:570` — *"public under MIT. The suppression protects nothing, and the
  public copy is citable today."*
- `strategy/PUBLICATION_STRATEGY.md:576` — *"The code/artifact licence split (**PolyForm Noncommercial 1.0.0
  for code, CC BY 4.0 for papers**) stands; what the public repo's **MIT** licence already granted over the
  **public** material cannot be undone for those versions ([`WITHHELD.md`](WITHHELD.md) §8.6; `UNVERIFIED`
  as to prose, which needs counsel)."*
- `strategy/ARCHIVE_WINDOW_CHECK.md:295` — *"the published root is MIT"* (of the target repository).

So the MIT in the build script describes **the target repository's published root** and the
**non-retroactivity** of that grant over versions already public. It is **not** a grant over the new package.

**The binding decision is PolyForm Noncommercial 1.0.0 + a required notice.** `strategy/CODE_LICENSING_STRATEGY.md:9-31`
(the **ERRATA — unit UMEMO1, 2026-10-15**, author clarification, quoted at `:11-14`: *"i wanna keep the core
pieces trade secrets … **so no licence on the main consonance folder that's proprietary**"*): the main
Consonance repository is **proprietary, all rights reserved, no public licence**; **each released piece** is
**source-available, public, PolyForm Noncommercial 1.0.0**, and carries `LICENSE` (PolyForm NC + Required
Notice), `COMMERCIAL.md`, `CONTRIBUTING.md` and a source-available README paragraph (`:25`). Only
**extracted pieces** are released, and the corrected file-by-file table is at §5.1 (`:31`). Independently:
`strategy/WITHHELD.md:132` — *"The subset itself is source-available under **PolyForm Noncommercial 1.0.0**;
its content is covered by the paper's CC BY 4.0 decision"*.

**The templates on disk** (`strategy/licence-templates/RELEASED-PIECE/`): `LICENSE` **5,662 bytes, sha256
`25aa637ba1689e87ad34c5acc25464a4eaaa2f5b2c84e3dc4d7ed84158277cfe`**, `COMMERCIAL.md` 3,379 B,
`CONTRIBUTING.md` 4,111 B. **⚠️ The orchestrator's figure — "4,563 bytes, sha256 `ffcca388…`" — matches
nothing on disk.** I hashed every file under `strategy/licence-templates/` and *no* file has that digest;
the PolyForm template is 5,662 B, not 4,563 B. Treat the quoted size/hash as **unverified** (it may be a
different file, a stale build, or a transcription error).

> **Superseded 2026-10-16 (UFIX24, dated record left unrewritten):** the templates were rewritten after this
> measurement. `strategy/licence-templates/RELEASED-PIECE/LICENSE` is now **5851 bytes**, sha256
> `3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900`, `COMMERCIAL.md` 3512 B and
> `CONTRIBUTING.md` 3036 B; the 5,662 B / `25aa637b…` / 3,379 B / 4,111 B values are the record. The build
> pins the digest at `sha256sum "$DEST/LICENSE"` (`:583`).

**The "fragments … fully MIT" statement does not exist.** I grepped `strategy/` and `orchestration/` for
`fully MIT` and for `fragments` — **no such author statement is on disk.** The nearest real text is
`PUBLICATION_STRATEGY.md:570/576` above, which is about the *public repo's* existing MIT over *already
public* material. **My recommendation: the two are not two categories — "fragments" has no referent here.**
If the author did say it, the quote is not in this workspace and the memo (`UMEMO1`) is later and binding.

**Verdict: MIT is STALE for a released piece; the binding instrument is PolyForm NC 1.0.0 + Required
Notice + `COMMERCIAL.md` + `CONTRIBUTING.md` + a source-available README paragraph.** This changes what the
package ships and adds three files, so it is a **decision for the author/orchestrator, not for a packaging
unit** — hence flagged, not switched.

### 12.2 Licence scope — two licences, one root file, and the division is prose-only

The package declares **code MIT** and **paper text CC BY 4.0** (README table, build-script line 344;
`:380` "everything under a package's `code/` directory, plus any script: **MIT**"; `:383` `eval/` "the same
**MIT** terms"; `:495` `gate.sh` "**MIT**"). The paper declaration comes from the author decision recorded
at `strategy/WITHHELD.md:124` (papers public under **CC BY 4.0**, 2026-10-15) and `:129-133`.

> **Superseded 2026-10-16 (UFIX24, dated record left unrewritten):** build-script lines 344, 380, 383 and 495
> no longer carry the MIT prose quoted here. `:344` is now the emitted root README's package table
> (`code **PolyForm NC 1.0.0** · paper text **CC BY 4.0**`); `:380`–`:382` extracts the source-available
> paragraph from `strategy/licence-templates/README-PARAGRAPHS.md` (heredoc `caseB=` at `:383`); `:495`–`:497`
> is the `run-verification.sh`/`VERIFICATION.txt` path caveat. The MIT framing is the record; the copy/pin
> sites are `:575`/`:579`/`:584` and the appended scope clause `:590`–`:602`.

**Stated plainly: the scope division is DECLARATION-ONLY — it lives in README prose.** There is **no**
per-directory notice (no `code/LICENSE`, no `paper/LICENSE`, no `eval/LICENSE`) and **no** scoping clause in
the root `LICENSE`; the root MIT file nominally covers the whole tree, including `paper/MANUSCRIPT.md`.
That is **materially weaker than a notice**, exactly as the orchestrator suspected: a downstream reuser who
reads only `LICENSE` has no signal that the paper text is CC BY 4.0, and one who reads only the README has
no verbatim licence text. Options, cheapest first — (i) a scoping clause in the root `LICENSE` naming
`paper/` as CC BY 4.0; (ii) per-directory `LICENSE` notices (`code/LICENSE`, `paper/LICENSE`); (iii) both.
Not implemented: it depends on the tier decision at §12.1.

### 12.3 Package count — one package staged; #7 is NOT packageable as a reproducibility package

`$PKG="$DEST/packages/exp12-encoder-crossover"` and `.ucurate1/pre/research-publish-packages/packages/` holds
**only that one package**, although the repository is named for *packages* plural. The second candidate is
`papers/gated-read-batching/` — verified `pass-with-corrections` by UVER10 with corrections applied, and
measured by me as **4 files hard-clean + `DISCLOSURE_CHANGES.md` (19 hits) to drop** (§7).

**Not packageable in this pass — what is missing, exactly.** The "minimal reproducibility subset" norm
(`strategy/WITHHELD.md:129-133`: fixture schema, the fixture, the evaluation harness and the exact commands,
and the pre-registered protocols) is not met, and the material does not exist to meet it:

| needed | status |
|---|---|
| manuscript + claims + refs + gaps | **present**, 4 files, hard-clean |
| raw rows (`gated-read-rows.jsonl`, 9,260 per-decision rows) | **absent outside `state/`** — only mirrors of the read-only target (`./state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/gated-read-rows.jsonl`); live copy is the target's |
| summary (`gated-read-summary.json`) | same — target/mirror only |
| analysis script / harness | **no `repro/gated-read-batching/` exists at all**; `find` for `*gated*read*` outside `state/` returns only `./papers/gated-read-batching` |
| fixture | **none** — nothing to freeze |
| exact commands / pre-registration | **none in the workspace** |

**Scope recommendation (for the orchestrator, not taken here):** either (a) ship it as a **paper-only**
package — the 4 documents, with the explicit statement that the source material is withheld and the `G/R/S/P`
locators resolve in the read-only checkout that is deliberately not redistributed (which is what §7 already
concludes for the encoder package's own locators) — or (b) **withhold** it until a subset is built. What it
must **not** ship as is a "reproducibility package": without rows, script or fixture its numbers cannot be
recomputed by a reader, and `papers/gated-read-batching/**` has no `repro/` counterpart to copy from. Adding
it now would also change the ship list, `NEVER_SHIP`, and the gate total, so it is out of this unit's scope.

### 12.4 What I did NOT do

- Did **not** switch MIT → PolyForm NC (would change shipped bytes and add 3 files; author's call).
- Did **not** add per-directory licence notices or a scoping clause.
- Did **not** add `papers/gated-read-batching/` or create a second package.
- Did **not** widen write paths, and did **not** run the real build.
- Left the staged tree in place, as instructed.

### 12.5 OPEN DEFECT — `redact.py` stage D can assert identity it does not have

**Recorded by UFIX12 from UREDACT3; contradicted by UVER12 and corrected here.** The original claim was that
`repro/encoder-crossover-190-SANITISED/redact.py` stage D writes the *source* digest into `MANIFEST.json`'s
`sha256` field while leaving `identical_to_source: true`. UVER12 re-checked it (see
`strategy/VERIFICATION_REPORT_12.md`) and found the opposite. **The verified position is:** the stage-D code at
`repro/encoder-crossover-190-SANITISED/redact.py:855-895` recomputes `flag = (sh == h)` correctly, so stage D is
correct; the **regenerated** MANIFEST has **25** flag-True rows and **0** contradictions, and the **8**
contradictions are in the **stale shipped** `repro/encoder-crossover-190-SANITISED/MANIFEST.json` — UREGEN1's
**6** (`EXCLUDED.md`, `INTEGRITY.md`, `LICENCE_TODO.md`, `README.md`, `harness/LEAD-WIRING.md`,
`harness/collect.py`) plus **2** pre-existing at source (`DECISION_CASE_SCHEMA.ts`,
`EXP12-typed-channel…prereg.md`). **So the defect is the stale committed MANIFEST, not the generator** — the
fix is to regenerate and commit it, not to change `redact.py`.

History: UREDACT3 found **6** stale identity rows and proposed a stage-D fix (evidence
`repro/encoder-crossover-190-SANITISED/REDACT3_REPORT.md:281-290`); UVER12 contradicted that claim.
**Correction added by UFIX15 on 2026-10-15; contradicting verifier: UVER12; source of the original claim's shipped rows: UREGEN1.**
