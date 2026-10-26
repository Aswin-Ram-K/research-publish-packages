#!/usr/bin/env python3
"""Build the 12-item instruction corpus for the lazy-loading measurement.

Original text, written for this experiment. No third-party documents.
Every item body is several paragraphs long so the corpus is a realistic
instruction payload (target 20,000-40,000 characters) rather than a stub.

Bodies are generated here so the corpus is reproducible: rerunning this script
regenerates byte-identical files, and MANIFEST.json records each sha256.
"""
import hashlib
import json
import pathlib

ITEMS = []


def add(kind, iid, title, body):
    ITEMS.append({"id": iid, "kind": kind, "title": title, "body": body.strip() + "\n"})


# ------------------------------- TOOLS (3) -------------------------------
add("tool", "T-1", "Record coalescer", """
TOOL T-1 -- coalesce_records

Purpose. Merge duplicate records emitted by the ingestion fan-out into one row per
natural key. The fan-out exists because a single upstream write can be observed by
several collectors at once; without coalescing, the warehouse accumulates N rows per
logical write, and every downstream join silently multiplies its result set. The tool
is deliberately narrow: it does not deduplicate across time windows and it does not
resolve keys, it only merges rows that already agree on a key.

Interface. coalesce_records(rows, key, conflict="earliest")

  rows      -- a list of dicts. Must be non-empty; an empty list returns an object
               with .rows == [] and is not an error.
  key       -- the field name used to group. Defaults to "record_id".
  conflict  -- "earliest" or "latest" decides which timestamp wins when two rows in
               the same bucket disagree on a field. Every other combination of
               {prefer, conflict} spellings is rejected with a ValueError rather
               than silently defaulted, because a silently defaulted conflict
               policy produces a wrong answer with no signal.

Behaviour.

  * Rows are bucketed by the key value. Bucket order is the order of first
    appearance in the input, so coalesce_records is stable with respect to input
    order and two runs over the same list produce identical output.
  * The winning row supplies every non-null field. Null fields are backfilled from
    the other rows in bucket order, so a field that is null in the winner but
    present in a loser is filled rather than lost.
  * Rows whose key value is missing or null are dropped, and the count is reported
    in .dropped. This is not an exception: partially-keyed batches are normal.
  * Returns an object with .rows (list of dicts), .dropped (int), .groups (int).

Limits. Memory is O(rows) and no chunking is performed. Do not call it on a stream
wider than available RAM. A spilling variant exists for that case but it is NOT part
of this tool; the two are not interchangeable because the spilling variant does not
preserve first-appearance bucket order.

Failure modes.

  * If more than 5 percent of rows lack the key field, KeyLikeMismatch is raised.
    That threshold exists because a handful of junk rows is dirt while a majority is
    almost always the wrong argument.
  * Passing key="id" when the data spells the field "record_id" drops every row and
    reports .dropped == len(rows). Check .dropped before trusting an empty result.
  * Timestamps are compared as strings, not parsed. Mixed formats in one bucket make
    the conflict policy arbitrary; normalise timestamps before coalescing.

Typical misuse. Calling this once per request in a hot path. It is a batch tool; the
per-request cost is dominated by dict construction, not by the merge itself.
""")

add("tool", "T-2", "Field splitter", """
TOOL T-2 -- split_fields

Purpose. Split a delimited text field into ordered parts while preserving empty
parts. This is the tool people reach for when they need to split a CSV-ish field that
is not quite CSV, and the reason it exists separately from the language's builtin
split is the max_parts behaviour below.

Interface. split_fields(text, sep=",", max_parts=0, quote=None)

  text       -- a str. None returns [].
  sep        -- a literal string delimiter, never a regular expression.
  max_parts  -- 0 means unlimited. A positive value keeps the first max_parts-1
                delimiters and lets the final part absorb the remainder verbatim,
                so the trailing delimiters stay inside the last part rather than
                disappearing.
  quote      -- None disables quote handling; supplying a quote character enables
                it with the limitations described below.

Behaviour.

  * Whitespace is never stripped. Callers that want stripping must strip the parts
    themselves; doing it inside would make positional alignment depend on content.
  * With max_parts=0 the result length always equals len(text.split(sep)),
    including trailing empty parts. Emitting trailing empties is deliberate:
    positional alignment beats tidiness, and a caller indexing into a record wants
    positions to mean the same thing in every row.
  * Quote handling is OFF by default and is partial when enabled. Quoted spans are
    atomic only when the opening quote is the very first character of a part. A
    quote that appears mid-part is treated as a literal character.
  * Returns a list of str.

Limits. O(len(text)). No nesting, no escaping, no multi-character quote handling. A
delimiter inside a quoted span still splits the part when the quote did not open the
part. If those cases matter, the input is not in this tool's domain.

Failure modes.

  * Passing a compiled regex as sep raises a TypeError rather than falling back to
    re.split, because the two disagree on empty-match handling and a silent fallback
    would change results for existing callers.
  * Using max_parts to skip a leading column works only if that column cannot itself
    contain sep. Prefer dropping the column after splitting.
  * Round-tripping through split_fields and a join is not lossless when max_parts > 0
    and the final part contained sep runs.
""")

