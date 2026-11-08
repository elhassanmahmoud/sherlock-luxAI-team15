# Artillery comparison adapter — staging handoff

Status: staged for independent read-only review, NOT executed or admitted. Repository remained frozen at 02ce1b2ce9a5b0780da1ee6462a2368b2226d495. No repository writes, Python execution, model imports, tests, games, commits, pushes or Git mutation were performed by this agent.

## Deliverables to review and later copy

All repository-relative destination paths are under `/tmp/artillery-comparison-staging/`:

| File | SHA256 at handoff |
| --- | --- |
| scripts/artillery_alignment_compare.py | 2e5606805e49e766ea3b14871a3a1930e02187d6b6ee40a74254f5a3e2f028e1 |
| scripts/artillery_alignment_eval.py | 98a2adc7a19d8b2efaecaa242dd227702f9348ea40504480e950d727feced793 |
| tests/test_artillery_alignment_compare.py | fc9bd1716ec438e6420e7988ef4092fc5eb3c51ec3670fe8e3189ddc59d4fec1 |
| docs/superpowers/specs/2026-11-08-artillery-comparison.md | e3f0604189466b0fc41e738baea79fc295692ea15c3bb61c7fb51295b9905fdb |
| docs/superpowers/plans/2026-11-08-artillery-comparison.md | 38560693b04c238b7e1c8aa2bd256a75bc29060f27a814931616ac03a6dd397b |

Auxiliary, not proposed repository files: `/tmp/artillery-training-acceptance-schema.json`, `/tmp/artillery-training-root-validation-schema.json`; staging also contains a copy `training-acceptance-schema.json`. These are schema templates with explicit placeholders, never real acceptance or hashes.

## Behavior and scope

- Narrow new adapters follow the existing Fog compare/eval pattern. Shared historical_path/checked_checkpoint, LOCAL_SIX/statistical helpers, confirm_checks and queue/receipt/resource safeguards are reused. No changes to old profiles/constants, agent, trainer or shared gates. Runtime guard wrapping is the existing temporary shared-queue pattern and restores the prior guard; no Fog profile globals are reassigned.
- Exact V14/CONTROL38/ALIGNED38 roles; original36 + final control43/44 or aligned43/44, ordered and uniform38. Original effective V14 inference cfg, both training flags False. Final single-network cfg differs only by aligned artillery flag on top of fixed training overrides. Strict finite/load/member/reload/exclusive output checks retained.
- Historical training uses actual artillery receipt schema: schema1/statusdone/eligibleFalse/artifacts with all nine names. It binds prepared global/local manifests/startweights and launch, complete supervisor, both pair gates and their proof hashes, independent PASS_DATA_ONLY/source_head report, and root validator per-arm actual receipt hash/env_steps193320/learn_steps60000.
- Acceptance schema approved by Root and coordinated with data auditor. `totals` uses actual_prefill_games160/actual_train_games1600/actual_validation_games128/executions1888/learn_steps240000. Arm counts adds executions472 to actual40/400/32, learn_steps60000, env_steps193320.
- Actual historical acceptance SHA remains None: require blocks candidate build before imports/loading. Training HEAD is verified full actual02ce1b2 SHA. Historical source identity stays historical and root rebasing does not waive missing artifacts.
- Replaybuffers (approximately187MB per arm) remain ignored and MUST NOT be added to Git. Models and compact raw evidence can be versioned; a pull alone cannot reproduce the full raw audit in the primary/Mahmoud checkout. Original buffers must be transferred separately and hash-verified there. Rebased reads fail closed when any is missing; no blanket artifact-portability claim is made.
- Seed acceptance SHA remains None: real comparison start fails until the new target-specific audit is accepted/pinned. Narrow schema: seed acceptance schema1/statusPASS/profile/cohorts/audit{path,sha256}; root audit statusPASS/no_observed_conflictsTrue/nonempty limitations/raw_audit{path,sha256}; optional files map binds additional raw evidence. All references repository-relative, all four20-seed lists bind in both phases.
- Exact prospective blocks 9800000–19, 9800100–19, 9801000–19, 9801100–19 fixed in code/spec/plan. 440 selection, conditional600 confirmation, LOCAL_SIX, same integer score/strict-win selection thresholds/ranking and seven+three confirmation gates. Default confirmation40/40, panel240/model. ALIGNED-minus-CONTROL descriptive only.
- Whole selection evidence revalidated before confirmation; both phases bind same source identity, all models, opponents, all four lists, spec/plan/sizing and acceptance proofs. Existing two-worker, quota, AC, STOP, lock, foreign-process and owned-cleanup behavior. No restart or nominee replacement.

