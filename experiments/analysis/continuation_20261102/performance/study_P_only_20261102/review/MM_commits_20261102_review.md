# Independent read-only review: Mahmoud commits, 2 November 2026

**Verdict:** `56bcc559` is compatible at the decision-logic level with the existing agent when `zone_rescue=False`, including both P flags enabled. This does **not** preserve the frozen source identity or extend P qualification to the new runtime. `35a9ebc` has two Important resource-safety findings before a public remote-play deployment. No Critical finding established. Do not integrate either commit into the P qualification target before the frozen release workflow closes.

Reviewed commits: `56bcc559c2db0989dbb6a2aa48b6f47ad78871c9`, `35a9ebc270621b236954b8a3647e9c6f589949ac`. Observed checkout HEADs remain Primary `ef38993826bbc7f053b0555c03c4a4314723f721`, Performance `03e54e267242ff642c126313fe5f512ed9d959ac`.

## Important findings

1. **The session cap does not bound model construction or concurrent inference.** In commit 35a9, `scripts/sherlock_server.py:131` calls the factory before taking the registry lock or enforcing `max_sessions`. ThreadingHTTPServer accepts concurrent requests. A pure dummy counterexample with `max_sessions=1` admitted eight simultaneous factory calls while the registry was still empty. The same issue scales beyond eight; the default cap is only a retained-entry cap. Distinct session locks also allow parallel inference. This can exhaust memory/CPU, evict a currently playing session (the stub then permanently returns STAY), and invalidate concurrent study timing. Reserve capacity before construction, enforce a global construction/inference budget, and reject excess active games instead of silently evicting them. Bound request-read time as well; authenticated slow bodies currently hold threads without a socket timeout. This is an authorized-client resource risk, not an unauthenticated inference endpoint.

2. **A tiny authenticated configuration request can request unbounded allocations.** `scripts/sherlock_server.py:205–211` checks only that env_cfg is a dict and passes it directly to the agent. A pure handler counterexample forwarded `map_width=map_height=1000000000` unchanged. `agents/sherlock/main.py:210–217` applies those dimensions and calls `belief.reset_game`; `belief.py:155–172` allocates multiple W×H arrays. The 4 MiB request limit does not protect this path. Validate the supported course configuration and strict numeric bounds before calling the agent; validate observation shapes/cardinality against it. Tests should prove rejection occurs before allocation, using a dummy agent.

**Integration safety consequence:** the existing conditional installer's `quiet` process pattern (install_qualified_P.py:325) does not recognize `scripts.sherlock_server`; the new server does not acquire the study/release quiet locks. Keep it stopped throughout evaluation, model/package QC and installation. Before later deployment, coordinate an explicit server-process exclusion/lock change with Root; do not silently expand the current frozen release scope.

## Default-off and P compatibility evidence

The global `_rescue` expression is unchanged. Every normal act resets `_rescue_zones` to an empty set, and the new population branch is skipped when the flag is false. `_rescue_for` then returns exactly the existing global boolean without reading assignment/candidate data. Constructor additions are empty bookkeeping only; the disabled branch uses no RNG or belief/assignment mutation.

A stdlib AST proof stripped only the two added constructor fields, the empty-zone reset and disabled zone branch, and the new helper; it replaced its six call sites with their exact former expressions. The **entire resulting main.py AST equals 56bcc559^**. Eight synthetic global-rescue × point_pair_swap × art_move_guard Boolean cases also returned the original boolean. Thus both existing P modifications retain their position and logic: pair assignment before features and artillery movement veto at its original stage. This establishes source-level decision equivalence for the fixed default-off configuration, not a measured gameplay or speed guarantee. Toggling the experimental flag during an act or monkeypatching the helper is outside that claim.

`zone_rescue=True` is a new independent evaluation-only behavior: assigned candidate targets inside sufficiently old relic zones without proven point tiles can be rescued even when points exist elsewhere. It does not require `cand_rescue=True`. The old global fallback still takes precedence. No strength claim follows from the historical cand_rescue result; the commit explicitly says the new mode has no performance measurement.

## Frozen P evidence and safest timing

`verify_P_package.py:101–116` requires current Primary runtime/builder bytes to equal the frozen checkout and original 03e blobs. Both config.py and main.py change in 56bcc559; an FF therefore correctly fails that guard regardless of the false default. The extra config field also changes the available configuration schema. Retain the strict guard and the original source/weight/master bindings.

