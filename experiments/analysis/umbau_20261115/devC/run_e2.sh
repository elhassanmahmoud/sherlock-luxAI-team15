#!/bin/bash
# Nachtrag zu run_e.sh (17.11.2026, 03:39, vor dem ersten Dev-C-Ergebnis): reiner Ensemble-Schüler v7 + v7L auf Dev C.
# Gleiche Leseregel wie in PLAN.md. Startet erst, wenn run_e.sh fertig ist (nie parallel).
SP=/private/tmp/claude-501/-Users-elhassanmahmoud-Documents-AKI-LuxAgent15/d5bcfcfa-cd35-4364-b2b5-1a6260ee2252/scratchpad
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $SP/frozen_v6 || exit 1
PY=$MAIN/.venv/bin/python
S=$MAIN/experiments/imitation/students
D=$MAIN/experiments/analysis/umbau_20261115/devC
DEVC=$MAIN/experiments/analysis/kaggle3_20261115/seeds_devC.json
R3=r3zip:$MAIN/experiments/releases/20261116_r3_finale/agent.zip
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 240); do grep -q E_DONE $SP/run_e.log 2>/dev/null && break; sleep 30; done
grep -q E_DONE $SP/run_e.log || { log "run_e nicht fertig, Abbruch"; exit 1; }
log "START Quelle $(head -1 SOURCE_HEAD.txt)"
[ -f $D/student_ens_v7_v7L_devC.csv ] || $PY -m scripts.par_eval --weights $S/ens_v7_v7L.pth \
    --opponents solution92,kaggle3,$R3 --set imit_stay_bias=1.5 --set imit_unstack=true --seed-list $DEVC \
    --workers 10 --out $D/student_ens_v7_v7L_devC.csv 2>&1 | grep -E "csv:|Error|Traceback"
shasum -a 256 $S/ens_v7_v7L.pth
log "E2_DONE"
