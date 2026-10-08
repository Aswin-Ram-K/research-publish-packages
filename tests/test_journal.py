"""Offline tests for :mod:`resextract.journal` (fixtures are local; no conftest).

Covers append ordering + monotonic ``seq``, chain verification, tamper
detection with the correct ``first_bad_seq``, and redaction of both
secret-named keys and secret-shaped values.
"""

from __future__ import annotations

import json
import re

import pytest

from pathlib import Path

from resextract import journal


# Synthetic secret-shaped fixtures, assembled at runtime from non-secret-shaped
# pieces so this file's bytes do not match the commit scanner (see
# docs/SECRET_SCAN_POLICY.md).  The runtime values keep the realistic shapes the
# redaction tests exercise.
_FAKE_API_KEY = "sk-" + "A7qZ" * 5        # 23 chars: sk- + 20 alnum
_FAKE_ACCESS_TOKEN = "okr_" + "R2mB" * 5  # 24 chars: okr_ + 20 alnum


@pytest.fixture()
def root(tmp_path):
    return tmp_path / "journal"


def test_append_order_and_seq_monotonic(root):
    j = journal.Journal("run-1", root)
    first = j.append("run.start", target="duval")
    second = j.append("llm.call", model="occamy-1.0", tokens_used=12)
    third = j.append("run.end", status="done")

    assert [first["seq"], second["seq"], third["seq"]] == [1, 2, 3]
    assert first["prev"] == ""
    assert second["prev"] == first["hash"]
    assert third["prev"] == second["hash"]
    assert first["ts"].endswith("Z") and second["kind"] == "llm.call"

    entries = list(journal.read("run-1", root=root))
    assert [e["seq"] for e in entries] == [1, 2, 3]
    assert [e["kind"] for e in entries] == ["run.start", "llm.call", "run.end"]
    assert [e["seq"] for e in journal.read("run-1", since_seq=1, root=root)] == [2, 3]
    assert journal.verify("run-1", root=root) == (True, None)
    assert (root / "run-1.jsonl").exists()


def test_journal_is_one_file_per_run(root):
    journal.append("a", "x", root=root)
    journal.append("b", "x", root=root)
    assert sorted(p.name for p in root.glob("*.jsonl")) == ["a.jsonl", "b.jsonl"]
    assert journal.verify("a", root=root) == (True, None)
    assert journal.verify("b", root=root) == (True, None)


def test_reserved_field_names_are_rejected(root):
    j = journal.Journal("run-1", root)
    with pytest.raises(ValueError, match=r"reserved keys: \['seq'\]"):
        j.append("x", seq=99)
    with pytest.raises(ValueError, match=r"reserved keys: \['hash'\]"):
        j.append("x", hash="deadbeef")


def test_verify_missing_run_is_not_ok(root):
    ok, bad = journal.verify("never-written", root=root)
    assert ok is False and bad is None


def test_tampering_is_detected_with_first_bad_seq(root):
    """RED→GREEN guard: hash-chain tamper detection (test_journal.py).

    Reverted guard — ``verify()`` trusting the stored ``hash`` instead of
    recomputing it (``if False:  # REVERTED GUARD``).  Real captured output of
    ``pytest tests/test_journal.py::test_tampering_is_detected_with_first_bad_seq
    tests/test_doctor.py::test_optional_leg_cannot_fail_the_doctor -q`` with that
    guard reverted (full log: ``state/logs/U0.3-redgreen.txt``)::

        FF                                                                   [100%]
        ________________ test_tampering_is_detected_with_first_bad_seq _________________
        ...
            ok, first_bad = journal.verify("run-tamper", root=root)
        >       assert ok is False
        E       assert True is False

        tests/test_journal.py:96: AssertionError
        =========================== short test summary info ============================
        FAILED tests/test_journal.py::test_tampering_is_detected_with_first_bad_seq
        2 failed in 0.02s

    Restoring the guard turns this test green (see ``state/logs/U0.3-pytest.txt``).
    """
    j = journal.Journal("run-tamper", root)
    j.append("one")
    j.append("two", value=2)
    j.append("three", value=3)

    path = root / "run-tamper.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[1])
    entry["value"] = 999  # tamper with the middle line, leaving its hash stale
    lines[1] = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ok, first_bad = journal.verify("run-tamper", root=root)
    assert ok is False
    assert first_bad == 2

    # Deleting the first line is caught as a seq/prev violation too.
    path.write_text("\n".join(lines[1:]) + "\n", encoding="utf-8")
    ok, first_bad = journal.verify("run-tamper", root=root)
    assert ok is False and first_bad == 2


