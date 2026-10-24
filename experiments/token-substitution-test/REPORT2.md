# REPORT2 — UTOK2: re-baselined substitution, extended to the residuals UTOK1 left

**Unit:** UTOK2 (only unit running). **Date of measurement:** this session.
**Source of truth:** the *present* bytes of `repro/encoder-crossover-190-SANITISED/` — nothing in `repro/`,
`papers/`, `experiments/second-labeller-190/` or `/home/zer0null/Duval` was written or read by any
script that changes state. All work happened on copies under `experiments/token-substitution-test/`.

**One-line verdict:** against the current bytes the substitution re-baselines cleanly; the ten CLAIMS
numbers hold 10/10; the scoring-projection digest moves (`57a29b4e…` → `d52893f4…`, declared); the hard-fail
gate falls **407 → 158** lines; the 2 protected option labels are **only partly** substitutable — they are
read by the route-A scorer and substituting them moves exactly one shipped number (`routeA.ties` 120 → 119,
§5 below) while leaving every headline value unchanged.

---

## 0. Verdict table

| Question | Answer |
|---|---|
| Baseline reproducible against present bytes | **yes** — source tree == `work2-orig` byte-for-byte, 58/58 files |
| Is the ten-value claim set preserved? | **yes — 10/10 unchanged** |
| scoring-projection digest | **moved**: `57a29b4e…` → `d52893f4c6d5502b906d679203e321dfb652ac98e07196b5baa06f9533d66676` (declared, expected) |
| train / dev digests | **same** (byte-identical before and after) |
| fixture-correctness digest | **same** (`8dd05ce6…`) |
| Option labels (a) substitutable | **partial** — no CLAIMS value moves, but `routeA.ties` 120 → 119, so shipped `metrics.json` stops regenerating byte-identically |
| Frozen `results/*.json` (b) substitutable | **yes** — display/evidence only; nothing reads their label strings |
| `harness/data/manifest.json:5,10,15` (c) | **3/3 neutralised**, manifest still valid JSON — but not durable (§7.4) |
| `/home/zer0null` + `duval` lines (d) | **0 remaining tree-wide** (was 5 lines / 10 pattern hits) |
| Hard-fail gate, before → after | **407 → 158** lines |
| Patterns that reach zero | `/home/zer0null`, `duval`, `src/scope`, `src/layer`, `admit(` (plus the 8 that were never present) |
| Patterns that do **not** reach zero | `publish-present-compete`, `EXCLUDED.md`, `REDACTION_REPORT`, `RESIDUALS.md`, `LICENCE_TODO`, `TRADE_SECRET`, `VERIFICATION_REPORT`, `StateClass`, `grantPolicy`, `src/broker`, `expanded[` — curation, not substitution (§7) |

---

## 1. Method and artefacts

* Engine: `experiments/token-substitution-test/substitute2.py` — UTOK1's 14-entry prose/question
  `MAPPING` (read from `experiments/token-substitution-test/mapping.json`) plus
  * path rules `/home/zer0null/Duval/`→`<target-repo>/`, `/home/zer0null/Duval`→`<target-repo>`,
    `/home/zer0null`→`<user-home>`;
  * `.json`/`.jsonl` are substituted as text and then checked with an object-diff guard that **aborts a
    file** if any change lands under the identity keys `id / kind / _line / sha256 / sourceSha256 /
    sha256_16 / correct / recorded_index / goldIndex / predIndex`;
  * `fixture/reflex-decisions.ts` is span-limited to the `question` / `options` / `rationale` /
    `namespaces` fields;
  * `.py` / `.sh` / `.bash` are **never** touched.
* Trees (all under `experiments/token-substitution-test/`):
  * `work2-orig/` — pristine copy of the current `repro/encoder-crossover-190-SANITISED/` (hash reference).
  * `work2-pre/` — second pristine copy used for the "before" acceptance run.
  * `work2-substituted/` — the extended-substitution tree (the released-candidate).
  * `work2-labels-only/` — probe: **only** the 2 option labels changed (attribution of the `ties` move).
  * `encoder-crossover-190/` — copy of `repro/encoder-crossover-190` (the as-audited control that
    `verify/run-verification.sh` requires as a **sibling** of the tree under test).
