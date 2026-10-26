"""Tests for the --thinking flag's payload seam (RUNNER-THINKING-FLAG).

The contract:
  auto -> the request body carries NO ``chat_template_kwargs`` key at all (byte-identical to
          every run before the flag existed);
  on   -> ``{"chat_template_kwargs": {"enable_thinking": true}}``;
  off  -> ``{"chat_template_kwargs": {"enable_thinking": false}}``.

These tests bind to ``request_body`` / ``thinking_kwargs`` only — no network, no requests,
no fixture, no manifest writes.

Run: .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests_thinking_flag.py -q
"""

import importlib.util
import json
import os
import sys
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_RUNNER = os.path.join(_HERE, "run_longrun.py")

_spec = importlib.util.spec_from_file_location("run_longrun_under_test", _RUNNER)
assert _spec and _spec.loader
rl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rl)

MESSAGES = [{"role": "system", "content": "sys"}, {"role": "user", "content": "q"}]

# The exact body the runner produced before this flag existed.  ``auto`` must reproduce it.
PRE_FLAG_KEYS = {"model", "messages", "temperature", "max_tokens", "stream", "stream_options"}


def cfg(thinking=None, stream=True):
    ns = SimpleNamespace(model="m", max_tokens=16384, stream=stream)
    if thinking is not None:
        ns.thinking = thinking
    return ns


def body_for(thinking=None, stream=True):
    return rl.request_body(cfg(thinking, stream), MESSAGES)


# ---------------------------------------------------------------- a) auto
def test_auto_has_no_chat_template_kwargs_key():
    body = body_for("auto")
    assert "chat_template_kwargs" not in body
    assert set(body) == PRE_FLAG_KEYS


def test_auto_is_byte_identical_to_the_pre_flag_payload():
    body = body_for("auto")
    expected = {
        "model": "m",
        "messages": MESSAGES,
        "temperature": 0,
        "max_tokens": 16384,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    assert json.dumps(body, sort_keys=True) == json.dumps(expected, sort_keys=True)


def test_missing_attribute_defaults_to_auto():
    # A namespace built without the flag (e.g. an older caller) must behave as auto.
    body = rl.request_body(SimpleNamespace(model="m", max_tokens=8, stream=False), MESSAGES)
    assert "chat_template_kwargs" not in body


# ----------------------------------------------------------------- b) off
def test_off_requests_disable_thinking():
    body = body_for("off")
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert set(body) == PRE_FLAG_KEYS | {"chat_template_kwargs"}


# ------------------------------------------------------------------ c) on
def test_on_requests_enable_thinking():
    body = body_for("on")
    assert body["chat_template_kwargs"] == {"enable_thinking": True}
    assert set(body) == PRE_FLAG_KEYS | {"chat_template_kwargs"}


# ------------------------------------------------------- the three settings differ
def test_only_the_thinking_key_differs_between_settings():
    auto, on, off = body_for("auto"), body_for("on"), body_for("off")
    for key in PRE_FLAG_KEYS:
        assert auto[key] == on[key] == off[key], key
    assert rl.thinking_setting(cfg("off")) == "off"
    assert rl.thinking_kwargs("auto") is None


def test_unknown_setting_is_refused():
    with pytest.raises(ValueError):
        rl.thinking_kwargs("maybe")
