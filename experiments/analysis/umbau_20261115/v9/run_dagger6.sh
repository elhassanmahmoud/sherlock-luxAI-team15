#!/bin/bash
# DAgger-Runde 6 (17.11.2026): R3 mit Schüler-Mix (r3t:schueler=ens8) spielt, der Kaggle-Lehrer beschriftet die Lagen
# des eingebauten Schülers. Danach v9 (Fortsetzung von v8, 2 Epochen), Ensemble v9 + v8L, Nachahmung auf den frischen
# Prüfspielen. Startet erst nach der zweiten Prüfung (nie parallel). Eingefrorene Quelle = Commit dieses Skripts.
#   run_dagger6.sh FROZEN_DIR CHECK2_LOG
set -u
FROZEN=$1; PREV_LOG=$2
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
IM=$MAIN/experiments/imitation; S=$IM/students
D=$MAIN/experiments/analysis/umbau_20261115/v9; mkdir -p $D/nachahmung
DATA=($IM/k3_b1 $IM/k3_b2 $IM/k3_b3 $IM/k3_dagger1 $IM/k3_dagger2 $IM/k3_dagger3 $IM/k3_dagger4 $IM/k3_dagger5 $IM/k3_dagger6_r3t)
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 720); do grep -q CHECK2_DONE $PREV_LOG 2>/dev/null && break; sleep 20; done
grep -q CHECK2_DONE $PREV_LOG || { log "zweite Prüfung nicht fertig, Abbruch"; exit 1; }
log "START Quelle $(cat SOURCE_HEAD.txt)"
[ -f $IM/k3_dagger6_r3t/collect.json ] || $PY -m scripts.imitate dagger --student "r3t:schueler=ens8" \
    --out $IM/k3_dagger6_r3t --games 600 --workers 10 --seed0 7257000 --mix kaggle3:0.6,v14:0.2,solution92:0.2 2>&1 \
    | grep -E "DAgger:|Error|Traceback"
log "DAGGER6_DONE"
[ -f $S/v9_from_v8.pth ] || { $PY -m scripts.imitate train --data "${DATA[@]}" --out $S/v9_from_v8.pth --epochs 2 \
    --lr 0.001 --seed 11 --low-memory --init $S/v8_from_v7.pth --prev-move > $S/v9_from_v8.log 2>&1;
    grep -E "Warmstart|Epoche|gespeichert|Error|Traceback" $S/v9_from_v8.log; }
log "v9 trainiert"
[ -f $S/ens_v9_v8L.pth ] || $PY -m scripts.imitate ensemble --students $S/v9_from_v8.pth $S/v8L_from_v7L.pth --out $S/ens_v9_v8L.pth
OE=experiments/analysis/umbau_20261115/tools/offline_eval.py
STUD=(V8=$S/v8_from_v7.pth ENS8=$S/ens_v8_v8L.pth V9=$S/v9_from_v8.pth ENS9=$S/ens_v9_v8L.pth)
for set in teacher dagger_v5; do
  [ -f $D/nachahmung/$set.json ] || $PY $OE --data $IM/k3_holdout_$set --students "${STUD[@]}" \
      --out $D/nachahmung/$set.json > $D/nachahmung/$set.md 2>&1
  grep -v Warn $D/nachahmung/$set.md; log "Nachahmung $set fertig"
done
cp $S/v9_from_v8.log $D/training_v9.log
shasum -a 256 $S/v9_from_v8.pth $S/ens_v9_v8L.pth
log "DAGGER6_ALL_DONE"
