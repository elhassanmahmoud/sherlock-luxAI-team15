# Artillery comparison — independent static review

Reviewed the staged five-file adapter against the approved `/tmp/artillery-performance-adapter-plan.md`, live artillery training spec, fixed comparison-sizing note, actual training/supervisor schemas, existing Fog adapters, shared executor/statistics helpers, acceptance schema templates, and implementation report.

**Result: Spec BLOCKED / Quality BLOCKED by one actionable finding below.** Apart from that finding, static Spec/Quality PASS is conditional on focused tests after the freeze and real acceptance/hash bindings. This is not runtime, model, training-data, seed-freshness, or performance acceptance.

## Finding

### [P1] Enforce the registered canonical Artillery STOP path

**Path/lines:** `/tmp/artillery-comparison-staging/scripts/artillery_alignment_eval.py:34–36` (`checked_stop`); also callers at 103, 253–254, and CLI overrides at 301/307/309.

`checked_stop` only validates a path's syntax/symlinks; it never requires equality to `STOP_FILE`. Consequently `start --stop-file /some/other/STOP` checks and records that other path, even if the canonical Artillery STOP already exists. A later ordinary `stop` call or the operator's registered canonical STOP then has no effect on that run. This conflicts with the explicitly fixed own canonical STOP and can leave two resource-consuming workers running after the intended stop signal. The training supervisor already enforces its canonical path. Root confirmed that a custom comparison STOP is not intended.

Require the resolved safe path to equal the canonical study `STOP_FILE` before admission/start and in the stop command. Keep the existing symlink rejection. Tests may monkeypatch the canonical module constant to a temporary location; production callers must not silently select a different STOP. Add focused cases rejecting a noncanonical path and showing that an existing canonical STOP blocks start even when an alternate path is supplied; retain symlink/owned-cleanup coverage. Existing fixture `make_state` at test lines 293–298 deliberately passes an arbitrary temporary STOP and needs adjustment with that regression.

## Reviewed behavior with no additional blocking finding

- Actual artillery receipts are read as `eligible=False` plus exact nine-name `artifacts`, including buffer/events. No Fog `eligible=True`, `smoke`, or legacy hash fields are assumed. Prepared starts/global/local manifests, pair evidence, final supervisor receipts/exit state, protected V14/ZIP, independent `PASS_DATA_ONLY` audit, and separate original root-validator proof are hash-bound. Historical roots are rebased without permitting missing files. The templates match the reader.
- `ACCEPTANCE_SHA256=None` and `SEED_ACCEPTANCE_SHA256=None` intentionally fail closed. The real training HEAD is pinned to `02ce1b2ce9a5b0780da1ee6462a2368b2226d495`; historical validation is kept distinct from the comparison HEAD. Actual root tensor/Adam/reload validation must still occur before historical acceptance. `PASS_DATA_ONLY` is not represented as such validation.
- Builder retains original 36 members, appends only final 43 then 44 Q states for the fixed role, uniform 38, exact effective V14 inference config, both new training flags False, finite/strict state checks and reload identity. Training config is checked independently; exclusive output and final input rechecks are present.
- Four exact 20-map lists and full role/job plan equality yield 11×40=440 selection and 15×40=600 confirmation. LOCAL_SIX is the correct panel. No third confirmation role, extra keys/jobs, substitute seeds, or automatic resumption is admitted.
- Selection uses integer half-wins, all five fixed gates, deterministic rank stages, and CONTROL38 tie-break. Confirmation delegates the unchanged seven gates and adds the existing three protections; panel size is 240/model and the strict default gate requires 40/40. ALIGNED−CONTROL remains descriptive.
- Entire CSV/receipt/command/input matrix is checked before statistics; shared helpers perform whole-map paired bootstrap, 5000 draws, seed 0, percentile intervals. Both phases bind all four lists, freshness evidence, models/opponents, spec/plan/sizing and source. Confirmation re-runs full selected evidence admission, including its independent summary acceptance and original source check.
- New modules do not alter old Fog constants/profiles. Shared queue guard wrapping is temporary and restored. Existing shared lock, AC check, strict <100% fresh quota, foreign-process check, maximum two owned workers, and group ownership cleanup are retained. No promotion action is added.
- Synthetic coverage includes major receipt/config/hash/matrix corruption paths, candidate order/NaN checks, ranking boundaries, both-phase freezing, missing selection bindings, third worker rejection, relative/absolute analysis paths, and old-profile preservation. It has not been executed, so no passing-test claim is made.

## Evidence and limits

Actual work was read-only shell inspection, diffs, line-numbered reads and SHA256 checks. **No Python, tests, model imports, games, repository edits, Git mutations, commits, or pushes were performed.** Only this review report was written.

Reviewed code hashes (match the implementation handoff):

- compare: `2e5606805e49e766ea3b14871a3a1930e02187d6b6ee40a74254f5a3e2f028e1`
- eval: `82a5c1f9566e9662f939e80f31c44ba90724272a72766f7c9a17cc5be8b026eb`
- tests: `abc0eb00f5cd66f61051c81fc970b5edc93992e239809340f03988a53044d83b`

Spec/plan hashes changed after the implementation handoff while Root requested an explicit local-buffer portability note; their current hashes are `e3f0604189466b0fc41e738baea79fc295692ea15c3bb61c7fb51295b9905fdb` and `38560693b04c238b7e1c8aa2bd256a75bc29060f27a814931616ac03a6dd397b`. The required buffers remaining local is a documented portability constraint, not a reason to waive their bindings.

After the narrow STOP fix: re-review its diff, run the appropriate focused synthetic and existing shared/Fog checks once model jobs have ended, pin actual historical/freshness acceptances, and perform real assembly/reload/admission before any performance start. V14 remains unchanged; no strength or promotion conclusion follows from this review.