* Logs: `logs2/` — `substitution2.txt`, `before2.txt`, `after2.txt`, `labels-only.txt`,
  `recompute-before2.txt`, `recompute-after2.txt`, `gate-{pristine,before,after}.txt`,
  `gate-table.txt`, `tree-hashes-{source,before,after}.txt`.

## 2. Step 1 — re-baseline (what UTOK1 could not do)

```
tree digest recipe:  cd <tree> && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum
repro/encoder-crossover-190-SANITISED  6bda08858d521691d677e931449cde0ac7f3e5be0ec909b196b5145fc1b789d6  58 files
work2-orig                             6bda08858d521691d677e931449cde0ac7f3e5be0ec909b196b5145fc1b789d6  58 files
work2-substituted                      080185fd176cbd3579c9933250a96d2b2015709de664e44e4829656f98f64e3d  58 files
SOURCE == work2-orig byte-identical:  yes (per-file sha256sum lists diff-clean; logs2/tree-hashes-source.txt vs logs2/tree-hashes-before.txt)
files changed by the extended substitution: 21 of 58, no files added or removed
```
`work2-pre` differs from `work2-orig` only in `verify/VERIFICATION.txt` — the acceptance script itself
regenerates that log (§7.5), which is why the "before" column of the gate table is not byte-identical to
the pristine column. (An earlier aggregate figure `3cd93105…` came from a differently-globbed copy and is
superseded by the recipe above.)

## 3. Step 2 — the extended substitution

Per-file change counts (from `logs2/substitution2.txt`, 0 aborts):

| file | changes | rule |
|---|---|---|
| `fixture/reflex-decisions.ts` | 48 | `fixture-spans` — 46 `question` fields + 2 `options` fields |
| `harness/data/fixture-190.json` | 48 | text + identity-key guard |
| `variants/no-union/files/fixture/reflex-decisions.ts` | 60 | global |
| `REDACTION_REPORT.md` | 56 | global |
| `SCRUB_REPORT.md` | 14 | global |
| `results/eval-shuffled-label.json` | 10 | text + guard |
| `results/eval-deberta-v3-base.json`, `results/eval-majority-class.json` | 9 each | text + guard |
| `results/eval-modernbert-base.json`, `results/eval-setfit-mpnet.json` | 8 each | text + guard |
| `results/baselines.json` | 6 | text + guard |
| `verify/redaction-log.json` | 6 | text + guard |
| `second-labeller/disagreements.jsonl` | 5 | text + guard |
| `second-labeller/EVIDENCE.md` | 4 | global |
| `fixture/DECISION_CASE_SCHEMA.ts`, `variants/…/DECISION_CASE_SCHEMA.ts` | 3 each | global |
| `harness/data/manifest.json` | 3 | text + guard (lines 5, 10, 15) |
| `RESIDUALS.md`, `verify/RESIDUAL-SCAN.txt` | 3 each | global |
| `second-labeller/RUN.json` | 1 | text + guard |
| `verify/VERIFICATION.txt` | 73 | global (and then regenerated by the acceptance run) |

Identity fields are provably untouched: the `id`/`kind`/`correct` lines of `fixture/reflex-decisions.ts`
diff clean, and `harness/data/fixture-190.json` has identical `id`/`kind`/`correct` for all 190 cases with
**exactly 2 option-label strings changed**. Instrumentation is byte-identical:
`redact.py`, `verify/run-verification.sh`, `verify/recompute-claims.py`, `second-labeller/parse_fixture.py`,
`harness/prepare.py`, `harness/tccommon.py`, `second-labeller/compare.py`.

### 3.1 The four residual classes

