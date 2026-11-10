# Authoritative envelope pointer

Run id `CCS-2026-11-05` is governed by `run/envelopes/CCS.json` (revision 5, `max_tokens: 2400`, thinking off via driver default, 144 calls).

`envelopes/CCS.json` revision 6 (`max_tokens: 3200`) was written to a path `run/driver.py` does not read and was NEVER used by any run; it is marked `void` in its own `envelope_revisions`. Neither file is deleted.
