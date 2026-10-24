# UFIXPKG8 — apply proven P-family tag-regex patch to live copies

## Purpose
The live tag regex `^(?:K|F|S|C|R|D)[0-9][0-9]$|^TAG_[0-9][0-9]$` rejects the `P` family
(`P01`–`P05`) that this project actually mints and ships, so the validator cannot validate
its own material. A prior unit (ufixpkg7) proved the corrected form on a copy at
`scratch/ufixpkg7/tag_re_control.py`:

    ^(?:K|F|S|C|R|D|P)[0-9][0-9]$|^TAG_[0-9][0-9]$

This unit applies that proven form to **every live copy** of the regex (not just the two
named), adds a regression test (P tag recognised / arbitrary word rejected), runs the suite,
and produces a red→green control on the live files.

## Hard bound
15 tool calls. Stop and report `partial` if the live copies cannot all be identified.

## Declared write paths (exactly these)
- orchestration/units/UBUILD1.build.sh
- strategy/OUTSIDE_TOKEN_REDACTION.md
- tests/**
- orchestration/units/UFIXPKG8.md
- orchestration/handoffs/UFIXPKG8.json
- scratch/ufixpkg8/**

## Constraints
- `/home/zer0null/Duval` strictly read-only; never run any `git` command against it.
- No installs, no network fetches, no real release destination; builds only under `scratch/**`.
- No new number not read from disk or measured. Every before-string asserted to occur exactly once.
- Do not weaken any other guard.

## Proof to produce
- red→green control on the **live** files (P tag unrecognised before, recognised after), non-vacuity stated.
- before/after for every file touched with occurrence counts.
- suite result + tests added; rejection of an arbitrary word demonstrated.
- handoff `orchestration/handoffs/UFIXPKG8.json`, re-parsed before finishing.
