# Match-weight owner implementation

Implemented only `scripts/match_weight_owner.py` and `tests/test_match_weight_owner.py`. No core, reward, study, plan or documentation changes; no real models/games/child processes, commits or push.

## Contract with study implementer

- One explicit CLI phase: technical, pair48, or pair49. Admission start must be48,48,49 respectively; no queue linking phases.
- Study functions: `admission(path,sha,stage)`, `output_dir(a)`, `worker_command(a,path,sha,state_path,role)`, `check_technical(receipt)` (whole receipt), and `validate_final_receipt(path,a,sha,role)` returning statusPASS or raising.
- One technical child with role technical, or exactly two original training children control/match. Owner state includes profile/stage/start, exact PID/argv records, source/protected/input bindings, explicit battery permission, usage receipt and STOP path. Inputs include the admitted inputs plus the admission file itself.
- Receipts at `<out>/<role>/receipt.json` must bind complete status, profile, role, stage, start, source, admission hash and actual launched command. Technical validator checks the four-game evidence. Training receipts additionally need440games and their exact release.json hash.
- Readiness requires both prefill.json and waiting.json files per arm; owner records their prefill hashes and awaiting_root_release. It never writes release.json. Existing waiting markers should remain as historical evidence after Root release. End tensor/replay validators run only after both child groups have exited. Root manually starts each later phase.

## Reused operation controls

Existing compute_lock/spawn_owned/shutdown_owned/group_alive, safe_path/save_state, fog supervisor guard and atomic exclusive JSON writer. The existing guard enforces actual fresh quota below100%, frozen source/HEAD/inputs/protected bytes, STOP and foreign process exclusion. Explicit admitted battery=True is passed unchanged. Owner source/interpreter and admission digest are checked. Output reservation is exclusive; symlink/hardlink paths are rejected by the existing physical-path helper. STOP, worker failure, mismatched receipt or failed final validator produce incomplete status, request STOP and clean only recorded children. No retry or automatic Root release.

## Actually executed checks

Targeted synthetic command:

`env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_match_weight_owner.py`

Final **19 passed in2.52s, exit0**, `/tmp/match-weight-owner-implementation/final-tests.log`.

Tests invoke the real owner main, persist real temporary state/receipt files, and replace only the not-yet-integrated study API, process spawning, external guard checks and clock waits. They cover each phase, at-most-two launches, no subsequent pair, duplicate-output refusal, unchanged original worker commands, manual readiness with no owner-created release, successful external release, receipt role/source/command/stage/start/profile/admission mismatch, nonzero child exit, lingering group rejection, final-validation failure, quota rejection before launch, unsafe output, and STOP/admission mutation after first spawn preventing the second launch.

`red.log` recorded17 fixture setup assertion errors because the owner module did not exist yet; `green-1.log`17PASS. Two additional STOP/admission integration cases produced the final19PASS. Both new files also parsed with ast and passed trailing-whitespace inspection. No historical suites repeated. The separate real study implementation and actual model/runtime qualification remain Root integration steps.

## Final SHA-256

- scripts/match_weight_owner.py: d6e277bab1ccdb7941670261407fb0a8fc1fe90be6addace9c776cc5451c8762
- tests/test_match_weight_owner.py: 8dfbf8c9e2588e0c6e477e96a33cccbb96f96005e0b01b213f4716e8b78017af
- /tmp/match-weight-owner-implementation/final-tests.log: 268b38fc5ecfd318aad1f31a974afe302b33cbac374387f059935b21da026a61

Independent reviewer has these bytes and API contract. No real-study success is claimed.
