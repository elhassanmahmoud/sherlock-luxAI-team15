#!/bin/bash
# Neue Eingabe "letzte eigene Bewegung" (v6) gegen gleich lange Kontrolle (v5c), beide Warmstart von v5 (16./17.11.2026).
# Eingefrorene Quelle 8324845. Startet erst, wenn run_v5.sh fertig ist (nie parallel zu Training oder Tests).
SP=/private/tmp/claude-501/-Users-elhassanmahmoud-Documents-AKI-LuxAgent15/d5bcfcfa-cd35-4364-b2b5-1a6260ee2252/scratchpad
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $SP/frozen_v6 || exit 1
PY=$MAIN/.venv/bin/python
IM=$MAIN/experiments/imitation; S=$IM/students; R=$IM/releases
D=$MAIN/experiments/analysis/umbau_20261115/v6; mkdir -p $D
DEVA=$MAIN/experiments/analysis/kaggle3_20261115/seeds_devA.json
R3=r3zip:$MAIN/experiments/releases/20261116_r3_finale/agent.zip
V14=self:$MAIN/agents/sherlock/weights/agent_p0.pth
SW=(--set imit_stay_bias=1.5 --set imit_unstack=true)
DATA=($IM/k3_b1 $IM/k3_b2 $IM/k3_b3 $IM/k3_dagger1 $IM/k3_dagger2 $IM/k3_dagger3)
log() { echo "$(date '+%H:%M:%S') $*"; }

until grep -q V5_DONE $SP/run_v5.log 2>/dev/null; do sleep 30; done
log "START Quelle $(head -1 SOURCE_HEAD.txt)"
[ -f $S/v5_b123d123.pth ] || { log "v5 fehlt"; exit 1; }
train() { out=$1; shift; [ -f $out ] && return
  $PY -m scripts.imitate train --data "${DATA[@]}" --out $out --epochs 2 --lr 0.001 --seed 6 --low-memory \
      --init $S/v5_b123d123.pth "$@" > ${out%.pth}.log 2>&1
  grep -E "Warmstart|Epoche|gespeichert|Error|Traceback" ${out%.pth}.log; log "$(basename $out) trainiert"; }
train $S/v6_pm_from_v5.pth --prev-move
train $S/v5c_from_v5.pth
pack() { [ -f $R/$1/weights/agent.pth ] || $PY -m scripts.imitate pack-hybrid --student $2 --mode mixed \
    --combat-radius 5 "${SW[@]}" --out $R/$1/weights/agent.pth 2>&1 | grep -v Warn; }
pack v6_mixed $S/v6_pm_from_v5.pth
pack v5c_mixed $S/v5c_from_v5.pth
run() { name=$1; shift; [ -f $D/$name.csv ] && return
  $PY -m scripts.par_eval "$@" --seed-list $DEVA --workers 10 --out $D/$name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$name fertig"; }
run hyb_v6_mixed_devA --weights $R/v6_mixed/weights/agent.pth --opponents solution92,kaggle3,$R3,$V14
run hyb_v5c_mixed_devA --weights $R/v5c_mixed/weights/agent.pth --opponents solution92,kaggle3,$R3,$V14
run student_v6_devA --weights $S/v6_pm_from_v5.pth --opponents solution92,kaggle3,$R3 "${SW[@]}"
run student_v6_sb0_devA --weights $S/v6_pm_from_v5.pth --opponents solution92,kaggle3 --set imit_unstack=true
run student_v5c_devA --weights $S/v5c_from_v5.pth --opponents solution92,kaggle3,$R3 "${SW[@]}"
shasum -a 256 $S/v6_pm_from_v5.pth $S/v5c_from_v5.pth $R/v6_mixed/weights/agent.pth $R/v5c_mixed/weights/agent.pth
log "V6_DONE"
