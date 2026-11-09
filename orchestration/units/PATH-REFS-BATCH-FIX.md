# PATH-REFS-BATCH-FIX — repair the wrong-directory citations, mechanically

Card: unit `PATH-REFS-BATCH-FIX` (board execution). Predecessor: `PHANTOM-PATH-FIX` (`0dac7b91`), which shipped
`experiments/ptr-engine/tools/path_refs.py` and baselined its census forward-only. This card spends that instrument: it
substitutes cited tokens so they resolve, and proves nothing but the token moved.

**Hard bound:** 40 tool calls. **Offline:** zero inference requests. **Automated:** no questions asked.
**Write paths:** `docs/**/*.md` (existing) · `orchestration/STATUS.md` · `orchestration/VERDICTS.md` ·
`orchestration/units/PATH-REFS-BATCH-FIX.md` · `orchestration/handoffs/PATH-REFS-BATCH-FIX.json` ·
`orchestration/journals/PATH-REFS-BATCH-FIX.jsonl` · `state/logs/path-refs-baseline.json` (see DEVIATION 1).

## Method (substitution only; oracle = the tool's own resolver)

1. `path_refs.scan()` at the session root gives every citation with its `classification` and `resolved`.
2. Fix set = every `wrong_dir` occurrence in `docs/**/*.md` + `orchestration/**/*.md` whose `resolved` names
   **exactly one** existing file. `resolved` is the tool's answer (`classify()`, `path_refs.py:138-152`); no second
   resolver was written.
3. Substitution replaces only the cited substring inside the `PATH_RE` match; trailing punctuation, backticks, prose and
   any `:LINE` suffix outside the match are untouched. No line was added, removed or reordered.
4. Ambiguous (`>=2` candidates) and `missing` occurrences are **skipped and listed**, not guessed.

## Result

| measure | before | after |
|---|---|---|
| census `ok` | 25,735 | 26034* |
| census `wrong_dir` | **794** | **645** |
| census `missing` | **266** | **266** |
| in-scope (`docs/**` + `orchestration/**/*.md`) `wrong_dir` | 280 | 130 |
| baseline anchors (distinct keys) | 752 | **641** |
| baseline occurrences | 1,057 | **911** |
| `path_refs.py --check` exit | 1 (3 new keys) | **0** |

\* `ok` rises by more than 150 because the 150 repairs land in `ok` *and* because peers wrote new documents
concurrently; one extra `wrong_dir` appeared in `orchestration/handoffs/*.json` during the pass (not this card's file,
and not counted as repaired). **Repaired: 150 citations across 68 files, 54 distinct cited tokens**, all
`wrong_dir`→`ok`.

## The proof: only path tokens moved

For each edited file both versions were normalised by replacing **every** citation token with `<P>`
(`PATH_RE.sub("<P>", text)`) and the normalised byte strings compared. All **68/68 byte-identical** — the check re-parses
both texts independently of the edit code, so any change outside a citation token changes a normalised file.

