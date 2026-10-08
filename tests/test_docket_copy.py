"""Unit tests for the material copy engine (U5.1).

Source-tree policy under test
-----------------------------
The copier treats the target repo as a strictly read-only, *symlink-hostile*
tree: **every** request whose path contains a symlink component is refused
(``refusal_reason="symlink"``), whether or not the link resolves inside the
root — links are never silently followed, because following a link inside the
docket tree is how a copy silently leaves its declared containment.  Alongside
that, secret refusal is two-layered (path shape *and* content shape) and runs
*before* the byte caps, so an over-cap or otherwise awkward path can never
smuggle a secret into ``material/``.

The fixture tree ``tests/fixtures/copy-src/`` is (re)built idempotently at
import time, so the suite is self-healing on a fresh checkout.
"""

from __future__ import annotations

import hashlib
import os
import stat
import time
from pathlib import Path

import pytest

from resextract.docket import copy as copy_mod
from resextract.docket.copy import (
    CopyIntegrityError,
    CopyRequest,
    Copier,
    is_binary,
    sha256_file,
)

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "copy-src"
MIB = 1024 * 1024


# ---------------------------------------------------------------------------
# fixture tree
# ---------------------------------------------------------------------------


def _write_if_missing(path: Path, data: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)
    os.chmod(path, mode)


