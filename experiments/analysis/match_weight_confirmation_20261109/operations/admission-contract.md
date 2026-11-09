# MATCH38 confirmation admission contract

Implementation: `scripts.match_weight_confirmation` and `scripts.match_weight_confirmation_owner`.
No phase has been admitted or started by the implementer. The old Eval copies are not rebuilt or loaded here.

## New admission JSON

Common fields follow the existing owner contract:

- `schema_version: 1`, `profile: "match_weight_confirmation_20261109"`, `stage: "confirmation"`, `start_authorized: true`, `allow_battery: true`.
- `root`: physical absolute checkout path; it must also be the current directory.
- `python`: exact project-venv executable path used in the owner command.
- `out`: `<root>/experiments/analysis/match_weight_confirmation_20261109/confirmation_v1`; must not already exist at owner start.
- `plans`: union of historical selection plans and the new confirmation spec/plan, as Root proposed.
- `source`: current `source_identity(root, python, plans)`, including current HEAD, all current source files, physical executable/hash and interpreter path.
- `protected`: exact existing original V14 p0/p1 and Gruppe15.zip hash map.
- `inputs`: physical absolute path → SHA256 for every historical/new input described below, plus this new owner file. All old selection-admission inputs must remain an unchanged subset. Historical source files are checked through `source.files`, not required a second time in `inputs` unless already there.
- `stop_file`: exclusive absolute STOP path; actual fresh usage file remains a CLI argument.

Historical fields (all bound in `inputs`):

| Field | Existing artifact |
|---|---|
| `selection_closure` | `experiments/analysis/match_weight_compare_20261109/operations/performance-closure.json`, fixed SHA `574cc99f8b943eb68a805871c96fd6d9f6fd61c4ed42fa37872d5a7bc3d0f3f9` |
| `selection_admission` | `.../performance-v1-admission.json` |
| `selection_state` | `.../performance_v1/state.json` |
| `selection_summary` | `.../performance_v1/summary.json` |
| `selection_audit` | `.../operations/performance-audit-results.json` |
| `selection_review` | `.../operations/performance-review.md` |

Their hashes must match the closed Root receipt. All five old CSVs must also be bound; owner receipts, complete exits, nomination, all four prior gates, independent PASS and summary/closure counts/files must agree. Technical receipt and acceptance paths come from the original selection admission, so merge its complete `inputs`. No historical `admission()` function is rerun. Every historical source-file hash must still match disk and be present unchanged in current `source.files`; Python/executable identity must match. HEAD may differ.

`models` has exactly two physical paths, identical to the accepted historical technical records:

- `v14`: existing `technical_v1/v14.pth`, SHA `817e565f8628a3a860c3dcb84e69e9d68c5f0954f791fbd06e0f115bf6cf95d2`.
- `match`: existing `technical_v1/match.pth`, SHA `ff66e696665019d304848ebf0e3b022fd1a1d08eaa9b25518f12f8c3e33e6a1b`.

`cohorts` has exactly `panel` and `direct`, each pointing to a bound JSON integer array: `9980000..9980019` and `9980100..9980159`. `seed_acceptance` points to bound JSON with `status:"PASS"`, the new `profile`, `cohorts` containing those exact arrays, `no_observed_conflicts:true`, nonempty `limitations`, and a nonempty `files` path/hash map. Every file in that map must also be bound in new `inputs`.

## CLI and outputs

Only after Root source commit/admission:

```text
<project-venv>/bin/python -B -m scripts.match_weight_confirmation_owner \
  --admission <absolute-new-admission.json> \
  --admission-sha <SHA256> \
  --usage-file <absolute-fresh-usage.json>
```

There is no technical/assembly phase or automatic second phase. The three exact commands use existing `scripts.par_eval`, `--workers 1`, no overrides: `v14_panel` and `match_panel` (160 rows each) in the first wave, `match_v14` (120 rows) in the second. Owner writes state, exact CSV receipts/returncodes and the summary only after all jobs finish and validate. STOP/failure cleans only owned groups and forbids resume/retry.

Pure interfaces: `admission(path, sha)`, `accepted_selection(a)`, `output_dir(a)`, `job_spec(a,name)` (role/cohort/games/opponents/csv), `performance_command(a,name)`, `validate_csv(a,name)`, `gate_checks(counts,panel,direct)`, `analyze(a)`.

Summary includes absolute W/D/L per role/opponent and direct, panel/opponent/direct score intervals, degeneracy flags, all eight fixed gates, `passed`, `promotion_authorized:false`, original CSV hashes and explicit empirical-interpretation limitations. The owner adds current source and admission SHA. Winning the gates never changes any protected weights.

## Actual validation of this implementation

No production archive or simulator was used. New synthetic suite plus existing comparison suite: **94 passed in 4.72 s**, exit 0. `/tmp/match-weight-confirmation-tests.log` is the actual output. Separate expected missing-module/owner logs are `/tmp/match-weight-confirmation-red.log` and `/tmp/match-weight-confirmation-owner-red.log`. No broader suite or real phase was run.