**(a) the 2 protected `expanded[]` option labels** — now `"the EXPANDED_A ref list"`, at
`fixture/reflex-decisions.ts:572`, `harness/data/fixture-190.json:573`,
`variants/no-union/files/fixture/reflex-decisions.ts:572`, and as an option-label dict key at
`results/eval-modernbert-base.json:343`. Result: **partial** — see §5.2.

**(b) frozen `results/*.json`** — substituted (6–10 changed lines each; byte length unchanged, e.g.
`results/eval-modernbert-base.json` 81268 → 81268 bytes). Nothing in the shipped code reads their label
strings: `verify/recompute-claims.py` consumes only `id` / `correct` / `accuracy` (and
`models['decider-4b-exp11-reproduction'].perCase`), and it returns
`ALL CLAIM NUMBERS PRESERVED: True`. They are **display/evidence only** → substitutable.

**(c) `harness/data/manifest.json:5,10,15`** — 3/3 neutralised and the file still parses:
```
"path":   "<target-repo>/.worktrees/integration/tools/typed-channel/data/corpus.json"
"path":   "<target-repo>/.worktrees/integration/tools/typed-channel/data/fixture-190.json"
"report": "<target-repo>/.worktrees/integration/tools/typed-channel/data/lint-report.json"
```

**(d) remaining `/home/zer0null` / `duval` lines** — the same 5 lines (the two `DECISION_CASE_SCHEMA.ts:2`
comment headers and the three manifest lines) are neutralised; `grep -riI -e /home/zer0null -e duval` over
the whole substituted tree now returns **0**. The `907fa39` revision anchor in those headers is **kept**:
`//   target: <target-repo>/evals/fixtures/reflex-decisions.ts (HEAD 907fa39)`.

## 4. Step 3.1 — the ten CLAIMS values

Run: `bash work2-substituted/verify/run-verification.sh /tmp/utok2-after` (exit 0) and
`python3 work2-substituted/verify/recompute-claims.py` (exit 0). The "before" run used the same commands on
`work2-pre`.

| # | value | before | after | verdict |
|---|---|---|---|---|
| 1 | comparison cases | 190 | 190 | unchanged |
| 2 | options_total | 721 | 721 | unchanged |
| 3 | routeA kappa (CLAIMS 0.3252) | 0.32520740993294694 | 0.32520740993294694 | unchanged |
| 4 | routeB agreement | 0.9052631578947369 | 0.9052631578947369 | unchanged |
| 5 | routeB kappa | 0.9013584840356494 | 0.9013584840356494 | unchanged |
| 6 | n_disagreements | 18 | 18 | unchanged |
| 7 | AB mutual agreement (CLAIMS 0.3526) | 0.3526315789473684 | 0.3526315789473684 | unchanged |
| 8 | closed-subset kappa (CLAIMS 0.8837) | 0.8837023738280471 | 0.8837023738280471 | unchanged |
| 9 | roster/bespoke kappa (CLAIMS 0.9140) | 0.9139973672663448 | 0.9139973672663448 | unchanged |
| 10 | disagreements_count_routeB | 18 | 18 | unchanged |

`recompute-claims.py` on the substituted tree: modernbert 0.3473684210526316, majority 0.45263157894736844,
chance floor 0.29105263157894734, quoted 0.6684, decider-4b reproduction 0.6789473684210526,
counts 39+27+90+34 = 190 — every line `OK`, `ALL CLAIM NUMBERS PRESERVED: True`.
**values_unchanged = 10/10, values_moved = []**.

## 5. Step 3.1 (continued) — the four digests, and the one shipped number that moves

| digest | before | after | verdict |
|---|---|---|---|
| scoring-projection `(id,kind,question,options,correct)` | `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300` | `d52893f4c6d5502b906d679203e321dfb652ac98e07196b5baa06f9533d66676` | **moved** (§5.1) |
| `harness/data/train.jsonl` | `24c39afa8606942ac2f4fb3e6f1ce5c2b0c9ee581b67d1aed38260d4aa020c09` | same | unchanged |
| `harness/data/dev.jsonl` | `d311a99f0d5b2bd8bcff03e9913b3857ec4c98ffd3714ce9a7afa42514eaa976` | same | unchanged |
| fixture-correctness `[[id,correct,len(options)]]` | `8dd05ce6fe31f6bef484e97bed9ec8c96fb5f2c0b17ebb20ff57afb8716c106a` | same | unchanged |

