#!/usr/bin/env python3
"""AGENTIC-CELL tests — offline, fake transport, zero requests.

    TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
        experiments/ptr-engine/longrun/tests/test_agentic_cell.py -q

WHAT EACH TEST PINS
-------------------
(a) a full episode emits one row per request and every row passes ``validate_row``;
(b) the episode stops on the final answer and sends nothing after it;
(c) ``--max-requests`` stops the episode at the cap, not one past it;
(d) the fold fires at least once inside a 16-step episode, and the compiler's own fold
    record says how many turns it dropped;
(e) a checkpoint whose value the policy dropped and which the model then got wrong is
    classified ``lost_then_failed`` — the design's signal, not a model error;
(f) each policy drops something when its window is exceeded, and ``none`` drops nothing;
(g) ``expected_present`` is true when the graded value is in the prompt and false when the
    policy dropped it — the E3 field, read from the exact message list that was sent;
(h) a path escaping the root is refused and the refusal is recorded on the row, not
    raised;
(i) the dry run sends nothing and its count equals the live run's row count;
(j) a live run refuses BEFORE the first request when the plan exceeds the cap, and writes
    no row file;
(k) the assignment's smoke: 1 task x 1 arm x 1 rep writes one row with
    ``steps_used <= 16``, ``requests <= 20``, ``compactions >= 1``;
(l) ``--offline`` re-grades an existing row file and sends nothing.

RED -> GREEN RECORD (house style)
---------------------------------
Each guard was reverted in ``agentic_cell.py``, the named test was run alone, and the
failure below is quoted from that run.  The revert is named so a later reader can repeat
it.  Command for every one of them::

    TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
        experiments/ptr-engine/longrun/tests/test_agentic_cell.py::<test> -q -x

(b) early stop — reverted by deleting the ``break`` after ``stopped = "final_answer"`` in
    ``run_episode``.  ``test_early_stop_on_the_final_answer``::

        >       assert row["steps_used"] == 4
        E       assert 16 == 4

(c) request cap — reverted ``if requests >= int(max_requests)`` to
    ``if requests > int(max_requests)``.  ``test_request_cap_stops_the_episode``::

        >       assert row["requests"] == 5 == len(tr.calls)
        E       assert 6 == 5

(d) fold fires — reverted by passing ``compact_every=10 ** 6`` to ``make_arm`` inside
    ``run_episode`` (a fold distance no 16-step episode can reach).
    ``test_fold_fires_at_least_once_in_a_16_step_episode``::

        >       assert row["compactions"] >= 1
        E       assert 0 >= 1

(e) lost_then_failed — reverted by emptying the ``lost`` list in ``_verdict``.
    ``test_lost_then_failed_is_classified``::

        >       assert row["verdict"] == "lost_then_failed"
        E       AssertionError: assert 'unsolved' == 'lost_then_failed'

(g) expected_present — reverted by hard-coding ``"expected_present": True`` on the graded
    row.  ``test_expected_present_false_when_the_policy_dropped_it``::

        >       assert final["expected_present"] is False
        E       assert True is False

(h) path refusal — reverted by appending a tool block only when the call executed, so a
    refusal vanished from the transcript.  ``test_path_escaping_the_root_is_refused_on_the_row``::

        >       assert any('<tool_result error="path_refused"/>' in str(m.get("content"))
        E       assert False

(j) budget refusal — reverted by replacing ``check_budget(...)`` with a permissive dict,
    so the first request went out.  ``test_live_run_refuses_before_sending_over_the_cap``::

        E       AssertionError: a request was sent

(m) prompt_declares_no_tool — reverted by deleting the ``check_prompt_declares_tool(task)``
    call in ``run_episode``.  ``test_prompt_declares_no_tool_refuses_before_any_request``::

        E       AssertionError: sent

(m2) tools_schema_sent — reverted by hard-coding ``tools_schema_sent = False``.
    ``test_tools_schema_sent_is_true_on_every_row``::

        >           assert row["tools_schema_sent"] is True, row["step"]
        E       AssertionError: 1
        E       assert False is True

(m3) dry-run folds — reverted by hard-coding ``compactions = 0`` in the dry-run branch.
    ``test_dry_run_reports_compactions_per_arm``::

        >           assert seen[arm]["compactions"] >= 1, arm
        E       AssertionError: pinned
        E       assert 0 >= 1

(m4) CLI dry-run folds — reverted by deleting the ``dry_run arm=…`` print in ``main``.
    ``test_cli_dry_run_reports_compactions_per_arm``::

        >       assert len(lines) == 3
        E       assert 0 == 3

(m5) CLI void refusal — reverted by deleting the ``return 3`` after the void check.
    ``test_cli_dry_run_refuses_a_void_plan``::

        >       assert rc == 3
        E       assert 0 == 3

(m6) offline running totals — reverted ``max(...)`` to ``sum(...)`` for ``evicted``.
    ``test_offline_regrades_rows_without_a_request``::

        >       assert ep["evicted"] == 8
        E       assert 64 == 8
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import agentic_cell as AC  # noqa: E402

FACT_A = "4017"
FACT_B = "4021"


# ------------------------------------------------------------------ fixtures
def make_fixture(tmp_path, *, task_id="AG-T1", turns=4, final_turn=None,
                 cp1_turn=2, window_tokens=4096):
    """A minimal ``consonance.longrun-fixture/2`` task the cell can actually run.

    ``documents`` is what ``run_longrun.index_lines`` renders L0's world index from, and
    ``checkpoints[].answer_spec`` is what ``grade_v5.derive_truth`` derives the graded
    value from — both are v2 fields, so this fixture exercises the real loader rather than
    a test-only shape.
    """
    snap = tmp_path / "snap"
    snap.mkdir(parents=True, exist_ok=True)
    consts = snap / "consts.py"
    consts.write_text("SYM_A = %s\nSYM_B = %s\n" % (FACT_A, FACT_B), encoding="utf-8")
    body = consts.read_text(encoding="utf-8")
    final_turn = final_turn or turns
    return {
        "schema": "consonance.longrun-fixture/2",
        "task_id": task_id,
        "N": turns,
        "bytes_per_token": 3.122,
        "window_tokens": window_tokens,
        "wall_tokens": window_tokens,
        "system_prompt": "Use read_file to find the constant the caller overrides.",
        "items": [{"id": "consts.py", "body": body}],
        "documents": [{"doc_id": "consts.py", "scope": "granted", "revoked": False,
                       "revoked_at_turn": None,
                       "revisions": [{"revision": 1, "value": body, "live_from_turn": 1}]}],
        "turns": [{"turn": i, "kind": "work",
                   "question": "Turn %d: read consts.py." % i}
                  for i in range(1, turns + 1)],
        "checkpoints": [
            {"id": "cp1", "turn": cp1_turn, "question": "What is SYM_A?",
             "expected": FACT_A,
             "answer_spec": {"kind": "NUM",
                             "derive": {"rule": "constant_value", "symbol": "SYM_A",
                                        "file": str(consts)}}},
            {"id": "cp2", "turn": final_turn, "question": "What is SYM_B?",
             "expected": FACT_B,
             "answer_spec": {"kind": "NUM",
                             "derive": {"rule": "constant_value", "symbol": "SYM_B",
                                        "file": str(consts)}}},
        ],
    }


def write_task(tmp_path, fixture):
    path = tmp_path / ("%s.json" % fixture["task_id"])
    path.write_text(json.dumps(fixture), encoding="utf-8")
    return str(path)


def make_task(tmp_path, **kw):
    return AC.load_task(write_task(tmp_path, make_fixture(tmp_path, **kw)))


class FakeTransport:
    """A scripted model.  ``script(n, messages)`` returns the n-th reply."""

    def __init__(self, script):
        self.script = script
        self.calls = []

    def send(self, messages, tools=None):
        self.calls.append({"messages": [dict(m) for m in messages],
                           "tools": list(tools or [])})
        return self.script(len(self.calls), messages)


class ExplodingTransport:
    """Proves a dry run / refused run never sends: any call is a test failure."""

    def send(self, messages, tools=None):
        raise AssertionError("a request was sent")


def tool_reply(path="consts.py", start=1, end=5, call_id="call_1"):
    return {"content": "",
            "tool_calls": [{"id": call_id, "name": "read_file",
                            "arguments_json": {"path": path, "start_line": start,
                                               "end_line": end},
                            "arguments_error": None}],
            "prompt_tokens": 1000, "completion_tokens": 0, "cached_tokens": 0}


def answer_reply(value=FACT_A):
    return {"content": "ANSWER: NUM %s" % value, "tool_calls": [],
            "prompt_tokens": 1000, "completion_tokens": 0, "cached_tokens": 0}


def read_rows(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def run(tmp_path, arm, script, *, max_steps=4, max_requests=20, budget_cap=1000,
        spent=0, transport=None, turns=4, final_turn=None, out_path=None,
        rows_path=None, dry_run=False, compact_every=AC.DEFAULT_COMPACT_EVERY,
        window_turns=AC.DEFAULT_WINDOW_TURNS, cp1_turn=None):
    task = make_task(tmp_path, turns=turns, final_turn=final_turn,
                     cp1_turn=cp1_turn if cp1_turn is not None
                     else (4 if turns >= 16 else 2))
    tr = transport if transport is not None else FakeTransport(script)
    res = AC.run_cell([task], arm, 1, tr, out_path=out_path, rows_path=rows_path,
                      max_steps=max_steps, max_requests=max_requests,
                      budget_cap=budget_cap, spent=spent,
                      repo_root=str(tmp_path / "snap"), log=lambda *a: None,
                      dry_run=dry_run, compact_every=compact_every,
                      window_turns=window_turns)
    return res, tr


# ------------------------------------------------------------------ (a)
def test_full_episode_emits_one_valid_row_per_request(tmp_path):
    script = lambda n, m: tool_reply(call_id="c%d" % n) if n in (1, 3) else answer_reply(
        FACT_A if n == 2 else FACT_B)
    res, tr = run(tmp_path, "none", script)
    rows = res["request_rows"]
    assert res["rows"] == 1
    assert len(rows) == 4 == len(tr.calls)
    for row in rows:
        AC.validate_row(row)
    assert [r["kind"] for r in rows] == ["work", "work", "work", "final"]
    assert [r["step"] for r in rows] == [1, 2, 3, 4]
    assert rows[1]["verified"] is True
    assert FACT_A in rows[1]["answer"]
    assert rows[3]["verified"] is True
    # the tool result really reached the transcript the model saw
    assert any(FACT_A in str(m.get("content")) for m in tr.calls[1]["messages"])


# ------------------------------------------------------------------ (b)
def test_early_stop_on_the_final_answer(tmp_path):
    script = lambda n, m: tool_reply(call_id="c%d" % n) if n in (1, 3) else answer_reply(
        FACT_A if n == 2 else FACT_B)
    res, tr = run(tmp_path, "none", script, max_steps=16, turns=16, final_turn=4,
                  cp1_turn=2)
    row = res["episodes"][0]
    assert row["stopped"] == "final_answer"
    assert row["steps_used"] == 4
    assert res["requests"] == 4 == len(tr.calls)
    assert row["solved"] is True


# ------------------------------------------------------------------ (c)
def test_request_cap_stops_the_episode(tmp_path):
    script = lambda n, m: tool_reply(call_id="c%d" % n)
    res, tr = run(tmp_path, "none", script, max_steps=16, max_requests=5, turns=16)
    row = res["episodes"][0]
    assert row["requests"] == 5 == len(tr.calls)
    assert row["stopped"] == "max_requests"
    assert row["steps_used"] == 5
    assert row["solved"] is False


# ------------------------------------------------------------------ (d)
def test_fold_fires_at_least_once_in_a_16_step_episode(tmp_path):
    script = lambda n, m: (answer_reply(FACT_A) if n == 4
                           else answer_reply(FACT_B) if n == 16
                           else tool_reply(call_id="c%d" % n))
    res, _tr = run(tmp_path, "bounded-context-fetch", script, max_steps=16, turns=16)
    row = res["episodes"][0]
    assert row["compactions"] >= 1
    assert row["verdict"] != "void"
    folds = [r for r in res["request_rows"] if r["fold_event"]]
    assert folds, "no request row recorded a fold"
    assert folds[0]["fold_kind"] in ("interval", "pressure")
    assert folds[0]["dropped_turns"] >= 1
    assert row["evicted"] >= 1


# ------------------------------------------------------------------ (e)
def test_lost_then_failed_is_classified(tmp_path):
    # a model that answers only from what is in view: the fold is what makes it fail
    def script(n, messages):
        if n == 4:
            return answer_reply(FACT_A)
        if n == 16:
            seen = FACT_B in AC.prompt_text(messages)
            return answer_reply(FACT_B if seen else "0")
        return tool_reply(call_id="c%d" % n)

    res, _tr = run(tmp_path, "masking-no-fetch", script, max_steps=16, turns=16)
    row = res["episodes"][0]
    assert row["verdict"] == "lost_then_failed"
    final = [c for c in row["checkpoints"] if c["step"] == 16][0]
    assert final["ok"] is False
    assert final["expected_present"] is False


# ------------------------------------------------------------------ (f)
def test_each_policy_drops_and_none_does_not(tmp_path):
    script = lambda n, m: (answer_reply(FACT_A) if n == 4
                           else answer_reply(FACT_B) if n == 16
                           else tool_reply(call_id="c%d" % n))
    for arm in AC.ARMS:
        res, _tr = run(tmp_path, arm, script, max_steps=16, turns=16)
        row = res["episodes"][0]
        if arm == "none":
            assert row["evicted"] == 0, arm
            assert row["compactions"] == 0, arm
            assert row["fold_mechanism"] == "none", arm
            continue
        assert row["evicted"] >= 1, arm
        assert row["fold_mechanism"] in ("mask", "journal-drop"), arm
    # the folding arms fold; the masking arm masks
    assert run(tmp_path, "pinned", script, max_steps=16, turns=16)[0]["episodes"][0][
        "compactions"] >= 1
    assert run(tmp_path, "masking-no-fetch", script, max_steps=16, turns=16)[0][
        "episodes"][0]["compactions"] == 0


# ------------------------------------------------------------------ (g)
def test_expected_present_true_when_the_value_is_in_the_prompt(tmp_path):
    script = lambda n, m: (answer_reply(FACT_A) if n == 4
                           else answer_reply(FACT_B) if n == 16
                           else tool_reply(call_id="c%d" % n))
    res, _tr = run(tmp_path, "none", script, max_steps=16, turns=16)
    final = [r for r in res["request_rows"] if r["kind"] == "final"][0]
    assert final["expected_present"] is True
    assert final["verified"] is True
    # a work row is not graded, so the field is null, never a default
    work = [r for r in res["request_rows"] if r["kind"] == "work"][0]
    assert work["expected_present"] is None
    assert work["verified"] is None


def test_expected_present_false_when_the_policy_dropped_it(tmp_path):
    def script(n, messages):
        if n == 4:
            return answer_reply(FACT_A)
        if n == 16:
            return answer_reply(FACT_B if FACT_B in AC.prompt_text(messages) else "0")
        return tool_reply(call_id="c%d" % n)

    res, _tr = run(tmp_path, "masking-no-fetch", script, max_steps=16, turns=16)
    final = [r for r in res["request_rows"] if r["kind"] == "final"][0]
    assert final["fold_event"] is False  # the mask arm does not fold
    assert final["dropped_turns"] >= 1
    assert final["expected_present"] is False
    assert final["verified"] is False


# ------------------------------------------------------------------ (h)
def test_path_escaping_the_root_is_refused_on_the_row(tmp_path):
    script = lambda n, m: (tool_reply(path="../../etc/passwd") if n == 1
                           else answer_reply(FACT_A) if n == 2
                           else answer_reply(FACT_B))
    res, tr = run(tmp_path, "none", script)
    rec = res["request_rows"][0]["tool_calls"][0]
    assert rec["ok"] is False
    assert rec["error"] == "path_refused"
    assert rec["bytes"] == 0
    # the refusal reached the transcript as a tool result, not as an exception
    assert any('<tool_result error="path_refused"/>' in str(m.get("content"))
               for m in tr.calls[1]["messages"])


def test_absolute_and_secret_shaped_paths_are_refused(tmp_path):
    root = str(tmp_path / "snap")
    os.makedirs(root, exist_ok=True)
    for bad in ("/etc/passwd", "~/x", "a/../../b", ".env", "keys/id_rsa"):
        target, reason = AC.resolve_read_path(bad, root)
        assert target is None and reason == "path_refused", bad


def test_grep_is_bounded_and_accepts_a_directory(tmp_path):
    root = tmp_path / "snap"
    (root / "sub").mkdir(parents=True, exist_ok=True)
    (root / "sub" / "more.py").write_text(
        "".join("HIT = %d\n" % i for i in range(200)), encoding="utf-8")
    text, rec = AC.grep_text(str(root), "HIT", "*.py")
    assert rec.get("error") is None
    assert rec["hits"] == AC.run_longrun.GREP_MAX_HITS
    assert rec["truncated"] is True
    assert text.splitlines()[0].startswith("sub/more.py:1: HIT = 0")
    # a directory is a legal grep path; a read of one is still refused
    assert AC.resolve_read_path("sub", str(root), allow_dir=True)[0] is not None
    assert AC.resolve_read_path("sub", str(root)) == (None, "path_not_found")
    assert AC.grep_text(str(root), "(")[1]["error"] == "bad_pattern"
    assert AC.grep_text(str(root), "")[1]["error"] == "missing_pattern"


# ------------------------------------------------------------------ (i)
def test_dry_run_sends_nothing_and_matches_the_live_row_count(tmp_path):
    task = make_task(tmp_path)
    planned = AC.plan([task], "none", 1, 4)
    dry, _tr = run(tmp_path, "none", None, transport=ExplodingTransport(), dry_run=True)
    assert dry["planned"] == planned["planned"] == 4
    assert dry["rows"] == 0

    script = lambda n, m: (answer_reply(FACT_A) if n == 2
                           else answer_reply(FACT_B) if n == 4
                           else tool_reply(call_id="c%d" % n))
    res, _tr = run(tmp_path, "none", script)
    assert len(res["request_rows"]) == dry["planned"]


def test_dry_run_line_names_the_plan(tmp_path, capsys):
    task = make_task(tmp_path)
    AC.run_cell([task], "compact", 2, ExplodingTransport(), dry_run=True,
                budget_cap=12094, spent=7, repo_root=str(tmp_path / "snap"))
    line = capsys.readouterr().out.strip()
    assert line.startswith("planned_requests=")
    assert "arm=compact" in line and "reps=2" in line and "spent=7" in line


# ------------------------------------------------------------------ (j)
def test_live_run_refuses_before_sending_over_the_cap(tmp_path):
    task = make_task(tmp_path)
    out = str(tmp_path / "rows-refused.jsonl")
    try:
        AC.run_cell([task], "none", 1, ExplodingTransport(), out_path=out,
                    max_steps=4, budget_cap=2, spent=0,
                    repo_root=str(tmp_path / "snap"), log=lambda *a: None)
    except AC.BudgetRefusal as exc:
        assert "planned=4" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("a run over the cap must refuse")
    assert not os.path.exists(out)


def test_quota_refusal_names_spent_and_cap(tmp_path):
    task = make_task(tmp_path)
    try:
        AC.check_budget(10, spent=AC.cell_mod.PROJECT_QUOTA - 5)
    except AC.BudgetRefusal as exc:
        assert "planned=10" in str(exc) and "headroom 5" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("a plan over the quota must refuse")


# ------------------------------------------------------------------ (k)
def test_smoke_one_task_one_arm_one_rep_writes_one_row(tmp_path):
    """The assignment's smoke: one row, inside every budget, with a fold."""
    script = lambda n, m: (answer_reply(FACT_A) if n == 4
                           else answer_reply(FACT_B) if n == 16
                           else tool_reply(call_id="c%d" % n))
    out = str(tmp_path / "AGENTIC-smoke.jsonl")
    rows_out = str(tmp_path / "rows-agentic-smoke.jsonl")
    res, tr = run(tmp_path, "bounded-context-fetch", script, max_steps=16, turns=16,
                  out_path=out, rows_path=rows_out)
    episodes = read_rows(out)
    assert len(episodes) == 1
    row = episodes[0]
    assert row["steps_used"] <= 16
    assert row["requests"] <= 20
    assert row["compactions"] >= 1
    assert row["solved"] is True
    assert row["planned_max"] == res["planned"]
    for key in ("task", "arm", "rep", "solved", "checkpoints", "steps_used", "requests",
                "refetch_count", "compactions", "evicted", "prompt_tokens_max",
                "billed_tokens"):
        assert key in row, key
    assert len(read_rows(rows_out)) == row["requests"] == len(tr.calls)


