#!/bin/bash
# DAgger-Runde 7 (17.11.2026): der beste reine Schüler (Ensemble v9 + v8L mit den Schaltern aus Dev F) spielt, der
# Kaggle-Lehrer beschriftet jede Lage. Danach v10 (Fortsetzung von v9, 2 Epochen), Ensemble v10 + v8L, Nachahmung auf
# den frischen Prüfspielen. Startet erst, wenn der vorherige Lauf sein Endsignal geschrieben hat (nie parallel).
#   run_dagger7.sh FROZEN_DIR PREV_LOG ENDSIGNAL SCHALTER...
#   (z. B. ... run_bestaetigung3.log BESTAETIGUNG3_DONE imit_stay_bias=1.0 imit_unstack=true imit_hold_points=true)
set -u
FROZEN=$1; PREV_LOG=$2; MARK=$3; shift 3
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $FROZEN || exit 1
PY=$MAIN/.venv/bin/python
IM=$MAIN/experiments/imitation; S=$IM/students
D=$MAIN/experiments/analysis/umbau_20261115/v10; mkdir -p $D/nachahmung
SW=(); for kv in "$@"; do SW+=(--set "$kv"); done
DATA=($IM/k3_b1 $IM/k3_b2 $IM/k3_b3 $IM/k3_dagger1 $IM/k3_dagger2 $IM/k3_dagger3 $IM/k3_dagger4 $IM/k3_dagger5
      $IM/k3_dagger6_r3t $IM/k3_dagger7)
log() { echo "$(date '+%H:%M:%S') $*"; }
for i in $(seq 1 720); do grep -q $MARK $PREV_LOG 2>/dev/null && break; sleep 20; done
grep -q $MARK $PREV_LOG || { log "$MARK fehlt, Abbruch"; exit 1; }
log "START Quelle $(cat SOURCE_HEAD.txt), Schalter $*"
[ -f $IM/k3_dagger7/collect.json ] || $PY -m scripts.imitate dagger --student $S/ens_v9_v8L.pth "${SW[@]}" \
    --out $IM/k3_dagger7 --games 600 --workers 10 --seed0 7262000 --mix kaggle3:0.6,v14:0.2,solution92:0.2 2>&1 \
    | grep -E "DAgger:|Error|Traceback"
log "DAGGER7_DONE"
[ -f $S/v10_from_v9.pth ] || { $PY -m scripts.imitate train --data "${DATA[@]}" --out $S/v10_from_v9.pth --epochs 2 \
    --lr 0.001 --seed 12 --low-memory --init $S/v9_from_v8.pth --prev-move > $S/v10_from_v9.log 2>&1;
    grep -E "Warmstart|Epoche|gespeichert|Error|Traceback" $S/v10_from_v9.log; }
log "v10 trainiert"
[ -f $S/ens_v10_v8L.pth ] || $PY -m scripts.imitate ensemble --students $S/v10_from_v9.pth $S/v8L_from_v7L.pth \
    --out $S/ens_v10_v8L.pth
OE=experiments/analysis/umbau_20261115/tools/offline_eval.py
STUD=(ENS9=$S/ens_v9_v8L.pth V10=$S/v10_from_v9.pth ENS10=$S/ens_v10_v8L.pth)
for set in teacher dagger_v5; do
  [ -f $D/nachahmung/$set.json ] || $PY $OE --data $IM/k3_holdout_$set --students "${STUD[@]}" \
      --out $D/nachahmung/$set.json > $D/nachahmung/$set.md 2>&1
  grep -v Warn $D/nachahmung/$set.md; log "Nachahmung $set fertig"
done
cp $S/v10_from_v9.log $D/training_v10.log
shasum -a 256 $S/v10_from_v9.pth $S/ens_v10_v8L.pth
log "DAGGER7_ALL_DONE"
