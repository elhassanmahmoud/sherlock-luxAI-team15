# Resume fixed ensemble study with the user-authorized account budget

## Authority and scope

On08.11 Moayed explicitly answered: "Nein, für diesen Auftrag das restliche Kontingent nutzen". This supersedes the previous30% reserve for this task only. No reset authorization. Six trained arms and four built candidates are already complete/audited; never retrain or modify them. Selection/confirmation thresholds, candidates, seeds, rule/reward behavior and V14/ZIP remain unchanged.

## Design and global constraints

Expose an explicit `--max-used-percent` controller option, default65, with this task launched at100. Persist it in the evaluation state; validate finite numeric 0<cap<=100 (booleans invalid). Usage receipts remain fresh/known/ordinary-allowed, and usedPercent must be strictly below the selectedcap. All other safeguards remain. Ordinary usage disallowed, exhausted, unknown or stale means controlled stop. Use no reset. Older controller states missing thefield retain65. No active model jobs now; finish all tests before selection. Existing isolated worktree is suitable; no new worktree needed.

### Task1: Explicit authorized quota ceiling

Files: scripts/ensemble_diversity_eval_supervisor.py and tests/test_ensemble_diversity_eval_supervisor.py only. Baseline c624b099b875a318cb4626e5ab95fe2355ce00a0. Read this brief first; it is the requirements.

1. TDD: Default65 continues rejecting65; explicit100 accepts65 and99 but rejects100; invalidcaps bool,zero,negative,NaN,infinity,>100 rejected. Freshness/disallowed checks cannotbe bypassed by a highcap. Tests for state/guard forwarding and CLI wiring as appropriate.
2. Add optional keyword max_used_percent=65 to check_usage/build_state/run_supervisor; propagate CLI float option through launch/state/guard. guard legacy absentfield defaults65. Ensure selectedcap visible in persistent state; launch arguments/state binding remain auditable.
3. Focused pytest for changedcontroller; no games. Use /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python. Do not weaken existing sources/model/CSV/provenance/power checks. No changes to shared modelsource, statistics, protectedweights, trainedartifacts or selectionplan.
4. Commit only ownedcode/tests after red/green and selfreview. Report concise evidence and limitations to workspace task1-report.md. No subagents or new experiments.

## Root follow-through

Independently review the narrow change, verify relevant existing tests, record revised budget policy in shared docs and recurring remote-sync prompt. Push and synchronize current main before new source freeze. Refresh fresh usage receipt, power and ownedprocess evidence, verify admitted weights unchanged. Run exactly39 selectionjobs/7800games with max-used-percent100; no paralleltests and atmosttwo modelworkers. Monitor GitHub/quota/power with subagent; keep study HEAD frozen through optionalconfirmation. Analyze all complete results, independently audit; nominate atmostone according to pre-existing rules. Only ifqualified, run one23200gameconfirmation and independentaudit. No replacement absent allgates plus course/runtime/reproduction/backupchecks. Preserve partials and report failures honestly.
