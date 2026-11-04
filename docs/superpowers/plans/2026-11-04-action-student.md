# Action student implementation plan

Spec: `docs/superpowers/specs/2026-11-04-action-student-design.md`. Execute with subagents and independent review; user approved all three steps and autonomous publication. No renewed approval needed.

## Global Constraints

Worktree `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15`, Python `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`. Finish by18Berlin; modelstop17:40. Two one-thread model workers maximum. No runtime-agent/default changes or promoted weights. Inputs immutable, exact protected hashes, no existing-output overwrite. Root owns real jobs, Git, integration and docs. No worker subagents or production jobs. Historical data remain intact. Fresh status/manifest must distinguish incomplete from completed.

## Review Focus

Exact copied Q hook before numpy masking mutation; current masks rather than next-step masks. Final canonical/world actions distinct from masked argmax. Whole-map split consistent across rounds; no diagnostic rows used for scale/fitting. Constant teacher-only scale and numerical stability, one-action rows. Manifest-bound RL seed everywhere including replay proofs. Single-net reload/finite outputs and deadline/exception paths. Focused meaningful tests, no need repeat unrelated historical suite.

### Task 1: Exact student-state collector

Files: new `scripts/student_collect.py`, `tests/test_student_collect.py`. Read relevant spec data section. Interface CLI `--student PATH --out DIR --seed-start 865100 --maps 30 --deadline-utc ISO`. `collect(student,out,seed_start,maps,deadline)` outputs `dataset.npz`, `manifest.json`, `games.jsonl`, `status.json`. Production maps30; tests may pass5 so one whole map diagnosis by last1/6 fraction, at least1; production last5 diagnostic maps. Output field contract verbatim in spec. Use scripts.common play_game, make_opponent, pinned teacher loader/mean from student_distill, V13 self opponent. Network hook only active collector instance, immediate numpy copies, match saved_prev fields, remove in finally. Copy final world actions and mirror movement direction back when needed. Dataset teacher labels in batches after games. Copy/retain all finite rows, count reset/no-unit/no-network steps. Act wrapper checks deadline each step; no partial dataset success. Reject occupied/protected outputs. Pin all dependencies/input/source/protected before/after, real load exactly one512net, no learning/save/optimizer mutation.

- [ ] Implement meaningful synthetic hook/mask/action tests and output/split guards, verify failure then success. Test no accidental mutation from CPU numpy alias.
- [ ] Implement collector and provide report with exact API, tests/limits. No commits or production games.

### Task 2: Masked action distillation and calibration

Files: new `scripts/student_action_distill.py`, `tests/test_student_action_distill.py`. CLI `--student PATH --datasets DIR [DIR ...] --out DIR --deadline-utc ISO`. Each DIR is a complete Task1dataset/manifest; validate status, hashes and array schemas before training. Expose loss/scale/metrics helpers for unit tests. Use exact loss and schedule from spec. Initialize from supplied S30/A1; fixed30action epochs then5value-only epochs; train only is_train, use teacher RMS across all legal trainentries for one global scale. Adam1e-4/batch1024/seed20261104, export final-only one-net contract compatible with student_reward_train `_student`. Datasetcollection rounds may share maps but must same split assignments. Sidecars record cumulative true update counts, startinginputhash, codepins, split, objective/scale, phasecounts, before/after masked agreement/legalregret/Qerror and ruleoverride metrics based on recorded collectoractions. Do not mislabel these as replayed newfinalpolicy actions. Verify calibration by unchanged body/adv tensors and numerical action-rank checks. Exact Agent_x reload noextra_q. Deadline nofinalcheckpoint on partial phases.

- [ ] Synthetic tests illegal perturbation/constantshift invariance, onelegalfinitezero, rankingerror, scaleusestrainonly, no teachergrad; schema/split/protected-output/partial refusal and headfreeze/compatibleexport checks.
- [ ] Implement + report evidence; no commits/jobs. Task1producer contract is above; do not import collector mutable internals.

### Task 3: Independent RL starts

Files: modify only `scripts/student_reward_train.py`, `tests/test_student_reward_train.py`. Add optional run_seed to prepare CLI/API default29; manifest stores/validates integer0..1000; runtime derives seed from prepared manifest. Preserve fixed counts40/160/32 and offset3000, all existing proof requirements. rollout_plan accepts seed default29. Use manifest seed consistently in learnerconstruction, finetune CLI, expectedopponent/mapplans, receipt verification. No process-global mutation to change seed. Legacy default manifest may be supported explicitly or rejected clearly, but never rewrite it. The newactionstudent remains exact existing checkpoint contract.

- [ ] Meaningful tests seeds31/32 distinct schedules, withinpairidenticalplans, configsdifferonlySAP, malformed/tamperedseed rejected; olddefaulttests retained.
- [ ] Implement/report; no commits/jobs.

### Task 4: Execute, audit, compare, publish

- [ ] Root technical realcollection observer/noobserver equivalence and timing; independent code review. Fixed two collection/fitting rounds then four RLarms when runtimefits, two modelworkers maximum, sources frozen perphase.
- [ ] Independent artifact/model/data checks. Fixed two ensembles only; plan/pins before freshgames. Seedinventory and measured fullphaseadmission. Compare all completed roles honestly, mark missing stages if deadlineprevents fullprotocol, no improvisation frompartialoutcomes.
- [ ] Statistical whole-card crosscheck and finalbranchreview; report forMahmoud, updateREADME/workstatus/protocol; meaningfulcommits/safemainpush. HashV14/ZIP, stopownjobs/watch, leaveforeignchanges. No promotion absentfullindependentqualification.
