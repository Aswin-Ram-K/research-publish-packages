# UCONT1 — Containment check: attribution of writes in the read-only target

**Status: done.** Verdict: **mixed** (dominantly ATTRIBUTED-EXTERNAL; one index-only OURS exposure; one residual
UNATTRIBUTED item).

**Deliverable:** [`strategy/CONTAINMENT_CHECK.md`](../../strategy/CONTAINMENT_CHECK.md)
**Handoff:** [`orchestration/handoffs/UCONT1.json`](../handoffs/UCONT1.json)

## Purpose

`AGENTS.md` requires target repos to be strictly read-only, proven by `git status` plus an mtime sweep. Unit UNC1A
found writes in `/home/zer0null/Duval` that it did not make. UCONT1's job was to **attribute** those writes — not
to assume an external actor and not to exonerate.

## Bound and constraint compliance

* Hard bound: **maximum 35 tool calls**. Used **26**. Reported `done`, not `partial`.
* **Zero `git` commands were run against the target.** Zero writes to the target. Git state was read as plain
  files (`.git/logs/HEAD`, `.git/worktrees/*/{gitdir,commondir,HEAD,ORIG_HEAD,logs/HEAD}`, `.git/index` parsed by
  byte search, `.git/objects/**` parsed with `python3`/`zlib`), and working-tree blob ids were re-derived with
  `sha1("blob <len>\0" + bytes)`.
* Wrote only the three declared paths.

## Findings (summary; details and tables in the deliverable)

| item class | attribution |
|---|---|
| `package.json`, `CONTRIBUTING.md`, `README.md`, `AGENTS.md` @ 18:26:07 (-0500) | **ATTRIBUTED-EXTERNAL, proven** — blobs changed in merge `8a86f195` from first parent `3c3e2ced`, whose reflog second `1792106767` is exactly the files' mtime second; subject `merge chore/suite-rust-test` |
| `docs/VISIT_LOG.md` @ 18:48:58 | **ATTRIBUTED-EXTERNAL** — changed by the same merge, re-stamped later |
| `traces/2026-09-28-duval-m0.jsonl` @ 18:50:03 | **ATTRIBUTED-EXTERNAL, content CHANGED** — parent `d04afbb8` blob `e25ac80f…` (**1,567,661 B / 1029 lines**) → HEAD `ec1f06d9` blob `2ec22a67…` (**1,570,243 B / 1031 lines**); that parent→HEAD pair is only **+2,582 B**, so the "+81 %" is pin 866816 B → HEAD 1,570,243 B, spanning many commits. **Superseded:** live re-measured **1,624,082 B / 1087 lines / sha256 `35687221…` at 2026-10-15 21:02:05** |
| `rust/target/tests/trybuild/**` churn 18:27:44.86→18:31:12.87 (380 files) | **consistent-with-foreign, NOT proven** — cargo writes no reflog/ref/commit; RUSTSBX (created 18:38:18) has its own separate `rust/target` |
| `.git/index` @ 18:53:12 | foreign fast-forward `ec1f06d9 → 5456b940 merge origin/main`; our 62 `status` runs are a possible prior writer, unprovable |
| target-mutating git verbs by our units | **none** |
| target writes by our units | **none** (one refused `touch` by UBUILD1) |
| index-write **exposure** by our units | **62 units** ran plain `git status` inside the target (no `--no-optional-locks`) |

## Corrections to the card's premises

* There is **no `.git/worktrees/RUSTSUITE`** and **no `refs/heads/chore/suite-rust-test`** any more — only
  `.git/worktrees/RUSTSBX` on `refs/heads/chore/sandbox-rust-toolchain`, created **18:38:18**, i.e. *after* the
  Rust churn. The foreign actor removed/replaced the earlier worktree between ~18:19 and 18:38.
* The target was **mutating live** during this check (worktree admin dirs stamped 18:51–18:55).

## Batch-claim impact

1. **Endangered:** any claim verified against the **live** trace path (bytes grew ~703 KB after our pin) — cite
   the pinned sha256 `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb`.
2. **Endangered:** "target untouched" as written — true only if restated as "no write by our units".
3. **Endangered:** the `git status`-as-proof method for the 62 units that ran it without `--no-optional-locks`.
4. **Not endangered:** workspace-captured hashed artefacts; time-scoped HEAD-identity claims.

## What could not be attributed (and why)

1. The identity of the cargo/trybuild invoker — no log/process record attests it; attribution rests on timing,
   branch naming and geometry only.
2. Which trybuild files belong to which invocation (one 3.5-min span; may be one run).
3. Whether any of our 62 `status` runs actually rewrote `.git/index` — overwritten at 18:53:12 by the foreign actor.
4. `RUSTSUITE` → `RUSTSBX`: rename vs remove+replace — no surviving evidence distinguishes them.
5. The 4 untracked paths UPAPER1b saw — deliberately not enumerated (would require a live `git status`, i.e. the
   exposure this unit documents).
