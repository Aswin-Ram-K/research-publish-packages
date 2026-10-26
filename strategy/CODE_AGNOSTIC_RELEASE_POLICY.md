# CODE_AGNOSTIC_RELEASE_POLICY — identifier census, total substitution, placeholder harness, totality check

**Unit:** UAGNOSTIC1 · **Supersedes:** the "ship the sanitised subset and manage the residue" approach of
`strategy/PUBLISH_PACKAGE_MANIFEST.md` (UCURATE1) and the partial substitution of
`experiments/token-substitution-test/REPORT2.md` (UTOK2).
**Instrument scanned:** `.ucurate1/pre/research-publish-packages` — 49 of the 58 shipped files carry a project identifier.
**Census tooling:** `scratch/uagnostic1/census{1..5}.py` → `scratch/uagnostic1/census.tsv`.

---

## 0. The policy this document serves, and what it changes

The author's decision for the publish package: **code-agnostic release, the way the large labs do it.**
Only the smallest portion needed for the validity of the paper's scope is released; project-level details are
redacted; project names become **random neutral tags**; and the harness is re-presented as a **placeholder
harness architecture** that hosts the instrument, rather than our harness with names stripped.

Four rules follow, and every section below is an audit against one of them:

| # | Rule | Audit |
|---|---|---|
| R1 | **Minimal for validity** — only the bytes a reader needs to re-derive a published number and see the limits of the claim | §A (load-bearing column), §C |
| R2 | **Code-agnostic** — no identifier of the system under study survives, in code, data, option labels, `kind` values, filenames, directory names, or prose | §A, §B, §D |
| R3 | **Random neutral tags**, applied uniformly | §B |
| R4 | **Placeholder harness** — a generic architecture hosting the instrument | §C |

**The load-bearing change of shape.** The superseded approach asked *"how much residue is left?"* — a
question answered by counting hits against a 24-string denylist. The new policy replaces the residue question
with a **totality question**: *"is any project reference left?"* — answered by asserting the released
vocabulary is **closed under its own declaration**, not by avoiding N known strings. §D makes that runnable
and states why the denylist cannot do the job.

---

## A. The identifier census

### A.0 Method

The gate's denylist era — the 24 HARD patterns and the 6 REVIEW patterns, written as the
`PATTERNS_HARD`/`PATTERNS_REVIEW` heredocs that then occupied `orchestration/units/UBUILD1.build.sh` (since
deleted by ULICENCE3) — was a **leak detector, not an inventory**: it named 30 strings someone already
thought of, which is the list the census below is measured against. The gate today is not a denylist at all:
it is the **positive vocabulary checker** written by the heredoc beginning
`cat > "$DEST/gate.sh" <<'GATE_EOF'`, currently `:771`–`:896` (`chmod +x` at `:897`), which fails the build
when a token outside `vocabulary/english.txt` (created `:691`), `vocabulary/code.txt` (`:695`–`:743`) or
`vocabulary/public.txt` (`:748`–`:769`) appears (invoked at `bash "$DEST/gate.sh"`, `:1005`). The
census was therefore built empirically, from the bytes:

1. **Fixture extraction** (`census1.py`): parse `.ucurate1/pre/research-publish-packages/packages/exp12-encoder-crossover/code/harness/data/fixture-190.json` — 190 records,
   2 options per record, all `rationale` values `""` and all `namespaces` `[]`.
2. **Vocabulary extraction** (`census2.py`): tokenise every file in the ship set, drop a stop-word/English
   fuzz, and rank what remains → **676 candidate tokens**.
3. **Seeded enumeration** (`census3.py`): 184 seeds assembled from the fixture schema, the as-audited
   `repro/encoder-crossover-190/` tree, `strategy/WITHHELD.md`'s mechanism register (M1–M13), the gate
   patterns, the option labels, and the prose pointers; each scanned case-insensitively over the ship set
   with exact counts and `path:line` provenance → `scratch/uagnostic1/census.tsv`.
4. **Stimulus separation** (`census4.py`): for every identifier, occurrences *inside the scored stimulus*
   (questions + option labels) versus occurrences only in metadata. This is what separates a rename that can
   move a number from one that cannot.
5. **Bucketing** (`census5.py`): category and load-bearing tallies.

### A.1 Headline counts

