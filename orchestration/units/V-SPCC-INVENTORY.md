# V-SPCC-INVENTORY — plan-vs-disk scorecard

Read-only audit of the executed Serving × Context programme. Every verdict below is
backed by a command pasted in this card. Nothing was restarted, no POST issued, no
file outside this card and its handoff written.

## Table

| # | Deliverable | Path (real) | Exists | Evidence (one line) | Verdict |
|---|---|---|---|---|---|
| 0 | Preservation commit + both merges pushed | git history | yes | `17182ff backup: screened serving WIP (unverified)` is pushed — `git branch -r --contains HEAD` → `origin/backup/screened-dirty-progress-2026-11-10-1348`; but `origin_main=5554d82 head=17182ff mergebase=5554d82`, i.e. **origin/main never advanced**; `git status --porcelain \| wc -l` = 108 | **partial** — preservation commit pushed to a backup branch; **neither merge is in main** |
| 1 | Findings ledger | `experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` | yes | 3291 B / 27 L; 7 finding rows, each with named source + line (`RESULTS-TX02-CELL1.md` line 20, `RESULTS-STACK-8014.md` line 24/38/62), status column VERIFIED, plus an "Open questions" section | **proven** (content, not just existence) |
| 2 | Stable-prefix compiler | `experiments/ptr-engine/ptr_engine/layers.py` | yes | 10393 B / 295 L; `:19 class PtrPrefixDrift`, `:31 class CompactionState`, `:151 escape_journal_content`, `:155 format_journal_line`, `:159 def compile_prompt(run, state, *, epoch, journal, work)` | **proven** |
| 3 | Prompt engine format spec | `experiments/ptr-engine/research-seed-concepts/PROMPT-ENGINE-V1.md` | yes | 4109 B / 71 L; sections `## Layers (byte-stable from the front)`, `## Line formats`, `## Epoch / compaction rule`, `## Answer contract` | **proven** |
| 4a | Serving launch script | `experiments/ptr-engine/serving/launch-sglang-spcc.sh` | yes | 2065 B / 63 L; `:54  --enable-hierarchical-cache`, `:41 --mamba-radix-cache-strategy extra_buffer`, `:26 sglang serve`; header `:5 adds --enable-hierarchical-cache (host-memory tier; was false live)` | **proven** on disk; **not applied live** (see Blocked / item 7) |
| 4b | Fork decision | `docs/serving-options/FORK-DECISION.md` | yes | 1592 B / 34 L; `## Fork gate (all three must hold, each demonstrated by a failing run)`, `## Rule if a gap is demonstrated` | **proven** |
| 5a | Remote model programme | `experiments/ptr-engine/serving/REMOTE-ROOT.md` | yes | 1241 B / 32 L; `# Remote writes — BLOCKED by default`, `## Current status`, `## Proposed root (proposal only — not authorised)`, `## Authorisation (verbatim)` | **proven** (as a refusal document) |
| 5b | Memory-window supervisor | `experiments/ptr-engine/serving/spcc_supervisor.py` | yes | 25412 B / 686 L; decision chain at `:562-584`: `allowance = "UNVERIFIED"` then killed/aborted/signal/peak-unknown/peak-exceeded/unaccounted-unknown/unaccounted-negative branches, `else: allowance = "VERIFIED"` — VERIFIED is the else-branch, i.e. the last resort | **proven** |
| 5c | Memory-window schema | `experiments/ptr-engine/serving/MEM-WINDOW.schema.md` | yes | 6960 B / 122 L; `## Invariants`, `## Open record`, `## Allowance decision table`, `## Refusal messages` | **proven** |
| 6 | Pre-registration | `experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md` | yes | 6580 B / 98 L; `## Budget reconciliation (ledger authority)`, E1 stable-prefix-vs-masking, E2 compaction cost, E3 distance cliff, E4 which model holds format, E5 host tier pays for itself | **proven** |
| 7a | Billed accounting | `experiments/ptr-engine/longrun/score_longrun.py` | yes | `:132 def billing_block`, docstring `Null cached_tokens are excluded (never counted as 0) for cached_fraction and coverage`, `:156 coverage`, `:170 cached_fraction`, `:177-178` emitted; wired at `:1078` and `:1291` | **proven** |
| 7b | One-answer-per-checkpoint guard | `experiments/ptr-engine/longrun/score_longrun.py` | yes | `:978 # fail loudly on duplicated non-interim answers for the same checkpoint id` … `:985 msg = "duplicate non-interim checkpoint answers: "` then `raise ValueError(msg)` | **proven** |
| 7c | Ledger reconcile | **`experiments/ptr-engine/tools/request_ledger.py`** | yes | `:796 def reconcile(paths=None, pattern=None, cap=DEFAULT_CAP, reserve=DEFAULT_RESERVE,` — **the plan's path `tools/request_ledger.py` does not exist** | **proven, wrong path** |
| — | Repo state note | `docs/CURRENT-REPO-STATE.md` | yes | 1082 B / 17 L, but its text is **stale and now false**: it asserts `HEAD: dfba6aa` and "`origin/main`: … Shares no common ancestor with this branch"; today `head=17182ff` and `mergebase=5554d82`, i.e. origin/main *is* an ancestor (grafted by the `--allow-unrelated-histories` merge it describes) | **partial** |
| — | `spcc` arm wired to the compiler | `experiments/ptr-engine/longrun/arm_cd.py` | yes | `:29 from ptr_engine.layers import (` / `:30 compile_prompt, …`; `:37 ARM_SPCC = "spcc"`; `:490 prompt = compile_prompt(self.run, self.state, epoch=…, journal=new_lines, work=l3)`; **reimplementation check**: `grep -c "^def compile_prompt\|^    def compile_prompt"` → `0` | **proven** — real call, no local copy |
| — | Arm dispatch + stamping | `experiments/ptr-engine/longrun/run_longrun.py` | yes | 211978 B / 4022 L; `:73 ARMS = (…, "spcc")`, `:1399 self.spcc = arm_cd.SpccArmState(fixture=fixture)`, `:1534 if arm == arm_cd.ARM_SPCC:`, stamps `:1502/:1546 info["prefix_sha256"]`, `:1549 info["layer_tokens"]`, `:2632 cached_tokens_normalized`, `:2700/:2703` emitted per turn | **proven** |
| — | Unit reports this session | `orchestration/handoffs/U-SPCC-*.json`, `V-SPCC-*.json` | yes | 23 SPCC handoffs (Nov 9 06:57 → 08:50); 21 carry pasted output, 2 carry prose only (`U-SPCC-5`, `U-SPCC-23`) | **proven with 2 exceptions** |

