#!/bin/bash
# Nacht 19./20.10.2026 (Teil 2): 6 weitere full_rules-Netze (70 % Solution_92) fuer ein
# 24er-Ensemble, danach Messung auf frischen Val-Karten 501 220-501 419 gegen all18_kdf;
# nach dem Ende von PPO cnn2 die Checkpoints auf Val 720-819 gegen BC messen.
# Abgabe-Gewichte werden NICHT angefasst. Log: experiments/overnight_2010.log
cd "$(dirname "$0")/.."
LOG=experiments/overnight_2010.log
PY=.venv/bin/python
D=experiments/compare/regeln
E=experiments/ensembles
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
done_runs() { grep -l '"status": "done"' experiments/runs/$1/manifest.json 2>/dev/null | wc -l; }
weights() { for d in experiments/runs/$1; do printf "%s " "$d/weights/agent.pth"; done; }
ev() { name=$1; w=$2; first=$3; n=$4; shift 4
    $PY -m scripts.par_eval --weights $w "$@" --first $first --n $n --workers ${WORKERS:-6} \
        --out $D/$name.csv 2>&1 | grep -v geladen >> $LOG; }

log "Start"
$PY -m scripts.run_experiments --variants full_rules --starts 6 --first-start 18 --games 4000 \
    --val-every 250 --workers 6 --date 20261019 --tag sol70 --extra --no-test --sol92-frac 0.7 \
    > experiments/batch_20261019_full_rules_sol70b.log 2>&1
log "6 Netze fertig: $(done_runs '20261019_full_rules_s1[89]_sol70') + $(done_runs '20261019_full_rules_s2[0-3]_sol70')"
NEW=$(weights "20261019_full_rules_s1[89]_sol70")$(weights "20261019_full_rules_s2[0-3]_sol70")
ALL18=$(weights "20261019_full_rules_s[0-5]")$(weights "20261019_full_rules_s[6-9]_sol70")$(weights "20261019_full_rules_s1[01]_sol70")$(weights "20261019_full_rules_opp_s*_pool")
$PY -m scripts.build_ensemble --out $E/all24.pth $ALL18 $NEW >> $LOG 2>&1
$PY -m scripts.set_cfg $E/all24.pth $E/all24_kdf.pth keep_dead_fast=true >> $LOG 2>&1
ev Y_all24_720 $E/all24_kdf.pth 720 100
$PY -m scripts.compare_report --ref $D/R_all18_720.csv $D/Y_all24_720.csv >> $LOG 2>&1
ev Y_all18_1220 $E/all18_kdf.pth 1220 200
ev Y_all24_1220 $E/all24_kdf.pth 1220 200
$PY -m scripts.compare_report --ref $D/Y_all18_1220.csv $D/Y_all24_1220.csv >> $LOG 2>&1

while pgrep -f "ppo_train ppo --run cnn2" > /dev/null; do sleep 120; done
log "PPO cnn2 beendet"
for it in 0050 0100 0150 0200; do
    [ -f experiments/ppo/cnn2/ppo_$it.pth ] || continue
    ev P2_ppo${it}_720 experiments/ppo/cnn2/ppo_$it.pth 720 100
    $PY -m scripts.compare_report --ref $D/P2_bc_720.csv $D/P2_ppo${it}_720.csv >> $LOG 2>&1
done
log "Ende"
