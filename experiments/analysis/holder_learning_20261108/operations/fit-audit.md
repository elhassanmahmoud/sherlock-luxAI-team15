# Independent fixed-fit audit — PASS

Reconstructed all162 rows ×16 public features independently from raw training candidates, excluding the stored79-vector and all branch/hidden fields from feature extraction. Retained92 positive,50 negative and20 zero labels across20 represented training maps. No validation data read; no project modules or Torch imported.

Applied equal map mass1/20, training-only weighted means/population standard deviations, scale1 for the single near-zero variance feature, z clipping to[-5,5], and fixed ridge0.1 with unpenalized intercept. Independently solved the augmented weighted least-squares system; no alternative penalties, thresholds, features or refits proposed.

Maximum absolute reproduction errors: mean 0, scale 0, coefficients/intercept 4.22e-15, predictions 2.22e-14; all below1e-11. Every training threshold decision matches. Saved coefficients also satisfy the weighted ridge optimality equations (max residual 2.72e-15).

Exact feature/schema/cadence/H12/threshold1.0 and adequacy report verified. Receipt, plan, head, training manifest, all192 training artifacts, all330 sources, executable and protected V14 files match their pins under759c8fa1908184de04421ee9fb3547e55bf7663a. Head SHA-256:0f61a4070020dab415ce02ae76f4c752533d4f97e58af7ece2bcffc09d4a8dc4. Source checksum audit complete; source remains unchanged.

1085 checks. Full independently reconstructed features, row weights, labels and predictions are recorded in fit-audit.json. This accepts fit arithmetic/provenance; it does not establish validation or gameplay improvement.
