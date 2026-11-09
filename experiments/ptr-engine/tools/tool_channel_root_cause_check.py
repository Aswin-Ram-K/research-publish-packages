#!/usr/bin/env python3
"""Offline assertion set for TOOL-CHANNEL-ROOT-CAUSE.

Proves, with no network and no cell, three things about the tool channel:

  1. the client's wire body has no ``tools`` / ``tool_choice`` member (static);
  2. the runner's tool channel is a TEXT protocol parsed out of ``content`` (static),
     and the fixture never teaches that protocol (static);
  3. the endpoint DOES answer a ``tools`` array structurally, and does not when the
     array is withheld (replayed from the recorded probe, not re-sent).

Exit codes: 0 = every assertion held.  1 = an assertion failed (FAIL).
13 = the recorded probe is missing/unreadable, so no verdict can be stamped
(UNSTAMPED — never report this as FAIL: it measured nothing).
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.join(HERE, "..", "longrun")
CLIENT = os.path.join(LONGRUN, "client.py")
RUNNER = os.path.join(LONGRUN, "run_longrun.py")
FIXTURE = os.path.join(LONGRUN, "tasks-v6", "LR-01.v8.json")
PROBE = os.path.join(HERE, "..", "measure", "probe-tool-channel-raw.json")

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  <-- " + detail))
    if not ok:
        fails.append(name)


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def request_body_source(src: str) -> str:
    start = src.index("def request_body(")
    end = src.index("\ndef ", start + 10)
    return src[start:end]


def main() -> int:
    src = read(CLIENT)
    body_src = request_body_source(src)
    # 1. the body literal, and every later mutation of it, carries no tools member
    keys = re.findall(r'^\s{8}"([a-z_]+)":', body_src, re.M)
    check("client.request_body keys carry no 'tools'", "tools" not in keys, str(keys))
    check("client.request_body keys carry no 'tool_choice'", "tool_choice" not in keys, str(keys))
    mutations = re.findall(r'body\["([a-z_]+)"\]', src)
    check("no body['tools'] assignment anywhere in client.py",
          "tools" not in mutations and "tool_choice" not in mutations, str(mutations))
    check("the only wire URL is /chat/completions",
          src.count('/chat/completions"') == 1, "url sites")
    # the docstring's assumption is undocumented-by-code: it names tools, no code adds them
    check("request_digest docstring names tools but body never carries them",
          "and ``tools`` where an engine takes" in body_src or "and ``tools`` where an engine takes" in src)

    # 2. the runner channel is text parsing, and the prompt never requests that syntax
    run = read(RUNNER)
    check("runner parses calls out of content (parse_tool_calls defined)",
          "def parse_tool_calls(" in run)
    check("runner gates the channel on argv --tools", 'TOOL_NAMES = ("read_file",)' in run)
    check("runner requires the literal marker '<tool_call>'",
          '"<tool_call>"' in run)
    turns = json.loads(read(FIXTURE))
    doc = json.dumps(turns)
    check("fixture never contains the '<tool_call>' marker", "<tool_call>" not in doc,
          "fixture teaches the protocol")
    sp = turns["system_prompt"]
    check("fixture mentions read_file only negatively (checkpoint paragraph)",
          sp.count("read_file") == 1 and "no read_file" in sp, "system_prompt")
    sys_prompt_has_protocol = "<tool_call>" in sp or "read_file {" in sp
    check("system_prompt never defines the call syntax", not sys_prompt_has_protocol)

    # 3. the recorded endpoint probe
    if not os.path.exists(PROBE):
        print("UNSTAMPED: probe record %s is absent — nothing measured" % PROBE)
        return 13
    try:
        probe = json.loads(read(PROBE))
        wt = probe["with_tools"]
        wot = probe["without_tools"]
    except Exception as exc:  # noqa: BLE001
        print("UNSTAMPED: probe record unreadable (%s) — nothing measured" % exc)
        return 13
    calls = wt.get("tool_calls") or []
    check("endpoint returns a structured tool call when 'tools' is sent", bool(calls), str(wt)[:200])
    check("endpoint sets finish_reason='tool_calls'", wt.get("finish_reason") == "tool_calls",
          str(wt.get("finish_reason")))
    if calls:
        fn = (calls[0] or {}).get("function") or {}
        args = json.loads(fn.get("arguments") or "{}")
        check("the structured call is read_file", fn.get("name") == "read_file", str(fn.get("name")))
        check("the structured call carries a path and a line range",
              isinstance(args.get("path"), str) and "start_line" in args and "end_line" in args,
              str(args))
        check("content is empty on a tool-call turn (the call replaced prose)",
              wt.get("content_len") == 0, str(wt.get("content_len")))
    check("without 'tools' the same prompt yields prose, no tool_calls",
          not wot.get("tool_calls") and wot.get("finish_reason") == "stop",
          "%s / %s" % (wot.get("tool_calls"), wot.get("finish_reason")))

    print("\n%d assertion(s) failed" % len(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
