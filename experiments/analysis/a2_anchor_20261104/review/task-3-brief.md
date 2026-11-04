### Task 3: Anchored training adapter

**Files:** Create `scripts/student_anchor_train.py`, `tests/test_student_anchor_train.py`; avoid modifying existing trainer if a restored wrapper suffices.
**Interfaces:** `prepare --student PATH --datasets DIR... --out DIR --run-seed {25,26}` creates CONTROL/ANCHOR paired manifests. `run --prepared DIR --arm {control,anchor} --deadline-utc ISO` runs original fixed 40/160/32 pipeline with training-only combined loss. `validate --prepared DIR --arm NAME` validates completion and sidecar provenance. Document actual implemented invocation in help.
- [ ] Write failing tests: lambda 0 exact TD parameters/optimizer/RNG; positive anchor supplies gradients only through student legal centered preferences; single-action zero; own RNG doesn't consume replay RNG; no excluded rows; cleanup after exception; output/source/input guards.
- [ ] Implement existing TD update plus weight 0.1 action_loss on 256 training rows, one shared backward/clip/step; same targets and counter schedule. Keep value shifts unanchored. Do not alter production Agent_x source.
- [ ] Record source/data/model pins and separate actual TD/anchor/total metrics, updates, sample split/count. Reuse existing training audit and verify paired prefill (same configs/rewards).
- [ ] Run tests and independent review; root baseline/full relevant checks and commit before trials.

