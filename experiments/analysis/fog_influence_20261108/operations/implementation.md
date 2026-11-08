# Fog influence implementation — 08.11.2026

Implemented only `scripts/fog_influence.py` and `tests/test_fog_influence.py`. No games, training, weight changes/search, real model-bank execution, commits or pushes.

CLI after source commit/review, using the project Python:

```
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m scripts.fog_influence --expected-head FULL_CURRENT_HEAD --usage-file ACTUAL_FRESH_USAGE_JSON
```

Fixed exclusive output: `experiments/analysis/fog_influence_20261108/run_v1/`. Its parent already holds method-review metadata; the new subfolder preserves that metadata. Existing run output is never overwritten/adopted. Default STOP is canonical system-temp `/private/tmp/sherlock-fog-influence-20261108/STOP` on this Mac. Signals/STOP interrupt the offline work; partial evidence remains, state is incomplete, no automatic retry.

Input binding reuses `F.historical_acceptance`/`F.validate_admission`, with independent audit JSON trust anchor `cf563a0ac4c8ee890ee33800cc00e189d3d9104e11becca99e51c91441b49198` for the four local replay buffers. Accepted V14/candidates/final checkpoints remain unchanged. Actual checkpoints must have no CNN policy and share79features/6actions/hidden/dueling/finitefloat32 weights; all candidate order/config checks are retained. No Agent or environment is constructed.

Sampling is PCG64seed0, sequential arms control41/neutral41/control42/neutral42, without replacement within each buffer, up to2500 eligible rows each. Uses only `ns` with its stored `mask`, excludes done/nonlegal rows, rejects malformed/nonfinite input. No current-state mask substitution or recorded-action quality label. Bank metadata reports exact byte-unique `(ns,mask)` count; across-arm duplicates stay.

Before any forward: exclusively writes `bank.npz` (features/masks/original row indices/arm indices) and `bank_manifest.json` (buffer hashes, bank byte/content hashes, ordered40member hashes and sampling details). These become guarded inputs. Then CPUfloat32/eval/no_grad forwards40 members (original36,control41/42,neutral41/42), and independently reloads/forwards each actual38-member candidate. `torch.stack(...).mean` must reproduce each independent mean at atol/rtol1e-6. Fixed batches512; no fitting/tuning.

`outputs.npz` stores all40memberQ arrays, V14/CONTROL38/NEUTRAL38 means, both independent candidate means, row/arm indices and ordered member labels/hashes. `summary.json` contains legal minus1e9 masked proposal changes/SAPto-from counts including per-bank-arm counts; memberQ/legal-gap distributions; pairP−baseB and2/38scaled contributions at both winners; fixed V14best/runnerup margin changes for all>=2legal rows; changed-winner margins separately; parent18 versus allfourfinal members. Reports are descriptive, with explicit trained-on/dependent replay, no confidence intervals, action-quality/Fog/final-rule/strength claims.

Execution uses existing compute_lock, source/HEAD/input/protected hash checks, AC/fresh actual quota<100 and newer foreign probe/model/test process checks. One model process; no children/work queue. Full guard before model inspection/sampling/forward and after outputs; STOP/signal checked each batch, full resource/hash checks at most10seconds apart. Source plans/current interpreter and every accepted input/output bank are bound in state/summary.

Tests: initial TDD collection failed because module did not exist. Final focused command:

```
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_fog_influence.py -q --disable-warnings --maxfail=1
11 passed in 2.41s
```

Coverage: capped deterministic no-replacement next-state sampling, sequential RNG, exact pooled duplicates, tampered buffer hashes, nonfinite/wrong-schema inputs, legal masking/illegal-winner failure, pair/full-mean arithmetic, fixed runnerup margins even without action change,1legal rows, independent-mean tolerance/nonfinite errors, and exclusive pre-forward bank evidence. Only synthetic arrays/files; no real models/buffers forwarded. No test process active. Root final runtime/model audit and actual guarded diagnosis remain pending.
