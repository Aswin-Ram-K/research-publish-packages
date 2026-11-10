# Arms (campaign)

## A — verbatim append-only history
- Hypothesis: re-emitting every earlier observation byte-identically maximises prefix-cache reuse.
- Trade: largest prompt; no compression.
- Prefix behaviour: fully prefix-stable (turn N text is a byte prefix of turn N+1).

## B — append-only typed event records
- Stable header (system preamble) + content-addressed full bodies. Each body is inlined on first appearance and referenced via `#body:<sha256>` thereafter within a render; across turns earlier records are never rewritten.
- Trade: typed records add overhead but enable exact body recovery.
- Prefix behaviour: fully prefix-stable.

## C — rolling observation masking with resolvable bodies
- Older observations replaced by `#body:<sha256>` + one-line gist; full body retrievable via body store. mask_after default 6 (no-op below).
- Trade: smaller prompt; breaks prefix stability.
- Prefix behaviour: not prefix-stable.

## D — bounded summary + raw bodies
- Older turns collapsed into a bounded summary; raw bodies remain recoverable.
- Trade: most compression; breaks prefix stability.
- Prefix behaviour: not prefix-stable.

## Information equality
"Information" = set of body digests resolvable in the store + the current question string (meta.current_question). All four arms store the same bodies and report the same current_question; verified by test_equal_task_information_at_turn_12.

## Body store
Content-addressed under arms/store/<aa>/<digest>. Missing/digest-mismatched resolve raises BodyMissing/DigestMismatch; never a placeholder. verify_all() checks every stored body.

## Gist policy (content-free)
Masked turns replace their body with a `#body:<digest>` reference plus a
structural gist only: `{"turn":N,"kind":"observation","bytes":B,"sha256_8":"..."}`.
The gist carries no task content (no expected values, no observations), so a
retrieval mechanism can be shown to matter. Verified by
test_gist_is_structural_and_content_free over D1..D4.

## GET recovery protocol
Uniform across all four arms (identical system preamble) for instruction parity:
some observations appear only as `#body:<digest>` with a structural gist. If the
model needs exact bytes, it replies with exactly one line `GET <digest>` and
nothing else; the body is supplied in the next message and it may then answer.
At most one such request per turn.

- `resolve_requests(output) -> list[str]`: parses and validates GET requests
  (64-hex + store presence); raises BodyMissing/DigestMismatch on unknown or
  tampered digests, never silently satisfies.
- `recovery_message(digest) -> dict`: returns the message supplying the verified
  body; raises BodyMissing/DigestMismatch on mismatch.

A retrieval costs one extra dispatched model request and is part of C/D's
measured cost.

## Cache-namespace salting
`build_messages(..., salt=None)` inserts exactly one `session=<salt>` line into the
system preamble (after the fixed body, before the `ARM:` line) when a salt is
given; with `salt=None` no line is emitted (historical byte-for-byte).

Campaign salt convention: `csc-<run_id>-<task>-<seed>` — deliberately NOT
including the arm, so the four arms of a cell share a namespace; arm order is
counterbalanced instead of isolated. Flushing the shared SGLang radix cache is
forbidden; salt-level isolation is verifiable by the preflight cold/repeat/
divergence probe.

## Answer format line
Shared preamble ends with a uniform "Answer format: ..." line (identical in all arms)
instructing the model to end with a single `key=value` line; earlier tokens such as
`</think>` or markdown are ignored by the grader's final-line extraction.
