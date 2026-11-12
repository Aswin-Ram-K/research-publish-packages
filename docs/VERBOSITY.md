# VERBOSITY — does the grow arm's longer answer explain the TTFT gap?

_Generated offline by `experiments/ptr-engine/longrun/tests/test_verbosity.py` (sha256 `9f6aa0e984b6595d`) at 2026-11-12T00:43:27Z from 119 rows files. Zero inference requests._

**Verdict: `confound_immaterial`.** holding completion length equal leaves 86.7% of the TTFT gap in which arm a (pointer-stable) is 0.37x the first-token latency of arm b (transcript-grow), i.e. b is 2.67x slower; the fitted b_completion is +0.0720 per ln-token and completion length differs 0.19x between the arms, so verbosity covers only 13.3% of it

Scope: p95 TTFT is refused corpus-wide at arm level (no cell reaches n>=60), so this verdict is stated on the median/mean TTFT gap plus the log-log decomposition; p90 is the reported tail.

## 1. Corpus (pinned)

| rows file | rows | completed turns | sha256 |
|---|---|---|---|
| `rows-abs2-2026-11-09.jsonl` | 242 | 198 | `20bcd6c34b4aef825bc47a6b18e357ca0a13ed0e4b2cdcf5e436d481a1fbdba8` |
| `rows-agentic-compact-20261112T003017Z.jsonl` | 129 | 0 | `89842ea9ddd23da2811dbc84fe3ddd5dca6afd0f1a9ad28f50163420d960b249` |
| `rows-agentic-masking-no-fetch-20261112T000932Z.jsonl` | 128 | 0 | `71124799d4cdcf32abb793331e973e062b9b0e41f7182d0faa9ddf99bf0a5732` |
| `rows-agentic-none-20261112T000204Z.jsonl` | 72 | 0 | `3000b78b986b4fc817f22992d2be23b785a27af635259dc5a26dc602b7fc9cb3` |
| `rows-agentic-none-20261112T000932Z.jsonl` | 128 | 0 | `52f3a13cf50420a4fbd9b577d19eebe4b055f6d1d31117b0242fbab39ace942b` |
| `rows-agentic-none-20261112T002154Z.jsonl` | 128 | 0 | `87d3c7b73139894fa9432299d0f55b57e89d68e2db83532e0cc6d024ab63a4fe` |
| `rows-agentic-pinned-20261112T000932Z.jsonl` | 59 | 0 | `3fe1e3d7c65bc23f3d47e03d3bd92e92cd5f2b9f21335a1de7dcad8376f6687d` |
| `rows-agentic-pinned-20261112T002154Z.jsonl` | 28 | 0 | `d5952b5037c254f3ae22cc65a3e2f5bbf2b46d3d402f09bd436128c4e4715d37` |
| `rows-agentic-pinned-20261112T003017Z.jsonl` | 128 | 0 | `62825502973547a256f504c0fcdb910807b5488cc06d67e6a6e3c9de49395fc2` |
| `rows-agg-8014.jsonl` | 141 | 99 | `e5ec0b61bcac3e3ae232e415436fd2cd9567143dffde5f9755b3749b493ed355` |
| `rows-agg-fetch-mt36.jsonl` | 41 | 34 | `0066da598801d9a1d8686f8c9953b8081aaa5dab0caec9fb763aad9bde4b5fe2` |
| `rows-agg-fetch-mt50.jsonl` | 54 | 41 | `baca066374f4b2110ff8d93be8b87529249d0dbfd4075963757604dc7daab3a9` |
| `rows-agg-fetch-r1.jsonl` | 10 | 8 | `8ebdacbed7e87477fc83b069ac291cd3565b6603758fabbe056b22927e892e68` |
| `rows-agg-fetch-test.jsonl` | 36 | 30 | `ac77a1a496ad9c9014aff143a03827377a8a86ee7b4c477e2bda5e89b2941707` |
| `rows-agg-fetch-test2.jsonl` | 37 | 29 | `eb6d1dc6fa95496584893da6a4c63849b46d9f572a32482e50990602562be7f6` |
| `rows-agg-masking-r1.jsonl` | 100 | 100 | `07a35c4df79ee2da32207b33a1e3041afd29b7769fede8d565e19b99be2b7e4d` |
| `rows-agg2-2026-11-09.jsonl` | 242 | 209 | `3d3bbb379915057515df06e4115bf8509d294a3d9b2f3afeb6313efbdb64c2ea` |
| `rows-agg3-instructed.jsonl` | 122 | 94 | `ecb48ddec660295279a398857a91d2856a32c439a43bba243db67bf545a1d074` |
| `rows-baseline-2026-10-26.jsonl` | 105 | 84 | `638c84942e3bcdba4b416cceda9214f3fdcc99c42171639bf5c52736f40e032d` |
| `rows-cell-bounded-context-fetch-20261111T231050Z.jsonl` | 101 | 100 | `227aa34901a2bf3317a837a5606e4cdf0261b9dac03cd2754bd52f3f21a3e358` |
| `rows-cell-bounded-context-fetch-20261111T231625Z.jsonl` | 119 | 99 | `3487db7d486f4fc713821724b3135fbd83a1dde39821848f5c1cf6d8ec37f152` |
| `rows-cell-lease-reopen-20261027T004219Z.jsonl` | 7 | 0 | `7d49862313b01b7ef7db5b9d86e4bc921678d0ec05985e528d603ef7e59a7f64` |
| `rows-cell-lease-reopen-20261027T024223Z.jsonl` | 30 | 10 | `6bf8cf9ba751d0892ce595fc2a1d4845b741575b014e2a37cc9fa62cfb8a16aa` |
| `rows-cell-lease-reopen-20261027T084049Z.jsonl` | 56 | 12 | `e58c21f8366695915211d801cd7b9c6c475d923552080abba651843307aabb7e` |
| `rows-cell-lease-reopen-20261028T032823Z.jsonl` | 91 | 34 | `8b7774afc9ce19bb0fe0bfda98f5a0e83802505d42e18242130a9a57453de822` |
| `rows-cell-lease-reopen-20261028T033139Z.jsonl` | 96 | 27 | `1efd44659c68dc709702ca589d9ba7510e7950a6f627a659d39f52841b77c54f` |
| `rows-cell-masking-no-fetch-20261111T230833Z.jsonl` | 100 | 100 | `89ff9911dc673c29ff446e0e5b5dce5b6d424e742851776badf7c918239785dc` |
| `rows-cell-masking-no-fetch-20261111T231412Z.jsonl` | 100 | 100 | `34d7d45e00b248fb7c030728197f40675b8e3cb5c72d7f5bfad93c97146ae3f9` |
| `rows-cell-pinned-20261111T230953Z.jsonl` | 100 | 100 | `3ebe23ac936d5288615bbcbbf09bb2a07a8cfe983e09feeeb763a4199053ae41` |
| `rows-cell-pinned-20261111T231541Z.jsonl` | 100 | 100 | `1229680906db4c1326f60995262f2ad10349d9ea9a09f6b6a5253eb8f7eae81f` |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | 6 | 5 | `5ac9dd992f5d8715696925f56c225024e172cb98b4b9a937a0ee63bd099e9800` |
| `rows-cell-pointer-stable-20261026T182535Z.jsonl` | 27 | 25 | `46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1` |
| `rows-cell-pointer-stable-20261026T202040Z.jsonl` | 12 | 11 | `26b7f43fa3092447e4b9e88f72b035ffec39201d6c3e07bd7b1eb8206b1fa76c` |
| `rows-cell-pointer-stable-20261026T204258Z.jsonl` | 12 | 12 | `52a983eb9e36ed6cbbc21776890e30fc174a92f83f32247bfb2ca5c34365644e` |
| `rows-cell-pointer-stable-20261027T004027Z.jsonl` | 25 | 10 | `c1962d864cac9698a58f4805d81e0902087ae9f6e182fe5b9691830eec5ee05c` |
| `rows-cell-pointer-stable-20261028T024509Z.jsonl` | 96 | 37 | `7164c871de24a41c8ed189d64e89721ba4192a971f497a05ac84c9f806f4ba6d` |
| `rows-cell-pointer-stable-20261028T024942Z.jsonl` | 93 | 34 | `6d006f4bff9ed77290604ae2e849d4d87841f299fc246746d3f136a9e66f7be7` |
| `rows-cell-pointer-stable-20261028T025312Z.jsonl` | 94 | 38 | `bcbd294d6b69342746fb354b73126ef5713ba3726c3be4ac6d99b9295d150ac0` |
| `rows-cell-pointer-stable-20261028T025853Z.jsonl` | 93 | 39 | `9a9caf34c4c1ee00c9343803a135b690f9001c1fed6b4f38fd53f40b0db4c00b` |
| `rows-cell-pointer-stable-20261028T030232Z.jsonl` | 94 | 38 | `e01c94ae7fcddb145d9268dcdc08b3dbd888737ff92c147131018eebae57bf51` |
| `rows-cell-pointer-stable-20261028T030559Z.jsonl` | 89 | 38 | `a94fd3fbf81040f11101eb9d38b148b6659d7455068e69327d4b7c332c0b60ec` |
| `rows-cell-spcc-20261111T230914Z.jsonl` | 100 | 100 | `7a67a5b86e7f6939091a7444e4939171f0030bba8cc096eb713f692bb2528301` |
| `rows-cell-spcc-20261111T231458Z.jsonl` | 100 | 100 | `cc75c9226a0f4dacc28f6c6941eb2b8ee6a909b73b9a1e6653d7d9b55a63a88c` |
| `rows-cell-transcript-compact-20261026T203733Z.jsonl` | 12 | 12 | `df877fba7283c4617e4e94ce3070bed93782b4882fd59dd65d89b8ecefc95175` |
| `rows-cell-transcript-compact-20261027T004155Z.jsonl` | 14 | 12 | `cbabecfcdcbb21231161fc098252e626d56136482c6c46f615254badbf35aad0` |
| `rows-cell-transcript-compact-20261028T032235Z.jsonl` | 66 | 40 | `151299d09b2d8f3fae6891b32a13e025cae6ad7cc9760d2d303d378b67f373f1` |
| `rows-cell-transcript-compact-20261028T032430Z.jsonl` | 81 | 43 | `16ef4dbc13b1e341f30d9307ea304712ba450b617b6339b67f420bc80cabc8d7` |
| `rows-cell-transcript-grow-20261026T202444Z.jsonl` | 12 | 7 | `6f86c9c962f4653c833442627bb5467d9fbc5ac758172891db0d82f990399e35` |
| `rows-cell-transcript-grow-20261027T004129Z.jsonl` | 13 | 11 | `1a5301971a1b72b4676dde2665dd020f8e10141bbdedc83e528063cc98c57130` |
| `rows-cell-transcript-grow-20261028T030925Z.jsonl` | 77 | 36 | `cf606122235e1f1b96fbde81584b7949ba69da053d25c6cde236375311444d02` |
| `rows-cell-transcript-grow-20261028T031218Z.jsonl` | 53 | 37 | `430da1e6c8bf8071c62b3e590045d8320c0f8c0168d9b0dc1ffe279db49ca52b` |
| `rows-cell-transcript-grow-20261028T031401Z.jsonl` | 56 | 39 | `94b98c4113fc7920c2e6c356d548a8af0e52c7594dbcd1aa5a93afd38394b69b` |
| `rows-cell-transcript-grow-20261028T031606Z.jsonl` | 56 | 43 | `116983aa31b40cdd2b255cf719027fc978ab53faf0481e68785ff9fd2541b994` |
| `rows-cell-transcript-grow-20261028T031753Z.jsonl` | 82 | 40 | `457ac0148766215d9b00333ef180fc06a36568dca7825e2231f420ef62486dcb` |
| `rows-cell-transcript-grow-20261028T032058Z.jsonl` | 53 | 33 | `6d2cd6088683463a6979940651875f566d304eecaed06beac8d4c535fb554e88` |
| `rows-compliance-diag-2026-11-08.jsonl` | 3 | 0 | `c89dece49389c7903f584b396c59279374c6b2b6071525f34ef4832bbc3f65bd` |
| `rows-contrast24-tx01-20261109.jsonl` | 51 | 48 | `e74d1edee409eb55b4b0b06b8625bfd082f30139203a3612ddb121b4899cd4ed` |
| `rows-control-nomask-tx01-20261109.jsonl` | 48 | 48 | `96a66ea4646ee136a968ddff0700efc4ef7ad3c840e0f7ed75774147aa6856f5` |
| `rows-e1-final-2026-11-10.jsonl` | 300 | 300 | `0c50aa25acdaf380e12590a65c0e1ccb6ccb021e3af21bf305bec97d0629e8bd` |
| `rows-e1-indexfix-2026-11-10.jsonl` | 343 | 300 | `c76173b156c7cc751d3bf2def0dd71554b8bce66c67b5254112e98d9ff62c3a0` |
| `rows-e1-parserfix-2026-11-10.jsonl` | 325 | 287 | `53377e69f5c027a6e4c58e04037bb9a0d57fa122371b1ccff69711399d02348e` |
| `rows-e1-spcc-2026-11-10.jsonl` | 100 | 100 | `65febf07d8561bd6adc0c97015b4e07a302387a5ff5a10ce574170d0c1762216` |
| `rows-e1-tools-2026-11-10.jsonl` | 318 | 289 | `691b72ed6e06f4065268d026f2b7b02fbc6e480714d45324c89da7f3d4c3d056` |
| `rows-e2-compact-2026-11-10.jsonl` | 300 | 300 | `9e27d730252c5f4ff4308d5d5dd2befd848575c8ec05e5f4b679f1e613634faf` |
| `rows-e2-turnover-2026-11-10.jsonl` | 300 | 300 | `ca9fb1cb6a1ae39de275df1a23e85e51a8f00ef2c57f7c842dcc9201c54837cf` |
| `rows-e3-retain-2026-11-10.jsonl` | 200 | 200 | `8870d1f5624ce2dd88967f3f8648edb385ededf4cfd96faed941a6cdb2612108` |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | 61 | `c01c7b4a477fe24bc55370ceddf26d885a1fe827e7135023cdde48b271e8c934` |
| `rows-fetchall-c-20261109.jsonl` | 48 | 48 | `eed2a44094bb683bc1ebf94b472c19d167f37070f4079cc10db7ba575be0a225` |
| `rows-fetchall-d-20261109.jsonl` | 53 | 48 | `885ee23678f29d252b9498564e80d8b53850f92eeb28caa181528f21138825be` |
| `rows-fetchinstruct-probe.jsonl` | 5 | 5 | `3132a134dc6b638964c14ad17bd3463b37b47bafae817db4885819466fa5977d` |
| `rows-fetchmandate-20261109.jsonl` | 10 | 10 | `edbc9dd9b78845b002e27d72f1dc71eb2505a90d64692bc9d38e9348b474247a` |
| `rows-hop-2026-11-09.jsonl` | 450 | 348 | `603f59458b086bf1a55eb2d1b0eab5e0e0e12f129dacab9f53c6af32f2bcd5ce` |
| `rows-hop-8014-r2.jsonl` | 191 | 178 | `b0ea03d3eb1b2f9bba0e796266d80fb6ee561532ce0bb0f9ce81e748fee23463` |
| `rows-hop-8014-r3.jsonl` | 247 | 221 | `933feb0f3e6573efa3be3b18744e8390c69e5f6f001ea9fbdadee022d2b3bf55` |
| `rows-hop-8014.jsonl` | 195 | 176 | `bffdd8cc6f0b7d066e40649c5be04e213238555293dfe3231b9bb0560ccd5e58` |
| `rows-hop2-fetch.jsonl` | 208 | 173 | `4ecb5182862c05dc34aa27ccfe15f2228e535706da8931ab77d9ed9942a9fbe5` |
| `rows-hop2-masking.jsonl` | 180 | 180 | `c23b252ddd9a979511f174d310b7ec0d757382c89109223a6c3c13150f8587ab` |
| `rows-hop3-instructed.jsonl` | 197 | 176 | `d396f03698d62994b4b793de62deab81a6efe80e855b57ceb73a19198d2bc4ae` |
| `rows-live-2026-10-26.jsonl` | 27 | 0 | `3d02b4d473304f0012b34024cc517c70d7f23b60de1103c1ca1b93a7e2752e5b` |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | 24 | `9d4ad90ce34cb781c04e9f73fba50ffb47d5b35d6d1491389d22a49044516405` |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | 23 | `9b1097234bf8d2464a4d24ec48cf0cccc1ecd64bd853815fc6643b1ad3da3368` |
| `rows-longrun-2026-10-26.jsonl` | 192 | 93 | `bc61d38192d4e4316021ec8d3d0e21dcb8e6153f463260a0138da21969d0b21e` |
| `rows-longrun-CELLTX01.jsonl` | 111 | 95 | `f2652fcccfc8fb1d146d0c06518bb71e230d53a19f78c7b5f5d1d734bd2a83ef` |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | 177 | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | 95 | `80d85fe0e977af164a5ffeca8b2f95350c6614d2112455c3ace93765530ff921` |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | 88 | `999f298dac8b83569c4059946e7789b76ec485b24a5c9a39d6c1616f0501c28e` |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | 47 | `f11391aa2989949f904b8092074cb7b85b65dfe5b8c89431930fe921b28de77f` |
| `rows-longrun-v5-tools.jsonl` | 72 | 47 | `586b66f27939bd05e09d8b48dad745a5fa268c3f31103695746df3e3f8443cb5` |
| `rows-longrun-v6-tools.jsonl` | 72 | 48 | `1e78d75f259afbe0406643825941a65b4773b4342b847698005ad5908b3e531e` |
| `rows-pilot-thinking-2026-10-26.jsonl` | 6 | 5 | `6b81a6281ce0b266f45ab1b95fc3834e446bea5708e5466988b28e133a0e9e10` |
| `rows-posctrl-2026-11-08.jsonl` | 48 | 48 | `b9a058e64fe0d60cb8f00172fb3b1fe2295b8bd6ee869c4396427f21cb239a36` |
| `rows-rep2-bounded-context-fetch-maskon-tx01-20261109.jsonl` | 109 | 96 | `025189d94e0f4859137964d5c44f3c23cb29def68b32ea85ff60e766f7b99ba4` |
| `rows-rep2-masking-no-fetch-maskoff-tx01-20261109.jsonl` | 48 | 48 | `ef00c872abf91f6d9c05f0094b1c7c8fee5f46b3b2fa131d6b5043e2a5a001a0` |
| `rows-rep2-masking-no-fetch-maskon-tx01-20261109.jsonl` | 48 | 48 | `21eccf524f6afaaadbffb310b2b70ba71b9968df1550a2560eb6ac46eee3f611` |
| `rows-smoke-spcc-2026-11-10.jsonl` | 6 | 6 | `248a95f8af381cfb956183ec40b54b57993505561e1ef1f3a96ed9786ef74efe` |
| `rows-smoke-spcc2-2026-11-10.jsonl` | 6 | 6 | `d4457a9d9e0335b51fe6b730dd78590f58d8eee9df2495a81c68e84da211d328` |
| `rows-smoke-tx01-20261109.jsonl` | 16 | 9 | `921b0232509f131797e086db5c4cd6775ac7ee29b1a67ba1bd1d6e857409216c` |
| `rows-smoke2-tx01-20261109.jsonl` | 10 | 10 | `fc45132c77d3d9e06ae1cccff20084c6df4cd60dbbcc2c874a4c969c00c4e10f` |
| `rows-spcc-billedproof-2026-11-10.jsonl` | 100 | 100 | `26ab72817c64f4310cb14e98051aaa2a64fd4712c8805fe93454d300105444d7` |
| `rows-stack8014-bounded-context-fetch-tx01-20261109.jsonl` | 1 | 0 | `67e6e53722861e741a4d738f89750138901e79e5da304c7461d523a3d8060b3e` |
| `rows-stack8014-masking-no-fetch-maskoff-tx01-20261109.jsonl` | 48 | 48 | `3f16ad811ad5345cbd5863937844b40bf86df2d5c8dea3e9fec93d12769dbc0b` |
| `rows-stack8014-masking-no-fetch-maskon-tx01-20261109.jsonl` | 48 | 48 | `faf6984de181caba78bc92bce2b4275e7051434f13d44f3e34829c90d641f9e7` |
| `rows-sup-2026-11-09.jsonl` | 269 | 203 | `f0a519d6525a2fc7d5eb7c4b42a16e5bd36333f1375e46b552c0d1ee71e80d7a` |
| `rows-sup2-fetch.jsonl` | 145 | 90 | `8ed12d3ae412cad33ff935ee28d3727053ea83975e2705401eb756073a02222d` |
| `rows-sup2-masking.jsonl` | 103 | 103 | `72ee581dc237da39ea33798c845298ddd1eacbbcc9911c1bff4d419e506fdfe7` |
| `rows-toolcallfix-d-20261109T064028Z.jsonl` | 27 | 24 | `677b1e5e426a84d07b36c320b243d2621782215c7eef421ac7fbd0794eafd203` |
| `rows-tx01-real-20261109.jsonl` | 10 | 10 | `c05e51b879fa23e53e5dd0258ede289bd066c690ec86f2eaa169cc84de438dc2` |
| `rows-tx02-fetch-r1.jsonl` | 110 | 87 | `065db80c2fc3b75af0154ce2c7e9855047f718092349fd62e274d60db8245755` |
| `rows-tx02-fetch-r2.jsonl` | 114 | 88 | `43f5d56160cdaf1ba32f907876b95cbe88bc7aad42fcfe99624ec6137f610618` |
| `rows-tx02-masking-r1.jsonl` | 88 | 88 | `8579154ca451a17739b2d7265b8544f8516016e50faa095ab2530fce3381e2e6` |
| `rows-tx02-masking-r2.jsonl` | 88 | 88 | `d2fd0dd2ad70fe9bbcfd8bf36ae2bb77851feafb9ea2eefe649166f438f9da57` |
| `rows-tx03-8014-fetch-r1.jsonl` | 148 | 100 | `af546fbf5c584f2205bf248c8c4e05b8e0a87c9b625ec5413c9f330a2c885a91` |
| `rows-tx03-8014-masking-r1.jsonl` | 100 | 100 | `b50dd265637563838c5e18b486d1712b668aaadf21ca4df4f62d318d4cb8fb11` |
| `rows-tx03-fetch-r1.jsonl` | 105 | 89 | `7c188e971b0d7567ac6ceeedb6f20ea9487c015ede80d19c34937d8d3885af02` |
| `rows-tx03-fetch-r2.jsonl` | 101 | 87 | `f00a71eb6bc6d8e15f38e3211317b3870ddf156bcef55167599992dbffbf4fd7` |
| `rows-tx03-fetchfix-r1.jsonl` | 138 | 99 | `d673b2aad76f528f24a03a1a06a324c6d0af4cdb355eab23893cc2a08f12fb4a` |
| `rows-tx03-fetchfix-r2.jsonl` | 134 | 100 | `1f1f68212406aebdcb587942b827ef92b1160ac9b4d1af33e069e8428517ca4d` |
| `rows-tx03-masking-r1.jsonl` | 100 | 100 | `014c3dcbbee0950a78eb280905052b90f767317db27eaed67940b1bf3014a448` |
| `rows-tx03-masking-r2.jsonl` | 100 | 100 | `924985598bd0a9128e93d451acc07cfda71d4685d834f66df8fea1d0ec347793` |

