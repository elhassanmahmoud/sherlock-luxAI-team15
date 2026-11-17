#!/bin/bash
# Test der Taktikschicht über R3 auf Dev D (7256100-7256199, beide Seiten), Plan in PLAN.md.
# Läuft aus einer eingefrorenen Kopie des Repos (git archive des Plan-Commits), streng nacheinander, 10 Prozesse.
#   run_screen.sh FROZEN_DIR
set -u
FROZEN=$1
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
D=$MAIN/experiments/analysis/r3t_20261117
SEEDS=$D/seeds_devD.json
R3=r3zip:$FROZEN/experiments/releases/20261116_r3_finale/agent.zip
log() { echo "$(date '+%H:%M:%S') $*"; }
log "START Quelle $(cat SOURCE_HEAD.txt)"
run() { name=$1; w=$2; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval --weights "$w" --opponents solution92,kaggle3 --seed-list $SEEDS --workers 10 \
      --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run r3_devD $R3
run granate_devD "r3t:granate"
run sog_devD "r3t:sog"
run tanken_devD "r3t:tanken"
run alle_devD "r3t:granate,sog,tanken"
# Erklärung: Energie- und Todesanalyse je Variante auf den Analysekarten (nicht zur Auswahl)
for v in granate sog tanken "granate,sog,tanken"; do
  name=diag_$(echo $v | tr ',' '_')
  [ -f $D/$name/matches.csv ] || $PY experiments/analysis/r3_kaggle_20261117/diagnose.py --agent "r3t:$v" \
      --seeds 7256000:7256030 --workers 10 --out $D/$name 2>&1 | grep -E "Spiele|Error|Traceback"
done
shasum -a 256 $FROZEN/experiments/releases/20261116_r3_finale/agent.zip
log "SCREEN_DONE"
