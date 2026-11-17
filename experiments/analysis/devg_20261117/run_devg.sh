#!/bin/bash
# Dev-G-Vergleich (PLAN.md, 17.11.2026): R3, PS (Ensemble v9 + v8L), E10 (v10 + v8L) und E3 (v10 + v9 + v8L), alle
# Schüler mit den Schaltern S, auf 7264000-7264199 gegen Solution und Kaggle. Startet nach DAgger-Runde 7 und v10.
#   run_devg.sh FROZEN_DIR PREV_LOG SCHALTER...
set -u
FROZEN=$1; PREV_LOG=$2; shift 2
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/devg_20261117
S=$FROZEN/experiments/imitation/students
SEEDS=$D/seeds_devG.json
R3ZIP=$FROZEN/experiments/releases/20261116_r3_finale/agent.zip
SW=(); for kv in "$@"; do SW+=(--set "$kv"); done
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 720); do grep -q DAGGER7_ALL_DONE $PREV_LOG 2>/dev/null && break; sleep 20; done
grep -q DAGGER7_ALL_DONE $PREV_LOG || { log "DAgger 7 nicht fertig, Abbruch"; exit 1; }
log "START Quelle $(cat SOURCE_HEAD.txt), Schalter $*"
[ -f $S/ens_v10_v9_v8L.pth ] || $PY -m scripts.imitate ensemble --students $S/v10_from_v9.pth $S/v9_from_v8.pth \
    $S/v8L_from_v7L.pth --out $S/ens_v10_v9_v8L.pth 2>&1 | grep -v Warn
shasum -a 256 $R3ZIP $S/ens_v9_v8L.pth $S/ens_v10_v8L.pth $S/ens_v10_v9_v8L.pth
run() { name=$1; shift; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval "$@" --seed-list $SEEDS --workers 10 --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run r3_devG --weights "r3zip:$R3ZIP" --opponents solution92,kaggle3
run ps_devG --weights $S/ens_v9_v8L.pth --opponents solution92,kaggle3 "${SW[@]}"
run e10_devG --weights $S/ens_v10_v8L.pth --opponents solution92,kaggle3 "${SW[@]}"
run e3_devG --weights $S/ens_v10_v9_v8L.pth --opponents solution92,kaggle3 "${SW[@]}"
log "DEVG_DONE"