# ------------------------------------------------------------------ (l)
def test_offline_regrades_rows_without_a_request(tmp_path):
    script = lambda n, m: (answer_reply(FACT_A) if n == 4
                           else answer_reply(FACT_B) if n == 16
                           else tool_reply(call_id="c%d" % n))
    rows_out = str(tmp_path / "rows-agentic-offline.jsonl")
    run(tmp_path, "bounded-context-fetch", script, max_steps=16, turns=16,
        rows_path=rows_out)
    episodes = AC.offline_episodes(rows_out)
    assert len(episodes) == 1
    ep = episodes[0]
    assert ep["offline"] is True
    assert ep["requests"] == 16
    assert ep["solved"] is True
    assert [c["step"] for c in ep["checkpoints"]] == [4, 16]
    # running totals are read as totals, not summed down the column
    assert ep["compactions"] == 1
    assert ep["evicted"] == 8
    assert ep["refetch_count"] == 13
    assert ep["verdict"] == "solved"
    assert ep["fold_mechanism"] == "journal-drop"


# ------------------------------------------------------------------ (m) m00447
def test_a_non_v2_task_is_refused_by_name(tmp_path):
    """Only ``consonance.longrun-fixture/2`` is accepted; anything else is named."""
    path = tmp_path / "AG-OLD.json"
    path.write_text(json.dumps({"task_id": "AG-OLD", "version": "AG-OLD.v1",
                                "steps": [{"prompt": "read a"}],
                                "final_question": "q", "expected": "1",
                                "answer_form": "NUM"}), encoding="utf-8")
    try:
        AC.load_task(str(path))
    except AC.TaskError as exc:
        assert "unsupported_task_schema" in str(exc)
        assert "AG-OLD.json" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("a non-v2 task must be refused")
    # a v2 document with the wrong schema string is refused the same way
    fixture = make_fixture(tmp_path)
    fixture["schema"] = "consonance.longrun-fixture/1"
    try:
        AC.load_task(write_task(tmp_path, fixture))
    except AC.TaskError as exc:
        assert "unsupported_task_schema: consonance.longrun-fixture/1" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("v1 must be refused")


