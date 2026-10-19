#!/bin/bash
# Nacht-Pipeline 19./20.10.2026: wartet auf die Trainings, baut Ensembles,
# misst sie auf Val-Karten 500 720-500 819 und startet danach PPO fuer cnn2.
# Abgabe-Gewichte werden NICHT angefasst. Log: experiments/overnight_1910.log
cd "$(dirname "$0")/.."
LOG=experiments/overnight_1910.log
PY=.venv/bin/python
RULES="--set early_inference=true --set relic_filter=true --set subset_infer=true --set explore_grid=true --set scripted_explore=true --set explore_stale=20 --set keep_dead_fast=true"
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }

done_runs() {  # Anzahl fertiger Laeufe mit Muster $1
    grep -l '"status": "done"' experiments/runs/$1/manifest.json 2>/dev/null | wc -l
}
weights() {  # Gewichte aller Laeufe mit Muster $1
    for d in experiments/runs/$1; do printf "%s " "$d/weights/agent.pth"; done
}
evaluate() {  # evaluate NAME CHECKPOINT
    $PY -m scripts.par_eval --weights "$2" $RULES --first 720 --n 100 --workers ${WORKERS:-6} \
        --out experiments/compare/regeln/$1_720.csv >> $LOG 2>&1
    $PY -m scripts.compare_report --ref experiments/compare/regeln/N_r6_kdf_720.csv \
        experiments/compare/regeln/$1_720.csv >> $LOG 2>&1
}

log "Start"
R6=$(weights "20261019_full_rules_s[0-5]")

# 1) 6 Netze mit 70 % Solution_92
while [ "$(done_runs '20261019_full_rules_s*_sol70')" -lt 6 ]; do sleep 120; done
S70=$(weights "20261019_full_rules_s*_sol70")
log "sol70 fertig"
$PY -m scripts.build_ensemble --out experiments/ensembles/sol70_6.pth $S70 >> $LOG 2>&1
$PY -m scripts.build_ensemble --out experiments/ensembles/rules12.pth $R6 $S70 >> $LOG 2>&1
evaluate R_sol70_6 experiments/ensembles/sol70_6.pth
evaluate R_rules12 experiments/ensembles/rules12.pth

# 2) PPO fuer cnn2 (Start bei den BC-Gewichten des Lehrers rules6)
while ! grep -q "gespeichert" experiments/ppo/cnn2/log.txt 2>/dev/null; do sleep 120; done
log "cnn2 BC fertig"
WORKERS=6 evaluate P2_bc experiments/ppo/cnn2/bc.pth
nohup $PY -m scripts.ppo_train ppo --run cnn2 --iters 200 --games 48 --workers 6 --lr 1e-4 \
    --epochs 3 --mb 4096 --sol92 0.7 --default 0.1 --teacher 0.2 --detach-value --vf-warmup 5 \
    > experiments/ppo/cnn2/ppo_stdout.txt 2>&1 &
log "PPO cnn2 gestartet"

# 3) 6 Netze mit Gegner-Strafe + Pool
while [ "$(done_runs '20261019_full_rules_opp_s*_pool')" -lt 6 ]; do sleep 120; done
OPP=$(weights "20261019_full_rules_opp_s*_pool")
log "opp/pool fertig"
$PY -m scripts.build_ensemble --out experiments/ensembles/opp6.pth $OPP >> $LOG 2>&1
$PY -m scripts.build_ensemble --out experiments/ensembles/all18.pth $R6 $S70 $OPP >> $LOG 2>&1
WORKERS=4 evaluate R_opp6 experiments/ensembles/opp6.pth
WORKERS=4 evaluate R_all18 experiments/ensembles/all18.pth
log "Ende"
