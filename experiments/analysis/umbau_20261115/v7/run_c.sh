#!/bin/bash
# Schritt 3 (17.11.2026 nachts): DAgger-Runde 4 mit dem besten Schueler aus v6/v5c, dann v7 (Warmstart) und v7L
# (groesseres Netz von Grund auf), Tests auf Dev A. Eingefrorene Quelle 8324845 (frozen_v6). Streng nacheinander.
#   run_c.sh BEST_STUDENT PREV(0|1) STAY_BIAS
SP=/private/tmp/claude-501/-Users-elhassanmahmoud-Documents-AKI-LuxAgent15/d5bcfcfa-cd35-4364-b2b5-1a6260ee2252/scratchpad
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
BEST=$1; PREV=$2; SB=$3
cd $SP/frozen_v6 || exit 1
PY=$MAIN/.venv/bin/python
IM=$MAIN/experiments/imitation; S=$IM/students; R=$IM/releases
D=$MAIN/experiments/analysis/umbau_20261115/v7; mkdir -p $D
DEVA=$MAIN/experiments/analysis/kaggle3_20261115/seeds_devA.json
R3=r3zip:$MAIN/experiments/releases/20261116_r3_finale/agent.zip
SW=(--set imit_stay_bias=$SB --set imit_unstack=true)
PM=(); [ "$PREV" = "1" ] && PM=(--prev-move)
DATA=($IM/k3_b1 $IM/k3_b2 $IM/k3_b3 $IM/k3_dagger1 $IM/k3_dagger2 $IM/k3_dagger3 $IM/k3_dagger4)
log() { echo "$(date '+%H:%M:%S') $*"; }

log "START Quelle $(head -1 SOURCE_HEAD.txt), bester Schueler $BEST, letzte Bewegung $PREV, Stay-Bias $SB"
[ -f $IM/k3_dagger4/collect.json ] || $PY -m scripts.imitate dagger --student $BEST --out $IM/k3_dagger4 \
    --games 600 --workers 10 --seed0 7253000 --mix kaggle3:0.6,v14:0.2,solution92:0.2 "${SW[@]}" 2>&1 \
    | grep -E "DAgger:|Error|Traceback"
log "DAGGER4_DONE"
[ -f $S/v7_from_best.pth ] || { $PY -m scripts.imitate train --data "${DATA[@]}" --out $S/v7_from_best.pth --epochs 2 \
    --lr 0.001 --seed 7 --low-memory --init $BEST "${PM[@]}" > $S/v7_from_best.log 2>&1
  grep -E "Warmstart|Epoche|gespeichert|Error|Traceback" $S/v7_from_best.log; log "v7 trainiert"; }
[ -f $S/v7L_scratch.pth ] || { $PY -m scripts.imitate train --data "${DATA[@]}" --out $S/v7L_scratch.pth --epochs 2 \
    --lr 0.002 --seed 8 --low-memory --ch 96 --blocks 8 --hidden 384 "${PM[@]}" > $S/v7L_scratch.log 2>&1
  grep -E "Epoche|gespeichert|Error|Traceback" $S/v7L_scratch.log; log "v7L trainiert"; }
pack() { [ -f $R/$1/weights/agent.pth ] || $PY -m scripts.imitate pack-hybrid --student $2 --mode mixed \
    --combat-radius 5 "${SW[@]}" --out $R/$1/weights/agent.pth 2>&1 | grep -v Warn; }
pack v7_mixed $S/v7_from_best.pth
pack v7L_mixed $S/v7L_scratch.pth
run() { name=$1; shift; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval "$@" --seed-list $DEVA --workers 10 --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run student_v7_devA --weights $S/v7_from_best.pth --opponents solution92,kaggle3,$R3 "${SW[@]}"
run hyb_v7_mixed_devA --weights $R/v7_mixed/weights/agent.pth --opponents solution92,kaggle3,$R3
run student_v7L_devA --weights $S/v7L_scratch.pth --opponents solution92,kaggle3,$R3 "${SW[@]}"
run hyb_v7L_mixed_devA --weights $R/v7L_mixed/weights/agent.pth --opponents solution92,kaggle3,$R3
shasum -a 256 $S/v7_from_best.pth $S/v7L_scratch.pth $R/v7_mixed/weights/agent.pth $R/v7L_mixed/weights/agent.pth
log "C_DONE"