### 5.1 The projection digest moves again — declared

`d52893f4c6d5502b906d679203e321dfb652ac98e07196b5baa06f9533d66676` on the fully-substituted tree. It
differs from UTOK1's `75d4b0a22c50eb7fe80ccdee5ffaecdb647f4373a90fae34e3dd0468cbb91a69` because UTOK1
measured an 18:17 snapshot that is not reproducible; **this** value is against the present bytes. A digest
that moves when `question`/`options` change is expected and is declared here. No CLAIMS value moves.

### 5.2 Answer to (a): the option labels are only PARTLY substitutable

`verify/run-verification.sh` §5 regenerates `second-labeller/metrics.json` in each scratch tree and compares
them. Before substitution the pristine release regenerates `orig == san` and `san == shipped` exactly
(`while initial`: `True`, `True`). After the extended substitution both become `False`, and a full
key-by-key walk of the two regenerated metrics files finds **exactly one content difference**:

```
DIFF /routeA/ties   120 (as-audited) != 119 (substituted)
```

(plus the four hand-added documentation keys `_correction`, `limitation`, `passes/labelsB.json/limitation`,
`routeB_primary/limitation` which the script deliberately strips). **Attribution probe:** a tree where
**only** the 2 option labels were changed (`work2-labels-only/`, no question substitution at all) reproduces
the same single difference `/routeA/ties 120 != 119` — so the movement is caused by the labels, not by the
prose mapping. `second-labeller/compare.py` really does read option text to score
(`route_a` = `len(tokens(option) ∩ tokens(question))` + 0.5 if the normalised option is a substring of the
question, argmax, ties → lowest index), so a metric that depends on ties moves. What does **not** move:
route-A agreement/κ, route-B agreement/κ, `n_disagreements` 18, `AB_mutual_agreement`, both stratification
κ, and all ten CLAIMS values. The labels-only probe's projection digest is
`2e7bc1842a7ec23a49e84a2ff281eed26c8bb6e8867c47c9a1e714d0ca403ec2`.

Consequences for a released fixture: the 2 label strings are safe to substitute **for every checked claim**,
but the shipped `second-labeller/metrics.json` must then either be regenerated (and mention `ties: 119`) or
the change must be declared, because the acceptance script's own "sanitised regeneration == shipped"
equality will read `False`. `routeA.ties` appears in no CLAIM.

### 5.3 The other `run-verification.sh` self-checks (all differences are intended consequences)

* §3 `empty_rationales 190 / empty_namespaces 190` in the sanitised scratch vs `0 / 0` in as-audited: a
  property of the shipped sanitised release (its rationales/namespaces are emptied by design), not of this
  substitution.
* §6 five rows, 18 → 18; before: `keys that differ: ['recorded_rationale']`, every other key identical
  `True`; after: `keys that differ: ['question','recorded_rationale']`, every other key identical `False`.
  This is a **fix**, not a regression: the shipped `second-labeller/disagreements.jsonl` still carried
  as-audited question text, and the substitution sanitised it. Only `question` and `recorded_rationale`
  differ; options, labels and indices remain identical.
* §7 STRICT residual scan on the sanitised tree: **325 → 25** lines (as-audited stays 416 in both runs,
  unchanged). §8 field classification: `question` 47 cases / 56 occurrences → **2 / 2**; `options` 2 / 2 →
  **0 / 0**.
* §1 instrument digest of `fixture/reflex-decisions.ts` changes (as-audited
  `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`, substituted
  `a4af933c96b9edbd7f30ba9e9eceac634c948958d91e262da9741e401dbda708`) — declared by the script itself.
