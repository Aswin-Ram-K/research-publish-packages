# Grader proof

Mechanism: answer-as-artifact. `tasks/grade/run.py --task <id> --artifact <path>` extracts a fenced Python block (or reads raw), seeds pinned Duval sources, executes the artifact, and prints one JSON line per check plus `verified_success`. `--list` prints check ids, kinds and thresholds from `acceptance.checks`.

## Seed tamper demonstration

```text
REFUSED: digest mismatch: expected 3ffccf2f2f08e65872aa8770234e71d271eb2e6f29e7324673d16bd3135aeafc, got 5d7734e481787db03ffd626c5e5eff898d5647f14997d0564af978cce26970c0
```

## 20 graded outcomes

| task | case | verified_success | failing checks |
|---|---|---:|---|
| T1.discovery | pass | true | none |
| T1.discovery | wrong | false | prov.algorithm, der.algorithm |
| T1.discovery | missing_constraint | false | der.algorithm, neg.no_network |
| T1.discovery | tampered | false | der.algorithm, neg.no_seed_write |
| T1.discovery | hardcoded | false | der.algorithm |
| T2.discovery | pass | true | none |
| T2.discovery | wrong | false | prov.ref_kind_count, der.first_ref_kind |
| T2.discovery | missing_constraint | false | der.first_ref_kind, neg.no_network |
| T2.discovery | tampered | false | der.first_ref_kind, neg.no_seed_write |
| T2.discovery | hardcoded | false | der.first_ref_kind |
| T3.heldout | pass | true | none |
| T3.heldout | wrong | false | prov.scope_count, der.authority_scopes |
| T3.heldout | missing_constraint | false | der.authority_scopes, neg.no_network |
| T3.heldout | tampered | false | der.authority_scopes, neg.no_seed_write |
| T3.heldout | hardcoded | false | der.authority_scopes |
| T4.heldout | pass | true | none |
| T4.heldout | wrong | false | prov.state_fields, der.state_fields |
| T4.heldout | missing_constraint | false | der.state_fields, neg.no_network |
| T4.heldout | tampered | false | der.state_fields, neg.no_seed_write |
| T4.heldout | hardcoded | false | der.state_fields |

## Representative JSON lines

