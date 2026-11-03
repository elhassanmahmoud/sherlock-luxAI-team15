# Independent final V14 Python 3.10 technical review

**PASS for the recorded, limited V14 technical scope. No blocking runtime discrepancy found.** This is compatibility evidence for the unchanged existing V14 on the tested macOS arm64 environment, not P promotion, Windows certification or a new strength result. Two provenance limits are retained below rather than silently strengthened.

## Actual completed checks

- `runner310`: exit 0; exactly eight complete 303-step games, all combinations of two reused development seeds (500720/500721), both sides and default/Solution_92. Each record reports fresh belief and verified loaded weights. The reviewed runner verifies every loaded state against the checkpoint, then rejects anything except eight complete games. The logs identify 36 loaded networks.
- `zip310`: exit 0; existing ZIP works under both `agents/` and project-root layouts, both sides, with 36 networks. The train=True-style constructor/save/update probes retain frozen evaluation mode and unchanged checkpoint bytes. These are first-step/API/frozen-update smoke checks, **not full games**.
- `record313`: exit 0; one real 303-step game using the unchanged packaged agent on both sides, seed 4242; 36 networks loaded. The record script invokes update after each step and records both teams.
- `replay310`: exit 0; 303 recorded steps, two players per step (606 player-action comparisons), **zero differing actions**, 36 networks and frozen=True. Replay does not simulate another game.

Thus there are **nine new full technical games: 8+1**, not eleven or more. The initial SciPy failure occurred during agent import before games and adds zero. All four log hashes match process.json. I independently rehashed all eight distinct protected paths across process/runner receipts; current raw V14, both active weights and ZIP remain unchanged.

## Payload/source and repaired environment

ZIP SHA256 remains `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`; raw V14 remains `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. Embedded checkpoint SHA is `d3d87209ca3a0a44eae26f052d863e68f54b427cb1b0e19082a21b3bd02e05c4`. ZIP member inventory matches the payload receipt. I independently compared all **14 bundled runtime modules byte-for-byte with git75af0c5**, not with the current zone-rescue source.

The existing payload receipt reports 36 ordered float32 79/256/6 networks, exact tensor/metadata/other-field equality and only `cfg.frozen=True` added. Raw frozen is absent with effective default False. It explicitly covers the existing legacy V14 payload; it is **not** a successful invocation of the P actual qualification validator. No model/tensor reload was performed by this reviewer.

The isolated Python environment is 3.10.22, torch2.2.2, NumPy1.26.4, JAX/JAXLIB0.4.35 and luxai-s3 0.2.1. SciPy1.15.3 was replaced by the official macOS14 arm64 1.14.1 wheel. I verified its local SHA against the repair receipt and archived PyPI response, all 25 repair-evidence hashes, all ten engine Python hashes, and the interpreter SHA. Before/after distribution records differ **only for SciPy**; all 60 current version/RECORD pairs equal the final snapshot, including the other 59 unchanged distributions. The recorded dependency/library checks pass. The intermediate macOS12 wheel was rejected/replaced and is not the validated final environment.

Performance HEAD remains 03e54e267242ff642c126313fe5f512ed9d959ac. No technical result here validates the newly integrated zone_rescue behavior or changes P's failed confirmation decision.

## Provenance limits

1. process.json records exact commands, log hashes, exit codes and durations, but omits cwd/start timestamps and a run-time source snapshot. It therefore cannot alone prove historical launch cwd or chronology relative to environment repair. Root reports execution from frozen performance03e after mutation stopped; current source/engine/package identities and logs are consistent. Do not present the receipt alone as a complete immutable launch attestation.
2. Root confirms the payload producer and launcher were inline commands, not saved executable files. The producer used the previously reviewed config_schema/checkpoint_schema (explicit defaults, raw False/embedded True) and strict_equal over the entire raw checkpoint with only frozen=True added, with CPU uint8 tensor-byte comparison. An initial missing-defaults TypeError produced no games; the corrected invocation passed. Root reports the launcher held the existing resource lock, used performance03e cwd and THREAD_ENV, and wrote fresh logs. These are after-the-fact method statements, not retroactively created launch/source attestations. Independent checks here validate the resulting archive/raw/embedded bytes and historical members; the exact inline execution cannot be reconstructed from a preserved producer file.

These limit provenance wording, not the observed exit-0 runtime evidence. No repeat model/game activity was requested or performed to fill them. Course timing limits remain unknown; measured timing is not deadline certification. No Windows execution or all-dependency-version compatibility is claimed.

## Game ledger

**218+1,632+3,000+9,000+9 = 13,859 explicitly recorded game executions.** The earlier 218 derive from the established ledger (26 diagnostic +24 prototype +168 Gaussian). The first-wave audit supports two completed 816-game arms, 1,632 total, while the four-arm pilot remained incomplete. Selection/confirmation counts were separately audited. Earlier traces were not all re-audited in this technical review. This sum mixes technical, training, validation and evaluation executions; it is not a claim of 13,859 unique maps or fresh independent performance trials. Unit tests, package smoke calls, unsuccessful imports and action replay add no full games.

Machine-readable evidence and artifact hashes: `/tmp/V14_py310_final_review.json`. Review used only source/JSON/log/ZIP-byte/file-hash reads and stdlib; no Torch, actual model, game, environment execution, network service, source edit or repository mutation.
