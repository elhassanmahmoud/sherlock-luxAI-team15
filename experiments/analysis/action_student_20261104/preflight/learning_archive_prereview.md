# Completed learning/archive and diagnostic admission pre-review

**Learning artifacts and launch admission pass this bounded pre-review.** No diagnostic CSV, partial outcome, active evaluation log or result summary was read. No Torch/model load, gameplay, training or project test suite was executed. This is not the final 1400-game or publication review.

## Actual stdlib verification

`review_learning_static.py` completed successfully in under a second; its durable result is `learning_static_prereview.json`.

- All eight candidate files match their candidate-manifest SHA256, size and original run file exactly. A1/A2 agree with completed fit checkpoint hashes; four RL copies agree with their final receipts; the two ensemble hashes agree with the prelaunch ensemble verification. A1 is explicitly an intermediate, not an extra diagnostic role.
- Both RL archive manifests contain 30 copied files. All 60 archived files match the recorded hash/size and original source bytes. Each of the four arms has done-status/final receipt, 40 prefill + 160 training + 32 known validation games, 200 rollout log rows, 32 validation log rows and 160 CSV learning rows. All hashed evidence files match. All four start from the same A2 hash. Within each start, stored prefill digests match each other and paired_prefill.json; configs differ in exactly w_sap_hit. Independent prior audits additionally attest actual model/replay/update checks; this review did not rerun those model-dependent audits.
- Both archived collection packages have completed manifest/status, 60 game rows and exact dataset/games hashes. Both fits have complete status and exactly 30 action + 5 value epochs. Fit/update/metric values in the draft match archived evidence: A1 6125 updates and 72.08→82.93%; A2 12215 updates and 81.99→86.70%, regret 0.04125→0.02339. A2's one near-tie pair change and zero non-tie changes are accurately described as calibration observations. These are development decision metrics, not wins.
- Final protocol preserves every predefined role, opponent and seed list; both external seed files match their embedded lists, have twenty unique seeds and are disjoint. All **91 source hashes and 33 input hashes** match current bytes. This includes both seed files, resolved interpreter, guard/controller/auditor helpers, all role/opponent weights and protected inputs.
- Independently recomputed the padded two-worker queue from the recorded historical means, 15% multiplier and 12-second per-job startup: **3005.5975 seconds**, identical to admission. Launch at 15:48:13 UTC therefore estimates completion 16:38:19 UTC, before 16:40 model stop. The estimate is explicitly not a worst-case guarantee and includes twenty minutes of post-model closure reserve. No fresh outcomes influence admission.

## Concrete corrections before final publication

1. **Clarified, no missing auditor artifact:** the two RL independent-audit receipts cite SHA256 `30c026726d2a2aa6fe84b102a9996403a60cc3b24b6aae1a3e568b0a71608bbd`. The exact auditor exists under each `rl/seed{27,28}/independent_audit/` and is already included in that seed's checked 30-file archive manifest. My initial preflight-only search overlooked those deeper archived copies; the earlier suggestion that archival provenance was missing is withdrawn. A central preflight duplicate is optional discoverability only.
2. The archive README is an older intermediate text saying RL still outstanding. Update it at closure to distinguish the now-complete four learning arms from the still-running diagnostic.
3. The report draft is correctly marked as a draft outside the repository. Its final phrase claiming independent Abschlussprüfungen must only enter the published report after those final checks actually pass. Likewise, completed 303-step diagnosis, versioned data and final protected-file checks must be based on the subsequent final receipts; they are not yet certified by this pre-review.

Optional wording precision: change “Das Einzelnetz erhält die echte Aktionsmaske” to “Der Aktionsverlust verwendet die tatsächlich verwendete Netzmaske” to avoid suggesting extra mask inputs to the unchanged 79-feature network. The following sentences already explain the loss correctly.

No operational blocker or change to the admitted running experiment is indicated. Final artifact/statistics/docs delta review remains pending completion of the entire fixed comparison. Existing independent-audit limitations should remain visible: pre-calibration tensors and per-transition original reward contexts were not retained, and recorded runtime attestations cannot all be reconstructed from the bounded final replay.

## Archive-path follow-up

Confirmed 126 historical-source-to-archive mappings resolve to existing files. Collection/fitting mappings use repository-relative archive paths; RL archive destinations preserve their original absolute creation path and resolve through the repository-root suffix; candidate manifest paths are repository-relative. Both fits’ referenced dataset files and all four RL receipts’ final checkpoint paths have archived counterparts in those mappings. Original absolute provenance paths are intentionally historical, not falsely promised as runnable on a different machine. Replay omission remains explicit. Exact RL auditor hashes were confirmed in both deep independent_audit directories.
