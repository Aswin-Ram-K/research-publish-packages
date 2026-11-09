"""Gate for TOOL-CHANNEL-ROOT-CAUSE: the offline assertions must all hold.

This is a thin pytest wrapper over ``tools/tool_channel_root_cause_check.py`` so the
diagnosis is re-runnable by a judge that only knows test runners. It touches no network:
the endpoint half replays the recorded probe at
``experiments/ptr-engine/measure/probe-tool-channel-raw.json``.
"""
from __future__ import annotations

import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "..", "tools", "tool_channel_root_cause_check.py")


def _load():
    spec = importlib.util.spec_from_file_location("tool_channel_root_cause_check", CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_tool_channel_root_cause_holds():
    mod = _load()
    rc = mod.main()
    assert rc == 0, "assertions failed: %r" % (mod.fails,)