## 2. Per-arm distributions, grouped by file (n in every row)

| file | arm | n | completion tok mean / med / p90 / max | answer chars mean / med / p90 | tok/char | prompt tok med / p90 | TTFT ms mean / med / p90 | TTFT p95 |
|---|---|---|---|---|---|---|---|---|
| `rows-abs2-2026-11-09.jsonl` | bounded-context-fetch | 98 | 7.7 / 5.0 / 11.0 / 11.0 | 14.3 / 12.0 / 17.0 | 0.5397 | 2604.5 / 3596.1 | 175.8 / 169.4 / 232.1 | 239.9 |
| `rows-abs2-2026-11-09.jsonl` | masking-no-fetch | 100 | 5.8 / 5.0 / 11.0 / 11.0 | 12.7 / 12.0 / 17.0 | 0.4598 | 1877.5 / 3065.9 | 185.1 / 174.7 / 196.1 | 200.4 |
| `rows-agg-8014.jsonl` | bounded-context-fetch | 99 | 37.0 / 12.0 / 20.0 / 2309.0 | 103.9 / 18.0 / 50.0 | 0.3556 | 3681.0 / 4800.8 | 163.6 / 136.6 / 279.2 | 308.4 |
| `rows-agg-fetch-mt36.jsonl` | bounded-context-fetch | 34 | 9.5 / 11.0 / 12.0 / 12.0 | 15.8 / 17.0 / 18.0 | 0.6034 | 1651.0 / 2460.4 | 171.1 / 172.6 / 228.6 | refused (n=34<60) |
| `rows-agg-fetch-mt50.jsonl` | bounded-context-fetch | 41 | 9.3 / 11.0 / 12.0 / 12.0 | 15.6 / 17.0 / 18.0 | 0.5962 | 1881.0 / 2973.0 | 221.2 / 229.0 / 274.2 | refused (n=41<60) |
| `rows-agg-fetch-r1.jsonl` | bounded-context-fetch | 8 | 9.5 / 9.0 / 11.0 / 11.0 | 38.8 / 46.0 / 46.0 | 0.2452 | 871.5 / 1354.1 | 138.2 / 133.4 / 189.5 | refused (n=8<60) |
| `rows-agg-fetch-test.jsonl` | bounded-context-fetch | 30 | 13.7 / 12.0 / 23.0 / 23.0 | 23.5 / 18.0 / 43.0 | 0.5822 | 1573.5 / 2533.9 | 223.8 / 222.3 / 263.1 | refused (n=30<60) |
| `rows-agg-fetch-test2.jsonl` | bounded-context-fetch | 29 | 8.9 / 11.0 / 11.0 / 12.0 | 15.4 / 17.0 / 17.2 | 0.5762 | 1542.0 / 2453.4 | 170.2 / 158.0 / 225.3 | refused (n=29<60) |
| `rows-agg-masking-r1.jsonl` | masking-no-fetch | 100 | 7.3 / 5.0 / 12.0 / 12.0 | 13.9 / 12.0 / 18.0 | 0.5233 | 2756.5 / 3710.5 | 181.3 / 175.5 / 250.5 | 264.3 |
| `rows-agg2-2026-11-09.jsonl` | bounded-context-fetch | 109 | 34.5 / 11.0 / 133.6 / 353.0 | 64.7 / 17.0 / 240.8 | 0.5324 | 3449.0 / 5866.4 | 235.1 / 219.8 / 313.9 | 397.7 |
| `rows-agg2-2026-11-09.jsonl` | masking-no-fetch | 100 | 7.1 / 5.0 / 11.1 / 12.0 | 13.8 / 12.0 / 17.1 | 0.5174 | 2769.0 / 3734.5 | 170.0 / 171.1 / 226.0 | 232.8 |
| `rows-agg3-instructed.jsonl` | bounded-context-fetch | 94 | 41.1 / 5.0 / 12.0 / 1018.0 | 96.2 / 12.0 / 18.0 | 0.4275 | 3301.5 / 4781.5 | 188.5 / 182.8 / 249.3 | 269.3 |
| `rows-baseline-2026-10-26.jsonl` | C | 24 | 225.7 / 300.0 / 300.0 / 300.0 | 150.8 / 200.0 / 200.0 | 1.4970 | 2059.0 / 2637.0 | — | — (no TTFT field) |
| `rows-baseline-2026-10-26.jsonl` | C0 | 24 | 236.1 / 300.0 / 300.0 / 300.0 | 175.4 / 200.0 / 200.0 | 1.3464 | 5131.0 / 6571.0 | — | — (no TTFT field) |
| `rows-baseline-2026-10-26.jsonl` | R | 36 | 46.7 / 5.5 / 197.0 / 300.0 | 38.1 / 12.0 / 126.0 | 1.2261 | 4317.5 / 6429.0 | — | — (no TTFT field) |
| `rows-cell-bounded-context-fetch-20261111T231050Z.jsonl` | bounded-context-fetch | 100 | 10.2 / 5.0 / 5.0 / 474.0 | 18.1 / 12.0 / 12.0 | 0.5651 | 3387.0 / 5217.1 | 236.7 / 232.1 / 276.9 | 294.5 |
| `rows-cell-bounded-context-fetch-20261111T231625Z.jsonl` | bounded-context-fetch | 99 | 50.9 / 5.0 / 10.0 / 1398.0 | 142.5 / 12.0 / 16.0 | 0.3574 | 4047.0 / 5453.8 | 240.1 / 226.0 / 290.3 | 364.7 |
| `rows-cell-lease-reopen-20261027T024223Z.jsonl` | lease-reopen | 10 | 49.7 / 43.5 / 68.8 / 85.0 | 125.0 / 120.5 / 195.1 | 0.3976 | 1227.0 / 2360.9 | 125.7 / 126.1 / 147.0 | refused (n=10<60) |
| `rows-cell-lease-reopen-20261027T084049Z.jsonl` | lease-reopen | 12 | 47.8 / 27.0 / 78.7 / 201.0 | 121.2 / 64.5 / 265.5 | 0.3938 | 1224.0 / 1238.3 | 158.1 / 158.3 / 170.0 | refused (n=12<60) |
| `rows-cell-lease-reopen-20261028T032823Z.jsonl` | lease-reopen | 34 | 46.4 / 31.5 / 83.4 / 229.0 | 106.7 / 79.5 / 196.1 | 0.4348 | 1236.5 / 1378.8 | 132.7 / 112.7 / 135.0 | refused (n=34<60) |
| `rows-cell-lease-reopen-20261028T033139Z.jsonl` | lease-reopen | 27 | 67.7 / 50.0 / 132.0 / 317.0 | 158.4 / 108.0 / 193.6 | 0.4271 | 1268.0 / 2560.0 | 156.8 / 129.5 / 197.5 | refused (n=27<60) |
| `rows-cell-masking-no-fetch-20261111T230833Z.jsonl` | masking-no-fetch | 100 | 5.3 / 5.0 / 5.0 / 10.0 | 12.2 / 12.0 / 12.0 | 0.4330 | 3025.0 / 4782.1 | 207.9 / 207.8 / 229.3 | 233.1 |
| `rows-cell-masking-no-fetch-20261111T231412Z.jsonl` | masking-no-fetch | 100 | 5.4 / 5.0 / 5.0 / 19.0 | 12.6 / 12.0 / 12.0 | 0.4304 | 3102.0 / 4859.1 | 215.5 / 214.7 / 248.8 | 258.1 |
| `rows-cell-pinned-20261111T230953Z.jsonl` | pinned | 100 | 5.3 / 5.0 / 5.0 / 10.0 | 12.2 / 12.0 / 12.0 | 0.4327 | 2620.0 / 4006.3 | 202.6 / 196.7 / 230.9 | 240.6 |
| `rows-cell-pinned-20261111T231541Z.jsonl` | pinned | 100 | 7.5 / 5.0 / 5.0 / 228.0 | 13.6 / 12.0 / 12.0 | 0.5521 | 2682.5 / 3963.6 | 190.3 / 189.4 / 207.3 | 212.2 |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | pointer-stable | 5 | 4688.6 / 1415.0 / 10984.0 / 13126.0 | 366.4 / 152.0 / 781.2 | 12.7964 | 4312.0 / 4336.8 | 408.7 / 399.6 / 658.0 | refused (n=5<60) |
| `rows-cell-pointer-stable-20261026T182535Z.jsonl` | pointer-stable | 25 | 162.7 / 56.0 / 481.2 / 718.0 | 600.6 / 248.0 / 1773.0 | 0.2708 | 4863.0 / 5006.2 | 195.8 / 141.6 / 206.0 | refused (n=25<60) |
| `rows-cell-pointer-stable-20261026T202040Z.jsonl` | pointer-stable | 11 | 410.6 / 205.0 / 607.0 / 2386.0 | 1449.4 / 807.0 / 1856.0 | 0.2833 | 4864.0 / 4999.0 | 149.3 / 141.9 / 175.4 | refused (n=11<60) |
| `rows-cell-pointer-stable-20261026T204258Z.jsonl` | pointer-stable | 12 | 119.8 / 73.5 / 353.7 / 462.0 | 387.6 / 237.0 / 1066.1 | 0.3090 | 4862.0 / 5005.4 | 151.5 / 138.8 / 168.2 | refused (n=12<60) |
| `rows-cell-pointer-stable-20261027T004027Z.jsonl` | pointer-stable | 10 | 63.8 / 58.5 / 90.9 / 189.0 | 99.3 / 61.5 / 190.2 | 0.6425 | 5286.0 / 5553.3 | 270.8 / 166.0 / 482.4 | refused (n=10<60) |
| `rows-cell-pointer-stable-20261028T024509Z.jsonl` | pointer-stable | 37 | 52.1 / 28.0 / 79.6 / 445.0 | 116.6 / 64.0 / 169.2 | 0.4468 | 5309.0 / 6344.2 | 181.4 / 152.5 / 288.2 | refused (n=37<60) |
| `rows-cell-pointer-stable-20261028T024942Z.jsonl` | pointer-stable | 34 | 51.1 / 38.5 / 103.4 / 229.0 | 91.8 / 58.5 / 135.4 | 0.5574 | 5299.5 / 5398.2 | 163.7 / 154.9 / 214.7 | refused (n=34<60) |
| `rows-cell-pointer-stable-20261028T025312Z.jsonl` | pointer-stable | 38 | 56.7 / 31.5 / 134.0 / 390.0 | 109.3 / 59.0 / 163.0 | 0.5188 | 5301.0 / 6390.3 | 381.5 / 159.8 / 312.0 | refused (n=38<60) |
| `rows-cell-pointer-stable-20261028T025853Z.jsonl` | pointer-stable | 39 | 47.4 / 28.0 / 85.6 / 261.0 | 97.4 / 60.0 / 188.0 | 0.4868 | 5296.0 / 6157.0 | 199.0 / 148.2 / 232.3 | refused (n=39<60) |
| `rows-cell-pointer-stable-20261028T030232Z.jsonl` | pointer-stable | 38 | 36.7 / 20.5 / 70.6 / 142.0 | 61.9 / 56.5 / 109.8 | 0.5927 | 5299.0 / 5980.4 | 190.6 / 149.9 / 237.4 | refused (n=38<60) |
| `rows-cell-pointer-stable-20261028T030559Z.jsonl` | pointer-stable | 38 | 51.0 / 27.5 / 122.6 / 289.0 | 112.9 / 74.0 / 198.6 | 0.4517 | 5304.0 / 6740.8 | 187.2 / 156.0 / 253.2 | refused (n=38<60) |
| `rows-cell-spcc-20261111T230914Z.jsonl` | spcc | 100 | 5.3 / 5.0 / 5.0 / 10.0 | 12.2 / 12.0 / 12.0 | 0.4330 | 2966.0 / 4737.0 | 189.9 / 189.2 / 211.8 | 223.5 |
| `rows-cell-spcc-20261111T231458Z.jsonl` | spcc | 100 | 5.3 / 5.0 / 5.0 / 10.0 | 12.2 / 12.0 / 12.0 | 0.4330 | 3094.0 / 4865.0 | 206.8 / 195.9 / 232.1 | 287.6 |
| `rows-cell-transcript-compact-20261026T203733Z.jsonl` | transcript-compact | 12 | 20.2 / 21.0 / 22.0 / 44.0 | 80.8 / 92.0 / 93.0 | 0.2497 | 5187.0 / 5398.0 | 142.5 / 141.9 / 168.0 | refused (n=12<60) |
| `rows-cell-transcript-compact-20261027T004155Z.jsonl` | transcript-compact | 12 | 50.9 / 64.5 / 69.0 / 69.0 | 50.6 / 42.0 / 55.0 | 1.0066 | 5556.0 / 5716.4 | 143.0 / 144.1 / 157.3 | refused (n=12<60) |
| `rows-cell-transcript-compact-20261028T032235Z.jsonl` | transcript-compact | 40 | 49.1 / 70.0 / 72.0 / 190.0 | 85.4 / 69.0 / 99.0 | 0.5746 | 6347.0 / 7731.0 | 158.2 / 157.8 / 180.7 | refused (n=40<60) |
| `rows-cell-transcript-compact-20261028T032430Z.jsonl` | transcript-compact | 43 | 76.4 / 73.0 / 124.0 / 383.0 | 163.6 / 94.0 / 117.0 | 0.4671 | 7773.0 / 8897.4 | 224.6 / 185.6 / 365.9 | refused (n=43<60) |
| `rows-cell-transcript-grow-20261026T202444Z.jsonl` | transcript-grow | 7 | 821.3 / 382.0 / 2124.4 / 3895.0 | 2942.1 / 1420.0 / 7448.6 | 0.2791 | 9650.0 / 11930.0 | 725.7 / 915.1 / 1154.5 | refused (n=7<60) |
| `rows-cell-transcript-grow-20261027T004129Z.jsonl` | transcript-grow | 11 | 57.1 / 72.0 / 72.0 / 72.0 | 70.9 / 78.0 / 78.0 | 0.8051 | 5607.0 / 5699.0 | 211.8 / 150.4 / 172.2 | refused (n=11<60) |
| `rows-cell-transcript-grow-20261028T030925Z.jsonl` | transcript-grow | 36 | 59.2 / 70.0 / 75.0 / 388.0 | 103.6 / 69.0 / 100.0 | 0.5718 | 7140.5 / 8054.0 | 207.8 / 163.4 / 230.3 | refused (n=36<60) |
| `rows-cell-transcript-grow-20261028T031218Z.jsonl` | transcript-grow | 37 | 60.4 / 72.0 / 75.0 / 95.0 | 76.7 / 71.0 / 96.0 | 0.7868 | 6379.0 / 7596.4 | 156.7 / 156.2 / 179.4 | refused (n=37<60) |
| `rows-cell-transcript-grow-20261028T031401Z.jsonl` | transcript-grow | 39 | 73.7 / 76.0 / 80.0 / 502.0 | 132.5 / 87.0 / 120.2 | 0.5563 | 7157.0 / 8368.8 | 169.1 / 161.0 / 200.0 | refused (n=39<60) |
| `rows-cell-transcript-grow-20261028T031606Z.jsonl` | transcript-grow | 43 | 57.1 / 70.0 / 72.0 / 318.0 | 92.1 / 69.0 / 81.0 | 0.6200 | 6362.0 / 7874.8 | 172.1 / 167.9 / 195.8 | refused (n=43<60) |
| `rows-cell-transcript-grow-20261028T031753Z.jsonl` | transcript-grow | 40 | 62.8 / 69.0 / 126.5 / 340.0 | 88.4 / 58.0 / 119.9 | 0.7100 | 6959.5 / 7912.4 | 173.4 / 162.8 / 192.6 | refused (n=40<60) |
| `rows-cell-transcript-grow-20261028T032058Z.jsonl` | transcript-grow | 33 | 48.8 / 70.0 / 72.0 / 92.0 | 74.4 / 69.0 / 81.0 | 0.6565 | 6252.0 / 7526.8 | 176.0 / 161.0 / 192.2 | refused (n=33<60) |
| `rows-contrast24-tx01-20261109.jsonl` | bounded-context-fetch | 24 | 10.5 / 11.0 / 11.0 / 18.0 | 30.4 / 30.0 / 30.0 | 0.3471 | 857.5 / 1342.9 | 103.0 / 104.3 / 117.1 | refused (n=24<60) |
| `rows-contrast24-tx01-20261109.jsonl` | masking-no-fetch | 24 | 5.0 / 5.0 / 5.0 / 5.0 | 12.0 / 12.0 / 12.0 | 0.4167 | 475.5 / 765.7 | 93.5 / 92.2 / 114.6 | refused (n=24<60) |
| `rows-control-nomask-tx01-20261109.jsonl` | masking-no-fetch | 48 | 5.8 / 5.0 / 9.0 / 9.0 | 13.4 / 12.0 / 17.0 | 0.4346 | 970.0 / 1459.8 | 130.8 / 112.9 / 209.3 | refused (n=48<60) |
| `rows-e1-final-2026-11-10.jsonl` | bounded-context-fetch | 100 | 10.8 / 5.0 / 18.0 / 18.0 | 24.2 / 12.0 / 40.0 | 0.4458 | 2279.5 / 3461.5 | 172.0 / 180.7 / 223.6 | 234.6 |
| `rows-e1-final-2026-11-10.jsonl` | masking-no-fetch | 100 | 5.9 / 5.0 / 5.5 / 52.0 | 13.1 / 12.0 / 12.4 | 0.4529 | 1765.0 / 2855.5 | 131.8 / 127.6 / 160.9 | 203.5 |
| `rows-e1-final-2026-11-10.jsonl` | spcc | 100 | 6.2 / 5.0 / 10.0 / 10.0 | 13.0 / 12.0 / 16.0 | 0.4804 | 935.5 / 1252.8 | 116.0 / 116.6 / 127.7 | 132.6 |
| `rows-e1-indexfix-2026-11-10.jsonl` | bounded-context-fetch | 100 | 7.6 / 10.0 / 10.0 / 10.0 | 14.1 / 16.0 / 16.0 | 0.5398 | 2745.5 / 3784.5 | 145.9 / 133.3 / 200.9 | 206.5 |
| `rows-e1-indexfix-2026-11-10.jsonl` | masking-no-fetch | 100 | 6.0 / 5.0 / 10.0 / 10.0 | 12.8 / 12.0 / 16.0 | 0.4663 | 2065.0 / 3155.5 | 134.2 / 133.6 / 157.5 | 159.9 |
| `rows-e1-indexfix-2026-11-10.jsonl` | spcc | 100 | 6.9 / 5.0 / 10.0 / 86.0 | 13.8 / 12.0 / 16.0 | 0.4957 | 1302.5 / 1619.8 | 124.4 / 124.0 / 139.6 | 149.6 |
| `rows-e1-parserfix-2026-11-10.jsonl` | bounded-context-fetch | 88 | 6.2 / 5.0 / 10.0 / 10.0 | 13.0 / 12.0 / 16.0 | 0.4808 | 2426.0 / 3304.3 | 145.2 / 131.0 / 194.2 | 198.4 |
| `rows-e1-parserfix-2026-11-10.jsonl` | masking-no-fetch | 100 | 5.4 / 5.0 / 5.0 / 10.0 | 12.3 / 12.0 / 12.0 | 0.4383 | 1765.0 / 2855.5 | 125.1 / 123.7 / 146.2 | 152.2 |
| `rows-e1-parserfix-2026-11-10.jsonl` | spcc | 99 | 10.8 / 5.0 / 10.0 / 467.0 | 13.9 / 12.0 / 16.0 | 0.7782 | 1289.0 / 1607.6 | 121.8 / 122.0 / 135.4 | 140.5 |
| `rows-e1-spcc-2026-11-10.jsonl` | spcc | 100 | 6.0 / 5.0 / 10.0 / 10.0 | 12.7 / 12.0 / 16.0 | 0.4720 | 935.5 / 1252.8 | 114.2 / 115.1 / 127.6 | 137.4 |
| `rows-e1-tools-2026-11-10.jsonl` | bounded-context-fetch | 89 | 6.7 / 5.0 / 10.0 / 18.0 | 13.6 / 12.0 / 16.0 | 0.4950 | 2278.0 / 3376.0 | 243.2 / 144.2 / 219.2 | 230.3 |
| `rows-e1-tools-2026-11-10.jsonl` | masking-no-fetch | 100 | 5.4 / 5.0 / 5.0 / 10.0 | 12.3 / 12.0 / 12.0 | 0.4383 | 1765.0 / 2855.5 | 123.1 / 122.9 / 142.6 | 148.7 |
| `rows-e1-tools-2026-11-10.jsonl` | spcc | 100 | 6.2 / 5.0 / 10.0 / 10.0 | 12.9 / 12.0 / 16.0 | 0.4756 | 1288.5 / 1605.8 | 123.0 / 122.9 / 134.8 | 147.2 |
| `rows-e2-compact-2026-11-10.jsonl` | spcc | 300 | 6.4 / 5.0 / 10.0 / 10.0 | 13.1 / 12.0 / 16.0 | 0.4881 | 945.5 / 1621.8 | 160.0 / 129.9 / 165.3 | 202.9 |
| `rows-e2-turnover-2026-11-10.jsonl` | spcc | 300 | 7.1 / 5.0 / 10.0 / 10.0 | 13.7 / 12.0 / 16.0 | 0.5212 | 1521.5 / 2650.7 | 137.4 / 129.0 / 198.0 | 216.5 |
| `rows-e3-retain-2026-11-10.jsonl` | masking-no-fetch | 100 | 7.5 / 10.0 / 10.0 / 10.0 | 14.0 / 16.0 / 16.0 | 0.5377 | 2483.0 / 3742.0 | 131.3 / 133.5 / 154.3 | 158.9 |
| `rows-e3-retain-2026-11-10.jsonl` | spcc | 100 | 7.4 / 5.0 / 10.0 / 10.0 | 13.9 / 12.0 / 16.0 | 0.5316 | 2119.5 / 3037.4 | 135.5 / 135.6 / 160.0 | 164.2 |
| `rows-equalinfo-2026-10-26.jsonl` | C0F | 15 | 4.0 / 2.0 / 7.0 / 7.0 | 4.4 / 2.0 / 8.0 | 0.9091 | 22575.0 / 22594.0 | 1004.9 / 183.8 / 3152.0 | refused (n=15<60) |
| `rows-equalinfo-2026-10-26.jsonl` | C0FT | 18 | 96.5 / 4.5 / 283.0 / 283.0 | 3.0 / 2.0 / 8.0 | 32.1667 | 22617.5 / 22700.0 | 3115.8 / 192.5 / 9130.2 | refused (n=18<60) |
| `rows-equalinfo-2026-10-26.jsonl` | R | 28 | 78.8 / 7.0 / 249.7 / 298.0 | 9.9 / 2.0 / 22.0 | 7.9675 | 2578.0 / 12937.6 | 2697.8 / 603.1 / 7722.1 | refused (n=28<60) |
| `rows-fetchall-c-20261109.jsonl` | masking-no-fetch | 48 | 5.0 / 5.0 / 5.0 / 5.0 | 12.0 / 12.0 / 12.0 | 0.4167 | 833.0 / 1294.0 | 89.8 / 90.8 / 119.4 | refused (n=48<60) |
| `rows-fetchall-d-20261109.jsonl` | bounded-context-fetch | 48 | 9.3 / 5.0 / 33.0 / 33.0 | 25.3 / 12.0 / 98.0 | 0.3693 | 1261.5 / 1851.0 | 104.6 / 104.3 / 150.2 | refused (n=48<60) |
| `rows-fetchinstruct-probe.jsonl` | bounded-context-fetch | 5 | 7.2 / 5.0 / 11.6 / 16.0 | 17.2 / 12.0 / 27.6 | 0.4186 | 798.0 / 1117.0 | 147.0 / 127.7 / 192.4 | refused (n=5<60) |
| `rows-fetchmandate-20261109.jsonl` | bounded-context-fetch | 5 | 6.0 / 5.0 / 8.0 / 10.0 | 15.4 / 12.0 / 22.2 | 0.3896 | 698.0 / 733.2 | 88.5 / 86.6 / 104.2 | refused (n=5<60) |
| `rows-fetchmandate-20261109.jsonl` | masking-no-fetch | 5 | 22.8 / 5.0 / 58.4 / 94.0 | 61.2 / 12.0 / 159.6 | 0.3725 | 455.0 / 490.2 | 94.4 / 107.2 / 111.3 | refused (n=5<60) |
| `rows-hop-2026-11-09.jsonl` | bounded-context-fetch | 168 | 30.8 / 5.0 / 109.0 / 433.0 | 70.1 / 12.0 / 250.0 | 0.4394 | 3500.5 / 6448.5 | 195.7 / 182.6 / 271.4 | 361.5 |
| `rows-hop-2026-11-09.jsonl` | masking-no-fetch | 180 | 5.8 / 5.0 / 11.0 / 11.0 | 12.6 / 12.0 / 17.0 | 0.4563 | 3102.5 / 5240.8 | 192.9 / 181.5 / 240.0 | 304.0 |
| `rows-hop-8014-r2.jsonl` | bounded-context-fetch | 178 | 19.1 / 5.0 / 16.0 / 884.0 | 48.0 / 12.0 / 39.0 | 0.3970 | 4326.5 / 7592.4 | 158.5 / 137.0 / 262.7 | 316.3 |
| `rows-hop-8014-r3.jsonl` | bounded-context-fetch | 221 | 15.7 / 5.0 / 11.0 / 1484.0 | 38.4 / 12.0 / 17.0 | 0.4079 | 7056.0 / 9729.0 | 239.5 / 217.8 / 337.7 | 376.3 |
| `rows-hop-8014.jsonl` | bounded-context-fetch | 176 | 23.5 / 5.0 / 16.0 / 2515.0 | 59.9 / 12.0 / 39.0 | 0.3919 | 6200.0 / 8387.0 | 161.4 / 142.1 / 267.5 | 295.7 |
| `rows-hop2-fetch.jsonl` | bounded-context-fetch | 173 | 7.7 / 5.0 / 16.0 / 103.0 | 17.3 / 12.0 / 38.0 | 0.4483 | 3547.0 / 5724.8 | 209.0 / 190.4 / 252.8 | 279.0 |
| `rows-hop2-masking.jsonl` | masking-no-fetch | 180 | 5.8 / 5.0 / 11.0 / 11.0 | 12.6 / 12.0 / 17.0 | 0.4563 | 3102.5 / 5240.8 | 174.9 / 173.3 / 206.4 | 215.3 |
| `rows-hop3-instructed.jsonl` | bounded-context-fetch | 176 | 7.0 / 5.0 / 16.0 / 26.0 | 15.9 / 12.0 / 38.0 | 0.4378 | 3634.5 / 5775.0 | 163.0 / 145.2 / 211.7 | 227.3 |
| `rows-longrun-2026-10-26-fix.jsonl` | transcript-grow | 14 | 3483.1 / 2097.5 / 7477.2 / 14501.0 | 3337.3 / 1860.0 / 6754.7 | 1.0437 | 2794.5 / 37404.4 | 1550.1 / 226.3 / 3904.4 | refused (n=14<60) |
| `rows-longrun-2026-10-26-policy.jsonl` | transcript-grow | 15 | 5242.8 / 4720.0 / 12952.6 / 14352.0 | 20645.8 / 13174.0 / 57129.8 | 0.2539 | 36840.0 / 49531.8 | 5279.6 / 3204.1 / 12574.3 | refused (n=15<60) |
| `rows-longrun-2026-10-26.jsonl` | lease-reopen | 39 | 110.5 / 119.0 / 128.0 / 128.0 | 246.6 / 239.0 / 423.6 | 0.4482 | 185.0 / 202.0 | 1547.1 / 1567.9 / 2208.6 | refused (n=39<60) |
| `rows-longrun-2026-10-26.jsonl` | pointer-stable | 12 | 110.1 / 128.0 / 128.0 / 128.0 | 439.9 / 527.5 / 683.5 | 0.2502 | 1872.5 / 1918.0 | 919.9 / 525.9 / 1688.7 | refused (n=12<60) |
| `rows-longrun-2026-10-26.jsonl` | transcript-compact | 41 | 112.4 / 107.0 / 128.0 / 128.0 | 238.9 / 243.0 / 260.0 | 0.4705 | 4390.0 / 6425.0 | 908.9 / 630.1 / 1466.5 | refused (n=41<60) |
| `rows-longrun-CELLTX01.jsonl` | bounded-context-fetch | 47 | 6.0 / 5.0 / 9.0 / 9.0 | 13.9 / 12.0 / 17.0 | 0.4312 | 1341.0 / 2139.4 | 104.6 / 102.7 / 148.9 | refused (n=47<60) |
| `rows-longrun-CELLTX01.jsonl` | masking-no-fetch | 48 | 5.0 / 5.0 / 5.0 / 5.0 | 12.0 / 12.0 / 12.0 | 0.4167 | 833.0 / 1294.0 | 93.5 / 94.6 / 121.3 | refused (n=48<60) |
| `rows-longrun-c-2026-10-26.jsonl` | lease-reopen | 34 | 244.6 / 87.5 / 538.8 / 2470.0 | 802.5 / 272.5 / 1717.2 | 0.3047 | 429.0 / 442.4 | 140.7 / 136.2 / 143.3 | refused (n=34<60) |
| `rows-longrun-c-2026-10-26.jsonl` | pointer-stable | 47 | 103.0 / 73.0 / 151.8 / 964.0 | 387.6 / 272.0 / 609.8 | 0.2657 | 2213.0 / 2219.0 | 185.3 / 167.0 / 206.6 | refused (n=47<60) |
| `rows-longrun-c-2026-10-26.jsonl` | transcript-compact | 48 | 37.6 / 36.0 / 40.0 / 62.0 | 149.4 / 140.0 / 168.0 | 0.2516 | 3867.0 / 5263.6 | 205.4 / 202.5 / 216.9 | refused (n=48<60) |
| `rows-longrun-c-2026-10-26.jsonl` | transcript-grow | 48 | 634.5 / 550.0 / 1358.1 / 1500.0 | 2480.1 / 2050.0 / 4945.4 | 0.2558 | 18239.5 / 31642.4 | 507.7 / 482.2 / 767.4 | refused (n=48<60) |
| `rows-longrun-v3-2026-10-26.jsonl` | pointer-stable | 47 | 83.0 / 54.0 / 120.4 / 1070.0 | 312.7 / 190.0 / 396.0 | 0.2653 | 2250.0 / 2262.8 | 181.4 / 168.3 / 217.7 | refused (n=47<60) |
| `rows-longrun-v3-2026-10-26.jsonl` | transcript-grow | 48 | 23.2 / 23.0 / 26.0 / 26.0 | 78.5 / 79.0 / 95.0 | 0.2955 | 3545.5 / 4708.4 | 200.7 / 200.7 / 214.7 | refused (n=48<60) |
| `rows-longrun-v4-2026-10-26.jsonl` | pointer-stable | 40 | 122.0 / 34.0 / 279.0 / 1694.0 | 449.5 / 131.5 / 1028.0 | 0.2713 | 4105.0 / 4124.4 | 200.4 / 187.8 / 253.4 | refused (n=40<60) |
| `rows-longrun-v4-2026-10-26.jsonl` | transcript-grow | 48 | 23.6 / 22.0 / 29.0 / 29.0 | 81.4 / 72.0 / 113.0 | 0.2902 | 5409.0 / 6585.7 | 221.3 / 199.8 / 215.4 | refused (n=48<60) |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | pointer-stable | 47 | 75.8 / 63.0 / 118.4 / 268.0 | 250.6 / 212.0 / 407.2 | 0.3025 | 4213.0 / 4326.4 | 198.7 / 201.6 / 251.7 | refused (n=47<60) |
| `rows-longrun-v5-tools.jsonl` | pointer-stable | 47 | 117.9 / 69.0 / 152.8 / 1146.0 | 390.5 / 247.0 / 465.4 | 0.3018 | 4253.0 / 4269.8 | 159.5 / 139.4 / 159.2 | refused (n=47<60) |
| `rows-longrun-v6-tools.jsonl` | pointer-stable | 48 | 206.8 / 62.5 / 323.1 / 3283.0 | 648.4 / 219.0 / 1038.0 | 0.3189 | 4259.5 / 5755.0 | 177.2 / 144.8 / 269.5 | refused (n=48<60) |
| `rows-pilot-thinking-2026-10-26.jsonl` | transcript-grow | 5 | 4470.2 / 2027.0 / 11160.4 / 15624.0 | 13353.6 / 6559.0 / 32775.6 | 0.3348 | 8453.0 / 24191.2 | 1320.7 / 675.7 / 3049.6 | refused (n=5<60) |
| `rows-posctrl-2026-11-08.jsonl` | masking-no-fetch | 48 | 39.2 / 31.0 / 43.0 / 370.0 | 133.8 / 89.0 / 175.0 | 0.2927 | 6063.0 / 7299.4 | 187.1 / 191.8 / 220.3 | refused (n=48<60) |
| `rows-rep2-bounded-context-fetch-maskon-tx01-20261109.jsonl` | bounded-context-fetch | 96 | 10.1 / 5.0 / 33.0 / 33.0 | 27.0 / 12.0 / 98.0 | 0.3728 | 1150.0 / 1929.5 | 111.5 / 106.3 / 164.7 | 174.5 |
| `rows-rep2-masking-no-fetch-maskoff-tx01-20261109.jsonl` | masking-no-fetch | 48 | 5.8 / 5.0 / 9.0 / 9.0 | 13.4 / 12.0 / 17.0 | 0.4346 | 970.0 / 1459.8 | 159.6 / 165.8 / 233.5 | refused (n=48<60) |
| `rows-rep2-masking-no-fetch-maskon-tx01-20261109.jsonl` | masking-no-fetch | 48 | 5.0 / 5.0 / 5.0 / 5.0 | 12.0 / 12.0 / 12.0 | 0.4167 | 833.0 / 1294.0 | 99.0 / 97.1 / 123.1 | refused (n=48<60) |
| `rows-smoke-spcc-2026-11-10.jsonl` | spcc | 6 | 9.2 / 5.0 / 17.5 / 18.0 | 23.3 / 12.0 / 46.0 | 0.3929 | 626.5 / 725.5 | 140.2 / 146.1 / 173.2 | refused (n=6<60) |
| `rows-smoke-spcc2-2026-11-10.jsonl` | spcc | 6 | 7.5 / 7.5 / 10.0 / 10.0 | 14.0 / 14.0 / 16.0 | 0.5357 | 702.0 / 804.5 | 110.4 / 107.8 / 125.2 | refused (n=6<60) |
| `rows-smoke-tx01-20261109.jsonl` | masking-no-fetch | 6 | 10.0 / 10.0 / 10.0 / 10.0 | 16.0 / 16.0 / 16.0 | 0.6250 | 299.5 / 353.5 | 105.2 / 105.4 / 129.3 | refused (n=6<60) |
| `rows-smoke2-tx01-20261109.jsonl` | bounded-context-fetch | 5 | 265.8 / 212.0 / 444.0 / 562.0 | 986.0 / 787.0 / 1703.8 | 0.2696 | 4808.0 / 5403.0 | 211.5 / 199.4 / 264.3 | refused (n=5<60) |
| `rows-smoke2-tx01-20261109.jsonl` | masking-no-fetch | 5 | 33.4 / 33.0 / 38.0 / 38.0 | 115.0 / 105.0 / 135.0 | 0.2904 | 4406.0 / 4512.6 | 371.1 / 128.4 / 746.5 | refused (n=5<60) |
| `rows-spcc-billedproof-2026-11-10.jsonl` | masking-no-fetch | 100 | 5.4 / 5.0 / 5.0 / 10.0 | 12.3 / 12.0 / 12.0 | 0.4383 | 1765.0 / 2855.5 | 128.6 / 130.0 / 149.4 | 164.9 |
| `rows-stack8014-masking-no-fetch-maskoff-tx01-20261109.jsonl` | masking-no-fetch | 48 | 5.7 / 5.0 / 8.0 / 11.0 | 13.2 / 12.0 / 14.0 | 0.4351 | 970.0 / 1454.4 | 194.8 / 195.4 / 267.6 | refused (n=48<60) |
| `rows-stack8014-masking-no-fetch-maskon-tx01-20261109.jsonl` | masking-no-fetch | 48 | 5.3 / 5.0 / 5.0 / 21.0 | 13.7 / 12.0 / 12.0 | 0.3891 | 841.0 / 1310.0 | 204.6 / 189.6 / 248.8 | refused (n=48<60) |
| `rows-sup-2026-11-09.jsonl` | bounded-context-fetch | 100 | 6.5 / 5.0 / 10.0 / 10.0 | 13.2 / 12.0 / 16.0 | 0.4947 | 2786.5 / 3712.1 | 195.7 / 180.7 / 257.3 | 323.8 |
| `rows-sup-2026-11-09.jsonl` | masking-no-fetch | 103 | 5.6 / 5.0 / 10.0 / 10.0 | 12.5 / 12.0 / 16.0 | 0.4503 | 1940.0 / 3225.8 | 185.0 / 165.3 / 269.8 | 294.4 |
| `rows-sup2-fetch.jsonl` | bounded-context-fetch | 90 | 6.8 / 5.0 / 11.0 / 11.0 | 13.5 / 12.0 / 17.0 | 0.5037 | 2681.0 / 3803.0 | 207.9 / 188.3 / 274.1 | 329.8 |
| `rows-sup2-masking.jsonl` | masking-no-fetch | 103 | 5.7 / 5.0 / 11.0 / 11.0 | 12.6 / 12.0 / 17.0 | 0.4529 | 1948.0 / 3232.8 | 181.2 / 172.1 / 250.1 | 303.4 |
| `rows-toolcallfix-d-20261109T064028Z.jsonl` | bounded-context-fetch | 24 | 5.3 / 5.0 / 6.4 / 8.0 | 12.8 / 12.0 / 12.7 | 0.4183 | 802.5 / 1574.4 | 91.1 / 89.9 / 127.3 | refused (n=24<60) |
| `rows-tx01-real-20261109.jsonl` | bounded-context-fetch | 5 | 5.0 / 5.0 / 5.0 / 5.0 | 12.0 / 12.0 / 12.0 | 0.4167 | 693.0 / 728.2 | 124.8 / 133.3 / 163.8 | refused (n=5<60) |
| `rows-tx01-real-20261109.jsonl` | masking-no-fetch | 5 | 5.6 / 5.0 / 6.8 / 8.0 | 12.4 / 12.0 / 13.2 | 0.4516 | 369.0 / 404.2 | 106.9 / 94.9 / 131.4 | refused (n=5<60) |
| `rows-tx02-fetch-r1.jsonl` | bounded-context-fetch | 87 | 6.9 / 5.0 / 10.0 / 21.0 | 13.9 / 12.0 / 16.0 | 0.4983 | 2371.0 / 3230.4 | 158.3 / 150.1 / 190.4 | 202.2 |
| `rows-tx02-fetch-r2.jsonl` | bounded-context-fetch | 88 | 11.4 / 12.0 / 12.0 / 83.0 | 22.1 / 23.0 / 23.0 | 0.5164 | 2396.5 / 3439.4 | 166.3 / 160.0 / 227.1 | 240.4 |
| `rows-tx02-masking-r1.jsonl` | masking-no-fetch | 88 | 5.8 / 5.0 / 10.0 / 10.0 | 12.6 / 12.0 / 16.0 | 0.4586 | 1667.0 / 2655.5 | 123.4 / 125.6 / 141.0 | 147.6 |
| `rows-tx02-masking-r2.jsonl` | masking-no-fetch | 88 | 7.1 / 5.0 / 10.0 / 36.0 | 14.7 / 12.0 / 16.0 | 0.4830 | 1667.0 / 2655.5 | 120.2 / 123.4 / 134.8 | 141.6 |
| `rows-tx03-8014-fetch-r1.jsonl` | bounded-context-fetch | 100 | 7.9 / 9.0 / 9.0 / 32.0 | 13.3 / 12.0 / 12.0 | 0.5923 | 2388.5 / 3362.1 | 140.3 / 129.6 / 231.9 | 241.5 |
| `rows-tx03-8014-masking-r1.jsonl` | masking-no-fetch | 100 | 6.0 / 5.0 / 10.0 / 10.0 | 12.8 / 12.0 / 16.0 | 0.4659 | 1765.0 / 2870.5 | 131.2 / 126.2 / 173.6 | 230.6 |
| `rows-tx03-fetch-r1.jsonl` | bounded-context-fetch | 89 | 7.0 / 5.0 / 11.6 / 18.0 | 15.4 / 12.0 / 20.8 | 0.4570 | 2236.0 / 3431.0 | 145.5 / 128.6 / 189.0 | 191.5 |
| `rows-tx03-fetch-r2.jsonl` | bounded-context-fetch | 87 | 7.4 / 5.0 / 18.0 / 18.0 | 16.3 / 12.0 / 40.0 | 0.4514 | 2315.0 / 3363.8 | 140.8 / 126.0 / 189.7 | 194.9 |
| `rows-tx03-fetchfix-r1.jsonl` | bounded-context-fetch | 99 | 7.2 / 5.0 / 10.0 / 10.0 | 13.8 / 12.0 / 16.0 | 0.5242 | 2447.0 / 3396.8 | 141.2 / 124.4 / 187.8 | 194.5 |
| `rows-tx03-fetchfix-r2.jsonl` | bounded-context-fetch | 100 | 7.2 / 5.0 / 10.0 / 10.0 | 13.8 / 12.0 / 16.0 | 0.5254 | 2496.5 / 3384.3 | 126.6 / 119.6 / 184.3 | 197.4 |
| `rows-tx03-masking-r1.jsonl` | masking-no-fetch | 100 | 5.4 / 5.0 / 5.0 / 10.0 | 12.3 / 12.0 / 12.0 | 0.4383 | 1765.0 / 2855.5 | 120.8 / 119.4 / 143.5 | 148.8 |
| `rows-tx03-masking-r2.jsonl` | masking-no-fetch | 100 | 5.9 / 5.0 / 5.5 / 52.0 | 13.1 / 12.0 / 12.4 | 0.4529 | 1765.0 / 2855.5 | 119.2 / 119.4 / 140.7 | 144.2 |

