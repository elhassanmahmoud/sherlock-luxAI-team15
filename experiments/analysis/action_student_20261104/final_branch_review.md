# Final action-student branch review

**APPROVED. No blocking or important findings remain.** The implementation, completed learning artifacts, full fixed diagnostic and final scientific/documentation claims are ready for the root's publication and operational closure steps. This verdict does not claim that Git publication, primary-checkout synchronization or observer shutdown has already happened.

## Reviewed scope

This completes the ongoing review from base `b19e520` through the frozen experiment source `96b524b4fe70a0008e5cee2244dae6d74195f209`. Earlier code, operational-helper and learning/archive reviews are retained separately. This final delta covers the 17-job controller completion, all 1400 diagnostic rows, independent report/JSON, root crosscheck, new `docs/AKTIONSSCHUELER_20261104.md`, new archive/candidate READMEs and the changes in README, CLAUDE, Arbeitsstand, experiment protocol, design and implementation plan.

No new games, training, model loads, Torch audits or project test-suite runs were launched. Source and model files were not edited by this review. The prior 136-test evidence and independent all-row/model audits are reviewed evidence, not represented as tests rerun here.

## Actual final verification

- `git diff --check` passed. Tracked changes at review time are the documented closure edits; runtime/learning source remains unchanged from the already reviewed experiment freeze.
- A new bounded stdlib check (`review_final_static.py`) independently read every one of the 17 completed CSVs and verified exact planned role/card/side/opponent keys, uniqueness, total **1080 panel + 320 direct = 1400**, all 303 steps/scoring v2, and recorded outcome consistency with match-win counts. It recomputed W–D–L for each panel role/opponent and direct role and matched the independent summary.
- All 17 CSV hashes agree simultaneously with the controller and independent audit. All 17 jobs and guard receipts say completed/exit 0. The controller is complete with no running jobs, and the recorded protocol/controller/auditor/state/root-crosscheck hash chain matches the archived files.
- Independently verified the specific degenerate-interval explanation: A2 and V14 have identical Solution card means on every one of the twenty observed panel cards. Thus the reported paired bootstrap [0,0] is a property of these empirical differences; the prose correctly rejects universal equivalence.
- All twelve local links in the new report and archive/candidate overview resolve.
- Result of these checks: `final_static_verification.json`, status passed. Earlier `learning_static_prereview.json` verified eight exact candidate copies, sixty RL archive files, completed collection/fitting/RL receipts and all 91 source/33 input hashes. Final root crosscheck independently rechecks those pins and reports 288 numeric equalities. No game replay or reconstruction of engine internals is claimed by either CSV check.

## Claims and conclusions

The headline numbers match the source evidence: Solution A2 **38/40** versus S30 **16/40**, V14 **38/40**; three-opponent panel A2 **94/120** versus V14 **98/120**, delta **−3.33 pp [−10.83,+4.17]**; A2 direct **14/40**, **35% [15,55]**. A2−S30 panel **+30.00 pp [19.15,40.83]** is attributed to the combined action-learning/data/calibration package, not an isolated component.

All four RL endpoints and both predetermined two-network ensembles have lower observed panel scores than A2. Separate SAP0-control deltas are correctly reported as **−2.50 pp [−11.67,+6.67]** and **−1.67 pp [−12.50,+10.83]**. The report does not turn uncertain Solution improvements into a general reward recommendation, or use these finite observations to rule out RL, ensembles or single networks in general.

The exact Dueling architecture and parameter count, current network masks versus final rule actions, teacher raw-Q versus final teacher policy, signed SAP hit/miss term, preserved inference rules versus unchanged training-specific rule paths, and explicit exploration counter initialization are all explained consistently with the reviewed code. Whole-card resampling preserves both sides and all panel opponents; multiple exploratory comparisons and limited training-seed uncertainty are explicitly disclosed.

The execution total is correct: **4 technical + 120 collection + 928 prefill/train/known-validation + 1400 diagnostic = 2452 executions**; **18340** new supervised updates and **96000** RL updates. Observer evidence contains four actual executions (two sides, each with/without observer), not four pairs. Model completion **16:33:47 UTC / 17:33:47 Berlin** agrees with controller completion and precedes the fixed stop.

**Keeping V14 is supported and appropriately conservative.** Neither the small diagnostic nor equal Solution counts are misrepresented as a completed qualification/promotion. There is no post-result mixture selection, second confirmation, new package claim or Moodle-upload claim. Protected weight/ZIP hashes, prior package-test scope and future research questions remain clearly separated.

## Closure/documentation status

- The stale 32 seed labels have been corrected to 28 with an explicit editorial note; actual pre-result manifests/plan and experiments already used 27/28.
- The archive README now recognizes completed RL and diagnostic stages. Historical absolute paths remain intentionally historical; mapped copies and hashes are documented. The exact RL auditor source is already present in both seed-specific independent_audit archives (the earlier preflight-only discoverability concern was withdrawn).
- Arbeitsstand explicitly leaves final review/publication/operational closure for their actual receipts, and the combined publication checkbox remains open. Those statuses are honest at the time of review; root should update them only after the corresponding actions.
- Root's planned spacing-only cleanup does not affect this approval. Optional wording precision, not a blocker: “Der Aktionsverlust verwendet die tatsächlich verwendete Netzmaske” avoids the slight ambiguity in “Das Einzelnetz erhält die echte Aktionsmaske”; the network still has 79 inputs and the surrounding text already explains the loss correctly.

Remaining required work belongs to the root's authorized closure: archive this final review/check evidence, finish safe Git publication and primary-checkout coordination, record actual owned-process shutdown/protected hashes and update the publication/closure status. No further experiment or model change is requested by this review.
