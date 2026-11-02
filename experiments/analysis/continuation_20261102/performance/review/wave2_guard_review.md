# Independent second-wave guard review

**Verdict after path fix: PASS for the controlled single launch. No open Important
or Critical findings.** Reviewed `/tmp/sherlock-continue-20261102/train_targeting_wave2.py`
SHA256 `2cd401b2f63040157a7b98e6fa9b18cd6afe295ffdb96d0140933a44763cb84b`.

Important issue found and fixed by Root: the original supervisor was pinned under
`/private/tmp/.../train_targeting.py`, whereas the new guard used `/tmp/...` as a
hash-map key. This made original source identity comparison fail despite equal
bytes. Independently reproduced the mismatch with a pure source-identity check;
resolving only that supervisor path restored exact identity equality. Read the
fixed line and `wave2_identity_preflight.json` (source/weights equal).

The guard accepts only the precise original schema-KeyError boundary, verifies
original supervisor/child PIDs absent, proves both first-arm success records plus
720 rollout / 96 raw validation / 600 ordered CSV rows and 303/v2 episodes,
retains the original deadline and source/weight pins, starts only components19,
monitors the pair, stops owned children on failure and leaves final four-arm
admission to Root. New and original supervisors self-pin; no original script edit.

Nonblocking hardening: check both new logs and run-record paths before the first
Popen as well as both run directories. Currently a second-arm stale log can be
discovered only after spawning the first child. My read-only snapshot confirmed
all six paths absent, so this is not an existing collision or a blocker for this
controlled launch.

Read the reported nine synthetic schema checks; did not rerun them. No models,
games, training or test suite started. No repository/source edits. The original
supervisor was still running during inspection, so this review is not a claim
that the runtime launch conditions have already been met.
