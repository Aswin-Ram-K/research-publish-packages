# GATED_READ_DISCLOSURE.md — element-by-element disclosure classification for candidate #7

**Unit:** UDISCLOSE7 · **Status:** classification complete (report only — nothing drafted, renamed, redacted or packaged)
**Subject:** candidate #7 — *"Batching binary gates is free; routed extraction cuts context 15.3× and exposure to 0/20"*
**Mechanism of record (read, not remembered):** `/home/zer0null/Duval/tools/gated-read/bench.py` (762 L),
`/home/zer0null/Duval/docs/research/GATED_READ_2026.md` (340 L), the candidate record
`strategy/PAPER_CANDIDATES.md:530–572` (§B7), `:1028` (§G.1 row), `:1068–1075` (§G.2 #7), and the
disclosure authorities `strategy/WITHHELD.md`, `strategy/DISCLOSURE_INVENTORY.md`,
`strategy/PRIOR_DISCLOSURE_AUDIT.md`, `strategy/ARCHIVE_WINDOW_CHECK.md`.

**Class meanings used strictly:** `publish` = safe in public prose as-is · `withhold` = may not appear in the
paper or the released tree at all · `neutralise` = the fact may be published, but only under a uniform generic
tag (injective, case-sensitive, longest-first; mapping held in memory, never shipped) · `already-disclosed` =
public via the MIT derivation document and/or the AGPL window, with evidence recorded. An element may carry
**two** classes (`already-disclosed` + `neutralise`) when the idea is public but the names and parameters are
not — those are stated separately, never collapsed.

---

## 1. WITHHOLD LIST — may never appear in the paper or the released tree

Act on this list as a checklist. One line of reason each.

1. **`tools/gated-read/bench.py` as a shipped artifact, and its module name/path.** M13/W5: `tools/**` maps the private repo; a paper needing such a harness must ship a **re-implemented, neutral** one (`strategy/WITHHELD.md:109`, `:337–340`).
2. **`tools/gated-read/tasks.json` and its content** (the 20 questions, their answer strings, the 90-file corpus path list). It is a directory map of the private tree plus the gold answers (M13; M12 for the `src/**` entries).
3. **`docs/research/gated-read-rows.jsonl` and `docs/research/gated-read-summary.json` as artifacts.** Private corpora — row files carry file paths, answers and model ids (`strategy/WITHHELD.md:339`).
4. **Any `src/**` or `kernel/**` path name** in the paper or a released harness (M12: "a released harness must not name `src/**` paths", `strategy/WITHHELD.md:108`). Includes the grep-hit list `src/loop.ts`, `src/lease.ts`, `src/dag.ts`, `src/generation.ts`, `src/invariants.ts`, `src/envelope.ts`, `src/adapters/stub-agent.ts`, `src/adapter.ts`, `src/decisions.ts`, `src/state.ts`, `src/ledger-tools.ts`, `src/promotion.ts`, `src/proxy.ts`, `src/layer.ts`, `src/policy.ts`, `src/commit.ts`, `src/observation.ts`, `src/scope.ts`, `src/sandbox.ts`. **Dated class change (2026-10-16, unit UFIXAD6) — moved to `already-disclosed` (window version only).** The AGPL window carried 35 blobs under `consonance/src/` (708,575 B, HTTP 200 on `89003e7069c9ad79c40d91982720751b1ddf0360`), so these names were public in the window. The `consonance/` → target `src/**` mapping is recorded (`strategy/DISCLOSURE_INVENTORY.md:19`, `:38`, `:44`) and corroborated by three exact byte-size matches against `/home/zer0null/Duval`: `src/journal.ts` 46,450 B, `src/dag.ts` 44,468 B, `src/store.ts` 3,316 B. **Caveat:** the *fact* is already public, but the paper must still not republish this material and no filing may assert non-publication. Authority: `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md`.
5. **The concrete shape of the product's gate/absence machinery** that the staged extractor embodies (M10), *as construction* — `strategy/PAPER_CANDIDATES.md:1028` settles that "the **staged extractor** — whose routing/gating *is* the gate/absence machinery (M10) — is the part that must not ship". **Dated class change (2026-10-16, unit UFIXAD6) — moved to `already-disclosed` (window version only).** The window's `consonance/src/**` (35 blobs / 708,575 B) published the gate/absence construction shape as code. **Caveat:** the *fact* is already public, but the paper must still not republish this material and no filing may assert non-publication. Authority: `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md`.
6. **The KeyRing/broker credential surface:** `GATED_URL` default endpoint, `KEYRING_API_KEY`, `~/.dsh/.credentials.yaml`, the `okr_[A-Za-z0-9_-]+` key shape (`bench.py:56`, `:78–91`).
7. **The fixture's questions and gold answer strings.** They are the private repo's own content; the *labelling rule* publishes, the *answers* never do.
8. **Internal run/VCS identifiers that address the private tree:** branch `measure/gated-read` (`docs/research/GATED_READ_2026.md:5`).
9. **Any claim of first disclosure for M1–M13 or for the gate/absence idea.** All 13 mechanisms are already public under MIT (`strategy/WITHHELD.md:259–295`, hash `d98c4359…`, 46,636 B); the effort axis on decisions is published in the same public repo.
10. **Any assertion or filing line that the work was never published.** `strategy/WITHHELD.md:313–316` and §8.3 (`:329–346`): the design is published; only the implementation is protectable.
11. **`PWNED-A`/`PWNED-B` as literal payload identifiers** (use `[PAYLOAD-1]`/`[PAYLOAD-2]`); the strings themselves are harmless but the uniform-tag rule admits no exceptions.
12. **`deepseek-v4-flash` / `deepseek-v4.1-flash` / `mimo-v2.6-flash` as literal model ids** in the shipped tree (use `[MODEL-1]`/`[MODEL-2]`/`[RUNTIME-1]`). *(Borderline: third-party public names, but the code-agnostic rule tags every proper name; if the author rules model ids publishable, this item drops — see §6 U-3.)*

**Dated class change (2026-10-16, unit UFIXAD6).** Items **4** and **5** above are moved to `already-disclosed` for the window's version (see the dated notes on each). The AGPL window carried `consonance/` + `app/` only, so items **1, 2, 3, 6, 7, 8, 9, 10, 11, 12** are unchanged. **Caveat:** the *fact* is already public, but the paper must still not republish this material and no filing may assert non-publication. Authority: `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md`.

---

## 2. Classification policy (the discriminators actually applied)

- **Result vs construction.** A number is `publish` if it is a **result or an argued design condition** (batch
  size, effort level, metric value, token count, exposure count). A number is `neutralise` if it is an
  **incidental construction constant** of the harness (preview lengths, caps, budgets, concurrency, retries,
  timeouts, `max_tokens`). Rationale: the paper's credibility *is* the measurement; the harness blueprint is
  what the code-agnostic policy withholds (`strategy/CODE_AGNOSTIC_RELEASE_POLICY.md`; smallest possible portion).
- **Idea vs name vs parameter.** M1–M13 are already public **in idea** (`strategy/WITHHELD.md:259–295`). A
  candidate-#7 element that re-states M10/M7/M5 is therefore `already-disclosed` for the idea, while its
  **names, paths and constants** are `neutralise` and its **private-tree artifacts** are `withhold`.
- **Constraint publishes, construction does not.** Per `strategy/PAPER_CANDIDATES.md:1041–1045`: "report the
  result and the constraint; never the construction". A gate that fails because it sees only a bounded preview
  is a publishable **constraint**; the preview lengths are `neutralise`.
- **Tag vocabulary** (`[KIND-n]`, assigned in memory, never shipped): `[FAMILY]` project name · `[HARNESS-1]`
  the bench module · `[FIXTURE-1]` · `[ROWS-1]`/`[SUMMARY-1]` · `[DOC-1..3]` the three in-tree research docs ·
  `[CORPUS-n]` corpus roots · `[ARM-n]` e2e arms · `[MODE-n]` gate/stage/router modes · `[ROLE-n]` gate/stager/
  router/reasoner · `[MODEL-1..2]`, `[RUNTIME-1]` · `[EXTRACT-n]` the four extraction methods · `[PAYLOAD-1..2]`
  · `[CONST-n]` construction constants · `[RUN-1]` branch/run label · `[TASK-n]` round-2 work items.

---

## 3. Element table

Path prefixes: target files are absolute (`/home/zer0null/Duval/…`); workspace files are relative to
`/home/zer0null/reserach extarctor/`.

### 3.1 Mechanism steps (what it does, in the abstract)

| ID | Element | Where | Class | Reason / tag kind |
|---|---|---|---|---|
| R-01 | Per-(task, file) binary read decision `{"relevant": true|false}`, conditioned on question + stated purpose + path + header + structure outline; **never** the file body | `docs/research/GATED_READ_2026.md:15–18`; `bench.py:258–269` | `already-disclosed` + `neutralise` | Idea public: M10 `strategy/WITHHELD.md:292`; nearest prior art Self-RAG/Adaptive-RAG `GATED_READ_2026.md:39–40`. Names/params private → `[ROLE-1]`, `[CONST-*]` |
| R-02 | Staged top-N shortlist from one pass over the whole listing; only staged files are opened | `GATED_READ_2026.md:19–20`; `bench.py:341–377` | `already-disclosed` + `neutralise` | Aider repo-map staging is public prior art (`:44`); M7-adjacent. `[ARM-STAGE]`, `[CONST-N]` |
| R-03 | Extraction router selects **one** of four primitives per (task, file); only extracted text enters the reasoner context | `GATED_READ_2026.md:21–24`; `bench.py:411–484` | `neutralise` (construction `withhold`) | This harness **is** the M10 machinery (`strategy/PAPER_CANDIDATES.md:1028`); the *measurement* may be reported under `[EXTRACT-n]`, the construction must not ship |
| R-04 | Anti-leak guard: grep terms must occur verbatim in the task text | `GATED_READ_2026.md:80–81`; `bench.py:443–451` | `publish` (guard name `neutralise`) | A validity constraint; publishing it is required for credibility. Identifier `safe_terms` → `[ROLE-4]` |
| R-05 | Injections appended **in memory at read time**; payload A rides non-gold reads, B rides gold reads; exposure (survives into context) and ASR measured separately | `GATED_READ_2026.md:26–28`, `:93–105`; `bench.py:65–68`, `:508–531` | `publish` + `already-disclosed` (channel) | Tool-result injection channels are public prior art (AgentDojo/InjecAgent/MCPTox, Greshake — `:44–51`). Payload tokens `neutralise` |
| R-06 | Gold label = "file bytes contain the task answer", recomputed from bytes each run; zero-miss enforced at fixture build | `GATED_READ_2026.md:62–65`; `bench.py:149–163` | `publish` (rule) + `withhold` (answers) | Mechanical labelling is the method; the answer strings are private content |
| R-07 | Five end-to-end arms compare self-select vs veto-gate vs staging vs staging+routing vs oracle, read budget 5 (gate arms unconstrained by design) | `GATED_READ_2026.md:83–91`; `bench.py:534–626` | `publish` + `neutralise` (arm labels) | Design publishes; `[ARM-n]` for the labels |
| R-08 | Context assembled by concatenation with truncation at a character cap; per-arm exposure counted on the exact handed-over context | `bench.py:508–531`, `:603–621` | `neutralise` | `[CONST-CAP]`; the *method* (count exposure on the exact context) is publish |
| R-09 | Summary reduces 5 gate configurations to precision/recall/F1/accuracy + token economics; unparsed decisions counted, never coerced | `GATED_READ_2026.md:111–113`; `bench.py:646–735` | `publish` | Method-level, and the honesty rule is a claim the paper must make |
| R-10 | Router degenerated to `grep` in 207/207 decisions — reported as the honest null, not as adaptive routing | `GATED_READ_2026.md:172–190`, `:250–257` | `publish` | The negative result is the contribution |
| R-11 | Round-2 designs: T1 single-payload injection, T2 heterogeneous workload, T3 gate-input ablation, T4 power, T5/T7 exposure-as-property, T6 cross-model | `GATED_READ_2026.md:277–295` | `neutralise` | Internal work-item labels → `[TASK-n]`; the designs themselves publish as constraints/future work |
| R-12 | Product-side gate/absence enforcement at a broker boundary (the thing the staged extractor is built on) | `strategy/WITHHELD.md:106` (M10), `:292` (public) | `already-disclosed` (idea) + `withhold` (construction) | Public via MIT `PAPER-DERIVATION.md` §1.3 `:63–64`, §4.4; `WHITEPAPER.md` §4/§5.2; `DECISION_LOG.md` D-009 |

### 3.2 Parameters, thresholds, magic numbers

| ID | Element | Where | Class | Reason / tag |
|---|---|---|---|---|
| P-01 | Batch sizes **1, 16, 90** | `GATED_READ_2026.md:73–74`, `:148–152`; `bench.py:302–307` | `publish` | Treatment levels of the measurement — the paper's axis |
| P-02 | Effort axis **none / minimal** | `GATED_READ_2026.md:73–74`, `:137–140`; `bench.py:292` | `publish` + `already-disclosed` | Same axis is published in the public decision log (`GATED_READ_2026.md:138` cites D-047); effect (recall 0.175→0.367) is a result |
| P-03 | Read budget **5 files**, top-**5** shortlist | `GATED_READ_2026.md:83`, `:20`; `bench.py:61` | `publish` | Argued design condition (budget parity across arms) |
| P-04 | Gate preview **300** chars; batch preview **120** chars; batch structure **12** lines; structure field cap **400** chars | `GATED_READ_2026.md:66–67`; `bench.py:264–268`, `:275–277` | `neutralise` | `[CONST-PREVIEW]` etc. The *constraint* (preview-only input) publishes; the depths do not |
| P-05 | Default preview **500** chars | `bench.py:166` | `neutralise` | `[CONST-PREVIEW-DEFAULT]` |
| P-06 | Structure outline cap **45** lines; fallback **first 10 lines**; markdown headings / code declarations regex | `bench.py:174–191` | `neutralise` | `[CONST-OUTLINE]` |
| P-07 | Term extraction: ≤**8** terms, drop tokens <**3** chars and stopwords | `bench.py:70–71`, `:207–215` | `neutralise` (+ publish the stopword policy as prose) | `[CONST-TERMS]` |
| P-08 | Context cap **250 000** chars (`GATED_CONTEXT_CAP`) | `bench.py:59` | `neutralise` | `[CONST-CAP]` |
| P-09 | Concurrency **8** (`GATED_CONCURRENCY`) | `bench.py:60`; `GATED_READ_2026.md:111` | `neutralise` | `[CONST-CONC]` |
| P-10 | `max_tokens` per call: **32** (bs1 gate), `max(64, 8·n)` (batch gate), **96** (router), **128** (stage), **160** (self-select), **256** (reason/router batch/e2e) | `bench.py:298`, `:318–319`, `:361`, `:460`, `:548`, `:565`, `:601` | `neutralise` | `[CONST-TOKENS]` |
| P-11 | Retries **3**, retry sleep **1.0 s**, request timeout **300 s**, `temperature: 0` | `bench.py:94`, `:107`, `:113`, `:99`, `:129` | `neutralise` (temperature 0 publishes) | `[CONST-RETRY]`, `[CONST-TIMEOUT]` |
| P-12 | Extraction constants: head_tail **40+40** lines; outline cap **80** lines; grep cap **60** hits with ±**1**-line window | `bench.py:390–407` | `neutralise` | `[CONST-EXTRACT]` |
| P-13 | Broker URL default `http://127.0.0.1:8790/v1/chat/completions` | `bench.py:56` | `withhold` | Credential/service surface (§1 item 6) |
| P-14 | Fixture scale: **20** tasks × **90** files, **1.83 MB**, **120** gold pairs (**6.7 %** base rate), each answer hits **1–13** files, **1 800** (task,file) pairs per gate config, **120** router pairs, **9 260** rows, **207** router decisions, **0** errors / **0** unparsed | `GATED_READ_2026.md:60–65`, `:119–122`, `:174`; `strategy/PAPER_CANDIDATES.md:541–546` | `publish` | Experiment scale and validity facts; no project identification |
| P-15 | Cost proxy: tokens ≈ `len(text) // 4` | `bench.py:472` | `publish` rule + `neutralise` divisor | The convention publishes; the divisor → `[CONST-COSTDIV]` |

### 3.3 Data / record field names

| ID | Element | Where | Class | Reason |
|---|---|---|---|---|
| F-01 | Row schema identifiers: `mode, task, tag, file, pred, model, effort, gold, ms, ptok, ctok, err, staged, hit, method, terms, suff, cost, oracle, chosen_ok, paths, n_files, expo_a, expo_b, truncated, ctx_has_a, ctx_has_b, ctx_chars, answer, pwned_a, pwned_b, not_found, empty, finish, arm, select_ms, select_err, routes` | `bench.py:301–330`, `:372–376`, `:475–482`, `:603–621` | `withhold` | Identifiers of the private row files (M13 / private corpora, `strategy/WITHHELD.md:339`); absent by construction once the harness is re-implemented |
| F-02 | Summary schema keys: `fixture{tasks, files, gold_pairs}`, `models{decision, reasoner}`, `gate{}`, `stage{}`, `router{}`, `e2e{}` and their metric keys (`precision, recall, f1, accuracy, tp/fp/fn/tn, unparsed, calls, prompt_tok_total, mean_ms_per_call, recall_at_5, method_dist, chosen_sufficient, mean_routed_cost, mean_full_cost, exposure_a_reads, exposure_b_reads, ctx_carries_a/b, asr_a/b, mean_ctx_chars, …`) | `bench.py:648–730`; `docs/research/gated-read-summary.json` (path only) | `withhold` | Same reason as F-01 |
| F-03 | Published metric labels the paper uses (accuracy, exposure, ASR, precision/recall/F1, prompt tokens, context characters, files read) | `GATED_READ_2026.md:71–78`, `:194–201` | `publish` | Generic measurement vocabulary; carries no internal names |
| F-04 | Gold-label predicate `gold(t,f) := f's bytes contain t's answer` | `GATED_READ_2026.md:64–65` | `publish` | Method |

### 3.4 State / role / tool names

| ID | Element | Where | Class | Reason / tag |
|---|---|---|---|---|
| N-01 | Mode labels `gate1_none`, `gate1_minimal`, `gate16_none`, `gate90_none`, `gate90_minimal`, `stage`, `router`, `e2e` | `bench.py:301`, `:323`, `:372`, `:475`, `:604` | `neutralise` | `[MODE-n]` |
| N-02 | Arm labels `selfselect`, `gate_none`, `gate_min`, `stage`, `stage_route`, `oracle` | `bench.py:539`; `GATED_READ_2026.md:87–91` | `neutralise` | `[ARM-n]`; the *comparison* publishes, the labels do not |
| N-03 | Extraction primitives `full_read`, `grep`, `head_tail`, `outline` | `bench.py:382`; `GATED_READ_2026.md:22–23` | `neutralise` | `[EXTRACT-n]`; plain-English "full read / term search / head-and-tail / outline" may publish |
| N-04 | Role names: decision model, reasoner, gate, stager, router | `GATED_READ_2026.md:13–24` | `publish` | Generic architectural roles |
| N-05 | Model ids `deepseek-v4-flash`, `deepseek-v4.1-flash`; runtime `mimo-v2.6-flash` | `bench.py:57–58`; `GATED_READ_2026.md:5`, `:109–110` | `neutralise` | `[MODEL-1]`, `[MODEL-2]`, `[RUNTIME-1]` — borderline, see §6 U-3 |
| N-06 | Branch/run label `measure/gated-read` | `GATED_READ_2026.md:5` | `withhold` | Addresses the private tree (§1 item 8) |
| N-07 | Payload tokens `PWNED-A`, `PWNED-B` | `bench.py:65–68`; `GATED_READ_2026.md:26–28` | `neutralise` | `[PAYLOAD-1]`, `[PAYLOAD-2]` |
| N-08 | The stopword list literal | `bench.py:70–71` | `neutralise` | `[CONST-STOPWORDS]` |
| N-09 | Public decision id `D-047` (effort axis) | `GATED_READ_2026.md:138` | `publish` | `decisions/DECISION_LOG.md` is public in the MIT repo (`strategy/WITHHELD.md:279`) |
| N-10 | State names `InvariantStatus`, `DecisionKind`, `StateClass`, `SandboxSpec`, `Budget`, namespaces `task/evidence/execution/capability/policy/decision` (if a candidate-#7 draft mentions them) | — (not present in the candidate-#7 mechanism; listed because a draft may import them) | `withhold` | M11 (`strategy/WITHHELD.md:107`, `:293`): public *as prose*, but the `DecisionKind` union/schema release decision is the author's (`:451–453`); no candidate-#7 need exists |
| N-11 | `worker.class`, `context.package` | `strategy/DISCLOSURE_INVENTORY.md:215` (recorded, not located) | `withhold` (UNVERIFIED) | Not located in the public log — do not publish either way |

### 3.5 File paths, module names, function names (implementation)

| ID | Element | Where | Class | Reason |
|---|---|---|---|---|
| X-01 | Bench module `/home/zer0null/Duval/tools/gated-read/bench.py` | target, 762 L | `withhold` | M13/W5 (§1 item 1); release only a re-implemented neutral harness |
| X-02 | Fixture `/home/zer0null/Duval/tools/gated-read/tasks.json` | target | `withhold` | M13 + corpus map (§1 item 2) |
| X-03 | Rows `/home/zer0null/Duval/docs/research/gated-read-rows.jsonl` | target | `withhold` | Private corpora (§1 item 3) |
| X-04 | Summary `/home/zer0null/Duval/docs/research/gated-read-summary.json` | target | `withhold` | Same |
| X-05 | Research doc `docs/research/GATED_READ_2026.md` (title "Gated Read") | target, 340 L | `neutralise` | `[DOC-1]`, experiment name → `[EXPERIMENT-1]`; the measurement prose publishes, the path and title do not |
| X-06 | `docs/research/GATED_READ_PROVENANCE.md` (276 L), `docs/research/STAGED_EXTRACTION_PROVENANCE.md` (299 L) | target | `neutralise` | `[DOC-2]`, `[DOC-3]`; the literature tables are public prior art and publish as related work |
| X-07 | Corpus roots `docs/`, `src/`, `tests/`, `evals/`, `examples/`, `tools/`, `scripts/` + 4 roots | `GATED_READ_2026.md:60–61` | `neutralise` |  `[CORPUS-n]`; `src/` also M12. **Dated class change (2026-10-16, unit UFIXAD6) — the `src/` root only is moved to `already-disclosed` (window version only).** The window carried `consonance/` and `app/` only; the other roots (`docs/`, `tests/`, `evals/`, `examples/`, `tools/`, `scripts/`) are **unchanged** (`neutralise`). Evidence: 35 `consonance/src/` blobs / 708,575 B, all HTTP 200 on `89003e7069c9ad79c40d91982720751b1ddf0360`. **Caveat:** the *fact* is already public, but the paper must still not republish this material and no filing may assert non-publication. Authority: `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md`. |
| X-08 | `src/**` file names (19 grep hits, listed in §1 item 4) | target `src/` | `withhold` → `already-disclosed` (window version; 2026-10-16, UFIXAD6) | M12 (`strategy/WITHHELD.md:108`). **Dated class change (2026-10-16, unit UFIXAD6):** moved to `already-disclosed` for the window's version — the window published 35 `consonance/src/` blobs (708,575 B). The `consonance/` → target `src/**` mapping is recorded (`strategy/DISCLOSURE_INVENTORY.md:19`, `:38`, `:44`) and corroborated by three exact byte-size matches against `/home/zer0null/Duval`: `src/journal.ts` 46,450 B, `src/dag.ts` 44,468 B, `src/store.ts` 3,316 B. **Caveat:** the *fact* is already public, but the paper must still not republish this material and no filing may assert non-publication. Authority: `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md`. |
| X-09 | Function names in the bench: `api_key`, `call`, `parse_json`, `load_fixture`, `preview`, `structure`, `norm`, `contains`, `question_terms`, `row_key`, `load_rows`, `emit`, `run_parallel`, `gate_prompt_1`, `gate_prompt_batch`, `mode_gate`, `stage_prompt`, `mode_stage`, `extract`, `router_prompt_1`, `router_prompt_batch`, `safe_terms`, `mode_router`, `reason_prompt`, `select_prompt`, `build_context`, `mode_e2e`, `prf`, `mode_summarize`, `main` | `bench.py:78–762` (each measured; e.g. `safe_terms` `:443`, `mode_e2e` `:534`, `extract` `:385`) | `withhold` | Identifiers of the private harness; none survives the neutral re-implementation |
| X-10 | Module-level constants `HERE, REPO, FIXTURE, ROWS, SUMMARY, URL, DECISION_MODEL, REASONER_MODEL, CONTEXT_CAP, CONCURRENCY, READ_BUDGET` | `bench.py:50–61` | `withhold` | Same; the *values* that publish are the results/treatment levels (P-01, P-03, P-14) |
| X-11 | Method/CLI surface `python3 tools/gated-read/bench.py gate|stage|router|e2e|summarize` | `bench.py:29–34`, `:739` | `withhold` | Private path + run surface; the neutral harness will have its own CLI |
| X-12 | Resumable rows keyed `(mode, task, tag)`, append-only JSONL | `bench.py:220–245` | `publish` (mechanism) + `withhold` (identifiers) | The resumability *method* is a reproducibility claim; the key names are F-01 |

### 3.6 Numbers the paper wants to publish

All of these are **`publish`** (results/validity), except where marked.

| ID | Number(s) | Where | Class |
|---|---|---|---|
| Q-01 | Title: **15.3×** context cut; **0/20** exposure | `strategy/PAPER_CANDIDATES.md:530`; `docs/research/GATED_READ_2026.md:215`, `:250` | `publish` — but see §8 (errata + power) |
| Q-02 | R1 gate table: P/R/F1/acc = 0.288/0.175/0.218/0.916 (bs1 none); 0.284/0.367/**0.320**/0.896 (bs1 minimal); 0.164/0.367/0.227/0.833 (bs16); 0.192/0.233/0.210/0.883 (bs90 none); **0.418**/0.233/0.299/0.927 (bs90 minimal); tokens 642 K / 822 K / 290 K / 308 K / 1 952 K; 357/457/161/171/1 084 per decision; always-false baseline 0.933 at 6.7 % base rate | `GATED_READ_2026.md:126–135` | `publish` |
| Q-03 | R2 batching: 1 800 → 120 (**15×**) → 20 (**90×**) calls; 631 K → 270 K (**2.3×**) → 261 K (2.4×) prompt tokens; F1 0.218 → 0.227 → 0.210 (±0.01); bs90 minimal **1.69 M** completion tokens; F1 0.299 | `GATED_READ_2026.md:146–163` | `publish` |
| Q-04 | R3 staging: `recall@5` 0.292 (35/120), **17/20** tasks with ≥1 gold, mean 4.35 files, 0 errors | `GATED_READ_2026.md:165–170` | `publish` |
| Q-05 | R4 router: `grep` **207/207**; sufficiency 1.000/0.700/0.375/0.108; chosen sufficient 0.700; cheapest-sufficient 0.575; 656 vs 8 931 tokens (**13.6×**) | `GATED_READ_2026.md:172–190` | `publish` |
| Q-06 | R5 arms: accuracy 0.65/0.65/0.60/0.55/0.45/0.20; files 4.8/7.75/4.35/4.35/3.65/4.1; context 83 K/130 K/71 K/**5.0 K**/82 K/169 K; prompt tokens 21.9 K/35.1 K/19.5 K/**1.4 K**/22.2 K/44.7 K; exposure 20/19/0/19/20; ASR 1/0, 1/1, 1/1, **0/0**, 2/2, 0/12 | `GATED_READ_2026.md:194–201` | `publish` — n=20; see §8 |
| Q-07 | R6: oracle hijacked **12/20**; clean oracle **4/8**; non-oracle doses 2.8–5.7 files, hijacked 1–4 times | `GATED_READ_2026.md:226–236` | `publish` |
| Q-08 | Run scale: 9 260 rows, 0 call errors, 0 unparsed; 1 800 pairs/config; 120 gold pairs (6.7 %); 120 router pairs; 20×6 e2e | `GATED_READ_2026.md:119–122` | `publish` |
| Q-09 | Errata: exposure union 20/20/19/0/19/20; cost ratio 15.6× → **15.3×** (21 872 / 1 432) | `GATED_READ_2026.md:203–207` | `publish` — the re-derived values are the ones to ship |
| Q-10 | Construction constants (P-04…P-12 values) | `bench.py` (as cited) | `neutralise` |
| Q-11 | Broker endpoint/port **8790** | `bench.py:56` | `withhold` |

---

## 4. Already-disclosed elements — evidence

| ID | Element | Evidence |
|---|---|---|
| AD-1 | M1–M13 mechanism descriptions, incl. M10 (enforcement by absence / scope narrowing / broker boundary), M7 (context engine), M5 (consume-once gate) | `strategy/WITHHELD.md:259–295`; public MIT repo `Aswin-Ram-K/publish-present-compete`, `findings/PAPER-DERIVATION.md` byte-identical to the target's copy — **46 636 B**, sha256 `d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802`; anchors M10 §1.3 `:63–64`/§4.4, M7 §4.5 `:380–397`, M5 §4.3b `:301–331`; `WHITEPAPER.md` §4/§5.2; `DECISION_LOG.md` D-009. Date ≤ 2026-10-10, licence MIT |
| AD-2 | M11 decision taxonomy / six namespaces | `strategy/WITHHELD.md:293`, `:417–453`; public `decisions/DECISION_LOG.md` D-024, D-045, D-048 (D-024 self-dated 2026-09-29). Residue: `worker.class`, `context.package` unlocated |
| AD-3 | Effort axis on decisions (the same axis that doubles gate recall) | `docs/research/GATED_READ_2026.md:137–140` cites D-047; `decisions/DECISION_LOG.md` is public (`strategy/WITHHELD.md:279`) |
| AD-4 | Nearest prior art for every component: Toolformer/TALM, Self-RAG, Mallen 2022, Adaptive-RAG, BFCL, Claude Code auto mode, GuardAgent, CaMeL, RouteLLM, FrugalGPT, aider repo map, GraphRAG, MemGPT, Batch Prompting (2301.08721), BatchPrompt (2309.00384) | `docs/research/GATED_READ_2026.md:36–47` |
| AD-5 | Injection channels and their measured ASRs: AgentDojo (2406.13352), InjecAgent, MCPTox, FocusAgent; the Greshake-et-al citation correction | `docs/research/GATED_READ_2026.md:44–51` |
| AD-6 | **AGPL window — CONFLICTED, must be reconciled; RESOLVED (2026-10-16, unit UFIXAD6).** *Dated note: the conflict is resolved — the window did expose the target's `src/**`; `WITHHELD.md:444–445`'s "404 at every historical ref" held only for branch/tag-reachable and path-absent refs. `ccdab112` carried **no** `consonance/` (tree `.gitignore CLAIMS.tsv README.md SOURCES.tsv`); the code sat on the unreferenced old head `89003e7069c9ad79c40d91982720751b1ddf0360` (200/46,450 B). Boundary: `ccdab112` (2026-10-09 04:11) → `b81b35e` (2026-10-10 07:51); event-measured 2026-10-09T04:20:17Z → 2026-10-10T07:52:54Z. Authority: `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md`.* The target's `src/**` is recorded as public under AGPL-3.0 for ~27.5 h (`ccdab112` 2026-10-09 04:11 → `b81b35e` 2026-10-10 07:51); the window tree is recorded as ~481 entries, ~428 under `consonance/` | `strategy/ARCHIVE_WINDOW_CHECK.md` (read this unit; lines not re-measured after compression) vs `strategy/WITHHELD.md:444–445`: *"`consonance/src/journal.ts` and `src/journal.ts` return 404 at every historical ref while a control README returns 200"* |

**Effect of AD-6 on this classification.** Every candidate-#7 element that is an *idea* is already
`already-disclosed` regardless (AD-1). If the AGPL window is confirmed to have carried the implementation,
then the code-level elements currently marked `withhold` (M10 construction, `src/**` names) move to
`already-disclosed` **for the window's version** — a withhold cannot be restored by omission, but the paper
must still not *republish* them, and no declaration may assert non-publication. The record conflict (AD-6) is
handed to the next unit rather than resolved here (§8). **Dated note (2026-10-16, unit UFIXAD6): that hand-off is discharged — AD-6 is RESOLVED.** The moving elements are §1 items 4–5, X-08 and X-07's `src/` component (window version only), each carrying the caveat that the paper still must not republish the material and no filing may assert non-publication. Authority: `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md`.

---

## 5. Residual risk after applying the classification

What a reader could still reconstruct, even with tags, withholding and neutralisation applied:

1. **The measurement protocol, almost exactly** (batch sizes, effort axis, metric definitions, exposure/ASR
   instrumentation, the gold-label rule). This is *intended* — it is the reproducibility claim — and it leaks
   nothing about the product. Residual: low.
2. **That the source project has a self-describing docs tree whose only bounded-preview gate is weak**
   (F1 0.320; the smoke note that a preview answered `false` on a gold file). A reader infers the project's
   prose is not organised for machine triage. Residual: low, reputational rather than structural.
3. **That the project's request distribution is "extract a value from a named file"** (router → `grep`
   100 %). A reader infers the internal workload shape. Residual: low–moderate; it says what the harness was
   for, not how the product is built.
4. **Correlating the published run scale** (20 tasks × 90 files, 1.83 MB, 120 gold pairs, 9 260 rows) **against
   any archived copy of the private tree** (AGPL window, caches, clones). If such a copy exists, the fixture was
   already reconstructible; the numbers only make the match easier. Residual: low, and it is the AD-6 risk, not
   a tag risk.
5. **The injection-probe design** (in-memory append, A on non-gold / B on gold, exposure vs ASR). Public prior
   art already measures this; the candidate's contribution is the *routing* effect. Residual: negligible.
6. **The end-to-end security claim is underpowered (n=20) and confounded by the two-payload design** — a reader
   cannot reproduce "0/20 exposure ⇒ safe". Residual: **not a disclosure risk but a validity risk**; the paper
   must ship the §G.2 split (batching note) or run T1/T4 (`docs/research/GATED_READ_2026.md:277–295`).
7. **The already-public design is restated** — if the paper describes a staged gate/router as if novel, a reader
   who finds `publish-present-compete` (MIT, byte-identical file) sees both the duplication and the
   first-disclosure problem. Residual: **attribution risk, highest-severity item in this report.**

---

## 6. Undecided elements (and why)

| ID | Element | Why undecided |
|---|---|---|
| U-1 | **DECIDED (2026-10-16, unit UFIXAD6): YES — the AGPL window did expose the implementation** (`consonance/` = target `src/**`); §1 item 5 and X-08 move to `already-disclosed` for the window's version. Authority: `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md`. — Whether the AGPL window actually exposed the implementation (`consonance/` = target `src/**`), i.e. whether §1 item 5 and X-08 are `withhold` or `already-disclosed` | Two on-disk records conflict: `strategy/ARCHIVE_WINDOW_CHECK.md` (window carried the tree) vs `strategy/WITHHELD.md:444–445` (404 at every historical ref). The 3-attempt stop rule applied: the authority files were read this unit but the extracted copies were released before a re-measure, and the remaining call bound could not re-open them. **Do not guess** — the applying unit must re-read `strategy/ARCHIVE_WINDOW_CHECK.md` and, if needed, `strategy/DISCLOSURE_INVENTORY.md` §P10. |
| U-2 | Whether `tools/gated-read/bench.py` is M13-protected core inventory or a separable research harness releasable after re-implementation | Classified `withhold`-as-artifact + releasable-as-neutral-protocol by reading `strategy/WITHHELD.md:109`, `:340` literally (`tools/**` is M13). Whether the batching note needs *any* harness to ship is a release-set decision, not a disclosure one. |
| U-3 | Whether vendor model ids (`deepseek-v4-flash`, `deepseek-v4.1-flash`, `mimo-v2.6-flash`) are neutralised or plain-publishable | Third-party public names, not project identifiers; the code-agnostic rule as recorded tags every proper name. No authority read this unit decides it. Conservative default applied: `neutralise`. |
| U-4 | Whether the four-plus corpus directory names are "project-level detail" (M12-ish) or generic | They name a private tree's top-level layout; no rule read this unit addresses directory names as such. Conservative default applied: `neutralise` (`[CORPUS-n]`). |
| U-5 | Exact line anchors inside `strategy/ARCHIVE_WINDOW_CHECK.md`, `strategy/DISCLOSURE_INVENTORY.md`, `strategy/PRIOR_DISCLOSURE_AUDIT.md` | Read this unit before context compression; the temp extraction was released. Every claim used from them here is at **file level**, and is labelled as such — no line number is invented. |

---

## 7. The minimal set of elements that must be replaced by generic tags

If (and only if) these are tagged, candidate #7's publishable scope — the batching note of
`strategy/PAPER_CANDIDATES.md:1088–1089` — becomes publishable with **no** construction disclosure:

1. **All private-tree path names and filenames** — `[HARNESS-1]`, `[FIXTURE-1]`, `[ROWS-1]`, `[SUMMARY-1]`,
   `[DOC-1..3]`, all `tools/**` and `docs/research/**` paths, all `src/**` paths (`tokens 1,2,3,4,5,6,10,11` of §1).
2. **All internal role/mode/arm identifiers** — `[ROLE-n]`, `[MODE-n]`, `[ARM-n]`, `[EXTRACT-n]`, `[EXPERIMENT-1]`,
   `[RUN-1]`, `[TASK-n]` (N-01, N-02, N-03, X-05, X-06, R-11).
3. **All construction constants** — `[CONST-*]` (P-04…P-12, P-15, Q-10).
4. **The corpus root names** — `[CORPUS-n]` (X-07).
5. **Payload tokens and model ids** — `[PAYLOAD-1..2]`, `[MODEL-1..2]`, `[RUNTIME-1]` (N-05, N-07).
6. **The project/product family name** — `[FAMILY]` (not named in the candidate-#7 mechanism itself, but the
   paper's affiliation/availability statement will name it).

Everything else **publishes as-is**: the phenomenon (gate weakness, batching nearly free, routing degrades to
grep), the treatment levels 1/16/90 and none/minimal, the metric definitions, all result numbers (Q-02–Q-09),
the injection protocol, the gold-label rule, the anti-leak constraint, and the related-work framing.

---

## 8. Record defects found (reported, not fixed)

1. `strategy/PAPER_CANDIDATES.md:537` says staged extraction "reaches the best arm's accuracy at **1/14** the
   context"; `:547` and `docs/research/GATED_READ_2026.md:215` say **15.3×** (21 872 / 1 432), and the errata
   (`GATED_READ_2026.md:203–207`) already corrected 15.6× → 15.3×. 1/14 matches no measured pair. **Fix:** use
   the re-derived 15.3× and delete the 1/14 wording.
2. `strategy/PAPER_CANDIDATES.md:536–538` ("reaches the best arm's accuracy") is contradicted by
   `docs/research/GATED_READ_2026.md:194–201`: `stage_route` 0.55 < `selfselect`/`gate_min` 0.65. `:548` hedges
   this as "inside the noise band"; the title-level claim does not. **Fix:** state the band explicitly or drop it.
3. `docs/research/GATED_READ_2026.md:250` headline says exposure **0/20** while R5's own union column reads
   **0** only for `stage_route` — consistent, but `:203` errata shows the union was wrong once. **Fix:** ship
   the re-derived table, and mark the two-payload ASR as a lower bound (`:257`).
4. **AD-6 conflict** (`strategy/WITHHELD.md:444–445` vs `strategy/ARCHIVE_WINDOW_CHECK.md`): the 404 check
   probed `consonance/src/journal.ts` and `src/journal.ts`. If the public mirror maps the target's `src/**` to
   `consonance/**`, the probed paths do not exist in *either* tree and the 404 is uninformative — which would
   mean the implementation **was** public in the window. **Fix:** re-run the 404 probe against the correct
   mirror path (e.g. `consonance/journal.ts`), and reconcile §8.9/§8.3 with the window record.
5. `strategy/PAPER_CANDIDATES.md:544` "prompt tokens 2.4×" vs `:546`/`GATED_READ_2026.md:151` "2.3×" for
   bs16 — both appear; the table's own figure is 2.3×. **Fix:** quote the table.

---

## 9. Handoff notes

- **Report only.** No paper text, no rename, no redaction, no package, no build was produced or touched;
  `papers/gated-read-batching/**` (CLAIMS.md 12 245 B, DISCLOSURE_CHANGES.md 39 448 B, GAPS.md 14 234 B,
  MANUSCRIPT.md 32 002 B, REFS.md 8 827 B) was **not** read for prose and **not** modified.
- **Applying unit must decide first:** (i) U-1 (window vs 404), because it moves §1 items 4–5 and X-08; (ii) the
  scope split — batching note only (recommended, `strategy/PAPER_CANDIDATES.md:1088–1089`) versus full title.
- **Do not re-derive R5 before fixing defect 1–3**; the title numbers depend on them.
- The withhold list (§1) is the checklist to run against every sentence *before* drafting, per the
  m00703/m01523 standing instruction.
