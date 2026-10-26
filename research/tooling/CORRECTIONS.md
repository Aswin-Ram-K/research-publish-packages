# Corrections — verifier V1 against the published research set

**Unit:** S5 (correction, post-verification) · **Date:** 2026-10-23 · **Repo:** `/home/zer0null/reserach extarctor`
**Verifier of record:** `research/tooling/handoffs/V1.json` — verdict `partial`: **12 reproduced, 6 contradicted**, plus 5 items raised by the main session afterwards (C7–C11: four record-accuracy fixes and one correction to *my own* first-pass fix).

**This file supersedes the clauses it names, and nothing else.** `01-inventory.md` and `02-candidates.md` remain the record and are **not rewritten** — the only change to them is the errata section appended at the end of `01-inventory.md` (`## §7 Errata`). `FINDINGS.md` carries targeted edits, each marked `(corrected by V1 — see CORRECTIONS.md C#)`. The recommendation table (§4) keeps its shape: the corrections change **cost and wording**, and in one case (C1) the *kind* of work, but not a single ADD/EVALUATE/REJECT verdict.

**Every entry was re-verified in this session** against disk, source, or the plugin package — V1 was not taken on faith. Where I could not re-run V1's exact command I say so; where my line numbers differ from V1's by one or two lines, mine are the measured ones.

**Reading an entry:** claim as published → what is true → proof → which document carried it → effect on the recommendation.

---

## C1 — G5: incremental re-index is wired and disabled, not absent

**Claim as published.** `01-inventory.md:28` (§1 row 14, "Incremental graph re-index after commits") says *"**nothing** … no `graphify update`/`watch` call exists in `src/` (grep)"*, status `absent`; §2b row `update` says *"no … grep `\.update(` in `src/` → 0 graphify calls"*; G5 (`01-inventory.md:138-139`) repeats *"no `graphify update`/`watch` call exists"*. `FINDINGS.md` §0 bullet 1 then listed "incremental refresh ✓ … none connected".

**What is actually true.** The refresh engine has a complete, wired copy-then-update path:

| `path:line` | what it is |
|---|---|
| `src/resextract/refresh/review.py:416` | `def _run_graphify_update(copy_dir: Path, *, timeout: float) -> tuple[bool, int, str]:` |
| `src/resextract/refresh/review.py:431` | `argv = ["stdbuf", "-oL", "-eL", os.fspath(binary), "update", os.fspath(copy_dir)]` |
| `src/resextract/refresh/review.py:433` | `proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)` |
| `src/resextract/refresh/review.py:628` | `ok, rc, tail = _run_graphify_update(copy_root, timeout=timeout)` (guarded by `elif run_update:`) |
| `src/resextract/refresh/review.py:861` | `run_graph_update: bool = True` — the default |
| `src/resextract/refresh/review.py:904` | `run_update=run_graph_update` — passed into the update pass |
| `src/resextract/run.py:1781` | `run_graph_update=False` — **the only** caller that disables it |

The update runs against a **staged copy**, not the target: `_stage_repo_copy` (`review.py:443`) copies the tree to `copy_root = root / "repo"` (`:521`), `_place_graph` (`:476`) puts the preserved graph into the copy, and the resulting record reports both `copy_sha256` and `original_unchanged` — i.e. the engine is explicitly built so the source `state/kg` graph and the target are untouched.

So the true statement is: **the pipeline has a wired, copy-then-update re-index, disabled at one call site** — not an absent one. Residual gap, and it is smaller than "build incremental refresh": the refreshed graph lives in the staged copy and is not adopted back into `state/kg/<slug>/` in the same run.

**Proof.** The commands in the table above (`sed -n '410,440p'`, `grep -n 'argv = \["stdbuf"'`, `sed -n '855,868p'` on `refresh/review.py`; `sed -n '1775,1790p'` on `run.py`). My grep of `_run_graphify_update|run_graph_update` over `src/` returns exactly those seven lines and nothing else.

