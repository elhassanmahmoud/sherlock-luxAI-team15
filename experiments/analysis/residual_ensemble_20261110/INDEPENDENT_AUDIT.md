# Independent residual artifact audit

PASS within reviewed scope. 6623 checks; 8 technical and 240 training game records; 24,000 total updates.

Both exact fixed 120-game sequences, 40 zero-update prefills and 80 learning games at 150 updates each, 12,000 finite loss rows and Adam steps per arm, target equality, 79→256→256 Dueling residual tensors, shared zero-head member18 initialization, and distinct finite trained residuals verified directly. Full replay array schemas/finiteness/generations/terminal rows inspected. Input/output/protected-file hashes and receipt bindings agree. V14/ZIP unchanged in worktree and Primary.

- No independent neural inference/cache-value recomputation, causal diagnosis, or claim of strength. Root already performed replay signatures and additive inference; this audit checked full raw array finiteness/shape/generations/terminal labels, not all replay signatures again.
- Historical source identities read from accepted completion and matching state; no attempt to treat later selection source changes as training tampering.
- Technical raw game records contain digests rather than complete stepwise traces; exact digest/score parity is verified, not independently rerun.
- Stored checkpoint counters and Adam/loss rows cross-correlate 12000 updates per arm, but historical gradient execution cannot be independently replayed without rerunning training.

Selection not read or analyzed in this stage. Ready for completed-selection follow-up.

# Completed selection audit
PASS. 4538 additional checks; 11161 combined. Exactly 200 records across the five fixed jobs, no missing/duplicate/excluded/replaced role-map-side keys. All 303-step, scoring-v2, result/win, zero-caught-error and file identity checks agree. All 436 recorded source files and the runtime executable match; both candidates match the previously independently audited training hashes.
| Agent | Solution wins | Direct wins | Direct map-bootstrap 95% | Solution delta vs V14, 95% |
|---|---:|---:|---:|---:|
| R61 | 35/40 | 14/40 | 15–55% | −12.5 pp [−25; −2.5] |
| R62 | 38/40 | 10/40 | 9.875–45% | −5 pp [−12.5; 0] |
| V14 | 40/40 | — | — | reference |

Both starts fail both fixed gates (direct ≥24/40 and Solution ≥V14). No nominee, no confirmation, no V14/ZIP replacement. The independent calculations agree exactly with the original analysis.

5000 PCG64(seed=0) draws of 20 complete maps with replacement, retaining both sides. Paired Solution contrasts join all identical map/side keys before map averaging; linear 2.5/97.5 percentiles. Separate training and selection data.

- V14 Solution 40/40 gives an empirical bootstrap [1,1] because every observed map is all-wins. This degenerate interval does not express zero population uncertainty and is not evidence of a universal 100% win rate.
- This fixed screen rejects both starts under the preregistered practical gates; it does not show that all residual methods fail. No confirmation, candidate replacement or extra sampling is authorized by this result.
- No games, model inference or tests were rerun. Scores and action-trace digests are checked for internal consistency and recorded-file integrity, not recomputed from unavailable full simulator traces.
- The recorded source/input/output identities are currently exact, including all source files and executable bytes; this is evidence of artifact identity, not an independent reconstruction of every past process event.
