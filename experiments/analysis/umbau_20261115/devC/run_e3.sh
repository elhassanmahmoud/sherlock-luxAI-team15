#!/bin/bash
# Nachtrag 2 (17.11.2026, 05:58, vor dem ersten Dev-C-Spiel dieses Kandidaten): Hybrid Ensemble v8 + v8L auf Dev C.
# Gleiche Leseregel wie in PLAN.md. Ausgewählt nur nach Dev A (+2,25 gegen Solution+Kaggle). Letzter Dev-C-Kandidat.
# Eingefrorene Quelle 8324845 (frozen_v6). Läuft allein, keine anderen Spiel- oder Trainingsprozesse.
SP=/private/tmp/claude-501/-Users-elhassanmahmoud-Documents-AKI-LuxAgent15/d5bcfcfa-cd35-4364-b2b5-1a6260ee2252/scratchpad
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $SP/frozen_v6 || exit 1
PY=$MAIN/.venv/bin/python
R=$MAIN/experiments/imitation/releases
D=$MAIN/experiments/analysis/umbau_20261115/devC
DEVC=$MAIN/experiments/analysis/kaggle3_20261115/seeds_devC.json
R3=r3zip:$MAIN/experiments/releases/20261116_r3_finale/agent.zip
log() { echo "$(date '+%H:%M:%S') $*"; }
log "START Quelle $(head -1 SOURCE_HEAD.txt)"
[ -f $D/hyb_ens_v8_v8L_mixed_devC.csv ] || $PY -m scripts.par_eval --weights $R/ens_v8_v8L_mixed/weights/agent.pth \
    --opponents solution92,kaggle3,$R3 --seed-list $DEVC --workers 10 --out $D/hyb_ens_v8_v8L_mixed_devC.csv 2>&1 \
    | grep -E "csv:|Error|Traceback"
shasum -a 256 $R/ens_v8_v8L_mixed/weights/agent.pth $MAIN/experiments/releases/20261116_r3_finale/agent.zip
log "E3_DONE"
