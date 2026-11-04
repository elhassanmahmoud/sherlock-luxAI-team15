# Fixed A2-anchor diagnostic admission preparation

Prepared `/tmp/sherlock-a2-anchor-20261104/prepare_diagnostic.py` only. SHA-256: `56b457344961f7149fed33a178857408be8a2bb933f94c911204f24bb32e84de`.

Verification actually performed: Python AST syntax parse of the final helper, static comparison with the fixed specification, current admission/manifests and receipt producer, existing controller, prior completed action-student state/guard schema and data-auditor contract. The helper was **not executed**. No models loaded, Torch imported, inference, tests, games, training, repository/source/HEAD edits, candidate copying, or commits performed. Only this report and the helper were written.

## Fixed scope and outputs when later admitted

- Exact source `09c69349afc020a7b2418c249657a5698c472964` required throughout preparation and controller execution.
- Six roles in order: V14, A2, CONTROL25, CONTROL26, ANCHOR25, ANCHOR26. V14 and A2 retain their original paths. Only four exact outer-receipt final checkpoints are copied to `experiments/candidates/a2_anchor_20261104/{ROLE}.pth`; no ensembles, checkpoint selection, or overwrite permitted.
- Portable provenance at candidate `manifest.json`, `/tmp/.../role_manifest.json`, and diagnostic archive `role_manifest.json`; all copies hash-pinned.
- Six panel jobs: 20 cards 867000–867019, both sides, Solution/default/V13 = 720 games. Five direct jobs: cards 867100–867119, both sides, V14 opponent = 200 games. Total 11 jobs and 920 games, fixed order consumed directly by the existing `run_diagnostic.py`.
- Protocol `/tmp/sherlock-a2-anchor-20261104/diagnostic_protocol.json`, identical archived copy under `experiments/analysis/a2_anchor_20261104/diagnostic/`.
- Seeds, role manifest, runtime admission, helper/controller/guard, independent results auditor, independent learning auditor and audit, crosscheck helper and training admission copied into that new archive. Existing archives and outputs are never overwritten.
- All tracked Python files and all `.py` in agents/scripts/lux are pinned; original training source hashes must match. Inputs bind learning datasets, manifests, outer/inner receipts and evidence, all four final checkpoints and copies, protected worktree/primary weights and ZIP, Python binary, installed engine `.py`, dependency versions, seeds, helpers, auditors, historical timing CSV/state/guards, seed inventory and spec. Each pin remains immutable through all controller jobs.
- Statistical protocol fixes whole-card pairing, both sides/all panel opponents, 5,000 bootstrap draws with seed 0, exploratory 95% intervals; starts remain separate. It records exact ANCHOR qualification/ranking and forbids promotion from this diagnostic, ensembles, new hyperparameter search and fallback after failed confirmation.

## Independent completion contract

The learning auditor agent agreed this exact minimum for `/tmp/sherlock-a2-anchor-20261104/learning_completion_audit.json`:

```json
{
  "schema_version": 1,
  "status": "passed",
  "independent": true,
  "source_commit": "09c69349afc020a7b2418c249657a5698c472964",
  "auditor_script": "/tmp/sherlock-a2-anchor-20261104/learning_completion_auditor.py",
  "auditor_sha256": "<actual auditor hash>",
  "training_admission_sha256": "<actual admission hash>",
  "pair_prefill_equal": {"25": true, "26": true},
  "arms": {
    "CONTROL25": {
      "prepared": "<absolute seed25 prepared directory>",
      "receipt_sha256": "<outer anchor_receipt.json hash>",
      "checkpoint_sha256": "<outer final checkpoint hash>",
      "guard_sha256": "<completed seed25_control_guard.json hash>",
      "public_validate_passed": true,
      "independent_checks_passed": true
    },
    "CONTROL26": "<same fields with seed26/control>",
    "ANCHOR25": "<same fields with seed25/anchor plus anchor_active_verified=true>",
    "ANCHOR26": "<same fields with seed26/anchor plus anchor_active_verified=true>"
  }
}
```

The placeholder strings above illustrate the shape only; all four entries must be actual objects. Optional root `evidence_sha256` is an absolute file-path→hash map. The helper structurally/hash-checks the outer receipts, fixed final-only path, inner receipts/evidence/config/budgets/statuses itself. It requires the independent auditor's actual public `validate` pass rather than importing/executing that heavy validator again. Completed guards must attest exit 0 and the exact training command; their recorded guard PID, child PID and owned process group must be absent.

## Runtime admission and integration

Invoke only after all four arms and the independent completion audit actually pass, with current account/battery readings:

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B \
  /tmp/sherlock-a2-anchor-20261104/prepare_diagnostic.py \
  --data-ready --account-used-percent CURRENT --battery-percent CURRENT
```

Use numeric current values in place of CURRENT. Admission rejects account use >=65% or battery <35%. It reads timing/key fields only from the already completed action-student diagnostic. Per-opponent maxima across the earlier 512-wide single roles bound new single panels; V14 uses its earlier panel timing. Directs use the actually measured previous single-versus-V14 timings. Each class additionally takes the greater observed completed guard wall time. Bases receive 15% padding and 12s per job startup; a two-worker queue follows actual controller order. Full estimated completion must precede **2026-11-04 22:00 UTC / 23:00 Berlin** before any output mutation and again before protocol publication. There is no reduction or new game execution here.

The separate existing controller invocation is:

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B \
  /tmp/sherlock-a2-anchor-20261104/run_diagnostic.py \
  --protocol /tmp/sherlock-a2-anchor-20261104/diagnostic_protocol.json
```

Root retains responsibility for its guarded launch and current operational checks. Launch before the runtime record's `latest_estimated_launch_utc`; the controller itself only enforces the hard deadline, so do not leave an admitted protocol waiting and then launch after its estimate no longer fits. The runtime record includes the fixed model deadline and 23:20 Berlin closure target.

Unresolved integration is intentionally limited to live evidence: all four final outer receipts/completed guards, the independently passed audit with agreed fields, current account/battery readings, full-runtime fit, and the actual separate guarded launch. The helper assumes the same commands already used for seed25: relative `--prepared experiments/runs/20261104_a2_anchor/seed{25,26}`, public `--arm control|anchor`, and `--deadline-utc 2026-11-04T21:00:00Z`. Root should preserve that command shape for seed26. It refuses reused PID ambiguity, any existing preparation/candidate/diagnostic targets, changed pins and unresolved initial local inventory overlaps. Partial output on a later I/O/pin failure is preserved for explicit review, never deleted or retried automatically.

The existing local freshness inventory has documented seedless/external-trial limits; those remain in the protocol. It does not claim global freshness. Keep every pinned input, including archived admission files, immutable while the controller runs: it hashes all of them before every job. Actual results auditing and root crosscheck remain separate after the full 920 games complete.

## Pre-admission path integration correction

Minimally changed only the learning auditor identity comparison to compare resolved filesystem paths: macOS `/tmp/...` and `/private/tmp/...` now identify the same auditor. Exact auditor SHA-256 equality remains mandatory. Reviewed analogous audit binding comparisons: the per-arm prepared paths are under the `/Users/...` worktree, whose resolved spelling is identical; hash-only receipt/checkpoint/guard bindings require no path adjustment. No other contracts weakened. The updated helper was AST-parsed only; it was not executed, and no repository/source/HEAD/data changes or heavy checks were performed. Current helper SHA-256 is `56b457344961f7149fed33a178857408be8a2bb933f94c911204f24bb32e84de`. The independent auditor's current accepted hash remains checked at admission against its actual file bytes.
