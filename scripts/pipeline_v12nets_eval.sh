#!/bin/bash
# 22.10.2026: nach dem zweiten Netz-Training (pipeline_v8nets_b.sh): Ensembles mit V10-Config aus
# 18 V3-Netzen + 12 neuen (v10mix30) und nur den 12 neuen (v10nets12), Entwicklungsmessung gegen V10.
cd "$(dirname "$0")/.."
PY=.venv/bin/python
E=experiments/ensembles
R=experiments/runs/20261022_full_rules_v8_s
NEW=""
for s in 70 71 72 80 81 82 60 61 62 90 91 92; do NEW="$NEW ${R}${s}_sol70/weights/agent.pth"; done
$PY -m scripts.build_ensemble --out $E/v10mix30_raw.pth $E/v10_V8st.pth $NEW
$PY -m scripts.build_ensemble --out $E/v10nets12_raw.pth $NEW
$PY - <<'PY'
import torch
v10 = torch.load("experiments/ensembles/v10_V8st.pth", map_location="cpu", weights_only=False)
for name in ("v10mix30", "v10nets12"):
    ck = torch.load(f"experiments/ensembles/{name}_raw.pth", map_location="cpu", weights_only=False)
    ck["cfg"] = dict(v10["cfg"])
    torch.save(ck, f"experiments/ensembles/{name}.pth")
    print(name, "Netze", 1 + len(ck.get("ensemble", [])))
PY
shasum -a 256 $E/v10mix30.pth $E/v10nets12.pth
bash experiments/analysis/hard_map_training_20261021/dev_eval2.sh v10mix30 ${WORKERS:-7} $E/v10mix30.pth &
bash experiments/analysis/hard_map_training_20261021/dev_eval2.sh v10nets12 ${WORKERS:-7} $E/v10nets12.pth &
wait
echo "Ende"
