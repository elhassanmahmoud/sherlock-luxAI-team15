# Independent final P-only fallback implementation review

**Specification: PASS. Code quality: PASS. No open Important/Critical findings.**
Reviewed only the new `/tmp/sherlock-continue-20261102/p_only_fallback/` copies
against the already accepted fallback design and the preceding full-tool review.

## Verified hashes

- Driver: `7700ba0ab0bb2eda3d7ced9b252da615af10669ddb42b58f23e3ae0940610308`
- Builder: `7be85c7f8bc2f55888c78ae3603a56df0d7ae546225fcb8c1f196cb1df550102`
- Statistics: `2916fd4e8e68dcd1cabac45c210bb871a97e0587cd408217b51d34ae39f8378e`
- Driver tests: `14b10b5bc6d2483e7524e0fed22dc9e3c42896d09ad38ae7ec55016325ae324a`
- Builder tests: `8fd4825efdf8fd32d6b4378fb60291db41ca9328f44cca3dadb109a2d25598ad`
- Statistics tests: `0ab6ea0fad16c81277850fe7eaae5cdd63c24abb6c9f36aa6c03faaba604aba1`

Independently rehashed all seven original files listed in initial_copy_manifest:
**all unchanged**. The stable original tools were not modified by the fallback.

## Findings

- Driver allowlists exactly baseline+P or baseline+P+PT. Job construction derives
  roles from this frozen roster. P-only is3jobs/3000selection games; full remains
  5jobs/4600. Both retain100selection maps. Confirmation remains3jobs/9000 with
  300panel/default maps and300separate direct maps. PT confirmation is rejected
  when absent from the original roster.
- Shared freeze hashes, fixed job reconstruction and selection receipt/summary
  checks remain intact. Extending/replacing the master after selection changes
  the bound freeze and is rejected; no late PT addition or runner-up path.
- Builder's --p-only and --audit modes are mutually exclusive in CLI and function
  entry, before Torch import for invalid combinations. P-only reads only the
  exact-SHA V14 source and its own saved output, retaining all36 ordered states
  and changing only the two P flags. It neither reads training end checkpoints
  nor claims a training audit: training_audit_used=false, no audit_path/hash,
  empty replacement inputs, only P output and no replaced indices.
- Full builder mode still requires an ACCEPTED audit, no failed checks/warnings,
  exactly all four arms and unchanged evidence hashes, including the adapted
  finals. Both18/19 are replaced; all other34 states and source config apart from
  the P flags remain exact. No partial PT fallback was introduced.
- Statistics derives selection candidates and expected3000/4600total from the
  validated immutable roster. Confirmation total remains9000. The PANEL6/default
  split, whole-map paired bootstrap, gates, draw valuation, P-before-PT tie rule,
  direct outcome counts and exact completeness checks are otherwise unchanged.
  P-only does not automatically nominate P: it must pass all existing gates.
- The diff leaves two-worker execution, class-rate carryover/global relative
  slowdown, remaining9000confirmation budget,20%time margin,60minute closure,
  battery rules, source/model/interpreter pins, path normalization, protected
  spawn/cleanup and owned-receipt reservation unchanged.

## Evidence and execution boundary

Inspected the narrow source diffs and new tests, including P-only3000→9000 file
pipeline, immutable roster/late PT rejection, mutual exclusivity, source-only P
build, missing-arm rejection and unchanged full-mode output. Read final_unittest.log:
49tests passed in1.719s, no skips (22driver+16statistics+11builder), as reported by
Root/implementer. Did not rerun that suite. No concrete new defect required an
additional counterexample.

No repository edits, model/tensor loads, training, environment games or fresh
outcomes were performed/read by this review. This PASS does not choose a route
or start a study. Root must record the resource-based route before the first841
outcome and freeze the chosen copies/artifacts. P-only initial latest selection
19:24:43Berlin and confirmation21:41:02 remain conditional on actual slowdown and
resource admission;33%battery without AC still forbids a new long phase under
the current thresholds. The adaptation deadline is not extended by this fallback.
