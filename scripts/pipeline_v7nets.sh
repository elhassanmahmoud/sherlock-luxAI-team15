#!/bin/bash
# 22.10.2026: 6 weitere Netze mit V7-Gedaechtnis im Training (Variante full_rules_v7 = V6-Regeln +
# nebula_infer + drift_track; Starts 57-59 und 67-69, je 3000 Spiele, 70 % Solution_92, Trainingskarten
# 570000-591499 und 670000-691499). Danach Ensemble mix30 = 18 V3-Netze + 6 V6-Netze + 6 neue mit der
# Config von RULES_FROM (Regeln/Schalter) und Entwicklungsmessung auf dev_hard330/dev_easy330.
#   RULES_FROM=experiments/ensembles/<kandidat>.pth bash scripts/pipeline_v7nets.sh
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_v7nets.log
PY=.venv/bin/python
E=experiments/ensembles
R=experiments/runs/20261022_full_rules_v7_s
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
log "Start Training"
for first in 57 67; do
    $PY -m scripts.run_experiments --variants full_rules_v7 --starts 3 --first-start $first --games 3000 \
        --val-every 500 --workers 3 --date 20261022 --tag sol70 --extra --no-test --sol92-frac 0.7 \
        > experiments/batch_20261022_full_rules_v7_$first.log 2>&1 &
done
wait
log "Training fertig: $(tail -1 experiments/batch_20261022_full_rules_v7_57.log) / $(tail -1 experiments/batch_20261022_full_rules_v7_67.log)"
W=""
for s in 57 58 59 67 68 69; do W="$W ${R}${s}_sol70/weights/agent.pth"; done
$PY -m scripts.build_ensemble --out $E/v7nets6.pth $W >> $LOG 2>&1
log "Netze gebaut; Mischung und Messung folgen mit RULES_FROM (siehe Arbeitsstand)"