## Actual verification and limitations

Tests were staged first, before production staging. No RED, GREEN, syntax compile, import, pytest, torch or game was run because Root explicitly prohibited any Python/tests/models while workers are active. Thus there is no passing-test or executable-completeness claim. Root must run the focused synthetic suite after the freeze, plus appropriate existing shared/Fog checks and independent review.

Read-only static checks performed:

- Read project rules/current work status, accepted adapter plan, fixed training spec, comparison sizing, old adapters/tests, actual artillery receipt/supervisor schema and actual prepared manifest metadata.
- Confirmed actual full source HEAD and actual prepared pins/source/config key shapes with read-only Git/jq.
- Inspected staged code/text for copied historical names/seeds/gates. Remaining Fog references are intentional shared helpers and old-profile regression assertions.
- `git diff --no-index --check /dev/null <file>` on each of five deliverables emitted no whitespace diagnostics. Each returned1 because no-index compares a new file to empty; these were static diff checks, not test passes.
- SHA256 recorded for all five staged deliverables above.

Tests include exact440/600 matrices, all role/rank thresholds, old Fog constants unchanged, raw/receipt/source corruption before stats, root rebasing, actual eligibleFalse artifact shape, missing buffer/events/prepared/pair/root/audit evidence, inconsistent historical cfg/counters, unpinned trust anchors, freshness acceptance rejection, all-phase list/sizing freezing, candidate order/config/NaN/member errors, third worker rejection, relative/absolute API/CLI paths, STOP/AC/quota/foreign-process behavior and conditional confirmation with exactly10 gates. These tests are UNRUN.

## Remaining Root-controlled steps

1. Keep all staged files outside repository until all training workers/supervisor are complete and training data/Tensor/Adam/Reload validators are accepted on the original source.
2. Archive independent/root proofs, create the exclusive historical acceptance using templates and real hashes. Set actual ACCEPTANCE_SHA256.
3. Finish target-specific freshness scan, record limitations/root acceptance, bind actual raw report(s), pin SEED_ACCEPTANCE_SHA256. Both None placeholders intentionally block.
4. Copy only the five intended files after the freeze, run actual focused synthetic checks and independent review; fix reported errors without asserting pre-run success.
5. Build/reload/validate real candidate artifacts, prepare exact lists/plans, review admission and freeze the new source through selection and optional confirmation.
6. Update Arbeitsstand/Experimentprotokoll only after completed work; no such repository documentation was touched in this staging subtask.

## Fix round1 — canonical STOP (independent review P1)

The independent static review found that a caller could override STOP with another safe path, bypassing the registered canonical stop signal. Root confirmed custom STOP paths are not intended. Scoped fix changes only staged eval/tests and this report:

- `checked_stop` first applies the existing safe-path/symlink checks, then requires exact equality to the module's canonical STOP_FILE. All start/admission/stop callers already use this function, so alternate paths are rejected rather than registered.
- Synthetic test cases were written before the production edit: canonical path accepted, another safe path rejected, existing canonical STOP stops run_supervisor before admission/launch, and alternate path cannot bypass it. Existing symlink rejection remains. The synthetic artifact fixture explicitly monkeypatches STOP_FILE to its isolated temporary path so ordinary fixture states use the same canonical contract.
- No comparison method, role, seed, gate, other adapter, spec or plan changed. Compare/spec/plan SHA256s reconfirmed unchanged.
- Actual verification: scoped source read and SHA256, plus no-index whitespace checks for the two changed files with no diagnostics (exit1 reflects new files versus empty). No Python, imports, tests or games executed; both new tests and existing suite remain UNRUN pending training freeze end. No runtime success is claimed. Independent scoped re-review is requested before later actual tests.

Updated eval SHA256: 98a2adc7a19d8b2efaecaa242dd227702f9348ea40504480e950d727feced793.
Updated tests SHA256: fc9bd1716ec438e6420e7988ef4092fc5eb3c51ec3670fe8e3189ddc59d4fec1.
