#!/usr/bin/env python3
"""tests_score_adapter.py — observed exit codes for the two accepted fixture schemas.

Run with .venv/bin/python experiments/ptr-engine/longrun/tests_score_adapter.py .
Every case scores a real log against a real or /tmp fixture by invoking
score_longrun.py as a subprocess and asserts the exit code, the verdict and the
guarantee it is supposed to prove.  Prints one JSON document; exits 1 on failure.

Cases
  GREEN_RUNTIME   runtime-schema fixture (consonance.longrun-fixture/1) whose
                  acceptance surface is deterministic (log-carried artefact
                  checks, structured negative constraints, literal repair):
                  exit 0, verified_success true.
  RED_CONSTRAINT  same fixture/log + a negative-constraint violation:
                  exit 1, excerpt quoted in the check evidence.
  RED_TAMPER      /tmp copy of runtime/LR-01.json whose row digest matches
                  neither candidate: exit 2, tampered true.
  RED_ABSENT      runtime/LR-01.json, log truncated before the last checkpoint:
                  exit 1, cp.t46 fail with "no record at turn 46".
  AUDITED_DIGEST  runtime/LR-01.json rows carrying the authored digest: accepted,
                  fixture_sha256_matched == authored_derived_from, tamper_scope
                  discloses that the runtime file is not certified.
  LR01_RUNTIME    runtime/LR-01.json as frozen: exit 1 with the eight
                  unverifiable required checks named (prose acceptance).
  PARITY          the same 48-turn log vs fixtures/LR-01.json (authored) and
                  runtime/LR-01.json (runtime): identical check verdicts.
  AUTHORED_*      authored-schema mini fixture: green 0 / wrong checkpoint 1 /
                  tampered 2 -- the authored path is unchanged.
"""

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LONGRUN = ROOT / "experiments/ptr-engine/longrun"
SCORER = LONGRUN / "score_longrun.py"
AUTHORED = LONGRUN / "fixtures/LR-01.json"
RUNTIME = LONGRUN / "runtime/LR-01.json"
TMP = Path(tempfile.mkdtemp(prefix="score-adapter-"))
results = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def score(fixture, run_path):
    proc = subprocess.run(
        [sys.executable, str(SCORER), "--fixture", str(fixture), "--run", str(run_path)],
        capture_output=True, text=True)
    card = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            card = json.loads(line)
    return proc.returncode, card


def write_log(path, rows):
    Path(path).write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def long_rows(digest, turns=48, contents=None, artefact=None, extra=None):
    contents = contents or {}
    rows = [{"fixture_sha256": digest, "task_id": "LR-01", "arm": "B", "rep": 1}]
    for turn in range(1, turns + 1):
        row = {"turn": turn, "arm": "B", "rep": 1,
               "content": contents.get(turn, "work turn %d: read, edit, re-run" % turn)}
        if artefact and turn == artefact[0]:
            row["artifacts"] = {artefact[1]: artefact[2]}
        rows.append(row)
    for row in extra or []:
        rows.append(row)
    return rows


def rt_fixture():
    fixture = json.loads(RUNTIME.read_text(encoding="utf-8"))
    fixture["acceptance"] = {
        "checks": [
            {"id": "check.1", "kind": "artifact", "path": "acceptance/lr01.txt",
             "must_contain": ["DEFAULT_MAX_REFS == 64", "exit 0"]},
            {"id": "check.2", "kind": "artifact", "path": "acceptance/lr01.txt",
             "must_contain": ["pytest tests/test_scope.py", "9 passed"]},
            {"id": "check.3", "kind": "artifact", "path": "acceptance/lr01.txt",
             "must_contain": ["PTR_NOT_A_REFERENCE", "one ledger row"]},
            {"id": "check.4", "kind": "artifact", "path": "acceptance/lr01.txt",
             "must_contain": ["9 test functions"]},
        ],
        "negative_constraints": [
            {"id": "con.no_guard_weaken", "kind": "constraint",
             "literal": "weakened the isinstance(scope, Scope) guard"},
            {"id": "con.no_test_delete", "kind": "constraint",
             "must_not_delete_tests": True},
            {"id": "con.no_fixture_edit", "kind": "constraint",
             "no_write": "experiments/ptr-engine/longrun/fixtures/LR-01.json"},
        ],
    }
    fixture["repair"] = dict(fixture["repair"])
    fixture["repair"]["accept_literal"] = "restore the typed guard deleted at turn 8"
    return fixture


def case(name, fn):
    try:
        results.append(dict(name=name, **fn()))
    except AssertionError as exc:
        results.append({"name": name, "ok": False, "error": str(exc)})
        print(json.dumps({"case": name, "FAILED": str(exc)}, indent=1))
        raise


AUTH = sha(AUTHORED)
RUN = sha(RUNTIME)
ARTEFACT = "DEFAULT_MAX_REFS == 64 -> exit 0\npytest tests/test_scope.py -> 9 passed\n" \
           "PTR_NOT_A_REFERENCE leaves one ledger row\n9 test functions\n"
