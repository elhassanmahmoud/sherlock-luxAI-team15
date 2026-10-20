#!/bin/bash
# 20.10.2026 abends: CNN cnn3 = Nachahmung von all18_fo10 (bester Kandidat) + PPO.
# Ablauf: 1200 Lehrerspiele -> BC (48 Kanaele x 4 Bloecke, 6 Epochen) -> PPO 60 Iterationen
# (Stand alle 5) -> Messung BC + PPO-Staende auf Val 720-819 -> bester Stand und
# all18_fo10 auf frischen Karten 502 020-502 219. Abgabe-Gewichte werden NICHT angefasst.
# Log: experiments/pipeline_cnn3.log, Lauf: experiments/ppo/cnn3/
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_cnn3.log
PY=.venv/bin/python
D=experiments/compare/regeln
R=experiments/ppo/cnn3
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
ev() { name=$1; w=$2; first=$3; n=$4
    $PY -m scripts.par_eval --weights $w --first $first --n $n --workers 7 --out $D/$name.csv 2>&1 \
        | grep -v geladen >> $LOG; }
wr() { $PY - "$1" <<'PYEOF'
import sys, pandas as pd
d = pd.read_csv(sys.argv[1]); print(d[d.opponent == "solution92"].result.mean())
PYEOF
}

log "Start"
mkdir -p $R
$PY -m scripts.ppo_train collect --run cnn3 --seed 3 --workers 7 --games 1200 \
    --teacher-path experiments/ensembles/all18_fo10.pth > $R/collect_stdout.txt 2>&1 || { log "collect FEHLER"; exit 1; }
log "Lehrerspiele fertig"
$PY -m scripts.ppo_train bc --run cnn3 --seed 3 --epochs 6 --lr 5e-4 --mb 4096 --ch 48 --blocks 4 \
    > $R/bc_stdout.txt 2>&1 || { log "BC FEHLER"; exit 1; }
log "BC fertig"
$PY -m scripts.ppo_train ppo --run cnn3 --seed 3 --iters 60 --games 48 --workers 6 --lr 1e-4 \
    --epochs 3 --mb 4096 --sol92 0.7 --default 0.1 --teacher 0.2 --detach-value --vf-warmup 5 \
    --save-every 5 > $R/ppo_stdout.txt 2>&1 || log "PPO FEHLER"
log "PPO fertig"
ev Q3_bc_720 $R/bc.pth 720 100
best=$R/bc.pth; bestwr=$(wr $D/Q3_bc_720.csv)
for it in 0010 0020 0030 0040 0050 0060; do
    [ -f $R/ppo_$it.pth ] || continue
    ev Q3_ppo${it}_720 $R/ppo_$it.pth 720 100
    w=$(wr $D/Q3_ppo${it}_720.csv)
    if $PY -c "import sys; sys.exit(0 if float('$w') > float('$bestwr') else 1)"; then best=$R/ppo_$it.pth; bestwr=$w; fi
done
log "bester cnn3-Stand auf Val 720: $best ($bestwr)"
ev Q3_best_2020 $best 2020 200
ev Q3_a18fo10_2020 experiments/ensembles/all18_fo10.pth 2020 200
$PY -m scripts.compare_report --ref $D/Q3_a18fo10_2020.csv $D/Q3_best_2020.csv 2>&1 | grep -E "default |solution92" >> $LOG
log "Ende"
