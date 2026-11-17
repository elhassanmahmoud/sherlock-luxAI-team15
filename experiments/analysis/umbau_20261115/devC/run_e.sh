#!/bin/bash
# Schritt 5 (17.11.2026 nachts): Gegenprobe auf Dev C (7164000-7164099, bisher unbenutzt, Mahmouds Reservierung).
# Dev C ist ein zweiter Entwicklungssatz, KEINE Bestätigung. Vorab festgelegte Leseregel (vor dem ersten Spiel):
#   Ein Kandidat kommt nur dann für eine spätere, vorab festgelegte Bestätigung auf 7159000-7159399 in Frage
#   (die zusätzlich ein Ja von Mahmoud und Moayed braucht), wenn er auf Dev C gegen Solution+Kaggle zusammen
#   mindestens +2 Prozentpunkte über R3 liegt (gepaart nach Karte) und gegen Solution nicht unter R3.
# Eingefrorene Quelle 8324845 (frozen_v6). Startet erst, wenn run_d.sh fertig ist (nie parallel).
SP=/private/tmp/claude-501/-Users-elhassanmahmoud-Documents-AKI-LuxAgent15/d5bcfcfa-cd35-4364-b2b5-1a6260ee2252/scratchpad
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $SP/frozen_v6 || exit 1
PY=$MAIN/.venv/bin/python
IM=$MAIN/experiments/imitation; R=$IM/releases
D=$MAIN/experiments/analysis/umbau_20261115/devC; mkdir -p $D
DEVC=$MAIN/experiments/analysis/kaggle3_20261115/seeds_devC.json
R3=r3zip:$MAIN/experiments/releases/20261116_r3_finale/agent.zip
log() { echo "$(date '+%H:%M:%S') $*"; }

for i in $(seq 1 240); do grep -q D_DONE $SP/run_d.log 2>/dev/null && break; sleep 30; done
grep -q D_DONE $SP/run_d.log || { log "run_d nicht fertig, Abbruch"; exit 1; }
log "START Quelle $(head -1 SOURCE_HEAD.txt)"
run() { name=$1; w=$2; shift 2; [ -f $D/$name.csv ] && return
  [ -f "${w#r3zip:}" ] || { log "$name: $w fehlt, uebersprungen"; return; }
  $PY -m scripts.par_eval --weights $w "$@" --seed-list $DEVC --workers 10 --out $D/$name.csv 2>&1 \
      | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run r3_devC $R3 --opponents solution92,kaggle3
run v15_devC $R/v15_candidate/weights/agent.pth --opponents solution92,kaggle3,$R3
run hyb_v7L_mixed_devC $R/v7L_mixed/weights/agent.pth --opponents solution92,kaggle3,$R3
run hyb_ens_v7_v7L_mixed_devC $R/ens_v7_v7L_mixed/weights/agent.pth --opponents solution92,kaggle3,$R3
shasum -a 256 $R/v15_candidate/weights/agent.pth $R/v7L_mixed/weights/agent.pth $R/ens_v7_v7L_mixed/weights/agent.pth \
    $MAIN/experiments/releases/20261116_r3_finale/agent.zip
log "E_DONE"
