# UFIXNOTE1 — correct stale build records (BUILD_NOTES.md / METADATA.md)

- Unit: UFIXNOTE1
- Purpose: measure on-disk truth for three papers; correct every stale figure in
  `papers/*/submission/BUILD_NOTES.md` and `papers/*/submission/METADATA.md`; keep every
  superseded value visible as dated history; never edit measured numbers, claims, refs, or bib.
- Papers: encoder-crossover-190, gated-read-batching, replay-record-not-decision
- Declared write paths: papers/*/submission/BUILD_NOTES.md, papers/*/submission/METADATA.md,
  orchestration/units/UFIXNOTE1.md, orchestration/handoffs/UFIXNOTE1.json, scratch/ufixnote1/**
- Hard bound: 12 tool calls
- Constraints: /home/zer0null/Duval STRICTLY READ-ONLY, never run git against it;
  submission/main.tex is GENERATED (never hand-edit; regenerate only via
  `python3 tools/package/md2tex.py --package <slug>`); do not change any measured number,
  claim, reference, or bibliography entry; do not rewrite history.
- Status: in progress