def test_prompt_declares_no_tool_refuses_before_any_request(tmp_path):
    """A prompt that never names the tool is refused by name, not measured as a failure."""
    fixture = make_fixture(tmp_path)
    fixture["system_prompt"] = "Find the constant the caller overrides."
    task = AC.load_task(write_task(tmp_path, fixture))
    try:
        AC.run_cell([task], "none", 1, ExplodingTransport(), max_steps=4,
                    repo_root=str(tmp_path / "snap"), log=lambda *a: None)
    except AC.TaskError as exc:
        assert "prompt_declares_no_tool" in str(exc)
        assert "AG-T1" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("a task that cannot fetch must be refused")
    # the guard is on the episode too, so a direct call cannot bypass it
    try:
        AC.run_episode(task, "none", 1, cfg=AC.EpisodeCfg(model="fake"),
                       send=lambda c, m: (_ for _ in ()).throw(
                           AssertionError("sent")),
                       root=str(tmp_path / "snap"), steps=4)
    except AC.TaskError as exc:
        assert "prompt_declares_no_tool" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("run_episode must refuse too")


def test_tools_schema_sent_is_true_on_every_row(tmp_path):
    script = lambda n, m: (answer_reply(FACT_A) if n == 2
                           else answer_reply(FACT_B) if n == 4
                           else tool_reply(call_id="c%d" % n))
    res, _tr = run(tmp_path, "none", script)
    assert res["request_rows"]
    for row in res["request_rows"]:
        assert row["tools_schema_sent"] is True, row["step"]
    assert res["episodes"][0]["tools_schema_sent"] is True
    # the schema really is in the body the client would build
    cfg = AC.EpisodeCfg(model="fake", tools="read_file,grep")
    names = {(t.get("function") or {}).get("name")
             for t in AC.episode_tools_body_members(cfg).get("tools") or []}
    assert {"read_file", "grep"} <= names