Cells withheld (n<5), listed so no small cell masquerades as a distribution:

- `rows-longrun-2026-10-26-fix.jsonl` / `lease-reopen`: n=3 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26-fix.jsonl` / `pointer-stable`: n=3 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26-fix.jsonl` / `transcript-compact`: n=4 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26-policy.jsonl` / `lease-reopen`: n=2 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26-policy.jsonl` / `pointer-stable`: n=3 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26-policy.jsonl` / `transcript-compact`: n=3 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26.jsonl` / `transcript-grow`: n=1 < 5: not reported as a distribution, no p90/p95
- `rows-smoke-tx01-20261109.jsonl` / `bounded-context-fetch`: n=3 < 5: not reported as a distribution, no p90/p95

## 3. The decomposition

Regression pooled across arms **within one file**, so no slope crosses a file boundary:

| file | n | b_prompt | b_completion | R² | c_completion (prompt omitted, upper bound) | corr(ln prompt, ln completion) |
|---|---|---|---|---|---|---|
| `rows-abs2-2026-11-09.jsonl` | 242 | +0.0183 | +0.3995 | 0.603 | +0.4015 | 0.145 |
| `rows-agg-8014.jsonl` | 141 | +0.1529 | +0.3404 | 0.372 | +0.3387 | -0.031 |
| `rows-agg-fetch-mt36.jsonl` | 41 | +0.5580 | +0.2596 | 0.749 | +0.3451 | 0.276 |
| `rows-agg-fetch-mt50.jsonl` | 54 | +0.4782 | +0.1731 | 0.664 | +0.2103 | 0.197 |
| `rows-agg-fetch-r1.jsonl` | 10 | +0.5937 | +0.4318 | 0.901 | +0.4421 | 0.040 |
| `rows-agg-fetch-test.jsonl` | 36 | +0.5163 | +0.2643 | 0.663 | +0.2882 | 0.077 |
| `rows-agg-fetch-test2.jsonl` | 37 | +0.6031 | +0.2612 | 0.806 | +0.3331 | 0.252 |
| `rows-agg-masking-r1.jsonl` | 100 | -0.0243 | +0.1594 | 0.104 | +0.1801 | -0.527 |
| `rows-agg2-2026-11-09.jsonl` | 242 | +0.0153 | +0.1019 | 0.158 | +0.1037 | 0.280 |
| `rows-agg3-instructed.jsonl` | 122 | +0.0155 | +0.1558 | 0.238 | +0.1569 | 0.202 |
| `rows-cell-bounded-context-fetch-20261111T231050Z.jsonl` | 101 | +0.1247 | +0.0445 | 0.187 | +0.0526 | 0.101 |
| `rows-cell-bounded-context-fetch-20261111T231625Z.jsonl` | 119 | +0.1883 | +0.1051 | 0.413 | +0.1206 | 0.304 |
| `rows-cell-lease-reopen-20261027T024223Z.jsonl` | 30 | +0.7483 | +0.3284 | 0.316 | +0.2863 | -0.061 |
| `rows-cell-lease-reopen-20261027T084049Z.jsonl` | 56 | +0.4751 | +0.1622 | 0.344 | +0.1844 | 0.081 |
| `rows-cell-lease-reopen-20261028T032823Z.jsonl` | 91 | +0.8564 | +0.1583 | 0.245 | +0.1583 | -0.000 |
| `rows-cell-lease-reopen-20261028T033139Z.jsonl` | 96 | +0.7102 | +0.0821 | 0.280 | +0.1007 | 0.048 |
| `rows-cell-masking-no-fetch-20261111T230833Z.jsonl` | 100 | +0.1474 | +0.1027 | 0.613 | -0.0698 | -0.405 |
| `rows-cell-masking-no-fetch-20261111T231412Z.jsonl` | 100 | +0.1988 | +0.1169 | 0.473 | -0.0270 | -0.329 |
| `rows-cell-pinned-20261111T230953Z.jsonl` | 100 | +0.0945 | +0.4474 | 0.324 | +0.4314 | -0.073 |
| `rows-cell-pinned-20261111T231541Z.jsonl` | 100 | +0.0901 | -0.0131 | 0.162 | -0.0045 | 0.114 |
| `rows-cell-pointer-stable-20261026T182535Z.jsonl` | 27 | -5.5388 | -0.0128 | 0.501 | +0.0641 | -0.418 |
| `rows-cell-pointer-stable-20261026T202040Z.jsonl` | 12 | +0.0955 | -0.0344 | 0.515 | -0.0358 | -0.332 |
| `rows-cell-pointer-stable-20261026T204258Z.jsonl` | 12 | -0.3453 | -0.0047 | 0.020 | +0.0133 | -0.714 |
| `rows-cell-pointer-stable-20261027T004027Z.jsonl` | 25 | -1.0010 | +0.2143 | 0.062 | +0.1842 | 0.187 |
| `rows-cell-pointer-stable-20261028T024509Z.jsonl` | 96 | +1.0822 | +0.0645 | 0.059 | +0.0702 | 0.047 |
| `rows-cell-pointer-stable-20261028T024942Z.jsonl` | 93 | +1.1802 | +0.0380 | 0.063 | +0.0478 | 0.076 |
| `rows-cell-pointer-stable-20261028T025312Z.jsonl` | 94 | +0.7365 | +0.0360 | 0.019 | +0.0387 | 0.034 |
| `rows-cell-pointer-stable-20261028T025853Z.jsonl` | 93 | +1.6356 | +0.0809 | 0.178 | +0.0787 | -0.010 |
| `rows-cell-pointer-stable-20261028T030232Z.jsonl` | 94 | +1.9435 | +0.0454 | 0.111 | +0.0192 | -0.142 |
| `rows-cell-pointer-stable-20261028T030559Z.jsonl` | 89 | +0.5085 | +0.0656 | 0.031 | +0.0689 | 0.061 |
| `rows-cell-spcc-20261111T230914Z.jsonl` | 100 | +0.0614 | +0.0324 | 0.073 | +0.0101 | -0.133 |
| `rows-cell-spcc-20261111T231458Z.jsonl` | 100 | +0.0538 | -0.1403 | 0.035 | -0.1592 | -0.135 |
| `rows-cell-transcript-compact-20261026T203733Z.jsonl` | 12 | +2.7963 | -0.0143 | 0.739 | -0.1259 | -0.370 |
| `rows-cell-transcript-compact-20261027T004155Z.jsonl` | 14 | +2.5261 | -0.0408 | 0.614 | -0.1124 | -0.581 |
| `rows-cell-transcript-compact-20261028T032235Z.jsonl` | 66 | +1.5474 | +0.0776 | 0.215 | +0.0699 | -0.033 |
| `rows-cell-transcript-compact-20261028T032430Z.jsonl` | 81 | +0.7556 | +0.0378 | 0.089 | +0.0151 | -0.147 |
| `rows-cell-transcript-grow-20261026T202444Z.jsonl` | 12 | -0.0842 | +0.0376 | 0.027 | +0.0416 | -0.480 |
| `rows-cell-transcript-grow-20261027T004129Z.jsonl` | 13 | -7.4233 | -0.0815 | 0.123 | +0.1149 | -0.526 |
| `rows-cell-transcript-grow-20261028T030925Z.jsonl` | 77 | -0.1466 | +0.1032 | 0.029 | +0.1053 | -0.085 |
| `rows-cell-transcript-grow-20261028T031218Z.jsonl` | 53 | -0.2011 | +0.0105 | 0.004 | +0.0114 | -0.027 |
| `rows-cell-transcript-grow-20261028T031401Z.jsonl` | 56 | +0.1153 | +0.0037 | 0.002 | +0.0015 | -0.126 |
| `rows-cell-transcript-grow-20261028T031606Z.jsonl` | 56 | +1.0041 | +0.0414 | 0.148 | +0.0408 | -0.003 |
| `rows-cell-transcript-grow-20261028T031753Z.jsonl` | 82 | +1.1290 | +0.0658 | 0.121 | +0.0605 | -0.033 |
| `rows-cell-transcript-grow-20261028T032058Z.jsonl` | 53 | +1.2747 | +0.0964 | 0.152 | +0.0881 | -0.038 |
| `rows-contrast24-tx01-20261109.jsonl` | 51 | +0.2431 | +0.2538 | 0.504 | +0.3869 | 0.654 |
| `rows-control-nomask-tx01-20261109.jsonl` | 48 | -0.3947 | +0.3237 | 0.264 | -0.0018 | 0.406 |
| `rows-e1-final-2026-11-10.jsonl` | 300 | +0.0688 | +0.2874 | 0.342 | +0.3023 | 0.174 |
| `rows-e1-indexfix-2026-11-10.jsonl` | 343 | +0.1018 | +0.4857 | 0.748 | +0.5027 | 0.243 |
| `rows-e1-parserfix-2026-11-10.jsonl` | 325 | +0.1545 | +0.3909 | 0.676 | +0.4072 | 0.161 |
| `rows-e1-spcc-2026-11-10.jsonl` | 100 | +0.2513 | +0.1064 | 0.215 | +0.1709 | 0.379 |
| `rows-e1-tools-2026-11-10.jsonl` | 318 | +0.1277 | +0.3709 | 0.365 | +0.3964 | 0.225 |
| `rows-e2-compact-2026-11-10.jsonl` | 300 | -0.0356 | +0.0699 | 0.005 | +0.0608 | 0.273 |
| `rows-e2-turnover-2026-11-10.jsonl` | 300 | +0.0552 | +0.1287 | 0.056 | +0.1364 | 0.114 |
| `rows-e3-retain-2026-11-10.jsonl` | 200 | +0.0605 | +0.2739 | 0.493 | +0.2962 | 0.204 |
| `rows-equalinfo-2026-10-26.jsonl` | 67 | -0.0244 | +0.6549 | 0.693 | +0.6610 | -0.397 |
| `rows-fetchall-c-20261109.jsonl` | 48 | +0.4636 | +0.6249 | 0.571 | +1.9982 | — |
| `rows-fetchall-d-20261109.jsonl` | 53 | +0.4485 | +0.2808 | 0.665 | +0.3578 | 0.425 |
| `rows-fetchmandate-20261109.jsonl` | 10 | -0.0670 | -0.1458 | 0.403 | -0.1362 | -0.416 |
| `rows-hop-2026-11-09.jsonl` | 450 | +0.0665 | +0.0952 | 0.119 | +0.1105 | 0.400 |
| `rows-hop-8014-r2.jsonl` | 191 | +0.0164 | +0.2911 | 0.255 | +0.2898 | -0.102 |
| `rows-hop-8014-r3.jsonl` | 245 | +0.0837 | +0.1785 | 0.130 | +0.1482 | -0.364 |
| `rows-hop-8014.jsonl` | 194 | +0.0594 | +0.3896 | 0.341 | +0.3783 | -0.207 |
| `rows-hop2-fetch.jsonl` | 208 | +0.1634 | +0.3443 | 0.529 | +0.3410 | -0.028 |
| `rows-hop2-masking.jsonl` | 180 | +0.0800 | +0.2193 | 0.309 | +0.2035 | -0.072 |
| `rows-hop3-instructed.jsonl` | 197 | +0.1814 | +0.4862 | 0.625 | +0.4822 | -0.026 |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | +0.6665 | -0.0957 | 0.622 | +0.2102 | 0.414 |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | +0.9527 | +0.0987 | 0.851 | +0.8526 | 0.589 |
| `rows-longrun-2026-10-26.jsonl` | 93 | -0.1842 | +0.8194 | 0.344 | +0.7240 | 0.078 |
| `rows-longrun-CELLTX01.jsonl` | 111 | +0.2930 | +0.4213 | 0.875 | +0.4955 | 0.456 |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | +0.3184 | +0.0720 | 0.721 | +0.0724 | 0.001 |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | +0.0373 | -0.0531 | 0.052 | -0.0583 | -0.385 |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | -0.1902 | -0.0297 | 0.036 | -0.0227 | -0.316 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | -2.0609 | +0.0635 | 0.295 | +0.0187 | 0.203 |
| `rows-longrun-v5-tools.jsonl` | 72 | +0.2432 | +0.0759 | 0.064 | +0.0661 | -0.133 |
| `rows-longrun-v6-tools.jsonl` | 72 | +1.8084 | +0.0748 | 0.775 | +0.0310 | -0.128 |
| `rows-posctrl-2026-11-08.jsonl` | 48 | +0.6301 | +0.1238 | 0.210 | +0.1007 | -0.111 |
| `rows-rep2-bounded-context-fetch-maskon-tx01-20261109.jsonl` | 109 | +0.3100 | +0.3129 | 0.780 | +0.3917 | 0.462 |
| `rows-rep2-masking-no-fetch-maskoff-tx01-20261109.jsonl` | 48 | +0.0433 | +0.2827 | 0.026 | +0.3185 | 0.406 |
| `rows-rep2-masking-no-fetch-maskon-tx01-20261109.jsonl` | 48 | +0.2164 | +1.4105 | 0.274 | +2.0515 | — |
| `rows-smoke-tx01-20261109.jsonl` | 16 | +0.6062 | +0.1659 | 0.614 | +0.3843 | 0.793 |
| `rows-smoke2-tx01-20261109.jsonl` | 10 | +0.0209 | -0.1200 | 0.039 | -0.1194 | 0.372 |
| `rows-spcc-billedproof-2026-11-10.jsonl` | 100 | +0.0493 | -0.0003 | 0.040 | -0.0149 | -0.088 |
| `rows-stack8014-masking-no-fetch-maskoff-tx01-20261109.jsonl` | 48 | +0.5906 | +0.0281 | 0.952 | +0.5367 | 0.398 |
| `rows-stack8014-masking-no-fetch-maskon-tx01-20261109.jsonl` | 48 | +0.3618 | -0.0620 | 0.225 | -0.0198 | 0.049 |
| `rows-sup-2026-11-09.jsonl` | 269 | +0.2235 | +0.2218 | 0.646 | +0.2434 | 0.219 |
| `rows-sup2-fetch.jsonl` | 145 | +0.0183 | +0.2236 | 0.581 | +0.2248 | 0.219 |
| `rows-sup2-masking.jsonl` | 103 | +0.1876 | +0.0152 | 0.230 | -0.0043 | -0.038 |
| `rows-toolcallfix-d-20261109T064028Z.jsonl` | 27 | +0.5413 | +0.3810 | 0.857 | +0.5025 | 0.599 |
| `rows-tx01-real-20261109.jsonl` | 10 | +0.1543 | +0.5393 | 0.086 | +0.4039 | -0.371 |
| `rows-tx02-fetch-r1.jsonl` | 110 | +0.1462 | +0.3688 | 0.585 | +0.3710 | 0.035 |
| `rows-tx02-fetch-r2.jsonl` | 114 | +0.3254 | +0.3013 | 0.549 | +0.3058 | 0.032 |
| `rows-tx02-masking-r1.jsonl` | 88 | +0.0225 | +0.0925 | 0.030 | +0.0764 | -0.312 |
| `rows-tx02-masking-r2.jsonl` | 88 | +0.0442 | +0.0813 | 0.065 | +0.0520 | -0.533 |
| `rows-tx03-8014-fetch-r1.jsonl` | 148 | -0.1200 | +0.7370 | 0.738 | +0.7314 | 0.096 |
| `rows-tx03-8014-masking-r1.jsonl` | 100 | +0.1253 | +0.0537 | 0.063 | +0.0142 | -0.136 |
| `rows-tx03-fetch-r1.jsonl` | 105 | +0.0584 | +0.4563 | 0.757 | +0.4600 | 0.114 |
| `rows-tx03-fetch-r2.jsonl` | 101 | +0.1446 | +0.4451 | 0.739 | +0.4517 | 0.083 |
| `rows-tx03-fetchfix-r1.jsonl` | 138 | +0.0309 | +0.5089 | 0.752 | +0.5119 | 0.191 |
| `rows-tx03-fetchfix-r2.jsonl` | 134 | +0.4383 | +0.4833 | 0.706 | +0.5095 | 0.120 |
| `rows-tx03-masking-r1.jsonl` | 100 | +0.0635 | +0.0863 | 0.065 | +0.0675 | -0.088 |
| `rows-tx03-masking-r2.jsonl` | 100 | +0.0585 | +0.0829 | 0.087 | +0.0511 | -0.264 |