### T1.discovery / pass
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.algorithm","ok":true,"evidence":"stdout contains 'algorithm=blake2b512'"}
{"check":"rec.shard_prefix","ok":true,"evidence":"stdout contains 'shard_prefix=2'"}
{"check":"der.algorithm","ok":true,"evidence":"original stdout has 'algorithm=blake2b512'; perturbed stdout has 'algorithm=sha256'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": true}
```
### T1.discovery / wrong
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.algorithm","ok":false,"evidence":"stdout missing 'algorithm=blake2b512'; got 'algorithm=md5\\nshard_prefix=2'"}
{"check":"rec.shard_prefix","ok":true,"evidence":"stdout contains 'shard_prefix=2'"}
{"check":"der.algorithm","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'algorithm=md5\\nshard_prefix=2'; perturbed stdout 'algorithm=md5\\nshard_prefix=2'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T1.discovery / missing_constraint
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.algorithm","ok":true,"evidence":"stdout contains 'algorithm=blake2b512'"}
{"check":"rec.shard_prefix","ok":true,"evidence":"stdout contains 'shard_prefix=2'"}
{"check":"der.algorithm","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'algorithm=blake2b512\\nshard_prefix=2'; perturbed stdout 'algorithm=blake2b512\\nshard_prefix=2'"}
{"check":"neg.no_network","ok":false,"evidence":"network import detected in artifact"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T1.discovery / tampered
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.algorithm","ok":true,"evidence":"stdout contains 'algorithm=blake2b512'"}
{"check":"rec.shard_prefix","ok":true,"evidence":"stdout contains 'shard_prefix=2'"}
{"check":"der.algorithm","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'algorithm=blake2b512\\nshard_prefix=2'; perturbed stdout 'algorithm=blake2b512\\nshard_prefix=2'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":false,"evidence":"seeded input changed: src/hash.ts"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T1.discovery / hardcoded
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.algorithm","ok":true,"evidence":"stdout contains 'algorithm=blake2b512'"}
{"check":"rec.shard_prefix","ok":true,"evidence":"stdout contains 'shard_prefix=2'"}
{"check":"der.algorithm","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'algorithm=blake2b512\\nshard_prefix=2'; perturbed stdout 'algorithm=blake2b512\\nshard_prefix=2'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T2.discovery / pass
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.ref_kind_count","ok":true,"evidence":"stdout contains 'ref_kinds=16'"}
{"check":"rec.first_ref_kind","ok":true,"evidence":"stdout contains 'first_ref_kind=task'"}
{"check":"der.first_ref_kind","ok":true,"evidence":"original stdout has 'first_ref_kind=task'; perturbed stdout has 'first_ref_kind=alpha'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": true}
```
### T2.discovery / wrong
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.ref_kind_count","ok":false,"evidence":"stdout missing 'ref_kinds=16'; got 'ref_kinds=99\\nfirst_ref_kind=task'"}
{"check":"rec.first_ref_kind","ok":true,"evidence":"stdout contains 'first_ref_kind=task'"}
{"check":"der.first_ref_kind","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'ref_kinds=99\\nfirst_ref_kind=task'; perturbed stdout 'ref_kinds=99\\nfirst_ref_kind=task'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T2.discovery / missing_constraint
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.ref_kind_count","ok":true,"evidence":"stdout contains 'ref_kinds=16'"}
{"check":"rec.first_ref_kind","ok":true,"evidence":"stdout contains 'first_ref_kind=task'"}
{"check":"der.first_ref_kind","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'ref_kinds=16\\nfirst_ref_kind=task'; perturbed stdout 'ref_kinds=16\\nfirst_ref_kind=task'"}
{"check":"neg.no_network","ok":false,"evidence":"network import detected in artifact"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T2.discovery / tampered
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.ref_kind_count","ok":true,"evidence":"stdout contains 'ref_kinds=16'"}
{"check":"rec.first_ref_kind","ok":true,"evidence":"stdout contains 'first_ref_kind=task'"}
{"check":"der.first_ref_kind","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'ref_kinds=16\\nfirst_ref_kind=task'; perturbed stdout 'ref_kinds=16\\nfirst_ref_kind=task'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":false,"evidence":"seeded input changed: src/reference.ts"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T2.discovery / hardcoded
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.ref_kind_count","ok":true,"evidence":"stdout contains 'ref_kinds=16'"}
{"check":"rec.first_ref_kind","ok":true,"evidence":"stdout contains 'first_ref_kind=task'"}
{"check":"der.first_ref_kind","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'ref_kinds=16\\nfirst_ref_kind=task'; perturbed stdout 'ref_kinds=16\\nfirst_ref_kind=task'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T3.heldout / pass
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.scope_count","ok":true,"evidence":"stdout contains 'authority_scopes=2'"}
{"check":"rec.no_decision_refused","ok":true,"evidence":"stdout contains 'real_change_without_decision_refused=true'"}
{"check":"der.authority_scopes","ok":true,"evidence":"original stdout has 'authority_scopes=2'; perturbed stdout has 'authority_scopes=3'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": true}
```
### T3.heldout / wrong
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.scope_count","ok":false,"evidence":"stdout missing 'authority_scopes=2'; got 'authority_scopes=9\\nreal_change_without_decision_refused=true'"}
{"check":"rec.no_decision_refused","ok":true,"evidence":"stdout contains 'real_change_without_decision_refused=true'"}
{"check":"der.authority_scopes","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'authority_scopes=9\\nreal_change_without_decision_refused=true'; perturbed stdout 'authority_scopes=9\\nreal_change_without_decision_refused=true'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T3.heldout / missing_constraint
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.scope_count","ok":true,"evidence":"stdout contains 'authority_scopes=2'"}
{"check":"rec.no_decision_refused","ok":true,"evidence":"stdout contains 'real_change_without_decision_refused=true'"}
{"check":"der.authority_scopes","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'authority_scopes=2\\nreal_change_without_decision_refused=true'; perturbed stdout 'authority_scopes=2\\nreal_change_without_decision_refused=true'"}
{"check":"neg.no_network","ok":false,"evidence":"network import detected in artifact"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T3.heldout / tampered
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.scope_count","ok":true,"evidence":"stdout contains 'authority_scopes=2'"}
{"check":"rec.no_decision_refused","ok":true,"evidence":"stdout contains 'real_change_without_decision_refused=true'"}
{"check":"der.authority_scopes","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'authority_scopes=2\\nreal_change_without_decision_refused=true'; perturbed stdout 'authority_scopes=2\\nreal_change_without_decision_refused=true'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":false,"evidence":"seeded input changed: src/authority.ts"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T3.heldout / hardcoded
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.scope_count","ok":true,"evidence":"stdout contains 'authority_scopes=2'"}
{"check":"rec.no_decision_refused","ok":true,"evidence":"stdout contains 'real_change_without_decision_refused=true'"}
{"check":"der.authority_scopes","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'authority_scopes=2\\nreal_change_without_decision_refused=true'; perturbed stdout 'authority_scopes=2\\nreal_change_without_decision_refused=true'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T4.heldout / pass
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.state_fields","ok":true,"evidence":"stdout contains 'state_fields=16'"}
{"check":"rec.derived_regions","ok":true,"evidence":"stdout contains 'derived_regions=12'"}
{"check":"der.state_fields","ok":true,"evidence":"original stdout has 'state_fields=16'; perturbed stdout has 'state_fields=17'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": true}
```
### T4.heldout / wrong
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.state_fields","ok":false,"evidence":"stdout missing 'state_fields=16'; got 'state_fields=9\\nderived_regions=12'"}
{"check":"rec.derived_regions","ok":true,"evidence":"stdout contains 'derived_regions=12'"}
{"check":"der.state_fields","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'state_fields=9\\nderived_regions=12'; perturbed stdout 'state_fields=9\\nderived_regions=12'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T4.heldout / missing_constraint
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.state_fields","ok":true,"evidence":"stdout contains 'state_fields=16'"}
{"check":"rec.derived_regions","ok":true,"evidence":"stdout contains 'derived_regions=12'"}
{"check":"der.state_fields","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'state_fields=16\\nderived_regions=12'; perturbed stdout 'state_fields=16\\nderived_regions=12'"}
{"check":"neg.no_network","ok":false,"evidence":"network import detected in artifact"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T4.heldout / tampered
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.state_fields","ok":true,"evidence":"stdout contains 'state_fields=16'"}
{"check":"rec.derived_regions","ok":true,"evidence":"stdout contains 'derived_regions=12'"}
{"check":"der.state_fields","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'state_fields=16\\nderived_regions=12'; perturbed stdout 'state_fields=16\\nderived_regions=12'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":false,"evidence":"seeded input changed: src/observation.ts"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
### T4.heldout / hardcoded
```json
{"check":"exec.exit0","ok":true,"evidence":"exit code 0"}
{"check":"prov.state_fields","ok":true,"evidence":"stdout contains 'state_fields=16'"}
{"check":"rec.derived_regions","ok":true,"evidence":"stdout contains 'derived_regions=12'"}
{"check":"der.state_fields","ok":false,"evidence":"tracking failed: original exit 0, perturbed exit 0; original stdout 'state_fields=16\\nderived_regions=12'; perturbed stdout 'state_fields=16\\nderived_regions=12'"}
{"check":"neg.no_network","ok":true,"evidence":"not fired"}
{"check":"neg.no_seed_write","ok":true,"evidence":"not fired"}
{"check":"neg.no_outside_write","ok":true,"evidence":"not fired"}
{"verified_success": false}
```