add("tool", "T-3", "JSON note writer", """
TOOL T-3 -- write_note_json

Purpose. Write one JSON object to a file atomically. Intended for handoff notes,
small state snapshots, and per-run metadata where a half-written file would mislead
a reader.

Interface. write_note_json(path, obj, indent=2)

Behaviour.

  * Writes to <path>.tmp in the same directory as path, flushes, fsyncs the file, then
    renames it over <path>. A reader therefore sees either the old file or the new
    file and never a partial one.
  * Refuses to serialise anything that is not a dict at the top level. A list or a
    scalar raises rather than being wrapped, because wrapping invents a schema.
  * Non-serialisable values raise. Nothing is coerced to str implicitly, so a
    datetime in the payload is an error rather than an ISO string that happens to
    parse on this machine.
  * The tmp file is not removed on failure; it is overwritten on the next call. A
    leftover .tmp is therefore evidence of a crash, not evidence of corruption.

Limits. Sized for small payloads, on the order of a few megabytes. It is not a log
writer: do not call it once per request, the fsync dominates. Concurrent writers to
the same path are last-rename-wins with no locking; if two processes must append to
one logical note, they need a queue in front of this tool.

Failure modes.

  * A path whose parent directory does not exist raises. The tool does not create
    directories, so a mistyped export path fails loudly instead of scattering files.
  * A rename across filesystems falls back to a copy plus replace, which is not
    atomic. Keep the tmp file beside the destination, which this tool does by
    construction.
""")

# ------------------------------- SKILLS (3) ------------------------------
add("skill", "S-1", "Pre-release checklist", """
SKILL S-1 -- Pre-release checklist

When to use. Before tagging a release of a service that has downstream consumers.
For a leaf service with no consumers, only steps 1, 2 and 5 apply; the rollback
rehearsal is calibrated for changes that other teams pin.

Steps.

  1. Pin the dependency set and commit the lockfile. An unlocked release is not a
     release, it is a reproduce-on-good-luck build. If the lockfile diff is large and
     surprising, that is itself the finding, not churn to ignore.

  2. Run the full test suite on the release commit, not on a branch tip and not on a
     merge-queue head. The point is to test the exact tree that will be tagged.

  3. Rehearse the rollback on a staging copy: deploy the candidate, then roll back,
     then confirm the previous version still serves. Rehearsal must precede the tag,
     because after the tag the previous build is already being evicted from the
     staging fleet and the rehearsal stops being meaningful.

  4. Write the changelog entry before the tag, so the tag points at text that
     already exists. Writing the changelog afterwards reliably produces a release
     described by whatever was remembered at the end rather than by what shipped.

  5. Tag, push the tag, and announce in the channel with the exact commit hash.
     Announcing a branch name instead of a hash is the single most common way an
     announcement becomes stale within the hour.

Verification. The release is complete only when step 3 has a recorded rehearsal
naming the version pair (previous, candidate). A checklist with step 3 skipped is a
deploy, not a release, and should be labelled as such in the announcement.

Failure modes. The common trap is rehearsing rollback after the tag, when the
previous version has already left staging. The second trap is treating a green unit
suite as step 2 while skipping the integration jobs, which is where release-blocking
failures actually live.

Estimated effort. Step 3 is the only one that costs real time; on a service with a
simple deploy it is under fifteen minutes, and it is the step that has caught the
most defects in practice.
""")

