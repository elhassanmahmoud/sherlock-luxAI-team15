# Observational holder-departure diagnostic

08 November 2026. Existing historical traces only; no games, models, tests, or repository edits.

## Result

The conservative observable hold screen has **zero qualifying decisions in both groups**. These traces do not currently support a no-visible-nearby-enemy, nonnegative-field-energy hold intervention. Most recorded departures occur with a visible armed enemy nearby; this does not establish that departing is optimal, but prevents calling these departures needless or safe to override.

The 12 traces contain six selected loss games on four maps and six historical control games on three maps. Controls are not matched or representative. All three matches are included, including won matches inside lost games. Decisions, units, sides, vacancy windows, and repeated states are dependent.

## Exact population

Stored `sole_holder=true`, own energy >=0, assigned target equals current position, canonical final action in 1..4, and destination is not a currently known point. This reproduces 211 loss-game and 66 control departures. Every selected final action equals masked Q argmax. The underlying sole-holder step counts are 7009 and 8781.

| Observation | Loss decisions /211 | Control decisions /66 |
|---|---:|---:|
| Current tile energy negative / zero / positive | 52 /12 /147 | 18 /6 /42 |
| Destination tile energy negative / zero / positive | 8 /16 /187 | 11 /1 /54 |
| Destination field energy higher / same / lower | 130 /16 /65 | 39 /7 /20 |
| Current tile nebula | 8 | 9 |
| Destination tile nebula | 7 | 8 |
| Any visible enemy within Chebyshev(sap_range+1) of origin | 206 | 62 |
| Nonnegative visible enemy within that radius | 204 | 62 |
| Armed visible enemy (energy >= sap_cost) within that radius | 203 | 62 |
| Own energy >= move_cost+sap_cost | 148 | 41 |
| At least12 steps remaining (100−match_step) | 210 | 64 |
| Both energy and remaining-step conditions | 147 | 41 |
| Both +current tile nonnegative field energy +nonnebula +STAY legal | 102 | 23 |
| Above +no visible enemy within stated radius | **0** | **0** |
| Origin unoccupied in next same-match observation | 174 | 62 |
| Origin unoccupied for at least3 consecutive observations | 72 | 40 |
| Origin unoccupied for at least5 consecutive observations | 47 | 28 |
| Vacancy right-censored by match/reset boundary | 16 | 9 |

| Numeric summary | Loss median [min,max] | Control median [min,max] |
|---|---:|---:|
| Own energy | 47 [1,161] | 55 [10,182] |
| Current field energy | 2 [−5,9] | 1 [−5,9] |
| Destination field energy | 4 [−7,10] | 4 [−4,8] |
| Remaining match steps | 44 [10,67] | 37 [2,83] |
| Q(STAY)−Q(selected movement) | −1.51785 [−8.35864,−0.00397] | −0.98612 [−6.46373,−0.02190] |
| Consecutive vacant following observations | 1 [0,65] | 3 [0,44] |

All current tile field-energy readings have observation age0 and current tile sensor visibility. Destination is currently visible in210/211 and64/66 decisions; destination field energies elsewhere are agent memory, not guaranteed current truth.

## What eliminates the proposed screen

The only five loss-group departures with no observed enemy in the specified radius all leave **negative-energy points** for positive-energy nonpoints:

| Seed/side, observation, UID | Own energy | Current → destination field energy | Vacancy observations |
|---|---:|---:|---:|
| 831043/P0,235,3 | 37 | −1→2 | 1 |
| 831043/P0,237,3 | 36 | −1→2 | 1 |
| 831043/P0,239,3 | 35 | −1→2 | 6 |
| 831043/P1,242,6 | 97 | −3→2 | 1 |
| 831043/P1,247,4 | 68 | −3→2 | 7 |

The four corresponding control decisions are831001/P0 andP1, observations118/120, UID1, current−4→destination5, energy98/97, vacancy1/0. No visible enemy is not equivalent to no hidden enemy. These small repeated negative-field cases suggest an energy-versus-immediate-point tradeoff for a future diagnostic, not a demonstrated repair or permission to relax the screen until it triggers.

## Interpretation and limits

Vacancy counts consecutive following pre-action observations with no nonnegative ally at the original coordinate, stopping on reoccupation or match/reset boundary. Zero means immediately reoccupied; right censoring is recorded. Windows overlap and are not independent or additive lost points. Actual productive point availability, terrain drift, combat response, and a counterfactual STAY trajectory are not inferred. Q gaps are raw incumbent ensemble units, not calibrated expected-point losses. Stronger Q preference for movement does not establish movement optimality.

The earlier high departure count alone was insufficient support for a hold patch. The added conditions supply a useful negative result: a conservative hold-vs-base intervention would have no effect on this historical trace population. Do not start a performance study of that exact inactive screen or broaden it post hoc while calling it the same hypothesis. Separately investigate energy/pressure-aware holding if authorized, with conditions fixed before new outcomes.

## Files

- `/tmp/sherlock-holder-diagnostic.py`: standard-library-only calculation; reads all12 gzipped source traces and writes JSON.
- `/tmp/sherlock-holder-diagnostic.json`: full277 decision records, exact per-group distributions, screen summaries, and SHA256 identities of all12 original traces.
- Source directory: `experiments/analysis/continuation_20261102/targeting/`.

No source trace or repository file was changed.