| measure | value |
|---|---|
| distinct project-specific identifiers present in the ship set | **172** |
| total occurrences | **53,395** |
| shipped files carrying ≥1 | **49** of 58 |
| identifiers in the **scored stimulus** (questions/options) → renaming can perturb a tokeniser metric | **33** |
| identifiers **rename-safe** (metadata only, not model input) | **90** |
| identifiers **incidental** (filenames, paths, prose pointers, the scanner's own denylist) | **49** |
| of the above, identifiers that occur **only inside `gate.sh`** | **17** |
| identifiers matched by the 24 HARD + 6 REVIEW patterns | **31** of 172 → **81% are structurally invisible to the gate** |
| distinct option labels in the fixture | **215** |
| option labels that name or imply mechanism | **100** distinct / **193** occurrences |

**The single largest finding, stated first.** The leak is not concentrated in the 62 lines
`strategy/REGEN_ASSESSMENT.md` §2 counted. It is **53,395 occurrences across 172 identifiers**,
and the *greatest* part of it is the **metadata field vocabulary** (`nCandidate`, `nKind`, `nSituation`,
`clanId`, `ruleId`, `familyId`, `stateKey`, `goldIndex`, `pChosen`, `predLabel`, `constructionRule`,
`optionSetVersion`, `questionVersion`, `ruleSeenByReviser`, …) at ~32,000 occurrences, which no pattern list
has ever named. The second largest is the **in-stimulus mechanism vocabulary** (`reasoner`, `editor`,
`fs.read`, `fs.write`, `test.run`, `attached`/`detached`/`output-only`, `pin`, `projection`, `refusal`,
`manifest`, `topology`, `capability`, `scope`, `layer`) at ~4,600 occurrences. The 24 HARD patterns cover
none of either class.

### A.2 Full census, by category

`LK` = load-bearing and **rename-sensitive** (appears in the scored stimulus; a rename can perturb
`route_a`'s tokeniser metric — see §B.3) · `LS` = load-bearing and **rename-safe** (metadata only; a
consistent bijection cannot move a published number) · `INC` = incidental project reference (delete or
re-tag). Locations are representative — full `path:line` provenance for every identifier is in
`scratch/uagnostic1/census.tsv`.


#### A.2.1 `kind` values (the fixture's decision taxonomy)

*7 identifiers, 9,502 occurrences.*

| identifier | occ | files | class | representative locations |
|---|---:|---:|:--:|---|
| `memory.admission` | 1,857 | 3 | LS | gate.sh:68, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:12, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:57, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1026, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1034 … |
| `acquisition` | 1,379 | 2 | LS | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:15, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:60, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1927, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1934, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1935 … |
| `worker.class` | 1,343 | 2 | LS | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:9, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:54, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:87, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:88, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:98 … |
| `context.package` | 1,284 | 2 | LS | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:10, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:55, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:417, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:425, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:426 … |
| `topology` | 1,244 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:14, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:59, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1679, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1685, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1686 … |
| `escalation` | 1,232 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:13, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:58, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1342, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1349, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1350 … |
| `capability.family` | 1,163 | 3 | LS | gate.sh:69, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:11, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:56, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:733, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:740 … |

#### A.2.2 Dotted namespace values in metadata

*6 identifiers, 2,169 occurrences.*

| identifier | occ | files | class | representative locations |
|---|---:|---:|:--:|---|
| `acquisition.path` | 477 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:22, packages/exp12-encoder-crossover/code/harness/data/corpus.json:85, packages/exp12-encoder-crossover/code/harness/data/corpus.json:92, packages/exp12-encoder-crossover/code/harness/data/corpus.json:137, packages/exp12-encoder-crossover/code/harness/data/corpus.json:284 … |
| `routing.team` | 417 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:181, packages/exp12-encoder-crossover/code/harness/data/corpus.json:389, packages/exp12-encoder-crossover/code/harness/data/corpus.json:483, packages/exp12-encoder-crossover/code/harness/data/corpus.json:556, packages/exp12-encoder-crossover/code/harness/data/corpus.json:580 … |
| `route.team` | 416 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:18, packages/exp12-encoder-crossover/code/harness/data/corpus.json:29, packages/exp12-encoder-crossover/code/harness/data/corpus.json:36, packages/exp12-encoder-crossover/code/harness/data/corpus.json:148, packages/exp12-encoder-crossover/code/harness/data/corpus.json:180 … |
| `lease.scope` | 380 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:26, packages/exp12-encoder-crossover/code/harness/data/corpus.json:167, packages/exp12-encoder-crossover/code/harness/data/corpus.json:524, packages/exp12-encoder-crossover/code/harness/data/corpus.json:525, packages/exp12-encoder-crossover/code/harness/data/corpus.json:538 … |
| `escalation.decision` | 240 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:24, packages/exp12-encoder-crossover/code/harness/data/corpus.json:111, packages/exp12-encoder-crossover/code/harness/data/corpus.json:115, packages/exp12-encoder-crossover/code/harness/data/corpus.json:144, packages/exp12-encoder-crossover/code/harness/data/corpus.json:336 … |
| `topology.shape` | 239 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:23, packages/exp12-encoder-crossover/code/harness/data/corpus.json:99, packages/exp12-encoder-crossover/code/harness/data/corpus.json:105, packages/exp12-encoder-crossover/code/harness/data/corpus.json:155, packages/exp12-encoder-crossover/code/harness/data/corpus.json:310 … |

#### A.2.3 Tool / capability tokens

*7 identifiers, 4,171 occurrences.*

| identifier | occ | files | class | representative locations |
|---|---:|---:|:--:|---|
| `fs.read` | 894 | 1 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:81, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:90, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:134, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:167, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:167 … |
| `fs.write` | 850 | 1 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:81, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:90, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:123, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:134, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:167 … |
| `test.run` | 832 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:123, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:124, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:178, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:179, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:255 … |
| `net.fetch` | 769 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:74, packages/exp12-encoder-crossover/code/harness/data/corpus.json:82, packages/exp12-encoder-crossover/code/harness/data/corpus.json:1753, packages/exp12-encoder-crossover/code/harness/data/corpus.json:1778, packages/exp12-encoder-crossover/code/harness/data/corpus.json:1803 … |
| `model.call` | 754 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:73, packages/exp12-encoder-crossover/code/harness/data/corpus.json:81, packages/exp12-encoder-crossover/code/harness/data/corpus.json:1754, packages/exp12-encoder-crossover/code/harness/data/corpus.json:1779, packages/exp12-encoder-crossover/code/harness/data/corpus.json:1804 … |
| `memory.write` | 46 | 3 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:134, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:134, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:135, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:222, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:223 … |
| `web.fetch` | 26 | 5 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:343, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:344, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:298, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:300, packages/exp12-encoder-crossover/eval/results/baselines.json:208 … |

#### A.2.4 Agent-class and role names

*11 identifiers, 4,634 occurrences.*

| identifier | occ | files | class | representative locations |
|---|---:|---:|:--:|---|
| `editor` | 1,480 | 2 | LK | .gitignore:6, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:81, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:90, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:91, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:102 … |
| `verifier` | 1,206 | 4 | LK | README.md:41, packages/exp12-encoder-crossover/README.md:82, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:101, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:124, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:178 … |
| `reasoner` | 1,177 | 1 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:90, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:91, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:102, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:112, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:113 … |
| `attached` | 365 | 1 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:81, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:90, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:91, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:102, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:113 … |
| `detached` | 197 | 1 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:124, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:134, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:135, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:167, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:168 … |
| `output-only` | 53 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:90, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:112, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:112, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:113, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:167 … |
| `code-inspector` | 50 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:167, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:168, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:233, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:234, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:255 … |
| `memory-curator` | 44 | 3 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:134, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:135, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:222, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:223, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:55 … |
| `researcher` | 26 | 5 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:343, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:344, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:298, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:300, packages/exp12-encoder-crossover/eval/results/baselines.json:208 … |
| `critic` | 25 | 5 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:354, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:355, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:311, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:313, packages/exp12-encoder-crossover/eval/results/baselines.json:216 … |
| `code-review` | 11 | 8 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:112, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:113, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:29, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:33, packages/exp12-encoder-crossover/eval/results/baselines.json:61 … |

#### A.2.5 Mechanism symbols and API fragments

*30 identifiers, 304 occurrences.*

| identifier | occ | files | class | representative locations |
|---|---:|---:|:--:|---|
| `StateClass` | 63 | 2 | LK | gate.sh:52, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:90, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:101, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:112, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:123 … |
| `grantPolicy` | 42 | 2 | LK | gate.sh:53, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:90, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:90, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:112, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:112 … |
| `expanded[` | 29 | 6 | LK | gate.sh:59, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:572, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:573, packages/exp12-encoder-crossover/eval/results/baselines.json:348, packages/exp12-encoder-crossover/eval/results/baselines.json:349 … |
| `policyHash` | 26 | 5 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:539, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1539, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:531, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:1770, packages/exp12-encoder-crossover/eval/results/baselines.json:327 … |
| `admit(` | 21 | 7 | LK | gate.sh:58, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:146, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:72, packages/exp12-encoder-crossover/eval/results/baselines.json:83, packages/exp12-encoder-crossover/eval/results/baselines.json:1457 … |
| `broker` | 12 | 4 | LK | README.md:37, gate.sh:54, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:233, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:233, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:288 … |
| `LintSideSpec` | 11 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:91, packages/exp12-encoder-crossover/code/harness/lint.ts:138, packages/exp12-encoder-crossover/code/harness/lint.ts:174, packages/exp12-encoder-crossover/code/harness/lint.ts:175, packages/exp12-encoder-crossover/code/harness/lint.ts:291 … |
| `LintRow` | 10 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:86, packages/exp12-encoder-crossover/code/harness/lint.ts:93, packages/exp12-encoder-crossover/code/harness/lint.ts:103, packages/exp12-encoder-crossover/code/harness/lint.ts:125, packages/exp12-encoder-crossover/code/harness/lint.ts:125 … |
| `LogisticPairHead` | 8 | 6 | LS | packages/exp12-encoder-crossover/code/harness/README.md:54, packages/exp12-encoder-crossover/code/harness/defect-probe.py:6, packages/exp12-encoder-crossover/code/harness/defect-probe.py:47, packages/exp12-encoder-crossover/code/harness/defect-probe.py:87, packages/exp12-encoder-crossover/code/harness/evaluate.py:67 … |
| `DecisionKind` | 7 | 4 | LS | gate.sh:67, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:3, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:8, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:19, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:53 … |
| `DecisionCase` | 7 | 5 | LS | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:3, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:17, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:62, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:77, packages/exp12-encoder-crossover/eval/second-labeller/EVIDENCE.md:278 … |
| `ToolCallIR` | 5 | 3 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:831, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:941, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:893, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:1033, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:6 |
| `CorpusShape` | 5 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:496, packages/exp12-encoder-crossover/code/harness/lint.ts:515, packages/exp12-encoder-crossover/code/harness/lint.ts:516, packages/exp12-encoder-crossover/code/harness/lint.ts:524, packages/exp12-encoder-crossover/code/harness/lint.ts:528 |
| `KIND_ALIAS` | 5 | 1 | LS | packages/exp12-encoder-crossover/code/harness/tccommon.py:42, packages/exp12-encoder-crossover/code/harness/tccommon.py:70, packages/exp12-encoder-crossover/code/harness/tccommon.py:103, packages/exp12-encoder-crossover/code/harness/tccommon.py:103, packages/exp12-encoder-crossover/code/harness/tccommon.py:108 |
| `GrantPolicy` | 4 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:288, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:798, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:234, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:851 |
| `DECISION_CASES` | 4 | 3 | LS | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:6, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:77, packages/exp12-encoder-crossover/code/harness/export-fixture.ts:26, packages/exp12-encoder-crossover/code/harness/export-fixture.ts:58 |
| `ContaminationFlag` | 4 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:150, packages/exp12-encoder-crossover/code/harness/lint.ts:164, packages/exp12-encoder-crossover/code/harness/lint.ts:192, packages/exp12-encoder-crossover/code/harness/lint.ts:267 |
| `CorpusCase` | 4 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:488, packages/exp12-encoder-crossover/code/harness/lint.ts:498, packages/exp12-encoder-crossover/code/harness/lint.ts:524, packages/exp12-encoder-crossover/code/harness/lint.ts:528 |
| `DirectionReport` | 4 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:157, packages/exp12-encoder-crossover/code/harness/lint.ts:179, packages/exp12-encoder-crossover/code/harness/lint.ts:257, packages/exp12-encoder-crossover/code/harness/lint.ts:258 |
| `FixtureCase` | 4 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:336, packages/exp12-encoder-crossover/code/harness/lint.ts:501, packages/exp12-encoder-crossover/code/harness/lint.ts:519, packages/exp12-encoder-crossover/code/harness/lint.ts:520 |
| `LintableCase` | 4 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:117, packages/exp12-encoder-crossover/code/harness/lint.ts:125, packages/exp12-encoder-crossover/code/harness/lint.ts:138, packages/exp12-encoder-crossover/code/harness/lint.ts:488 |
| `MutationProposal` | 4 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1495, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1992, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:1722, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:2311 |
| `RemovedRow` | 4 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:239, packages/exp12-encoder-crossover/code/harness/lint.ts:259, packages/exp12-encoder-crossover/code/harness/lint.ts:267, packages/exp12-encoder-crossover/code/harness/lint.ts:268 |
| `DemoProbe` | 3 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:351, packages/exp12-encoder-crossover/code/harness/lint.ts:378, packages/exp12-encoder-crossover/code/harness/lint.ts:445 |
| `DemoResult` | 3 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:375, packages/exp12-encoder-crossover/code/harness/lint.ts:399, packages/exp12-encoder-crossover/code/harness/lint.ts:581 |
| `GramSample` | 3 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:144, packages/exp12-encoder-crossover/code/harness/lint.ts:154, packages/exp12-encoder-crossover/code/harness/lint.ts:244 |
| `LintField` | 3 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:81, packages/exp12-encoder-crossover/code/harness/lint.ts:88, packages/exp12-encoder-crossover/code/harness/lint.ts:126 |
| `LintReport` | 3 | 1 | LS | packages/exp12-encoder-crossover/code/harness/lint.ts:247, packages/exp12-encoder-crossover/code/harness/lint.ts:303, packages/exp12-encoder-crossover/code/harness/lint.ts:563 |
| `CommitRecord` | 1 | 1 | LS | gate.sh:57 |
| `consonance` | 1 | 1 | LS | gate.sh:41 |

#### A.2.6 Metadata, corpus and scoring field names

*59 identifiers, 31,999 occurrences.*

| identifier | occ | files | class | representative locations |
|---|---:|---:|:--:|---|
| `nKind` | 3,186 | 4 | LS | gate.sh:67, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:3, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:8, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:19, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:53 … |
| `nCandidate` | 3,180 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:1, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:1, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:1, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:2, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:2 … |
| `nSituation` | 3,179 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:1, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:1, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:1, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:2, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:2 … |
| `familyId` | 2,234 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:184, packages/exp12-encoder-crossover/code/harness/data/corpus.json:210, packages/exp12-encoder-crossover/code/harness/data/corpus.json:236, packages/exp12-encoder-crossover/code/harness/data/corpus.json:262, packages/exp12-encoder-crossover/code/harness/data/corpus.json:288 … |
| `clanId` | 2,233 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:179, packages/exp12-encoder-crossover/code/harness/data/corpus.json:205, packages/exp12-encoder-crossover/code/harness/data/corpus.json:231, packages/exp12-encoder-crossover/code/harness/data/corpus.json:257, packages/exp12-encoder-crossover/code/harness/data/corpus.json:283 … |
| `ruleId` | 2,228 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:180, packages/exp12-encoder-crossover/code/harness/data/corpus.json:206, packages/exp12-encoder-crossover/code/harness/data/corpus.json:232, packages/exp12-encoder-crossover/code/harness/data/corpus.json:258, packages/exp12-encoder-crossover/code/harness/data/corpus.json:284 … |
| `goldIndex` | 1,965 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:1, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:2, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:3, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:4, packages/exp12-encoder-crossover/code/harness/data/dev.jsonl:5 … |
| `pChosen` | 1,334 | 2 | LS | packages/exp12-encoder-crossover/code/harness/evaluate.py:175, packages/exp12-encoder-crossover/code/harness/evaluate.py:329, packages/exp12-encoder-crossover/code/harness/evaluate.py:339, packages/exp12-encoder-crossover/code/harness/evaluate.py:396, packages/exp12-encoder-crossover/eval/results/baselines.json:50 … |
| `predLabel` | 1,334 | 2 | LS | packages/exp12-encoder-crossover/code/harness/evaluate.py:174, packages/exp12-encoder-crossover/code/harness/evaluate.py:328, packages/exp12-encoder-crossover/code/harness/evaluate.py:393, packages/exp12-encoder-crossover/code/harness/evaluate.py:396, packages/exp12-encoder-crossover/eval/results/baselines.json:47 … |
| `ruleSeenByReviser` | 1,228 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:183, packages/exp12-encoder-crossover/code/harness/data/corpus.json:209, packages/exp12-encoder-crossover/code/harness/data/corpus.json:235, packages/exp12-encoder-crossover/code/harness/data/corpus.json:261, packages/exp12-encoder-crossover/code/harness/data/corpus.json:287 … |
| `caseId` | 1,214 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:568, packages/exp12-encoder-crossover/code/harness/data/corpus.json:592, packages/exp12-encoder-crossover/code/harness/data/corpus.json:616, packages/exp12-encoder-crossover/code/harness/data/corpus.json:640, packages/exp12-encoder-crossover/code/harness/data/corpus.json:664 … |
| `constructionRule` | 1,000 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:5449, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5486, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5525, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5562, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5595 … |
| `optionSetVersion` | 1,000 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:5460, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5497, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5536, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5573, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5606 … |
| `questionVersion` | 1,000 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:5459, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5496, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5535, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5572, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5605 … |
| `stateKey` | 1,000 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:5438, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5471, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5508, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5547, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5584 … |
| `predIndex` | 955 | 3 | LS | packages/exp12-encoder-crossover/code/harness/evaluate.py:327, packages/exp12-encoder-crossover/code/harness/evaluate.py:342, packages/exp12-encoder-crossover/code/harness/tccommon.py:241, packages/exp12-encoder-crossover/code/harness/tccommon.py:246, packages/exp12-encoder-crossover/code/harness/tccommon.py:256 … |
| `caseCount` | 210 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:567, packages/exp12-encoder-crossover/code/harness/data/corpus.json:591, packages/exp12-encoder-crossover/code/harness/data/corpus.json:615, packages/exp12-encoder-crossover/code/harness/data/corpus.json:639, packages/exp12-encoder-crossover/code/harness/data/corpus.json:663 … |
| `caseIds` | 210 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:568, packages/exp12-encoder-crossover/code/harness/data/corpus.json:592, packages/exp12-encoder-crossover/code/harness/data/corpus.json:616, packages/exp12-encoder-crossover/code/harness/data/corpus.json:640, packages/exp12-encoder-crossover/code/harness/data/corpus.json:664 … |
| `defectReport` | 185 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:5455, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5492, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5531, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5568, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5601 … |
| `deliveryDelay` | 185 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:5454, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5491, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5530, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5567, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5600 … |
| `refundRequest` | 185 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:5453, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5490, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5529, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5566, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5599 … |
| `securitySignal` | 185 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:5452, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5489, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5528, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5565, packages/exp12-encoder-crossover/code/harness/data/corpus.json:5598 … |
| `crossSession` | 160 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:8320, packages/exp12-encoder-crossover/code/harness/data/corpus.json:8353, packages/exp12-encoder-crossover/code/harness/data/corpus.json:8392, packages/exp12-encoder-crossover/code/harness/data/corpus.json:8425, packages/exp12-encoder-crossover/code/harness/data/corpus.json:8460 … |
| `procedureLike` | 160 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:8321, packages/exp12-encoder-crossover/code/harness/data/corpus.json:8354, packages/exp12-encoder-crossover/code/harness/data/corpus.json:8393, packages/exp12-encoder-crossover/code/harness/data/corpus.json:8426, packages/exp12-encoder-crossover/code/harness/data/corpus.json:8461 … |
| `stepCount` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:19971, packages/exp12-encoder-crossover/code/harness/data/corpus.json:20007, packages/exp12-encoder-crossover/code/harness/data/corpus.json:20043, packages/exp12-encoder-crossover/code/harness/data/corpus.json:20079, packages/exp12-encoder-crossover/code/harness/data/corpus.json:20111 … |
| `terminalChain` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:19970, packages/exp12-encoder-crossover/code/harness/data/corpus.json:20006, packages/exp12-encoder-crossover/code/harness/data/corpus.json:20042, packages/exp12-encoder-crossover/code/harness/data/corpus.json:20078, packages/exp12-encoder-crossover/code/harness/data/corpus.json:20110 … |
| `needsRead` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:25254, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25291, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25328, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25365, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25402 … |
| `needsWrite` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:25253, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25290, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25327, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25364, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25401 … |
| `needsTest` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:25252, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25289, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25326, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25363, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25400 … |
| `needsCapability` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:11191, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11225, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11259, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11293, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11325 … |
| `needsEvidence` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:11190, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11224, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11258, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11292, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11324 … |
| `needsLiveModel` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:22693, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22725, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22757, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22789, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22821 … |
| `budgetTight` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:11192, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11226, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11260, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11294, packages/exp12-encoder-crossover/code/harness/data/corpus.json:11326 … |
| `largePayload` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:16975, packages/exp12-encoder-crossover/code/harness/data/corpus.json:17015, packages/exp12-encoder-crossover/code/harness/data/corpus.json:17053, packages/exp12-encoder-crossover/code/harness/data/corpus.json:17093, packages/exp12-encoder-crossover/code/harness/data/corpus.json:17129 … |
| `answerableFromState` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:22692, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22724, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22756, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22788, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22820 … |
| `emitsVerdict` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:25255, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25292, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25329, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25366, packages/exp12-encoder-crossover/code/harness/data/corpus.json:25403 … |
| `policyHuman` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:16976, packages/exp12-encoder-crossover/code/harness/data/corpus.json:17016, packages/exp12-encoder-crossover/code/harness/data/corpus.json:17054, packages/exp12-encoder-crossover/code/harness/data/corpus.json:17094, packages/exp12-encoder-crossover/code/harness/data/corpus.json:17130 … |
| `policyRequiresHuman` | 105 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:22694, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22726, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22758, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22790, packages/exp12-encoder-crossover/code/harness/data/corpus.json:22822 … |
| `declaresFsRead` | 80 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:13883, packages/exp12-encoder-crossover/code/harness/data/corpus.json:13924, packages/exp12-encoder-crossover/code/harness/data/corpus.json:13967, packages/exp12-encoder-crossover/code/harness/data/corpus.json:14002, packages/exp12-encoder-crossover/code/harness/data/corpus.json:14043 … |
| `declaresFsWrite` | 80 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:13884, packages/exp12-encoder-crossover/code/harness/data/corpus.json:13925, packages/exp12-encoder-crossover/code/harness/data/corpus.json:13968, packages/exp12-encoder-crossover/code/harness/data/corpus.json:14003, packages/exp12-encoder-crossover/code/harness/data/corpus.json:14044 … |
| `declaresModelCall` | 80 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:13887, packages/exp12-encoder-crossover/code/harness/data/corpus.json:13928, packages/exp12-encoder-crossover/code/harness/data/corpus.json:13971, packages/exp12-encoder-crossover/code/harness/data/corpus.json:14006, packages/exp12-encoder-crossover/code/harness/data/corpus.json:14047 … |
| `declaresNetFetch` | 80 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:13886, packages/exp12-encoder-crossover/code/harness/data/corpus.json:13927, packages/exp12-encoder-crossover/code/harness/data/corpus.json:13970, packages/exp12-encoder-crossover/code/harness/data/corpus.json:14005, packages/exp12-encoder-crossover/code/harness/data/corpus.json:14046 … |
| `declaresTestRun` | 80 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:13885, packages/exp12-encoder-crossover/code/harness/data/corpus.json:13926, packages/exp12-encoder-crossover/code/harness/data/corpus.json:13969, packages/exp12-encoder-crossover/code/harness/data/corpus.json:14004, packages/exp12-encoder-crossover/code/harness/data/corpus.json:14045 … |
| `namesAgent` | 50 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:39001, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39035, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39071, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39105, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39141 … |
| `namesRun` | 50 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:39002, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39036, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39072, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39106, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39142 … |
| `namesTask` | 50 | 1 | LS | packages/exp12-encoder-crossover/code/harness/data/corpus.json:39000, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39034, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39070, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39104, packages/exp12-encoder-crossover/code/harness/data/corpus.json:39140 … |
| `latencyMs` | 45 | 3 | LS | packages/exp12-encoder-crossover/code/harness/analyze.py:170, packages/exp12-encoder-crossover/code/harness/analyze.py:170, packages/exp12-encoder-crossover/code/harness/analyze.py:340, packages/exp12-encoder-crossover/code/harness/analyze.py:346, packages/exp12-encoder-crossover/code/harness/analyze.py:446 … |
| `reproducesAt3dp` | 35 | 3 | LS | packages/exp12-encoder-crossover/code/harness/analyze.py:320, packages/exp12-encoder-crossover/code/harness/analyze.py:320, packages/exp12-encoder-crossover/code/harness/analyze.py:325, packages/exp12-encoder-crossover/code/harness/analyze.py:325, packages/exp12-encoder-crossover/code/harness/analyze.py:495 … |
| `orderPermutationFlips` | 19 | 2 | LS | packages/exp12-encoder-crossover/eval/results/DEFECT-EVIDENCE.json:13, packages/exp12-encoder-crossover/eval/results/DEFECT-EVIDENCE.json:21, packages/exp12-encoder-crossover/eval/results/DEFECT-EVIDENCE.json:29, packages/exp12-encoder-crossover/eval/results/DEFECT-EVIDENCE.json:37, packages/exp12-encoder-crossover/eval/results/DEFECT-EVIDENCE.json:45 … |
| `routeA_index` | 19 | 2 | LS | packages/exp12-encoder-crossover/eval/second-labeller/compare.py:163, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:1, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:2, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:3, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:4 … |
| `routeA_label` | 19 | 2 | LS | packages/exp12-encoder-crossover/eval/second-labeller/compare.py:163, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:1, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:2, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:3, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:4 … |
| `routeB_index` | 19 | 2 | LS | packages/exp12-encoder-crossover/eval/second-labeller/compare.py:162, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:1, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:2, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:3, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:4 … |
| `routeB_label` | 19 | 2 | LS | packages/exp12-encoder-crossover/eval/second-labeller/compare.py:162, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:1, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:2, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:3, packages/exp12-encoder-crossover/eval/second-labeller/disagreements.jsonl:4 … |
| `sharedGramCount` | 18 | 3 | LS | packages/exp12-encoder-crossover/code/harness/collect.py:281, packages/exp12-encoder-crossover/code/harness/collect.py:282, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:100, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:124, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:152 … |
| `maxPairSharedGramCount` | 11 | 5 | LS | packages/exp12-encoder-crossover/code/harness/collect.py:281, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:101, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:125, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:153, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:181 … |
| `fieldsThatCarriedTheSharedGrams` | 8 | 3 | LS | packages/exp12-encoder-crossover/code/harness/collect.py:284, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:105, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:133, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:161, packages/exp12-encoder-crossover/code/harness/data/lint-report.json:183 … |
| `canRequestEscalation` | 7 | 4 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:81, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:277, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1418, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:221, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:1637 … |
| `expiresAtEpoch` | 6 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:472, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:809, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1007, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:445, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:865 … |
| `reasonerCalls` | 4 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:321, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1363, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:272, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:1577 |

#### A.2.7 Project-specific file names

*13 identifiers, 222 occurrences.*

| identifier | occ | files | class | representative locations |
|---|---:|---:|:--:|---|
| `typed-channel` | 78 | 2 | INC | packages/exp12-encoder-crossover/code/harness/README.md:1, packages/exp12-encoder-crossover/code/harness/README.md:1, packages/exp12-encoder-crossover/code/harness/README.md:3, packages/exp12-encoder-crossover/code/harness/README.md:3, packages/exp12-encoder-crossover/code/harness/README.md:22 … |
| `reflex-decisions` | 48 | 10 | INC | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:2, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:6, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:2, packages/exp12-encoder-crossover/code/harness/README.md:55, packages/exp12-encoder-crossover/code/harness/collect.py:72 … |
| `reflex-decisions.ts` | 31 | 10 | INC | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:2, packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:6, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:2, packages/exp12-encoder-crossover/code/harness/README.md:55, packages/exp12-encoder-crossover/code/harness/collect.py:72 … |
| `tccommon` | 16 | 10 | INC | packages/exp12-encoder-crossover/code/README.md:21, packages/exp12-encoder-crossover/code/harness/README.md:53, packages/exp12-encoder-crossover/code/harness/README.md:71, packages/exp12-encoder-crossover/code/harness/analyze.py:36, packages/exp12-encoder-crossover/code/harness/analyze.py:404 … |
| `fixture-190.json` | 12 | 10 | INC | packages/exp12-encoder-crossover/code/harness/LEAD-WIRING.md:23, packages/exp12-encoder-crossover/code/harness/README.md:55, packages/exp12-encoder-crossover/code/harness/data/manifest.json:10, packages/exp12-encoder-crossover/code/harness/evaluate.py:8, packages/exp12-encoder-crossover/code/harness/export-fixture.ts:30 … |
| `export-fixture.ts` | 11 | 8 | INC | packages/exp12-encoder-crossover/README.md:55, packages/exp12-encoder-crossover/code/harness/LEAD-WIRING.md:21, packages/exp12-encoder-crossover/code/harness/LEAD-WIRING.md:38, packages/exp12-encoder-crossover/code/harness/README.md:22, packages/exp12-encoder-crossover/code/harness/README.md:55 … |
| `defect-probe.py` | 9 | 6 | INC | packages/exp12-encoder-crossover/code/harness/README.md:40, packages/exp12-encoder-crossover/code/harness/README.md:61, packages/exp12-encoder-crossover/code/harness/collect.py:91, packages/exp12-encoder-crossover/code/harness/defect-probe.py:3, packages/exp12-encoder-crossover/code/harness/defect-probe.py:20 … |
| `tcmodel` | 5 | 5 | INC | packages/exp12-encoder-crossover/code/harness/README.md:54, packages/exp12-encoder-crossover/code/harness/defect-probe.py:35, packages/exp12-encoder-crossover/code/harness/evaluate.py:44, packages/exp12-encoder-crossover/code/harness/tcmodel.py:2, packages/exp12-encoder-crossover/code/harness/train.py:52 |
| `tccommon.py` | 3 | 3 | INC | packages/exp12-encoder-crossover/code/README.md:21, packages/exp12-encoder-crossover/code/harness/README.md:53, packages/exp12-encoder-crossover/code/harness/tccommon.py:2 |
| `LEAD-WIRING.md` | 3 | 3 | INC | packages/exp12-encoder-crossover/code/harness/LEAD-WIRING.md:4, packages/exp12-encoder-crossover/code/harness/collect.py:372, packages/exp12-encoder-crossover/eval/results/REPORT.md:193 |
| `DECISION_CASE_SCHEMA.ts` | 2 | 2 | INC | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:1, packages/exp12-encoder-crossover/paper/MANUSCRIPT.md:794 |
| `tcmodel.py` | 2 | 2 | INC | packages/exp12-encoder-crossover/code/harness/README.md:54, packages/exp12-encoder-crossover/code/harness/tcmodel.py:2 |
| `EXP12-typed-channel-comparison-prereg.md` | 2 | 1 | INC | packages/exp12-encoder-crossover/paper/MANUSCRIPT.md:751, packages/exp12-encoder-crossover/paper/MANUSCRIPT.md:797 |

#### A.2.8 Project-specific paths

*20 identifiers, 237 occurrences.*

| identifier | occ | files | class | representative locations |
|---|---:|---:|:--:|---|
| `EXP#12` | 80 | 7 | INC | README.md:17, packages/exp12-encoder-crossover/README.md:1, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:2, packages/exp12-encoder-crossover/code/harness/LEAD-WIRING.md:1, packages/exp12-encoder-crossover/code/harness/LEAD-WIRING.md:14 … |
| `EXP#11` | 58 | 4 | INC | packages/exp12-encoder-crossover/code/harness/README.md:56, packages/exp12-encoder-crossover/code/harness/analyze.py:12, packages/exp12-encoder-crossover/code/harness/analyze.py:20, packages/exp12-encoder-crossover/code/harness/analyze.py:192, packages/exp12-encoder-crossover/code/harness/analyze.py:223 … |
| `tools/typed-channel` | 48 | 3 | INC | packages/exp12-encoder-crossover/code/harness/README.md:1, packages/exp12-encoder-crossover/code/harness/README.md:22, packages/exp12-encoder-crossover/code/harness/README.md:25, packages/exp12-encoder-crossover/code/harness/README.md:28, packages/exp12-encoder-crossover/code/harness/README.md:31 … |
| `evals/fixtures/reflex-decisions.ts` | 25 | 9 | INC | packages/exp12-encoder-crossover/code/fixture/DECISION_CASE_SCHEMA.ts:2, packages/exp12-encoder-crossover/code/harness/README.md:55, packages/exp12-encoder-crossover/code/harness/collect.py:72, packages/exp12-encoder-crossover/code/harness/collect.py:402, packages/exp12-encoder-crossover/code/harness/evaluate.py:432 … |
| `src/broker` | 5 | 3 | LK | gate.sh:54, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:233, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:233, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:170, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:170 |
| `src/policy.ts` | 4 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:112, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1919, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:29, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:2222 |
| `src/loop.ts` | 4 | 2 | LK | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:167, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:1688, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:94, packages/exp12-encoder-crossover/code/harness/data/fixture-190.json:1928 |
| `/home/zer0null` | 1 | 1 | INC | gate.sh:36 |
| `duval` | 1 | 1 | INC | gate.sh:37 |
| `publish-present-compete` | 1 | 1 | INC | gate.sh:40 |
| `a5ef1b28` | 1 | 1 | INC | gate.sh:38 |
| `89003e70` | 1 | 1 | INC | gate.sh:39 |
| `src/scope` | 1 | 1 | INC | gate.sh:55 |
| `src/layer` | 1 | 1 | INC | gate.sh:56 |
| `dag.ts` | 1 | 1 | INC | gate.sh:65 |
| `store.ts` | 1 | 1 | INC | gate.sh:66 |
| `TRADE_SECRET` | 1 | 1 | INC | gate.sh:46 |
| `DISCLOSURE_INVENTORY` | 1 | 1 | INC | gate.sh:48 |
| `EXPOSURE_CLOSURE` | 1 | 1 | INC | gate.sh:49 |
| `ARCHIVE_WINDOW` | 1 | 1 | INC | gate.sh:50 |

#### A.2.9 Prose pointers to internal documents

*19 identifiers, 157 occurrences.*

| identifier | occ | files | class | representative locations |
|---|---:|---:|:--:|---|
| `DECIDER_STACK_DECISION.md` | 26 | 5 | INC | packages/exp12-encoder-crossover/eval/preregistration/EXP12-typed-channel-comparison-prereg.md:50, packages/exp12-encoder-crossover/eval/preregistration/EXP12-typed-channel-comparison-prereg.md:50, packages/exp12-encoder-crossover/paper/GAPS.md:144, packages/exp12-encoder-crossover/paper/MANUSCRIPT.md:68, packages/exp12-encoder-crossover/paper/MANUSCRIPT.md:118 … |
| `PAPER_CANDIDATES.md` | 22 | 7 | INC | packages/exp12-encoder-crossover/eval/second-labeller-190/ROBUSTNESS.md:20, packages/exp12-encoder-crossover/eval/second-labeller-190/ROBUSTNESS.md:259, packages/exp12-encoder-crossover/eval/second-labeller-190/RUN2.json:65, packages/exp12-encoder-crossover/eval/second-labeller/EVIDENCE.md:21, packages/exp12-encoder-crossover/eval/second-labeller/EVIDENCE.md:309 … |
| `MANUSCRIPT.md` | 21 | 4 | INC | README.md:24, packages/exp12-encoder-crossover/README.md:32, packages/exp12-encoder-crossover/README.md:44, packages/exp12-encoder-crossover/paper/CHECKLIST.md:3, packages/exp12-encoder-crossover/paper/CHECKLIST.md:3 … |
| `LEARNINGS.md` | 20 | 4 | INC | packages/exp12-encoder-crossover/paper/CHECKLIST.md:153, packages/exp12-encoder-crossover/paper/CLAIMS.md:14, packages/exp12-encoder-crossover/paper/CLAIMS.md:33, packages/exp12-encoder-crossover/paper/CLAIMS.md:33, packages/exp12-encoder-crossover/paper/CLAIMS.md:34 … |
| `LICENSE_ANALYSIS.md` | 18 | 2 | INC | packages/exp12-encoder-crossover/paper/CHECKLIST.md:81, packages/exp12-encoder-crossover/paper/CHECKLIST.md:81, packages/exp12-encoder-crossover/paper/CHECKLIST.md:88, packages/exp12-encoder-crossover/paper/CHECKLIST.md:97, packages/exp12-encoder-crossover/paper/CHECKLIST.md:98 … |
| `REDACTION_REPORT.md` | 10 | 3 | INC | packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:21, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:25, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:79, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:80, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:420 … |
| `L1_HEAD_TO_HEAD.md` | 8 | 6 | INC | packages/exp12-encoder-crossover/code/harness/analyze.py:271, packages/exp12-encoder-crossover/code/harness/collect.py:249, packages/exp12-encoder-crossover/code/harness/evaluate.py:147, packages/exp12-encoder-crossover/code/harness/export-fixture.ts:9, packages/exp12-encoder-crossover/code/harness/tccommon.py:11 … |
| `FINDINGS_REGISTER.md` | 4 | 3 | INC | packages/exp12-encoder-crossover/eval/second-labeller/EVIDENCE.md:258, packages/exp12-encoder-crossover/eval/second-labeller/RUN.json:105, packages/exp12-encoder-crossover/eval/second-labeller/RUN.json:107, packages/exp12-encoder-crossover/paper/CHECKLIST.md:137 |
| `PUBLICATION_STRATEGY.md` | 4 | 2 | INC | packages/exp12-encoder-crossover/eval/second-labeller/EVIDENCE.md:276, packages/exp12-encoder-crossover/eval/second-labeller/RUN.json:100, packages/exp12-encoder-crossover/eval/second-labeller/RUN.json:100, packages/exp12-encoder-crossover/eval/second-labeller/RUN.json:126 |
| `AGENTS.md` | 4 | 4 | INC | packages/exp12-encoder-crossover/code/harness/analyze.py:469, packages/exp12-encoder-crossover/code/harness/prepare.py:11, packages/exp12-encoder-crossover/eval/results/REPORT.md:11, packages/exp12-encoder-crossover/paper/CLAIMS.md:95 |
| `EXCLUDED.md` | 3 | 3 | INC | gate.sh:42, packages/exp12-encoder-crossover/code/fixture/reflex-decisions.ts:28, packages/exp12-encoder-crossover/code/verify/recompute-claims.py:14 |
| `DECIDER_TIER.md` | 3 | 2 | INC | packages/exp12-encoder-crossover/code/harness/README.md:72, packages/exp12-encoder-crossover/eval/preregistration/EXP12-typed-channel-comparison-prereg.md:79, packages/exp12-encoder-crossover/eval/preregistration/EXP12-typed-channel-comparison-prereg.md:79 |
| `WIRING.md` | 3 | 3 | INC | packages/exp12-encoder-crossover/code/harness/LEAD-WIRING.md:4, packages/exp12-encoder-crossover/code/harness/collect.py:372, packages/exp12-encoder-crossover/eval/results/REPORT.md:193 |
| `CITATION.cff` | 3 | 2 | INC | packages/exp12-encoder-crossover/paper/CHECKLIST.md:103, packages/exp12-encoder-crossover/paper/OPEN_QUESTIONS.md:58, packages/exp12-encoder-crossover/paper/OPEN_QUESTIONS.md:88 |
| `VERIFICATION_REPORT` | 2 | 2 | INC | gate.sh:51, packages/exp12-encoder-crossover/eval/second-labeller/metrics.json:5 |
| `INTEGRITY.md` | 2 | 2 | INC | packages/exp12-encoder-crossover/code/harness/LEAD-WIRING.md:34, packages/exp12-encoder-crossover/code/verify/recompute-claims.py:16 |
| `GATED_READ_PROVENANCE.md` | 2 | 1 | INC | packages/exp12-encoder-crossover/paper/REFS.md:27, packages/exp12-encoder-crossover/paper/REFS.md:130 |
| `WITHHELD.md` | 1 | 1 | INC | gate.sh:47 |
| `RESIDUALS.md` | 1 | 1 | INC | gate.sh:44 |

#### A.2.10 Identifiers that occur **only** inside `gate.sh`

`gate.sh` ships the 24-pattern HARD list and the 6-pattern REVIEW list **verbatim**, and the scanner excludes
itself (`--exclude="$SELF"`, `gate.sh:69`). It is therefore the one shipped file that the gate can never
audit, and it carries **17** project identifiers that appear nowhere else in the package:

`/home/zer0null`, `89003e70`, `ARCHIVE_WINDOW`, `CommitRecord`, `DISCLOSURE_INVENTORY`, `EXPOSURE_CLOSURE`, `RESIDUALS.md`, `TRADE_SECRET`, `WITHHELD.md`, `a5ef1b28`, `consonance`, `dag.ts`, `duval`, `publish-present-compete`, `src/layer`, `src/scope`, `store.ts`

That list is itself a leak inventory: it names nine internal process documents, five target-repo
identifiers, our source paths, and four mechanism symbols. **R2 cannot be satisfied while `gate.sh` ships in
this form.** Either the scanner stops shipping (recommended — §D ships a positive *checker* instead) or the
pattern file is externalised so the released tree contains no denylist.

### A.3 The five carriers, and where the current curation already stops

| carrier | example | in the scored stimulus? | current curation |
|---|---|---|---|
| `kind` values and id prefixes | `worker.class`, `memory.admission`, `topology` | no (field + id) | ships untouched (`redact.py` `SAFE_KEYS`) |
| metadata / corpus field names | `nCandidate`, `clanId`, `ruleSeenByReviser` | no | ships untouched — **~32k occurrences, never named by any pattern** |
| mechanism vocabulary in **questions and option labels** | `reasoner`, `editor`, `fs.write`, `admit()`, `expanded[]`, `StateClass`, `grantPolicy` | **yes — this is the model's input** | `redact.py` substitutes only `question`; **`options` are deliberately excluded** (`redact.py:206–207`; `CASE_FIELDS = ("question",)` at `:208`) |
| filenames, directory names, prose pointers | `reflex-decisions.ts`, `LEAD-WIRING.md`, `EXP12-typed-channel-comparison-prereg.md`, `REDACTION_REPORT.md` ×7 in the shipped fixture header | no | ships / partially neutralised (3 path rules only) |
| the scanner's own denylist | `gate.sh:36–59` | no | **ships verbatim, self-excluded** |

### A.4 Rationale strings — measured, and the answer is narrower than the card expected

The card anticipates that rationale strings are a leak carrier because *"in this fixture (they) often explain
the mechanism in plain English."* Measured:

- In the **as-audited** tree `repro/encoder-crossover-190/fixture/reflex-decisions.ts`, **all 190** `rationale`
  values are populated and every one is a full plain-English justification of the mechanism, e.g.
  *"plan() constructs the permitted set. For a grantPolicy of 'none' the construction emits model + context
  and nothing else …"* — internal API names, type names and enforcement rules in prose.
- In the **ship set**, both `code/fixture/reflex-decisions.ts` and `code/harness/data/fixture-190.json` carry
  **190 empty** `rationale` strings and **190 empty** `namespaces` arrays. The sanitisation stage already
  emptied them (value-level only; `id`, `kind`, `question`, `options`, `correct` are byte-identical to the
  as-audited instrument).

So rationale **values** are *not* a live carrier in the current ship set. What *is* a live carrier is the
**header comment of the shipped fixture** (`code/fixture/reflex-decisions.ts:1–27`), which is prose and does
ship: it names `REDACTION_REPORT.md` seven times, `EXCLUDED.md`, `redact.py`, `UREDACT1`, `repro/encoder-crossover-190/`,
`SANITISED`, `HEAD 907fa39`, and describes the withheld system's semantics. That header must be replaced by a
neutral provenance block under R2 — it is the cleanest, cheapest win in this whole document.

---

## B. The substitution map

### B.1 Scheme: `NEUTRAL-TAG/v1`

Placeholders are **class-prefixed ordinals**, not descriptive renames:

```
K01 … K07   kind values            (K = decision kind)
F01 … F59   metadata field names   (F = field)
S01 … S30   mechanism symbols      (S = symbol)
C01 … C07   tool / capability tok  (C = capability)
R01 … R11   agent-class / role     (R = role)
D01 … D39   filenames, dirs, pointers (D = document/path)   [most are DELETED, not re-tagged]
```
Ordinals are assigned by a **seed-shuffled** permutation of the internal identifier list, so the tag carries
no lexical hint of the original. The mapping table `M` is an **internal artefact and does not ship** — if it
shipped, it would be the census. `TAG_01 … TAG_99` is retained as the scheme for top-level *directory* names
(§C), where no tokeniser sees them.

Two properties make this scheme safe, and both are checkable:

- **Token-boundary preservation.** Every tag matches `^[A-Za-z][0-9]{2,}$`, which the scorer's
  `TOKEN = re.compile(r"[a-z0-9]+")` (`second-labeller/compare.py:19`) reads as **exactly one token**
  (`k01`, `f17`, …). A descriptive camelCase rename (`policyField`) can split into two or more tokens and
  change overlap counts; an ordinal tag cannot.
- **Absence from the scored text.** The fixture's 190 questions contain **888 distinct tokens**. No `K/F/S/C/R`
  tag collides with any of them, because the tags are alphanumeric strings of a shape the corpus does not use.

### B.2 Stratum 1 — rename-safe identifiers (`LS`, 90 identifiers)

These never enter the model's input, so a bijective rename **cannot move any published number**:

- all 7 `kind` values and 6 dotted namespace values (−→ `K01…K07`);
- all 59 metadata/corpus/scoring field names (−→ `F01…F59`);
- every non-scored symbol (e.g. `CommitRecord`, gate-only).

**Consequences that are not numbers but must be regenerated:** the label keys inside
`eval/results/eval-*.json`, `eval/results/baselines.json`, `second-labeller/labelsB.json`,
`second-labeller/disagreements.jsonl` and `eval/results/DEFECT-EVIDENCE.json` are keyed by `kind` value and
by option label. Those files are derived artefacts; they must be **regenerated** under the new tags, not
hand-edited. `code/verify/recompute-claims.py` consumes only `id`, `correct` and `accuracy`, so the ten
CLAIMS numbers are invariant under stratum 1 — this is exactly what UTOK2 measured (ten numbers hold 10/10).

### B.3 Stratum 2 — the scored stimulus (`LK`, 33 identifiers + 100 option labels)

This is the stratum where the policy meets physics, and it must be stated plainly.

**The option labels and questions are simultaneously (a) the model's input — the numbers are a function of
them — and (b) plain-English descriptions of the withheld mechanism.** `redact.py:206–207` already knows
this: `CASE_FIELDS = ("question",)` (`:208`) deliberately excludes `options`, and the comment records that
substituting a single option label moved `routeA.ties` from 120 to 119.

The measured mechanism of that movement (UVER12/UTOK2, reproduced logic): `route_a()` scores each option by
distinct-token overlap with the question plus a 0.5 bonus when the normalised option is a substring of the
normalised question. `admit(` tokenises to the single token `admit`; `ADMIT_A` tokenises to `admit` **and
`a`**, and `a` occurs in the question, so that option's overlap rose by one and broke a tie toward itself.
Any rename that **adds** a token present in the question can move `routeA.*`; a rename that only **removes or
replaces** tokens, or adds tokens absent from all 190 questions, cannot.

**Therefore the safe rule, which applies to every rename in this stratum:**

> **R-B.3.1** Before/after every rename touching `question`, `options`, `kind`, `id` or any label-keyed
> results file, re-run `second-labeller/compare.py` and assert that **every** `routeA.*` field in
> `second-labeller/metrics.json` is byte-identical. Any movement is a declared change, not a silent one.
> **R-B.3.2** Prefer tags that *remove* tokens. Where the original is an identifier inside prose
> (`"none -- admit() mints the state"`, `"the expanded[] ref list"`), delete the identifier and keep the
> prose readable (`"none -- the decision mints the state"`) rather than injecting an alphanumeric tag, which
> changes the token multiset. 656 two-character tokens are absent from all 190 questions and are available if
> a tag is genuinely required.

**And then the fork, which the orchestrator must decide, because the two horns cannot both be taken:**

| | **F-A · Minimal rename** (recommended for this paper) | **F-B · Full re-instantiation** |
|---|---|---|
| what changes | identifiers in the stimulus are replaced by neutral terms of the same kind **only where they are unambiguous identifiers** (`StateClass`, `grantPolicy`, `admit()`, `expanded[]`, `policyHash`, class names, capability tokens); plain-English mechanism prose stays | questions and option labels are rewritten into a coherent neutral domain (e.g. a generic typed-entitlement instrument) |
| R2 "no identifier" | **satisfied** — no project identifier survives | **satisfied** |
| R2 "…or in prose" | **not satisfied** — the prose still describes a generic mechanism in English, though no longer *our* names | satisfied |
| published numbers | **preserved**, and re-derivable from the shipped bytes (re-run `compare.py` per R-B.3.1; UTOK2 measured all ten CLAIMS numbers invariant) | **destroyed** — the model's input changed, so every encoder arm must be **re-run** and `results/*.json`, `CLAIMS.md`, `results/REPORT.md` and every number in `MANUSCRIPT.md` re-derived |
| cost | days | a full re-evaluation of five encoder arms plus the 4B decider |
| fits the author's words | *"redacting any project level details and just creating random tags"* | *"abstract the understandings from the experiments"* |

**Recommendation: F-A, with the prose clause read as "no project identifier", not "no English about
mechanisms".** A reader cannot re-derive 0.6789 from `TAG_07`; an instrument whose options are opaque tags is
not an instrument. If the author wants the stricter reading, F-B is the only honest route and the paper must
be re-numbered, not re-worded. **This is the single most important thing in this document.**

### B.4 Stratum 3 — pointers, filenames, directories (`INC`, 49 identifiers)

Delete rather than rename where the file itself does not ship (a renamed pointer to an absent document is
still a pointer). Where a name must survive because it is read at runtime, re-tag it:

| current | action | reason |
|---|---|---|
| `REDACTION_REPORT.md` ×7, `EXCLUDED.md`, `SCRUB_REPORT.md`, `INTEGRITY.md`, `RESIDUALS.md`, `LICENCE_TODO.md`, `MANIFEST.json`, `REDACT3_REPORT.md`, `VERIFICATION_REPORT*` | **delete the pointer** | names internal process documents; none ships, so the pointer is unresolvable **and** revealing |
| `code/fixture/reflex-decisions.ts:1–27` header block | **replace with a neutral provenance block** | ships, is prose, names `REDACTION_REPORT.md` ×7, `redact.py`, `UREDACT1`, `repro/…`, `HEAD 907fa39` |
| `reflex-decisions.ts` | `D01` (or `instrument.ts`) | project-specific name; recorder logs it in 2 places |
| `DECISION_CASE_SCHEMA.ts` | `D02` (or `schema.ts`) | `DecisionCase`/`DecisionKind` name the withheld taxonomy |
| `tccommon.py`, `tcmodel.py`, `defect-probe.py` | `D03`–`D05` | `tc` = typed-channel, our harness's name |
| `LEAD-WIRING.md` | `D06` | names a withheld composition concept |
| `EXP12-typed-channel-comparison-prereg.md` | `D07` | package name + `typed-channel` |
| `EXP#12`, `paper #3`, `EXP12` | `TAG_07` | internal experiment numbering |
| `typed-channel` (also `MANUSCRIPT.md:133`, `:321`, `:754`) | `TAG_07` | our internal harness's name |
| `gate.sh` | **do not ship** | ships the denylist; self-excluded from its own scan |

---

## C. The placeholder harness architecture (design sketch)

The harness is re-presented as a **generic measurement host** that loads an instrument and does not know what
the instrument is about. Nothing in the tree says what the instrument decides, who wrote it, or what system
it describes.

```
research-publish-packages/
├── README.md            what this is, the claim it supports, the licence
├── LICENSE
├── check.sh             the released totality check (§D) — a positive vocabulary assertion, NOT a denylist
├── instrument/          THE INSTRUMENT (everything the numbers are a function of)
│   ├── schema.ts        <INSTRUMENT> record shape: id, kind, question, options[], correct, rationale, namespaces
│   ├── instrument.ts    the 190 records, tags applied, rationales/namespaces empty
│   └── data/
│       ├── instrument.json   the same 190 records, machine-readable
│       ├── manifest.json     digests + generation provenance (no internal paths)
│       ├── corpus.json       optional corpus/BEHAVIOUR features (F-tags)
│       ├── train.jsonl / dev.jsonl
│       └── lint-report.json
├── host/                THE PLACEHOLDER HARNESS — a generic architecture, not ours
│   ├── README.md        "host: load an instrument, fit a head, score it"
│   ├── prepare.py       instrument -> train/dev splits
│   ├── fit.py           fit a head            (was train.py)
│   ├── score.py         score a head          (was evaluate.py)
│   ├── summarise.py     per-kind / per-stratum breakdown (was analyze.py)
│   ├── collect.py       gather runs into one table
│   ├── emit.py          instrument -> alternative serialisation (was export-fixture.ts)
│   ├── lint.ts          instrument self-consistency
│   └── wiring.md        how a head is wired to an instrument (generic; was LEAD-WIRING.md)
├── baselines/           the scorer + the human second pass, presented as generic baselines
│   ├── token_overlap.py (was compare.py)
│   ├── parse.py, metrics.json, labels_b.json, disagreements.jsonl, EVIDENCE.md, RUN.json
│   ├── README.md        pre-registration of the baseline
│   └── robustness/      second pass, RUN2.json + ROBUSTNESS.md   (was second-labeller-190/)
├── runs/                frozen results (was eval/)
│   ├── RUN-<model>.json, RUN-baseline-*.json
│   ├── DEFECT-EVIDENCE.json
│   └── REPORT.md
├── verify/
│   └── recompute-claims.py    reads instrument + runs/, prints the ten numbers
└── paper/               the manuscript, its claims, its references
```

**Entry points and what each does** — deliberately verb-like and domain-free: `host/prepare.py` →
`instrument, split → dataset`; `host/fit.py` → `dataset → head`; `host/score.py` → `head × instrument →
per-record predictions`; `host/summarise.py` → `predictions → table`; `baselines/token_overlap.py` →
`instrument → predicted labels + tie count`; `verify/recompute-claims.py` → `instrument + runs/ → the ten
numbers`.

**What the architecture must not do.** It must not name: the system under study, our repository, our
directories, our experiment numbers, our agents or classes, our capability vocabulary, our internal
documents, or any branch/commit. The instrument is an opaque artefact the host consumes; the host is a
generic architecture that could host *any* typed-single-label instrument. That is R4, and it is a *shape*
requirement, not a find-and-replace: a renamed copy of our harness would still have its call graph, its
concept vocabulary and its file roles. The sketch above removes the roles (`LEAD-WIRING` becomes
`host/wiring.md`), not just the names.

---

## D. The totality check

### D.1 Why the 24-pattern HARD list cannot answer the question

The HARD list is a **denylist of 24 literal strings** plus 6 review strings. It can only
report what someone already thought of, so it answers *"did we leak any of the 30 strings we enumerated?"* —
never *"is any project reference left?"*. Measured on the same tree:

- the census found **172** distinct project-specific identifiers; the denylist matches **31**
  (including the 17 that live only inside `gate.sh`) → **141 identifiers, ~81%,
  are structurally invisible to it**;
- the gap is not a fringe: it contains the whole **metadata field class** (~32,000 occurrences) and most of
  the **in-stimulus mechanism vocabulary** — `reasoner` (38), `editor` (50), `fs.read` (24), `fs.write` (27),
  `test.run` (7), `memory.write` (5), `web.fetch` (2), `code-inspector` (7), `memory-curator` (4),
  `output-only` (12), `attached` (38), `detached` (20), `pin` (26), `projection` (13), `refusal` (15),
  `manifest` (19), `topology` (22), `capability` (11), `broker` (5), `scope` (10), `layer` (9),
  `acquisition`, `escalation` — **none of which any pattern names**;
- it **excludes itself** (`gate.sh:69`), so the file that holds the denylist is never scanned, and it ships
  the denylist. The gate cannot audit the gate;
- and it runs a `case-insensitive` `grep -F` per pattern, so it catches literal substrings only — never a
  case/separator variant (`state_class`, `STATE-CLASS`), a n-gram, or a term that was renamed yesterday.

Adding strings cannot fix the shape. A closed pattern set has a **complement problem**; the totality check
inverts it.

### D.2 The procedure (runnable)

```bash
# 0. Build the candidate release (successor of UBUILD1.build.sh, which emits the code-agnostic tree).
REL=.ucurate1/pre/research-publish-packages       # candidate released tree
INT=repro/encoder-crossover-190                   # the as-audited internal instrument
MAP=scratch/uagnostic1/substitution.tsv           # internal map M — MUST NOT be copied into $REL

# 1. Open inventory: tokenise the released tree; split on [^A-Za-z0-9_.$/@-].
#    Every token is endeavoured to be a member of one of:
#      (a) the placeholder grammar    ^(K|F|S|C|R|D)[0-9]{2}$ | ^TAG_[0-9]{2}$
#      (b) a frozen public identifier  (model ids, library names — agent_docs/public_ids.txt)
#      (c) a frozen English word list  (agent_docs/words.txt)
#    Anything else is a REVIEW line, not a verdict — English prose is open-ended, so (c) can never close.
python3 tools/token_inventory.py "$REL" > /tmp/rel.tokens

# 2. THE VERDICT — differential totality. M is total on the internal project vocabulary.
python3 tools/totality_check.py     --internal "$INT" --internal-extra docs experiments repro     --released "$REL" --map "$MAP" --public agent_docs/public_ids.txt --english agent_docs/words.txt
#    asserts, and FAILS LOUDLY otherwise:
#    T1  project_tokens(internal) ∩ tokens(released) == {}
#        (no internal project token survives in the released tree in any form)
#    T2  image_M(project_tokens(internal)) ⊆ tokens(released)
#        (every project token has its declared image present, or is listed in DROP)
#    T3  M is injective and total on its domain; every released tag has exactly one preimage
#        (no orphan tags, no two identifiers sharing a tag)
#    T4  every internal project token NOT in the released tree is either in DROP.tsv or in dom(M)
#        (nothing was silently dropped)
#    T5  no released file contains a scanner/denylist:
#        ! grep -RIl 'PATTERNS_HARD\|PATTERNS_REVIEW\|HARD_FILE\|GATE_EOF\|CODE_VOCAB_EOF\|PUBLIC_VOCAB_EOF' "$REL"
#          the first three names are the character strings of the denylist that `orchestration/units/UBUILD1.build.sh`
#          no longer contains (ULICENCE3 deleted those heredocs); the last three name the positive vocabulary
#          checker that replaced it, written by the heredoc beginning `cat > "$DEST/gate.sh" <<'GATE_EOF'`
#          (currently `:771`–`:896`, `chmod +x` at `:897`)

# 3. Variant fuzz — substrings and separators. For every identifier in M's domain, generate its
#    n-grams (n>=4) and case/separator variants (StateClass, state_class, state-class, stateclass,
#    STATECLASS) and grep. Any hit is a failure of T1.
python3 tools/variant_sweep.py --map "$MAP" --tree "$REL"

# 4. Clean-room replay. Clone/copy $REL to /tmp/rel, with no access to M, INT, or this workspace,
#    and run its own shipped checker. It must PASS from a tree that has never seen the internal names.
cp -r "$REL" /tmp/rel && ( cd /tmp/rel && ./check.sh )
```

**Deliverable of the check:** the released tree carries `check.sh` that asserts the **positive** property —
*every token in this tree is a declared member of this tree's own vocabulary* (instrument schema + README
glossary + frozen public lists + English fuzz), with the placeholder grammar accepted wholesale. A tree that
satisfies that is closed under its own description; a tree that does not, cannot be audited by listing the
strings we happened to remember.

