#!/bin/bash
# Nachtrag 2 zum Taktiktest (PLAN.md): Schüler auf R3 und Vergleich mit dem Hybrid auf Dev D. Startet nach run_screen2.sh.
#   run_screen3.sh FROZEN_DIR SCREEN2_LOG
set -u
FROZEN=$1; PREV_LOG=$2
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/r3t_20261117
SEEDS=$D/seeds_devD.json
HYB=$MAIN/experiments/imitation/releases/ens_v8_v8L_mixed/weights/agent.pth
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 360); do grep -q SCREEN2_DONE $PREV_LOG 2>/dev/null && break; sleep 20; done
grep -q SCREEN2_DONE $PREV_LOG || { log "zweiter Durchgang nicht fertig, Abbruch"; exit 1; }
log "START Quelle $(cat SOURCE_HEAD.txt)"
run() { name=$1; w=$2; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval --weights "$w" --opponents solution92,kaggle3 --seed-list $SEEDS --workers 10 \
      --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run schueler_devD "r3t:schueler=ens8"
run schueler_alle_devD "r3t:schueler=ens8,granate,sog,tanken"
run hyb_ens8_devD "$HYB"
for v in "schueler=ens8" "schueler=ens8,granate,sog,tanken"; do
  name=diag_$(echo $v | tr ',=' '__')
  [ -f $D/$name/matches.csv ] || $PY experiments/analysis/r3_kaggle_20261117/diagnose.py --agent "r3t:$v" \
      --seeds 7256000:7256030 --workers 10 --out $D/$name 2>&1 | grep -E "Spiele|Error|Traceback"
done
shasum -a 256 $FROZEN/experiments/imitation/students/ens_v8_v8L.pth $HYB
log "SCREEN3_DONE"
