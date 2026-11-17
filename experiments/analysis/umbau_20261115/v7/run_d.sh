#!/bin/bash
# Schritt 4 (17.11.2026 nachts): frische Prüfspiele für die Nachahmung (nie trainiert), Messung aller Schüler,
# Ensemble der besten Schüler und Dev-A-Test. Eingefrorene Quelle 8324845 (frozen_v6). Streng nacheinander.
#   run_d.sh ENS_NAME MEMBER1 MEMBER2 [MEMBER3 ...]   (alle Mitglieder mit gleicher Eingabe)
SP=/private/tmp/claude-501/-Users-elhassanmahmoud-Documents-AKI-LuxAgent15/d5bcfcfa-cd35-4364-b2b5-1a6260ee2252/scratchpad
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
ENS=$1; shift; MEMBERS=("$@")
cd $SP/frozen_v6 || exit 1
PY=$MAIN/.venv/bin/python
IM=$MAIN/experiments/imitation; S=$IM/students; R=$IM/releases
D=$MAIN/experiments/analysis/umbau_20261115/v7; mkdir -p $D/nachahmung
DEVA=$MAIN/experiments/analysis/kaggle3_20261115/seeds_devA.json
R3=r3zip:$MAIN/experiments/releases/20261116_r3_finale/agent.zip
SW=(--set imit_stay_bias=1.5 --set imit_unstack=true)
OE=experiments/analysis/umbau_20261115/tools/offline_eval.py
mkdir -p $(dirname $OE) && cp $MAIN/$OE $OE
log() { echo "$(date '+%H:%M:%S') $*"; }

log "START Quelle $(head -1 SOURCE_HEAD.txt), Ensemble $ENS aus ${MEMBERS[*]}"
# 1) Frische Prüfspiele: Lehrer spielt selbst (7254000-7254059) und Schüler v5 spielt, Lehrer beschriftet (7254100-7254159)
[ -f $IM/k3_holdout_teacher/collect.json ] || $PY -m scripts.imitate collect --out $IM/k3_holdout_teacher --games 60 \
    --workers 10 --seed0 7254000 2>&1 | grep -E "Sammeln|Spiele|Error|Traceback"
[ -f $IM/k3_holdout_dagger_v5/collect.json ] || $PY -m scripts.imitate dagger --student $S/v5_b123d123.pth \
    --out $IM/k3_holdout_dagger_v5 --games 60 --workers 10 --seed0 7254100 --mix kaggle3:0.6,v14:0.2,solution92:0.2 \
    "${SW[@]}" 2>&1 | grep -E "DAgger:|Error|Traceback"
log "PRUEFSPIELE_DONE"
# 2) Ensemble bauen und packen
[ -f $S/$ENS.pth ] || $PY -m scripts.imitate ensemble --students "${MEMBERS[@]}" --out $S/$ENS.pth
[ -f $R/${ENS}_mixed/weights/agent.pth ] || $PY -m scripts.imitate pack-hybrid --student $S/$ENS.pth --mode mixed \
    --combat-radius 5 "${SW[@]}" --out $R/${ENS}_mixed/weights/agent.pth 2>&1 | grep -v Warn
# 3) Nachahmung messen (alle Schüler auf beiden Prüfsätzen)
STUD=(V5=$S/v5_b123d123.pth V5C=$S/v5c_from_v5.pth V6=$S/v6_pm_from_v5.pth V7=$S/v7_from_best.pth V7L=$S/v7L_scratch.pth ENS=$S/$ENS.pth)
for set in teacher dagger_v5; do
  [ -f $D/nachahmung/$set.json ] || $PY $OE --data $IM/k3_holdout_$set --students "${STUD[@]}" \
      --out $D/nachahmung/$set.json > $D/nachahmung/$set.md 2>&1
  cat $D/nachahmung/$set.md | grep -v Warn; log "Nachahmung $set fertig"
done
# 4) Ensemble auf Dev A
run() { name=$1; shift; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval "$@" --seed-list $DEVA --workers 10 --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run student_${ENS}_devA --weights $S/$ENS.pth --opponents solution92,kaggle3,$R3 "${SW[@]}"
run hyb_${ENS}_mixed_devA --weights $R/${ENS}_mixed/weights/agent.pth --opponents solution92,kaggle3,$R3
shasum -a 256 $S/$ENS.pth $R/${ENS}_mixed/weights/agent.pth
log "D_DONE"
