#!/bin/bash
# Frische Bestätigung 5 (PLAN.md, Abschnitt "Danach") auf 7267000-7267399: Kandidatenpaket, K-Paket und R3-Paket gegen
# Solution und Kaggle; danach der Kandidat (Repo-Code mit seinen Schaltern) direkt gegen das K-Paket auf 7267000-7267099.
#   run_bestaetigung5.sh FROZEN_DIR KANDIDAT_ZIP PREV_LOG PREV_MARKER KEY=VALUE...
set -u
FROZEN=$1; CAND=$2; PREV_LOG=$3; MARKER=$4; shift 4
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/devh_20261117
R3ZIP=$FROZEN/experiments/releases/20261116_r3_finale/agent.zip
KZIP=$FROZEN/experiments/candidates/devf_20261117/agent_p9_s10_halter.zip
W=$FROZEN/experiments/imitation/students/ens_v9_v8L.pth
SW=(--set imit_stay_bias=1.0 --set imit_unstack=true --set imit_hold_points=true); for kv in "$@"; do SW+=(--set "$kv"); done
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 1080); do grep -q $MARKER $PREV_LOG 2>/dev/null && break; sleep 10; done
grep -q $MARKER $PREV_LOG || { log "$MARKER fehlt, Abbruch"; exit 1; }
log "START Quelle $(cat SOURCE_HEAD.txt), Kandidat $CAND, Schalter $*"
shasum -a 256 $R3ZIP $KZIP $CAND $W
run() { name=$1; seeds=$2; shift 2; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval "$@" --seed-list $seeds --workers 10 --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run bestaetigung5_kandidat $D/seeds_bestaetigung5.json --weights "r3zip:$CAND" --opponents solution92,kaggle3
run bestaetigung5_k $D/seeds_bestaetigung5.json --weights "r3zip:$KZIP" --opponents solution92,kaggle3
run bestaetigung5_r3 $D/seeds_bestaetigung5.json --weights "r3zip:$R3ZIP" --opponents solution92,kaggle3
run bestaetigung5_direkt $D/seeds_bestaetigung5_direkt.json --weights $W "${SW[@]}" --opponents "r3zip:$KZIP"
log "BESTAETIGUNG5_DONE"
