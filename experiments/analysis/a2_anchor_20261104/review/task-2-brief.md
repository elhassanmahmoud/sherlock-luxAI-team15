### Task 2: Loss traces

**Files:** Create `scripts/student_failure_trace.py`, `tests/test_student_failure_trace.py`.
**Interfaces:** CLI accepts `--model`, `--opponent` (solution92 or self), optional `--opponent-path`, `--seed`, `--side`, `--out`, `--deadline-utc`. One normal and one instrumented game per invocation; compare every action and final metrics, retain observation-only JSONL and summary. Agent may be A2 single or V14 ensemble. Hook inputs/raw outputs exactly once; compare teacher Q only on copied features, outside act if needed.
- [ ] Tests cover canonical mirroring, hook restoration on failure, no reset ghost rows, ensemble mean raw Q, no second act/context, per-match counter reset.
- [ ] Implement wrapper around normal play path, not a divergent replacement simulator. Capture actual state available to agent and final outputs; no hidden-state assistance.
- [ ] Run tests/review, then prescribed known-case paired replays (24 executions total), one CPU slot. Root analyzes earliest consequential divergence and missing evidence.