* `verify/run-verification.sh` exits **0** on the substituted tree.

## 6. Step 3.2 — the hard-fail gate, per pattern

Transcribed list (`experiments/token-substitution-test/work2-scan/hard.txt`, 24 lines, from
`orchestration/units/UBUILD1.build.sh:423-448`), invoked as
`grep -rn -I -i -F -f ../work2-scan/hard.txt . --exclude-dir=.git` with the tree as cwd.
"pristine" = shipped bytes of `work2-orig`; "before" = `work2-pre` after its own acceptance run (the
apples-to-apples baseline); "after" = `work2-substituted` after its acceptance run.

| pattern | pristine | before | after |
|---|---|---|---|
| `/home/zer0null` | 5 | 5 | **0** |
| `duval` | 5 | 5 | **0** |
| `a5ef1b28` | 0 | 0 | 0 |
| `89003e70` | 0 | 0 | 0 |
| `publish-present-compete` | 1 | 1 | 1 |
| `consonance` | 0 | 0 | 0 |
| `EXCLUDED.md` | 27 | 27 | 27 |
| `REDACTION_REPORT` | 116 | 116 | 96 |
| `RESIDUALS.md` | 36 | 36 | 35 |
| `LICENCE_TODO` | 17 | 17 | 17 |
| `TRADE_SECRET` | 3 | 3 | 3 |
| `WITHHELD.md` | 0 | 0 | 0 |
| `DISCLOSURE_INVENTORY` | 0 | 0 | 0 |
| `EXPOSURE_CLOSURE` | 0 | 0 | 0 |
| `ARCHIVE_WINDOW` | 0 | 0 | 0 |
| `VERIFICATION_REPORT` | 13 | 13 | 13 |
| `StateClass` | 111 | 114 | 5 |
| `grantPolicy` | 82 | 85 | 12 |
| `src/broker` | 9 | 11 | 3 |
| `src/scope` | 4 | 4 | **0** |
| `src/layer` | 3 | 3 | **0** |
| `CommitRecord` | 0 | 0 | 0 |
| `admit(` | 46 | 46 | **0** |
| `expanded[` | 58 | 57 | 2 |
| **TOTAL** | **407** | **407** | **158** |

The small pristine→before shifts (`StateClass` 111→114, `src/broker` 9→11, `expanded[` 58→57) come from the
acceptance run regenerating `verify/VERIFICATION.txt`, which quotes the tree's own tooling lines.

**Patterns at zero after the substitution (13):** `/home/zer0null`, `duval`, `src/scope`, `src/layer`,
`admit(`, plus the eight that were already zero (`a5ef1b28`, `89003e70`, `consonance`, `WITHHELD.md`,
`DISCLOSURE_INVENTORY`, `EXPOSURE_CLOSURE`, `ARCHIVE_WINDOW`, `CommitRecord`).

**Patterns that do NOT reach zero (11), and where they live:**

