#!/usr/bin/env python3
"""Read-only SGLang /metrics snapshot helper."""
from __future__ import annotations
import argparse, datetime, urllib.request, os
from pathlib import Path

FAMILIES = ("sglang:cache_hit_rate", "sglang:prefill_effective_tokens_total",
            "sglang:uncached_prompt_tokens_histogram")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="http://192.168.2.168:8012")
    ap.add_argument("--phase", default="baseline")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()
    base = args.endpoint.rstrip("/")
    url = base + "/metrics"
    with urllib.request.urlopen(url, timeout=10) as r:
        text = r.read().decode("utf-8", "replace")
    # filter families
    lines = []
    for line in text.splitlines():
        if any(fam in line for fam in FAMILIES) or line.startswith("#"):
            # keep header comments for those families too
            if line.startswith("#"):
                # include if next? simpler: include all comments
                pass
            lines.append(line)
    # keep only relevant families + their HELP/TYPE comments
    wanted = set(FAMILIES)
    out_lines = []
    i = 0
    raw = text.splitlines()
    # include HELP/TYPE lines whose metric name in wanted, plus data lines
    for line in raw:
        if line.startswith("#"):
            # check if any wanted family appears
            if any(f in line for f in wanted):
                out_lines.append(line)
        else:
            if any(line.startswith(f) for f in wanted):
                out_lines.append(line)
    body = "\n".join(out_lines) + "\n"
    out_dir = Path(args.out_dir) if args.out_dir else Path(__file__).resolve().parent / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = out_dir / f"{args.phase}-{ts}.prom"
    header = f"# endpoint: {base}\n# counters: {', '.join(FAMILIES)}\n"
    out.write_text(header + body)
    print(str(out))

if __name__ == "__main__":
    main()