**Red→green.** Inject any internal identifier (e.g. `grantPolicy`) into a copy of `$REL`; `./check.sh` and T1
must fail. Revert; both must pass.

### D.3 What the check cannot do — stated, not hidden

The English fuzz means an all-English leak that names no project identifier (e.g. a sentence describing the
mechanism without using any of our names) passes every mechanical test. That is not a checker defect; it is
the **F-A/F-B fork of §B.3** expressed as a limitation: mechanical totality covers *identifiers*, and the
policy's "…or in prose" clause is enforceable only by human reading of the manuscript and the instrument's
option text. §D therefore proves R2's identifier clause completely and R2's prose clause not at all.

---

## E. What this means for the paper

### E.1 `papers/encoder-crossover-190/MANUSCRIPT.md:793` (and `:258`) — the fixture digest

The manuscript currently states the sha256
`076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`. Measured:

| file | sha256 |
|---|---|
| as-audited `repro/encoder-crossover-190/fixture/reflex-decisions.ts` | `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796` ← **what the manuscript cites** |
| shipped `…/code/fixture/reflex-decisions.ts` | `751dc007ba115dccc5815fdf97c9ce7b34b0dc990a6e57802d762e9b35ad9cae` |
| shipped `…/code/harness/data/fixture-190.json` | `3c64af010783f82c9af6066b4ac5525ac86e3775bb6e65ad9107258e0b82a032` |