A positive `b_prompt` is prefill cost — more prompt tokens, later first token. `b_completion` is the number the confound hypothesis needs: if longer answers delayed the first token it would be positive and material. TTFT is clocked to the first streamed delta, so the answer is produced **after** that instant.

| file | arms (a − b) | TTFT ratio | completion × | b_prompt·Δln p | b_completion·Δln c | residual | gap share prompt / completion / residual | survives completion normalisation | survives: most conservative (used) |
|---|---|---|---|---|---|---|---|---|---|
| `rows-abs2-2026-11-09.jsonl` | bounded-context-fetch − masking-no-fetch | 0.97x | 1.28x | +0.006 | +0.097 | -0.134 | -20% / -316% / 436% | 416.0% | 100.0% |
| `rows-agg2-2026-11-09.jsonl` | bounded-context-fetch − masking-no-fetch | 1.35x | 1.76x | +0.006 | +0.058 | +0.234 | 2% / 19% / 79% | 80.6% | 67.9% |
| `rows-contrast24-tx01-20261109.jsonl` | bounded-context-fetch − masking-no-fetch | 1.11x | 2.05x | +0.146 | +0.182 | -0.228 | 145% / 181% / -227% | -81.5% | -176.6% |
| `rows-e1-final-2026-11-10.jsonl` | bounded-context-fetch − masking-no-fetch | 1.28x | 1.64x | +0.016 | +0.143 | +0.087 | 6% / 58% / 35% | 41.8% | 38.8% |
| `rows-e1-final-2026-11-10.jsonl` | bounded-context-fetch − spcc | 1.43x | 1.50x | +0.048 | +0.117 | +0.190 | 13% / 33% / 53% | 67.0% | 65.3% |
| `rows-e1-final-2026-11-10.jsonl` | masking-no-fetch − spcc | 1.12x | 0.92x | +0.032 | -0.025 | +0.104 | 29% / -23% / 94% | 122.7% | 100.0% |
| `rows-e1-indexfix-2026-11-10.jsonl` | bounded-context-fetch − masking-no-fetch | 1.07x | 1.26x | +0.032 | +0.111 | -0.076 | 48% / 165% / -112% | -64.6% | -70.3% |
| `rows-e1-indexfix-2026-11-10.jsonl` | bounded-context-fetch − spcc | 1.16x | 1.20x | +0.066 | +0.091 | -0.012 | 46% / 62% / -8% | 37.6% | -368.1% |
| `rows-e1-indexfix-2026-11-10.jsonl` | masking-no-fetch − spcc | 1.08x | 0.96x | +0.034 | -0.021 | +0.064 | 44% / -26% / 83% | 126.5% | 100.0% |
| `rows-e1-parserfix-2026-11-10.jsonl` | bounded-context-fetch − masking-no-fetch | 1.14x | 1.13x | +0.053 | +0.046 | +0.034 | 40% / 35% / 25% | 65.4% | 63.9% |
| `rows-e1-parserfix-2026-11-10.jsonl` | bounded-context-fetch − spcc | 1.17x | 0.97x | +0.074 | -0.012 | +0.097 | 47% / -8% / 61% | 107.7% | 100.0% |
| `rows-e1-parserfix-2026-11-10.jsonl` | masking-no-fetch − spcc | 1.03x | 0.86x | +0.021 | -0.058 | +0.063 | 82% / -225% / 244% | 325.1% | 100.0% |
| `rows-e1-tools-2026-11-10.jsonl` | bounded-context-fetch − masking-no-fetch | 1.33x | 1.19x | +0.044 | +0.066 | +0.173 | 16% / 23% / 61% | 76.8% | 75.2% |
| `rows-e1-tools-2026-11-10.jsonl` | bounded-context-fetch − spcc | 1.33x | 1.08x | +0.062 | +0.027 | +0.196 | 22% / 10% / 69% | 90.5% | 89.8% |
| `rows-e1-tools-2026-11-10.jsonl` | masking-no-fetch − spcc | 1.00x | 0.90x | +0.018 | -0.039 | +0.022 | 1059% / -2299% / 1340% | 2398.6% | 100.0% |
| `rows-e3-retain-2026-11-10.jsonl` | masking-no-fetch − spcc | 0.97x | 1.02x | +0.006 | +0.006 | -0.047 | -18% / -16% / 134% | 116.5% | 116.5% |
| `rows-equalinfo-2026-10-26.jsonl` | C0F − C0FT | 0.48x | 0.26x | +0.000 | -0.890 | +0.165 | -0% / 123% / -23% | -22.7% | -813.7% |
| `rows-equalinfo-2026-10-26.jsonl` | C0F − R | 0.40x | 0.26x | -0.051 | -0.881 | +0.011 | 6% / 96% / -1% | 4.3% | 3.4% |
| `rows-equalinfo-2026-10-26.jsonl` | C0FT − R | 0.82x | 1.01x | -0.051 | +0.008 | -0.153 | 26% / -4% / 78% | 104.2% | 64.1% |
| `rows-fetchmandate-20261109.jsonl` | bounded-context-fetch − masking-no-fetch | 0.95x | 0.64x | -0.035 | +0.065 | -0.084 | 65% / -120% / 155% | 220.1% | 100.0% |
| `rows-hop-2026-11-09.jsonl` | bounded-context-fetch − masking-no-fetch | 1.00x | 2.25x | +0.015 | +0.077 | -0.092 | 7929% / 39684% / -47513% | -39584.0% | -45965.1% |
| `rows-longrun-2026-10-26.jsonl` | lease-reopen − pointer-stable | 1.96x | 1.02x | +0.427 | +0.018 | +0.226 | 64% / 3% / 34% | 97.4% | 97.4% |
| `rows-longrun-2026-10-26.jsonl` | lease-reopen − transcript-compact | 1.69x | 0.97x | +0.573 | -0.027 | -0.024 | 110% / -5% / -5% | 105.2% | 90.4% |
| `rows-longrun-2026-10-26.jsonl` | pointer-stable − transcript-compact | 0.86x | 0.95x | +0.146 | -0.045 | -0.249 | -98% / 30% / 168% | 69.8% | 69.8% |
| `rows-longrun-CELLTX01.jsonl` | bounded-context-fetch − masking-no-fetch | 1.10x | 1.16x | +0.147 | +0.064 | -0.113 | 149% / 65% / -114% | 35.2% | 23.8% |
| `rows-longrun-c-2026-10-26.jsonl` | lease-reopen − pointer-stable | 0.77x | 1.24x | -0.514 | +0.016 | +0.244 | 202% / -6% / -96% | 106.1% | 106.1% |
| `rows-longrun-c-2026-10-26.jsonl` | lease-reopen − transcript-compact | 0.69x | 2.57x | -0.687 | +0.068 | +0.249 | 185% / -18% / -67% | 118.3% | 116.1% |
| `rows-longrun-c-2026-10-26.jsonl` | lease-reopen − transcript-grow | 0.29x | 0.24x | -1.146 | -0.102 | +0.012 | 93% / 8% / -1% | 91.7% | 89.8% |
| `rows-longrun-c-2026-10-26.jsonl` | pointer-stable − transcript-compact | 0.89x | 2.07x | -0.173 | +0.052 | +0.005 | 150% / -45% / -4% | 145.4% | 126.4% |
| `rows-longrun-c-2026-10-26.jsonl` | pointer-stable − transcript-grow | 0.37x | 0.19x | -0.632 | -0.118 | -0.232 | 64% / 12% / 24% | 88.0% | 86.7% |
| `rows-longrun-c-2026-10-26.jsonl` | transcript-compact − transcript-grow | 0.42x | 0.09x | -0.459 | -0.170 | -0.237 | 53% / 20% / 27% | 80.3% | 77.8% |
| `rows-longrun-v3-2026-10-26.jsonl` | pointer-stable − transcript-grow | 0.91x | 2.41x | -0.017 | -0.047 | -0.026 | 19% / 52% / 29% | 48.1% | 43.0% |
| `rows-longrun-v4-2026-10-26.jsonl` | pointer-stable − transcript-grow | 0.93x | 2.13x | +0.053 | -0.022 | -0.105 | -71% / 30% / 141% | 70.0% | 70.0% |
| `rows-smoke2-tx01-20261109.jsonl` | bounded-context-fetch − masking-no-fetch | 0.81x | 6.76x | +0.002 | -0.229 | +0.011 | -1% / 106% / -5% | -6.2% | -6.2% |
| `rows-sup-2026-11-09.jsonl` | bounded-context-fetch − masking-no-fetch | 1.07x | 1.14x | +0.079 | +0.028 | -0.036 | 110% / 39% / -50% | 60.8% | 56.9% |
| `rows-tx01-real-20261109.jsonl` | bounded-context-fetch − masking-no-fetch | 1.14x | 0.91x | +0.099 | -0.051 | +0.082 | 76% / -39% / 63% | 138.9% | 100.0% |

