# Inference development comparison

All three datasets passed the completion, exact-key, frozen-file and baseline reproduction checks. Scores are mean result; draws count as 0.5.

| Candidate | Opponent | Reference | Candidate | Delta | 95% paired-map interval |
|---|---|---:|---:|---:|---:|
| active | default | 100.00% | 100.00% | +0.00 pp | [+0.00, +0.00] pp |
| active | solution92 | 85.00% | 86.67% | +1.67 pp | [-2.50, +5.83] pp |
| sap | default | 100.00% | 100.00% | +0.00 pp | [+0.00, +0.00] pp |
| sap | solution92 | 85.00% | 85.83% | +0.83 pp | [-2.50, +5.00] pp |

Selected for fresh confirmation: **none**.
Reason: `no_eligible_candidate`.

Solution92 delta > 0 and lower95 > 0; default delta >= -0.02. If two qualify, larger Solution92 delta; exact tie selects none.

Each comparison uses the same 60 maps on both sides, 5,000 whole-map bootstrap draws with RNG seed 0. The two candidate intervals are unadjusted. These reused development maps select a direction; they do not constitute fresh confirmation.

No job or promotion is triggered. A selected candidate still needs the separately reserved fresh comparison and technical release checks.

Frozen experiment HEAD: `4ca353ef2af38bdaea9c1d3a4b70525020006dc5`.
