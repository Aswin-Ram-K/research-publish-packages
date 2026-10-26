# CONTAINMENT_CHECK — attribution of the writes found in `/home/zer0null/Duval`

Unit: **UCONT1**. Snapshot time: **2026-10-15 18:54–18:56 CDT** (`date` → `Thu Oct 15 06:54:37 PM CDT 2026`).
Status: **mixed** — every working-tree write I found is attributable to a session *other than this workspace's
units*, and this workspace's units additionally exposed the target's `.git/index` to writes by running plain
`git status` inside it. One residual item stays unattributed.

## 0. Method (and what this report is not)

* **No `git` command was run against `/home/zer0null/Duval`.** No write of any kind was made to it.
* Git state was read **as plain files**: `.git/HEAD`, `.git/ORIG_HEAD`, `.git/COMMIT_EDITMSG`, `.git/FETCH_HEAD`,
  `.git/logs/HEAD`, `.git/logs/refs/heads/*`, `.git/refs/heads/*`, `.git/packed-refs`, `.git/worktrees/*/{gitdir,commondir,HEAD,ORIG_HEAD,logs/HEAD}`.
* Blob identities were computed **without git**, by parsing zlib-deflated loose objects under `.git/objects/`
  and by re-deriving `sha1("blob <len>\0" + bytes)` for working-tree files. The `.git/index` was parsed by byte
  search for the path, reading the 62-byte entry header at `pathpos-62`.
* `/home/zer0null/Duval/.worktrees/` (the checkouts) and `.git/worktrees/` (the admin dirs) were listed but not
  written.
* **The target is mutating right now.** A concurrent session is live in it (see §2). Every timestamp below is a
  snapshot of 18:54–18:56 and may already be superseded.

## 1. mtime sweep

Whole-tree recent count (excluding nothing):

| command | result |
|---|---|
| `find . -newermt "2026-10-08" -type f \| wc -l` | **35824** |
| `find . -type f -newermt "2026-10-15 18:00:00" ! -newermt "2026-10-15 19:30:00" \| wc -l` | **5123** |

Files with mtime in **18:26:06–09**, excluding `.git/`, `node_modules/`, `rust/target/` — **exactly four**:

| path | mtime (-0500) | size (B) |
|---|---|---|
| `/home/zer0null/Duval/AGENTS.md` | 2026-10-15 18:26:07.334543343 | 16907 |
| `/home/zer0null/Duval/CONTRIBUTING.md` | 2026-10-15 18:26:07.335318978 | 9693 |
| `/home/zer0null/Duval/README.md` | 2026-10-15 18:26:07.335419179 | 19869 |
| `/home/zer0null/Duval/package.json` | 2026-10-15 18:26:07.337521206 | 9039 |

The other files named in the unit card:

| path | mtime (-0500) | size (B) |
|---|---|---|
| `/home/zer0null/Duval/traces/2026-09-28-duval-m0.jsonl` | 2026-10-15 18:50:03.338951832 | 1570243 |
| `/home/zer0null/Duval/docs/VISIT_LOG.md` | 2026-10-15 18:48:58.803462196 | 551333 |
| `/home/zer0null/Duval/.git/index` | 2026-10-15 18:53:12.517387150 | 68280 |
| `/home/zer0null/Duval/rust/target` (dir) | 2026-10-15 18:27:45.650284180 | — |
| `/home/zer0null/Duval/rust/target/tests/trybuild/x86_64-unknown-linux-gnu/debug/.fingerprint/core-state-tests-2997bdab929c3a99/output-bin-trybuild000` | 2026-10-15 18:31:12.8728274230 | 2617 |
| `/home/zer0null/Duval/rust/target/tests/trybuild/x86_64-unknown-linux-gnu/debug/deps/trybuild000-2997bdab929c3a99.d` | 2026-10-15 18:31:12.8098269740 | 458 |
| `/home/zer0null/Duval/rust/target/tests/trybuild/x86_64-unknown-linux-gnu/debug/.fingerprint/core-state-tests-701284699bbedde4/bin-core-state-tests.json` | 2026-10-15 18:31:12.7818267740 | 717 |

`trybuild` churn: **380 files**, all newer than 18:00; mtime span **1792106864.86 → 1792107072.87**
= **18:27:44.86 → 18:31:12.87** (a single ~3.5-minute run). The Rust target dir itself was stamped 18:27:45.