**Why S1 and my own summary got it wrong — the methodological lesson.** The invocation is a **literal CLI argv list**, not a `Graphify.update(...)` method call. The grep that the inventory was built on — `\.update(` — can only see method calls, so it returned 0, and the doc's own conclusion hardened around that zero. The helper's docstring (`review.py:417-426`) even says *"this module never calls `Graphify.update` at all"*: that sentence is **true**, and it is precisely why the method-call grep missed the subcommand — the subcommand name lives inside a list of strings, one level below the wrapper. An inventory built on method-call greps is blind to direct argv construction, and a wrapper existing (`kg/graphify.py:1245 def update`, `:1607 def watch`) says nothing about whether the binary is invoked.

**Carried by.** `01-inventory.md` §1 row 14, §2b row `update`, G5; `FINDINGS.md` §0 bullet 1, §2a "incremental currency", §4d; `README.md` index row for S1.

**Effect on the recommendation.** P0-d changes **kind**: from "build incremental refresh" (M, new plumbing) to "**enable and verify what already exists**" (S — one default at `run.py:1781`, or thread it, then prove it on one refresh). The read-only rule is satisfied **by construction**: the update runs on `<state_root>/refresh/<slug>/repo`, never on the target.

**But "just flip the flag" is wrong advice, and the disabling is deliberate** — see **C11**. `run.py:1768-1771` states the reason in the same function: *"graph update off — a graph update would copy the target into the workspace"*. `_stage_repo_copy` copies the **whole target tree**; the refresh engine's default is on (`review.py:861`) precisely so that a caller who can afford the copy gets the update, and this caller says it cannot. The fix is therefore **make the copy cheap, then enable** — bounded to the admitted set — not "enable and hope". Residual work after that: adopting the copy's refreshed graph back into `state/kg/`.

---

## C2 — "2 of 28 subcommands" → 3 of ~27 families, ≈89% unused

**Claim as published.** `FINDINGS.md` §0 bullet 1 and §2, `README.md` row, `handoffs/S1.json`: *"the pipeline invokes 2 of its 28 subcommands"*, *"≈93% of the installed surface is dark"*.

**What is actually true.** Three command **families** are invoked:

| family | call site |
|---|---|
| `extract` | `src/resextract/run.py:1357` `result = gf.extract(...)` |
| `query` | `src/resextract/mine/candidates.py:920` `result = self._graphify.query(question, graph=..., budget=...)` |
| `update` | `src/resextract/refresh/review.py:431` (literal argv, see C1) |

