# Independent Task 1 review — changes requested

Reviewed commit `4503dba73eefd78c337e80e34f06a65d502f2c4c` against `ec29a17`, its packaged diff, task brief/report, AGENTS.md/CLAUDE.md and latest handoff. Scope is the two committed Python files only. Root's subsequent documentation commit is excluded. No repository edits, full games, model-weight loads or repeated full suite.

## Actionable finding

**[P2] Normalize or explicitly label directional action fields for player 1** — `scripts/observe_loss_mechanisms.py:88-89` (also line 117).

`_rule_override` receives canonical actions/masks, and `_prev_actions` also retains canonical action classes. The observer copies those values without conversion, while `position`, `final_action`, truth snapshots and known tiles are real-space values. The module declares that all record coordinates are real and the record carries no canonical-frame label. For player 1 this makes an unchanged legal action appear to change direction or violate its recorded legal mask, undermining both-side transition analysis. Convert the copied before/after/recorded classes and movement mask entries using the same mirror mapping as the agent, or explicitly name/label canonical fields and supply their frame mapping. Do not alter agent actions or masks themselves. Add a non-STAY/non-SAP player-1 regression because the current both-side tests exercise only mirror-invariant STAY/SAP.

Concrete synthetic reproduction with existing `Agent_x`, `FixedQ(2)`, `AgentConfig(scripted_explore=False)`, `player_1`, observation step/match_step 25 and unit `(23,23,100)`:

```text
position=[23,23]
before_rule=2; after_rule=2; recorded_action_class=2
final_action=[1,0,0]
legal_mask=[True,False,True,True,False,False]
legal_mask[final_action[0]]=False
```

The canonical RIGHT (2) correctly becomes real UP (1); no rule changed it and the real UP is legal. Only the emitted schema misrepresents their shared frame. This does not invalidate the STAY-to-SAP boolean itself, because those classes are invariant under mirroring.

## Checks and assessment

- Recorded test logs inspected: focused 8 passed (2.03 s); full 231 passed plus 14 subtests (35.24 s). Did not rerun the suite. One small synthetic action-only reproduction above was run; no full game or training.
- Passivity: delegates one original policy call and one original rule call per observed decision, restores the instance hook in `finally`, returns the original action array, does not consume randomness or feed truth into the policy. No changes to existing agent/common/scoring/engine sources.
- Time/reset: pre-step truth and obs_t decision are aligned; transition truth_after comes from `info.final_state`; reconstructed final point increment follows the existing version-2 scoring helper. Match winners use actual team-win deltas. Energy tiebreak sum matches installed engine's masked sum, including negative masked energies.
- Legal/oracle split: legal context comes from the original observation and public env config; hidden state is separately recorded. Unknown/negative-energy enemies cannot qualify for can_move_to_unit. Cost-only margins explicitly disclaim simultaneous effects and cannot be read as measured damage/collision outcomes. No causal damage attribution is claimed.
- pt_sap: inference conservatively requires late STAY-to-SAP, enabled pt_sap and no competing flags/CNN. All current competing late branches are accounted for; false negatives with enabled-but-inactive competing flags are intentional uncertainty, not false attribution.
- Output/reference: exclusive output directory/raw files, fixed hashes, source/input/HEAD checks before and after games, exact selected 20 keys, comparison of all 23 non-time GAME_FIELDS, 303 transitions, three matches and twelve snapshots are enforced. Input/source hashes bind bytes to this run; reviewed unchanged source/HEAD remains an operational prerequisite.
- `git diff --check ec29a17 4503dba` passed. No other actionable findings within the authorized narrow scope.

Recommendation: correct the frame/schema issue and verify the targeted player-1 regression before releasing the 20-game batch. Batch reproduction remains outstanding and is not implied by the existing unit/suite results.

## Scoped re-review — 525060f approved

Reviewed the packaged `32f0694..525060f` diff on 21 October 2026. The prior P2 is resolved; no additional findings in this delta.

- `before_rule`, `after_rule`, and `recorded_action_class` now use the existing agent geometry's world direction conversion when the belief is mirrored.
- The legal mask is reordered with the same mirror permutation. This is correct because the direction permutation `[0,2,1,4,3]` is an involution: each real index selects its corresponding canonical entry. STAY and SAP remain unchanged; both five-class and six-class masks are handled.
- Conversion affects only copied diagnostic values. `record_rule` still returns the original unconverted result to the agent; the final action array, agent's stored classes and original masks are untouched. Thus the fix does not change action selection or RNG behavior.
- The new regression uses the exact player-1 boundary counterexample, asserts the three emitted classes agree with real UP, and checks the complete real-space mask plus final-action legality.
- Inspected `/tmp/sherlock-loss-observer-frame-focused.log`: **9 passed in 2.05 s**. `git diff --check 32f0694 525060f` passed. No tests were rerun by this reviewer, and no games/model jobs were started.

Final review disposition: **Approved for the planned fixed 20-game diagnostic batch**, with reference reproduction and output-integrity checks still required during and after that batch. This approval is for observer correctness within the stated passive scope, not a preemptive claim that the unrun batch reproduces its reference.
