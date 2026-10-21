# Independent precheck of CNN3 analysis helpers

Reviewed 21 October 2026 while the single fixed trainer was active. Read-only review of the two helpers, their text archives, `compare_report`, the PPO loader/save path, evaluation schema and existing manifest/control evidence. No helper execution, Torch/engine import, model test, training or game was performed. Only this report was written. This is a static review, not the final data audit.

Reviewed helper hashes, both byte-identical to their `.py.txt` archives:

- `analyze.py`: `10d93449ef8d3b14d2398b97cde9695044e5cbaef598b35b131b85c53b400028`
- `verify_training.py`: `eb6e97a0c12ce44f75454e8b773e1ec32c377f76b42af65790259239db14dde4`

**Initial verdict: statistical calculation and fixed gates are correct; strengthen data validation and evidence binding before using the analysis output as the gate decision.** The following initial findings are retained as review history; see the rereview below for their current status. These helpers are outside the existing 66-file source freeze, so root may correct and rearchive them without modifying running model sources.

## Rereview after corrections

The revised `analyze.py` (`755189ccda3d509c0e2989ec87c4f66f90da3c181120fb00f23f5a74ece5ce11`) and `verify_training.py` (`665d17e53c821c93a52ffa264ac4c86d42fd570da659f6cc3a6273a41a402160`) are each byte-identical to their updated archives. Their changed sections were reread without execution, project import, Torch import or tests.

The two substantive findings are resolved: analysis now checks the full evaluation schema and finite/nonnegative measurements, fractional ranges, legal match-win counts, result/game-win/point-win consistency, the four required unique successful jobs, completed output hashes, current source HEAD, verified final checkpoint path/hash in the frozen inputs, and warmstart/training-CSV identity. It validates the training-check flags and directly compares the four fixed control rows with V3 rather than relying solely on the JSON assertion. The verifier adds stage, current feature dimension, single-policy/loaded-key/architecture checks, statistic ranges, elapsed-time cap/deadline and the training CSV hash. The unchanged statistical logic remains approved.

One small closure was sent to root before use: require `set(control.columns) == set(GAME_FIELDS)` before iterating the control columns, so a missing non-time column cannot silently escape reproduction; also bind `reproduction['v3_sha256']` to the protected current V3 hash. The existing control CSV does have the full schema, so this is completeness of the helper, not observed corruption. With those two assertions, no remaining static-review blocker is identified. Final numerical/checkpoint verification and the independent completed-data audit remain outstanding.

## Required analysis corrections

1. **Finite and valid measurements (`analyze.py:25–31`).** `validated_results` validates only keys and `result`; it drops all other fields internally. The helper therefore does not establish its protocol's finite-measurement requirement. Pandas `invalid_frac.max()` skips missing values, so a mixture of zero and NaN passes. NaN match-win fields also fall through the nested comparison to a draw. Require the complete expected schema, numeric conversion and finiteness for every numeric measurement, legal integer match wins in 0–3 with their sum at most 3, and exact `invalid_frac == 0` for every row. Check `game_win == (our_wins > opp_wins)` and `point_win` against recorded point totals, using the production convention. Fractions/counts should have their normal ranges; `secs` must be finite and nonnegative. These checks supplement, rather than replace, the existing exact keys and result checks.

2. **Bind gate inputs to successful, verified jobs (`analyze.py:11–15,49,55–56`).** Recording a newly calculated input hash does not prove it equals the completed job's output hash. The helper embeds `v3_reproduction.json` and `training_check.json` without asserting their success fields or identities. Before deciding gates, require the named baseline, controls, training and candidate jobs exactly once, successful with post-job input verification; compare their CSV output hashes/row counts with the current files. Require the four expected V3 control keys, all-non-time equality, and matching V3/reference/control hashes (preferably independently recreate the four-row comparison). Require the training-check success/completion fields, fixed `ppo_0010.pth` path, 10 iterations/240 games, matching warmstart and current final-checkpoint hashes; bind the candidate job's `--weights` to that same final checkpoint. Add that final checkpoint to the launcher's frozen inputs before candidate evaluation. Check current Git HEAD against the recorded source head before reporting that head. The existing broad `all(j...)` is useful but does not require the expected jobs or connect candidate data to the approved checkpoint.

These are validation gaps, not evidence that the already recorded baseline or controls are wrong. Root's control JSON records four games and all 23 non-time summary fields identical; the final independent audit should reproduce that claim directly from the CSVs.

## Correct statistical and gate behavior

- Exact equality to the Cartesian set of two opponents × seeds 500720–500779 × both sides, combined with 240 rows and duplicate rejection, guarantees all 240 keys. It prevents a common-subset result from silently replacing the registered sample.
- Actual wins are counted with `result == 1`; draws and losses remain separate. Replacing `result` with the binary actual-win indicator before `compare_results` correctly makes the reported comparison an actual-win-rate difference.
- `compare_results` joins opponent/map/side, averages the paired differences over both sides per map, and resamples 60 whole-map differences with replacement. It uses 5,000 draws, `default_rng(0)` freshly for each comparison, and 2.5/97.5 percentiles. This implements the specified paired-map interval; it is conditional on these fixed trained agents and reused development maps.
- Advancement requires all three fixed criteria: at least 108 Solution_92 wins, strictly more Solution_92 wins than PPO60, and 120 default wins. It does not infer strength from training `wr_*`, select a different historical/intermediate checkpoint, or add a post-hoc CI requirement to development.

## Training verifier

The core correctly requires no active registered job and successful training with post-job hash verification; ten ordered rows and 24 games each; positive unit-step counts; finite required training fields and expected missing teacher results. It compares original iteration 60 with final/current iteration 10, unchanged architecture, matching policy keys, finite final tensors, equality to the latest policy, and at least one changed tensor. The actual `PPOAgent(..., train=False)` load is checked for exact policy and effective config plus disabled sampling/training. Root should execute this once, alone, after the trainer exits.

`AgentConfig.from_dict(start['cfg'])` followed by `buffer_capacity=1` is the correct effective-config normalization. It includes newly defaulted fields such as `joint_moves=False`, while checking that saved final/current configuration equals the effective original. This is not a newly enabled coordination behavior. Architecture, tensor-finiteness and loaded-policy identity remain unexecuted checks in this static review.

Before final verification, also assert `stage == 'ppo'` for start/final/current, feature dimension 79 for current as well as start/final, no nonempty ensemble in any checkpoint and no loaded `extra_nets`, and exact loaded policy key set/architecture. The reviewed save path writes one policy, so these close metadata/identity checks rather than indicate a suspected extra model. Require nonnegative/positive time fields and `wr_sol92`, `wr_default`, `clipfrac` in [0,1]; retain the allowed `wr_teacher=nan`. Verify recorded training elapsed time against the fixed cap and deadline, and include the training CSV hash in the report so the final evidence is bound to the rows checked. Do not claim restoration of historical optimizer state: the existing fresh-Adam wording is correct.

After the corrections, reread changed helper sections and confirm archive equality. The final-data review remains separate: this precheck does not certify completed training, checkpoint validity, evaluated candidate strength or any deployment gate.
