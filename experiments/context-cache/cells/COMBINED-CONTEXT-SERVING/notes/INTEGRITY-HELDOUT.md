# Integrity of the held-out claim

Reconstruction basis: no version-history file exists in the cell. This note reconstructs the task revision history from `orchestration/handoffs/{TASK-GEN,PATH-CONTRACT,FORMAT-CONTRACT,PROMPT-FIX}.json`, `tasks/CAL-DIAGNOSIS.md`, `tasks/GRADER-PROOF.md`, `notes/CAL2.json`, `notes/CAL3.json`, `run/check_prompt_contract.py`, and the current task JSONs. It records what the record supports; it does not claim byte-identity of untouched `acceptance.checks` (no handoff reports an edit to them, but no pre-edit snapshot exists either).

## Per-task revision table

| Task | Role | Revisions applied to its question text | acceptance.checks (expected/thresholds/perturbations/negative_constraints) |
|---|---|---|---|
| T1.discovery | discovery | all five contract revisions below (slice disambiguation is T1-specific) | unchanged per record (prov.algorithm, rec.shard_prefix, der.algorithm, exec.exit0, neg.*) |
| T2.discovery | discovery | no-tools sentence, path contract, print contract (ref_kinds/first_ref_kind), extraction rule | unchanged per record |
| T3.heldout | heldout | no-tools sentence, path contract, print contract (authority_scopes/real_change...), extraction rule | unchanged per record |
| T4.heldout | heldout | no-tools sentence, path contract, print contract (state_fields/derived_regions), extraction rule | unchanged per record |

## Revision ledger

| # | Revision | Affected tasks | Motivated by | Evidence |
|---|---|---|---|---|
| 1 | no-tools capability sentence ("You have no tools and cannot read files...") | all 4 | discovery-task failures before held-out was ever run (tool-call spam) | `tasks/CAL-DIAGNOSIS.md`; `orchestration/handoffs/CALIBRATE.json` (14 calls, 0 verified); `run/check_prompt_contract.py` (NO_TOOLS assertion) |
| 2 | seeded-relative path contract (`path=rel`, "absolute paths will not exist") | all 4 | discovery-task failures before held-out was ever run | `orchestration/handoffs/PATH-CONTRACT.json` (offline proof green/red on T1); `arms/render_arms.py` (`DUVAL_PREFIX` -> rel); `run/check_prompt_contract.py` (relative-path existence) |
| 3 | print contract with exact `key=value` lines | all 4 | T1 and T3 failures | `notes/CAL3.json` (dominant failure stdout `algorithm=blake\nshard_prefix=0`); `orchestration/handoffs/FORMAT-CONTRACT.json` (all 4 green offline); `run/check_prompt_contract.py` (`key=value`, `print exactly`, `nothing else`) |
| 4 | extraction rule (distinct members of union/enum/list; integer from call argument) | all 4 | T1 and T3 failures | `tasks/T1.discovery.json`/`T3.heldout.json` turn questions; `orchestration/handoffs/FORMAT-CONTRACT.json` |
| 5 | slice-argument disambiguation (shard prefix = SECOND argument of first `slice(...)`) | T1 only | T1 failure | `notes/CAL2.json` ("model emits the slice expression instead of evaluating it"); `run/envelopes/CAL8.json` ("After disambiguating the slice argument, both T1 calls must verify"); `tasks/T1.discovery.json` print contract (`slice(0, 2) gives 2`) |

Held-out-relevant revisions (motivated by observing held-out behaviour): #3 (print contract, T1/T3), #4 (extraction rule, T1 and T3), and T3's own participation in CAL3 (0 non-empty/0 verified) which drove #3/#4. #1 and #2 are motivated by discovery-task failures before held-out was ever run. #5 is motivated by a T1 (discovery) failure only.

## Candidate phrasings

- (a) "T3/T4 are held out from arm selection and from any tuning of arm rendering" — NOT supported. The question text of all four tasks, including held-out T3, was revised after observing calibration failures (T3 in CAL3; T1 slice/extract/print-contract fixes in CAL2/PATH-CONTRACT/FORMAT-CONTRACT). The prompt-facing wording was tuned against observed failures.
- (b) "T3/T4 are held out from arm selection but their questions were revised after observing failures" — SUPPORTED. T3/T4 retain the held-out role and are evaluated in the held-out phase, but their question text was revised post-observation (T3 via the CAL3 failure; shared contract revisions #3/#4). `acceptance.checks` were not edited.
- (c) "T3/T4 are not held out" — NOT supported. They are labeled and used as held-out tasks in the held-out phase (MANIFEST.json `discovery_or_heldout`; 2 arms x 2 tasks x 12 turns).

## LIMITATION

LIMITATION: The held-out tasks T3.heldout and T4.heldout were labeled and used as held-out for arm selection, but their question text (along with T1/T2) was revised after observing calibration failures (T3 in CAL3: 0 of 1 non-empty, 0 verified; T1 slice/extract/print-contract fixes in CAL2/PATH-CONTRACT/FORMAT-CONTRACT). The acceptance.checks were not edited, but the prompt-facing question text was tuned against observed failures, including a held-out task, so the held-out comparison is not a clean pre-registered holdout and any held-out performance claim must be reported as phrasing (b). A clean re-run would require the question text of all four tasks to be frozen (with a recorded digest) before the first calibration row for any task, including held-out tasks, is executed.