| pattern | after | owning files (after tree) | why substitution cannot clear it |
|---|---|---|---|
| `publish-present-compete` | 1 | `verify/scrub-uscrub1.py` | the scrub script itself embeds the pattern list |
| `EXCLUDED.md` | 27 | `SCRUB_REPORT.md` 7, `REDACTION_REPORT.md` 5, `README.md` 3, `INTEGRITY.md` 3, `EXCLUDED.md` 2, `verify/recompute-claims.py` 1, + others | it is a **filename** the process documents cross-reference |
| `REDACTION_REPORT` | 96 | `REDACTION_REPORT.md` 30, `RESIDUALS.md` 10, `README.md` 10, `second-labeller/OWED_CORRECTIONS.md` 9, `redact.py` 8, `variants/…/reflex-decisions.ts` 7, + others | same: a filename + the tooling's own name |
| `RESIDUALS.md` | 35 | `RESIDUALS.md` 12, `REDACTION_REPORT.md` 10, `verify/VERIFICATION.txt` 6, `README.md` 3, `INTEGRITY.md` 3, `MANIFEST.json` 1, + others | same |
| `LICENCE_TODO` | 17 | `SCRUB_REPORT.md` 6, `LICENCE_TODO.md` 3, `REDACTION_REPORT.md` 2, `README.md` 2, `verify/integrity-table.md` 1, `MANIFEST.json` 1, + others | same |
| `TRADE_SECRET` | 3 | `REDACTION_REPORT.md`, `README.md`, `INTEGRITY.md` | documentation *about* the withheld class |
| `VERIFICATION_REPORT` | 13 | `REDACTION_REPORT.md` 9, `second-labeller/metrics.json` 1, `second-labeller/OWED_CORRECTIONS.md` 1, `RESIDUALS.md` 1, `INTEGRITY.md` 1 | a withheld artefact's name |
| `StateClass` | 5 | `redact.py` 3, `verify/run-verification.sh` 2 | the redaction tooling's own deny-list/regex strings |
| `grantPolicy` | 12 | `redact.py` 4, `verify/run-verification.sh` 2, `fixture/reflex-decisions.ts` 2, `variants/…/reflex-decisions.ts` 2, `harness/data/fixture-190.json` 2 | 10 = tooling + **2 question strings** (mapping gap, §7.3) |
| `src/broker` | 3 | `SCRUB_REPORT.md` 3 | a report that names the residual |
| `expanded[` | 2 | `verify/VERIFICATION.txt` 1 (quotes `parse_fixture.py:50`), `second-labeller/parse_fixture.py` 1 (code comment) | a shipped reader's comment — `.py` is never edited by substitution |

## 7. What remains, and why substitution is not the fix

**7.1 Curation, not substitution** (exactly as the unit card directs): `code/verify/**` (`redact.py`,
`verify/run-verification.sh`, `verify/recompute-claims.py`, `verify/scrub-uscrub1.py`,
`verify/VERIFICATION.txt`), `EXCLUDED.md`, `LICENCE_TODO.md`, `REDACTION_REPORT(.md)`, `RESIDUALS.md`, and
the process documents that cross-reference them (`README.md`, `INTEGRITY.md`, `SCRUB_REPORT.md`,
`MANIFEST.json`, `second-labeller/OWED_CORRECTIONS.md`). These files *name* the withheld artefacts and *are*
the redaction tooling; deciding what ships — or rewriting the documents and the gate list — is a curation
decision, not a token substitution. This is where 133 of the 158 remaining hits sit (the four filename
patterns + `TRADE_SECRET` + `VERIFICATION_REPORT`).

**7.2 The `907fa39` / `ad301ae` revision anchors stay.** They are the read-only proof that the fixture was
cut from a named revision of the target repository; removing them would weaken a checked claim. They were
**not** removed — only the absolute path prefix was neutralised (`…reflex-decisions.ts (HEAD 907fa39)`).
Two digests of the instrument (`tccommon.INSTRUMENT_190_SHA256` and the run-verification §1 line) still
pin the bytes.

**7.3 The 2 `grantPolicy` question strings are a mapping gap.** After substitution these two `question`
values still contain the mechanism word, in all three copies
(`fixture/reflex-decisions.ts:288,798`, `harness/data/fixture-190.json:234,851`,
`variants/…/reflex-decisions.ts:288,798`):
```
"A step must read the workspace root listing. A class declares a GrantPolicy whose scope narrows its tool grants to 'src/**', and the broker …"
"The step's class is editor with declared tools ['fs.read','fs.write'], and the class's GrantPolicy applies scope 'src/**' to every tool grant it …"
```
UTOK1's mapping does not carry those two sentences' camel-case `GrantPolicy`. They are substitutable in
principle, but doing so edits **model input** and would move the scoring-projection digest a further time —
so it was not attempted here (outside the (a)–(d) mandate, and not to be tuned until the gate passes).
They account for the whole of `grantPolicy`'s non-tooling residue (2+2+2).