## Handoff evidence table (session scope)

| File | unit | status | evidence quality |
|---|---|---|---|
| U-SPCC-0 | U-SPCC-0 | done | pasted (`starting_branch`, `starting_status_count`, `starting_status_breakdown`) |
| V-SPCC-0 | V-SPCC-0 | done | pasted (`log_head`, `status_porcelain_lines`, `head`, `origin_head`) |
| U-SPCC-0B | U-SPCC-0B | done | pasted (`git_log`, `status_count`, `roots`, `row_tallies`) |
| U-SPCC-1 | U-SPCC-1 | done | pasted (`wc_l`, `grep_VERIFIED`, `table`) |
| V-SPCC-1 | V-SPCC-1 | complete | pasted (`grep_verified`, `grep_unverified`, `rows`) |
| U-SPCC-4 | U-SPCC-4 | done | pasted (`bash_n`, `dry_run`, `mem_window_refusal`) |
| U-SPCC-4B | U-SPCC-4B | done | pasted (`grep`, `bash_n`, `dry_run`) |
| U-SPCC-5 | U-SPCC-5 | done | **prose only** — `evidence` = `{tests}`, no pasted output |
| V-SPCC-5 | V-SPCC-5 | done | pasted (`author_tests`, `open_window_61`, `memavailable_low`) |
| U-SPCC-5B | U-SPCC-5B | done | pasted (`acceptance_pytest`, `collected`, `normal_run`) |
| V-SPCC-5B | V-SPCC-5B | done | pasted (`suite`, `check2_window_removal`, `check3_kill_path`) |
| U-SPCC-5C | U-SPCC-5C | complete | pasted (`test_command`, `test_result`, `new_tests`) |
| V-SPCC-5C | V-SPCC-5C | done | pasted (`check1_suite`, `check2_decision_table`, `check2_driven`) |
| U-SPCC-5D | U-SPCC-5D | COMPLETE | pasted (`red_before_branch`, `green_full_suite`, `final_chain`) |
| U-SPCC-6 | U-SPCC-6 | done | pasted (`budget_output`, `hypothesis_E1..E3`) |
| U-SPCC-7 | U-SPCC-7 | done | pasted (`tests`, `reproduce`, `reconcile`) |
| U-SPCC-8 | U-SPCC-8 | **partial** | pasted (`verdict_before`, `verdict_after`, `verdict_red_green`) |
| U-SPCC-9A | U-SPCC-9A | done | pasted (`class_b_root_cause`, `class_b_before_after`) |
| U-SPCC-9B | U-SPCC-9B | complete | pasted (`stop_reason`, `verbosity`, `false_pass`, `lost_fixture`) |
| U-SPCC-9C | U-SPCC-9C | complete | pasted (`four_file_before`, `three_suites_after`, `build_fixture_check`) |
| U-SPCC-2C | U-SPCC-2C | done | pasted (`pytest_spcc`, `grep_compile_prompt_arm_cd`) |
| V-SPCC-23 | V-SPCC-23 | done | pasted (`author_tests`, `determinism`, `drift`, `prefix_stability`) |
| U-SPCC-23 | U-SPCC-23 | done | **prose only** — `evidence` = `{pytest, direct_run, commands}`, no pasted output |