Finish the registered P confirmation and independent data audit first. If P qualifies, perform package/course/runtime QC and the authorized conditional installation against the bound 03e-compatible runtime **before** integrating Mahmoud's core change. Preserve the resulting ZIP, source manifest and weights immutably. If P fails, retain V14; this review does not authorize replacement. Afterwards, integrate Mahmoud's default-off research work separately. A raw P checkpoint executed by the newly merged runtime has a new source identity, even if the disabled-branch argument predicts identical actions; do not describe that newly assembled runtime as the exact qualified artifact without a separately bound compatibility/release decision. A frozen packaged P remains tied to its original bundled runtime.

A later compatibility check can use identical observations, fixed V14/P weights, fixed seeds and all relevant rule states to compare old versus new default-off actions, Q arrays, assignments and RNG states for both P flags true. Include rescue true/false, point-known/unknown, matches and nebula cases. Run only after current workers stop. Keep zone-on performance experiments separate. No such real-agent test was run here.

## Remote-server scope and smaller observations

The new module does not start a service at import; `main` is explicit, binds loopback, and public cloudflared requires `--tunnel`. The client ZIP contains a stub and bearer connection secret, not neural weights. The server loads the existing battle ZIP and requires frozen config; training/update/save behavior is disabled on the stub. Those are useful boundaries, not a substitute for bounded workload admission.

The public-tunnel/helper startup precedes main's try/finally, so a later startup failure can leave a helper process unreaped; shutdown only sends terminate without waiting. Tighten lifecycle cleanup before deployment. `load_token` should reject an empty existing token file, since empty stored token equals the default absent header. ZIP loading also relies on import caching of `Gruppe15`; multiple factories in one interpreter should not be used to claim a newly selected archive was actually loaded. None of these paths was invoked.

## Verification and scope

Evidence: `/tmp/MM_review_20261102/check.py`, `/tmp/MM_review_20261102/evidence.json`. Fresh execution succeeded with stdlib-only extracted AST and dummy objects: full normalized-main AST equality, eight Boolean cases, and both resource counterexamples. No Torch, NumPy, model, agent/environment import, socket/server/tunnel, game, unfinished outcome, checkout or repository edit occurred. New tests were read; the HTTP integration fixture was deliberately not run under the no-server constraint. Author-reported game equivalence and suite counts are not independent results of this review.

Commit-35a9 source SHA256:
- main.py: `8de06de511bcbe090293715c1d72fec048e6ef4aa91713f766bee6a5e30b2beb`
- config.py: `f6f3b6fb35c9ac7e98c91484e69f919ea41c15cba8a0e5fab77b19edfcc995e6`
- sherlock_server.py: `d1b274a0263ce0118aa44f08ac37c504a03490c122ba93863947340a701a8a23`
- sherlock_remote_stub.py: `8ecd3e6050de31a03ebf4ccc6066c9e2108c631fef4cb38a1b5ef718e418cb9c`

## Narrow repair contract for the separate implementation worktree

For this course-only endpoint, preserve omitted width/height defaults of 24 and accept supplied structural dimensions only as integer 24; accept max_units only as integer 16. Reject Boolean, fractional and nonfinite numeric substitutes. Optional unit_sensor_range needs an explicit supported bound (0..24 is a conservative structural ceiling; narrow to the actual course range after reading its configuration). Do not silently clamp. Keep the ordinary small scalar course parameters; reject nested/oversized configuration structures. Check fixed observation array shapes/cardinality before inference. This is a deliberately course-specific interface, not support for arbitrary map sizes.

Reserve capacity under the registry lock before invoking the factory, counting pending plus retained sessions. Constructor failure must release the reservation. Reject excess admission explicitly instead of evicting a live game. A nonblocking single-construction gate and bounded inference gate prevent bursts of heavy calls; retain the existing per-session lock. Expiration must not reclaim a session currently serving a request. Test reservations with blocked dummy factories, failure/retry, and active-session retention; test invalid config with a dummy that records any call. None of these repairs requires starting an HTTP service, loading a model or altering the frozen P checkout. Root coordinates the separate worktree and any fix acceptance.
