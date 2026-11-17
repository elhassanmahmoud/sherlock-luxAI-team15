#!/bin/bash
# Dev-H-Nachträge (PLAN.md, 20:08 und 20:39): ENDE10F und MASKFREI auf 7266000-7266199 gegen Solution und Kaggle,
# 10 Prozesse, nach dem letzten Dev-H-Agenten. Eingefrorene Quelle mit dem Schalter imit_end_force.
#   run_devh_nachtrag.sh FROZEN_DIR PREV_LOG
set -u
FROZEN=$1; PREV_LOG=$2
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/devh_20261117
W=$FROZEN/experiments/imitation/students/ens_v9_v8L.pth
SEEDS=$D/seeds_devH.json
K=(--set imit_stay_bias=1.0 --set imit_unstack=true --set imit_hold_points=true)
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 1080); do grep -q DEVH_DONE $PREV_LOG 2>/dev/null && break; sleep 10; done
grep -q DEVH_DONE $PREV_LOG || { log "Dev H nicht fertig, Abbruch"; exit 1; }
log "START Quelle $(cat SOURCE_HEAD.txt)"
shasum -a 256 $W
run() { name=$1; shift; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval --weights $W "${K[@]}" "$@" --opponents solution92,kaggle3 --seed-list $SEEDS --workers 10 \
      --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run ende10f_devH --set imit_end_fill=10 --set imit_end_force=true
run maskfrei_devH --set safe_moves=false --set collision_guard=false
log "NACHTRAG_DONE"
