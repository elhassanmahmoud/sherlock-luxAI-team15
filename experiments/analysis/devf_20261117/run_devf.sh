#!/bin/bash
# Dev-F-Vergleich (PLAN.md, 17.11.2026): R3 und der reine Schüler PB mit vier Schaltereinstellungen auf
# 7259000-7259199 gegen Solution und Kaggle. Streng nacheinander, 10 Prozesse.
#   run_devf.sh FROZEN_DIR BASIS_SCHUELER (ens_v8_v8L.pth oder ens_v9_v8L.pth)
set -u
FROZEN=$1; BASE=$FROZEN/experiments/imitation/students/$2
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/devf_20261117
SEEDS=$D/seeds_devF.json
R3ZIP=$FROZEN/experiments/releases/20261116_r3_finale/agent.zip
log() { echo "$(date '+%H:%M:%S') $*"; }
log "START Quelle $(cat SOURCE_HEAD.txt), Basis $2"
shasum -a 256 $R3ZIP $BASE
run() { name=$1; shift; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval "$@" --seed-list $SEEDS --workers 10 --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run r3_devF --weights "r3zip:$R3ZIP" --opponents solution92,kaggle3
run pb_devF --weights $BASE --opponents solution92,kaggle3 --set imit_stay_bias=1.5 --set imit_unstack=true
run pb_h_devF --weights $BASE --opponents solution92,kaggle3 --set imit_stay_bias=1.5 --set imit_unstack=true \
    --set imit_hold_points=true
run pb_s10_devF --weights $BASE --opponents solution92,kaggle3 --set imit_stay_bias=1.0 --set imit_unstack=true
run pb_s10_h_devF --weights $BASE --opponents solution92,kaggle3 --set imit_stay_bias=1.0 --set imit_unstack=true \
    --set imit_hold_points=true
run pb_hf_devF --weights $BASE --opponents solution92,kaggle3 --set imit_stay_bias=1.5 --set imit_unstack=true \
    --set imit_hold_points=true --set imit_fill_points=6
run pb_s10_hf_devF --weights $BASE --opponents solution92,kaggle3 --set imit_stay_bias=1.0 --set imit_unstack=true \
    --set imit_hold_points=true --set imit_fill_points=6
log "DEVF_DONE"
