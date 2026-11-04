# Explicit epoch-count amendment review

## Spec verdict: PASS

Reviewed the amendment brief, supplied diff, current producer/test code, repository instructions, and implementer report. The current two file hashes match the report exactly.

- `EPOCHS` remains 3; API keyword and CLI option both default to it. The existing default-three integration is unchanged.
- `type(epochs) is int` with inclusive 1..100 validation occurs before output reservation or input loading. This rejects booleans, floats, zero, negatives, values above 100, strings, and NumPy scalar integers through the API. CLI integer parsing feeds the same validator; invalid numeric text is rejected by argparse before running the producer.
- `range(epochs)` drives the unchanged complete training loop. Every completed epoch increments `epochs_completed`; updates and observed training rows continue to count actual batches and rows. A normal complete run therefore has updates = epochs * ceil(pooled training rows / 1024), and training_rows_seen = epochs * pooled training rows.
- Requested manifest count and exported `distillation_epochs` use the validated request. The explicit pre-export equality check requires all requested epochs. Existing deadline/error handling still prevents partial export.
- Diff contains no model, loss, seed, replay processing, or gameplay configuration change. Docstring now reflects requested completion.
- Added real tiny-fixture API/CLI tests request two epochs, check two updates/64 training rows, manifest and checkpoint metadata, and exact Agent_x reload. Invalid API tests assert no output is created. This matches the brief’s specified test scope.

## Quality verdict: PASS

No actionable correctness, regression, or maintainability findings in the scoped amendment. The change is small and consistently threads one validated value through the existing producer. Existing incomplete/deadline behavior remains intact.

## Verification and limits

Independently inspected the current diff and calculated SHA-256 values:

- scripts/student_distill.py: d79c07ba4df4dcd56f2784a4ad51201be5a1818c2a22a85b22b8cfea7095a6fa
- tests/test_student_distill.py: 3b86de3b8b0ff771000aaff90b0f7aa10da4d28f62f4017dd8c7d688b8969b6f

`git diff --check` passed during review. Implementer reports expected red-before-green failures followed by 29 passing focused tests; these same-code tests were not repeated. Boundary values 1 and 100 are supported by the directly inspected inclusive guard and generic loop, rather than separate producer executions. No production run, games, source edits, commits, or subagents were performed. Only this review artifact was written.
