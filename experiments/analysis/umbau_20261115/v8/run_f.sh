#!/bin/bash
# Schritt 6 (17.11.2026 frueh): DAgger-Runde 5 mit dem Ensemble v7 + v7L als Spieler, dann v8 (Fortsetzung von v7,
# 2 Epochen) und v8L (Fortsetzung von v7L, 1 Epoche), Ensemble v8 + v8L, Dev-A-Tests (rein und Hybrid).
# Eingefrorene Quelle 8324845 (frozen_v6). Streng nacheinander. Muss vor 08:30 fertig sein.
SP=/private/tmp/claude-501/-Users-elhassanmahmoud-Documents-AKI-LuxAgent15/d5bcfcfa-cd35-4364-b2b5-1a6260ee2252/scratchpad
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $SP/frozen_v6 || exit 1
PY=$MAIN/.venv/bin/python
IM=$MAIN/experiments/imitation; S=$IM/students; R=$IM/releases
D=$MAIN/experiments/analysis/umbau_20261115/v8; mkdir -p $D
DEVA=$MAIN/experiments/analysis/kaggle3_20261115/seeds_devA.json
R3=r3zip:$MAIN/experiments/releases/20261116_r3_finale/agent.zip
SW=(--set imit_stay_bias=1.5 --set imit_unstack=true)
DATA=($IM/k3_b1 $IM/k3_b2 $IM/k3_b3 $IM/k3_dagger1 $IM/k3_dagger2 $IM/k3_dagger3 $IM/k3_dagger4 $IM/k3_dagger5)
log() { echo "$(date '+%H:%M:%S') $*"; }

log "START Quelle $(head -1 SOURCE_HEAD.txt)"
[ -f $IM/k3_dagger5/collect.json ] || $PY -m scripts.imitate dagger --student $S/ens_v7_v7L.pth --out $IM/k3_dagger5 \
    --games 600 --workers 10 --seed0 7255000 --mix kaggle3:0.6,v14:0.2,solution92:0.2 "${SW[@]}" 2>&1 \
    | grep -E "DAgger:|Error|Traceback"
log "DAGGER5_DONE"
train() { out=$1; init=$2; ep=$3; seed=$4; [ -f $out ] && return
  $PY -m scripts.imitate train --data "${DATA[@]}" --out $out --epochs $ep --lr 0.001 --seed $seed --low-memory \
      --init $init --prev-move > ${out%.pth}.log 2>&1
  grep -E "Warmstart|Epoche|gespeichert|Error|Traceback" ${out%.pth}.log; log "$(basename $out) trainiert"; }
train $S/v8_from_v7.pth $S/v7_from_best.pth 2 9
train $S/v8L_from_v7L.pth $S/v7L_scratch.pth 1 10
[ -f $S/ens_v8_v8L.pth ] || $PY -m scripts.imitate ensemble --students $S/v8_from_v7.pth $S/v8L_from_v7L.pth \
    --out $S/ens_v8_v8L.pth
[ -f $R/ens_v8_v8L_mixed/weights/agent.pth ] || $PY -m scripts.imitate pack-hybrid --student $S/ens_v8_v8L.pth \
    --mode mixed --combat-radius 5 "${SW[@]}" --out $R/ens_v8_v8L_mixed/weights/agent.pth 2>&1 | grep -v Warn
run() { name=$1; shift; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval "$@" --seed-list $DEVA --workers 10 --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run student_ens_v8_v8L_devA --weights $S/ens_v8_v8L.pth --opponents solution92,kaggle3,$R3 "${SW[@]}"
run hyb_ens_v8_v8L_mixed_devA --weights $R/ens_v8_v8L_mixed/weights/agent.pth --opponents solution92,kaggle3,$R3
shasum -a 256 $S/v8_from_v7.pth $S/v8L_from_v7L.pth $S/ens_v8_v8L.pth $R/ens_v8_v8L_mixed/weights/agent.pth
log "F_DONE"
