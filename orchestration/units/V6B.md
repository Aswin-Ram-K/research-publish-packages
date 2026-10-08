# V6B — independent adversarial verifier, U6.5 nested-docket path validator

Purpose: try to break the new `safe_docket_slug` boundary. Fix nothing. cwd workspace-only; source reverts confined to `src/resextract/dashboard/api.py`, done last, sha-proven, bit-identical restore.

Method: 53 slug inputs through a raw ASGI scope (bypassing client-side dot-segment normalisation), against a scratch copy of the dockets tree under `state/verify/V6B/` with planted symlinks, a corrupt manifest, a file-as-segment, an internal-'..' dir name, and a symlinked heading file. Then three sha-proven reverts (api.py:122, realpath containment, segment validation), then one live server.

Result: PARTIAL. The validator holds — 0 x 500, 0 out-of-root 200 for any requested path, every traversal refused by segment validation, `escape` refused by realpath. One handler-level gap found: a symlinked HEADING_FILE inside an accepted docket is read through the symlink and its heading text + size are served (see handoff bypasses_found).

Evidence: orchestration/handoffs/V6B.json, state/verify/V6B/{attacks.json,probe3.log,live-dockets.json,live-nested.json,reverts.py,control.py}, state/logs/V6B-serve*.log
