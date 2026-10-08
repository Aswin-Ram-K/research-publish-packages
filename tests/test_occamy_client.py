"""Offline tests for the Occamy client (``resextract.llm``).

Everything here runs against ``httpx.MockTransport`` — no network.  The single
live smoke test at the bottom is skipped unless ``--live`` is passed.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from pydantic import BaseModel

from conftest import chat_response, sse_response, tool_call
from resextract.llm import (
    Budget,
    BudgetExhausted,
    ChatResult,
    ModelRequestError,
    OccamyClient,
    SyncOccamyClient,
    UnparseableOutput,
    Usage,
    UsageRecord,
    build_request_body,
    extract_json_object,
    load_config,
    parse_usage,
)
from resextract.llm.occamy import find_config_path


# Synthetic sk- shaped fixture, assembled at runtime from non-secret-shaped pieces
# so this file's bytes do not match the commit scanner (docs/SECRET_SCAN_POLICY.md).
_FAKE_API_KEY = "sk-" + "T3nW" * 5 + "xYz"  # 26 chars: sk- + 23 alnum


class Brief(BaseModel):
    title: str
    count: int


# --------------------------------------------------------------------------- #
# 1. The thinking switch
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_thinking_off_sends_disable_flag(make_client) -> None:
    """RED→GREEN guard: thinking off MUST send enable_thinking=false.

    Reverting the fix (``if not thinking:`` → ``if False:`` in
    ``build_request_body``) makes this test fail.  Real red output
    (``.venv/bin/python -m pytest
    tests/test_occamy_client.py::test_thinking_off_sends_disable_flag -q``)::

        >       assert "chat_template_kwargs" in body, "thinking=False must send chat_template_kwargs"
        E       AssertionError: thinking=False must send chat_template_kwargs
        E       assert 'chat_template_kwargs' in {'model': 'occamy-1.0', 'messages':
        E         [{'role': 'user', 'content': 'hi'}], 'max_tokens': 32, 'temperature': 0.0}

        tests/test_occamy_client.py:70: AssertionError
        =========================== short test summary info ============================
        FAILED tests/test_occamy_client.py::test_thinking_off_sends_disable_flag - As...
        1 failed in 0.02s

    Green: the key is present and false.
    """
    harness = make_client(lambda req, i: chat_response())
    async with harness.client as client:
        await client.chat([{"role": "user", "content": "hi"}], thinking=False, max_tokens=32)
    body = harness.recorder.body(0)
    assert "chat_template_kwargs" in body, "thinking=False must send chat_template_kwargs"
    assert body["chat_template_kwargs"]["enable_thinking"] is False
    assert harness.recorder.count == 1


@pytest.mark.asyncio
async def test_thinking_on_omits_flag(make_client) -> None:
    harness = make_client(lambda req, i: chat_response(reasoning="hidden thought"))
    async with harness.client as client:
        result = await client.chat(
            [{"role": "user", "content": "hi"}], thinking=True, max_tokens=32
        )
    assert "chat_template_kwargs" not in harness.recorder.body(0)
    assert result.thinking is True


def test_build_request_body_is_pure_both_ways() -> None:
    off = build_request_body(
        model="occamy-1.0",
        messages=[{"role": "user", "content": "x"}],
        thinking=False,
        max_tokens=8,
    )
    on = build_request_body(
        model="occamy-1.0",
        messages=[{"role": "user", "content": "x"}],
        thinking=True,
        max_tokens=8,
    )
    assert off["chat_template_kwargs"] == {"enable_thinking": False}
    assert "chat_template_kwargs" not in on


# --------------------------------------------------------------------------- #
# 2. reasoning_content / content separation
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_reasoning_and_content_are_separate_fields(make_client) -> None:
    harness = make_client(
        lambda req, i: chat_response(content="The answer is 391.", reasoning="17*23: 17*20=340, +51=391")
    )
    async with harness.client as client:
        result = await client.chat([{"role": "user", "content": "17*23?"}], thinking=True)
    assert result.content == "The answer is 391."
    assert result.reasoning_content == "17*23: 17*20=340, +51=391"
    assert "391" not in result.reasoning_content.split(":")[0]
    assert "17*20" not in result.content
    assert result.reasoning_content != result.content


@pytest.mark.asyncio
async def test_thinking_off_has_empty_reasoning(make_client) -> None:
    harness = make_client(
        lambda req, i: chat_response(
            content="OK",
            usage={
                "prompt_tokens": 14,
                "completion_tokens": 2,
                "total_tokens": 16,
                "completion_tokens_details": {"reasoning_tokens": 0},
            },
        )
    )
    async with harness.client as client:
        result = await client.chat([{"role": "user", "content": "say OK"}], thinking=False, max_tokens=16)
    assert result.reasoning_content == ""
    assert result.usage.reasoning_tokens == 0
    assert result.usage.completion_tokens == 2


def test_parse_usage_reads_several_shapes() -> None:
    assert parse_usage(
        {
            "prompt_tokens": 5,
            "completion_tokens": 10,
            "total_tokens": 15,
            "completion_tokens_details": {"reasoning_tokens": 4},
        }
    ) == Usage(prompt_tokens=5, completion_tokens=10, reasoning_tokens=4, total_tokens=15)
    assert parse_usage({"prompt_tokens": 1, "completion_tokens": 2, "reasoning_tokens": 3}) == Usage(
        prompt_tokens=1, completion_tokens=2, reasoning_tokens=3, total_tokens=3
    )
    assert parse_usage(None) == Usage()
    added = Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2) + Usage(
        prompt_tokens=2, completion_tokens=2, total_tokens=4
    )
    assert added.total_tokens == 6


# --------------------------------------------------------------------------- #
# 3. Tool calls
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_tool_call_name_and_json_string_args_decoded(make_client) -> None:
    harness = make_client(
        lambda req, i: chat_response(
            content=None,
            finish_reason="tool_calls",
            tool_calls=[
                tool_call("graph_query", '{"query": "novel primitives", "k": 3}')
            ],
        )
    )
    async with harness.client as client:
        result = await client.chat(
            [{"role": "user", "content": "find novel primitives"}],
            thinking=False,
            tools=[{"type": "function", "function": {"name": "graph_query"}}],
            tool_choice="auto",
        )
    assert result.finish_reason == "tool_calls"
    assert len(result.tool_calls) == 1
    call = result.tool_calls[0]
    assert call.name == "graph_query"
    assert call.arguments == {"query": "novel primitives", "k": 3}
    assert call.raw_arguments == '{"query": "novel primitives", "k": 3}'
    assert call.args_error is None
    body = harness.recorder.body(0)
    assert body["tool_choice"] == "auto"
    assert body["tools"][0]["function"]["name"] == "graph_query"


@pytest.mark.asyncio
async def test_unparseable_tool_arguments_keep_raw_text(make_client) -> None:
    harness = make_client(
        lambda req, i: chat_response(
            content=None,
            finish_reason="tool_calls",
            tool_calls=[tool_call("graph_query", '{"query": ')],  # truncated JSON
        )
    )
    async with harness.client as client:
        result = await client.chat([{"role": "user", "content": "x"}], thinking=False)
    call = result.tool_calls[0]
    assert call.name == "graph_query"
    assert call.arguments == {}
    assert call.raw_arguments == '{"query": '
    assert call.args_error and "JSONDecodeError" in call.args_error


# --------------------------------------------------------------------------- #
# 4. The null-name continuation-delta quirk
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_null_name_delta_does_not_clobber_announced_name(make_client) -> None:
    """Upstream quirk: continuation deltas carry ``"function": {"name": null}``.

    The final tool call must keep ``graph_query`` — never ``None``/``""`` — and
    the argument fragments must still be concatenated.
    """
    harness = make_client(
        lambda req, i: chat_response(
            content=None,
            finish_reason="tool_calls",
            tool_calls=[
                tool_call("graph_query", '{"query":', call_id="call_9", index=0),
                tool_call(None, ' "novel"}', call_id=None, index=0),
            ],
        )
    )
    async with harness.client as client:
        result = await client.chat([{"role": "user", "content": "x"}], thinking=False)
    call = result.tool_calls[0]
    assert call.name == "graph_query"
    assert call.name is not None and call.name != ""
    assert call.id == "call_9"
    assert call.arguments == {"query": "novel"}


@pytest.mark.asyncio
async def test_streamed_null_name_delta_keeps_announced_name(make_client) -> None:
    chunks = [
        {
            "id": "cmpl-1",
            "model": "occamy-1.0",
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": "", "reasoning_content": "weighing options"},
                    "finish_reason": None,
                }
            ],
        },
        {
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_a",
                                "type": "function",
                                "function": {"name": "graph_explain", "arguments": '{"node":'},
                            }
                        ]
                    },
                    "finish_reason": None,
                }
            ]
        },
        {
            "choices": [
                {
                    "index": 0,
                    "delta": {"tool_calls": [{"index": 0, "function": {"name": None}}]},
                    "finish_reason": None,
                }
            ]
        },
        {
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "tool_calls": [
                            {"index": 0, "function": {"name": None, "arguments": ' "OrderService"}'}}
                        ]
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {
                "prompt_tokens": 30,
                "completion_tokens": 40,
                "total_tokens": 70,
                "completion_tokens_details": {"reasoning_tokens": 12},
            },
        },
    ]
    harness = make_client(lambda req, i: sse_response(chunks))
    async with harness.client as client:
        result = await client.chat(
            [{"role": "user", "content": "explain"}], thinking=True, stream=True
        )
    assert result.streamed is True
    assert result.content == ""
    assert result.reasoning_content == "weighing options"
    assert result.finish_reason == "tool_calls"
    assert result.usage.reasoning_tokens == 12
    call = result.tool_calls[0]
    assert call.name == "graph_explain"
    assert call.id == "call_a"
    assert call.arguments == {"node": "OrderService"}
    assert harness.recorder.body(0)["stream"] is True


# --------------------------------------------------------------------------- #
# 5. Retries
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_500_then_200_succeeds_with_two_attempts(make_client) -> None:
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        if index == 0:
            return httpx.Response(500, text="upstream exploded")
        return chat_response(content="recovered")

    harness = make_client(handler)
    async with harness.client as client:
        result = await client.chat([{"role": "user", "content": "x"}], thinking=False)
    assert result.content == "recovered"
    assert result.attempts == 2
    assert harness.recorder.count == 2
    assert len(harness.sleep.delays) == 1
    assert 0.25 <= harness.sleep.delays[0] <= 0.5  # base 0.5, jitter in [0.5, 1.0]


@pytest.mark.asyncio
async def test_500_four_times_raises_after_max_attempts(make_client) -> None:
    harness = make_client(lambda req, i: httpx.Response(503, text="down"))
    async with harness.client as client:
        with pytest.raises(ModelRequestError) as excinfo:
            await client.chat([{"role": "user", "content": "x"}], thinking=False)
    assert excinfo.value.status == 503
    assert excinfo.value.attempts == 4
    assert harness.recorder.count == 4
    assert len(harness.sleep.delays) == 3
    # exponential and capped
    assert harness.sleep.delays[0] <= harness.sleep.delays[-1] <= 8.0


@pytest.mark.asyncio
async def test_connection_error_is_retried(make_client) -> None:
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        if index == 0:
            raise httpx.ConnectError("refused", request=request)
        return chat_response(content="second try")

    harness = make_client(handler)
    async with harness.client as client:
        result = await client.chat([{"role": "user", "content": "x"}], thinking=False)
    assert result.content == "second try"
    assert result.attempts == 2


@pytest.mark.asyncio
async def test_400_raises_immediately_with_one_attempt(make_client) -> None:
    harness = make_client(lambda req, i: httpx.Response(400, text="bad request: nope"))
    async with harness.client as client:
        with pytest.raises(ModelRequestError) as excinfo:
            await client.chat([{"role": "user", "content": "x"}], thinking=False)
    assert excinfo.value.status == 400
    assert "bad request: nope" in excinfo.value.body
    assert excinfo.value.attempts == 1
    assert harness.recorder.count == 1
    assert harness.sleep.delays == []


@pytest.mark.asyncio
async def test_429_honours_retry_after(make_client) -> None:
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        if index == 0:
            return httpx.Response(429, text="slow down", headers={"Retry-After": "2"})
        return chat_response(content="ok after backoff")

    harness = make_client(handler)
    async with harness.client as client:
        result = await client.chat([{"role": "user", "content": "x"}], thinking=False)
    assert result.content == "ok after backoff"
    assert harness.sleep.delays == [2.0]
    assert harness.recorder.count == 2


@pytest.mark.asyncio
async def test_garbage_body_is_not_retried(make_client) -> None:
    harness = make_client(lambda req, i: httpx.Response(200, text="<html>nope</html>"))
    async with harness.client as client:
        with pytest.raises(ModelRequestError):
            await client.chat([{"role": "user", "content": "x"}], thinking=False)
    assert harness.recorder.count == 1


# --------------------------------------------------------------------------- #
# 6. Budget
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_budget_call_cap_exhausts_before_second_request(make_client) -> None:
    harness = make_client(lambda req, i: chat_response(), budget=Budget(max_calls=1))
    async with harness.client as client:
        first = await client.chat([{"role": "user", "content": "1"}], thinking=False)
        assert first.content == "ok"
        with pytest.raises(BudgetExhausted) as excinfo:
            await client.chat([{"role": "user", "content": "2"}], thinking=False)
    assert excinfo.value.reason == "calls"
    assert excinfo.value.calls_used == 1
    assert harness.recorder.count == 1, "no HTTP request may leave on an exhausted budget"


@pytest.mark.asyncio
async def test_budget_token_cap_raises_on_charge(make_client) -> None:
    usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    harness = make_client(lambda req, i: chat_response(usage=usage), budget=Budget(max_tokens=100))
    async with harness.client as client:
        with pytest.raises(BudgetExhausted) as excinfo:
            await client.chat([{"role": "user", "content": "x"}], thinking=False)
    assert excinfo.value.reason == "tokens"
    assert excinfo.value.tokens_used == 150
    assert excinfo.value.max_tokens == 100


def test_budget_check_and_charge_are_direct() -> None:
    budget = Budget(max_tokens=10, max_calls=2)
    budget.begin_call()
    budget.charge(4)
    assert budget.remaining_tokens == 6
    assert budget.remaining_calls == 1
    budget.charge(6)
    with pytest.raises(BudgetExhausted):
        budget.check()
    unlimited = Budget()
    for _ in range(100):
        unlimited.begin_call()
    assert unlimited.remaining_tokens is None


# --------------------------------------------------------------------------- #
# 7. Metering, traces, secret hygiene
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_every_call_appends_a_usage_record(make_client) -> None:
    records: list[UsageRecord] = []

    def handler(request: httpx.Request, index: int) -> httpx.Response:
        if index == 0:
            return chat_response(
                content="hi",
                reasoning="because",
                usage={
                    "prompt_tokens": 9,
                    "completion_tokens": 4,
                    "total_tokens": 13,
                    "completion_tokens_details": {"reasoning_tokens": 3},
                },
            )
        return httpx.Response(400, text="nope")

    harness = make_client(handler, usage_sink=records.append, label="unit-test")
    async with harness.client as client:
        await client.chat([{"role": "user", "content": "1"}], thinking=True)
        with pytest.raises(ModelRequestError):
            await client.chat([{"role": "user", "content": "2"}], thinking=False)
    assert len(records) == 2
    ok, bad = records
    assert ok.ok is True and ok.label == "unit-test"
    assert (ok.prompt_tokens, ok.completion_tokens, ok.reasoning_tokens, ok.total_tokens) == (9, 4, 3, 13)
    assert ok.thinking is True and ok.wall_ms >= 0 and ok.request_id == "req-1"
    assert bad.ok is False and bad.status == 400 and bad.total_tokens == 0
    assert bad.error and "400" in bad.error


@pytest.mark.asyncio
async def test_api_key_never_reaches_trace_or_metering(make_client) -> None:
    secret = _FAKE_API_KEY
    records: list[UsageRecord] = []

    def tool_handler(request: httpx.Request, index: int) -> httpx.Response:
        if index == 0:
            return chat_response(
                content=None,
                finish_reason="tool_calls",
                tool_calls=[tool_call("dig", "{}")],
            )
        return chat_response(content="done")

    harness = make_client(tool_handler, api_key=secret, usage_sink=records.append)
    async with harness.client as client:
        loop = await client.run_tool_loop(
            [{"role": "user", "content": "go"}],
            tools=[{"type": "function", "function": {"name": "dig"}}],
            handlers={"dig": lambda args: {"found": "value"}},
            max_steps=3,
        )
    blob = json.dumps(loop.model_dump(mode="json"), default=str)
    blob += json.dumps([r.model_dump(mode="json") for r in records])
    assert secret not in blob
    assert "Authorization" not in blob
    # the key *is* used on the wire, in the header only
    assert harness.recorder.requests[0].headers["authorization"] == f"Bearer {secret}"


# --------------------------------------------------------------------------- #
# 8. run_tool_loop
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_tool_loop_executes_handler_and_records_serialisable_trace(make_client) -> None:
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        if index == 0:
            return chat_response(
                content=None,
                reasoning="I should query the graph first.",
                finish_reason="tool_calls",
                tool_calls=[tool_call("graph_query", '{"query": "novel"}', call_id="call_a")],
            )
        return chat_response(content="Final: 3 novel primitives.", reasoning="counting")

    harness = make_client(handler)
    seen: list[dict] = []

    async def graph_query(args: dict) -> dict:
        seen.append(args)
        return {"nodes": [{"id": "n1"}, {"id": "n2"}], "unserialisable": {1, 2}}

    async with harness.client as client:
        result = await client.run_tool_loop(
            [{"role": "user", "content": "mine"}],
            tools=[{"type": "function", "function": {"name": "graph_query"}}],
            handlers={"graph_query": graph_query},
            max_steps=4,
            thinking=True,
        )

    assert result.stopped_reason == "final_answer"
    assert result.content == "Final: 3 novel primitives."
    assert result.tool_calls == 1
    assert seen == [{"query": "novel"}]
    assert len(result.steps) == 2

    step0, step1 = result.steps
    assert step0.step == 1 and step0.thinking is True
    assert step0.reasoning_content == "I should query the graph first."
    assert step0.tool_calls[0].name == "graph_query"
    assert step0.tool_calls[0].arguments == {"query": "novel"}
    execution = step0.executions[0]
    assert execution.ok is True
    assert execution.result["nodes"][0]["id"] == "n1"
    assert execution.result_digest.startswith("sha256:")
    assert execution.duration_ms >= 0
    assert step1.reasoning_content == "counting"
    assert step1.content == "Final: 3 novel primitives."
    assert step1.executions == []
    assert result.usage.total_tokens == 36  # two calls x 18

    # the trace is what the dashboard reads: it must round-trip as JSON
    trace = json.dumps(result.model_dump(mode="json"))
    restored = json.loads(trace)
    assert restored["steps"][0]["executions"][0]["result"]["unserialisable"] == [1, 2]

    # follow-up request carries the assistant tool_calls turn + the tool result
    followup = harness.recorder.body(1)["messages"]
    assert followup[0]["role"] == "user"
    assert followup[1]["role"] == "assistant"
    assert followup[1]["tool_calls"][0]["function"]["name"] == "graph_query"
    assert followup[1]["tool_calls"][0]["id"] == "call_a"
    assert followup[2]["role"] == "tool"
    assert followup[2]["tool_call_id"] == "call_a"
    assert "n1" in followup[2]["content"]


@pytest.mark.asyncio
async def test_tool_loop_missing_handler_feeds_error_back_to_model(make_client) -> None:
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        if index == 0:
            return chat_response(
                content=None,
                finish_reason="tool_calls",
                tool_calls=[tool_call("nope", "{}", call_id="call_z")],
            )
        return chat_response(content="recovered without the tool")

    harness = make_client(handler)
    async with harness.client as client:
        result = await client.run_tool_loop(
            [{"role": "user", "content": "go"}],
            tools=[{"type": "function", "function": {"name": "nope"}}],
            handlers={},
            max_steps=3,
        )
    execution = result.steps[0].executions[0]
    assert execution.ok is False
    assert "no handler registered" in (execution.error or "")
    assert result.stopped_reason == "final_answer"
    tool_message = harness.recorder.body(1)["messages"][-1]
    assert tool_message["role"] == "tool"
    assert "no handler registered" in tool_message["content"]


@pytest.mark.asyncio
async def test_tool_loop_failing_handler_is_recorded_not_raised(make_client) -> None:
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        if index == 0:
            return chat_response(
                content=None,
                finish_reason="tool_calls",
                tool_calls=[tool_call("boom", "{}")],
            )
        return chat_response(content="gave up")

    def boom(args: dict) -> dict:
        raise RuntimeError("handler exploded")

    harness = make_client(handler)
    async with harness.client as client:
        result = await client.run_tool_loop(
            [{"role": "user", "content": "go"}],
            tools=[{"type": "function", "function": {"name": "boom"}}],
            handlers={"boom": boom},
            max_steps=3,
        )
    execution = result.steps[0].executions[0]
    assert execution.ok is False
    assert execution.error == "RuntimeError: handler exploded"
    assert result.content == "gave up"


@pytest.mark.asyncio
async def test_tool_loop_stops_at_step_cap(make_client) -> None:
    harness = make_client(
        lambda req, i: chat_response(
            content=None,
            finish_reason="tool_calls",
            tool_calls=[tool_call("loop_tool", "{}")],
        )
    )
    async with harness.client as client:
        result = await client.run_tool_loop(
            [{"role": "user", "content": "spin"}],
            tools=[{"type": "function", "function": {"name": "loop_tool"}}],
            handlers={"loop_tool": lambda args: "again"},
            max_steps=2,
        )
    assert result.stopped_reason == "max_steps"
    assert len(result.steps) == 2
    assert result.tool_calls == 2
    assert harness.recorder.count == 2, "the step cap must not be exceeded"


# --------------------------------------------------------------------------- #
# 9. call_json
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_call_json_invalid_then_valid_succeeds_on_attempt_two(make_client) -> None:
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        if index == 0:
            return chat_response(content="Sure! Here is a brief: {oops}")
        return chat_response(content='```json\n{"title": "Lanes", "count": 3}\n```')

    harness = make_client(handler)
    async with harness.client as client:
        brief = await client.call_json(
            [{"role": "user", "content": "summarise"}], Brief, thinking=False, max_tokens=128
        )
    assert isinstance(brief, Brief)
    assert brief.title == "Lanes" and brief.count == 3
    assert harness.recorder.count == 2
    retry_messages = harness.recorder.body(1)["messages"]
    assert retry_messages[-1]["role"] == "user"
    retry_text = retry_messages[-1]["content"]
    assert '"required JSON schema"' in retry_text or "Required JSON schema" in retry_text
    assert '"title"' in retry_text and '"count"' in retry_text, "schema must be echoed back"
    assert "Validation error" in retry_text
    assert harness.recorder.body(1)["response_format"] == {"type": "json_object"}
    assert retry_messages[-2]["role"] == "assistant"


@pytest.mark.asyncio
async def test_call_json_invalid_twice_raises_unparseable_with_raw_text(make_client) -> None:
    second = "I am afraid I cannot produce JSON today."
    harness = make_client(
        lambda req, i: chat_response(content="not json at all" if i == 0 else second)
    )
    async with harness.client as client:
        with pytest.raises(UnparseableOutput) as excinfo:
            await client.call_json([{"role": "user", "content": "summarise"}], Brief)
    exc = excinfo.value
    assert exc.raw_text == second
    assert "title" in exc.last_error or "JSONDecodeError" in exc.last_error
    assert exc.attempts == 2
    assert exc.schema_name == "Brief"
    assert harness.recorder.count == 2
    assert not isinstance(exc, Brief)


@pytest.mark.asyncio
async def test_call_json_validation_error_message_is_carried(make_client) -> None:
    harness = make_client(
        lambda req, i: chat_response(content='{"title": "x", "count": "many"}')
    )
    async with harness.client as client:
        with pytest.raises(UnparseableOutput) as excinfo:
            await client.call_json([{"role": "user", "content": "s"}], Brief)
    assert "ValidationError" in excinfo.value.last_error


def test_extract_json_object_handles_prose_and_fences() -> None:
    assert extract_json_object('{"a": 1}') == {"a": 1}
    assert extract_json_object('Here you go:\n```json\n{"a": 2}\n```\n') == {"a": 2}
    assert extract_json_object('prefix {"a": 3} suffix') == {"a": 3}
    with pytest.raises(json.JSONDecodeError):
        extract_json_object("no json here")
    with pytest.raises(json.JSONDecodeError):
        extract_json_object("")


# --------------------------------------------------------------------------- #
# 10. Config + sync wrapper
# --------------------------------------------------------------------------- #


def test_load_config_reads_the_frozen_toml() -> None:
    config_path = find_config_path()
    assert config_path is not None and config_path.is_file()
    cfg = load_config(config_path)
    assert cfg.base_url == "http://192.168.2.168:8012/v1"
    assert cfg.model == "occamy-1.0"
    assert cfg.api_key == "local"
    assert cfg.max_tokens > 0
    missing = load_config(Path("/nonexistent/resextract.toml"))
    assert missing.base_url == "http://192.168.2.168:8012/v1"


@pytest.mark.asyncio
async def test_defaults_do_not_read_a_config_when_absent() -> None:
    cfg = load_config(Path("/nonexistent/resextract.toml"))
    assert cfg.model == "occamy-1.0"
    async with OccamyClient(
        base_url="http://example.invalid/v1", model="m", config_path=Path("/nope.toml")
    ) as client:
        assert client.chat_url == "http://example.invalid/v1/chat/completions"
        assert client.api_key == "local"


def test_sync_wrapper_returns_typed_result(make_client) -> None:
    harness = make_client(lambda req, i: chat_response(content="sync ok"))
    sync_client = SyncOccamyClient(harness.client)
    result = sync_client.chat([{"role": "user", "content": "hi"}], thinking=False, max_tokens=8)
    assert isinstance(result, ChatResult)
    assert result.content == "sync ok"
    assert harness.recorder.body(0)["chat_template_kwargs"]["enable_thinking"] is False


@pytest.mark.asyncio
async def test_sync_wrapper_refuses_inside_running_loop(make_client) -> None:
    harness = make_client(lambda req, i: chat_response())
    sync_client = SyncOccamyClient(harness.client)
    with pytest.raises(RuntimeError, match="running event loop"):
        sync_client.chat([{"role": "user", "content": "hi"}], thinking=False)


# --------------------------------------------------------------------------- #
# 11. Live smoke (skipped by default)
# --------------------------------------------------------------------------- #


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_thinking_toggle_and_record_timings() -> None:
    """Two real calls: thinking off must cost ~0 reasoning tokens; on must think."""
    cfg = load_config()
    async with OccamyClient(
        base_url=cfg.base_url, model=cfg.model, timeout_s=180.0
    ) as client:
        off = await client.chat(
            [{"role": "user", "content": "Reply with exactly: OK"}],
            thinking=False,
            max_tokens=16,
        )
        on = await client.chat(
            [{"role": "user", "content": "What is 17*23? Think it through, then answer."}],
            thinking=True,
            max_tokens=256,
        )

    assert off.reasoning_content == ""
    assert off.usage.reasoning_tokens == 0, off.model_dump(mode="json")
    assert on.reasoning_content.strip() != ""

    evidence = {
        "endpoint": client.chat_url,
        "model": off.model,
        "thinking_off": {
            "wall_ms": off.wall_ms,
            "content": off.content,
            "usage": off.usage.model_dump(mode="json"),
            "raw_usage": off.raw_usage,
        },
        "thinking_on": {
            "wall_ms": on.wall_ms,
            "content": on.content,
            "reasoning_content_chars": len(on.reasoning_content),
            "usage": on.usage.model_dump(mode="json"),
            "raw_usage": on.raw_usage,
        },
    }
    out = Path("state/logs")
    out.mkdir(parents=True, exist_ok=True)
    (out / "U0.2-live.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
