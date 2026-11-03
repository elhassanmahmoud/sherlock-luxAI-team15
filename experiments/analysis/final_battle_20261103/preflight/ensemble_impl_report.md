# Final candidate builder and seed audit

Implemented only `scripts/final_battle_candidates.py` and `tests/test_final_battle_candidates.py` in `/Users/moayedshawesh/Desktop/KI/sherlock-november-followup`. No commit, no real candidate construction, no games, no forward calls, no training, no supervisor edits.

## Builder

- Fixed PAIR18/PAIR24/FT18/Z36 rosters exactly as the accepted plan. q is index 0. No weight averaging or duplicated net copies. Z36 changes only zone_rescue=true; all other inference configurations equal the raw V14 dictionary.
- SHA-pinned V14, exactly 36 unique float32 DuelingDQN members,79 features / 6 actions, all layer shapes and finite tensors validated before output creation.
- Correct first selected q and matching target_q. Constructs inference-only checkpoints, drops stale optimizer/source-history metadata, normalizes env_steps 60000 / learn_steps 0 with explicit manifest explanation. These counters are not presented as new training history.
- Only new directories inside this worktree's experiments/ensembles; no overwrite or symlink traversal. Source and trained inputs are rehashed after writing. Manifest is written last only after checkpoint reload/tensor/config verification.
- Ordered source indices and tensor hashes, source/output/builder hashes, full inference configuration, net and unique tensor counts, and training provenance retained. C36 explicitly nonnominatable.
- Optional --control and --rescue must be supplied together. Both use scripts.final_rescue_train.validate_final_receipt against their actual role (control18/adapt18); all chronology/audit/checkpoint/prepared-source evidence checked there. Builder additionally pins component 18, V14 source tensor,1200 training / 120 prefill / 96 validation games,180000 updates / env_steps 459960, correct final artifact, no duplicate tensors, and identical opponent/side chronology. Only index 18 is replaced; inference flags remain V14.

## Verification actually executed

- Initial missing-builder red test: 1 failed; initial fixture suite also failed as expected before implementation.
- Core builder: 12 passed.
- Training integration red test reproduced the initially mismatched wrapper import; corrected to the actual final_rescue_train interface.
- Final focused suite: 18 passed in 5.93 s. Includes synthetic complete receipts using the real trainer receipt validator, exact member identity/config/target, malformed source/hash/count/shape/NaN/duplicates, output protections, incomplete optional inputs, swapped roles, modified final weights, incomplete counts/chronology, and correct C36/R36 replacement.
- One authorized real-source READ ONLY validation: source SHA 98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8; 36 members, 36 unique hashes, 79 features, 6 actions, hidden 256,dueling=true. No candidate outputs or agent constructed.
- Full suite remains root-owned because simultaneous model work/suite is centrally coordinated. Focused tests establish builder behavior, not game strength or release approval.

## Commands for root

Run from the followup worktree after source freeze. The interpreter is shared with the primary checkout; this worktree has no .venv.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m scripts.final_battle_candidates --source agents/sherlock/weights/agent_p0.pth --out experiments/ensembles/final_battle_20261103
```

This builds the four untrained candidates only. To build all six in a new output directory, append both `--control experiments/runs/CONTROL_RUN/weights/agent.pth` and `--rescue experiments/runs/RESCUE_RUN/weights/agent.pth`, substituting the coordinator's actual new run names. Each run must contain its verified `final_receipt.json`. Do not create the four-candidate directory first if the intended final roster includes training arms: output directories are deliberately never overwritten.

## Seed audit

Machine-readable detail: `/tmp/sherlock-final-20261103/seed_audit.json`.

All 7 registered worktrees scanned; 6,908 CSV copies, 1,474 unique CSV contents, 1,578,774 seed rows, 667 unique JSON files and 1,110 unique text files. Compressed CSVs included. No CSV consumption overlaps, no read/parse errors.

- **Real prior consumption:** 495000–495003 were historical scratchpad training games. Evidence: primary docs/ARBEITSSTAND.md:977 / followup:969, explicitly acknowledged again in docs/superpowers/plans/2026-11-02-targeting-adaptation.md:24. Root explicitly accepts these four reused prefill cards; do not call the prefill block wholly fresh.
- Other 495000–495059 mentions are abandoned control19/adapt19 preparation plans; those arms were not run.
- Training 493000–493599: no consumed data found. The older night_20261101 audit lists 491500–495000 as an available gap/possible command, not an executed run.
- Screen 851000–851079, confirmation 852000–852399 and direct 853000–853399: no prior consumption found; current final-battle plan reservation only. One 852166 match is a SHA digest; three JSONL numeric matches have actual seeds 485007/484302/484310 outside all requested ranges.
- Audit establishes absence in inspected local records, not universal absence of undocumented/external runs. Known prefill repeats are training-only and do not overlap the new evaluation blocks.
