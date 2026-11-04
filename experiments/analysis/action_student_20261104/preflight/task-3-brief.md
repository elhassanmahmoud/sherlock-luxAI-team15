### Task 3: Independent RL starts

Files: modify only `scripts/student_reward_train.py`, `tests/test_student_reward_train.py`. Add optional run_seed to prepare CLI/API default29; manifest stores/validates integer0..29; runtime derives seed from prepared manifest. Preserve fixed counts40/160/32 and offset3000, all existing proof requirements. rollout_plan accepts seed default29. Use manifest seed consistently in learnerconstruction, finetune CLI, expectedopponent/mapplans, receipt verification. No process-global mutation to change seed. Legacy default manifest may be supported explicitly or rejected clearly, but never rewrite it. The newactionstudent remains exact existing checkpoint contract.

- [ ] Meaningful tests seeds27/28 distinct schedules, withinpairidenticalplans, configsdifferonlySAP, malformed/tamperedseed rejected; olddefaulttests retained.
- [ ] Implement/report; no commits/jobs.


Root ruling beforeimplementation: supported seeds0..29 only because existingfinetune reserves validationmapregion; actualstudy27/28. Keepcorefinetuneunchanged. Legacyseedlessmanifestsrejectclearlywithoutmutation.
