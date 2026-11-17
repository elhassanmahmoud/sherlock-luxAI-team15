#!/bin/bash
# Zweite Prüfung (PLAN.md): R3, SCHUELER, SCHUELER_ALLE, HYB_ENS8 auf 7256200-7256399, gegen Solution und Kaggle.
#   run_check2.sh FROZEN_DIR
set -u
FROZEN=$1
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/r3t_20261117
SEEDS=$D/seeds_check2.json
R3=r3zip:$FROZEN/experiments/releases/20261116_r3_finale/agent.zip
HYB=$MAIN/experiments/imitation/releases/ens_v8_v8L_mixed/weights/agent.pth
log() { echo "$(date '+%H:%M:%S') $*"; }
log "START Quelle $(cat SOURCE_HEAD.txt)"
run() { name=$1; w=$2; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval --weights "$w" --opponents solution92,kaggle3 --seed-list $SEEDS --workers 10 \
      --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run r3_check2 $R3
run schueler_check2 "r3t:schueler=ens8"
run schueler_alle_check2 "r3t:schueler=ens8,granate,sog,tanken"
run hyb_ens8_check2 "$HYB"
shasum -a 256 $FROZEN/experiments/releases/20261116_r3_finale/agent.zip $FROZEN/experiments/imitation/students/ens_v8_v8L.pth $HYB
log "CHECK2_DONE"