| file | sha256 before | B before | B after | Δ | tokens | sha256 after | normalised sha256 | token-only check |
|---|---|---|---|---|---|---|---|---|
| `docs/CAPGATE-FOREIGN-RED.md` | `9eafa4a00b57…` | 3289 | 3382 | +93 | 3 | `7f4ae1d7e999e77a4a96879981727f7f0b2b2db06ea849066d2339fe597ee9c3` | `b4baf7789bc27e432e624fc22e0722393fc630125cc5383cf5d79455f5aa1056` | byte-identical |
| `docs/COLD-START-PROBE.md` | `b75702dccf54…` | 6872 | 6903 | +31 | 1 | `28ef7a91ab83cbd0e0739c39c42e08956b88de74aecf3d75d4836b906849d5db` | `5a4b7353fab335e7c617d421fd24254acfa6e86f7c330116a22fc9ffdf05004b` | byte-identical |
| `docs/DECIDABILITY-SEAM.md` | `d1444d7c6d75…` | 7243 | 7269 | +26 | 1 | `1e4eafe0907404719e6dc1fa30abe7dfb1f7c8307dc28fd3f8e403b18b56b0e1` | `caa2bff139472303becd87e088520b25e9f7e358451bdb1a3d5730ec86978050` | byte-identical |
| `docs/EXIT-CODES.md` | `b9eda873e817…` | 14035 | 14097 | +62 | 2 | `48f45746231e3071733aec6f28f92930829d729c4af1078bb8a9236f2ae2caa4` | `d0dfcbb02dde2396757d8b93e8d59f4b1445b57a67432e9dd1933b5bd5ed956c` | byte-identical |
| `docs/EXTERNAL-EVAL-PRACTICE.md` | `23cde09e67d3…` | 37972 | 38041 | +69 | 3 | `67af142738d2ff53757b59ca712c84c9821d97ce392ab03a2d46e1a5c2c87083` | `3ae396962c5a324df3bdc543264c455adf810d00dbac7ed14df21657707a6b39` | byte-identical |
| `docs/EXTERNAL_WORKSPACE_POINTER_PROTOCOL.md` | `1edc6307780e…` | 11475 | 11455 | -20 | 1 | `2411bcb0f83fb9e38f33b1e29cd9e03c9c03b030785890e9cefb0f1c65707802` | `ba89e0f71806ef21dccb16c69a613bf7ac0072959731f65be1743045b1771232` | byte-identical |
| `docs/FROZEN-TREE.md` | `1f6ddcad22bc…` | 6795 | 6826 | +31 | 1 | `f36fe0590d74c040f4ea3d496fe7dbf68bdc332e38c9e3363a5a4b92bf4c090a` | `114ec68d2956f0e36b02e491627e92f0f2629ce3b3fa7e82198bf31e0326bb65` | byte-identical |
| `docs/GATE-CHAIN.md` | `89f2a7890cd2…` | 34616 | 34802 | +186 | 6 | `4c1f3b6c42879133b71094db87dd3942e25528bebd3c1a14e4520f4b864ec1aa` | `bb543ac1a899003326860dde98188436a23fac286b68846ebfb0fdb0ec85b66f` | byte-identical |
| `docs/GRADE-V5-REPAIR.md` | `4ab9854f18f9…` | 5711 | 5804 | +93 | 3 | `7d6b467eb43d299460155a20b6e84e85efa661d47f33f1329108ef6053c26372` | `051bc0306c0a7d0de523baf793ddba78e97278d8b5f843f7ab2183248dddb1eb` | byte-identical |
| `docs/GRADE-V6-DERIVE.md` | `77beeab4828c…` | 10201 | 10325 | +124 | 4 | `5b5be192ef73a612dc5cff5f9b2f20f3f248b2ba4b7b9ea45d94d93c85cca1b9` | `fce7aa842bbcf10d4c7aca6723ce71114b89844063ac0cde644a2aa11cc8e8ed` | byte-identical |
| `docs/LATENCY-ERA-CENSUS.md` | `ca010068543d…` | 51787 | 51849 | +62 | 2 | `650258ab01259168dfb751c771e1ce7fe55432fa433552ab7af54651a862e6df` | `daceba22bf460738beb6616c98008267f1ca750ad29d74bf698d6ac6e22dec0a` | byte-identical |
| `docs/LOST-FIXTURE.md` | `b0614a96a244…` | 11906 | 11968 | +62 | 2 | `65ac1fc8d1e0c30222347e3beb942ed8b0466ea3fb1c1980a6f4a49cbc453731` | `9805ffa4bf048a9c0aea82d9662dcec51dcfc2d713ff870b5066710f1e04eece` | byte-identical |
| `docs/PROJECTION.md` | `f69af7b42a00…` | 4471 | 4502 | +31 | 1 | `c15a1ff34770e714c291a81eadb87827ddc91ef2da0bd493a0e9cd6b0fb36ea9` | `b970831f20f4475d7d509f3f3d3e94ee768b2f2795e8a2c509d8f269df823280` | byte-identical |
| `docs/PROVENANCE-REFUSAL.md` | `fe6735af7dc8…` | 11403 | 11589 | +186 | 6 | `5e079cd2bf718251212e07b36376196b1b43f88acd449a873fdead5c63c7c65d` | `87bf897d3617d4f889d85a3f4e261e1699baa38bf915cb2d334b603aa1f8e88f` | byte-identical |
| `docs/QUALITY-REASON-MIX.md` | `1ab38138c953…` | 14344 | 14375 | +31 | 1 | `3dd6dd119010329d8b36c8d147035090698580e763093a68bfeb7692c93614b5` | `ac94c2e4e0dcc8a7d7f9d1e14d96135fda1f72daffd35dd3c5d846a3857646a6` | byte-identical |
| `docs/RECLAIM-ACCEPTANCE.md` | `1335af486cb4…` | 5146 | 5239 | +93 | 3 | `3b124513c3a81f379e0c14910d65876cb06f8555f519ed618d99ad93c8339850` | `fa0f89f066ae6247417b33490e40eae0dbf69b4081b66188622d902b726f3410` | byte-identical |
| `docs/REQUEST-IDENTITY.md` | `65eac00d4a1a…` | 13659 | 13690 | +31 | 1 | `9e3564b67597c177bafffb06a2228879599190d3de6ab88c65adb68a10790b7f` | `8aefededc029bdf5a58dc3e4442adcab83f1631d23435c20e3df4e342bae945b` | byte-identical |
| `docs/REQUEST-LEDGER.md` | `4495b46de7fa…` | 22265 | 22288 | +23 | 1 | `f8b7b70ebc1b51d0fc13b407e202bdc2d0e91dc1a3e6faded53c8116c72e49a9` | `efec0fe0006130f21e1c7b7225b9ef4048afa4fa1ccda0e8508512f7c26a587e` | byte-identical |
| `docs/TREE-FREEZE.md` | `16be461054c5…` | 7941 | 8003 | +62 | 2 | `c5565d64d8b24fcd2caaac04623a524118575c5db26fb2cbc17deb569944d89b` | `6a518c174dc213c5d8fc3135f42225f9400317d74f6757bd5b2a7b2aee95bef6` | byte-identical |
| `docs/V-CAPGATE-REFUSE.md` | `f458dedae19b…` | 7337 | 7368 | +31 | 1 | `cde280b0344a0338941c1e6f90c55794cf8703f645334c22ff74ec8d535d05dd` | `3eee0181327ab2a940d70fe8df710b9f76630fdc9fc510855124c3152ecac3d2` | byte-identical |
| `docs/V-GATE-OPERAND.md` | `d7b795612784…` | 8063 | 8218 | +155 | 5 | `70a345fd510a0025b246b8c112a4cdca55a1dca49f544fa91f58f4da9f3ea8d8` | `1b05286abed07c7f3fc1dd15a4ce6ef8ff3381c1fa940e56aff14051041e4fea` | byte-identical |
| `docs/VERDICT-BACKFILL-FIXTURE-GENERATIONS.md` | `3c232cf187db…` | 3360 | 3391 | +31 | 1 | `e64f704882186fbeeeba73f05fd651b34eeb133bcd23b490554f0f9da3ed0232` | `f210cd086eb5b2cd400a5f6039ed1f54ed24f3fc65afecd5a8d1026dd6f7e747` | byte-identical |
| `docs/VERDICT-SEMANTICS.md` | `09e2f971e869…` | 4392 | 4423 | +31 | 1 | `2b4102f5c8857622688d19acf308d8c3c7909e507b23d0d8a0f50841524bd983` | `fbc8cef8f7f820696209500bc11fe5458a5ff867d414aeb3746460d87da5c780` | byte-identical |
| `orchestration/units/ANSWER-CONTRACT.md` | `8d2dcf919aba…` | 7882 | 8006 | +124 | 4 | `a139839e04345cb9d7a1863e598a143147f4cf6f9ceaf6a5553787eaebd616a5` | `9cf377c5887a16b0313e440e5492e6af1708e2c4fcb10043b1e2dd855d350f15` | byte-identical |
| `orchestration/units/ARM-TREATMENTS-FIRE.md` | `5e10f2bc1cc3…` | 1754 | 1785 | +31 | 1 | `176b6ce9cf04605789dfe9e78074c0833f7f3ebffcf39742450b071ee2fdac9b` | `dd70e95f66625aa6d2cf20e971065e1f6c16b0f7d62bf3f36220a3dfd8fc9d9b` | byte-identical |
| `orchestration/units/CAPGATE-FOREIGN-RED.md` | `cde351c7fef2…` | 1384 | 1446 | +62 | 2 | `8d49799040dacbc413da115c77f741631ff514b7d4b3ac0f0690629ce94f67d0` | `5391f3f1697406eb044aba21f1eae2cf1e9b1ac3b04fe77edfaf928622f04e51` | byte-identical |
| `orchestration/units/CAPGATE-UNRECORDED-REFUSE.md` | `1ce7d41c63df…` | 1964 | 2026 | +62 | 2 | `af2dd7e55604077f2af77f8ccb7d9d4c6718c01a53f41b346ef97dfe727fdcde` | `77e7346db4df62e1353ab3bcbf61751c75030695e8edc5954df818dcfd5dc309` | byte-identical |
| `orchestration/units/CHECKPOINT-COVERAGE.md` | `6b977715426a…` | 3198 | 3229 | +31 | 1 | `32aa0a322c474f41e5403df3e4450561f65411cd180b4ea4ab2b518b420ba939` | `6f47c60ab6e049a3426ed9dc87568546d1dbe512b991f432d262651387dcfd5f` | byte-identical |
| `orchestration/units/CLAIM-ROW-STAMP.md` | `a488222b54f9…` | 861 | 1047 | +186 | 6 | `b7c3149021a195f4ae8050e44fc74284d8b5a1da78065a4bc48d66a8016515a4` | `3ed8aa213debd6c112929e52193c94c22c58e1a4afb255ee585b29e45398be25` | byte-identical |
| `orchestration/units/DEDUPE-ROOT-CAUSE.md` | `f5672a58ea5b…` | 8000 | 8031 | +31 | 1 | `dea3b433206f129bfdb4d881b8584d180390f671363fe9b263a39557142a80e8` | `05ae2aa221a23cbf844302b0773390c8fe6b58fde520447c19fdb6421527f8b6` | byte-identical |
| `orchestration/units/DET-VERIFY.md` | `3df09b955dda…` | 14743 | 14772 | +29 | 1 | `f71f4b0d6dc0681f56578c00cd59364877feeab5d0f9214c0c3f64de3e93bddc` | `9bbe17069de9152f3640876cc96daeb8a1df3f34ea3778e44c2c8a034b78d71c` | byte-identical |
| `orchestration/units/ENGINE-R2.md` | `c93f55969691…` | 5112 | 5135 | +23 | 1 | `5ded6f7824c7509041fbe0aa17bb79d1d60f47a1b078cfb128febe5c217e7169` | `121b51bee2773a44702313ec6b1c4750ac31d56af48eb72d13ac6cad877bc26e` | byte-identical |
| `orchestration/units/EVAL-STATS.md` | `de06b7f75697…` | 6395 | 6426 | +31 | 1 | `2eb26f46912112f82890bc44f9709515dd483eb1a7089c39fd572db1bc3587ca` | `c8952662847206b273d07068a3e30b2d8299211e9e7510dd0402496615fd0566` | byte-identical |
| `orchestration/units/EXIT-CODE-TABLE-2.md` | `e495da7fde33…` | 7315 | 7377 | +62 | 2 | `893564d1937c2fa53b174c012f87c2be4d9eaec83bd61613a5a40f70604aac34` | `0006d09467800e65a1fec76bb4aa08220013ac9b08bd182a625f2a3676f81934` | byte-identical |
| `orchestration/units/EXIT-CODE-TABLE.md` | `4e5433a251d9…` | 4317 | 4379 | +62 | 2 | `0d7aa47d62636a4056bb2c3fbc1a059faf578ef6c43d9986f3f5921cac297e4b` | `c7384b1c5aa41969d81ce111353743208556e54a72c5bb06193b5dd1907ff65a` | byte-identical |
| `orchestration/units/FETCH-CHANNEL.md` | `9793908fb3f5…` | 3527 | 3558 | +31 | 1 | `68b7d326b05fe18a402549c22e220505d81f1d33445fc9ce2599e08b3748f92e` | `f23b2957f7f2b2096c2ea6d812e77a5241019f1bbd0039a815ffe6df4673b5bb` | byte-identical |
| `orchestration/units/FIXTURE-GENERATIONS.md` | `f477ea05c4b3…` | 2322 | 2353 | +31 | 1 | `94b2e8b28b9bec3108cbec88885a395a60f8d2eb846b71bb6e777202a109cf15` | `419c490ce6d3b3b9d0e77fb6d23e10cb5847d098e7cf4b601252058d09759276` | byte-identical |
| `orchestration/units/GATE-CHAIN-FIX.md` | `c2ea4ab5d74c…` | 2018 | 2173 | +155 | 5 | `735e36280607ad964aa98890c9070cfb1303ab88da471bac20249ded26e2ad88` | `4503e7cc0f3fb6e93f1a085fcb29a3fba1b3f3fb51ce14b2c2d0831290bc13b1` | byte-identical |
| `orchestration/units/GATE-OPERAND-VALIDATION.md` | `43dd23ebcaa2…` | 5407 | 5531 | +124 | 4 | `b5329826a2fbf5b33348a431ebaa6be666955b3ab9c7eaf1d348335802458082` | `5d837922eda207b0a59410a6a548356dab600f3d9fad04007f0709903b360cd6` | byte-identical |
| `orchestration/units/GRADE-V4-R2.md` | `0b5a5d35efc1…` | 6977 | 7039 | +62 | 2 | `934ad8480126a286ea015648ff9993d09cd7575ecce5fe34fd87658ed74ce061` | `b6206543463e04117d668748cc833e055a1ff4318d98e55d511076038da10ca4` | byte-identical |
| `orchestration/units/GRADE-V6-DERIVE.md` | `f72f80d504ba…` | 3588 | 3619 | +31 | 1 | `eeab2d2a2164d8f31f8712d9a5538bc4815df58ed0b8c90655b98fd1f7b01be3` | `93e7fbfd84643cfe6c6a4a67e2a0dbaf3d14d186c500023cfdf7071625fbced1` | byte-identical |
| `orchestration/units/HARNESS-FIX-CLIENT.md` | `45816cf777ab…` | 6943 | 6974 | +31 | 1 | `869b3225c68acde11acc0a2a45fad667b5837b020171c77776938101ee940748` | `11ff4c9498f56fc56899dc6f58d84f8573186d9b7202aaf62ed5adae217363be` | byte-identical |
| `orchestration/units/HARNESS-GUARDS.md` | `e7e2531d3fa5…` | 6364 | 6519 | +155 | 5 | `f88fd60354c8ad86f7f6e3863b59a3f6f83420142e6afa0a8cda7433bb09d850` | `fee6e675ad61b9236b13e920b213dea3fc89864dfbb17433b3ca06acf3ccbe7c` | byte-identical |
| `orchestration/units/HIT-LEDGER.md` | `8c475faa7280…` | 8009 | 8285 | +276 | 12 | `d090633af30bc9bf029a0a253eaf97c5d5bf78abbd000ffe59a9077367deb664` | `c30f9cb0a643fe9b96e5ef7f2540eb11ba737c7091d7f5c2d58202618faeee6e` | byte-identical |
| `orchestration/units/LEDGER-CONSERVATIVE.md` | `6a083b31dea5…` | 2908 | 2931 | +23 | 1 | `818c3f16fa53a91efe6b3745da9b5b078e0936b5c4298cfe3f64893cb38dd780` | `f95bb9b3c3aa382d273f221c022e9c0bcba5069e02b6b9804c08d6719befb507` | byte-identical |
| `orchestration/units/MATRIX-HONESTY.md` | `289c57e2df58…` | 3787 | 3818 | +31 | 1 | `3ed73cdd28e244e0463635d077a53b18220f7444d8259b0140eee511ed2998c2` | `4b11d85c548a8008ce6fee33734f35e340dd6e94a032c039026322ce1ba539ea` | byte-identical |
| `orchestration/units/PROBE-CP3-V6.md` | `a41e263aa0f1…` | 6379 | 6441 | +62 | 2 | `0d22089c52609d5139960825caca9d622a392a730a799125a87e93731b3e2e0c` | `54494f85d18d3e706c5bc39e03c2cc6b6fe3d020fc26c2ed55d743df6efb265a` | byte-identical |
| `orchestration/units/PROJECTION-CALIBRATION.md` | `371dd81131a7…` | 4205 | 4236 | +31 | 1 | `239fce8f6da8c8d89853b46910d709cd5150f2f2f81d053a1d88d8122c6d52e3` | `e17fca3db2ec6d037d68a8fbce8d9ca463499cd0fa958e9925c778994d2f4e8f` | byte-identical |
| `orchestration/units/PROJECTION-MODE.md` | `2420b3a95334…` | 2973 | 3004 | +31 | 1 | `15c519960bfbc0c60a564607463e166482215442b1e49030cd22547985ba6747` | `23ed5b8b129ad6ad25da402cbbb1847f91d8628af4f350fcea3b2d81f1de0a2b` | byte-identical |
| `orchestration/units/PTR-ENGINE-P0.md` | `a5f4a98d47d5…` | 2885 | 2908 | +23 | 1 | `83c18c24385f556ef7fd266e1f7e97cd28966e049efa7044373345ca66d51a8a` | `2dad3336e49ebb2a42a352e2dd825ccfb8c96697ea7863616ca99923cc291dff` | byte-identical |
| `orchestration/units/RECLAIM-ACCEPTANCE.md` | `ed718b3af394…` | 1839 | 1870 | +31 | 1 | `c4627be6b3bedcfd7e391c82ffbfc7d7695cf9a8447f486a043fdaf0a0eb74d4` | `1197429d274c9693e67ad55bb922cc7407b29c0ac0f34b79197dd6bc9809d4ba` | byte-identical |
| `orchestration/units/RUNNER-WALL-KEY.md` | `691461640764…` | 1695 | 1726 | +31 | 1 | `6305e454e7496edbbf61674ed2146e3f3a8a3a239585893ef54196717f55f409` | `2eecb178f090fb9883365f0899b35ecdc4d5b3867e938b73ff985400627b711e` | byte-identical |
| `orchestration/units/SEAM-TEST-RED.md` | `b957f3c15641…` | 6105 | 6198 | +93 | 3 | `13d6fd70d79dc4a74a2f26783237a601586fc030fcfeb51780ab6c561962da96` | `d4ddd4a9ccc7c5b878a1b05e0fed60af5cd8c1143d818f0cb3a464a4fbb039a3` | byte-identical |
| `orchestration/units/SPAWN-RECORD-BIND.md` | `045f9fd5cacf…` | 1255 | 1286 | +31 | 1 | `e41b57727546b0effc6591c59bed7ea54631127c3d251c810dc6f904be9a24b3` | `38c30253e238d4d286b2c0c7963eaa69e1212e96158029557393c0d3307c8f8b` | byte-identical |
| `orchestration/units/SPAWN-TREE-BIND.md` | `86465b429a80…` | 2521 | 2583 | +62 | 2 | `811f5d0c0351201fcfff86c6858c9ab42aa021bcc0da57d82c9f5013f8c2c9e7` | `97c0658dea0b004b8f89267b8e05b4f001ebf1d0bc94c564e2259871edb23b2c` | byte-identical |
| `orchestration/units/STOP-REASON-HOLES.md` | `8e42e6774510…` | 1976 | 2007 | +31 | 1 | `853a94033158f8f6ce7fb10c2adca7da76a1242c5f0fc89cbe1613e3a05c27ce` | `f9ff268a9c9feebec8302d3094d033472288ac0ff606f0672abae4d1969c3d9f` | byte-identical |
| `orchestration/units/TRANCH1-DRYRUN.md` | `cffb9f39f169…` | 2531 | 2562 | +31 | 1 | `478e7343e8146c5ba0a7ac5ea2be10be66cc5df2c5e3b4aff514a582a893cbf0` | `5fcb9251cb949cc18169a05762d28e24772dfba1ffe3fa3eb86359633bc6abb9` | byte-identical |
| `orchestration/units/TURN-ROW-ATTRIBUTION.md` | `0171fa5e2368…` | 2588 | 2650 | +62 | 2 | `0707678255487ce02d54d265628e79ad1cb728672e43c69ebfaa129247356c86` | `2da11ce5a81ac788a6c741c0065ea07c77bc8be51bb6f4e5b36826b097620c93` | byte-identical |
| `orchestration/units/V-ENGINE-P0.md` | `fdd0be4efac1…` | 8657 | 8772 | +115 | 5 | `a1a503419f2151a21401d190250ea3d31d3565366e6baf36deb303b9b832babd` | `1e2789f3a268e1d6ca19ec886ead8b456a258f77346fcd5d39d909124ed3c21d` | byte-identical |
| `orchestration/units/V6-COMPLETE.md` | `9b32466d7d3d…` | 3165 | 3196 | +31 | 1 | `00a5ea3e4515a94d94398ad9a574e4e66a1034f714d8f55511fef9b91c7a379f` | `3689908b376c9a5f956d60b8996201c26a13882c2e1bb1d31bbb716de6ca3598` | byte-identical |
| `orchestration/units/V8-DRYRUN-REFREEZE.md` | `fab023fbb90b…` | 692 | 723 | +31 | 1 | `b98cc4b53f6e0dfcee7d7c2def92c26c82b1eeb303a5e8d3be4fc462fa818f4c` | `a8149589756783ba01399d4b961eb2cdd3b4f05743896dc2917dc52a69936b73` | byte-identical |
| `orchestration/units/VERDICT-REFUSAL-SEMANTICS.md` | `b045d98f50a1…` | 1385 | 1416 | +31 | 1 | `d85e220d6293fec3e14dd320ff215bdaec2482220ada316224d3be3d3fe7fa82` | `87b7dd8148572282d13c79210d55fd43e883df98216bc93f863c740fe0ddacd9` | byte-identical |
| `orchestration/units/WIRE-CAP-GATE.md` | `bef09e0a9b03…` | 3206 | 3237 | +31 | 1 | `76f6b8458c3042f6f816332a5f6e59b19d33fe4f465c23a46b407749e87a7989` | `7a3001ff16e58820d2737906633b4774c711f6e48ccfc6407d44a1cd966015d2` | byte-identical |
| `orchestration/units/WIRE-CLAIM-MODE.md` | `3495179368ae…` | 1549 | 1611 | +62 | 2 | `29e224413b45a0d48df1dd47c05a9a17de5108b9b0510902d7a205c24126c6a8` | `f8787789833580f8e93828a6b183c3fae79b194e742596e7cd47d15a75d24d56` | byte-identical |
| `orchestration/units/WIRE-CLIENT.md` | `f954eaffa579…` | 4889 | 5137 | +248 | 8 | `a365e6d013ed6f07ad7b9f1f00d72c4f878601728289768d3628343970108849` | `7bba421f1500af1e70ba091d84e75514b375bfd9342cc66290d258fcd79f67ef` | byte-identical |
| `orchestration/units/WIRE-GATES.md` | `52a101439396…` | 4188 | 4250 | +62 | 2 | `30b7c97076aaf1342d0d1c4ddc0bdccd096af75237a78e88c1d5c9c6768a8136` | `b04a51e69c3d4eedd271231b3f9e7d8bd4041784ba6006d2523d1dbff9d2d4cf` | byte-identical |
| `orchestration/units/WIRE-PROVENANCE-INTO-STATS.md` | `a054a40f539f…` | 3297 | 3299 | +2 | 1 | `eb0d40b875239cbc50486bae88ed9ecaa3abf20ed5bf209c734b7c1590208f47` | `6587801c8efbef74796ae2b4e80128ceb876ca2e0fbd5fb805b9fdf635d46854` | byte-identical |
| `orchestration/units/WIRE-TREE-FREEZE-INTO-VERDICTS.md` | `e850f5467e91…` | 1774 | 1805 | +31 | 1 | `95e881a74842259b31f7f5eef12e1f062a9f88f126098b172debd919db5158fd` | `3d042904656605d4b649c4e5afcc3f15a4c19aba5e80976a4042ea5b9ad5a6b6` | byte-identical |

