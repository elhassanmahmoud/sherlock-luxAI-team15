# Independent resource-cost review, before fresh outcomes

**Recommendation: approve the simpler existing seven-opponent par_eval path and
two predeclared timing classes.** No model/game or driver/repository edit made by
this review. This is design approval, not acceptance of a new implementation.

The current global maximum of every job's wall seconds/game confounds inherently
different workloads. A direct ensemble duel is costlier than the fixed mixed
panel. Applying its rate to all future panel games is unnecessarily pessimistic;
separating fixed workload classes does not change sample size, gates, candidates,
nomination or inference targets. Timing updates must use time/counts only, never
wins or intermediate gate results.

## Independently verified historical evidence

Read only old `experiments/analysis/night_20261101/{selection,confirmation200}_state.json`
and their already-consumed CSVs. Every CSV matched the recorded SHA before timing
extraction. Full compact numbers: `historical_cost_class_review.json`.

- Seven-opponent jobs, two workers: 2.0335–2.1952 wall seconds/game in selection;
  2.0444/2.0984 in confirmation. Thus **2.22** is a conservative historical floor
  for this same combined workload, not for a new serial-default design.
- Direct jobs, two workers: 2.8720–2.9848 in selection and 2.8056 in confirmation.
  **3.0** is a rounded historical floor.
- Old default row-duration means: maximum2.5729 process seconds/game while two
  workers ran. Old jobs mixed panel+default; exact separate wall timing is not
  recorded. Reconstructing worker streams and allocating all job overhead to the
  six-opponent part gave a maximum panel estimate2.34735 wall seconds/game, but
  this remains a reconstruction rather than a separately measured new job.

The proposed three-class design was methodologically valid, but introduced the
serial-default cost unnecessarily. Existing par_eval delegates `default` to
common.make_opponent, and the old real seven-opponent runs exercised that exact
path successfully. No demonstrated incompatibility requires the monkeypatch
adapter. Keep six opponents in the statistical panel; the seventh default stays
an independent safety metric even when its games share the execution job.

## Approved timing rule to freeze before 841 games

Classes: `combined_panel` = seven opponents at two workers, initial2.22;
`direct` = direct V14 games at two workers, initial3.0 wall seconds/game.
For each class retain the maximum measured complete-job wall/game rate over all
roles/phases; never lower a rate after observing outcomes. For common thermal/load
risk, let slowdown=max(1, each observed_class_max / initial_class_rate), and use
max(observed_class_max, initial_class_rate×slowdown) for each class. This preserves
relative workload costs while applying any observed relative slowdown globally.

Project **1.2 × sum(exact remaining games per class × effective class rate)**,
then add the unchanged3600-second closure reserve before04:30Z/05:30Berlin.
Selection must also budget the entire possible confirmation:8400 combined+600
direct. Actual selection:4200combined+400direct (five jobs). Confirmation:8400+
600 (three jobs). No extra division by worker count. Retain hard model cutoff,
battery/resource rules, fresh outputs and incomplete-phase rejection.

At initial rates:

| Phase | Base | With20% |
|---|---:|---:|
| Selection4600 |175.40min|210.48min|
| Confirmation9000 |340.80min|408.96min|

Both+60min closure = **679.44min =11h19m26s**. Latest selection start before05:30
is **18:10:34 Berlin**; latest confirmation is **21:41:02**. These are upper
bounds on start times, not promised throughput; slower new jobs only move them
earlier. Remaining training, candidate audit, source commit/freeze and checks
must finish before selection admission.

For comparison, the earlier serial-default proposal at2.4/2.5729/2.9848 needed
227.55min selection +443.17min confirmation +60closure =12h10m43s. Its “8h24”
confirmation estimate already included the60-minute closure; do not count that
reserve twice. Global3.0 for all9000 would budget540min+60 for confirmation and
could reject a feasible fixed mix. Conversely, old global2.22 underestimates the
new direct weighting slightly; use the exact two-class calculation above.

Required before execution: amend and freeze the protocol/manifest timing rule,
review the runner change and combined-job CSV/statistics schema, keep independent
complete-data admission and all statistical gates unchanged. No partial phase
may qualify if new runtimes later make the deadline infeasible.
