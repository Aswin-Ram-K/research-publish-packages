#!/usr/bin/env python3
"""Probe: for ONE measured chat prompt, compare the server's cached_tokens as read by
/v1/chat/completions (usage.prompt_tokens_details) vs a /generate re-send.

The question is whether a /generate re-send of the SAME token stream is warm. If /v1/tokenize
renders `enable_thinking:False` differently from the chat endpoint's render, the two request
shapes share no prefix and the /generate read would be cold by construction -- a trap, not a
measurement. This probe reports both before any measurement depends on it.
"""
import json, sys, uuid
sys.path.insert(0, "/home/zer0null/reserach extarctor/experiments/ptr-engine/quality")
from runner import post_json, MODEL, FRAMING, BLOCK_SIZE

body = ("The quarterly calibration record for the lumen instrument is filed under schedule K. " * 90)
msgs = [{"role": "system", "content": body + uuid.uuid4().hex},
        {"role": "user", "content": "Reply with the single word OK."}]
out = {}

# 1. how /v1/tokenize renders it with and without the thinking kwarg
t_plain = post_json("/v1/tokenize", {"model": MODEL, "messages": msgs})["count"]
t_think = post_json("/v1/tokenize", {"model": MODEL, "messages": msgs,
                                     "chat_template_kwargs": {"enable_thinking": False}})["count"]
out["tokenize_plain"] = t_plain
out["tokenize_think_off"] = t_think

# 2. what the chat endpoint itself reports for prompt_tokens / cached_tokens (cold prefix)
chat = post_json("/v1/chat/completions", {"model": MODEL, "messages": msgs, "max_tokens": 4,
                                          "temperature": 0.0,
                                          "chat_template_kwargs": {"enable_thinking": False}})
u = chat.get("usage") or {}
out["chat_prompt_tokens_cold"] = u.get("prompt_tokens")
out["chat_prompt_tokens_details_cold"] = u.get("prompt_tokens_details")

# 3. re-send the identical CHAT request: warm expected
chat2 = post_json("/v1/chat/completions", {"model": MODEL, "messages": msgs, "max_tokens": 4,
                                           "temperature": 0.0,
                                           "chat_template_kwargs": {"enable_thinking": False}})
u2 = chat2.get("usage") or {}
out["chat_rewarm_prompt_tokens"] = u2.get("prompt_tokens")
out["chat_rewarm_details"] = u2.get("prompt_tokens_details")

# 4. rebuild plain text of the same body content and /generate it (no template at all)
ids = post_json("/v1/tokenize", {"model": MODEL, "text": body + msgs[0]["content"][-32:]})["ids"] \
    if False else None
# render via the plain (non-thinking) template path is not reachable from /generate;
# instead test: does /generate of the RAW body text hit? (expect 0 -- different stream)
g = post_json("/generate", {"text": body, "sampling_params": {"max_new_tokens": 2, "temperature": 0}})
m = g.get("meta_info") or {}
out["generate_rawtext_prompt_tokens"] = m.get("prompt_tokens")
out["generate_rawtext_cached_tokens"] = m.get("cached_tokens")
out["generate_rawtext_cached_details"] = m.get("cached_tokens_details")
# re-send the same raw text: is /generate itself warm?
g2 = post_json("/generate", {"text": body, "sampling_params": {"max_new_tokens": 2, "temperature": 0}})
m2 = g2.get("meta_info") or {}
out["generate_rawtext_repeat_prompt_tokens"] = m2.get("prompt_tokens")
out["generate_rawtext_repeat_cached_tokens"] = m2.get("cached_tokens")
out["generate_rawtext_repeat_cached_details"] = m2.get("cached_tokens_details")

print(json.dumps(out, indent=1))