How to read the table: arms are listed `a − b`, so `TTFT ratio` is arm a's mean-log TTFT over arm b's (below 1 means a is faster), `completion ×` is `exp(delta ln completion)` = arm a's answer length relative to arm b's, the three share columns are `beta * delta` in log units, and the last two columns are the share of the gap that survives removing the fitted completion-length term (the most conservative of the mean-log model, the completion-only upper bound, and the p50 basis is the one the verdict uses). Shares outside 0-100% are honest arithmetic on near-zero gaps, not errors.

**Headline (G4 / `rows-longrun-c-2026-10-26.jsonl`).** `pointer-stable` answers at **0.19x** the completion length of `transcript-grow` — the other arm's answers are **5.14x** longer — yet `pointer-stable`'s mean-log TTFT is **0.37x** that of `transcript-grow`. Split by the fitted coefficients: prompt tokens -0.632, completion length -0.118, residual -0.232 of a -0.982 log gap. **88.0% of the gap survives holding completion length equal.**

On the **p50** basis the gap is **0.35x** (prompt -0.672, completion -0.142, residual -0.247 of -1.060); the completion-only upper bound is -0.118 of that gap, and the most conservative surviving fraction across all three accountings — mean-log model, completion-only upper bound, p50 basis — is **86.7%**, which is the number the verdict rests on.

