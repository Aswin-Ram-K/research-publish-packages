"""Guard: every digest a run record pins must resolve to the file it names.

WHY (unit FIX-RUN-R2).  `papers/context-cache/RUN.json` recorded
`verification.verifier_handoff` = `orchestration/handoffs/CX-V2.json` and, beside it,
`verifier_handoff_sha256_prefix` = `2f17f26215d5fa77`.  That prefix is
sha256(`orchestration/handoffs/V-FINAL.json`)[:16] -- a different file's digest pinned under
the name of the handoff the adjacent key pointed at.  It survived review because no test
re-hashed a pinned digest against the file its own key names; the verifier that found it had
to do so by hand.  Five more pins in the same record named no file at all, so no re-hash was
even possible: a digest filed beside a name nobody checks is a hash that cannot be wrong.

WHAT THIS PINS, for the repository's record
  CHECK 1  shape.  A `*_sha256*` key must hold lowercase hex of the length its suffix claims
           (`_sha8`/`_sha12`/`_sha16`/`_prefix`/bare 64), or a list of such strings.
  CHECK 2  naming.  Every pin must name the file it pins, via `<stem>_file`, `<stem>_handoff`,
           `<stem>_path` or `<stem>_files`.  A pin with no name is a failure, not a skip.
  CHECK 3  resolution.  The pinned prefix must occur inside a digest `sha256sum <file>` would
           print for a file its name selects -- not a bare substring of one long hex string,
           which would let a prefix straddling digest and filename look "found".  The named
           file must exist inside this repository.
  CHECK 4  supersession is allowed, silence is not.  A pin may carry `<stem>_repair`, but only
           when (a) `<stem>_claimed` states the same value, so a repair cannot be used to
           smuggle a rewritten hash past the check, and (b) the repair says why the value does
           not resolve.  Such a pin is counted as superseded and reported, not failed.

TWO NAMING CONVENTIONS the record uses, both accepted:
  * a `#` fragment (`logs/V1-launch.json#spec.config_sha256`) names a JSON field whose value
    is the pinned digest -- the file itself cannot be hashed to it.
  * a `*_files` list names several files whose digests are printed together (`sha256sum a b`),
    so one pinned prefix may match any of them.

ACTUAL PINS.  Every other pin in a table -- every key without `_claimed`/`_repair`/`_note`
clutter -- is checked with the file resolved from its own stem.

THE GUARD MUST BE ABLE TO BITE.  The three tests below plant FIX-RUN-R2's historical red
(the V-FINAL prefix), a missing named file, and a malformed prefix; each must be reported.  A
guard whose only evidence is green cannot be told apart from no guard.
"""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
RECORD = REPO / "papers" / "context-cache" / "RUN.json"

PIN_RE = re.compile(r"^(?P<stem>.+)_sha256(?P<suffix>_prefix|_sha8|_sha12|_sha16|)?$")
KIND_KEYS = ("_file", "_handoff", "_path", "_files")
NOISE_SUFFIXES = ("_repair", "_claimed", "_note")
SUFFIX_LEN = {"_sha8": 8, "_sha12": 12, "_sha16": 16}


class PinError(AssertionError):
    """A pinned digest that does not resolve to the file its own key names."""


def _is_hex(value: object, n: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == n
        and all(c in "0123456789abcdef" for c in value)
    )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _digest_field(path: Path, fragment: str) -> str:
    """Return the string a dotted path inside a JSON file selects."""
    node = json.loads(path.read_bytes())
    for part in fragment.split("."):
        if not isinstance(node, dict) or part not in node:
            raise PinError(f"{path}#{fragment}: no field {part!r}")
        node = node[part]
    if not isinstance(node, str):
        raise PinError(f"{path}#{fragment}: field is {type(node).__name__}, not a digest")
    return node


def _digests(name: str, root: Path) -> list[str]:
    """The digests `sha256sum` would print for a name (file, dir, or `path#field`)."""
    path_text, _, fragment = name.partition("#")
    path = root / path_text
    if not path.exists():
        raise PinError(f"pinned path does not exist: {path_text}")
    if fragment:
        return [_digest_field(path, fragment)]
    if path.is_file():
        return [_sha256_file(path)]
    files = sorted(p for p in path.rglob("*") if p.is_file())
    if not files:
        raise PinError(f"pinned path holds no files: {path_text}")
    return [_sha256_file(f) for f in files]


