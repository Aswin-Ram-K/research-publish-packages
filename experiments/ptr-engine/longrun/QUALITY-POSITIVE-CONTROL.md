# Quality Positive Control

## 2026-11-08 — Re-homing suite execution to the independent verifier

Suite execution now belongs to the independent verifier at gate 0.8, not to a
model-driven exec channel. A model-driven exec channel was rejected because it
breaks read-only containment on a shared live server; only a fixed
argument-free pytest in a network-disabled sandbox would make it defensible.