add("skill", "S-2", "Failing-test triage", """
SKILL S-2 -- Triage a failing test

When to use. A test that passed before now fails and the cause is not obvious from
the output. Do not use this for a test that has never passed; that is authoring, not
triage.

Steps.

  1. Reproduce locally from a clean checkout at the failing commit. Running against a
     dirty tree reproduces your working state, which is not the state that failed.

  2. Establish determinism. Run the test five times. A test that fails under half
     the runs is a flake until proven otherwise, regardless of how suspicious the
     stack trace looks.

  3. For a suspected flake, check ordering assumptions first. Tests sharing a
     module-level cache, a fixed port, or a fixed clock fail depending on order and
     timing rather than on code. Re-running the suite with a randomised order and
     with the suspect test isolated distinguishes these two worlds cheaply.

  4. Only after ordering and determinism are ruled out, bisect the commits. Bisection
     is a search over a space that only makes sense when the failure is a function of
     the commit.

Verification. You can name the mechanism, not merely the culprit commit. "Fixed at
commit abc123" is not a diagnosis; "the cache is populated by an earlier test and
never cleared" is.

Failure modes. The classic failure is bisecting a flake; five bisections of a flake
yield five random commits and a false sense of precision. The second is trusting a
stack trace that points at line numbers shifted by a local change.

Time budget. If steps 1-3 have not localised the failure within an hour, escalate
with what you ruled out rather than bisecting blindly.
""")

add("skill", "S-3", "Prepare a change for review", """
SKILL S-3 -- Prepare a change for review

When to use. A change is functionally complete and you want it reviewed efficiently.
Apply it before requesting review, not after the reviewer has started.

Steps.

  1. Split mechanical churn into its own commit: formatting, renames, import
     reordering, generated code. The reviewer then reads only semantic hunks in the
     main commit, and a large but safe diff stops masking a small risky one.

  2. Write the description as three explicit sections: what changes, why now, and
     what you deliberately did not change. The third section is the one reviewers
     value most because it tells them where not to look.

  3. State the blast radius plainly: how many users or callers this touches, which
     downstream systems read the data, and whether a rollback is available.

  4. Pre-empt the two questions a reviewer is most likely to ask. If you can predict
     them, answer them in the description; if you cannot predict them, that is a sign
     the change's intent is not yet clear even to you.

Verification. The reviewer asks no question that the description already answers,
and the review has fewer rounds than the same author's previous change.

Failure modes. A mixed commit forces the reviewer to diff noise and they stop
reading carefully, which is worse than not reviewing at all. Descriptions that
narrate the implementation ("refactored X, renamed Y") without stating the why get
reviewed as if the why were obvious, and it rarely is.

Note on size. A change that genuinely cannot be split is usually two changes. Ask
whether the mechanical half could ship first.
""")

# ------------------------------- MEMORY (3) ------------------------------
add("memory", "M-1", "Cron retry and backoff policy", """
MEMORY M-1 -- Retry policy for scheduled jobs

Where this comes from. cron/policy.yaml, owned by the data platform group. This note
records the convention as it is applied, not the file's literal contents; when the
two disagree the file wins and this note is stale.

Policy for jobs scheduled by cron, on a non-zero exit:

  * Retry on an exponential schedule starting at 60 seconds and doubling each
    attempt, capped at 30 minutes between attempts.
  * Maximum of 5 attempts. After the fifth failure the job is marked dead and pages
    the owning group. The dead marking is what stops a morning page storm from
    becoming an all-day one.
  * Do NOT retry a non-zero exit that is a policy refusal (exit code 42). Those are
    deterministic refusals -- the input is ineligible, not the machine unlucky --
    and paging on the first occurrence is the correct action.
  * The backoff counter is reset only by a manual clear. Restarting the scheduler
    does not clear it; a restart is not an attempt at the work.
  * The 30-minute cap is the interval makeover target, not an error threshold.

Scope. This applies to cron-scheduled jobs only. Request-driven services use a
request budget rather than a retry schedule and are covered by a different document;
applying this table to an HTTP handler produces retries that nobody budgeted for.

Known exception. The weekly warehouse compactor opts out of the 5-attempt cap and
retries until its window closes, because a compactor that gives up mid-window leaves
an inconsistent table. Its page still fires on the fifth failure; it simply keeps
retrying behind the page.

History. The cap was raised from 3 to 5 after the ingest outage, where the third
attempt landed during a network window and the job died one attempt short.
""")