## 2. `.git/worktrees` evidence (read as plain files)

The card's "concurrent unrelated session" is confirmed and is **still active**:

```
.git/worktrees/RUSTSBX/HEAD      -> ref: refs/heads/chore/sandbox-rust-toolchain
.git/worktrees/RUSTSBX/ORIG_HEAD -> 05d789f4ac5c878700f75c25dc8e13f1cb20ecde
.git/worktrees/RUSTSBX/gitdir    -> /home/zer0null/Duval/.worktrees/RUSTSBX/.git
.git/worktrees/RUSTSBX/commondir -> ../..
.git/worktrees/RUSTSBX/logs/HEAD line 1:
  0000000000000000000000000000000000000000 05d789f4ac5c878700f75c25dc8e13f1cb20ecde
  Aswin Ram K <Aswin-Ram-K@users.noreply.github.com> 1792107498 -0500  reset: moving to HEAD
```

* `1792107498 -0500` = **18:38:18** — the RUSTSBX worktree was created **after** the Rust churn.
* RUSTSBX has its **own** `rust/target` (`/home/zer0null/Duval/.worktrees/RUSTSBX/rust/target`, dir mtime 18:55).
  Runs from RUSTSBX therefore do **not** explain the churn under `/home/zer0null/Duval/rust/target`.
* Worktree admin dirs touched today, newest first — this is liveliness, not history:
  `COREJ 18:54:14`, `FUNNEL 18:53:35`, `RUSTSBX 18:53:35`, `PARITY 18:53:35`, `VERIFY-ci 18:51:13`.
