# Conditional P installer: offline handoff

Prepared only; no actual study bundle has been opened by this helper, no model
was imported/executed, no release was installed, no repository was modified.
Independent code review is pending at the hashes below. A passed synthetic test
is not P performance eligibility or technical model QC.

Files:

- `/tmp/sherlock-continue-20261102/install_qualified_P.py`
- `/tmp/sherlock-continue-20261102/test_install_qualified_P.py`
- Approved input/schema design: `/tmp/P_release_installer_design.md`

Reviewed-candidate installer SHA256:
`87c3f94cc050a7dba7701f997b9a7067e924a76aba2b4ef28a7aa46e953ea2d2`

Synthetic test SHA256:
`64ae19607e5aa1960ddfbf84a7a9fd6d5932c10bc7ce7f15b987b9b1685b6b7f`

## Exact later CLI; none executed here

```sh
python3 -B /tmp/sherlock-continue-20261102/install_qualified_P.py check \
  --bundle /absolute/root_release_bundle.json
```

Read-only structured evidence/byte check. It invokes no legacy release parser,
model, runner, builder, bootstrap implementation or other project module. It
checks the real Root/independent audit schemas and the fixed P-only plan/CSV/
numeric gates, complete3000/9000 and shared03e archive. Missing or failed gates,
incomplete/non-ACCEPTED evidence, absent3.10 actual QC or changed bytes reject.

Only after actual independent performance and technical acceptance, closed source
freeze, quiet locks/readers/writers and a fresh Root authorization:

```sh
python3 -B /tmp/sherlock-continue-20261102/install_qualified_P.py install \
  --bundle /absolute/root_release_bundle.json \
  --authorization /absolute/root_install_authorization.json \
  --transaction /absolute/NEW_release_transaction --install
```

The authorization contains exactly the design's required verdict/bundle SHA/
target root/expected full target HEAD, actual issued/expires Unix seconds with
maximum600s lifetime, `readers_stopped=true`, `writers_stopped=true`, `model_jobs=0`.
The input bundle and the independent technical adapter fields are specified in
the approved design. Both active files receive the unchanged fixed raw-P bytes;
the separately supplied verified ZIP has `cfg.frozen=True`. This installer never
edits checkpoints or builds a ZIP.

## Failure and recovery

The transaction directory must be new. Its backup is immutable copied old p0,
old p1, old ZIP and a hash-bound manifest. Existing transaction/backup reuse is
refused; no blind skip. New/rollback copies are fsynced on each target filesystem.
Per-file intents precede the namespace operations. Individual publication uses
an atomic no-overwrite link after moving the old file to an owned holding name.
Three-file publication is **not simultaneous atomicity**: readers/writers must
actually be stopped. Hash/inode checks and rollback preserve unexpected foreign
files instead of overwriting them.

The persistent marker is
`TARGET_ROOT/agents/sherlock/weights/.P_release_pending.json`. It blocks any new
release while an earlier prepared, crashed or conflicting transaction is open,
even if all three targets still have their old bytes. Do not manually delete it
to retry. Successful commit or verified complete rollback removes its own marker.

Handled HUP/INT/TERM and ordinary failures attempt rollback and preserve failure
history. SIGKILL/power loss requires separately authorized recovery:

```sh
python3 -B /tmp/sherlock-continue-20261102/install_qualified_P.py recover \
  --transaction /absolute/existing_release_transaction \
  --authorization /absolute/root_recovery_authorization.json --recover
```

Recovery authorization requires verdict `AUTHORIZED_P_RECOVERY`, exact canonical
transaction path, current `journal_sha256`, fresh issued/expires seconds and the
same quiet reader/writer/model declarations. Recovery validates the exact current
helper SHA, journal paths/identity, old backup/manifest, historical authorization,
bundle and all evidence. It only rolls back; it never resumes installation.

Historical evidence naming an active target is checked through its verified OLD
backup, so a missing/owned-new target does not incorrectly fail the normal old-
target guard. A crash before the backup manifest was sealed is recoverable only
when no mutation entries exist and all live targets are still the original OLD
files. A foreign target yields `rollback_conflict`, stays intact and keeps the
pending marker; Root must resolve the exact reported path before another release.
Do not treat a conflict or exception as installation success.

## Actual offline tests

```sh
python3 -B /tmp/sherlock-continue-20261102/test_install_qualified_P.py
```

19/19 passed in3.563s. Fixtures use small synthetic bytes/ZIPs, complete synthetic
3000/9000 CSV/JSON chains, and patched synthetic constants. Production offers no
hash override flags. Actual root hashes/HEADs/models/study outcomes are never
used in the synthetic suite.

Coverage includes successful full installation and immutable backup; all seven
numeric gates; changed summary/CSV/state/master/audit bytes; missing3.10/tensor/
frozen-mode proof; explicit switch/fresh authorization; failure after each of
three publications; handled signal/handler restoration; two foreign-writer
cases; pending and foreign receipts; lock denial; target symlink/hardlink refusal;
owned-new/missing-target recovery with historical active-file evidence; recovery
before the backup seal; exact worker weights/flags/command; inline `check_battle`
and external `verify_P_package.py` process exclusion; no model-stack imports.

RED evidence is retained in `P_installer_RED_missing.log`,
`P_installer_RED_recovery.log` and `P_installer_RED_fixedjobs.log`; final focused
test output is `P_installer_GREEN.log`. No full repository suite or real install,
signal kill, model, ZIP-builder or course-runner test was run.
