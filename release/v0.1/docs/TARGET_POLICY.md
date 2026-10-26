# TARGET_POLICY — the Duval admission decision, recorded

Unit **U1.7**. Status: implemented, honoured, asserted. Config: [`config/targets.toml`](../config/targets.toml).
Code: [`src/resextract/kg/policy.py`](../src/resextract/kg/policy.py). Tests: [`tests/test_kg_policy.py`](../tests/test_kg_policy.py).

## The target

`duval` — `<workspace>`. It is **strictly read-only** for us and it is
**actively being written by a foreign actor** running its own self-build loop.
Evidence observed this session (all read-only):

* HEAD moved `6deaed0` → `b44e0e1` → `b2bade3` → `5cdc471a` → `3982f261` →
  `5cdc471a` this session (U1.7R re-read it before and after its audit:
  `5cdc471afb2a14934030d581a20f6a9bcffb727e` both times).
* `git status --porcelain` shows only untracked additions: `?? .ci-trunk.txt`, `?? .lane-j-scratch/` (2 entries).
* `.worktrees/run-1/` holds hundreds of files (443 counted, names only, no content read).

Consequence: any copy of this repo must be **commit-pinned**; an extraction must
never assume a stable HEAD, and we never walk or copy `.worktrees/`.

## The decision: `.lane-j-scratch/**` is ADMITTED

A sibling unit (U1.5) reported that untracked scratch in Duval
(`.ci-trunk.txt`, `.lane-j-scratch/**`, 20 files) is **not gitignored**, so
graphify's real predicate admits it into corpora; excluding it would mean
inventing policy. The decision is to **admit it**, and `docs/PLAN.md` lists
`.lane-j-scratch/*.md` as an include for this target.

Why it matters — observed sizes at HEAD `5cdc471`:

| path | bytes | what it is |
|---|---|---|
| `.lane-j-scratch/monograph.txt` | 83,832 (~83 KB) | a 42-section architecture monograph |
| `.lane-j-scratch/consonance-external-evidence-2026-10-07.md.txt` | 159,408 (~159 KB) | a URL + date + quote evidence review |

These are the **densest publishable material in the repo**. `.ci-trunk.txt`
(281,253 B) enters under the same rule and is harmless: it is scored low later,
not excluded now.

Note the near-miss this policy exists to prevent: the original include entry
`.lane-j-scratch/*.md` does **not** match `monograph.txt` (extension `.txt`) nor
`consonance-external-evidence-2026-10-07.md.txt` (`.md.txt`). An intent-only
config would have dropped both. That is why `include` carries an explicit
`.lane-j-scratch/**` **and** why the two files are named in `assert_present`.

## The rules

1. **Admission starts from graphify's real predicate** —
   `graphify.detect.ignored_predicate` (`.graphifyignore` + `.gitignore` chains +
   `$GIT_DIR/info/exclude` + the tracked-file exemption), `_is_noise_dir` and
   `_SKIP_FILES`, reached through `resextract.kg.ingest._walk`. No second
   implementation of ignore semantics exists in this layer.
2. **Config may narrow, never widen.** `exclude` globs turn an admit into a
   reject. An `include` entry that names something graphify prunes
   (`.git/`, `.worktrees/`, `node_modules/`) is a widening attempt and
   `TargetPolicy.from_config` raises `PolicyWideningError` naming the entry.
   `.worktrees/` is therefore *not* listed anywhere: the predicate already
   rejects it and listing it would imply the predicate is untrusted.
3. **Every decision names why.** `Admission(admitted, reason, source)` with
   `source ∈ {graphify_predicate, config_exclude, config_assert, noise_dir,
   ignored_dir, skip_file}`.

## The silent-loss guard: `assert_present`

Asserted (repo-relative, all confirmed to exist before being asserted):

| path | bytes | admitted |
|---|---|---|
| `.lane-j-scratch/monograph.txt` | 83,832 | yes |
| `.lane-j-scratch/consonance-external-evidence-2026-10-07.md.txt` | 159,408 | yes |
| `README.md` | 19,578 | yes |
| `CITATION.cff` | 973 | yes (admitted; graphify classifies it unsupported, so `ingest` normalises it — a coverage concern, not an admission one) |
| `docs/FINDINGS.md` | 27,401 | yes |

`policy_audit(target_root, policy)` reports, for each asserted path, whether it
exists and whether it is admitted:

* exists **and** admitted → `ok: true`;
* exists but **not** admitted → a `violations` entry:
  `asserted path '…' EXISTS (N bytes) but is NOT admitted (config_exclude: …) — violation: the corpus would SILENTLY lose it`;
* does **not** exist → a `missing_expected` violation, because the assertion
  documents intent that has drifted.

## The consequence if the policy changed silently

If a future ignore rule, graphify predicate change, or config default dropped
`.lane-j-scratch/`, the monograph and the evidence review would simply **not
appear** among findings. Nothing downstream would report their absence — there
would be no error, no gap, no note. With this policy, `policy_audit` returns a
non-empty `violations` list naming the path and the reason, and the test
`test_silent_loss_guard_reports_violation_not_quiet_absence` fails.

Both guards are red→green verified: reverting the violation append makes the
audit return `violations == []` (test fails), and reverting the widening refusal
makes `from_config` accept `.worktrees/` (test fails). The captured failure texts
are pasted both in the test module docstring and in each guard test's docstring.

## Live audit (U1.7R, read-only, HEAD `5cdc471a`)

`policy_audit("<workspace>", real_duval_policy)`:

* **537 files admitted**, 8 rejected; `rejected_by_reason = {ignored_dir: 4, noise_dir: 3, skip_file: 1}`.
* **`violations: []`** — every asserted path exists and is admitted.
* all five `assert_present` results `ok: true`: monograph 83,832 B; evidence
  review 159,408 B; `README.md` 19,578 B; `CITATION.cff` 973 B;
  `docs/FINDINGS.md` 27,401 B.
* `.ci-trunk.txt` admitted, 281,253 B, `source=graphify_predicate`.
* `.worktrees/` is recorded as **one** rejected directory entry
  (`source=noise_dir`, "never walked") because graphify prunes the whole subtree;
  it is not enumerated file-by-file, and we never read it.

Silent-loss demonstration (throwaway config `state/logs/U1.7R-exclude-demo.toml`
excluding `.lane-j-scratch/**`; the real config was not modified): the monograph
and the evidence review appear as **violations** —
`asserted path '…' EXISTS (83832 bytes) but is NOT admitted (config_exclude: …) —
violation: the corpus would SILENTLY lose it` — rather than as a quiet absence.
