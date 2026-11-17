#!/bin/bash
# Schritt 7 (17.11.2026 frueh): Nachahmung von v8, v8L und Ensemble v8 + v8L auf den frischen Pruefspielen
# (Lehrerspiele 7254000-7254059, Schuelerspiele v5 7254100-7254159; nie trainiert). V7 als Kontrolle: muss die
# Werte aus v7/nachahmung exakt wiederholen. Eingefrorene Quelle 8324845. Startet erst nach run_e3.sh (nie parallel).
SP=/private/tmp/claude-501/-Users-elhassanmahmoud-Documents-AKI-LuxAgent15/d5bcfcfa-cd35-4364-b2b5-1a6260ee2252/scratchpad
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $SP/frozen_v6 || exit 1
PY=$MAIN/.venv/bin/python
IM=$MAIN/experiments/imitation; S=$IM/students
D=$MAIN/experiments/analysis/umbau_20261115/v8; mkdir -p $D/nachahmung
OE=experiments/analysis/umbau_20261115/tools/offline_eval.py
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 120); do grep -q E3_DONE $SP/run_e3.log 2>/dev/null && break; sleep 15; done
grep -q E3_DONE $SP/run_e3.log || { log "run_e3 nicht fertig, Abbruch"; exit 1; }
log "START Quelle $(head -1 SOURCE_HEAD.txt)"
STUD=(V7=$S/v7_from_best.pth V8=$S/v8_from_v7.pth V8L=$S/v8L_from_v7L.pth ENS8=$S/ens_v8_v8L.pth)
for set in teacher dagger_v5; do
  [ -f $D/nachahmung/$set.json ] || $PY $OE --data $IM/k3_holdout_$set --students "${STUD[@]}" \
      --out $D/nachahmung/$set.json > $D/nachahmung/$set.md 2>&1
  grep -v Warn $D/nachahmung/$set.md; log "Nachahmung $set fertig"
done
log "G_DONE"