GOOD = {12: "64", 24: "31", 32: "restore the typed guard deleted at turn 8",
        46: "ledger.record_refusal(scope=..., serialized_ref=text, code=error.code), "
            "before re-raising"}


def green_runtime():
    fixture = rt_fixture()
    path = TMP / "green-runtime.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")
    log = write_log(TMP / "green.ndjson",
                    long_rows(sha(path), contents=GOOD,
                              artefact=(48, "acceptance/lr01.txt", ARTEFACT)))
    code, card = score(path, log)
    assert code == 0, "exit %s: failed=%s unverifiable=%s" % (
        code, card.get("failed_required"), card.get("unverifiable_required"))
    assert card["verified_success"] is True, card
    assert card["fixture_schema"] == "consonance.longrun-fixture/1"
    assert card["fixture_sha256_at_score"] == sha(path)
    assert card["fixture_sha256_matched"] == "fixture_file", card["fixture_sha256_matched"]
    assert card["tampered"] is False
    assert card["checkpoint_accuracy"] == "3/3", card["checkpoint_accuracy"]
    weak = [c for c in card["checks"] if c["kind"] == "constraint"]
    assert all("weak_constraint" in c for c in weak), "weak_constraint not reported"
    actors = [c for c in card["checks"] if c["kind"] == "repair"]
    assert actors and actors[0]["verdict"] == "pass", actors
    return {"fixture": str(path), "exit_code": code,
            "verified_success": card["verified_success"],
            "fixture_sha256_matched": card["fixture_sha256_matched"],
            "checkpoint_accuracy": card["checkpoint_accuracy"]}


def red_constraint():
    fixture = TMP / "green-runtime.json"
    bad = dict(GOOD)
    bad[40] = "we weakened the isinstance(scope, Scope) guard to make a ledger row appear"
    log = write_log(TMP / "red-constraint.ndjson",
                    long_rows(sha(fixture), contents=bad,
                              artefact=(48, "acceptance/lr01.txt", ARTEFACT)))
    code, card = score(fixture, log)
    assert code == 1, "exit %s" % code
    assert card["verified_success"] is False
    failed = [c for c in card["checks"] if c["verdict"] == "fail"]
    hit = [c for c in failed if c["kind"] == "constraint"]
    assert hit, "no constraint failed: %s" % failed
    assert "weakened the isinstance" in hit[0]["evidence"], hit[0]["evidence"]
    assert card["constraint_violations"], "no violation recorded"
    return {"exit_code": code, "verified_success": card["verified_success"],
            "check": hit[0]["id"], "evidence": hit[0]["evidence"],
            "excerpt": card["constraint_violations"][0]["excerpt"]}


def red_tamper():
    fixture = json.loads(RUNTIME.read_text(encoding="utf-8"))
    fixture["acceptance"]["checks"].append({"id": "check.99", "kind": "artifact",
                                            "path": "acceptance/lr01.txt",
                                            "must_contain": ["x"]})
    path = TMP / "tampered-lr01.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")
    log = write_log(TMP / "tamper.ndjson",
                    long_rows(sha(path), contents=GOOD,
                              artefact=(48, "acceptance/lr01.txt", ARTEFACT)))
    path.write_text(json.dumps(rt_fixture()), encoding="utf-8")  # edit after the run
    code, card = score(path, log)
    assert code == 2, "exit %s" % code
    assert card["tampered"] is True, card
    assert card["verified_success"] is False
    digest_check = [c for c in card["checks"] if c["id"] == "fixture.digest"][0]
    assert digest_check["verdict"] == "fail"
    return {"exit_code": code, "tampered": card["tampered"],
            "verified_success": card["verified_success"],
            "evidence": digest_check["evidence"]}


def red_absent():
    log = write_log(TMP / "truncated.ndjson", long_rows(RUN, turns=45, contents=GOOD))
    code, card = score(RUNTIME, log)
    assert code == 1, "exit %s" % code
    assert card["verified_success"] is False
    cp = [c for c in card["checks"] if c["id"] == "cp.t46"][0]
    assert cp["verdict"] == "fail", cp
    assert cp["evidence"] == "no record at turn 46", cp["evidence"]
    return {"exit_code": code, "check": cp["id"], "verdict": cp["verdict"],
            "evidence": cp["evidence"], "checkpoint_accuracy": card["checkpoint_accuracy"]}


def audited_digest():
    log = write_log(TMP / "authored-digest.ndjson",
                    long_rows(AUTH, contents=GOOD,
                              artefact=(48, "acceptance/lr01.txt", ARTEFACT)))
    code, card = score(RUNTIME, log)
    assert card["tampered"] is False, card
    assert card["fixture_sha256_matched"] == "authored_derived_from", card["fixture_sha256_matched"]
    assert "authored-only" in card["tamper_scope"], card["tamper_scope"]
    digest_check = [c for c in card["checks"] if c["id"] == "fixture.digest"][0]
    assert digest_check["verdict"] == "pass"
    return {"exit_code": code, "tampered": card["tampered"],
            "fixture_sha256_matched": card["fixture_sha256_matched"],
            "tamper_scope": card["tamper_scope"], "verified_success": card["verified_success"]}