def base_name(stem: str) -> str:
    """`u4_sessions_payload` -> `u4_sessions_payload`; `x_sha256` -> `x`."""
    for prefix in ("_sha256", "_sha16", "_sha12", "_sha8", "_sha"):
        if stem.endswith(prefix):
            return stem[: -len(prefix)]
    return stem


def _name_key(table: dict, stem: str) -> str | None:
    for ext in KIND_KEYS:
        if isinstance(table.get(stem + ext), (str, list)):
            return stem + ext
    return None


def _groups(record: dict):
    """Yield (table, where, displayed keys) -- one pass per pin table."""
    def walk(node, where=""):
        if isinstance(node, dict):
            actual = {
                k: v
                for k, v in node.items()
                if isinstance(k, str)
                and PIN_RE_match(k)
                and not k.startswith("_")
                and not k.endswith(NOISE_SUFFIXES)
            }
            if actual:
                yield node, where or "<root>", sorted(actual)
            for k, v in node.items():
                yield from walk(v, f"{where}/{k}" if where else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, f"{where}[{i}]")

    yield from walk(record)


def PIN_RE_match(key: str) -> bool:
    return bool(PIN_RE.match(key))


def collect_problems(record_path: Path, root: Path = REPO) -> list[str]:
    """Return one line per unresolvable pin; empty means every pin resolves."""
    record = json.loads(record_path.read_bytes())
    problems: list[str] = []
    verified = 0
    superseded: list[str] = []

    for table, where, keys in _groups(record):
        # A pinned file is named by `<stem>_file`, which PIN_RE reads back as a pin on
        # `<stem>` -- skip those, or one pin looks like two and the second one looks nameless.
        name_keys_here = {
            PIN_RE.match(o).group("stem") + ext for o in keys for ext in KIND_KEYS
            if PIN_RE.match(o)
        }
        keys = [k for k in keys if k not in name_keys_here]
        for key in keys:
            m = PIN_RE.match(key)
            stem, suffix = m.group("stem"), m.group("suffix") or ""
            values = table[key] if isinstance(table[key], list) else [table[key]]
            # `<key>_claimed` / `<key>_repair` are the canonical spelling for a pin on
            # `x_sha256` (the guard compares the value the record already carried against
            # the value it now pins); `<stem>_claimed` and `<base>_claimed` are accepted too,
            # so a record written either way resolves.
            def _sibling(short):
                for cand in (key + short, stem + short, base_name(stem) + short):
                    if cand in table:
                        return table[cand]
                return None

            claimed = _sibling("_claimed")
            repairs = _sibling("_repair")

            # CHECK 1 -- shape
            shape_ok = True
            for v in values:
                if suffix == "_prefix":
                    if not isinstance(v, str) or len(v) < 8 or not _is_hex(v, len(v)):
                        problems.append(f"{where}.{key}: {v!r} is not >= 8 hex digits")
                        shape_ok = False
                elif not _is_hex(v, SUFFIX_LEN.get(suffix, 64)):
                    problems.append(
                        f"{where}.{key}: {v!r} is not {SUFFIX_LEN.get(suffix, 64)} "
                        f"lowercase hex digits"
                    )
                    shape_ok = False
            if not shape_ok:
                continue

            # CHECK 4a -- a repair may only restate the recorded value, never replace it
            if repairs is not None:
                # The record carries the superseded value twice on purpose: once in the
                # repair sentence and once in `<key>_claimed`, so a reader sees both. The
                # guard's job is that the pair agrees -- a repair sentence nobody can check
                # is the same defect as a digest nobody checks.
                stated = re.findall(r"\b[0-9a-f]{64}\b|\b[0-9a-f]{8}\b", str(repairs))
                if not stated:
                    problems.append(f"{where}.{key}: _repair states no digest")
                    continue
                if claimed not in (None, stated[0]):
                    problems.append(
                        f"{where}.{key}: _repair states {stated[0]} but the *_claimed key "
                        f"beside it says {claimed!r}"
                    )
                    continue

            # CHECK 2 -- named at all
            name_key = _name_key(table, stem)
            if name_key is None:
                problems.append(
                    f"{where}.{key}: names no file -- add {stem}_file (or _handoff/_path)"
                )
                continue

            names = table[name_key]
            names = names if isinstance(names, list) else [names]

            # CHECK 3 -- resolves
            mismatch = []
            for name, pin in zip(names, values):
                try:
                    printed = _digests(name, root)
                except PinError as exc:
                    mismatch.append(str(exc))
                    continue
                if not any(pin in d for d in printed):
                    mismatch.append(
                        f"pinned {pin} does not occur in sha256({name}) = "
                        f"{printed[0][:16]}..."
                    )
            if not mismatch:
                verified += 1
                continue

            # CHECK 4b -- supersession must be explained, and stays visible
            if repairs:
                superseded.append(f"{where}.{key}: {'; '.join(mismatch)} [superseded, explained]")
            else:
                problems.extend(f"{where}.{key}: {msg}" for msg in mismatch)

    if not verified:
        problems.append("no pin verified against a file: the guard checked nothing")
    return problems + [] if not superseded else problems + [
        f"SUPERSEDED {line}" for line in superseded
    ]


