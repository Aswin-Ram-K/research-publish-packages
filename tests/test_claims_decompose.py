"""Offline tests for claim decomposition (U4.0).

Every test injects a client double: **zero** live LLM calls.  Fixtures:
``tests/fixtures/claims-store/target/`` (a 301-line README.md and two small
source files) and ``tests/fixtures/claims-store/graph.json`` (two nodes).

Red->green guards (reverted fix -> failing test, restored -> passing) are pasted
in the docstrings of :func:`test_guard_a_zero_verified_refs_rejected` and
:func:`test_guard_b_empty_settled_by_rejected`.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from resextract import store
from resextract.claims.decompose import (
    CLAIM_KINDS,
    INITIAL_VERIFICATION_STATE,
    decompose_candidates,
    normalise_text,
)
from resextract.llm import BudgetExhausted, UnparseableOutput

FIX = Path(__file__).resolve().parent / "fixtures" / "claims-store"

CAND_A = {
    "kind": "novel_primitive",
    "title": "alpha primitive",
    "summary": "alpha_main is defined in src/alpha.py",
    "provenance_json": [
        {"ref": "alpha_main", "kind": "graph_node", "exists": True},
        {"ref": "src/alpha.py#L3", "kind": "file_lines", "exists": True},
    ],
    "graph_nodes_json": ["alpha_main"],
}
CAND_B = {
    "kind": "invariant_or_enforcement",
    "title": "beta helper",
    "summary": "beta_helper is defined in src/beta.py",
    "provenance_json": [
        {"ref": "beta_helper", "kind": "graph_node", "exists": True},
        {"ref": "src/beta.py#L3", "kind": "file_lines", "exists": True},
    ],
    "graph_nodes_json": ["beta_helper"],
}

README_LINES = len((FIX / "target" / "README.md").read_text(encoding="utf-8").splitlines())


class ReplayClient:
    """Injected/replay double: no network, no model."""

    producer = "replay"

    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = 0
        self.seen_messages = []

    def call_json(self, messages, schema, **kwargs):
        self.calls += 1
        self.seen_messages.append(messages)
        if not self.payloads:
            raise AssertionError("ReplayClient ran out of scripted payloads")
        payload = self.payloads.pop(0)
        if isinstance(payload, BaseException):
            raise payload
        return schema.model_validate(payload)


def claim(text, kind="architectural", settled_by="Re-read the cited ref and re-run verify_provenance.",
          refs=("alpha_main",), **extra):
    body = {"text": text, "kind": kind, "settled_by": settled_by,
            "provenance_refs": list(refs), "confidence": 0.5}
    body.update(extra)
    return body


def make_store(tmp_path, candidates):
    db = tmp_path / "state.sqlite"
    store.init_db(db)
    con = store.connect(db)
    ids = []
    for cand in candidates:
        ids.append(store.insert_candidate(
            con, kind=cand["kind"], title=cand["title"], summary=cand["summary"],
            provenance_json=cand["provenance_json"], graph_nodes_json=cand["graph_nodes_json"],
            producer="replay"))
    con.commit()
    con.close()
    return db, ids


def repo(tmp_path):
    target = tmp_path / "repo"
    if not target.exists():
        shutil.copytree(FIX / "target", target)
    return target


def run(tmp_path, candidates, payloads, *, out=None, prompt_version="v1", client=None,
        db=None, ids=None):
    if db is None:
        db, ids = make_store(tmp_path, candidates)
    target = repo(tmp_path)
    client = client or ReplayClient(payloads)
    report = decompose_candidates(
        [{**c, "id": i} for c, i in zip(candidates, ids)],
        client=client, graph_path=FIX / "graph.json", target_root=target,
        store_path=db, out_dir=out or (tmp_path / "claims"), prompt_version=prompt_version)
    return report, client, db


def stored_claims(db):
    con = store.connect(db)
    rows = con.execute('SELECT id, candidate_id, kind, "text", provenance_json, verification_state, confidence FROM claims ORDER BY id').fetchall()
    con.close()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------- #

def test_two_atomic_claims_each_verified(tmp_path):
    report, client, db = run(tmp_path, [CAND_A], [{"claims": [
        claim("alpha_main is defined at src/alpha.py line 3.", refs=["alpha_main", "src/alpha.py#L3"]),
        claim("alpha_main returns its argument unchanged.", kind="behavioural", refs=["src/alpha.py#L3"]),
    ]}])
    assert client.calls == 1
    assert len(report.claims) == 2
    for c in report.claims:
        assert c.settled_by.strip()
        assert c.provenance_refs, "each claim needs >=1 verified ref"
        assert all(p["exists"] for p in c.provenance if p["ref"] in c.provenance_refs)
        assert c.verification_state == "unverified"
        assert c.kind in CLAIM_KINDS
    assert len(stored_claims(db)) == 2


def test_guard_a_zero_verified_refs_rejected(tmp_path):
    """RED->GREEN guard A: zero verified refs => rejected, never stored.

    RED (guard reverted: `if verdict.verified == 0:` -> `if False:`):
        FAILED tests/test_claims_decompose.py::test_guard_a_zero_verified_refs_rejected
        tests/test_claims_decompose.py:155: AssertionError   (1 failed in 0.08s)
        sha_before = sha_after = 95a38b36c69dede75f062d5d1602b9926f60bf41db1199eb56c441d8d6a900e9
        (backup restored bit-identical)
    GREEN (restored): 1 passed in 0.07s (full file: 11 passed in 0.10s)
    """
    report, _, db = run(tmp_path, [CAND_A], [{"claims": [
        claim("alpha_main is defined at src/alpha.py line 99999.",
              refs=["src/alpha.py#L99999-L99999"]),
    ]}])
    assert report.claims == []
    assert len(report.rejected) == 1
    assert "zero verified provenance refs" in report.rejected[0]["reason"]
    assert stored_claims(db) == []


def test_guard_b_empty_settled_by_rejected(tmp_path):
    """RED->GREEN guard B: an empty settled_by is not a claim.

    RED (guard reverted: `if not settled_by.strip():` -> `if False:`):
        FAILED tests/test_claims_decompose.py::test_guard_b_empty_settled_by_rejected
        tests/test_claims_decompose.py:171: AssertionError   (1 failed in 0.07s)
        sha_before = sha_after = 95a38b36c69dede75f062d5d1602b9926f60bf41db1199eb56c441d8d6a900e9
        (backup restored bit-identical; `diff -q` clean)
    GREEN (restored): 1 passed in 0.07s (full file: 11 passed in 0.10s)
    """
    report, _, db = run(tmp_path, [CAND_A], [{"claims": [
        claim("alpha_main is defined at src/alpha.py line 3.", settled_by="", refs=["alpha_main"]),
    ]}])
    assert report.claims == []
    assert len(report.rejected) == 1
    assert "empty settled_by" in report.rejected[0]["reason"]
    assert stored_claims(db) == []


def test_fabricated_span_on_real_file_rejected(tmp_path):
    """A real, plausible path must not rescue a fabricated citation."""
    assert README_LINES < 99999, "fixture README must be far shorter than the fabricated span"
    report, _, db = run(tmp_path, [CAND_A], [{"claims": [
        claim("The README documents the pipeline at line 99999.",
              refs=[f"README.md#L99999-L100000"]),
    ]}])
    assert report.claims == []
    assert len(report.rejected) == 1
    reason = report.rejected[0]["reason"]
    assert "zero verified provenance refs" in reason
    assert "beyond" in reason and "README.md" in reason
    assert stored_claims(db) == []


def test_dedupe_same_normalised_text_across_candidates(tmp_path):
    shared = "beta_helper is defined at src/beta.py line 3."
    report, _, db = run(tmp_path, [CAND_A, CAND_B], [
        {"claims": [claim(shared, refs=["alpha_main"])]},
        {"claims": [claim(shared.upper() + "  ", refs=["beta_helper"])]},
    ])
    assert len(report.claims) == 1
    assert report.deduped == 1
    assert len(stored_claims(db)) == 1
    assert normalise_text(shared) == normalise_text(shared.upper() + "  ")


def test_unparseable_output_on_one_candidate_continues(tmp_path):
    report, client, db = run(tmp_path, [CAND_A, CAND_B], [
        UnparseableOutput("{not json", "1 validation error for _Decomposition"),
        {"claims": [claim("beta_helper is defined at src/beta.py line 3.", refs=["beta_helper"])]},
    ])
    assert client.calls == 2
    assert [d["kind"] for d in report.degradations] == ["unparseable_output"]
    assert report.degradations[0]["candidate_id"] is not None
    assert len(report.claims) == 1
    assert report.claims[0].text.startswith("beta_helper")
    assert len(stored_claims(db)) == 1


def test_truncation_length_empty_content_is_not_zero_claims(tmp_path):
    report, _, db = run(tmp_path, [CAND_A], [
        UnparseableOutput("", "finish_reason=length: empty content (reasoning consumed max_tokens)"),
    ])
    assert report.claims == []
    assert report.partial is False
    assert len(report.degradations) == 1
    assert report.degradations[0]["kind"] == "truncation"
    assert "truncation, NOT zero claims" in report.degradations[0]["detail"]
    assert stored_claims(db) == []


def test_budget_exhausted_partial_keeps_earlier_claims(tmp_path):
    exhausted = BudgetExhausted("call budget exhausted: 1/1 calls used", reason="calls",
                                tokens_used=0, max_tokens=None, calls_used=1, max_calls=1)
    report, _, db = run(tmp_path, [CAND_A, CAND_B], [
        {"claims": [claim("alpha_main is defined at src/alpha.py line 3.", refs=["alpha_main"])]},
        exhausted,
    ])
    assert report.partial is True
    assert any(d["kind"] == "budget_exhausted" for d in report.degradations)
    assert len(report.claims) == 1
    assert len(stored_claims(db)) == 1
    out = Path(report.run_dir)
    assert json.loads((out / "report.json").read_text())["status"] == "partial"


def test_idempotent_resume_and_prompt_version_change(tmp_path):
    payloads = [{"claims": [claim(f"alpha_main is defined at src/alpha.py line {i}.", refs=["alpha_main"])]} for i in (3, 4)]
    db, ids = make_store(tmp_path, [CAND_A])
    report, client, _ = run(tmp_path, [CAND_A], [payloads[0]], db=db, ids=ids)
    assert report.resumed is False and client.calls == 1

    second = ReplayClient([])
    again, _, _ = run(tmp_path, [CAND_A], [], db=db, ids=ids, client=second)
    assert again.resumed is True
    assert second.calls == 0, "a resumed run must make zero model calls"
    assert again.model_calls == 0
    assert len(again.claims) == 1
    assert len(stored_claims(db)) == 1, "resume must not duplicate rows"

    # same text, different prompt_version => re-decomposed (not resumed) but the
    # existing claim is not duplicated (the DB-seeded dedupe holds across runs)
    third = ReplayClient([payloads[0]])
    changed, _, _ = run(tmp_path, [CAND_A], [payloads[0]], db=db, ids=ids,
                        prompt_version="v2", client=third)
    assert changed.resumed is False
    assert third.calls == 1, "a changed prompt_version must re-decompose"
    assert changed.deduped == 1
    assert len(stored_claims(db)) == 1, "a re-decompose must not duplicate an existing claim"


def test_metering_injected_client_is_not_model_derived(tmp_path):
    report, _, db = run(tmp_path, [CAND_A], [{"claims": [
        claim("alpha_main is defined at src/alpha.py line 3.", refs=["alpha_main"])]}])
    assert report.model_calls == 0
    assert report.producer == "replay"
    assert report.usage_records == 0
    payload = json.loads((Path(report.run_dir) / "report.json").read_text())
    assert payload["model_calls"] == 0 and payload["producer"] == "replay"
    assert Path(report.run_dir, "CLAIMS.md").is_file()
    assert (Path(report.run_dir) / "claims.jsonl").read_text().count("\n") == 1


def test_vocabularies_are_closed_and_documented(tmp_path):
    assert CLAIM_KINDS == ("measured", "behavioural", "architectural", "comparative", "negative", "definitional")
    assert INITIAL_VERIFICATION_STATE == "unverified"
    con = store.connect("state/state.sqlite") if Path("state/state.sqlite").is_file() else None
    if con is not None:
        ddl = con.execute("SELECT sql FROM sqlite_master WHERE name='claims'").fetchone()[0]
        con.close()
        assert "CHECK" not in ddl, "if the store later declares a CHECK, conform to it instead"
