# CAMPAIGN-ARMS

Arms package under $CAMPAIGN/arms/.

## Tests
PYTHONNOUSERSITE=1 python3 -m pytest tests/test_arms_contract.py -q -> 15 passed

## Defect fixes
1. Gist now structural content-free descriptor.
2. GET recovery protocol + resolve_requests + recovery_message.
3. Preamble parity: arms differ only in ARM line.

## Red proofs
- tampered body byte raises BodyMissing/DigestMismatch
- unknown digest raises BodyMissing
- first-byte change changes prefix identity
- renderer mutation changes renderer_sha256