So the manuscript already publishes the digest of **a file the package does not ship**. Under the
code-agnostic policy the instrument is re-tagged and its bytes change again, so the requirement is stronger
than correcting the hash:

> The manuscript must cite the **sha256 of the instrument as actually shipped**, computed from the released
> bytes at build time and injected by the build (never hand-copied), **and it must drop any
> "byte-identical to the as-audited instrument" claim** — every such claim (`code/fixture/reflex-decisions.ts:6–9`
> currently makes it) becomes false the moment tags are applied.

### E.2 `MANUSCRIPT.md:835–840` — "the code licence is still open"

Under the code-agnostic policy the withheld code is not released at all, so the paragraph as written becomes
false in both directions: there is no proprietary-code subset to license non-commercially, and the reason it
was "still open" (negotiating a source-available licence for code that embeds the withheld design) disappears
with the code. Required change:

> Replace the whole "Licence of the subset — separate, and still open" block with one sentence: the released
> harness is a **neutral re-implementation** released under a permissive licence (the paper's own CC BY 4.0 for
> text/data + a permissive code licence), it contains no part of the withheld system, and the separate
> source-available question applies only to the **withheld** system, which is not published.
> **`no licence has been chosen yet` (`:838`) must not survive into the release** — the policy removes the
> condition that made it open.
>
> If the author chooses **F-B**, this is unconditional. If **F-A**, the same text works provided the released
> `host/` files are genuinely generic — which is a §C question, not a licence question.