def lr01_runtime():
    log = write_log(TMP / "lr01-runtime.ndjson",
                    long_rows(RUN, contents=GOOD,
                              artefact=(48, "acceptance/lr01.txt", ARTEFACT)))
    code, card = score(RUNTIME, log)
    assert code == 1, "exit %s" % code
    assert card["verified_success"] is False
    assert "check.1" in card["unverifiable_required"]
    assert len(card["unverifiable_required"]) == 8, card["unverifiable_required"]
    assert card["fixture_sha256_matched"] == "fixture_file"
    return {"exit_code": code, "verified_success": card["verified_success"],
            "unverifiable_required": card["unverifiable_required"],
            "checkpoint_accuracy": card["checkpoint_accuracy"]}


def parity():
    authored_log = write_log(TMP / "parity-authored.ndjson",
                             long_rows(AUTH, contents=GOOD,
                                       artefact=(48, "acceptance/lr01.txt", ARTEFACT)))
    runtime_log = write_log(TMP / "parity-runtime.ndjson",
                            long_rows(RUN, contents=GOOD,
                                      artefact=(48, "acceptance/lr01.txt", ARTEFACT)))
    a_code, a_card = score(AUTHORED, authored_log)
    r_code, r_card = score(RUNTIME, runtime_log)
    key = lambda card: [(c["id"], c["kind"], c["verdict"], c["required"])
                        for c in card["checks"]]
    assert key(a_card) == key(r_card), "schema parity broken: %s vs %s" % (
        key(a_card), key(r_card))
    assert a_code == r_code == 1, (a_code, r_code)
    assert a_card["checkpoint_accuracy"] == r_card["checkpoint_accuracy"] == "3/3"
    return {"authored_exit": a_code, "runtime_exit": r_code,
            "checks_identical": True,
            "authored_matched": a_card["fixture_sha256_matched"],
            "runtime_matched": r_card["fixture_sha256_matched"]}


MINI = {
    "schema": "consonance.fixture/1", "task_id": "MINI", "class": "repo-fix",
    "objective": "minimal authored fixture for the regression case",
    "sources": [], "turns": [{"turn": i, "kind": "work", "instruction": "step %d" % i}
                             for i in range(1, 7)],
    "checkpoints": [{"turn": 6, "question": "which ref?", "expected": "k01"}],
    "repair": {"at_turn": 3, "wrong_assumption": "k99", "correct_action": "use k01",
               "accept_literal": "k01"},
    "acceptance": {"checks": [{"id": "check.1", "kind": "artifact", "path": "out.txt",
                               "must_contain": ["done"]}],
                   "negative_constraints": [{"id": "con.1", "kind": "constraint",
                                             "literal": "AUD-0000"}]},
    "expected": {"verified_success": True, "forbidden_claims": []},
}


def authored_schema():
    path = TMP / "mini-authored.json"
    path.write_text(json.dumps(MINI), encoding="utf-8")
    good = [{"fixture_sha256": sha(path), "task_id": "MINI", "arm": "A", "rep": 1}]
    for turn in range(1, 7):
        good.append({"turn": turn, "tokens": 10,
                     "content": "k01" if turn == 6 else "k01 done",
                     "artifacts": {"out.txt": "all done"}})
    log = write_log(TMP / "mini-green.ndjson", good)
    code, card = score(path, log)
    assert code == 0, "authored green regressed: exit %s %s" % (
        code, card.get("failed_required") or card.get("unverifiable_required"))
    assert card["verified_success"] is True
    assert card["fixture_schema"] == "consonance.fixture/1"
    assert card["fixture_sha256_matched"] == "fixture_file"
    assert card["tokens_to_verified_success"] == 60, card["tokens_to_verified_success"]
    bad = [dict(r) for r in good]
    bad[6] = dict(bad[6], content="k07 done")
    bad_log = write_log(TMP / "mini-red.ndjson", bad)
    code2, card2 = score(path, bad_log)
    assert code2 == 1 and card2["verified_success"] is False, (code2, card2)
    assert "cp.t6" in card2["failed_required"], card2["failed_required"]
    tamper_log = write_log(TMP / "mini-tamper.ndjson",
                           [dict(bad[0], fixture_sha256="0" * 64)] + bad[1:])
    code3, card3 = score(path, tamper_log)
    assert code3 == 2 and card3["tampered"] is True, (code3, card3)
    return {"green_exit": code, "red_exit": code2, "tamper_exit": code3,
            "green_tokens": card["tokens_to_verified_success"],
            "red_failed": card2["failed_required"]}


if __name__ == "__main__":
    assert AUTHORED.exists() and RUNTIME.exists()
    for name, fn in [("GREEN_RUNTIME", green_runtime),
                     ("RED_CONSTRAINT", red_constraint),
                     ("RED_TAMPER", red_tamper),
                     ("RED_ABSENT", red_absent),
                     ("AUDITED_DIGEST", audited_digest),
                     ("LR01_RUNTIME", lr01_runtime),
                     ("PARITY", parity),
                     ("AUTHORED_SCHEMA", authored_schema)]:
        case(name, fn)
    print(json.dumps({"ok": True, "tmp": str(TMP), "cases": results}, indent=1))
