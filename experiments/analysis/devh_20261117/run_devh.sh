#!/bin/bash
# Dev H (PLAN.md, 17.11.2026, abends): alle Taktiken und der Matchende-Sturm auf dem empfohlenen Schüler K,
# auf 7266000-7266199 gegen Solution und Kaggle, 10 Prozesse, streng nacheinander.
#   run_devh.sh FROZEN_DIR
set -u
FROZEN=$1
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/devh_20261117
W=$FROZEN/experiments/imitation/students/ens_v9_v8L.pth
SEEDS=$D/seeds_devH.json
K=(--set imit_stay_bias=1.0 --set imit_unstack=true --set imit_hold_points=true)
T7=granate+nebel+sog+sparen+wechsel+erobern+tanken
log() { echo "$(date '+%H:%M:%S') $*"; }
log "START Quelle $(cat SOURCE_HEAD.txt)"
shasum -a 256 $W
run() { name=$1; shift; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval --weights $W "${K[@]}" "$@" --opponents solution92,kaggle3 --seed-list $SEEDS --workers 10 \
      --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run k_devH
run ende10_devH --set imit_end_fill=10
run ende20_devH --set imit_end_fill=20
run alle_devH --set imit_tactics=$T7 --set imit_end_fill=10 --set end_sap=10 --set focus_sap=true --set imit_cover=0.5 \
    --set imit_sap_bias=0.5
run endsap_devH --set end_sap=10
run granate_devH --set imit_tactics=granate
run nebel_devH --set imit_tactics=granate+nebel
run sog_devH --set imit_tactics=sog
run focus_devH --set focus_sap=true
run sparen_devH --set imit_tactics=sparen
run wechsel_devH --set imit_tactics=wechsel
run erobern_devH --set imit_tactics=erobern
run tanken_devH --set imit_tactics=tanken
run cover_devH --set imit_cover=0.5
run sapbias_devH --set imit_sap_bias=0.5
log "DEVH_DONE"
