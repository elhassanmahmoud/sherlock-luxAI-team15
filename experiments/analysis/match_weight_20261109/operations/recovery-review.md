# Independent technical recovery review — PASS

No blocking findings in the usage formatter or final narrow attempt-2 runner change. Read the explicit plan amendment, actual interruption closure, complete formatter, existing usage guard, exact runner/test diff and supplied logs. No models, games, tests, imports of the formatter or repository edits were performed here. This review neither restarts a job nor releases a phase.

## Usage formatter

`/private/tmp/sherlock-write-usage.py` reads the actual supplied tool-response JSON, including its text-content envelope. It requires a Codex limit bucket and at least one available primary/secondary window; used percentages must be finite numeric values in [0,100], excluding booleans. It preserves the real boolean ordinaryUsageAllowed and uses the maximum available-window usage. The command-line path generates its own timezone-aware current UTC ISO timestamp; it never copies a human-readable timestamp from the response. The output is parsed back as timezone-aware before publication.

Validation occurs before a temporary file is created. The destination is absolute with a physical parent path. The formatter flushes/fsyncs a complete adjacent temporary file, atomically replaces the receipt, and removes temporary leftovers. It cannot expose a half-written JSON receipt. It does not reset usage or fetch/manipulate account limits. Writer acceptance of a valid percentage100 or allowed=False does not bypass the unchanged guard: the guard still refuses unavailable usage, stale/future receipts and actual usage≥100.

Read Root's actual supplied log: the existing guard accepts the corrected ISO receipt and rejects the historical malformed timestamp plus unavailable/nonfinite usage. The first fixture attempt failed on a macOS symlink path before reaching timestamp checks; this is separately disclosed and not counted as a successful timestamp test. The later physical `/private/tmp` check is the cited successful integration evidence. No such checks were rerun by this reviewer.

## Narrow runner change

Compared with a96ddeb, study logic changes only output_dir: absent attempt defaults to1/v1; only exact integer1or2 is allowed. Attempt2 requires restart_reason=monitor_timestamp_format and an input-hash-bound interruption closure with correct profile/status, ended original processes, valid original bindings, exactly both roles and exact per-role40prefill/75learning/11250update facts. Output must use the corresponding fixed stage_v2 path. The existing fresh-directory/exclusive writes still reject reuse.

No change to source member18, initialization, rewards, Float32 checks, UID mapping, seeds/cards/opponents,40+400schedule, manual prefill releases, learner or owner logic. V1 paths are not written. Fresh original weights/empty replay still come from the existing make_learner/load_initial path; incomplete checkpoints are never loaded. Pair49 retains its separate accepted-pair48 requirement. New technical source must first pass the unchanged four-known-game technical gate; subsequent phase admissions remain separate Root decisions. Attempt3 and automatic replacement loops do not exist.

The explicit amendment authorizes this single manual technical replacement before performance selection and counts v1 computation openly. Its interruption closure is consistent with the known stopped state: both arms40+75games and11250updates, no promotion, old checkpoints retained, freeze released. This review did not reload those checkpoints or repeat Root's original termination audit.

## Supplied focused verification

Read the three new synthetic cases covering default v1 and exact v2 paths, preserved v1 sentinel/no created v2 directory, invalid attempt types/versions/reasons, missing/changed closure hash, wrong roles/facts/status/process/binding flags. Final affected-file log: **25 passed in2.98s**; RED shows the missing v2 behavior before implementation. No broad suite was repeated here.

## Reviewed hashes

| Artifact | SHA-256 |
|---|---|
|/private/tmp/sherlock-write-usage.py|70343425711580a219d82af55354e837ed6a8d8bf2934cd95b0e6a0141e1feb3|
|/private/tmp/sherlock-usage-writer-check.log|132acfe34cf1110898c737f01dfee50b1044c9b4c191016fe283d79ec0a916c5|
|scripts/match_weight_study.py|a0ae96aac35f5e09787bfcce26802111d92e09f69242cfced4f49abd0f062b51|
|tests/test_match_weight_study.py|d852125736abd04553189173572e4c7cf6021991d8afcd46f90035dc2c29e186|
|/tmp/match-weight-attempt2/green.log|06ff91dceb6d1f487bed208c6de025da6113ef6c8165dd74acd11a4a19d7a861|
|operations/pair48-interruption-closure.json|140a846e0807b2a6315deb66fb4f553afacd2e07e34dc396f7a7394174921deb|

Actual fresh usage, new frozen source/admission, four real technical outcomes and all later pair results require Root's separate actual checks. None is pre-accepted here. The raw tool response's freshness remains an operational requirement; generating an ISO timestamp cannot authenticate a stale or invented response, so the writer must continue receiving the real freshly fetched response as specified.