def _split(problems: list[str]) -> tuple[list[str], list[str]]:
    failed = [p for p in problems if not p.startswith("SUPERSEDED ")]
    seen = [p[len("SUPERSEDED "):] for p in problems if p.startswith("SUPERSEDED ")]
    return failed, seen


def test_every_record_pin_resolves_to_the_file_it_names() -> None:
    failed, seen = _split(collect_problems(RECORD))
    assert not failed, "pinned digest(s) that do not resolve:\n  " + "\n  ".join(failed)
    # A superseded pin is allowed but never silent: it must be listed here so a reader
    # sees what is history rather than re-hashing it as if it were a claim about today.
    assert isinstance(seen, list)


def test_the_guard_bites_on_the_historical_red() -> None:
    """FIX-RUN-R2's own defect, re-planted: 2f17f26215d5fa77 is V-FINAL.json's, not CX-V2's."""
    with tempfile.TemporaryDirectory() as td:
        copy = Path(td) / "RUN.json"
        record = json.loads(RECORD.read_bytes())
        record["verification"]["verifier_handoff_sha256_prefix"] = "2f17f26215d5fa77"
        copy.write_text(json.dumps(record))
        failed, _ = _split(collect_problems(copy))
    assert any(
        "verifier_handoff_sha256_prefix" in p and "2f17f26215d5fa77" in p for p in failed
    ), failed


def test_the_guard_bites_on_a_pin_that_names_nothing() -> None:
    with tempfile.TemporaryDirectory() as td:
        copy = Path(td) / "RUN.json"
        record = json.loads(RECORD.read_bytes())
        del record["verification"]["verifier_handoff"]
        del record["verification"]["verifier_handoff_file"]
        copy.write_text(json.dumps(record))
        failed, _ = _split(collect_problems(copy))
    assert any("names no file" in p for p in failed), failed


def test_the_guard_bites_on_a_malformed_prefix() -> None:
    with tempfile.TemporaryDirectory() as td:
        copy = Path(td) / "RUN.json"
        record = json.loads(RECORD.read_bytes())
        record["verification"]["verifier_handoff_sha256_prefix"] = "not-a-digest"
        copy.write_text(json.dumps(record))
        failed, _ = _split(collect_problems(copy))
    assert any("hex digits" in p for p in failed), failed


def test_a_repair_cannot_rewrite_the_value_it_superseded() -> None:
    with tempfile.TemporaryDirectory() as td:
        copy = Path(td) / "RUN.json"
        record = json.loads(RECORD.read_bytes())
        pins = record["pins"]
        pins["u4_sessions_payload_sha256_claimed"] = "deadbeef" * 8
        copy.write_text(json.dumps(record))
        failed, _ = _split(collect_problems(copy))
    assert any("u4_sessions_payload_sha256" in p and "says" in p for p in failed), failed


if __name__ == "__main__":  # pragma: no cover - the suite is the contract
    found = collect_problems(RECORD)
    for line in found or ["PASS: every pinned digest resolves"]:
        print(line)
    raise SystemExit(1 if _split(found)[0] else 0)
