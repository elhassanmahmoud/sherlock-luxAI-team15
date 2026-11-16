#!/bin/bash
# DAgger-Runde 3 -> Schueler v5 -> Tests auf Dev A (16.11.2026), streng nacheinander.
# Eingefrorene Quelle 1c148c3 (Kopie im Scratchpad); Daten und Ergebnisse im Projektordner.
# Neu gegenueber 15.11.: Referenz ist die Abgabe R3 (Moayed, 16.11.), direkt und auf Dev A.
SP=/private/tmp/claude-501/-Users-elhassanmahmoud-Documents-AKI-LuxAgent15/d5bcfcfa-cd35-4364-b2b5-1a6260ee2252/scratchpad
MAIN=/Users/elhassanmahmoud/Documents/AKI_LuxAgent15
cd $SP/frozen_v5 || exit 1
PY=$MAIN/.venv/bin/python
IM=$MAIN/experiments/imitation; S=$IM/students; R=$IM/releases
D=$MAIN/experiments/analysis/umbau_20261115/v5; mkdir -p $D
DEVA=$MAIN/experiments/analysis/kaggle3_20261115/seeds_devA.json
R3=r3zip:$MAIN/experiments/releases/20261116_r3_finale/agent.zip
V14=self:$MAIN/agents/sherlock/weights/agent_p0.pth
V15=$R/v15_candidate/weights/agent.pth
SW=(--set imit_stay_bias=1.5 --set imit_unstack=true)
log() { echo "$(date '+%H:%M:%S') $*"; }

log "START Quelle $(cat SOURCE_HEAD.txt)"
[ -f $IM/k3_dagger3/collect.json ] || $PY -m scripts.imitate dagger --student $S/v4_b123d12.pth --out $IM/k3_dagger3 \
    --games 600 --workers 10 --seed0 7252000 --mix kaggle3:0.6,v14:0.2,solution92:0.2 "${SW[@]}" 2>&1 \
    | grep -E "DAgger:|Error|Traceback"
log "DAGGER3_DONE"
[ -f $S/v5_b123d123.pth ] || $PY -m scripts.imitate train --data $IM/k3_b1 $IM/k3_b2 $IM/k3_b3 $IM/k3_dagger1 \
    $IM/k3_dagger2 $IM/k3_dagger3 --out $S/v5_b123d123.pth --epochs 2 --ch 64 --blocks 6 --hidden 256 --seed 5 \
    --low-memory > $S/v5_b123d123.log 2>&1
grep -E "Epoche|gespeichert|Error|Traceback" $S/v5_b123d123.log
log "V5_TRAINED"
[ -f $R/v5_mixed/weights/agent.pth ] || $PY -m scripts.imitate pack-hybrid --student $S/v5_b123d123.pth --mode mixed \
    --combat-radius 5 "${SW[@]}" --out $R/v5_mixed/weights/agent.pth 2>&1 | grep -v Warn
run() { [ -f $D/$1.csv ] && return; shift_name=$1; shift
  $PY -m scripts.par_eval "$@" --seed-list $DEVA --workers 10 --out $D/$shift_name.csv 2>&1 | grep -E "csv:|Error|Traceback"
  log "$shift_name fertig"; }
run hyb_v5_mixed_devA --weights $R/v5_mixed/weights/agent.pth --opponents solution92,kaggle3,$R3,$V14
run r3_devA --weights $R3 --opponents solution92,kaggle3
run v15_vs_r3_devA --weights $V15 --opponents $R3
run student_v5_devA --weights $S/v5_b123d123.pth --opponents solution92,kaggle3,$R3 "${SW[@]}"
shasum -a 256 $S/v5_b123d123.pth $R/v5_mixed/weights/agent.pth
log "V5_DONE"