def test_row_carries_fetch_rounds_and_running_totals(tmp_path):
    script = lambda n, m: (answer_reply(FACT_A) if n == 4
                           else answer_reply(FACT_B) if n == 16
                           else tool_reply(call_id="c%d" % n))
    res, _tr = run(tmp_path, "bounded-context-fetch", script, max_steps=16, turns=16)
    rows = res["request_rows"]
    assert rows[0]["fetch_rounds"] == 1
    assert rows[0]["compactions"] == 0
    assert rows[0]["evicted"] == 0
    assert rows[0]["prompt_tokens_max"] == 1000
    fold = [r for r in rows if r["fold_event"]][0]
    assert fold["compactions"] == 1
    assert fold["evicted"] >= 1
    # the running total never goes backwards
    assert [r["compactions"] for r in rows] == sorted(r["compactions"] for r in rows)
    assert [r["evicted"] for r in rows] == sorted(r["evicted"] for r in rows)


def test_dry_run_reports_compactions_per_arm(tmp_path):
    """A dry run must show the fold firing before the live budget is spent."""
    task = make_task(tmp_path, turns=16)
    seen = {}
    for arm in AC.ARMS:
        res = AC.run_cell([task], arm, 1, ExplodingTransport(), dry_run=True,
                          max_steps=16, repo_root=str(tmp_path / "snap"),
                          log=lambda *a: None)
        seen[arm] = res
        assert res["rows"] == 0
    for arm in ("pinned", "bounded-context-fetch", "compact"):
        assert seen[arm]["compactions"] >= 1, arm
        assert seen[arm]["folds"][0]["void"] is False, arm
    assert seen["masking-no-fetch"]["compactions"] == 0
    assert seen["masking-no-fetch"]["evicted"] >= 1
    assert seen["none"]["compactions"] == 0 and seen["none"]["evicted"] == 0
    # the dry-run count is the live count, not an estimate
    script = lambda n, m: (answer_reply(FACT_A) if n == 4
                           else answer_reply(FACT_B) if n == 16
                           else tool_reply(call_id="c%d" % n))
    live, _tr = run(tmp_path, "bounded-context-fetch", script, max_steps=16, turns=16)
    assert live["episodes"][0]["compactions"] == seen["bounded-context-fetch"][
        "compactions"]


