# Conditional P installer: independent design/code review

**PASS for the approved offline installer scope, after the narrow review fixes. No remaining Important/Critical findings. This is not actual release eligibility or installation authorization.**

Installer SHA256 `87c3f94cc050a7dba7701f997b9a7067e924a76aba2b4ef28a7aa46e953ea2d2`; tests SHA256 `64ae19607e5aa1960ddfbf84a7a9fd6d5932c10bc7ce7f15b987b9b1685b6b7f`. Design: `/tmp/P_release_installer_design.md`.

Reviewed real summary/audit producer schemas against source only. Installer binds fixed OLD V14/raw P/old ZIP identities, complete3000/9000 selection/confirmation, common03e master, exact job paths/models/flags/workers and actual commands, full CSV keys, independent ACCEPTED audits and all evidence hashes. It reevaluates unchanged numeric gates with strict boolean agreement, checks original interpreter bytes and source/weight closure, and accepts only structured independent technical QC with Python3.10/course/layout/replay evidence. It does not forge legacy PASS logs or deserialize models. Technical assertions remain the responsibility of the independent QC producer; no such current final release proof is asserted here.

Transaction review: repository-common resource plus release-writer locks, live quiet-process check, fresh explicit Root authorization, exact fixed three targets, fresh transaction, immutable verified backups, same-filesystem staging, durable intent journal, no-overwrite publication, inode/hash ownership checks, signal rollback and journal-bound rollback-only recovery. Foreign target creation/replacement is preserved and yields a conflict. This is recoverable three-file publication inside a required reader/writer-free window, not simultaneous three-file atomicity. Noncooperating in-place writers remain outside flock control; this prerequisite is correctly explicit.

Important findings resolved during review:
1. A prepared/crashed transaction previously did not prevent a new transaction when targets were still OLD. A durable root-specific pending marker now blocks a second transaction until closure/recovery/manual resolution.
2. Recovery previously always required a sealed backup, making a crash during backup creation unrecoverable. The unsealed path now permits only no mutation entries and unchanged OLD targets.
3. Historical evidence substitution previously required a currently missing target to exist. The three verified old-backup substitutions now permit missing transitional target names while validating their real parent and backup bytes.
4. Fixed job verification now includes weights, two workers, two exact flag overrides and actual command; live no-job detection includes the intended inline check_battle and external verify_P_package command.

Independent targeted verification on the stable hashes: seven synthetic tests passed in1.309s. Cases: pending transaction exclusion, pre-backup recovery, missing-target recovery with historical QC evidence, fixed-job tampering, handled-signal rollback, foreign no-overwrite publication and no model-stack imports. The author's full19-test result was reviewed but not redundantly rerun. Only temporary synthetic bytes/JSON/CSVs/fake ZIPs used; no real bundle, unfinished confirmation data, Torch/models, real installation or repository edits.

Before actual use: finished confirmation and independent acceptance, source closure, actual package/tensor/course/Python3.10/replay QC, explicit target checkout and fresh authorization, quiet window and current quota are still required. The package verifier is reviewed separately and its structural/tensor-only verdict must not be confused with the full release-QC adapter.
