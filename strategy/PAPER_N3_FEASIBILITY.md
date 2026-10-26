# PAPER_N3_FEASIBILITY.md — can candidate N3 be written from what is on disk?

**Unit:** UREVER3 (feasibility only — no drafting, no prose). **Workspace:** `/home/zer0null/reserach extarctor`.
**Subject:** candidate **N3** — *an independent-verification protocol and a taxonomy of the defect classes it
catches.* **Hard bound:** 20 tool calls. Every count below carries the command that produced it.

All measurements were taken 2026-10-16 against the live disk. **Nothing here is taken from a prior summary.**

---

## 1. The corpus (MEASURED)

| Record class | Count | Bytes | Command |
|---|---|---|---|
| Unit cards `orchestration/units/*.md` | **415** | **1,472,601** | `ls -1 orchestration/units/*.md \| wc -l`; `cat orchestration/units/*.md \| wc -c` |
| …plus one non-`.md` unit artifact | 1 | `UBUILD1.build.sh` | `ls orchestration/units/ \| grep -v '\.md$'` |
| Handoffs `orchestration/handoffs/*.json` | **427** | **3,317,592** | `ls -1 orchestration/handoffs/*.json \| wc -l`; `cat … \| wc -c` |
| …of which JSON-parseable | **427 / 427** (0 unparseable) | — | python3 `json.load` loop over `glob('orchestration/handoffs/*.json')` |
| …of which `V*`-named | 60 | — | `ls -1 orchestration/handoffs/V*.json \| wc -l` |
| Verdicts file `orchestration/VERDICTS.md` | **3,309 lines** | **349,291** | `wc -c -l orchestration/VERDICTS.md` |
| …`## V<n>` sections in it | **53** | — | `grep -cE '^## V[0-9]' orchestration/VERDICTS.md` |
| …total `## ` sections | 63 | — | `grep -cE '^## ' orchestration/VERDICTS.md` |
| Verification reports `strategy/VERIFICATION_REPORT*.md` | **36** | **493,439** | `ls -1 strategy/VERIFICATION_REPORT*.md \| wc -l`; `du -cb … \| tail -1` |
| Entire `strategy/` tree | 118 files | (see `du -b strategy/*`) | `ls -1 strategy/` |

**Date range (mtime).** Handoffs: `2026-10-08 05:52:04` (`D1.json`) → `2026-10-16 14:52:48` (`VUFMT1.json`).
Unit cards: `2026-10-08 05:52:04` (`D1.md`) → `2026-10-16 17:07:37` (`UREVER2.md`). **Nine calendar days**,
one continuous batch sequence. Commands: `stat -c '%y' $(ls -1 orchestration/handoffs/*.json | head -1)` and
`… | tail -1)`.

**Corpus total for a release:** 415 cards + 427 handoffs + VERDICTS.md + 36 verification reports =
**5,632,923 bytes ≈ 5.4 MiB** across **1,259 files**.

---

## 2. The protocol as run (MEASURED, with quotes from `AGENTS.md`)

`AGENTS.md` states the contract. Quoted verbatim (the load-bearing clauses):

