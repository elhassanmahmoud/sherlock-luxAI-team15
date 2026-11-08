# Artillery comparison — fix round 1 static re-review

**Spec PASS / Quality PASS for the narrow fix.** The prior P1 canonical STOP finding is resolved in the reviewed staging. No remaining blocking findings from the original review or this scoped re-review. This remains conditional static acceptance, not permission to execute before the training freeze ends or evidence of passing tests.

## Fix checked

`scripts/artillery_alignment_eval.py:34–38` now applies the existing `safe_path` validation and then requires exact equality to the canonical module `STOP_FILE`. A different safe path fails with an explicit error. `safe_path` still rejects symlinks and hardlinked files before resolving the path; the definition canonicalizes only system tmp.

The three production routes use this check:

- `run_supervisor` lines 255–256 checks canonical identity and an existing STOP before model admission, handlers, locks, output creation, or launch.
- `build_state` line 105 records only a checked canonical path.
- CLI `stop` line 311 checks the same path before requesting STOP; CLI `start` routes through `run_supervisor`.

The two new synthetic cases at test lines 97–114 check canonical acceptance/noncanonical rejection and an existing canonical STOP blocking the supervisor while an alternate path cannot bypass it. Their `build_state` sentinel makes an admission attempt fail loudly. The artifact fixture at line 133 patches the canonical constant to its isolated temporary STOP, matching the explicit path passed by `make_state`. The existing symlink case remains and the actual helper's symlink rejection was inspected. No default-argument mismatch affects these explicit test calls.

No comparison method, matrix, seeds, gates, acceptance schema, old profile, resource queue, or ownership cleanup change was introduced by the fix. Compare/spec/plan hashes still match the previous reviewed values.

## Reviewed hashes

- eval: `98a2adc7a19d8b2efaecaa242dd227702f9348ea40504480e950d727feced793`
- tests: `fc9bd1716ec438e6420e7988ef4092fc5eb3c51ec3670fe8e3189ddc59d4fec1`
- compare unchanged: `2e5606805e49e766ea3b14871a3a1930e02187d6b6ee40a74254f5a3e2f028e1`
- spec unchanged: `e3f0604189466b0fc41e738baea79fc295692ea15c3bb61c7fb51295b9905fdb`
- plan unchanged: `38560693b04c238b7e1c8aa2bd256a75bc29060f27a814931616ac03a6dd397b`

## Actual checks and remaining boundary

Performed only line-numbered source/test/helper reads, a read-only diff against the existing adapter, implementation-report comparison and SHA256 checks. **No Python, imports, tests, models, games, repository writes, or Git mutation.** Only this `/tmp` re-review report was written.

Focused synthetic tests and appropriate shared/Fog regression checks remain UNRUN and must pass after training ends. Actual historical/root tensor validation, acceptance hashes, fresh-seed acceptance, real candidate assembly/reload/admission and the final source freeze remain required before performance execution. The `None` acceptance pins continue to fail closed. V14 remains unchanged; this review makes no strength/promotion claim.