## 4. Can the arms be compared on quality at all?

**No, not on any answer-length-sensitive metric.** Same grid, same treatment controls, answer length differing by roughly an order of magnitude: an `ANSWER:`-line rate or a verified-answer count then measures answer length as much as treatment. Per-arm answer length beside those counts:

| file | arm | n | median completion tok | median answer chars | `ANSWER:` line rate | answer_verified rate |
|---|---|---|---|---|---|---|
| `rows-abs2-2026-11-09.jsonl` | bounded-context-fetch | 98 | 5 | 12 | 1.00 | 0.23 |
| `rows-abs2-2026-11-09.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.15 |
| `rows-agg-8014.jsonl` | bounded-context-fetch | 99 | 12 | 18 | 1.00 | 0.00 |
| `rows-agg-fetch-mt36.jsonl` | bounded-context-fetch | 34 | 11 | 17 | 1.00 | 0.00 |
| `rows-agg-fetch-mt50.jsonl` | bounded-context-fetch | 41 | 11 | 17 | 1.00 | 0.00 |
| `rows-agg-fetch-r1.jsonl` | bounded-context-fetch | 8 | 9 | 46 | 1.00 | 0.00 |
| `rows-agg-fetch-test.jsonl` | bounded-context-fetch | 30 | 12 | 18 | 1.00 | 0.00 |
| `rows-agg-fetch-test2.jsonl` | bounded-context-fetch | 29 | 11 | 17 | 1.00 | 0.00 |
| `rows-agg-masking-r1.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.00 |
| `rows-agg2-2026-11-09.jsonl` | bounded-context-fetch | 109 | 11 | 17 | 0.92 | 0.04 |
| `rows-agg2-2026-11-09.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.00 |
| `rows-agg3-instructed.jsonl` | bounded-context-fetch | 94 | 5 | 12 | 0.97 | 0.01 |
| `rows-baseline-2026-10-26.jsonl` | C | 24 | 300 | 200 | 0.00 | 0.00 |
| `rows-baseline-2026-10-26.jsonl` | C0 | 24 | 300 | 200 | 0.00 | 0.00 |
| `rows-baseline-2026-10-26.jsonl` | R | 36 | 6 | 12 | 0.00 | 0.00 |
| `rows-cell-bounded-context-fetch-20261111T231050Z.jsonl` | bounded-context-fetch | 100 | 5 | 12 | 0.99 | 0.00 |
| `rows-cell-bounded-context-fetch-20261111T231625Z.jsonl` | bounded-context-fetch | 99 | 5 | 12 | 1.00 | 0.06 |
| `rows-cell-lease-reopen-20261027T024223Z.jsonl` | lease-reopen | 10 | 44 | 120 | 0.40 | 0.00 |
| `rows-cell-lease-reopen-20261027T084049Z.jsonl` | lease-reopen | 12 | 27 | 64 | 0.50 | 0.25 |
| `rows-cell-lease-reopen-20261028T032823Z.jsonl` | lease-reopen | 34 | 32 | 80 | 0.59 | 0.12 |
| `rows-cell-lease-reopen-20261028T033139Z.jsonl` | lease-reopen | 27 | 50 | 108 | 0.44 | 0.11 |
| `rows-cell-masking-no-fetch-20261111T230833Z.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.06 |
| `rows-cell-masking-no-fetch-20261111T231412Z.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.06 |
| `rows-cell-pinned-20261111T230953Z.jsonl` | pinned | 100 | 5 | 12 | 1.00 | 0.06 |
| `rows-cell-pinned-20261111T231541Z.jsonl` | pinned | 100 | 5 | 12 | 0.99 | 0.06 |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | pointer-stable | 5 | 1415 | 152 | 0.00 | 0.00 |
| `rows-cell-pointer-stable-20261026T182535Z.jsonl` | pointer-stable | 25 | 56 | 248 | 0.36 | 0.12 |
| `rows-cell-pointer-stable-20261026T202040Z.jsonl` | pointer-stable | 11 | 205 | 807 | 0.73 | 0.18 |
| `rows-cell-pointer-stable-20261026T204258Z.jsonl` | pointer-stable | 12 | 74 | 237 | 0.42 | 0.17 |
| `rows-cell-pointer-stable-20261027T004027Z.jsonl` | pointer-stable | 10 | 58 | 62 | 0.30 | 0.20 |
| `rows-cell-pointer-stable-20261028T024509Z.jsonl` | pointer-stable | 37 | 28 | 64 | 0.32 | 0.16 |
| `rows-cell-pointer-stable-20261028T024942Z.jsonl` | pointer-stable | 34 | 38 | 58 | 0.35 | 0.18 |
| `rows-cell-pointer-stable-20261028T025312Z.jsonl` | pointer-stable | 38 | 32 | 59 | 0.32 | 0.16 |
| `rows-cell-pointer-stable-20261028T025853Z.jsonl` | pointer-stable | 39 | 28 | 60 | 0.28 | 0.15 |
| `rows-cell-pointer-stable-20261028T030232Z.jsonl` | pointer-stable | 38 | 20 | 56 | 0.32 | 0.16 |
| `rows-cell-pointer-stable-20261028T030559Z.jsonl` | pointer-stable | 38 | 28 | 74 | 0.34 | 0.16 |
| `rows-cell-spcc-20261111T230914Z.jsonl` | spcc | 100 | 5 | 12 | 1.00 | 0.06 |
| `rows-cell-spcc-20261111T231458Z.jsonl` | spcc | 100 | 5 | 12 | 1.00 | 0.06 |
| `rows-cell-transcript-compact-20261026T203733Z.jsonl` | transcript-compact | 12 | 21 | 92 | 1.00 | 0.17 |
| `rows-cell-transcript-compact-20261027T004155Z.jsonl` | transcript-compact | 12 | 64 | 42 | 0.25 | 0.08 |
| `rows-cell-transcript-compact-20261028T032235Z.jsonl` | transcript-compact | 40 | 70 | 69 | 0.23 | 0.10 |
| `rows-cell-transcript-compact-20261028T032430Z.jsonl` | transcript-compact | 43 | 73 | 94 | 0.26 | 0.12 |
| `rows-cell-transcript-grow-20261026T202444Z.jsonl` | transcript-grow | 7 | 382 | 1420 | 0.43 | 0.29 |
| `rows-cell-transcript-grow-20261027T004129Z.jsonl` | transcript-grow | 11 | 72 | 78 | 0.27 | 0.09 |
| `rows-cell-transcript-grow-20261028T030925Z.jsonl` | transcript-grow | 36 | 70 | 69 | 0.22 | 0.11 |
| `rows-cell-transcript-grow-20261028T031218Z.jsonl` | transcript-grow | 37 | 72 | 71 | 0.22 | 0.16 |
| `rows-cell-transcript-grow-20261028T031401Z.jsonl` | transcript-grow | 39 | 76 | 87 | 0.26 | 0.15 |
| `rows-cell-transcript-grow-20261028T031606Z.jsonl` | transcript-grow | 43 | 70 | 69 | 0.19 | 0.16 |
| `rows-cell-transcript-grow-20261028T031753Z.jsonl` | transcript-grow | 40 | 69 | 58 | 0.30 | 0.17 |
| `rows-cell-transcript-grow-20261028T032058Z.jsonl` | transcript-grow | 33 | 70 | 69 | 0.21 | 0.15 |
| `rows-contrast24-tx01-20261109.jsonl` | bounded-context-fetch | 24 | 11 | 30 | 1.00 | 0.04 |
| `rows-contrast24-tx01-20261109.jsonl` | masking-no-fetch | 24 | 5 | 12 | 1.00 | 0.00 |
| `rows-control-nomask-tx01-20261109.jsonl` | masking-no-fetch | 48 | 5 | 12 | 1.00 | 0.25 |
| `rows-e1-final-2026-11-10.jsonl` | bounded-context-fetch | 100 | 5 | 12 | 1.00 | 0.05 |
| `rows-e1-final-2026-11-10.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.08 |
| `rows-e1-final-2026-11-10.jsonl` | spcc | 100 | 5 | 12 | 1.00 | 0.22 |
| `rows-e1-indexfix-2026-11-10.jsonl` | bounded-context-fetch | 100 | 10 | 16 | 1.00 | 0.48 |
| `rows-e1-indexfix-2026-11-10.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.08 |
| `rows-e1-indexfix-2026-11-10.jsonl` | spcc | 100 | 5 | 12 | 0.99 | 0.20 |
| `rows-e1-parserfix-2026-11-10.jsonl` | bounded-context-fetch | 88 | 5 | 12 | 1.00 | 0.19 |
| `rows-e1-parserfix-2026-11-10.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.08 |
| `rows-e1-parserfix-2026-11-10.jsonl` | spcc | 99 | 5 | 12 | 0.98 | 0.21 |
| `rows-e1-spcc-2026-11-10.jsonl` | spcc | 100 | 5 | 12 | 0.98 | 0.20 |
| `rows-e1-tools-2026-11-10.jsonl` | bounded-context-fetch | 89 | 5 | 12 | 1.00 | 0.25 |
| `rows-e1-tools-2026-11-10.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.08 |
| `rows-e1-tools-2026-11-10.jsonl` | spcc | 100 | 5 | 12 | 1.00 | 0.22 |
| `rows-e2-compact-2026-11-10.jsonl` | spcc | 300 | 5 | 12 | 1.00 | 0.25 |
| `rows-e2-turnover-2026-11-10.jsonl` | spcc | 300 | 5 | 12 | 1.00 | 0.41 |
| `rows-e3-retain-2026-11-10.jsonl` | masking-no-fetch | 100 | 10 | 16 | 1.00 | 0.42 |
| `rows-e3-retain-2026-11-10.jsonl` | spcc | 100 | 5 | 12 | 1.00 | 0.48 |
| `rows-equalinfo-2026-10-26.jsonl` | C0F | 15 | 2 | 2 | 0.00 | 0.00 |
| `rows-equalinfo-2026-10-26.jsonl` | C0FT | 18 | 4 | 2 | 0.00 | 0.00 |
| `rows-equalinfo-2026-10-26.jsonl` | R | 28 | 7 | 2 | 0.00 | 0.00 |
| `rows-fetchall-c-20261109.jsonl` | masking-no-fetch | 48 | 5 | 12 | 1.00 | 0.00 |
| `rows-fetchall-d-20261109.jsonl` | bounded-context-fetch | 48 | 5 | 12 | 1.00 | 0.06 |
| `rows-fetchinstruct-probe.jsonl` | bounded-context-fetch | 5 | 5 | 12 | 1.00 | 0.00 |
| `rows-fetchmandate-20261109.jsonl` | bounded-context-fetch | 5 | 5 | 12 | 1.00 | 0.00 |
| `rows-fetchmandate-20261109.jsonl` | masking-no-fetch | 5 | 5 | 12 | 1.00 | 0.00 |
| `rows-hop-2026-11-09.jsonl` | bounded-context-fetch | 168 | 5 | 12 | 0.79 | 0.10 |
| `rows-hop-2026-11-09.jsonl` | masking-no-fetch | 180 | 5 | 12 | 1.00 | 0.07 |
| `rows-hop-8014-r2.jsonl` | bounded-context-fetch | 178 | 5 | 12 | 1.00 | 0.02 |
| `rows-hop-8014-r3.jsonl` | bounded-context-fetch | 221 | 5 | 12 | 1.00 | 0.05 |
| `rows-hop-8014.jsonl` | bounded-context-fetch | 176 | 5 | 12 | 1.00 | 0.00 |
| `rows-hop2-fetch.jsonl` | bounded-context-fetch | 173 | 5 | 12 | 0.99 | 0.05 |
| `rows-hop2-masking.jsonl` | masking-no-fetch | 180 | 5 | 12 | 1.00 | 0.07 |
| `rows-hop3-instructed.jsonl` | bounded-context-fetch | 176 | 5 | 12 | 1.00 | 0.03 |
| `rows-longrun-2026-10-26-fix.jsonl` | transcript-grow | 14 | 2098 | 1860 | 0.00 | 0.00 |
| `rows-longrun-2026-10-26-policy.jsonl` | transcript-grow | 15 | 4720 | 13174 | 0.00 | 0.00 |
| `rows-longrun-2026-10-26.jsonl` | lease-reopen | 39 | 119 | 239 | 0.00 | 0.00 |
| `rows-longrun-2026-10-26.jsonl` | pointer-stable | 12 | 128 | 528 | 0.00 | 0.00 |
| `rows-longrun-2026-10-26.jsonl` | transcript-compact | 41 | 107 | 243 | 0.00 | 0.00 |
| `rows-longrun-CELLTX01.jsonl` | bounded-context-fetch | 47 | 5 | 12 | 1.00 | 0.26 |
| `rows-longrun-CELLTX01.jsonl` | masking-no-fetch | 48 | 5 | 12 | 1.00 | 0.00 |
| `rows-longrun-c-2026-10-26.jsonl` | lease-reopen | 34 | 88 | 272 | 0.00 | 0.00 |
| `rows-longrun-c-2026-10-26.jsonl` | pointer-stable | 47 | 73 | 272 | 0.00 | 0.00 |
| `rows-longrun-c-2026-10-26.jsonl` | transcript-compact | 48 | 36 | 140 | 0.00 | 0.00 |
| `rows-longrun-c-2026-10-26.jsonl` | transcript-grow | 48 | 550 | 2050 | 0.00 | 0.00 |
| `rows-longrun-v3-2026-10-26.jsonl` | pointer-stable | 47 | 54 | 190 | 0.66 | 0.02 |
| `rows-longrun-v3-2026-10-26.jsonl` | transcript-grow | 48 | 23 | 79 | 1.00 | 0.00 |
| `rows-longrun-v4-2026-10-26.jsonl` | pointer-stable | 40 | 34 | 132 | 0.75 | 0.03 |
| `rows-longrun-v4-2026-10-26.jsonl` | transcript-grow | 48 | 22 | 72 | 1.00 | 0.00 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | pointer-stable | 47 | 63 | 212 | 0.19 | 0.02 |
| `rows-longrun-v5-tools.jsonl` | pointer-stable | 47 | 69 | 247 | 0.09 | 0.00 |
| `rows-longrun-v6-tools.jsonl` | pointer-stable | 48 | 62 | 219 | 0.15 | 0.02 |
| `rows-pilot-thinking-2026-10-26.jsonl` | transcript-grow | 5 | 2027 | 6559 | 0.00 | 0.00 |
| `rows-posctrl-2026-11-08.jsonl` | masking-no-fetch | 48 | 31 | 89 | 1.00 | 0.02 |
| `rows-rep2-bounded-context-fetch-maskon-tx01-20261109.jsonl` | bounded-context-fetch | 96 | 5 | 12 | 1.00 | 0.12 |
| `rows-rep2-masking-no-fetch-maskoff-tx01-20261109.jsonl` | masking-no-fetch | 48 | 5 | 12 | 1.00 | 0.25 |
| `rows-rep2-masking-no-fetch-maskon-tx01-20261109.jsonl` | masking-no-fetch | 48 | 5 | 12 | 1.00 | 0.00 |
| `rows-smoke-spcc-2026-11-10.jsonl` | spcc | 6 | 5 | 12 | 1.00 | 0.00 |
| `rows-smoke-spcc2-2026-11-10.jsonl` | spcc | 6 | 8 | 14 | 1.00 | 0.33 |
| `rows-smoke-tx01-20261109.jsonl` | masking-no-fetch | 6 | 10 | 16 | 1.00 | 0.00 |
| `rows-smoke2-tx01-20261109.jsonl` | bounded-context-fetch | 5 | 212 | 787 | 1.00 | 0.00 |
| `rows-smoke2-tx01-20261109.jsonl` | masking-no-fetch | 5 | 33 | 105 | 1.00 | 0.00 |
| `rows-spcc-billedproof-2026-11-10.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.08 |
| `rows-stack8014-masking-no-fetch-maskoff-tx01-20261109.jsonl` | masking-no-fetch | 48 | 5 | 12 | 1.00 | 0.19 |
| `rows-stack8014-masking-no-fetch-maskon-tx01-20261109.jsonl` | masking-no-fetch | 48 | 5 | 12 | 1.00 | 0.00 |
| `rows-sup-2026-11-09.jsonl` | bounded-context-fetch | 100 | 5 | 12 | 1.00 | 0.22 |
| `rows-sup-2026-11-09.jsonl` | masking-no-fetch | 103 | 5 | 12 | 1.00 | 0.13 |
| `rows-sup2-fetch.jsonl` | bounded-context-fetch | 90 | 5 | 12 | 1.00 | 0.20 |
| `rows-sup2-masking.jsonl` | masking-no-fetch | 103 | 5 | 12 | 1.00 | 0.11 |
| `rows-toolcallfix-d-20261109T064028Z.jsonl` | bounded-context-fetch | 24 | 5 | 12 | 1.00 | 0.12 |
| `rows-tx01-real-20261109.jsonl` | bounded-context-fetch | 5 | 5 | 12 | 1.00 | 0.00 |
| `rows-tx01-real-20261109.jsonl` | masking-no-fetch | 5 | 5 | 12 | 1.00 | 0.00 |
| `rows-tx02-fetch-r1.jsonl` | bounded-context-fetch | 87 | 5 | 12 | 1.00 | 0.33 |
| `rows-tx02-fetch-r2.jsonl` | bounded-context-fetch | 88 | 12 | 23 | 1.00 | 0.41 |
| `rows-tx02-masking-r1.jsonl` | masking-no-fetch | 88 | 5 | 12 | 1.00 | 0.14 |
| `rows-tx02-masking-r2.jsonl` | masking-no-fetch | 88 | 5 | 12 | 1.00 | 0.14 |
| `rows-tx03-8014-fetch-r1.jsonl` | bounded-context-fetch | 100 | 9 | 12 | 1.00 | 0.42 |
| `rows-tx03-8014-masking-r1.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.08 |
| `rows-tx03-fetch-r1.jsonl` | bounded-context-fetch | 89 | 5 | 12 | 1.00 | 0.13 |
| `rows-tx03-fetch-r2.jsonl` | bounded-context-fetch | 87 | 5 | 12 | 1.00 | 0.08 |
| `rows-tx03-fetchfix-r1.jsonl` | bounded-context-fetch | 99 | 5 | 12 | 1.00 | 0.41 |
| `rows-tx03-fetchfix-r2.jsonl` | bounded-context-fetch | 100 | 5 | 12 | 1.00 | 0.42 |
| `rows-tx03-masking-r1.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.08 |
| `rows-tx03-masking-r2.jsonl` | masking-no-fetch | 100 | 5 | 12 | 1.00 | 0.08 |

