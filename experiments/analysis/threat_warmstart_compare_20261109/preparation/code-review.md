# Independent review: threat warmstart comparison

**Specification compliance: PASS. Code quality: PASS within the requested narrow scope. No actionable launch, method, or statistical blockers found in the final reviewed bytes.**

Reviewed the three new comparison files against `docs/superpowers/plans/2026-11-09-threat-warmstart-comparison.md`, reading existing loader, inference, game-loop, owner, historical receipt and bootstrap helpers only to resolve concrete interfaces. The historical training admission was not executed against the new HEAD. No tests, model loads, games, source edits, or Git operations were performed by this reviewer.

## Grounds for approval

- Assembly replaces exactly zero-based member 18. Each candidate contains its final 101-input Q followed by original members 0–17 and 19–35, for 36 total; both use V14 inference settings with only the prescribed feature/frozen changes. Explicit shape/dtype/key/finiteness and loaded-state comparisons catch loader fallbacks.
- Accepted final training hashes and Root closure/owner/receipt bindings are checked as historical data, while comparison source and phase admission are separate. The original training source is not re-admitted.
- Control standard-loader use remains conditional on actual same-width batch equality and four fixed stock-versus-null-adapter games. The first 16 exposed replay next states are fixed before checking legal masks; they are not silently replaced. The batch check uses all 36 outputs, means and legal argmaxes for sizes 1/8/16. Native actions, public trajectories, all per-step v2 point results and final outcomes are compared. A single environment is reused and closed, and games run with `train=False`.
- Performance requires separately bound Root technical acceptance. The five `par_eval --workers 1` commands use the exact three model paths, fixed 20-card cohorts and both sides. The direct opponents load their own bound checkpoint configuration. Owner waves are 2/2/1, without automatic retries or phase transitions; existing source/protected-file, quota, STOP, battery and ownership checks are reused.
- CSV validation enforces 40 unique complete games per block, prescribed opponent/cards/both sides, 303 steps, v2 points and consistent W/D/L and point results. Nomination uses actual victories, including 24/40 in each direct block; draws cannot satisfy those gates. Existing paired whole-card bootstrap helpers use 5000 draws with NumPy default PCG64 seed 0 and 95% percentile intervals, retaining half-point draw scores for the descriptive intervals. The report distinguishes screening nomination from promotion and discloses repeated selection/single-start limitations.
- Interrupted unfinished `par_eval` counts remain explicitly unknown; only completed validated CSV jobs are credited. The bounded natural descendant-cleanup wait does not signal unrelated groups.

## Evidence and review continuity

Initial hashes were observed before review. During review, the implementation finalized the narrow legal-argmax/first-exposed-row corrections and their synthetic cases; these deltas were inspected. Final hashes were then checked again and match the stable values supplied by Root. Owner bytes did not change. Inspected `/tmp/threat-comparison-implementation/final-tests.log`: **20 passed in 2.07s**. These are implementer-run synthetic tests, not reviewer reruns or real loader/game evidence.

## Final reviewed SHA-256

- `scripts/threat_warmstart_compare.py`: `cbffceb856a3ba62e2668d585222051c88f6f5c6e6f00eebae370ff89d95f5e7`
- `scripts/threat_warmstart_compare_owner.py`: `57d49a1129d7e018b1bf21ffb07f7f4ccdc8f091ffd1b3d3fef04046fc9f26f5`
- `tests/test_threat_warmstart_compare.py`: `2e621cf9855283b12b3271f0e11ea21835b76199fa947df26818e0f07048a641`
- `/tmp/threat-comparison-implementation/final-tests.log`: `a5fb2e78943c7d5e7bd4ed42832803794b39bd69b087bd917ec0b89ef831c1dc`

Approval is for the reviewed code to proceed to Root's separately admitted real technical loader/batch/game phase. Actual standard-loader equivalence, performance acceptance and any strength conclusion still require their prescribed runtime evidence; none are asserted here.
