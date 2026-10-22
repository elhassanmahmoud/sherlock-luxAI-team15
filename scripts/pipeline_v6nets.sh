#!/bin/bash
# 22.10.2026: 6 neue Netze mit V6-Regeln im Training (Variante full_rules_v6, Starts 27-29 und 37-39,
# je 3000 Spiele, 70 % Solution_92) und automatische Entwicklungsmessung: gleiche Regeln (Bs),
# 18 V3-Netze (v6_Bs) gegen 18 V3-Netze + 6 neue (v6mix24) und die 6 neuen allein (v6nets6),
# jeweils auf dev_hard330/dev_easy330 (Trainingskarten 270000-291499 und 370000-391499, die
# Entwicklungs-Sets bei 360000-361999). Abgabe-Gewichte unberuehrt. Log: experiments/pipeline_v6nets.log
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_v6nets.log
PY=.venv/bin/python
E=experiments/ensembles
R=experiments/runs/20261022_full_rules_v6_s
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
log "Start Training"
for first in 27 37; do
    $PY -m scripts.run_experiments --variants full_rules_v6 --starts 3 --first-start $first --games 3000 \
        --val-every 500 --workers 3 --date 20261022 --tag sol70 --extra --no-test --sol92-frac 0.7 \
        > experiments/batch_20261022_full_rules_v6_$first.log 2>&1 &
done
wait
log "Training fertig: $(tail -1 experiments/batch_20261022_full_rules_v6_27.log) / $(tail -1 experiments/batch_20261022_full_rules_v6_37.log)"
W=""
for s in 27 28 29 37 38 39; do W="$W ${R}${s}_sol70/weights/agent.pth"; done
$PY -m scripts.build_ensemble --out $E/v6nets6.pth $W >> $LOG 2>&1
$PY -m scripts.build_ensemble --out $E/v6mix24_raw.pth $E/v6_Bs.pth $W >> $LOG 2>&1
$PY -m scripts.set_cfg $E/v6mix24_raw.pth $E/v6mix24.pth nebula_avoid_mode=soft >> $LOG 2>&1
shasum -a 256 $E/v6nets6.pth $E/v6mix24.pth agents/sherlock/weights/agent_p0.pth >> $LOG
E2=experiments/analysis/hard_map_training_20261021/dev_eval2.sh
bash $E2 v6mix24 ${WORKERS:-8} $E/v6mix24.pth >> $LOG 2>&1
bash $E2 v6nets6 ${WORKERS:-8} $E/v6nets6.pth >> $LOG 2>&1
log "Ende (Vergleich mit D22_Bs_*: gleiche Regeln, 18 V3-Netze)"