The denominator is neither 28 nor 46. `.venv/bin/graphify --help` is a hand-written `Commands:` list; it presents **27 command families** (`install, uninstall, path, explain, diagnose, clone, merge-driver, merge-graphs, add, watch, update, cluster-only, label, query, affected, god-nodes, prs, save-result, reflect, check-update, tree, extract, provider, global, benchmark, export, hook`), and **46 distinct top-level names** once the 19 per-platform install aliases are counted (`install`'s own description lists `claude|windows|codebuddy|codex|opencode|aider|amp|agents|claw|droid|trae|trae-cn|gemini|cursor|antigravity|hermes|kiro|pi|devin`, and each alias also appears as its own help entry).

Correct phrasing: **"3 of ~27 families — roughly 89% unused"**, and the denominator is a **help-text family count, not a spec** — the number moves when graphify adds or groups commands, so it must be re-counted, not quoted, after an upgrade.

**Proof.** `.venv/bin/python -` parsing `.venv/bin/graphify --help`: 46 unique top-level names, 27 after removing the 19 aliases; families enumerated above. Call sites from `grep -rn "_run_graphify_update\|gf\.extract\|_graphify\.query\|run_graph_update" src/ --include=*.py`.

**Carried by.** `FINDINGS.md` §0 bullet 1, §2, §2a table header ("the unused 20"), `README.md` index row; `handoffs/S1.json`.

**Effect on the recommendation.** No verdict changes. It corrects the headline and one table row: `update` moves from "unused, would buy incremental currency" to "wired but disabled" (C1). The substantive claim — that most of the installed surface is never reached — survives at 89%.

---

## C3 — `context/budget.py` is not "imported by tests only"

**Claim as published.** `01-inventory.md:24` (§1 row 10): *"**imported only by tests** (`tests/test_context_*.py`)"*; `FINDINGS.md` §5: *"imported by tests only"*; G8: *"`context/budget.py`'s compaction is test-only"*.

**What is actually true.** No `src/` module imports it (the one `src/` hit is a docstring reference, `src/resextract/context/render.py:44`). Importers are:

- `tests/test_context_append_note.py:43` — `from resextract.context.budget import is_append_note, note_nodes`
- `experiments/context-cache/cells/U5/u5_cells.py:57` — `from resextract.context.budget import default_est_tokens`
- `experiments/context-cache/cells/U14/u14_append_note_probe.py:49` — `from resextract.context.budget import is_append_note`

Correct phrasing: **"no `src/` importer; imported by tests and by the context-cache experiments."**

**Proof.** `grep -rnE "context\.budget|from resextract\.context import budget" src/ tests/ experiments/ --include=*.py` → the four lines above.

**Carried by.** `01-inventory.md` §1 row 10, G8; `FINDINGS.md` §5 "Honest note on budget".

**Effect on the recommendation.** None of substance — the point the sentence exists to make (the module named `budget` does not govern the live prompt; the live limits are `QUERY_BUDGET=700` and the 60/40 menu caps) is unchanged. The error was over-claiming the *evidence* for a true conclusion, which is why it is corrected rather than argued.

---

## C4 — S2's "436-file Python target" is wrong twice

**Claim as published.** `02-candidates.md:18,21,25,26,49,57,59,77,83,91` and `handoffs/S2.json:12,27`: *"436 files"*, *"436-file Python target"*, *"436 Python files"* — used as the sizing premise for the zoekt / Sourcebot / Sourcegraph / CodeQL / SCIP / Joern verdicts.

**What is actually true.** The admitted build is **227 files**: `state/kg/duval/graphify-out/manifest.json` has 227 keys, and its extension mix is `.ts` 135 / `.json` 59 / `.mjs` 13 / `.py` 9 / `.sh` 8 (3 with no extension). The graph's own `source_file` values — 175 distinct files — are `.ts` 136 / `.mjs` 13 / `.py` 9 / `.sh` 8 / `.json` 3 / 6 extensionless. The target is **TypeScript-dominant**; it is not a Python target.

**Proof.** `python -c` over `state/kg/duval/graphify-out/manifest.json` (227 entries, mix above) and over `graph.json` `source_file` values (175 distinct, mix above). `state/logs/U8.12-prefix-copy.md:176` independently records `227/227 AST progress lines`.

**Carried by.** `02-candidates.md` (nine sentences), `handoffs/S2.json`; half-caught in `FINDINGS.md` §7.6 as an open question.

**Effect on the recommendation.** **No verdict flips** — zoekt, Sourcebot, Sourcegraph and CodeQL are REJECT at 227 files or 436, and the licence-key argument is independent of size. But every sizing sentence must cite **227 and the TS-dominant mix**; "Python target" is simply false, and a reader who knows the target would have doubted every later judgement because of it. The tree-sitter-adequacy argument (why SCIP/Joern are not yet worth it) gets *stronger* at 227 files.

---

## C5 — Sourcegraph "API 404" is not evidence about the repo

**Claim as published.** `02-candidates.md:25`: *"repo not publicly retrievable (API 404 on 2026-10-23)"*; `:107`: *"`<https://github.com/sourcegraph/sourcegraph>` returns 404 via the API (2026-10-23)."*

**What is actually true.** S2's own handoff (`handoffs/S2.json:40`) records: *"GitHub API rate limit (60/hr unauthenticated) was exhausted; counts for sourcegraph/sourcegraph and sourcegraph/sourcegraph-public are therefore recorded as 404/no-public-repo rather than as a star count."* The 404 was a **fallback label applied after rate-limit exhaustion**, not an observed response about the repository. A rate-limited unauthenticated call normally yields 403, so even the status code is suspect.

Downgrade to: **"unconfirmed — the unauthenticated GitHub API was rate-limited in this run; no public-repo metadata was retrievable."**

**Proof.** `grep -n -i "rate limit\|404" research/tooling/handoffs/S2.json` → `:40` as quoted; `02-candidates.md:25,107` as quoted.

**Carried by.** `02-candidates.md` §table row, prose §6, sources; `FINDINGS.md` §6 bullet (which repeats the licence-key half, which *is* sourced).

**Effect on the recommendation.** None — the verdict (REJECT) rests on the enterprise licence key, which is separately sourced (`sourcegraph.com/docs/admin/licensing`) and not on the 404. The correction is about the *kind* of evidence being presented: a rate-limit fallback recorded as an observation is the defect, and no prose may present it as an API fact.

---

## C6 — plugin registration does not work as shipped; promotion is a code change

**Claim as published.** `01-inventory.md:111-120`: registration via `ctx.tools.register(defineTool({...}))` with a "promotion blockers" list of two (package outside the workspace; profile write + restart). `FINDINGS.md` §2b: *"Whether registration works on this harness build … is **unverified either way** — not assumed broken … a fallback path may well carry it"*; §7.5 repeats that.

**What is actually true.** It fails as shipped, for two independent reasons:

1. **The contract rejects the definitions.** `register()` (`/home/zer0null/deepseek-harness/packages/core/tools/src/index.ts:1071`) accepts a plain object, but requires `output.render` to be a **function** and throws otherwise (`:1077`):
   ```
   throw new TypeError(`tool "${name}" must declare output { schema, render, presentationMeta? }`)
   ```
   The plugin's five `output:` blocks (`lib/index.js:173,256,339,417,491`) are **JSON schemas themselves** (`output: { type: 'object', additionalProperties: false, properties: {…} }`) — `grep 'render\|schema' lib/index.js` returns **0 hits**, so the key the registry looks for is absent and the key it does find is in the wrong place.
2. **The import resolves to a local shim.** The package ships `node_modules/@deepseek-ai/dsh-tools` — `"version": "0.0.0-shim"`, description *"Offline shim of the harness defineTool contract for unit testing … NOT used by the live harness"*, a 7-line `defineTool(def) { return def }`. The `await import('@deepseek-ai/dsh-tools')` at `lib/index.js:28` therefore **succeeds** and binds the shim, so the `catch` fallback is never reached and `register()` receives exactly the invalid definition.

The working comparator is the mounted `@local/dsh-plugin-openui` (`/home/zer0null/dsh-plugins/@local/dsh-plugin-openui/lib/index.js:201-203`):
```
output: {
  schema: { type: 'string' },
  render(_args, value) { return [{ type: 'text', text: String(value) }] },
```

**Proof.** `sed -n '1065,1085p' packages/core/tools/src/index.ts`; `grep -n 'output:' plugin/lib/index.js` → the five lines; `grep -n 'render\|schema' plugin/lib/index.js` → 0; `cat plugin/node_modules/@deepseek-ai/dsh-tools/{package.json,index.js}`; `sed -n '196,208p'` on the openui plugin.

**Carried by.** `01-inventory.md` §3 (promotion blockers), `FINDINGS.md` §2b, §3 plugin row, §4c, §7.5.

**Effect on the recommendation.** P0-c grows from a config flip to a **code change + config change + approval**: (i) rewrite five `output` blocks to `{ schema, render [, presentationMeta] }`; (ii) delete or stop resolving the local shim so the real `defineTool` contract applies; (iii) the graph-path/auto-ensure patch (§4c condition i); (iv) the `link:` + `cordis.patch.yml` row + restart. The "validate in a throwaway profile first" step survives but now has a *predicted* failure, which makes it a test of the patch instead of a coin flip. The tool's value is unchanged; its cost is not.

---

## C7 — S1's recorded evidence commands are not the commands that produced the findings

**Claim as published.** `handoffs/S1.json` `evidence.commands` entries 5, 7 and 12, e.g. `grep -rn 'leiden|graphifyignore' …` and `grep -rn '\.query(|\.affected(|…' src/ --include=*.py`.

**What is actually true.** Those strings are **BRE alternations without `-E`**, so `|` is a literal character and each pattern matches nothing. V1 re-ran them with `-E` and got 25 and 12 lines respectively. The *findings* are right; the *recorded commands* cannot have produced them. The fix is `-E` (or `grep -rnE`), and the reason it matters is that a later unit copies the `commands` array and will read 0 hits as "the claim no longer holds".

**Proof.** `python -c` printing `handoffs/S1.json` `evidence.commands` — the three entries are stored without `-E`. I verified the recorded strings, **not** the 25/12 counts, which are V1's.

**Carried by.** `handoffs/S1.json` only (S1's handoff is not in this unit's write path, so the correction is recorded here rather than edited — see "not edited" below). `01-inventory.md` §7 errata carries the lesson.

**Effect on the recommendation.** None — record hygiene. It does not change a single conclusion; it changes whether those conclusions can be re-derived by copying the handoff.

---

## C8 — `graphify_version` is nested, not top-level

**Claim as published.** `01-inventory.md:4-7`: *"`directed=false`, **`graphify_version=0.9.80`**, `built_at_commit=…`"* — listed as a peer of two top-level keys.

**What is actually true.** `json['graphify_version']` is `None`; the value lives at **`json['graph']['graphify_version']`** (`0.9.80`), beside `json['graph']['schema_version'] = 1`. The value is correct; the field path is not.

**Proof.** `python -c` over `state/kg/duval/graphify-out/graph.json`: top-level `None`, `['graph']['graphify_version'] == '0.9.80'`.

**Carried by.** `01-inventory.md` header; `FINDINGS.md` §8 artifact constants (which asserts `graphify_version=0.9.80` without a path — correct value, ambiguous location).

**Effect on the recommendation.** None — record accuracy only. A future reader scripting against the artifact would read `None` and conclude the graph predates the field.

---

## C9 — the plugin has a third promotion blocker: its definitions are not registry-ready

**Claim as published.** `01-inventory.md:117-120`: *"Promotion blockers, both concrete"* — (a) package outside the workspace, (b) profile write + restart.

**What is actually true.** There is a third, and it is the first one a promotion would hit: the five tool definitions are **not registry-ready** under the harness contract — `register()` requires `output: { schema, render }` and throws `TypeError: tool "<name>" must declare output { schema, render, presentationMeta? }` at `packages/core/tools/src/index.ts:1077` (full mechanism in **C6**), while the plugin's blocks carry neither key.

**Proof.** As C6.

**Carried by.** `01-inventory.md` §3 blocker list; `FINDINGS.md` §4c "Three conditions".

**Effect on the recommendation.** Adds a code change to P0-c (C6's effect); no verdict change. Listed separately because the blocker list is the operative checklist a promotion unit will follow, and an incomplete list is what caused the "unverified either way" hedge in the first place.

---

## C10 — row 13 is measured, not inferred

**Claim as published.** `01-inventory.md:27` (§1 row 13, rework backlog): *"driven from `refresh_target` **[inference: re-export implies use]**"*.

**What is actually true.** Measured: `src/resextract/refresh/review.py:945` — `entries = rework_entries(manifest, change, docket_links, now=now_dt)`. The rework backlog is driven from the refresh engine, so the row's `runtime` status is established rather than inferred.

**Proof.** `sed -n '938,950p' src/resextract/refresh/review.py` — the call is at `:945`, inside the refresh pass, and its `entries` are extended into `all_entries`.

**Carried by.** `01-inventory.md` §1 row 13, §5 bullet 1 ("Whether `refresh_target` calls `backlog.rework_entries` … the call graph was not traced").

**Effect on the recommendation.** None — it closes an open item and strengthens P0-d's context (a rework backlog already maps changes to entries; what it lacks is a mapping to a re-extraction command, which is what C1's enabled path supplies).

---

## C11 — the disabled update is a deliberate, stated tradeoff, and the copy is the cost

**Claim as corrected by C1 (my own first pass).** C1 correctly established that the engine exists and defaults on, but its first version read the `run.py:1781` flag as an oversight and recommended flipping it. That is wrong: the flag has a **stated reason at the call site**.

**What is actually true.** `src/resextract/run.py:1768-1771` (the refresh stage's own reason string) says: *"graph update off — a graph update would copy the target into the workspace"*. And `refresh_target` defaults the other way — `refresh/review.py:861` `run_graph_update: bool = True`, threaded at `:904` as `run_update=run_graph_update` — so the engine is *built* for the update and the one caller opts out for a cost reason, not a correctness reason.

The cost, measured: a full `_stage_repo_copy` (`review.py:443`) copies the target tree minus `node_modules`/`.worktrees`; the target is **166,314 files**, of which only **227** are admitted by the graph predicate, totalling **5,390,460 B = 5.39 MB** against `/home/zer0null/Duval` (227 present, 0 missing).

So the pipeline currently declines to copy ~166k files (and 18,624 `.md`) in order to re-index 5.39 MB.

**Proof.** `sed -n '1760,1782p' src/resextract/run.py`; `sed -n '855,868p'` and `:904` on `refresh/review.py`; `sed -n '443,455p'` on `_stage_repo_copy`; `python -c` summing `os.path.getsize` over every `manifest.json` key against `/home/zer0null/Duval` → 227 keys, 0 missing, 5,390,460 bytes.

**Carried by.** `FINDINGS.md` §4d (condition added); C1 above (effect paragraph).

**Effect on the recommendation.** P0-d's fix is now **"make the copy cheap, then enable"**, and it must state the bound:

- **Either** stage only the admitted set — the same 227 files that `config/targets.toml:14-52` + graphify's predicate already define — so `_stage_repo_copy` copies 5.39 MB instead of the whole tree, then run `graphify update` on that copy (the update is already written and defaults on);
- **or** leave `refresh` off and take incrementality from `graphify extract <target> --out state/kg/<slug>` — verified incremental via `manifest.detect_incremental`, and it writes only under `state/kg/`.

Either way the success test is unchanged: *refresh after a target commit produces a graph stamped with the new commit, without copying 166k files to re-index 5.39 MB.* The correction is meant to make the item **cheaper and safer**, not to swap one wrong claim for another; a plan that says "flip the flag" would trade a disabled feature for a 166k-file copy into the workspace.

---

## What this file does **not** change

Every number V1 reproduced is left exactly as published, and I re-verified each on 2026-10-23 before leaving it alone:

- graph artifact **3,188,231 B**; **2,685 nodes / 7,102 links**; `directed=false`; `built_at_commit=6deaed07af0d998d1672fe3f1ab1579e6ba0cdc4`
- sha256 `4790bbb1111b76ea7cfb8024a98cfb3ec8c4b038beb23f6e5b6fa729fcdd897b` == `config/graph_pin.toml:52`
- `MENU_NODE_LIMIT = 60`, `MENU_EDGE_LIMIT = 40` (`mine/candidates.py:125-126`), `QUERY_BUDGET = 700` (`:105`)
- graphifyy 0.9.80 Apache-2.0; ast-grep-py 0.51.0 cp314 wheel; ripgrep 15.2.0; the ADD/EVALUATE/REJECT verdicts; the 227-file manifest (C4)
- the containment finding: nothing under `src/`, `config/`, `docs/`, `tests/`, and no write inside `/home/zer0null/Duval`

## What was not edited, and why

`handoffs/S1.json` carries C7's defective `commands` array and `02-candidates.md` carries C4/C5, but neither file is in this unit's write path. Editing a prior unit's handoff would also make the verifier's evidence disagree with the record it verified. The errata section appended to `01-inventory.md` names both, which is the mechanism this directory uses: **append and mark, do not rewrite.**