The `sha256 before` column is the first 12 hex of the digest measured in the edit pass; the full 64-hex before-digest
lived only in that pass's ephemeral scratch and is not recoverable post-hoc (`git show HEAD:` does not help — these
`docs/` files are untracked). The durable, re-verifiable artefacts are the full **after** digest and the **normalised**
digest: recompute `sha256(PATH_RE.sub("<P>", open(f).read()))` and it must equal the recorded value — and that value is,
by construction, the same for the pre-edit text, which is exactly what the check asserted at edit time.

## Ten substitutions, verbatim

Quoted as a correction diff: a `-` line inside a `diff` fence is the token that was **replaced** and is not
a live reference (`path_refs.py:177-181`), so the corpus's own scanner reads these as history, not as citations.
```diff
- docs/CAPGATE-FOREIGN-RED.md:7  `tests/test_cap_gate.py` -> `experiments/ptr-engine/longrun/tests/test_cap_gate.py`
- docs/CAPGATE-FOREIGN-RED.md:49  `tests/test_row_attribution.py` -> `experiments/ptr-engine/longrun/tests/test_row_attribution.py`
- docs/COLD-START-PROBE.md:74  `tests/test_verdict_ritual.py` -> `experiments/ptr-engine/longrun/tests/test_verdict_ritual.py`
- docs/DECIDABILITY-SEAM.md:114  `docs/GRADER-FITNESS.md` -> `experiments/ptr-engine/measure/GRADER-FITNESS.md`
- docs/EXIT-CODES.md:80  `tests/test_exit_codes.py` -> `experiments/ptr-engine/longrun/tests/test_exit_codes.py`
- docs/EXTERNAL-EVAL-PRACTICE.md:382  `tests/test_scope.py` -> `experiments/ptr-engine/tests/test_scope.py`
- docs/EXTERNAL_WORKSPACE_POINTER_PROTOCOL.md:65  `orchestration/units/orchestration/cursors/r2-opt-sim.json` -> `orchestration/cursors/r2-opt-sim.json`
- docs/FROZEN-TREE.md:91  `tests/test_handoff_lint.py` -> `experiments/ptr-engine/longrun/tests/test_handoff_lint.py`
- docs/GATE-CHAIN.md:557  `tests/test_cap_gate.py` -> `experiments/ptr-engine/longrun/tests/test_cap_gate.py`
- docs/GATE-CHAIN.md:103  `tests/test_guards.py` -> `experiments/ptr-engine/longrun/tests/test_guards.py`
```