* **Correction to the card's premise:** there is **no `.git/worktrees/RUSTSUITE`** and **no branch
  `chore/suite-rust-test` ref** any more. `.git/refs/heads/chore/suite-rust-test` → ABSENT;
  `.git/logs/refs/heads/chore/suite-rust-test` → ABSENT; `.git/worktrees/RUSTSUITE` → ABSENT.
  Only `.git/refs/heads/chore/sandbox-rust-toolchain` remains under `.git/refs/heads/chore/`
  (that dir's mtime is 18:38:18). So the worktree/branch the earlier units observed has been
  **removed and replaced** by the foreign actor between ~18:19 and 18:38.

## 3. Attribution, class by class

### 3.1 `package.json` / `CONTRIBUTING.md` (and `README.md`, `AGENTS.md`) at 18:26:07 — **ATTRIBUTED-EXTERNAL, proven**

Root reflog, last lines (`/home/zer0null/Duval/.git/logs/HEAD`):

```
... 3c3e2cedde5910980e99519b57b920ecd8093f88 8a86f195830f93f6908d9a92a3262cac20ab9658
    Aswin Ram K <Aswin-Ram-K@users.noreply.github.com> 1792106767 -0500
    merge chore/suite-rust-test: Merge made by the 'ort' strategy.
```

`1792106767 -0500` = **18:26:07** — the *same second* as all four mtimes. Diffing the merge's tree against its
first parent's tree, computed from loose objects:

* merge `8a86f195` parents: `3c3e2ced…` (first), `57f4466c…` (second, tip of `chore/suite-rust-test`)
* tree diff `3c3e2ced` → `8a86f195` over 404 tracked files: **added 0, removed 0, changed 5**:

| path | pre-merge blob | merge blob |
|---|---|---|
| `AGENTS.md` | `42363788982a6d22848e60afdf662036c70240be` | `28635cba1058d02e1f51a8ca410d6d9049cdddde` |
| `CONTRIBUTING.md` | `f4fb6de847398d2b4e10d1792eed40c660db261a` | `79b031bfec2fb2ab8534cb87c6d383cf59fe10ca` |
| `README.md` | `6fb6216ecaa7f0b99ecf2d64ea6ff012bae2cf47` | `8da706a3ba6e321814ccc76f583479be18c88f71` |
| `package.json` | `7fd7748b8569249a53ddffe38f4ff65202d54449` | `85b6815566db275d802b25209c363d2465c9a920` |
| `docs/VISIT_LOG.md` | `ece2be2b79094643b0f5fb0058d12b8d743f38f7` | `3a7de387950e71874025e78331002c616b72e07b` |

The working-tree bytes of the four files equal their **post-merge** blobs and the `.git/index` entry blobs:

| path | index size | index blob = working sha1 | HEAD tree blob | verdict |
|---|---|---|---|---|
| `package.json` | 9039 | `85b6815566db275d802b25209c363d2465c9a920` | same | match |
| `CONTRIBUTING.md` | 9693 | `79b031bfec2fb2ab8534cb87c6d383cf59fe10ca` | same | match |
| `README.md` | 19869 | `8da706a3ba6e321814ccc76f583479be18c88f71` | same | match |
| `AGENTS.md` | 16907 | `28635cba1058d02e1f51a8ca410d6d9049cdddde` | same | match |

**Conclusion.** These are *content* writes, not touched-but-unchanged mtimes: the blobs changed in the merge
commit whose reflog second is exactly the files' mtime second, and the mtime set is exactly 4 of the 5 paths the
merge changed (`docs/VISIT_LOG.md` was changed by the same merge, then re-stamped later at 18:48:58 by the foreign
session's visit-log workflow). They belong to the **Consonance repo's own suite/docs**, and the merge that
produced them merged a branch literally named **`chore/suite-rust-test`** — i.e. a Rust/JS suite branch, not the
Consonance TypeScript tree's own work. Contemporaneous reflog/reflog-adjacent evidence: the merge line above, and
the follow-up `commit: chore(traces): settle the frontier behind the suite merge, and regenerate INDEX` at
`1792106886` = **18:28:06**.

### 3.2 `rust/target/tests/trybuild/**/.fingerprint` churn — **CONSISTENT-WITH-FOREIGN, not proven**

**What the evidence supports (timing and geometry):**

* The run spans **18:27:44.86 → 18:31:12.87** — 97 s after the `chore/suite-rust-test` merge (18:26:07) and
  7 minutes **before** the RUSTSBX worktree existed (18:38:18).
* It ran against the **root checkout's** `rust/target` (dir mtime 18:27:45), and RUSTSBX has a separate
  `rust/target`, so RUSTSBX cannot be its source.
* The branch merged 97 s earlier is named for exactly this: a **suite** rust **test** run.

**What the evidence does NOT support (the honest gap):** `cargo`/`trybuild` writes **no** reflog line, no ref, no
commit. Nothing in the target names the process, the PID, the shell, or the worktree that invoked it. There is no
`.git/worktrees` dir whose admin mtime falls in 18:27–18:31. So this is "**fails to contradict** the foreign-session
hypothesis", which is a weaker claim than "supports it".

**Also recorded:** the specific `.fingerprint` paths are regenerated artefacts of the same run
(`.../core-state-tests-{2997bdab929c3a99,701284699bbedde4,f11b650a353a0bd8}/{invoked.timestamp,bin-core-state-tests}`,
all 18:31:12.5–18:31:12.8). Note the crate name **`core-state-tests`** belongs to the Rust migration work
(`feat/rust-core-state`, merged 18:13:09), i.e. the same foreign programme.

### 3.3 `traces/2026-09-28-duval-m0.jsonl` at 18:50:03 — **CONTENT CHANGED; ATTRIBUTED-EXTERNAL**

The bytes **changed**. Proven without git three independent ways:

1. Reflog: `d04afbb8b36a047dc5a2f271fa476e4e31989cf6 → ec1f06d9639d2ce843b6dfea5085272ce985ab4d`,
   `1792108208 -0500` = **18:50:08**, `commit: chore(traces): settle the frontier behind the D-142/D-143 ledger append`
   (`.git/COMMIT_EDITMSG` mtime 18:50 holds the same subject).
2. Tree blobs for that path: **parent `d04afbb8` (18:49:14) → `e25ac80fba75745909e8b1bc89f1cf2bab18e79c`**;
   **HEAD `ec1f06d9` → `2ec22a6781240c3fd906d3692eeba432b9a8733d`**. Different blob ⇒ different bytes.
   *Measured from the objects themselves (zlib read of `/home/zer0null/Duval/.git/objects`, no git):
   `e25ac80f` = **1,567,661 B / 1029 lines**; `2ec22a67` = **1,570,243 B / 1031 lines**, sha256
   `03fa52a68dbf6d296aab649c93f341ff3a0629d849d789d81282191d86a795c2`. This parent→HEAD pair therefore shows
   only **+2,582 B**; the +703,427 B growth cited below is pin (866,816 B) → HEAD (1,570,243 B), across many
   commits, not this pair.*
3. Working tree = index = HEAD: file size **1570243**, working blob sha1 `2ec22a67…`, `.git/index` entry size
   1570243 and blob `2ec22a67…` → `index_match = YES`.

So it was **actually rewritten** (appended to), not merely touched by a read or a checkout. The write timestamp
(18:50:03) precedes the settling commit (18:50:08) by five seconds — the shape of a foreign "append the trace,
then commit it" workflow, the same workflow the reflog shows repeatedly (`chore(traces): settle the records …` at
16:10:21, 17:02:57, 18:15:27, 18:28:06, 18:49:14).

**Our own prior capture proves material growth.** `/home/zer0null/reserach extarctor/dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl`
is **866816 bytes** (573 records; 573 gated lines / 712 gate occurrences under the pattern set at
`strategy/LEAD_PACKAGE.md` §1 "Gate-hit measurement", `:41-46`), the **workspace docket repo's** recorded blob
`94495930fbf0fd991b14c1e4de79d87a93fce9ae` — *not a target object*: it is absent from
`/home/zer0null/Duval/.git/objects` — sha256
`431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb` (recorded in that docket's `MANIFEST.json`,
which also records `"src": "/home/zer0null/Duval/traces/2026-09-28-duval-m0.jsonl"`). The live file is now
**+703427 bytes (+81 %)** larger. *(The `grep` recorded here returned no hits at the time; the ids are now
recorded in this workspace — `orchestration/units/UCONT1.md` attribution table, trace row, `:30` — so a re-run hits.)*

### 3.4 `.git/index` at 18:53:12 — **foreign, and separately exposed by our own units**

`.git/index` mtime = 18:53:12.517387150, size 68280 — coincident with the reflog's
`ec1f06d9… → 5456b940… 1792108392 -0500` = **18:53:12** `merge origin/main: Fast-forward`;
`.git/FETCH_HEAD` (branch `main` of `https://github.com/Aswin-Ram-K/Consonance`) is mtime 18:53.
`.git/index.lock` is ABSENT (no stuck lock). See §4 for why this mtime is not attributable to us.

## 4. Per-unit audit of target-referencing commands

Parsed from the `commands` arrays only (not free text) across `orchestration/handoffs/*.json`:

* **136** handoffs reference `/home/zer0null/Duval`; **194** target-referencing command strings.
* git subcommands actually issued against the target (measured over real command strings; `--no-optional-locks`
  invocations excluded from the histogram): `rev-parse` (55), `status` (17), `log` (6), `reflog` (2),
  `merge-base` (2), `ls-tree` (2), `cat-file` (2), `ls-files` (1), `check-ignore` (1), `hash-object` (1),
  `rev-list` (1), `branch` (1), plus one `clone`.
* **62 units issued a plain `git -C /home/zer0null/Duval … status`** (no `--no-optional-locks`) as an actual
  command: U0.10, U0.17, U0.18, U0.20, U1.1, U1.4, U1.5, U1.6, U1.7R, U2.1, U2.4, U2.10, U3.4, U4.0, U5.1,
  U5.3, U5.4, U5.9, U5.10, U5.11, U5.12, U5.13, U5.14, U5.15, U5.17, U5.27, U5.28, U5.33, U6.9, U6.11, U6.16,
  U6.18, U6.20, U6.23, U7.1, U8.3, U8.6, U8.18, U8.19, U8.24, U8.25, U8.31, U8.32, U8.35, UCAND1, UDISC1,
  UDISC2, UEXP, UEXP2, UFIX6, UJ2, UJC1, UP2, UPAPER1a, UPAPER1b, UPAPER1c, UPAPER1d, UPAPER1e, UPIPE,
  UREFS, UREPRO, UTS1.
* **7 units confined their status to `--no-optional-locks`**: U0.25, U2.12, U4.3, U4.4, U5.18, U8.15, U8.36.
* **No unit ran a target-mutating git verb.** There is no `pull`, `fetch`, `checkout`, `switch`, `reset`,
  `restore`, `add`, `commit`, `stash`, `clean`, `merge`, `rebase`, `worktree`, `gc` or `update-index` against the
  target in any `commands` array. The `pull -q --ff-only origin main` / `checkout` pair that moved HEAD on
  Oct 8 was reported by **U0.15 itself** as a *foreign* actor (`orchestration/handoffs/U0.15.json`, `note` field).
* Target-write **attempts** — two, both resolved without a target write:
  * `UBUILD1`: `touch /home/zer0null/Duval/.ubuild1_probe` → **`Read-only file system`**. A write was attempted and
    the filesystem refused it. (This is evidence that some target writes were blocked at the sandbox/mount level;
    it is *not* evidence that the target is globally write-protected — §3 shows writes that succeeded.)
  * `UNC1A`: `/home/zer0null/Duval/node_modules/.bin/tsc -p tsconfig.emit.json && node probe-emit.mjs`. I checked
    the working location: the tsconfig is ours (`/home/zer0null/reserach extarctor/scratch/unc1a/sim/tsconfig.emit.json`
    exists) and the target has **only** `/home/zer0null/Duval/tsconfig.json` (`ls /home/zer0null/Duval/tsconfig*.json`).
    UNC1A therefore ran the target's **tsc binary** over the workspace's **simulated** package (`scratch/unc1a/sim/**`,
    e.g. `scratch/unc1a/sim/pkg-fixed/evals/prevention.ts`) and **did not compile in the target**. No target write
    is evidenced from this invocation.
* Read-only by construction: `U7.2`'s `git clone --no-hardlinks --depth 1 file:///home/zer0null/Duval state/verify/U7.2/duval-copy`
  reads the target and writes into the workspace; `UREDACT1`'s `git -C /home/zer0null/Duval hash-object <tree>/harness/analyze.py`
  computes a hash (no `-w`); `UPAPER1b/d`'s `cd /home/zer0null/Duval && git log|merge-base|ls-tree|branch` are
  read-only (these verbs do not refresh the index).

**The honest residue is the `status` calls.** Git's `status` computes freshness and, unless optional locks are
disabled (`--no-optional-locks` / `GIT_OPTIONAL_LOCKS=0`), writes the refreshed `.git/index` back — so the 62
units above were *able* to write inside the target's `.git/`, and each such run may transiently create
`.git/index.lock`. I cannot show that any particular one **did** (git rewrites the index only when the stat cache
is stale), and no artefact of ours survives: the current `.git/index` mtime is 18:53:12, written by the foreign
fast-forward, which overwrote whatever index state our runs left. This is a real but **index-only** exposure —
no working-tree file in the target was written by us.

## 5. Verdict

**mixed** — dominantly **ATTRIBUTED-EXTERNAL**, with one **OURS (index-only)** exposure and one residual
**UNATTRIBUTED** item.

| item | verdict |
|---|---|
| `package.json`, `CONTRIBUTING.md`, `README.md`, `AGENTS.md` @ 18:26:07 | **ATTRIBUTED-EXTERNAL** (proven: blob delta in merge `8a86f195` = reflog second 18:26:07) |
| `docs/VISIT_LOG.md` @ 18:48:58 | **ATTRIBUTED-EXTERNAL** (changed by the same merge; re-stamped later) |
| `traces/2026-09-28-duval-m0.jsonl` @ 18:50:03 | **ATTRIBUTED-EXTERNAL**, **content changed** (`e25ac80f` → `2ec22a67`) |
| `rust/target/tests/trybuild/**` churn 18:27:45–18:31:12 | **consistent-with-foreign, not proven** (no log attests the invocation) |
| `.git/index` @ 18:53:12 | foreign fast-forward (18:53:12) — but our 62 `status` runs are a plausible prior writer |
| target-mutating git verbs by our units | **none** |
| target writes by our units | **none** (only one refused `touch`) |
| our units' index-write exposure | **OURS, index-only, 62 units** |

**Scope of the verdict.** ATTRIBUTED-EXTERNAL covers *every working-tree write under `/home/zer0null/Duval` that
I found in the 18:26–18:53 window*. It does **not** cover (a) the identity of the process that invoked the Rust
suite, nor (b) the `.git/index` state between Oct 8 and 18:53:12, where our own units were possible writers.

## 6. What I could not attribute, and why

1. **The cargo/trybuild invocation itself (18:27:45–18:31:12).** `cargo` leaves no reflog, ref, or commit. No
   process table, shell history, or log was consulted (out of scope, and the target is live). Attribution rests
   on timing (97 s after merging `chore/suite-rust-test`), branch naming, and the fact that RUSTSBX did not exist
   yet and has its own target dir. *What is missing:* a shell history / process record / CI log naming the run.
2. **Which run wrote which of the 380 trybuild files.** They fall in one continuous 3.5-minute span, consistent
   with one invocation, but I cannot separate multiple invocations from the artefact mtimes alone.
3. **Whether any of our 62 plain-`git status` runs actually rewrote `.git/index`.** Git rewrites it only on a
   stale stat cache, and the current index (18:53:12) has been overwritten by the foreign actor. *Missing:*
   per-invocation index inodes/hashes captured at the time — nobody captured them.
4. **`RUSTSUITE` vs `RUSTSBX`.** Earlier units recorded `.git/worktrees/RUSTSUITE` and branch
   `chore/suite-rust-test`; both are **gone**. I cannot distinguish "renamed to RUSTSBX" from "removed and
   replaced" — no `RUSTSUITE` admin dir, ref, or log survives. (The two differ in branch name:
   `chore/suite-rust-test` vs `chore/sandbox-rust-toolchain`.)
