# TOOLS8014

Status: complete. Report at orchestration/notes/TOOLS8014.md.

Summary: vLLM 0.27.1 serving qwen3.5-9b (32768 window) lacks auto tool choice; add `--enable-auto-tool-choice --tool-call-parser qwen3_coder`. Harness already supports fetch tool via arm_cd; no harness change needed. Read-only requests only.