def ensure_fixture_tree(root: Path = FIXTURE_ROOT) -> Path:
    """Idempotently build the copy-engine fixture tree."""
    root.mkdir(parents=True, exist_ok=True)
    _write_if_missing(root / "pkg" / "mod.py", b"VALUE = 42\n" + b"# normal source file\n")
    _write_if_missing(root / "pkg" / "run.sh", b"#!/bin/sh\necho hi\n", 0o755)
    _write_if_missing(root / "pkg" / "setuid.sh", b"#!/bin/sh\necho setuid\n", 0o4755)
    _write_if_missing(root / "data" / "small.json", b'{"a": 1, "b": [2, 3]}\n')
    _write_if_missing(root / "sub" / "note.md", b"# Sub note\n\nexcerpt me\n")
    _write_if_missing(root / "assets" / "fig.png",
                      b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")
    _write_if_missing(root / ".env", b"RESEXTRACT_DEMO_KEY=demo-not-a-real-secret\n")
    _write_if_missing(
        root / "config" / "api.txt",
        b"token = sk-abcdefghijklmnopqrstuvwxyz0123456789\n",
    )
    for name, fill in (("a.txt", b"a"), ("b.txt", b"b"), ("c.txt", b"c")):
        _write_if_missing(root / "cap" / name, fill * 1000)

    big = root / "data" / "big.bin"
    if not big.exists() or big.stat().st_size != 3 * MIB:
        big.parent.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha256(b"big.bin")
        chunks = []
        for i in range(3 * MIB // 32):
            h.update(i.to_bytes(8, "big"))
            chunks.append(h.digest())
        big.write_bytes(b"".join(chunks))

    escape = root / "escape"
    if not escape.is_symlink():
        if escape.exists():
            escape.unlink()
        escape.symlink_to("../../../../../../etc/hostname")
    inner = root / "inner"
    if not inner.is_symlink():
        if inner.exists():
            inner.unlink()
        inner.symlink_to("data/small.json")
    return root


ensure_fixture_tree()

#: sha256 + mtime_ns + mode of every fixture source, captured at import
_BASELINE = {
    p: (sha256_file(p), os.lstat(p).st_mtime_ns, os.lstat(p).st_mode)
    for p in sorted(FIXTURE_ROOT.rglob("*"))
    if p.is_file() and not p.is_symlink()
}


def _full_requests() -> list[CopyRequest]:
    f = FIXTURE_ROOT
    return [
        CopyRequest(str(f / "pkg" / "mod.py"), "pkg/mod.py", "normal text"),
        CopyRequest(str(f / "pkg" / "run.sh"), "pkg/run.sh", "executable script"),
        CopyRequest(str(f / "pkg" / "setuid.sh"), "pkg/setuid.sh", "setuid script"),
        CopyRequest(str(f / "data" / "small.json"), "data/small.json", "json"),
        CopyRequest(str(f / "assets" / "fig.png"), "assets/fig.png", "binary"),
        CopyRequest(str(f / "sub" / "note.md"), "sub/note.md", "excerpt",
                    excerpt=(3, 3)),
    ]


@pytest.fixture()
def docket(tmp_path):
    return tmp_path / "docket"


# ---------------------------------------------------------------------------
# byte-exactness
# ---------------------------------------------------------------------------


def test_byte_exactness_independent_rehash(docket):
    """Every ``copied`` item's destination re-hashes to its source sha256."""
    copier = Copier(FIXTURE_ROOT, docket)
    report = copier.execute(copier.plan(_full_requests()))

    assert report.copied, "expected at least one copied item"
    assert report.refused_count == 0 and report.missing_count == 0
    for item in report.copied:
        dest = copier.material_path(item.dest)
        # independent re-hash, deliberately not report.verified
        assert sha256_file(dest) == sha256_file(item.src), item.dest
        assert os.path.getsize(dest) == item.bytes
    assert is_binary(copier.material_path("assets/fig.png")) is True
    assert is_binary(copier.material_path("pkg/mod.py")) is False


def test_exec_bit_preserved_and_setuid_stripped(docket):
    copier = Copier(FIXTURE_ROOT, docket)
    report = copier.execute(copier.plan(_full_requests()))
    by_dest = {i.dest: i for i in report.copied}

    run = stat.S_IMODE(os.stat(copier.material_path("pkg/run.sh")).st_mode)
    assert run & 0o111, "executable bit must survive the copy"
    assert by_dest["pkg/run.sh"].mode == run

    suid = stat.S_IMODE(os.stat(copier.material_path("pkg/setuid.sh")).st_mode)
    assert suid & 0o7000 == 0, "setuid/setgid/sticky must be stripped"
    assert suid == 0o755


# ---------------------------------------------------------------------------
# symlink policy  (red->green guard #1)
# ---------------------------------------------------------------------------


def test_symlinks_all_refused(docket):
    """All symlinks are refused — both escaping and internal ones.

    RED->GREEN (guard #1: symlink-component refusal).  Captured by running this
    test with the symlink branch of ``Copier._classify_inner`` replaced by a
    comment (``state/logs/U5.1-redgreen.py``):

        RED_GREEN_GUARD_1 (symlink gate reverted) -> pytest tests/test_docket_copy.py::test_symlinks_all_refused
        tests/test_docket_copy.py:195: in test_symlinks_all_refused
            assert report.copied == [] and report.linked == []
        E   AssertionError: assert ([CopyItem(src...binary=False)] == []
        E     Left contains one more item: CopyItem(src='.../copy-src/inner',
        E       dest='inner.json', sha256='534b86f4593...b6deb294047ace3', bytes=22,
        E       mode=420, excerpt=None, reason='inner', status='copied',
        E       refusal_reason=None, binary=False)
        E     Use -v to get more diff)
        FAILED tests/test_docket_copy.py::test_symlinks_all_refused

    i.e. the internal link ``inner`` was *copied* straight through: the gate is
    load-bearing for links that resolve inside the root, not merely for the
    escaping one (``escape`` is still caught by containment even without it).
    Restored, the same command reports ``15 passed``.
    """
    copier = Copier(FIXTURE_ROOT, docket)
    report = copier.execute(
        copier.plan(
            [
                CopyRequest(str(FIXTURE_ROOT / "escape"), "escape.txt", "escape"),
                CopyRequest(str(FIXTURE_ROOT / "inner"), "inner.json", "inner"),
            ]
        )
    )

    assert report.copied == [] and report.linked == []
    assert report.refused_count == 2
    reasons = {i.dest: i.refusal_reason for i in report.refused}
    assert reasons == {"escape.txt": "symlink", "inner.json": "symlink"}
    assert not os.path.exists(copier.material_path("escape.txt"))
    assert not os.path.exists(copier.material_path("inner.json"))


# ---------------------------------------------------------------------------
# secrets  (red->green guard #2)
# ---------------------------------------------------------------------------


def test_secret_path_refused_and_not_copied(docket):
    """``.env`` is refused by path shape and no copy reaches material/."""
    copier = Copier(FIXTURE_ROOT, docket)
    report = copier.execute(
        copier.plan([CopyRequest(str(FIXTURE_ROOT / ".env"), ".env", "oops")])
    )

    assert report.refused_count == 1
    item = report.refused[0]
    assert item.refusal_reason == "secret_path"
    assert item.sha256 is None, "secrets must not even be hashed into the docket"
    assert not os.path.exists(copier.material_path(".env"))


def test_secret_content_refused_and_not_copied(docket):
    """Innocuous filename, secret-shaped content: refused on content.

    RED->GREEN (guard #2: secret-content refusal).  Captured by running this
    test with the ``_secret_content_reason(src)`` call removed from
    ``Copier._classify_inner`` (``state/logs/U5.1-redgreen.py``):

        RED_GREEN_GUARD_2 (secret-content scan reverted) -> pytest tests/test_docket_copy.py::test_secret_content_refused_and_not_copied
        tests/test_docket_copy.py:251: in test_secret_content_refused_and_not_copied
            assert report.refused_count == 1
        E   AssertionError: assert 0 == 1
        E    +  where 0 = CopyReport(items=[CopyItem(src='.../copy-src/config/api.txt',
        E      dest='confi...d=1,
        E      written_paths=['/tmp/pytest-of-zer0null/pytest-1/test_secret_content_refused_an0/docket/material/config/api.txt']).refused_count
        FAILED tests/test_docket_copy.py::test_secret_content_refused_and_not_copied

    The ``written_paths`` entry is the point: ``api.txt`` was copied verbatim,
    ``sk-`` token and all, into the docket's ``material/``.  Restored, the same
    command reports ``15 passed``.
    """
    copier = Copier(FIXTURE_ROOT, docket)
    report = copier.execute(
        copier.plan(
            [CopyRequest(str(FIXTURE_ROOT / "config" / "api.txt"),
                         "config/api.txt", "innocuous name")]
        )
    )

    assert report.refused_count == 1
    item = report.refused[0]
    assert item.refusal_reason == "secret_content"
    assert not os.path.exists(copier.material_path("config/api.txt"))


def test_secret_not_bypassable_by_cap(docket):
    """Secret content refuses even when the file is over the per-file cap."""
    copier = Copier(FIXTURE_ROOT, docket, per_file_cap=16)
    report = copier.execute(
        copier.plan([CopyRequest(str(FIXTURE_ROOT / "config" / "api.txt"),
                                 "config/api.txt", "cap bypass attempt")])
    )
    assert report.refused_count == 1 and report.linked_count == 0
    assert report.refused[0].refusal_reason == "secret_content"


# ---------------------------------------------------------------------------
# caps
# ---------------------------------------------------------------------------


def test_over_cap_linked_in_links_md(docket):
    """big.bin over a 1 MiB cap becomes a LINKS.md stub, never a copy."""
    copier = Copier(FIXTURE_ROOT, docket, per_file_cap=1 * MIB)
    report = copier.execute(
        copier.plan([CopyRequest(str(FIXTURE_ROOT / "data" / "big.bin"),
                                 "data/big.bin", "big baseline")])
    )

    assert report.linked_count == 1 and report.copied_count == 0
    item = report.linked[0]
    assert item.refusal_reason == "per_file_cap"
    assert item.bytes == 3 * MIB
    assert not os.path.exists(copier.material_path("data/big.bin")), "must NOT be copied"

    links = Path(copier.links_path).read_text()
    assert item.sha256 in links
    assert str(3 * MIB) in links
    assert str(FIXTURE_ROOT / "data" / "big.bin") in links
    assert "cp -- " in links


def test_docket_cap_deterministic(docket):
    """Once the docket cap is hit, later items (sorted order) link — twice alike."""
    copier = Copier(FIXTURE_ROOT, docket, per_docket_cap=1500)
    requests = [
        CopyRequest(str(FIXTURE_ROOT / "cap" / n), f"cap/{n}", "cap probe")
        for n in ("c.txt", "a.txt", "b.txt")  # deliberately unsorted input
    ]

    first = copier.plan(requests)
    second = copier.plan(list(reversed(requests)))
    assert first.to_json() == second.to_json(), "plan must be order-independent"
    assert first.to_json() == copier.plan(requests).to_json()

    assert [i.dest for i in first.to_copy] == ["cap/a.txt"]
    assert [i.dest for i in first.to_link] == ["cap/b.txt", "cap/c.txt"]
    assert {i.refusal_reason for i in first.to_link} == {"docket_cap"}

    report = copier.execute(first)
    assert report.copied_count == 1 and report.linked_count == 2
    assert not os.path.exists(copier.material_path("cap/b.txt"))
    assert not os.path.exists(copier.material_path("cap/c.txt"))


# ---------------------------------------------------------------------------
# idempotency + excerpts
# ---------------------------------------------------------------------------


def test_idempotent_second_run_unchanged_mtimes(docket):
    """A second execute reports ``unchanged`` and rewrites nothing at all."""
    copier = Copier(FIXTURE_ROOT, docket)
    requests = _full_requests()

    first = copier.execute(copier.plan(requests))
    assert first.copied_count == len(requests)
    before = {
        i.dest: (os.stat(copier.material_path(i.dest)).st_mtime_ns,
                 os.stat(copier.material_path(i.dest)).st_ino,
                 sha256_file(copier.material_path(i.dest)))
        for i in first.copied
    }

    time.sleep(0.01)  # make any rewrite visible in mtime_ns
    second = copier.execute(copier.plan(requests))
    assert second.copied_count == 0
    assert second.unchanged_count == len(requests)
    for item in second.unchanged:
        dest = copier.material_path(item.dest)
        st = os.stat(dest)
        assert (st.st_mtime_ns, st.st_ino, sha256_file(dest)) == before[item.dest]
    assert second.written_paths == [], "nothing should be written on a no-op rerun"


def test_excerpts_md_written_with_span(docket):
    """EXCERPTS.md carries dest path, inclusive 1-based span and reason."""
    copier = Copier(FIXTURE_ROOT, docket)
    report = copier.execute(
        copier.plan(
            [CopyRequest(str(FIXTURE_ROOT / "sub" / "note.md"), "sub/note.md",
                         "shows the finding", excerpt=(3, 3))]
        )
    )
    assert report.copied_count == 1
    text = Path(copier.excerpts_path).read_text()
    assert "sub/note.md" in text
    assert "3-3" in text
    assert "shows the finding" in text

    # no excerpt -> no index file is emitted
    other = Copier(FIXTURE_ROOT, docket / "plain")
    other.execute(other.plan([CopyRequest(str(FIXTURE_ROOT / "pkg" / "mod.py"),
                                          "pkg/mod.py", "no excerpt")]))
    assert not os.path.exists(other.excerpts_path)


# ---------------------------------------------------------------------------
# integrity + confinement + source safety
# ---------------------------------------------------------------------------


def test_integrity_error_when_destination_tampered(docket, monkeypatch):
    """A destination that does not re-hash to the source raises, never 'copied'."""
    copier = Copier(FIXTURE_ROOT, docket)
    plan = copier.plan(
        [CopyRequest(str(FIXTURE_ROOT / "pkg" / "mod.py"), "pkg/mod.py", "tamper")]
    )

    real = copy_mod.sha256_file

    def lying_hasher(path, chunk=copy_mod.CHUNK):
        if os.path.basename(str(path)).startswith("mod.py"):
            return "0" * 64  # simulate on-disk corruption between copy and verify
        return real(path, chunk)

    monkeypatch.setattr(copy_mod, "sha256_file", lying_hasher)
    with pytest.raises(CopyIntegrityError) as excinfo:
        copier.execute(plan)

    err = excinfo.value
    assert err.sha_src == real(FIXTURE_ROOT / "pkg" / "mod.py")
    assert err.sha_dest == "0" * 64
    assert isinstance(err, RuntimeError)
    assert err.dest.endswith("mod.py")


def test_confinement_nothing_written_outside_docket(docket):
    """A full execute writes nothing outside ``docket_dir``."""
    parent = FIXTURE_ROOT.parent
    before = {p for p in parent.rglob("*")}
    outside = {p for p in Path("/tmp").glob("docket-*")}

    copier = Copier(FIXTURE_ROOT, docket)
    report = copier.execute(copier.plan(_full_requests()))

    assert {p for p in parent.rglob("*")} == before
    assert {p for p in Path("/tmp").glob("docket-*")} == outside
    for path in report.written_paths:
        assert str(path).startswith(str(docket / "material"))


def test_source_tree_untouched_by_full_execute(docket):
    """sha256 + mtime_ns + mode of every fixture source survive a full execute."""
    copier = Copier(FIXTURE_ROOT, docket)
    copier.execute(copier.plan(_full_requests()))
    copier.execute(copier.plan(_full_requests()))  # rerun too

    after = {
        p: (sha256_file(p), os.lstat(p).st_mtime_ns, os.lstat(p).st_mode)
        for p in sorted(FIXTURE_ROOT.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }
    assert after == _BASELINE

    # symlinks themselves are untouched as well
    assert (FIXTURE_ROOT / "escape").is_symlink()
    assert os.readlink(FIXTURE_ROOT / "inner") == "data/small.json"


def test_plan_never_raises_on_hostile_requests(docket):
    """Bad requests become reasoned refusals — plan() itself never raises."""
    copier = Copier(FIXTURE_ROOT, docket)
    requests = [
        CopyRequest("/etc/hostname", "outside.txt", "outside"),
        CopyRequest(str(FIXTURE_ROOT / "does-not-exist.txt"), "gone.txt", "missing"),
        CopyRequest(str(FIXTURE_ROOT / "sub"), "sub", "a directory"),
        CopyRequest(str(FIXTURE_ROOT / "pkg" / "mod.py"), "../../escape.py", "escape"),
        CopyRequest(str(FIXTURE_ROOT / "pkg" / "mod.py"), "/abs.py", "absolute"),
        CopyRequest(str(FIXTURE_ROOT / "pkg" / "mod.py"), "", "empty"),
    ]
    plan = copier.plan(requests)  # must not raise

    got = {i.dest: (i.status, i.refusal_reason) for i in plan.items}
    assert got["outside.txt"] == ("refused", "outside_target_root")
    assert got["gone.txt"] == ("missing", "not_found")
    assert got["sub"] == ("refused", "is_directory")
    assert got["../../escape.py"][1] == "unsafe_dest"
    assert got["/abs.py"][1] == "unsafe_dest"
    assert got[""][1] == "unsafe_dest"
    report = copier.execute(plan)
    assert report.copied_count == 0


def test_report_json_is_sorted_and_stable(docket):
    copier = Copier(FIXTURE_ROOT, docket)
    report = copier.execute(copier.plan(list(reversed(_full_requests()))))
    js = report.to_json()
    assert '"copied"' in js and '"linked"' in js
    assert js.index('"copied"') < js.index('"items"')  # sort_keys=True