Independent spot-check of the load-bearing arm claim: `U-SPCC-2C`'s
`grep_compile_prompt_arm_cd` agrees with what this audit re-ran
(`arm_cd.py:490`, zero local `def compile_prompt`). That unit's evidence is corroborated.

## Test counts

`timeout-plugin: no` — `pytest-timeout` is not installed, so `--timeout=120` was unavailable.

| File | Result |
|---|---|
| `test_matrix_audit.py` | **17 passed** in 0.55s |
| `test_build_fixture.py` | **5 passed** in 0.44s |
| `test_regrade_stamp.py` | **6 passed** in 0.34s |
| `test_lost_fixture.py` | **does not complete** — killed at 150s (`timeout 150`) |
| `test_journal_lint.py` | **1 failed, 13 passed** in 0.14s |
| `test_verdict_ritual.py` | **10 passed** in 0.05s |
| `test_request_ledger.py` | **1 failed, 15 passed** in 0.68s |

The whole `experiments/ptr-engine/longrun/tests/` directory (99 test files) was started
at 06:26 and had emitted **no summary after ~5 minutes**, so it was cancelled — it does
not form a usable gate as-is. (The 900s figure was the job's kill bound, not an observed
runtime; the only hard runtime fact is the per-file `test_lost_fixture.py` timeout above.)

## Blocked

- **Plan item 7 — host/hierarchical cache tier.** Blocked: the live server reports
  `enable_hierarchical_cache = False` (read-only
  `curl -s http://192.168.2.168:8012/get_server_info`, 481 keys;
  also `hicache_storage_backend = None`, `disable_radix_cache = False`,
  `enable_cache_report = True`, `radix_eviction_policy = 'lru'`,
  `model_path = …/models--Accio-Lab--occamy-1.0-NVFP4/…`, `context_length = 131072`,
  `max_running_requests = 5`). Raising it needs a container relaunch with
  `--enable-hierarchical-cache` (the flag `launch-sglang-spcc.sh:54` already carries but
  which has never been applied). No restart performed.
- **Plan item 8 — Nemotron weights on the GX10.** Blocked: remote writes are
  `BLOCKED by default` per `serving/REMOTE-ROOT.md:1-8` and the workspace-only write
  policy; the live endpoint serves the occamy NVFP4 snapshot, so there is no Nemotron
  to hold the answer contract. Cannot be demonstrated from this workspace.
- **Deliverable 0 second half — merges into `main`.** Not demonstrable: `origin/main`
  is still `5554d82`, identical to `merge-base HEAD origin/main`; the branch's work sits
  on `research/next-candidates-2026-10-24` @ `17182ff` and on two backup branches only.

## Remaining red tests

1. `test_request_ledger.py::TestRealCorpus::test_g_real_corpus_total_and_delta_from_466`
   — `AssertionError: 4 != 0 : OVER BUDGET: spent=7969 + would_spend=0 = 7969 > cap=4320 - reserve=0 = 4320 (over by 3649)`. **Correctly red** — a true bad fact: the real corpus has spent 7969 requests against a 4320 cap. The message itself notes the de-duplicated figure is 7939 and is deliberately not deducted.
2. `test_journal_lint.py::test_census_over_the_live_corpus_is_reported`
   — `AssertionError: new journal misses outside the frozen baseline: ['…/handoffs/A1-AUTHOR.json', '…/A2-FIX.json', '…/A3-FIX.json', '…/ACCFIX2.json', '…/ACCRESCOPE.json', '…/AN1-POSCTRL.json', …]`. **Stale expectation**: the test pins a frozen baseline of handoff files; the corpus grew to 1356 handoff JSONs, so any new handoff without journal lines trips it. The underlying observation (new handoffs carry no journal line) is real, but the test cannot distinguish a regression from corpus growth.
3. `test_lost_fixture.py` — no assertion fails; the file **hangs** past 150s. **Correctly red** as a suite-level defect (matches `U-SPCC-9C`'s own note that the full pytest of this file exceeds its budget).

## Bottom line

A reader may rely on the *code and document artefacts*: the compiler is real and the arm
calls it (`arm_cd.py:490`, no local copy), billed accounting and the duplicate-checkpoint
guard are real (`score_longrun.py:132/978`), the supervisor's `VERIFIED` is a genuine
last-resort else-branch (`spcc_supervisor.py:562-584`), and the seven deliverables with
matching paths exist with substantive content. A reader may **not** rely on the programme
being *delivered*: nothing is merged to `main`, the working tree is 108 paths dirty, the
live endpoint still runs with `enable_hierarchical_cache = False` so item 7 is unproven
and item 8 is policy-blocked, `docs/CURRENT-REPO-STATE.md` states two facts that are
now false, and the ledger test is red because the corpus really is 3649 requests over
budget.
