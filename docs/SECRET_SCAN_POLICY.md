# Secret-scan policy — commit gate

Decided in U0.6. The gate scans the **staged bytes** (`git diff --cached`) for six
patterns and refuses the commit if any matched value is not on the recorded set below.

| # | Pattern | Intended catch |
|---|---------|----------------|
| 1 | `sk-[A-Za-z0-9_-]{20,}` | provider API keys |
| 2 | `okr_[A-Za-z0-9]{16,}` | Occamy run / access tokens |
| 3 | `AKIA[0-9A-Z]{16}` | AWS access-key ids |
| 4 | `-----BEGIN [A-Z ]*PRIVATE KEY-----` | PEM private keys |
| 5 | `ghp_[A-Za-z0-9]{20,}` | GitHub personal access tokens |
| 6 | `Authorization: Bearer ` | bearer credentials in headers (marker, see below) |

## The rule is value-based, never path-based

For every match the gate extracts the matched text as a *candidate value* and looks it up
in the recorded set. The file's path is never consulted; no file and no directory is
exempt. Therefore:

- a recorded synthetic value is permitted **wherever it appears**, including inside a
  completed unit's evidence record;
- a real credential fails in **every** file — including the test files listed below —
  because its value is not on the set;
- a path-based exemption is out of policy. The only way to admit a value is to record it
  here (see *Changing the recorded set*).

Pattern 6 is a **marker, not a value**: its matched text is the header *name*, so it
carries no credential by itself. It is on the recorded set only so that code, tests and
evidence which name the header are not false positives; a credential placed after the
marker is still caught by patterns 1–5.

## Recorded set of known-synthetic fixture values

| Value | Len | Defined by | Why it exists |
|-------|-----|------------|---------------|
| `sk-A7qZA7qZA7qZA7qZA7qZ` | 23 | `tests/test_journal.py` — `_FAKE_API_KEY`, assembled at runtime | secret-shaped value under the secret-named key `api_key` and under the innocent key `note` (`test_redaction_of_secret_named_keys`, `test_redaction_of_secret_shaped_values_under_innocent_keys`) |
| `okr_R2mBR2mBR2mBR2mBR2mB` | 24 | `tests/test_journal.py` — `_FAKE_ACCESS_TOKEN`, assembled at runtime | a second prefix family, so the tests prove the shape list is not `sk-`-only |
| `sk-T3nWT3nWT3nWT3nWT3nWxYz` | 26 | `tests/test_occamy_client.py` — `_FAKE_API_KEY`, assembled at runtime | proves the key never reaches the trace or the metering record (`test_api_key_never_reaches_trace_or_metering`) while still being sent on the wire as `Bearer` |
| `sk-abcdefghijklmnopqrstuvwxyz0123456789` | 39 | `tests/test_docket_copy.py` and `tests/fixtures/copy-src/config/api.txt` (sibling unit, not touched here) | the synthetic fixture of the U0.3 store/docket redaction evidence ("0/5 chunks surviving under api_key/client_secret/token/innocent"), quoted in `orchestration/units/V0.md` and `orchestration/handoffs/V0.json`. Permitted **by value**; those records are never edited. |
| `Authorization: Bearer ` | 22 | none — structural marker | the header name named by pattern 6; quoted by U0.5's handoff and unit card |

## A completed unit's evidence record is never edited to satisfy the scanner

`orchestration/units/V0.md` and `orchestration/handoffs/V0.json` are a completed verifier's
evidence and stay byte-for-byte. When they contain a recorded synthetic value the commit
passes **by value**; if one of them ever contains a value that is not recorded, the correct
response is to investigate that value, never to rewrite the evidence.

## Changing the recorded set

Any addition or removal requires a handoff entry naming the new value and the test that
legitimises it, plus an update to this file. A value is admitted only when a test needs
that exact shape; "it is only a fixture" is not sufficient on its own.

## Source remediation (U0.6)

The fixture literals that previously sat in `tests/test_journal.py` and
`tests/test_occamy_client.py` (23, 24 and 26 characters) are now assembled at runtime from
non-secret-shaped pieces, so those files' bytes no longer match patterns 1–2 at all, while
the runtime values keep the shapes the tests exercise. Those superseded literal bytes are
defined by no file any more and are therefore deliberately **not** on the recorded set.

`tests/test_journal.py` additionally enforces the property:
`test_test_sources_carry_no_literal_secret_shapes` reads its own bytes and its sibling's and
fails on any literal match of patterns 1–2 (red→green proof in its docstring).
