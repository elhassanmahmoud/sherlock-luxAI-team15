#!/bin/bash
# Frische Bestätigung des Dev-G-Siegers (PLAN.md, Abschnitt "Danach") auf 7265000-7265399: R3-Paket, Kandidatenpaket und
# zur Information das zuletzt bestätigte Paket (PS) gegen Solution und Kaggle; danach der Kandidat direkt gegen R3 auf 7265000-7265099.
#   run_bestaetigung4.sh FROZEN_DIR KANDIDAT_ZIP PREV_LOG DUELL_ARGS...
set -u
FROZEN=$1; CAND=$2; PREV_LOG=$3; shift 3
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/devg_20261117
R3ZIP=$FROZEN/experiments/releases/20261116_r3_finale/agent.zip
P9ZIP=$MAIN/experiments/candidates/devf_20261117/agent_p9_s10_halter.zip
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 360); do grep -q DEVG_DONE $PREV_LOG 2>/dev/null && break; sleep 10; done
grep -q DEVG_DONE $PREV_LOG || { log "Dev G nicht fertig, Abbruch"; exit 1; }
log "START Quelle $(cat SOURCE_HEAD.txt), Kandidat $CAND, Duell $*"
shasum -a 256 $R3ZIP $CAND $P9ZIP
run() { name=$1; seeds=$2; shift 2; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval "$@" --seed-list $seeds --workers 10 --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run bestaetigung4_r3 $D/seeds_bestaetigung4.json --weights "r3zip:$R3ZIP" --opponents solution92,kaggle3
run bestaetigung4_kandidat $D/seeds_bestaetigung4.json --weights "r3zip:$CAND" --opponents solution92,kaggle3
run bestaetigung4_p9 $D/seeds_bestaetigung4.json --weights "r3zip:$P9ZIP" --opponents solution92,kaggle3
run bestaetigung4_direkt $D/seeds_bestaetigung4_direkt.json "$@" --opponents "r3zip:$R3ZIP"
log "BESTAETIGUNG4_DONE"
