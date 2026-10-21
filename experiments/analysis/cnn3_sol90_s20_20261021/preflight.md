# CNN3 preflight, 21 October 2026

Plan fixed before new games. Independent protocol and code reviews are archived here. Root corrected the run path and minibatch interpretation before outcomes, as recorded in the plan.

Source PPO60 hash, kind, iteration60, architecture (79 features/6 actions/16 planes/48 channels/4 blocks/detached critic), all32 finite policy tensors and actual loader identity verified. Source copied byte-for-byte into an exclusively new run directory; teacher provenance copied and all18_fo10 teacher hash verified at its required relative path. No random initialization or new critic is used.

Training schedule independently reproduced:240games/120maps,211Solution and29default. It is randomized by the fixed mixer, not exactly90/10 by count. No new training or evaluation yet at this preflight. Torch stream tests:6 expected failures before fix,8passing after. Full integration489tests plus14subtests passed82.30seconds. Tests preserveCPU RNG; no cross-hardware reproducibility claim.

The launcher is separately checked with fake children (no engine): success, nonzero exit with a TERM-ignoring descendant, and short deadline termination. An unreaped-child process-group EPERM on macOS was reproduced and handled with leader reaping and a live-state check; final deadline smoke records child-15 and no surviving group. Final code independently approved. It includes startup in projection, loss finiteness, low-memory guard and deadline cleanup. Final tensor/config/count verification remains mandatory after actual training.

Root owns outcome decisions. Source/HEAD/protected/input hash freeze and final seed/remote check occur immediately before first actual job. A conditional positive candidate needs a reviewed PPO-compatible course/package adapter; the existingDQN adapter is not a valid PPO check.
