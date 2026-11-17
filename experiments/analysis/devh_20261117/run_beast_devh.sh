#!/bin/bash
# Beast-Kombination einmal auf Dev H (PLAN.md, Abschnitt "Beast-Kandidat"), nur wenn mehrere Module helfen.
# Wartet auf das Ende von run_devh.sh. Schalter wie von analyze_devh.py ausgegeben.
#   run_beast_devh.sh FROZEN_DIR PREV_LOG KEY=VALUE...
set -u
FROZEN=$1; PREV_LOG=$2; shift 2
PREV_LOG=$(cd "$(dirname "$PREV_LOG")" && pwd)/$(basename "$PREV_LOG")  # absolut, vor dem cd
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/devh_20261117
W=$FROZEN/experiments/imitation/students/ens_v9_v8L.pth
SW=(--set imit_stay_bias=1.0 --set imit_unstack=true --set imit_hold_points=true); for kv in "$@"; do SW+=(--set "$kv"); done
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 1080); do grep -q DEVH_DONE $PREV_LOG 2>/dev/null && break; sleep 10; done
grep -q DEVH_DONE $PREV_LOG || { log "Dev H nicht fertig, Abbruch"; exit 1; }
log "START Quelle $(cat SOURCE_HEAD.txt), Beast-Schalter $*"
[ -f $D/beast_devH.csv ] || $PY -m scripts.par_eval --weights $W "${SW[@]}" --opponents solution92,kaggle3 \
    --seed-list $D/seeds_devH.json --workers 10 --out $D/beast_devH.csv 2>&1 | grep -E "csv:|Error|Traceback"
log "BEAST_DONE"