- Unit contract §4: *"**Persist your own card** to `orchestration/units/<UNIT>.md`."*
- Unit contract §5: *"Every unit ends by writing `orchestration/handoffs/<UNIT>.json` … A handoff MUST be valid JSON."*
- Unit contract §5: *"**Two handoff shapes are contracted** … The seven keys above define the **unit handoff**
  (a unit's report of its own work). A **verifier verdict** … is a *different* shape with a different job."*
- Unit contract §6: *"**Fresh context per unit.** … **No unit is ever extended** — it is superseded by a new unit."*
- Verification independence: *"Every batch gets a **separate verifier unit that is not the author**. It re-runs
  the evidence commands, checks the plan's clause, and includes a **red→green** check on at least one guard …
  Verdicts are recorded in `orchestration/VERDICTS.md`."*
- Hard constraints: *"**Never run a bare `git status` against a target** … of **136** handoffs carrying **194**
  target-referencing command strings, **62** ran a plain `git -C /home/zer0null/Duval … status` and **0** ran a
  target-mutating verb."*

### What the records show

**Shape separation is real but the `V*` prefix is not the discriminator.** Measured: **97 handoffs are
verdict-shaped** (carry `overall` or `checks`) and **330 are unit-shaped**. But only **60** are named `V*`. So
**37 verdict-shaped handoffs do not use the `V` prefix** — every `UVER<n>` handoff (UVER2, UVER4–UVER13,
UVER17, UVER21, UVER24, UVER28–UVER34, UVERAD6) plus `VUFIXTREE1`, `VUFMT1`, `UTRACE1`. A paper that says
"verifiers are the `V*` units" is off by 37/97 (38%).
Command: python3 loop over handoffs testing `'overall' in d or 'checks' in d`.

**Top-level key presence across all 427 handoffs (MEASURED).** `unit` 427 · `blocker` 424 ·
`next_unit_hint` 423 · `write_paths` 422 · `status` 361 · `evidence` 343 · `artifacts` 334 · `bound` 142 ·
`tool_calls` 124 · `checks` 96 · `overall` 95 · `overstated` / `not_reproduced` / `unverified` 84 each ·
`red_green` 70 · `containment` 59 · `corrections` 49 · `scope` 47 · `contradicted` 36. Command: python3
`collections.Counter` over `json.load` of every handoff.

**Verdict values (MEASURED).** `overall`: `PASS` 33 + `pass` 10 = **43 pass**; `PARTIAL` 18 + `partial` 18 =
**36 partial**; `pass-with-corrections` **12**; `FAIL` **4**. **Two spellings coexist** (`PASS`/`pass`,
`PARTIAL`/`partial`) — a normalisation hazard any recomputation must handle.

**⟂ Places the records show the protocol NOT followed:**

1. **The append-only / "never overwritten" claim is not verifiable for 90% of the corpus.** The workspace is a
   git repo with **5 commits, all dated 2026-10-08** (`git log --oneline | wc -l` → 5; `git log --format='%ad'
   --date=short | head -3` → all `2026-10-08`). Only **3 commits** touch `orchestration/VERDICTS.md` or
   `orchestration/handoffs/`. Everything from **2026-10-09 to 2026-10-16** — the overwhelming majority of the
   427 handoffs — is **uncommitted**, so an overwrite in that window is **undetectable**. The "dated and
   appended rather than overwritten" property is **asserted by prose, not evidenced by history**, for the whole
   period the paper would draw on.
2. **The protocol's own frozen figure does not reproduce.** `AGENTS.md` claims 136 handoffs / 194
   target-referencing command strings / 62 plain `status` / 0 mutating. Re-measured by deep recursive string
   extraction over all 427 handoffs: **134 files / 215 target-git strings / 86 plain `git … status` / 17 with
   `--no-optional-locks` / 0 genuinely mutating** (the 9 regex hits are prose mentions, `tail .git/logs/HEAD`,
   `find … -newermt`, `merge-base --is-ancestor`, `rev-list --count` — all reads). So the headline count is an
   **undercount (62 vs 86)** and the handoff count is off by 2. The *conclusion* (0 mutating) survives; the
   *number* does not. This is a self-instance of the very defect class the paper would claim to catch.
   Command: python3 recursive `walk()` collecting every string, then regex filters.
3. **The handoff shape census in `AGENTS.md` is stated as a measurement "at the time it was written"** (43 `V*`
   handoffs, U8.18). It is now **60**. A paper citing it must date-stamp it or recompute.
4. **One `.build.sh` lives under `orchestration/units/`** (`UBUILD1.build.sh`, untracked by git — a sibling
   handoff records `?? ` in `git status`), so "units are `.md` cards" is false as stated.

---

## 3. The defect classes, re-derived from the verifier verdicts

Built **only** from the machine-readable fields, not from prose. **573 recorded finding entries** across 97
verdict-shaped handoffs:

| Field (class as recorded) | Entries | Handoffs with ≥1 | One-line definition (as the field is used in practice) |
|---|---|---|---|
| `contradicted` | **49** | 23 | The recorded claim is **false** against the artifact/state it names. |
| `overstated` | **178** | 73 | The claim is directionally right but **exceeds** what the evidence supports (wrong magnitude, missing qualifier, stale-but-same-shape). |
| `not_reproduced` | **169** | 62 | Re-running the stated measurement **does not yield** the recorded figure. |
| `unverified` | **177** | 73 | Named, relevant, and **not checked** — the verifier's own honesty ledger. |

Command: python3 loop summing `len()` of each field over the 97 verdict-shaped handoffs (`inst()` treats
string/dict/list forms).

These four **are** a taxonomy with counts and are recomputable from the handoffs alone. **But they are the
verifier's own schema, not independently derived classes** — a paper must say which it is.

### Mechanism classes I re-derived (INFERRED from quoted text, not from a recorded field)

**MC-1 — live-path arithmetisation / stale pin.** A number true of a *live* path is cited after the path
moved; the pinned copy differs. Instances: **≥3 concrete sites, and 135/427 handoffs mention `stale`**
(coarse grep; most mentions are incidental). Instances:
- `orchestration/handoffs/UTRACE1.json` `contradicted[0]`: `"docs/LIVE_TARGET_NOTES.md:50 — 'traces/2026-09-28-duval-m0.jsonl | 431605e6 (866816 B)' as the working-tree state: live is now 35687221b1a19d540534ff601ee233f67b814f643243bc933107ce703bff075d / 1,624,082 B."`
- `orchestration/handoffs/UTRACE1.json` `overstated[0]`: `"strategy/CONTAINMENT_CHECK.md:261-262 — 'grew from 866816 B at our pin to 1570243 B now': the start is right, the 'now' is stale (1,624,082 B) and is not the pin; the pin is 866,816 B."`
- `orchestration/handoffs/UTRACE1.json` `not_reproduced[1]`: `"no pattern-set reading reproduces '1031 gate hits' on any state: pinned 712 occurrences / 573 gated lines, blob 2ec22a67 1205 occurrences / 1031 gated lines, live 1262 / 1087."`
Verdict: **a genuine class (3+ instances)**.

**MC-2 — the closing message is a claim, not evidence.** A unit's final report states a count its own artifact
contradicts. Instances: **≥2 strong**, 8 handoffs have `contradicted` entries mentioning a census/count.
- `orchestration/handoffs/UNEUTRAL4.json` §4: author (UNEUTRAL3) claimed bij census `TOTAL 8,213 · 99 of 184`;
  the verifier's re-run gives `TOTAL 5,384 · 95 of 184`, marked **`[U3✗U4] contradicted`**. Its §9 records
  *"The claimed bij census `8,213` / `99 of 184` has no on-disk source… no scanner exists under
  `scratch/uneutral3/`, so the number cannot be regenerated by any command I could find."* The same file
  records the author's digest `30b75581…` as belonging to a **superseded 20:06 build** (`rt/bij`) that no longer
  exists on disk, while the on-disk tree and two fresh rebuilds give `c7696edc…`.
- `orchestration/handoffs/U6.13.json`, key `census.note`: `"12 was correct for project-authored reads; wrong as a census of what the server serves. Pre-fix anonymous reachable on remote = 14; post-fix = 0."`
Verdict: **a genuine class (2 strong + 1 adjacent)** — at the `contradicted`-instance level it is well
supported; at the "recurring named mechanism" level it is **thin**.

**MC-3 — line-count-neutral edit ⇒ citation/digest rot.** Content changes, line count is preserved, so every
line-number citation still *resolves* while the bytes (and any digest pinned to them) have moved. Instances:
**1 primary; the string `line count` appears in 17 handoffs; explicit neutrality declarations in 4.**
- `orchestration/handoffs/UFIX15.json`, key `line_count_neutrality`: `"all 12 edited regions replaced with the same number of lines; every edited file's total line count unchanged (BS 1019; manifest, UCURATE1, UTOK1, REPORT unchanged), so existing citations to those files (e.g. PUBLISH_PACKAGE_MANIFEST.md:70,469) still resolve."`
  Same handoff, key `build_script_sha256_after`: `"…UBUILD1.build.sh, 1019 lines. UFIX15's prose edits at :500 and :520-521 necessarily change the digest; the LINE COUNT is preserved at 1019, so all line-number citations to this file still resolve. UFIX14's cited sha256 5c837c8d… is therefore now superseded by the UFIX15 prose edit."`
- `orchestration/handoffs/UCAND1.json` `next_unit_hint` uses the mirror-image test: `"(2) append-only check that sections A-F of PAPER_CANDIDATES.md and sections 0-12 of PUBLICATION_STRATEGY.md are unmodified (line counts 982 and 408 before the appended G and 13)"` — i.e. the corpus' own check for "unchanged" is a **line count**, the exact proxy MC-3 shows to be insufficient.
Verdict: **a real, precisely recorded phenomenon, but an ANECDOTE, not a class — one primary instance.** The
underlying general lesson (line count is not an integrity proxy; digests are) is strongly supported; the
*class* is not.

**MC-4 — superseded-build artifact.** A figure belongs to a build that no longer exists on disk.
Instances: **≥2**. The `30b75581…` digest above; and `orchestration/handoffs/UVER11.json` `contradicted`:
`"strategy/PUBLISH_PACKAGE_MANIFEST.md:286 says the unmodified ship set with no transform is 218 and 152 after
the three path rules; the artifact yields 156 untransformed (152 post-transform + 4 path-only lines)…"` with
`not_reproduced: "218 untransformed ship-set figure (artifact gives 156)"`. Grep `superseded build` → 2 files.
Verdict: **a real class (2 instances) — at the boundary; state it as 2, not as "recurring"**.

**MC-5 — the build consumed the wrong input tree.** `strategy/BUILD_INPUT_PIN.md` (unit UGATE1), headline:
*"the 59/46/13 split attributed in the literature to the build's input is in fact the **sanitised** tree's
split; `tree-three-r2` holds the 45 re-tagged staged paths."* The build's default input is
`scratch/ubij3/tree-three-r2/` (45 files), not the 59-file `repro/encoder-crossover-190-SANITISED/` that the
attributed split describes. Also `strategy/BUILD_PIN_CHANGE.md` (unit UFIXPIN1): the promoted tree was changed
`urecut1` → `uneutral10` in `orchestration/units/UBUILD1.build.sh:134` (`PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"` → new value), sha `bbf5a52c…` → `7bd71f8a…`.
Verdict: **real and consequential; 1–2 instances — a case study, not yet a class.**

**MC-6 — unreproducible frozen figure.** `AGENTS.md`'s own 136/194/62/0 census (see §2.2) plus the UFIXPIN1/BUILD_INPUT_PIN note that `MANIFEST.json` records no digest of the tree it derived from. Verdict:
**1 self-instance; honest but thin.**

**Classes with exactly one instance, therefore anecdotes, not classes:** MC-3 (line-count neutrality), MC-5,
MC-6.

---

## 4. The strongest instances the protocol caught

1. **A verifier contradicted its author on the central census.** `orchestration/handoffs/UNEUTRAL4.json` — the
   author's `8,213 / 99 of 184` vs the verifier's re-run `5,384 / 95 of 184`, marked `[U3✗U4] contradicted`,
   plus the finding that **no on-disk scanner can regenerate the author's number at all**.
2. **A stale trace pin that had been cited as current.** `orchestration/handoffs/UTRACE1.json` —
   `contradicted[0]`/`overstated[0]`: the pinned trace is 866,816 B; the live path had grown to 1,624,082 B,
   and `1570243 B "now"` was itself stale.
3. **A gate count that no state reproduces.** `orchestration/handoffs/UTRACE1.json` `not_reproduced[1]`:
   *"no pattern-set reading reproduces '1031 gate hits' on any state"* — 1,031 turns out to be a **line** count,
   not a gate count.
4. **A build reading a different tree than the one its split describes.** `strategy/BUILD_INPUT_PIN.md`: 59/46/13
   describes the sanitised tree; the build's default input is the 45-file `tree-three-r2`.
5. **The protocol's own census failing to reproduce.** `AGENTS.md`'s 62 plain `git status` vs my measured **86**
   (0 mutating either way).

---

## 5. What a reader could check (the honest failure mode)

**The single most important sentence in this report: almost everything a reader would care about is on trust.**

A reader of N3 could **verify from a release**: the **counts** in §1 and §3 (they are pure functions of the
handoff JSON and the file list), the **JSON validity** of all 427 handoffs, the **shape distribution**
(97/330), the **verdict value distribution**, and every **quoted field value** in §3 — because the quotes are
short excerpts of machine-readable fields in ~5.4 MiB of records.

A reader **could not verify, and would have to take on trust**:
- whether any verdict was **correct** — that requires the artifacts the verdicts are about (`/home/zer0null/Duval`,
  the `scratch/*` trees, model runs, fetched web pages), none of which is in the release subset and most of
  which **cannot be released** (read-only third-party target, or licence/disclosure-bound);
- whether the protocol was **actually followed** as claimed — independence is asserted by naming, not proven;
  there is no signature, no separate identity, and no timestamped launch record tying a verifier to an author;
- whether corrections were **appended rather than overwritten** — the git history stops at 2026-10-08 (§2.1);
- the **mechanism labels** in §3 (MC-1…MC-6) — those are **my inference from prose**, exactly the kind of
  evidence §"Rules" forbids as a basis for counting; a reader cannot recompute them because no field records
  them.

So the paper's *empirical* half is checkable; its *explanatory* half (the taxonomy) is **not**, and the paper
must say so.

---

## 6. The minimal reproducible subset

To recompute **every count in §1 and §3** (and re-parse every quote), a release needs exactly:

| Path | Files | Bytes |
|---|---|---|
| `orchestration/handoffs/*.json` | 427 | 3,317,592 |
| `orchestration/units/*.md` (+ `UBUILD1.build.sh`) | 416 | 1,472,601 |
| `orchestration/VERDICTS.md` | 1 | 349,291 |
| `strategy/VERIFICATION_REPORT*.md` | 36 | 493,439 |
| **Total** | **880** | **5,632,923 (≈5.4 MiB)** |

**If only the verdict counts (§3) are claimed, the release shrinks to `orchestration/handoffs/*.json` alone:
427 files, 3,317,592 bytes.** That is small enough to release. **But counts are all it recomputes** — no
verdict's correctness and no mechanism label survives that cut. If the paper claims any class beyond the four
recorded fields, **the counts cannot be recomputed from a subset small enough to release**, because the class
labels would have to be re-derived by re-running the verifier checks against artifacts that cannot be shipped.

---

## 7. Verdict

**(b) Draftable after one named measurement — with a scope reduction that must be accepted.**

- **Draftable now, and properly evidenced:** the protocol description (§2) and the **verdict-field taxonomy**
  (§3 header table: `contradicted` 49 / `overstated` 178 / `not_reproduced` 169 / `unverified` 177 over 97
  verdict-shaped handoffs) — these recompute from a 3.3 MiB releasable subset, and the paper's own §2 must
  carry the non-compliance findings (uncommitted corpus, the 37 mis-named verifiers, the unreproducible
  `AGENTS.md` census).
- **Not supported as written:** a *taxonomy of recurring nameable **defect classes*** at the mechanism level.
  After re-deriving from the verdicts rather than from prose, only **MC-1 (stale pin, ≥3)** and **MC-2
  (closing-message-as-claim, 2 strong)** reach multiple instances; **MC-3 (line-count-stable citation rot)**,
  **MC-4**, **MC-5**, **MC-6** have 1–2 instances each and are **anecdotes**. The user's two example classes are
  both *real* — the line-count one is the weakest (one instance) and the claim-not-evidence one is the stronger
  (two, one of them documented to an unrecoverable source).
- **The named measurement that would settle it:** a fresh, blind pass over the 97 verdict-shaped handoffs that
  assigns each of the 573 entries a **mechanism label against a published rubric** (with the label field
  written into the record), then a recount. Until that pass exists, mechanism class counts are not recomputable
  and the taxonomy claim rests on the author's prose.
- **Strongest spine if drafted:** **`contradicted`** — 49 instances across 23 handoffs, anchored on
  `orchestration/handoffs/UNEUTRAL4.json` (a verifier disproving its author) and
  `orchestration/handoffs/UTRACE1.json` (a pinned-vs-live trace that moved under a cited claim). It is the
  smallest class, the most consequential per instance, and the only one whose instances are individually
  quotable from machine-readable fields.

---

## Measured / inferred / could not determine

**MEASURED (command + output given in-line above).** All counts and byte figures in §1; 427/427 handoff JSON
validity; 97 verdict-shaped vs 330 unit-shaped; 60 `V*`; `overall` distribution 43 pass / 36 partial / 12
pass-with-corrections / 4 FAIL; finding counts 49/178/169/177; key-presence table; mtime ranges; VERDICTS.md
3,309 lines / 349,291 B / 53 `V` sections; 36 verification reports / 493,439 B; workspace git history = 5
commits, all 2026-10-08, 3 touching verdicts/handoffs; deep git-command re-extraction 134/215/86/17/0; the
`AGENTS.md` 136/194/62/0 claim not reproducing.

**INFERRED (stated as such).** The mechanism classes MC-1…MC-6 and their assignment; the claim that the 37
non-`V` verdict-shaped handoffs are verifier units (inferred from their `unit` ids, `overall` key and prose —
not from a recorded role field); the 5.4 MiB release subset as sufficient for the §3 counts; the reading that
`UCAND1`'s "line counts … unmodified" check is an instance of MC-3's proxy.

**COULD NOT DETERMINE.**
1. Whether **any** verdict is *correct* — the artifacts are out of scope/unreleasable; I did not re-run them.
2. Whether corrections were **appended vs overwritten** after 2026-10-08 — no VCS history exists for that window.
3. Whether verifier **independence** actually held (author ≠ verifier) — no machine-readable author field exists
   on the verdict shape; I did not cross-check all 97 verdict units against their subject units, so the
   "separate verifier" claim is **untested here**, not confirmed.
4. Why 24 handoff paths render in tool output as `<redacted:high-entropy:…>` while a programmatic
   `os.path.basename` vs `unit`-field comparison shows **0** mismatches — the redaction is applied at
   output-render time, not on disk; I could not determine the trigger. (It is a *reproducibility* hazard:
   a reader re-reading those files through a guarded tool sees a redacted path.)
5. The true count of mechanism-class instances for MC-4/MC-6 under a consistent rubric.
