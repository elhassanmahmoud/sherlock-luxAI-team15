#!/bin/bash
# Nachtrag 1 zum Taktiktest (PLAN.md): vier weitere Varianten auf Dev D, gleiche Regel. Startet erst nach run_screen.sh.
#   run_screen2.sh FROZEN_DIR SCREEN_LOG
set -u
FROZEN=$1; PREV_LOG=$2
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/r3t_20261117
SEEDS=$D/seeds_devD.json
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 360); do grep -q SCREEN_DONE $PREV_LOG 2>/dev/null && break; sleep 20; done
grep -q SCREEN_DONE $PREV_LOG || { log "erster Durchgang nicht fertig, Abbruch"; exit 1; }
log "START Quelle $(cat SOURCE_HEAD.txt)"
run() { name=$1; w=$2; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval --weights "$w" --opponents solution92,kaggle3 --seed-list $SEEDS --workers 10 \
      --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run nebel_devD "r3t:granate,nebel"
run erobern_devD "r3t:erobern"
run sparen_devD "r3t:sparen"
run wechsel_devD "r3t:wechsel"
for v in "granate,nebel" erobern sparen wechsel; do
  name=diag_$(echo $v | tr ',' '_')
  [ -f $D/$name/matches.csv ] || $PY experiments/analysis/r3_kaggle_20261117/diagnose.py --agent "r3t:$v" \
      --seeds 7256000:7256030 --workers 10 --out $D/$name 2>&1 | grep -E "Spiele|Error|Traceback"
done
log "SCREEN2_DONE"