## 5. What `RUN-A*` must report so this can never be ambiguous again

`RUN-A*` must publish, **per arm and per grid, with n and the rows-file sha256**: (1) `completion_tokens` and answer characters as mean/median/p90/max, so verbosity is never inferred from a slope; (2) TTFT at mean/median/p90 and a p95 **only** where n≥60, with the refusal stated below that floor; (3) the fitted `b_prompt`/`b_completion` with R², so a TTFT gap is decomposed rather than asserted; (4) `ANSWER:`-line rate and `answer_verified` rate **beside** median answer length, because a count metric that grows with answer length is not treatment evidence. A gap quoted without those four numbers is a slope with treatment and verbosity still tangled inside it.

## 6. Limits

- No p95 is published for any cell: the largest per-(file,arm) completed-turn cell is 300 rows, below the 60 floor. Mean/median/p90 published with n.
- TTFT is clocked to the first streamed delta; completion tokens are produced after that instant, so completion length cannot mechanically delay TTFT. b_completion is the load-bearing test of that.
- Answer length remains a real confound for quality and for ANSWER:-line production, which is a different dependent variable from TTFT.
- No field in these rows separates prefill *compute* from server queueing/wait: `ttft_ms` is one client-side first-delta clock. The prompt-side share is therefore a **proxy** (fitted on prompt tokens), not measured prefill FLOPs. A server-side `prefill_ms` (or per-request `queue_wait_ms`) is what would split them.
