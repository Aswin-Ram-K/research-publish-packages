"""Guards for QUALITY-CARRY-FORWARD: the statements block and the --check gate.

The record publishes two verbatim sentences attributed to MODAL-ANSWER-ACCURACY. A record that
loses either sentence, or loses an attribution, is not the record this unit shipped -- these tests
fail on that, and on a --check that stops detecting a mutated count or a drifted source digest.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "experiments" / "ptr-engine" / "tools" / "quality_carry_forward.py"
RECORD = ROOT / "experiments" / "ptr-engine" / "measure" / "QUALITY-CARRY-FORWARD.json"

STATEMENT_1 = (
    "era A's checkpoint answers are answer-production measurements under an instruction to read "
    "sources the arm could not read (46 of 48 turns in v5/v6/v7/v8 invite a read; `@knowledge:` "
    "0/48, literal `read_file` 0/48)"
)
STATEMENT_2 = (
    "under the modal-answer reading every arm scores 0/12; the three observed passes are one-off, "
    "one-arm, and none is the arm's most frequent answer."
)


def run_check(record: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), "--check", "--record", str(record)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )


def load_record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def write_record(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    return path


def test_statements_are_verbatim() -> None:
    texts = [s["text"] for s in load_record()["statements"]]
    assert STATEMENT_1 in texts, "statement 1 (answer production under an unreadable-source instruction) is missing"
    assert STATEMENT_2 in texts, "statement 2 (every arm 0/12, three one-off non-modal passes) is missing"


def test_statements_carry_attribution() -> None:
    record = load_record()
    statements = record["statements"]
    assert len(statements) >= 2
    for statement in statements:
        attribution = statement.get("attribution") or {}
        assert attribution.get("unit") == "MODAL-ANSWER-ACCURACY", statement["id"]
        assert attribution.get("path"), statement["id"]
        assert attribution.get("sha256"), statement["id"]
        assert attribution.get("figure_ids"), statement["id"]
        source = ROOT / attribution["path"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == attribution["sha256"], (
            f"{statement['id']} attributes a digest the source no longer has"
        )


def test_check_is_green_on_the_shipped_record() -> None:
    result = run_check(RECORD)
    assert result.returncode == 0, result.stdout + result.stderr


def test_check_goes_red_on_a_mutated_count(tmp_path: Path) -> None:
    record = load_record()
    target = next(f for f in record["figures"] if f["id"] == "distinct_answers.pointer-stable")
    assert target["value"] == 48
    target["value"] = 47
    mutated = write_record(tmp_path / "QUALITY-CARRY-FORWARD.json", record)
    result = run_check(mutated)
    assert result.returncode == 1, "a mutated count must fail --check"
    assert "DRIFT" in result.stdout


def test_check_goes_red_on_a_drifted_source_digest(tmp_path: Path) -> None:
    record = load_record()
    target = next(f for f in record["figures"] if f["id"] == "counterfactual_modal_pass_per_arm")
    target["source_sha256"] = "0" * 64
    mutated = write_record(tmp_path / "QUALITY-CARRY-FORWARD.json", record)
    result = run_check(mutated)
    assert result.returncode == 1, "a drifted source sha must fail --check"
    assert "source_sha256" in result.stdout


def test_check_goes_red_when_a_statement_is_dropped(tmp_path: Path) -> None:
    record = load_record()
    record["statements"] = [s for s in record["statements"] if s["id"] != "statement-2"]
    mutated = write_record(tmp_path / "QUALITY-CARRY-FORWARD.json", record)
    result = run_check(mutated)
    assert result.returncode == 1, "a statements block missing sentence 2 must fail --check"
    assert "lost a required sentence" in result.stdout