add("memory", "M-2", "Registry mirror conventions", """
MEMORY M-2 -- Internal registry mirror notes

What the mirror is. Every build pulls images and packages through an internal mirror
rather than from upstream. The mirror caches on first request and serves subsequent
requests locally.

Conventions that matter day to day:

  * Pinning by tag alone is not pinning. Tags in the mirror can be re-pointed when
    the upstream tag moves, so reproducible builds pin by digest. A build that
    mentions only a tag may resolve differently tomorrow with no error.
  * The mirror does not cache negative results. A missing artifact is re-checked
    against upstream every time, which is correct behaviour and also why a broken
    upstream token shows up as slow builds rather than as failures.
  * Retention is 90 days for unused artifacts, measured from last pull, not from
    last push. An artifact nobody has pulled in 90 days is evicted and re-fetched
    from upstream on the next request.
  * The mirror is read-only for build hosts. Pushing from a build host fails
    authorisation and is deliberate.

Failure modes. The most common outage cause is a full mirror disk, which surfaces to
builders as timeouts rather than as registry errors. If many builds fail at once,
check mirror health before bisecting individual pipelines.

What this note does NOT cover. The access control list, the on-call rotation, and the
capacity plan are elsewhere. Do not quote retention numbers from this note for
anything except the mirror.
""")

add("memory", "M-3", "Key rotation procedure notes", """
MEMORY M-3 -- Credential rotation notes

Scope. Notes from the last two rotation exercises, kept because the same three
surprises recur every time.

What happened, in order of cost:

  * Rotation and deployment are not independent. Rotating a key while an old
    deployment is still serving produces a window where the old pod reads with the
    retired credential. The correct order is: deploy the reader that accepts both,
    rotate, then deploy the reader that accepts only the new one.

  * Long-lived connections do not re-authenticate. A pooled database connection
    opened before the rotation keeps working until it is recycled, so a rotation that
    "went fine" can fail ninety minutes later when the pool turns over. Force a pool
    recycle after every rotation rather than waiting to observe it.

  * The emergency path must be tested on a normal day. Both rotations lost time to
    the break-glass credential being stored in a place the responder did not expect.
    That is a documentation defect, not a security defect, but it cost the most
    wall-clock time of anything in the exercise.

Conventions adopted afterwards:

  * Rotate on a schedule, never in response to an incident. An incident rotation is
    two changes at once.
  * Record the rotation in the same place the reader is documented. A rotation
    recorded only in a ticket is lost at the next rotation.

Non-goals. This note deliberately contains no key material, no paths to key
material, and no intervals; those live with the owning system.
""")

# ----------------------------- KNOWLEDGE (3) -----------------------------
add("knowledge", "K-1", "Queue internals notes", """
KNOWLEDGE K-1 -- Queue abstraction notes

Segmentation. The queue is segmented by time, not by key. Each segment is sealed when
it reaches a size target and a new segment is opened. Readers hold handles to two
segments in the normal case: the sealed one they are draining and the open one they
are following. This is why a reader's memory footprint is roughly twice the segment
size regardless of how much data the reader has actually consumed.

Swap semantics. Rebuilding a segment copies it into a staging path and then swaps it
in. Readers never observe a partially written segment. They may, however, observe the
old segment for a short window after the swap, so a rebuild is not a way to
immediately remove data from a reader's view.

Long polls. A long poll parks for up to 30 seconds. A parked reader that wakes to an
empty segment re-parks immediately. This is why idle consumers look busy in metrics:
parking and re-parking are indistinguishable from work at the poll layer, and a
consumer group with no traffic still shows a steady poll rate.

Backpressure. Backpressure is applied at the producer. Producers are never dropped,
only slowed, because dropping at the queue boundary loses the ordering guarantee that
the rest of the system depends on. The practical consequence is that a wedged
consumer always shows up first as rising producer latency rather than as an error
anywhere, so the first place to look for a consumer problem is the producer's
dashboard.

Do not. Do not treat the segment size as a throughput knob. Segments are sized for
read amplification, not for throughput, and shrinking them multiplies the number of
sealed segments a reader must hold.
""")