### E.3 The instrument's description: "a sealed typed-single-label decision fixture" / "typed-channel"

These are two different things and they get two different answers:

- **"a sealed typed-single-label decision fixture"** (`MANUSCRIPT.md:26`, `:84`, `:93`) — **compatible, keep.**
  It names no system: "typed" refers to the record's `kind` field, "single-label" to `correct: number`,
  "sealed" to the withheld rationales. It describes a *method*, which is exactly what R4 wants the reader to
  see. One caution: with the fixture's `kind` values re-tagged to `K01…K07` the word "typed" becomes
  under-explained — the reader sees seven opaque kinds. The release must ship a `kind` **glossary** that says
  what each tag means *at the level the task requires* (e.g. "K03: choose the component that performs an
  action"), which is the F-A/F-B fork again in miniature.
- **"typed-channel"** (`:133`, `:321`; and `:754`: *"recovered from an unmerged development branch (name and
  commit withheld), path `tools/typed-channel/`"*) — **not compatible, must change.** `typed-channel` is our
  internal harness's name and a path in the withheld repository. It becomes the placeholder tag `TAG_07`, and
  the provenance sentence must not name a private branch, commit, or path — it should state only that the
  released harness is a neutral re-implementation of a measurement host, external to the withheld system.
  Likewise `MANUSCRIPT.md`'s citations of `docs/DECIDER_STACK_DECISION.md` §11.6 and commit `ad301ae1…` name
  artefacts the release does not ship and must become internal-record references or be dropped.

---

## F. UNVERIFIED

1. **Whether F-A satisfies the author.** The policy's R2 says "…or prose"; F-A leaves generic English
   mechanism prose in the instrument. I could not resolve this from the author's words — *"redacting any
   project level details and just creating random tags"* reads as F-A, *"abstract the understandings from the
   experiments"* reads as F-B. **This is a decision for the author, not a measurement.**
2. **The full 215-label mapping is not written out.** §B gives the rule, the scheme and the 3 strata;
   100 literal replacement strings for the mechanism option labels are not proposed here, because doing so
   under F-A vs F-B is a different job (delete-the-identifier vs rewrite-the-domain).
3. **`routeA.*` invariance is asserted from UTOK2's measurement of two labels, not re-measured for the full
   stratum.** The procedure R-B.3.1 is stated; it has not been run over the whole rename set.
4. **The `kind`-glossary question** (§E.3) — what the released `K01…K07` tags are allowed to say — is
   unresolved and it determines whether the instrument is answerable at all.
5. **I did not read the whole of** `strategy/WITHHELD.md` (register M1–M13, ~150 lines), `CODE_LICENSING_STRATEGY.md`
   (~550 lines) or `strategy/VERIFICATION_REPORT_12.md`; I used their headings and grep hits. The licence
   recommendation in §E.2 follows from the policy, not from a full reading of the licensing analysis.
6. **The as-audited tree's `rationale`/`namespaces` values were sampled, not censused** — 3 examples read,
   190 counted. The full prose vocabulary inside the 190 rationales is not enumerated, so the claim "every one
   explains the mechanism in plain English" rests on the sample plus the shipped header's own statement.
7. **`scratch/uregen1/` (UREGEN1's 66-file tree) was not censused.** The census was run over the UCURATE1
   staged ship set (`.ucurate1/pre/research-publish-packages`), which the card names as the ship set. If the released tree is rebuilt from
   `scratch/uregen1/tree/` instead, the counts must be re-run there.
8. **The 62-line figure in `strategy/REGEN_ASSESSMENT.md` §2 was not independently reproduced**; §A.1 argues
   only that it is a floor, for the reason REGEN_ASSESSMENT itself gives (the pattern list's constraint).
