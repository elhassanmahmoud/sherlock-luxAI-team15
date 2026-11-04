# Task2 fix-round-2 scoped review

**ADDRESSED / PASS.** The sparse legacy configuration admission finding is resolved. No material spec or code-quality findings in this narrow fix.

Independently verified frozen SHA256:
- `scripts/student_reward_train.py`: `b91a1149422273800c01cf7d65750d933c36dc8d7809e91ac8e264d3071c0213`
- `tests/test_student_reward_train.py`: `d2112d19fcb2e4b504db37c9de5fec1676226818445be2c4d7f7f7c361f25ada`

Reviewed `/tmp/sherlock-student-20261104/reward_fix2.diff`, the two changed files, relevant producer/consumer/live-learner integration, implementer report, actual S30 check JSON, and captured test log. No games, model loads, source edits, commits or subagents were performed by this reviewer.

## Spec and integration

`_student` now checks the full effective `AgentConfig(**cp['cfg']).to_dict()` without wrongly requiring sparse serialized keys to equal the expanded mapping. Returning `dict(cp, cfg=cfg)` changes only the loaded object. Every explicitly serialized override is passed into the dataclass, so defaults fill omissions without replacing nondefaults. Required architecture/schedule values, exact permitted checkpoint fields, provenance validation, finite tensors and q/target equality checks remain intact.

`prepare` and `check_prepared` both call this normalized consumer, so manifest source_config, per-arm saved init configs, expected state hashes and live variant registration consistently use the same effective config. The shallow return preserves tensors/provenance, and prepare subsequently deep-copies before changing the arm configuration. Source hashes still compare original file bytes before/after; neither normalization nor prepare writes the source. Only the previously specified common training overrides and arm SAP treatment alter the effective role configs.

The new regression executes the real tiny producer using a sparse teacher config and explicit nondefault reward/rescue flags, then checks `_student`, both prepared arms, actual `Learners`, and `prove_initial`. It also checks the source hash and serialized cfg remain unchanged. This directly covers sparse producer → preparation → live constructor agreement, rather than only a synthetic normalized dict.

## Evidence reviewed

Captured covering test log: **21 passed in8.28s**, exit0 reported, one CPU thread. The implementation report records the new regression failing before the change. No repeat was justified by a concrete concern.

Actual S30 admission evidence records72 raw keys →167 effective keys, all explicit overrides preserved, both arms with identical q/target tensor SHA `4b94c376e8e290e151d32397f4024a6c47aceab59d7e7751d8d6322af13b9a7e`, no optimizer/replay, and only `w_sap_hit` differing (0.3 versus0). S3/S30 before-and-after file hashes match. This is implementer-generated evidence read by this reviewer, not a separately repeated production-checkpoint load.

The correction is minimal and consistent with current AgentConfig semantics. It neither changes the immutable student checkpoint nor relaxes optimizer/replay/unknown-field exclusion. Previous review conclusions remain applicable outside this scoped change.
