# Envelope reconciliation — CCS-2026-11-05

- Governing (authoritative) file for run id `CCS-2026-11-05`: `run/envelopes/CCS.json`, revision 5, `max_tokens: 2400`, thinking off via the driver default, 144 calls. Every recorded main row carries `max_tokens: 2400`.
- `envelopes/CCS.json` revision 6 (`max_tokens: 3200`) was written to a path `run/driver.py` never reads and was NEVER used in any run. It is marked `void` in its own `envelope_revisions` with that reason.
- Neither file was deleted. Pointer: `envelopes/CCS-AUTHORITATIVE.md`.