## Guard still bites (red→green)

Shrunk baseline copied into a `/tmp` tree: a clean document → `--check` exit **0**; the deliberate bad citation appended
→ exit **1** (`NEW docs/EXIT-CODES.md:2 wrong_dir`, the bad token `tests/test_exit_codes.py` for example, `->
experiments/ptr-engine/longrun/tests/test_exit_codes.py`; `0 known (baselined), 1 new`); citation removed → exit **0**.

## Residual, by reason

`wrong_dir` remaining **645** = in-scope ambiguous **130** (`docs/**/*.md` 20 · `orchestration/**/*.md` 110 — each with
≥2 same-basename candidates, so choosing is a human judgement, not a substitution) + out-of-scope
`orchestration/handoffs/*.json` **464** · `experiments/ptr-engine/measure/*` **51**.
`missing` remaining **266** (`docs/**/*.md` 33 · `orchestration/**/*.md` 53 · `orchestration/handoffs/*.json` 162 ·
`measure/*` 22) — none is this card's: a `missing` citation needs a decision about what was meant, and creating the file
it names is how a phantom becomes a lie (`path_refs.py:21-23`).

## DEVIATION 1 — the card's baseline path cannot work

The card named `experiments/ptr-engine/measure/path-refs-baseline.json` for the baseline; that file does not exist
and must not, because that directory is inside the scanner's own `SCAN_GLOBS`
(`experiments/ptr-engine/measure/*.json`, `path_refs.py:54-60`). A baseline written there is scanned as a document and
its anchors become citations: measured **717 new** keys and `--check` exit **1** (`NEW
…/path-refs-baseline.json:651 missing`, a path that does not exist, `state/logs/U8.15/unit_shape_baseline.json`). That file was deleted; the shrunk
baseline went to the tool's own default, `state/logs/path-refs-baseline.json` (`path_refs.py:84`), where `--check` reads
it with no argument. That path is **not** in the card's write list — it is the only placement that satisfies the card's
own "`--check` exit 0 required". The shrink is attributable: `frozen_by` now reads `PATH-REFS-BATCH-FIX`,
`prior_frozen_by` `PHANTOM-PATH-FIX`, plus a `shrink_note` stating that an absent key was repaired, not excused.

## What a reader needs

**95.20 % of the 1,957 citations in `docs/**/*.md` now resolve to a file that exists** (1,863 `ok`; 20 `wrong_dir`,
33 `missing`, 41 `ignored`). Excluding the 41 lines that say a path is absent, 97.24 % resolve.
