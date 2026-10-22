#!/bin/bash
# 22.10.2026: 6 Netze unter V8-Bedingungen (Variante full_rules_v8: korrigiertes Gedaechtnis und
# V8-Regeln auch im Training), Starts 70-72 und 80-82 (Karten laut protocol.train_seed: Blockenden
# ab Index 5000, z. B. 205000-206499), je 3000 Spiele, 70 % Solution_92. Danach v8mix24 = 18 V3-Netze
# + 6 neue mit V8-Config und Entwicklungsmessung gegen V8 (D22_Bsnpdroc_*). Abgabe unberuehrt.
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_v8nets.log
PY=.venv/bin/python
E=experiments/ensembles
R=experiments/runs/20261022_full_rules_v8_s
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
log "Start Training"
for first in 70 80; do
    $PY -m scripts.run_experiments --variants full_rules_v8 --starts 3 --first-start $first --games 3000 \
        --val-every 500 --workers 3 --date 20261022 --tag sol70 --extra --no-test --sol92-frac 0.7 \
        > experiments/batch_20261022_full_rules_v8_$first.log 2>&1 &
done
wait
log "Training fertig: $(tail -1 experiments/batch_20261022_full_rules_v8_70.log) / $(tail -1 experiments/batch_20261022_full_rules_v8_80.log)"
W=""
for s in 70 71 72 80 81 82; do W="$W ${R}${s}_sol70/weights/agent.pth"; done
$PY -m scripts.build_ensemble --out $E/v8nets6.pth $W >> $LOG 2>&1
$PY -m scripts.build_ensemble --out $E/v8mix24_raw.pth $E/v8_Bsnpdroc.pth $W >> $LOG 2>&1
$PY -m scripts.set_cfg $E/v8mix24_raw.pth $E/v8mix24.pth nebula_avoid_mode=soft >> $LOG 2>&1
shasum -a 256 $E/v8nets6.pth $E/v8mix24.pth >> $LOG
bash experiments/analysis/hard_map_training_20261021/dev_eval2.sh v8mix24 ${WORKERS:-12} $E/v8mix24.pth >> $LOG 2>&1
log "Ende (Vergleich mit D22_Bsnpdroc_*: V8, 18 V3-Netze)"