add("knowledge", "K-2", "Log retention and tiers", """
KNOWLEDGE K-2 -- Log retention across storage tiers

How the tier is chosen. Retention is set per storage tier, and the tier is determined
by the producing service's classification label, not by log volume, not by the name of
the service, and not by what the logs contain. A high-volume log from a tier:standard
service costs more but is still retained for the standard period.

Tier limits.

  * tier interactive -- 7 days. Meant for debugging in-flight incidents only.
  * tier standard    -- 30 days.
  * tier compliance  -- 400 days. This is the tier that reconciliation windows run
    against; the annual reconciliation window is the reason the number is 400 and
    not 365, since the window may be opened late. Do not shorten it.

The backfill tier is deliberately not in the table above. It holds 100 days and is
described separately because it also carries a different export path, a different
access control list, and a nightly export job. Quoting the standard tier limit for a
backfill log is a common and expensive mistake: 30 days is not the limit for
backfill, and a backfill log older than 30 days is still present and readable.

Backfill tier detail. Retention is 100 days. Export runs nightly to cheap storage;
the export path depends on shard count and is written into a manifest beside the
export, so the path is discovered, never guessed. Access requires the analytics role;
the standard read role is not sufficient, which is why a reader who can see every
other tier's logs gets an empty page for backfill and assumes the data is gone.

Changing a tier. Changing a producer's classification label does not retroactively
change retention of logs already written; the log store keeps what was written under
the old label until it ages out.
""")

add("knowledge", "K-3", "Search index rebuild notes", """
KNOWLEDGE K-3 -- Search index rebuild notes

What a rebuild is. The search index is rebuilt nightly from the source of truth.
A rebuild streams source rows, chunks them, embeds the chunks, and writes new
segments. Old segments are deleted only after the new ones are marked healthy, so a
rebuild is always atomic from a reader's perspective: a query sees the old index or
the new one, never a mixture.

Why rebuild time grows superlinearly. Rebuild time scales with the number of chunks,
and the chunk count scales with average document length. Longer documents therefore
hurt rebuild time before they hurt query latency, and the relationship is worse than
linear because longer documents also produce more overlapping chunks. Teams that
optimise query latency by shortening chunks make rebuilds slower, not faster.

Staleness. Between rebuilds the index lags the source. The lag is bounded by the
rebuild interval, so the index is at most one day stale for rows written after the
last rebuild began. Anything that needs fresher reads must query the source
directly; there is no incremental update path at this layer, and a "quick partial
rebuild" is not supported.

Failure handling. A rebuild that fails partway leaves the previous index in place.
Nothing is served from the half-built segments, and the failure is reported in the
rebuild notification rather than on the search side, which is why search dashboards
stay green through a failed rebuild.

Do not. Do not trigger a rebuild to fix a single wrong document. The whole index is
rebuilt or nothing is, and a rebuild for one row costs the same as a rebuild for the
whole corpus.
""")

def main():
    out = pathlib.Path(__file__).parent / "corpus"
    out.mkdir(parents=True, exist_ok=True)
    (out / "items.json").write_text(
        json.dumps({"items": ITEMS}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest, total = [], 0
    for it in ITEMS:
        raw = it["body"].encode("utf-8")
        (out / f"{it['id']}.txt").write_bytes(raw)
        total += len(it["body"])
        manifest.append({"id": it["id"], "kind": it["kind"],
                         "chars": len(it["body"]), "bytes": len(raw),
                         "sha256": hashlib.sha256(raw).hexdigest()})
    (out / "MANIFEST.json").write_text(json.dumps(
        {"items": manifest, "total_chars": total,
         "counts_by_kind": {k: sum(1 for m in manifest if m["kind"] == k)
                            for k in ("tool", "skill", "memory", "knowledge")}},
        indent=2) + "\n", encoding="utf-8")

    print(f"items={len(ITEMS)} total_chars={total}")
    for m in manifest:
        print(f"  {m['kind']:10s} {m['id']:4s} {m['chars']:6d} {m['sha256']}")


if __name__ == "__main__":
    main()