5. **The 4 untracked paths** `UPAPER1b` reported alongside HEAD `907fa39d` (`"907fa39 + 4 untracked (concurrent
   session)"`). I deliberately did not enumerate them: that requires a live `git status` inside the target, which
   would itself write the index — the exact exposure §4 documents.

## 7. Are any batch claims endangered?

**Yes — narrowly, but really.**

1. **Live-path claims about the trace file are endangered.** `traces/2026-09-28-duval-m0.jsonl` grew from
   **866816** B at our pin (2026-10-08 06:25:11) to **1570243** B at 18:50:03 (live object `2ec22a67…`; the
   docket's own recorded blob `94495930…` is not a target object). It has moved **again** since: **1,624,082** B /
   1087 lines / sha256 `35687221b1a19d540534ff601ee233f67b814f643243bc933107ce703bff075d` at 2026-10-15 21:02:05.
   Any batch claim verified against
   the *live* file is no longer reproducible; claims must cite the pinned copy and its sha256
   `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb` (or the **workspace docket repo's** own recorded blob `94495930fbf0fd991b14c1e4de79d87a93fce9ae`, not a target object)
   and say so. **A source of evidence for this batch's claims was mutated.**
2. **"The target was untouched" is false as written for the root checkout.** Five root files were rewritten at
   18:26:07/18:48:58 and the trace at 18:50:03 — by the foreign actor. The correct claim is: *"no write by this
   workspace's units"*, not *"no writes"*.
3. **The `git status` proof method is self-undermining** for the 62 units that ran plain `git status` in the
   target: the operation invoked as *proof* of read-only-ness is itself capable of writing `.git/index` there.
   The 7 units that used `--no-optional-locks` are the only ones whose containment proof is clean on this point.
4. **Not endangered:** claims about artefacts we copied into the workspace and hashed (the docket pin, dockets'
   MANIFEST sha256s), and HEAD-identity claims scoped to a time (`907fa39d…`, `5cdc5562…`): the reflog
   corroborates them (`907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` was HEAD until 18:15:27, exactly as several
   units recorded as "concurrent session present, HEAD advanced").

## 8. Exact evidence commands (all read-only; no git against the target)

```
date
find . -newermt "2026-10-08" -type f | wc -l                     # 35824
find . -type f -newermt "2026-10-15 18:00:00" ! -newermt "2026-10-15 19:30:00" | wc -l   # 5123
stat -c '%y | %s | %n' package.json CONTRIBUTING.md README.md AGENTS.md traces/2026-09-28-duval-m0.jsonl
cat .git/HEAD .git/ORIG_HEAD .git/COMMIT_EDITMSG .git/FETCH_HEAD
tail -25 .git/logs/HEAD
ls -la .git/worktrees ; cat .git/worktrees/RUSTSBX/{gitdir,commondir,HEAD,ORIG_HEAD} ; cat .git/worktrees/RUSTSBX/logs/HEAD
find rust/target -path '*trybuild*' -type f -printf '%T@ %s %p\n' | sort -n    # 380 files, 18:27:44.86 -> 18:31:12.87
# blob identities (no git): python3 zlib parse of .git/objects/** + sha1("blob <len>\0"+bytes)
#   merge 3c3e2ced -> 8a86f195 : added 0, removed 0, changed 5 (table in §3.1)
#   traces: parent d04afbb8 blob e25ac80f... ; HEAD ec1f06d9 blob 2ec22a67... ; working sha1 2ec22a67...
# handoff audit: python3 json parse of orchestration/handoffs/*.json, key == "commands", filter on the target path
```
