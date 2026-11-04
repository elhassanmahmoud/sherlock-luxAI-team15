# Independent RL training audit

Status: **PASSED**.

Checks: 94/94 passed.

Read-only inspection of actual raw rollout/validation rows, optimizer state, checkpoints and frozen hashes. No games or training performed by this audit. Known-card validation is not evidence of generalization or superiority.

## control

40 prefill + 160 learning games; 32 known validation games; 24000 Adam updates; env_steps=120600. Q tensors changed: True.

| Phase | SAP transitions | Removed signed | Removed absolute | Positive→nonpositive | Actual reward |
|---|---:|---:|---:|---:|---:|
| prefill | 3108 | 898.200000 | 1240.200000 | 337 | 48438.247875 |
| train | 12477 | 3807.600000 | 4931.400000 | 2266 | 196363.865042 |

Checkpoint SHA256: `c5df4fa5accbf110af590fce36ed1786f4fcea9022c603eae1b0d0995c3693b9`

## sap0

40 prefill + 160 learning games; 32 known validation games; 24000 Adam updates; env_steps=120600. Q tensors changed: True.

| Phase | SAP transitions | Removed signed | Removed absolute | Positive→nonpositive | Actual reward |
|---|---:|---:|---:|---:|---:|
| prefill | 3108 | 898.200000 | 1240.200000 | 337 | 47540.047875 |
| train | 9527 | 2799.900000 | 3890.700000 | 1205 | 191571.185000 |

Checkpoint SHA256: `900c420a67ecada72c9252964edc953100569fbff037490e1a7aa97ace89c31f`

## Findings

No technical discrepancies found.

Reload scope: independently strictly reloaded Q and target into QNet and checked exact tensor hashes; also inspected recorded live Agent_x reload identity proof. Validation isolation and action/replay agreement are runtime audit evidence, cross-checked against raw rows, not reconstructed environment games.

## Frozen artifacts and operational timing

Audited commit: `5b9f8836fb94c21a9cdbe07f49fb091a19de8426`. Source and protected hashes matched all prepared pins.

- control: `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/runs/20261104_student_reward30/runs/control/weights/agent.pth`
- sap0: `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/runs/20261104_student_reward30/runs/sap0/weights/agent.pth`

The coordinator recorded SIGSTOP/SIGCONT of its SAP0 worker from13:34:02.352150 to13:34:55.226684UTC to avoid the independently reviewed final-receipt/status publication interleaving. The recorded resume completed; both final artifacts pass after completion. This operational stagger did not alter the frozen source; artifact/source integrity and complete training chronology were independently checked. The artifact PASS does not claim that the original concurrent publication implementation was race-free.

Identical prefill action/feature-state transcripts accompany898.2 less actual aggregate reward in SAP0, exactly matching the removed signed SAP term. Genuine training occurred in both arms: final Q tensors changed and all saved Adam parameter states reached24,000 updates with finite moments, consistent with raw game chronology. Counterfactual exposure measures the intervention, and training/known-validation results do not establish superiority or unseen-map strength.
