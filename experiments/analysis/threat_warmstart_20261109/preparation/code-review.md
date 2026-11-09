# Threat warmstart review — snapshot review-1

**Compliance verdict: changes required before real execution.** The intended isolated two-arm design is implemented, but a deterministic initialization failure prevents the required technical phase. The explicit prefill barrier also has a publication race.

**Code-quality verdict: changes required (one P1, one P2).** No productive-core changes or broader redesign requested.

## Actionable findings

1. **[P1] Use a tolerant comparison for the inherited epsilon calculation** — `scripts/threat_warmstart.py:359`.
   The bound `preparation/source-config.json` has `eps_start=1.0`, `eps_end=0.05`, and `eps_decay_steps=60000`. `Agent_x.epsilon` computes `1.0 + (0.05 - 1.0)` at the prescribed `env_steps=60000`, producing `0.050000000000000044`, not exactly `.05`. Consequently every real `make_learner()` call fails its warmstart guard before the first technical game. Preserve the original epsilon schedule and replace this equality with a tight `math.isclose` check. Add a focused synthetic initialization test using the actual source-config epsilon values; current tests bypass `make_learner()`.

2. **[P2] Atomically publish the approval barrier before waiting workers can read it** — `scripts/threat_warmstart.py:44–47`, `498`, `502–508`.
   `write()` makes the destination visible with `open('x')` before JSON serialization finishes. Both live workers use `release.json.exists()` as their wake condition and then immediately parse that file. A worker scheduled during the write can read empty/truncated JSON and abort this explicitly non-restartable 40-game prefill run despite valid Root approval. Publish the fully flushed release with atomic, no-overwrite semantics, retaining single-use behavior. `prefill.json` uses the same publication pattern and is also watched while its writer is live. A focused synthetic test should exercise reader visibility before publication, without models or games.

## Scope and evidence

Read the task brief, project rules/current handoff, complete three-file diff, implementer report, and concrete original feature/replay/update/game/supervisor helper paths. Confirmed the working files match the reviewed snapshot hashes below. Inspected the provided final synthetic-test log: **23 passed in 2.81s**. Did not rerun tests, load model archives, run games, edit source/Git, or create subagents.

The reviewed design correctly selects member 18 (ensemble entry 17), copies all original tensors and the 79 first-layer columns, zero-expands to 101 inputs, initializes Q/target identically with fresh optimizer/replay, and adapts only control feature tails including cache/next states. Actual replay pushes retain original rewards and final native-to-canonical action labels; original update/learning paths are retained. The prefill comparison excludes only feature tails from replay equality, binds both original workers and Root review, and does not automatically release gradients. Fixed technical/training chronology, frozen source/input/protected-file checks, existing quota/STOP/battery permission guards, two-worker owner lock, final tensor/replay checks and incomplete receipts are present. Real trajectory equivalence and threat learning remain unproven until the authorized runtime phases.

## Reviewed SHA-256

- `scripts/threat_warmstart.py`: `eba3fe2bfbafeae4b3ba5bd31048e3aa4c93bfa9c182ae3f383e34b484581486`
- `scripts/threat_warmstart_owner.py`: `137aec6383b6186b9ab0cad728b06b173964e93290977f490686d5d0ef9288f0`
- `tests/test_threat_warmstart.py`: `98bc742ef0e90071d7c409c5c764e9c2879317433d0daa8ecb68793e9e963f0f`
