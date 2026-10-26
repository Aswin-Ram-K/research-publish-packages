"""Admission-policy tests for U1.7 — offline, fixture-only, zero LLM/network.

These tests pin the two guards that protect the highest-value research material
from *silent* exclusion:

* **the asserted-present violation guard** — an asserted file that exists but is
  not admitted must surface as a ``violations`` entry, never as a quiet absence;
* **the config-cannot-widen refusal** — config may narrow admission, never
  re-admit something graphify's predicate prunes.

Both were reverted to capture the red→green evidence pasted below.

Guard A (asserted-present violation) reverted — ``violations.append(
_not_admitted(...))`` replaced by ``pass`` — ``pytest -k silent_loss`` failed::

    >       assert audit.violations, "excluded asserted material produced NO violation (silent loss)"
    E       AssertionError: excluded asserted material produced NO violation (silent loss)
    E       assert []
    E        +  where [] = PolicyAudit(target_root='<workspace>', admitted={'.ci-trunk.txt': 39,...tract.kg.ingest._walk; config excludes can only narrow', 'assert_present: every asserted path exists and is admitted']).violations
    tests/test_kg_policy.py:197: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_kg_policy.py::test_silent_loss_guard_reports_violation_not_quiet_absence
    1 failed, 11 deselected in 0.06s

Guard B (config-cannot-widen) reverted — ``raise PolicyWideningError(...)``
replaced by ``pass`` — ``pytest -k cannot_widen`` failed::

    >           with pytest.raises(P.PolicyWideningError) as excinfo:
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    E           Failed: DID NOT RAISE PolicyWideningError
    tests/test_kg_policy.py:156: Failed
    =========================== short test summary info ============================
    FAILED tests/test_kg_policy.py::test_config_cannot_widen - Failed: DID NOT RA...
    1 failed, 11 deselected in 0.03s
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from resextract.kg import policy as P

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "policy-repo"

MONOGRAPH = ".lane-j-scratch/monograph.md"
ARTEFACT = "app.bundle.min.js"


def write_config(tmp_path: Path, *, include=None, exclude=None, assert_present=None, path=FIXTURE) -> Path:
    """Write a minimal [targets.<slug>] config pointing at the fixture repo."""
    def block(key: str, values) -> str:
        if not values:
            return f"{key} = []\n"
        body = ",\n".join(f'  "{v}"' for v in values)
        return f"{key} = [\n{body},\n]\n"

    text = (
        "[targets.fixture]\n"
        'slug = "fixture"\n'
        f'path = "{path}"\n'
        "read_only = true\n"
        + block("include", include if include is not None else ["docs/", ".lane-j-scratch/**"])
        + block("exclude", exclude or [])
        + block("assert_present", assert_present or [])
    )
    cfg = tmp_path / "targets.toml"
    cfg.write_text(text, encoding="utf-8")
    return cfg


def load(tmp_path: Path, **kw) -> P.TargetPolicy:
    return P.TargetPolicy.from_config(write_config(tmp_path, **kw), "fixture")


# --------------------------------------------------------------------------- #
# 1. the fixture tree is what these tests think it is
# --------------------------------------------------------------------------- #
def test_fixture_tree_complete():
    for rel in (
        MONOGRAPH,
        ".ci-trunk.txt",
        "README.md",
        "docs/FINDINGS.md",
        ".worktrees/run-1/deep.py",
        "node_modules/x.js",
        ".git/config",
        "tmp/scratch.md",
        ARTEFACT,
    ):
        assert (FIXTURE / rel).is_file(), rel


# --------------------------------------------------------------------------- #
# 2. the valuable material is admitted, and says why
# --------------------------------------------------------------------------- #
def test_monograph_and_readme_admitted_with_reason(tmp_path):
    policy = load(tmp_path, assert_present=[MONOGRAPH, "README.md"])
    for rel in (MONOGRAPH, ".ci-trunk.txt", "README.md", "docs/FINDINGS.md"):
        adm = policy.admit(rel)
        assert adm.admitted is True, (rel, adm)
        assert adm.source in P.ADMISSION_SOURCES
        assert adm.reason, rel
    assert policy.admit(MONOGRAPH).source == "config_assert"
    assert "predicate" in policy.admit(MONOGRAPH).reason
    # .ci-trunk.txt is admitted on the same rule; it is scored low later, not dropped.
    assert policy.admit(".ci-trunk.txt").source == "graphify_predicate"


# --------------------------------------------------------------------------- #
# 3. graphify's own machinery rejects the pruned subtrees, naming itself
# --------------------------------------------------------------------------- #
def test_worktrees_node_modules_git_rejected_by_graphify(tmp_path):
    policy = load(tmp_path)
    for rel in (".worktrees/run-1/deep.py", "node_modules/x.js", ".git/config"):
        adm = policy.admit(rel)
        assert adm.admitted is False, (rel, adm)
        assert adm.source in P.GRAPHIFY_SOURCES, (rel, adm)
        assert "graphify" in adm.reason.lower(), (rel, adm)
    # the gitignored scratch is rejected too, via the predicate on its parent dir
    assert policy.admit("tmp/scratch.md").admitted is False
    assert policy.admit("tmp/scratch.md").source in P.GRAPHIFY_SOURCES
    # and the audit records the pruned directories by reason
    audit = P.policy_audit(FIXTURE, policy)
    assert ".worktrees/" in audit.rejected
    assert audit.rejected[".worktrees/"].source == "noise_dir"
    assert audit.rejected_by_reason.get("noise_dir", 0) >= 3
    assert audit.rejected_by_reason.get("ignored_dir", 0) >= 1


# --------------------------------------------------------------------------- #
# 4. config exclude narrows an otherwise-admitted file
# --------------------------------------------------------------------------- #
def test_config_exclude_narrows_admission(tmp_path):
    wide = load(tmp_path, exclude=[])
    narrow = load(tmp_path, exclude=["*.min.js"])
    assert wide.admit(ARTEFACT).admitted is True
    assert wide.admit(ARTEFACT).source == "graphify_predicate"
    adm = narrow.admit(ARTEFACT)
    assert adm.admitted is False
    assert adm.source == "config_exclude"
    assert "exclude" in adm.reason
    # narrowing must not touch anything else
    assert narrow.admit(MONOGRAPH).admitted is True


# --------------------------------------------------------------------------- #
# 5. config may never WIDEN — refusal surfaced as an exception
# --------------------------------------------------------------------------- #
def test_config_cannot_widen(tmp_path):
    """Reverting the refusal (``raise`` -> ``pass``) must fail this test.

    Guard B, captured red->green (policy.py sha256 f8f1f7db…, refusal replaced by
    ``pass``)::

        >           with pytest.raises(P.PolicyWideningError) as excinfo:
        E           Failed: DID NOT RAISE PolicyWideningError
        tests/test_kg_policy.py:156: Failed
        FAILED tests/test_kg_policy.py::test_config_cannot_widen - Failed: DID NOT RA...
        1 failed, 11 deselected in 0.05s

    Restoring the ``raise`` turns it green again (12 passed).
    """
    for entry in (".worktrees/", ".git/", "node_modules/"):
        cfg = write_config(tmp_path, include=[entry])
        with pytest.raises(P.PolicyWideningError) as excinfo:
            P.TargetPolicy.from_config(cfg, "fixture")
        assert entry.rstrip("/") in str(excinfo.value)
        assert "widen" in str(excinfo.value).lower()
        # the refusal is also recorded, and non-strict loading still surfaces it
        lenient = P.TargetPolicy.from_config(cfg, "fixture", strict=False)
        assert lenient.widen_attempts
        assert entry.rstrip("/") in lenient.widen_attempts[0]
    # a legitimate include list is not a widening attempt
    ok = load(tmp_path, include=["docs/", ".lane-j-scratch/**"])
    assert ok.widen_attempts == []


# --------------------------------------------------------------------------- #
# 6. assert_present passes when the asserted files are admitted
# --------------------------------------------------------------------------- #
def test_assert_present_passes(tmp_path):
    policy = load(tmp_path, assert_present=[MONOGRAPH, "README.md", "docs/FINDINGS.md"])
    audit = P.policy_audit(FIXTURE, policy)
    assert audit.violations == []
    assert [a.path for a in audit.assertions] == [MONOGRAPH, "README.md", "docs/FINDINGS.md"]
    for result in audit.assertions:
        assert result.ok is True
        assert result.actual is True
        assert result.size_bytes > 0
        assert result.source in P.ADMISSION_SOURCES


# --------------------------------------------------------------------------- #
# 7. the silent-loss guard: excluding an asserted path is a VIOLATION
# --------------------------------------------------------------------------- #
def test_silent_loss_guard_reports_violation_not_quiet_absence(tmp_path):
    """Excluding the asserted material must be loud, not silent.

    This is guard A. With the violation append reverted to ``pass`` this test
    fails because ``violations`` comes back empty — which is exactly the silent
    loss the policy exists to prevent. Captured red->green (policy.py sha256
    f8f1f7db…, ``violations.append(_not_admitted(...))`` replaced by ``pass``)::

        >       assert audit.violations, "excluded asserted material produced NO violation (silent loss)"
        E       AssertionError: excluded asserted material produced NO violation (silent loss)
        E       assert []
        E        +  where [] = PolicyAudit(target_root='…/tests/fixtures/policy-repo', admitted={'.ci-trunk.txt': 39,...'assert_present: every asserted path exists and is admitted']).violations
        tests/test_kg_policy.py:197: AssertionError
        1 failed, 11 deselected in 0.06s

    Restoring the append turns it green again (12 passed).
    """
    policy = load(tmp_path, assert_present=[MONOGRAPH], exclude=[".lane-j-scratch/**"])
    assert policy.admit(MONOGRAPH).admitted is False
    audit = P.policy_audit(FIXTURE, policy)
    assert audit.violations, "excluded asserted material produced NO violation (silent loss)"
    joined = " ".join(audit.violations)
    assert MONOGRAPH in joined
    assert "config_exclude" in joined
    assert "silently" in joined.lower()
    result = audit.assertions[0]
    assert result.ok is False
    assert result.actual is False
    assert result.source == "config_exclude"
    # it is recorded as an explicit rejection, not merely absent from `admitted`
    assert MONOGRAPH in audit.rejected
    assert MONOGRAPH not in audit.admitted


# --------------------------------------------------------------------------- #
# 8. asserted path that does not exist is a missing_expected violation
# --------------------------------------------------------------------------- #
def test_missing_asserted_path_is_violation(tmp_path):
    ghost = ".lane-j-scratch/does-not-exist.md"
    policy = load(tmp_path, assert_present=[ghost])
    audit = P.policy_audit(FIXTURE, policy)
    assert audit.violations
    assert audit.violations[0].startswith("missing_expected")
    assert ghost in audit.violations[0]
    assert audit.assertions[0].exists is False
    assert audit.assertions[0].ok is False


# --------------------------------------------------------------------------- #
# 9. policy_diff makes a config change reviewable
# --------------------------------------------------------------------------- #
def test_policy_diff_reports_admission_change(tmp_path):
    before = load(tmp_path, exclude=[])
    after = load(tmp_path, exclude=["*.min.js"], assert_present=[MONOGRAPH])
    diff = P.policy_diff(before, after, paths=[ARTEFACT, MONOGRAPH, "README.md"])
    assert diff.newly_rejected == [ARTEFACT]
    assert diff.newly_admitted == []
    assert diff.changed[ARTEFACT] == (True, False)
    assert MONOGRAPH not in diff.changed
    assert "README.md" not in diff.changed
    assert diff.added_excludes == ["*.min.js"]
    assert diff.as_dict()["changed"][ARTEFACT] == [True, False]


# --------------------------------------------------------------------------- #
# 10. determinism
# --------------------------------------------------------------------------- #
def test_audit_is_deterministic(tmp_path):
    policy = load(tmp_path, assert_present=[MONOGRAPH, "README.md"], exclude=["*.min.js"])
    first = P.policy_audit(FIXTURE, policy).as_dict()
    second = P.policy_audit(FIXTURE, policy).as_dict()
    assert first == second
    assert list(first["admitted"]) == sorted(first["admitted"])
    assert list(first["rejected_by_reason"]) == sorted(first["rejected_by_reason"])


# --------------------------------------------------------------------------- #
# 11. robustness: nothing raises on odd paths
# --------------------------------------------------------------------------- #
def test_admit_never_raises_and_sources_are_known(tmp_path):
    policy = load(tmp_path)
    for rel in ("", "   ", "/", "./README.md", "a" * 4000, ".graphifyignore", "nonexistent/x.md"):
        adm = policy.admit(rel)
        assert adm.source in P.ADMISSION_SOURCES, (rel, adm)
        assert isinstance(adm.admitted, bool)
    # a non-existent target root is recorded, not fatal
    audit = P.policy_audit(FIXTURE / "no-such-dir", policy)
    assert audit.notes


# --------------------------------------------------------------------------- #
# 12. the real config keeps its intent (no Duval walk; config read only)
# --------------------------------------------------------------------------- #
def test_real_target_config_declares_the_decision():
    """GUARD: the REAL target's admission is pinned as a decision, not an accident (U4+U1.7R+KG-POLICY)."""
    cfg = Path(__file__).resolve().parents[1] / "config" / "targets.toml"
    policy = P.TargetPolicy.from_config(cfg, "duval")     # must not raise
    assert policy.widen_attempts == []
    assert policy.read_only is True
    # KG-POLICY (2026-10-23): the TARGET OWNER gitignored .lane-j-scratch/ (Duval
    # .gitignore:93, commit 90ba6d3, 2026-10-14), so graphify's predicate now
    # EXCLUDES it and any config include of it is a WIDENING attempt (guard B
    # refuses: PolicyWideningError, policy.py:327). The pinned decision is the
    # INVERSE: no config entry references the scratch dir, nothing asserts its
    # files. RESTORE PATH: if the owner un-ignores it, re-add include
    # ".lane-j-scratch/**" + the two scratch assert_present entries (files still
    # on disk: 83832 B + 159408 B) and restore the U1.7R positive pins.
    assert ".lane-j-scratch/**" not in policy.include
    assert not any(e.startswith(".lane-j-scratch") for e in policy.include)
    assert not any(".lane-j-scratch" in e for e in policy.assert_present)
    assert {".worktrees/", ".git/"} & (set(policy.include) | set(policy.exclude)) == set()