def _cli(tmp_path, *extra):
    """Run ``main`` against a real task dir and a real snapshot manifest."""
    import hashlib
    snap = tmp_path / "snap"
    tasks = tmp_path / "tasks"
    tasks.mkdir(exist_ok=True)
    fixture = make_fixture(tmp_path, turns=16)
    (tasks / ("%s.json" % fixture["task_id"])).write_text(json.dumps(fixture),
                                                          encoding="utf-8")
    manifest = {"files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(snap.iterdir()) if p.is_file()}}
    mpath = tmp_path / "manifest.json"
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    return AC.main(["--tasks", str(tasks), "--root", str(snap),
                    "--snapshot-manifest", str(mpath), "--reps", "1",
                    "--steps", "16", "--max-requests", "20", "--dry-run", *extra])


def test_cli_dry_run_reports_compactions_per_arm(tmp_path, capsys):
    rc = _cli(tmp_path, "--arms", "pinned,bounded-context-fetch,compact")
    out = capsys.readouterr().out
    assert rc == 0
    lines = [l for l in out.splitlines() if l.startswith("dry_run arm=")]
    assert len(lines) == 3
    for line in lines:
        assert "compactions=1" in line, line
        assert "void=False" in line, line


def test_cli_dry_run_refuses_a_void_plan(tmp_path, capsys):
    """A fold distance no episode can reach is refused, not measured as a void cell."""
    rc = _cli(tmp_path, "--arms", "pinned", "--compact-every", "1000")
    err = capsys.readouterr().err
    assert rc == 3
    assert "would be VOID" in err
    assert "pinned" in err



# ------------------------------------------------------------------ (g2)
def test_presence_is_measured_from_the_document_not_the_expected_string(tmp_path):
    """RED before 2026-11-11: a derived value is often not written the way the fixture
    spells it, so the literal test reported "absent" for a fact the prompt carried.

    Measured on the live task set: 9 of 16 agentic checkpoints are absent from their own
    document body under the literal test, and the ``none`` arm — which cannot lose
    anything — was being scored ``lost_then_failed``.  Presence is therefore measured
    from the document the fact lives in, and the literal test is recorded beside it.
    """
    fixture = make_fixture(tmp_path, turns=4)
    consts = tmp_path / "snap" / "consts.py"
    consts.write_text(
        "SYM_A = %s\nSYM_B = %s\n\n\ndef f(cfg):\n"
        "    return cfg.read_text(encoding=\"utf-8\")\n" % (FACT_A, FACT_B),
        encoding="utf-8")
    body = consts.read_text(encoding="utf-8")
    fixture["items"] = [{"id": "consts.py", "body": body}]
    fixture["documents"][0]["revisions"][0]["value"] = body
    # ``call_inside_function`` always parses the fixture's ``resolve.py`` source, so the
    # test file has to BE that source; ``derive.file`` is not consulted for this rule.
    fixture["sources"] = [{"id": "resolve.py", "path": str(consts)}]
    fixture["checkpoints"][1] = {
        "id": "cp2", "turn": 4, "question": "Which call does f make?",
        "expected": "cfg.read_text(encoding='utf-8')",
        "source": "tool_output:consts.py@r1",
        "answer_spec": {"kind": "CALL",
                        "derive": {"rule": "call_inside_function", "attr": "read_text",
                                   "function": "f", "file": str(consts)}},
    }
    task = AC.load_task(write_task(tmp_path, fixture))
    cp = task.checkpoint_at(4)
    # A CALL checkpoint's ``expected`` is the DERIVED structure, not the documented
    # string — which is why the literal test could never see it.
    assert cp["expected"]["callee"] == "cfg.read_text"
    assert cp["documented_expected"] == "cfg.read_text(encoding='utf-8')"
    assert cp["documented_expected"] not in body, "the fixture must not spell the call out"
    assert str(cp["expected"]) not in body
    anchor = AC._doc_anchor(task.fixture,
                            AC._checkpoint_source(task.fixture, cp["id"]))
    assert anchor and anchor in body

    def call_reply(value):
        return {"content": "ANSWER: CALL %s" % value, "tool_calls": [],
                "prompt_tokens": 1000, "completion_tokens": 0, "cached_tokens": 0}

    script = lambda n, m: (call_reply("cfg.read_text(encoding='utf-8')") if n == 4
                           else tool_reply(start=1, end=20, call_id="c%d" % n))
    tr = FakeTransport(script)
    res = AC.run_cell([task], "none", 1, tr, max_steps=4, max_requests=20,
                      budget_cap=1000, spent=0, repo_root=str(tmp_path / "snap"),
                      log=lambda *a: None)
    final = [r for r in res["request_rows"] if r["kind"] == "final"][0]
    assert final["expected_present"] is True, "the document was in the prompt"
    assert final["value_present"] is False, "the literal test cannot see a derived value"
    assert final["verified"] is True


def test_a_new_run_truncates_the_out_file_instead_of_mixing_two_runs(tmp_path):
    """RED before 2026-11-11: ``--out`` was opened in append mode, so a second run's
    episodes landed under the first run's.  Measured live: 36 stale lines carrying the
    old 5-arm plan's ``budget: 816`` sat under a new run's rows."""
    script = lambda n, m: (answer_reply(FACT_A) if n == 2
                           else answer_reply(FACT_B) if n == 4
                           else tool_reply(call_id="c%d" % n))
    rows = tmp_path / "rows.jsonl"
    out = tmp_path / "out.jsonl"
    run(tmp_path, "none", script, rows_path=str(rows))
    assert rows.exists() and read_rows(str(rows))

    assert AC.main(["--offline", str(rows), "--out", str(out)]) == 0
    first = len(read_rows(str(out)))
    assert first >= 1

    # A second run over the same rows must REPLACE the record, not double it.
    assert AC.main(["--offline", str(rows), "--out", str(out)]) == 0
    assert len(read_rows(str(out))) == first

    # ``--append`` is the explicit opt-in for accumulating.
    assert AC.main(["--offline", str(rows), "--out", str(out), "--append"]) == 0
    assert len(read_rows(str(out))) == 2 * first