def test_redaction_of_secret_named_keys(root):
    entry = journal.append(
        "redact-keys",
        "llm.call",
        root=root,
        api_key=_FAKE_API_KEY,
        Authorization="Bearer abcdefghijklmnop",
        nested={"password": "hunter2", "client_secret": "topsecretvalue"},
        access_token=_FAKE_ACCESS_TOKEN,
        tokens_used=1234,
        model="occamy-1.0",
    )
    assert entry["api_key"] == journal.REDACTED
    assert entry["Authorization"] == journal.REDACTED
    assert entry["nested"]["password"] == journal.REDACTED
    assert entry["nested"]["client_secret"] == journal.REDACTED
    assert entry["access_token"] == journal.REDACTED
    assert entry["tokens_used"] == 1234  # metering survives: "tokens" is not "token"
    assert entry["model"] == "occamy-1.0"

    raw = (root / "redact-keys.jsonl").read_text(encoding="utf-8")
    for needle in ("hunter2", "topsecretvalue", _FAKE_API_KEY, _FAKE_ACCESS_TOKEN):
        assert needle not in raw
    assert journal.verify("redact-keys", root=root) == (True, None)
    assert json.loads(raw)["api_key"] == journal.REDACTED


def test_redaction_of_secret_shaped_values_under_innocent_keys(root):
    base64_blob = "QWxsIHlvdXIgYmFzZTY0IGFyZSBiZWxvbmcgdG8gdXM="  # 48 chars, base64ish
    sha256_hex = "a" * 64  # legitimate digest: pure hex must NOT be redacted
    entry = journal.append(
        "redact-values",
        "fetch",
        root=root,
        note="used " + _FAKE_API_KEY + " to login",
        blob=base64_blob,
        digest=sha256_hex,
        url="https://example.org/page",
    )
    assert journal.REDACTED in entry["note"]
    assert _FAKE_API_KEY not in entry["note"]
    assert entry["blob"] == journal.REDACTED
    assert entry["digest"] == sha256_hex
    assert entry["url"] == "https://example.org/page"

    raw = (root / "redact-values.jsonl").read_text(encoding="utf-8")
    assert base64_blob not in raw and _FAKE_API_KEY not in raw
    assert journal.verify("redact-values", root=root) == (True, None)


def test_redaction_handles_lists_and_non_strings(root):
    entry = journal.append("redact-list", "tool.call", root=root, args=["plain", {"api_key": "x"}, 7, None])
    assert entry["args"][0] == "plain"
    assert entry["args"][1]["api_key"] == journal.REDACTED
    assert entry["args"][2] == 7 and entry["args"][3] is None


def test_run_id_is_path_safe(root):
    entry = journal.append("../../etc/passwd", "x", root=root)
    assert entry["seq"] == 1
    assert list(root.glob("*.jsonl"))[0].parent == root
    assert ".." not in list(root.glob("*.jsonl"))[0].name


# The two value-shape patterns the commit scanner applies to staged bytes.
_SCANNER_SHAPES = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),   # provider API key
    re.compile(r"okr_[A-Za-z0-9]{16,}"),    # Occamy run/access token
)


def test_test_sources_carry_no_literal_secret_shapes():
    """Guard: no scanner-matching secret shape may sit literally in the test sources.

    RED->GREEN PROOF (guard is not vacuous): a literal fixture was temporarily
    reintroduced and this test failed with::

        AssertionError: literal secret shape(s) on disk: test_journal.py:219 shape[0] (values withheld)

    Restoring the runtime-assembled fixture made it pass again.  The failure text
    names only file, line and pattern index -- never the matched value -- so
    pasting it here cannot itself reintroduce a matching shape.
    """
    here = Path(__file__).resolve()
    problems = []
    for path in (here, here.parent / "test_occamy_client.py"):
        text = path.read_text(encoding="utf-8")
        for index, pattern in enumerate(_SCANNER_SHAPES):
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"{path.name}:{line} shape[{index}]")
    if problems:
        raise AssertionError(
            "literal secret shape(s) on disk: " + ", ".join(problems) + " (values withheld)"
        )
    # The fixtures must still be secret-shaped at runtime, or the tests prove nothing.
    assert any(p.match(_FAKE_API_KEY) for p in _SCANNER_SHAPES)
    assert any(p.match(_FAKE_ACCESS_TOKEN) for p in _SCANNER_SHAPES)
