"""``resextract.llm`` — the Occamy-1.0 client.

Public surface::

    from resextract.llm import OccamyClient, Budget, BudgetExhausted

    async with OccamyClient(budget=Budget(max_tokens=50_000, max_calls=40)) as c:
        off = await c.chat([{"role": "user", "content": "hi"}], thinking=False)
        on = await c.chat([{"role": "user", "content": "assess this"}], thinking=True,
                          max_tokens=8192)

Read :mod:`resextract.llm.occamy` for the thinking policy: ``thinking=False``
sends ``chat_template_kwargs.enable_thinking=false`` (~0.25 s / 0 tokens) while
``thinking=True`` omits the key and buys private ``reasoning_content`` (~10.5 s
/ 397 reasoning tokens on the same trivial prompt — a ~40x lever).
"""

from .occamy import (
    DEFAULT_API_KEY,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    Budget,
    BudgetExhausted,
    ChatResult,
    ModelRequestError,
    OccamyClient,
    OccamyConfig,
    SyncOccamyClient,
    ToolCall,
    ToolCallRecord,
    ToolExecution,
    ToolLoopResult,
    ToolLoopStep,
    UnparseableOutput,
    Usage,
    UsageRecord,
    build_request_body,
    extract_json_object,
    find_config_path,
    load_config,
    parse_usage,
)

__all__ = [
    "DEFAULT_API_KEY",
    "DEFAULT_BASE_URL",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MODEL",
    "Budget",
    "BudgetExhausted",
    "ChatResult",
    "ModelRequestError",
    "OccamyClient",
    "OccamyConfig",
    "SyncOccamyClient",
    "ToolCall",
    "ToolCallRecord",
    "ToolExecution",
    "ToolLoopResult",
    "ToolLoopStep",
    "UnparseableOutput",
    "Usage",
    "UsageRecord",
    "build_request_body",
    "extract_json_object",
    "find_config_path",
    "load_config",
    "parse_usage",
]
