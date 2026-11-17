#!/bin/bash
# Frische Bestätigung (BESTAETIGUNG_PLAN.md) auf 7159000-7159399: R3 und das Kurspaket des Kandidaten gegen Solution
# und Kaggle, dazu zur Information direkt gegen R3 auf 7159000-7159099 (Kandidat als gleichwertige r3t-Spec, weil pro
# Prozess nur ein R3-Paket geladen werden kann; das Paket spielt nachweislich gleich).
#   run_bestaetigung.sh FROZEN_DIR KANDIDAT_ZIP KANDIDAT_SPEC
set -u
FROZEN=$1; CAND=$2; SPEC=$3
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/r3t_20261117
R3ZIP=$FROZEN/experiments/releases/20261116_r3_finale/agent.zip
log() { echo "$(date '+%H:%M:%S') $*"; }
log "START Quelle $(cat SOURCE_HEAD.txt), Kandidat $CAND ($SPEC)"
shasum -a 256 $R3ZIP $CAND
run() { name=$1; w=$2; opps=$3; seeds=$4; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval --weights "$w" --opponents "$opps" --seed-list $seeds --workers 10 \
      --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run bestaetigung_r3 "r3zip:$R3ZIP" solution92,kaggle3 $D/seeds_bestaetigung.json
run bestaetigung_kandidat "r3zip:$CAND" solution92,kaggle3 $D/seeds_bestaetigung.json
run bestaetigung_direkt "r3t:$SPEC" "r3zip:$R3ZIP" $D/seeds_bestaetigung_direkt.json
log "BESTAETIGUNG_DONE"