**7.4 The manifest neutralisation is not durable.** Verified: re-running `harness/prepare.py` on the
substituted tree (exit 0) rewrites `manifest.json` and emits **local absolute paths** instead of the
neutralised ones —
`"path": "/tmp/u2m/san/harness/data/corpus.json"`, `…/fixture-190.json`, `…/lint-report.json`
(`harness/tccommon.py:56-62` `DATA = HERE / "data"`; `harness/prepare.py:175`; the same key set, 9 keys).
That regenerated manifest is gate-clean (0 path hits) but differs from the shipped bytes, so
`sanitised-regeneration == shipped` will read `False` for the manifest as it already does for
`metrics.json`. (Correction to an earlier assumption: `prepare.py` does **not** re-introduce the
`/home/zer0null/Duval` target-repo paths — it emits paths local to the tree.) Fixing the manifest's
provenance lines properly means patching `prepare.py` to emit a placeholder, or freezing the manifest and
not regenerating it — again curation.

**7.5 `verify/VERIFICATION.txt` is an acceptance-run output.** The acceptance script tees its own output to
`<tree>/verify/VERIFICATION.txt`, including absolute scratch paths under whatever `$W` is used. That is why
the primary before/after runs above were made with the script's own `/tmp` scratch rather than a scratch
inside the workspace: an in-workspace scratch makes the regenerated log itself trip `/home/zer0null`
(measured: the total rises to 384-with-7-extra-`/home/zer0null` lines in the workspace-scratch variant).
The 7 hits that remain in the after tree's log are the log quoting the tooling's own pattern lines.

## 8. UNVERIFIED

1. `encoder-crossover-190/` is a copy of `repro/encoder-crossover-190`; it was **not** checked against the
   live `/home/zer0null/Duval` HEAD (the card forbids touching that repo, and `TARGET_REPO` was unset, so
   §1's target-HEAD check printed "not supplied").
2. No claim about downstream consumers **outside** this subset: whether anything else in the wider project
   cites `routeA.ties = 120` or the old option-label string. Only the shipped code in this subset was
   grepped.
3. The projection digest that would result from *also* fixing the 2 `GrantPolicy` question strings (§7.3)
   was not measured.
4. Whether `harness/analyze.py` can run at all (it needs the excluded `manifest-eval.json`) — unchanged by
   this unit; its read of `manifest.json` was not exercised.
5. The mapping's byte-length-preserving property was confirmed on the two `results/*.json` files checked
   (81268 → 81268, 80853 → 80853) but not exhaustively on all 21 changed files.
6. The gate was run with the 24-line `hard.txt` and `--exclude-dir=.git`; `UBUILD1.build.sh`'s extra
   `--exclude="$SELF"` (excluding the gate script itself) was not reproduced, so the counts here may be
   marginally conservative if the shipped tree ever contains a copy of the gate script.
7. `verify/VERIFICATION.txt` in the released candidate is a *regenerated* log (from the /tmp-scratch run),
   not the shipped log with substitutions applied; if the author wants the shipped log preserved, it must
   be substituted and not re-run.
8. UTOK1's `75d4b0a2…` digest could not be compared (18:17 snapshot, not reproducible) — the comparison
   here is only against the present bytes.

## 9. Reproduction

```bash
cd "experiments/token-substitution-test"
cp -a ../../repro/encoder-crossover-190-SANITISED work2-orig      # pristine reference
cp -a ../../repro/encoder-crossover-190-SANITISED work2-substituted
python3 substitute2.py "$PWD/work2-substituted"                    # 21 files, 0 aborts
cp -a ../../repro/encoder-crossover-190 encoder-crossover-190      # as-audited control (sibling)
cp -a work2-orig work2-pre
bash work2-substituted/verify/run-verification.sh /tmp/utok2-after > logs2/after2.txt 2>&1
python3 work2-substituted/verify/recompute-claims.py
( cd work2-substituted && grep -rn -I -i -F -f ../work2-scan/hard.txt . --exclude-dir=.git ) | wc -l
```
