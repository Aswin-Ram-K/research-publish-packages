# kg-mini

A tiny fixture repo used by the resextract test suite to exercise the local
graphify binary without any LLM/network access.

## Layout

- `pkg/core.py` — `Job` class and `run_job`
- `pkg/util.py` — `slugify`, `clamp`, `DEFAULT_RETRIES`
- `main.py` — CLI entry point
