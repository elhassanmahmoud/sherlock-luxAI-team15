#!/bin/bash
# Frische Bestätigung (BESTAETIGUNG_PLAN.md) auf 7260000-7260399: R3-Paket und Kandidatenpaket gegen Solution und
# Kaggle, danach zur Information der Kandidat direkt gegen R3 auf 7260000-7260099. Für das Duell spielt der Kandidat
# als gleichwertige Spec (pro Prozess kann nur ein Paket mit dem Modul `sherlock` geladen werden; die Gleichheit von
# Paket und Spec wird vorher geprüft).
#   run_bestaetigung.sh FROZEN_DIR KANDIDAT_ZIP DUELL_ARGS...
#   z. B. run_bestaetigung.sh $F experiments/candidates/deve_20261117/agent_p9.zip \
#         --weights $F/experiments/imitation/students/ens_v9_v8L.pth --set imit_stay_bias=1.5 --set imit_unstack=true
set -u
FROZEN=$1; CAND=$2; shift 2
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/deve_20261117
R3ZIP=$FROZEN/experiments/releases/20261116_r3_finale/agent.zip
log() { echo "$(date '+%H:%M:%S') $*"; }
log "START Quelle $(cat SOURCE_HEAD.txt), Kandidat $CAND, Duell $*"
shasum -a 256 $R3ZIP $CAND
run() { name=$1; seeds=$2; shift 2; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval "$@" --seed-list $seeds --workers 10 --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run bestaetigung_r3 $D/seeds_bestaetigung.json --weights "r3zip:$R3ZIP" --opponents solution92,kaggle3
run bestaetigung_kandidat $D/seeds_bestaetigung.json --weights "r3zip:$CAND" --opponents solution92,kaggle3
run bestaetigung_direkt $D/seeds_bestaetigung_direkt.json "$@" --opponents "r3zip:$R3ZIP"
log "BESTAETIGUNG_DONE"
