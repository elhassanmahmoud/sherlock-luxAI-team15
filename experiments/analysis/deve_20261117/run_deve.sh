#!/bin/bash
# Dev-E-Vergleich (PLAN.md, 17.11.2026): R3, S8, S9, S9H, P8, P9 auf 7258000-7258199 gegen Solution und Kaggle,
# danach zur Information direkt gegen R3 auf 7258000-7258049. Streng nacheinander, 10 Prozesse.
#   run_deve.sh FROZEN_DIR
set -u
FROZEN=$1
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/deve_20261117
SEEDS=$D/seeds_devE.json; DS=$D/seeds_devE_direkt.json
R3ZIP=$FROZEN/experiments/releases/20261116_r3_finale/agent.zip
S=$FROZEN/experiments/imitation/students
SW=(--set imit_stay_bias=1.5 --set imit_unstack=true)
log() { echo "$(date '+%H:%M:%S') $*"; }
log "START Quelle $(cat SOURCE_HEAD.txt)"
shasum -a 256 $R3ZIP $S/ens_v8_v8L.pth $S/ens_v9_v8L.pth
run() { name=$1; seeds=$2; shift 2; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval "$@" --seed-list $seeds --workers 10 --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run r3_devE $SEEDS --weights "r3zip:$R3ZIP" --opponents solution92,kaggle3
run s8_devE $SEEDS --weights "r3t:schueler=ens8" --opponents solution92,kaggle3
run s9_devE $SEEDS --weights "r3t:schueler=ens9" --opponents solution92,kaggle3
run s9h_devE $SEEDS --weights "r3t:schueler=ens9,schueler_halter" --opponents solution92,kaggle3
run p8_devE $SEEDS --weights $S/ens_v8_v8L.pth --opponents solution92,kaggle3 "${SW[@]}"
run p9_devE $SEEDS --weights $S/ens_v9_v8L.pth --opponents solution92,kaggle3 "${SW[@]}"
log "DEVE_EXTERN_DONE"
run s8_direkt $DS --weights "r3t:schueler=ens8" --opponents "r3zip:$R3ZIP"
run s9_direkt $DS --weights "r3t:schueler=ens9" --opponents "r3zip:$R3ZIP"
run s9h_direkt $DS --weights "r3t:schueler=ens9,schueler_halter" --opponents "r3zip:$R3ZIP"
run p8_direkt $DS --weights $S/ens_v8_v8L.pth --opponents "r3zip:$R3ZIP" "${SW[@]}"
run p9_direkt $DS --weights $S/ens_v9_v8L.pth --opponents "r3zip:$R3ZIP" "${SW[@]}"
log "DEVE_DONE"
