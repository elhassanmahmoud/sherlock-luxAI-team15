#!/bin/bash
# 20.10.2026 spaetabends: 6 x full_rules_v3 (pt_sap/far_cand schon im Training, 3000 Spiele,
# 70 % Solution_92), danach Ensembles v3nets6 und all24v3 auf Val 720-819 und frischen
# Karten 502 620-502 819 gegen all18_v3. (502 420-502 619 sind fuer Moayed reserviert.)
# Abgabe-Gewichte werden NICHT angefasst. Log: experiments/pipeline_v3nets.log
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_v3nets.log
PY=.venv/bin/python
D=experiments/compare/regeln
E=experiments/ensembles
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
weights() { for d in experiments/runs/$1; do printf "%s " "$d/weights/agent.pth"; done; }
ev() { name=$1; w=$2; first=$3; n=$4
    $PY -m scripts.par_eval --weights $w --first $first --n $n --workers 6 --out $D/$name.csv 2>&1 \
        | grep -v geladen >> $LOG; }
cmp() { $PY -m scripts.compare_report --ref $D/$1.csv $D/$2.csv 2>&1 | grep -E "default |solution92" >> $LOG; }
log "Start"
$PY -m scripts.run_experiments --variants full_rules_v3 --starts 6 --first-start 40 --games 3000 \
    --val-every 250 --workers 6 --date 20261020 --tag sol70 --extra --no-test --sol92-frac 0.7 \
    > experiments/batch_20261020_full_rules_v3.log 2>&1
log "Training fertig"
V3=$(weights "20261020_full_rules_v3_s4[0-5]_sol70")
ALL18=$(weights "20261019_full_rules_s[0-5]")$(weights "20261019_full_rules_s[6-9]_sol70")$(weights "20261019_full_rules_s1[01]_sol70")$(weights "20261019_full_rules_opp_s*_pool")
$PY -m scripts.build_ensemble --out $E/v3nets6.pth $V3 >> $LOG 2>&1
$PY -m scripts.build_ensemble --out $E/all24v3_raw.pth $ALL18 $V3 >> $LOG 2>&1
$PY -m scripts.set_cfg $E/all24v3_raw.pth $E/all24v3.pth keep_dead_fast=true far_opp=10 far_cand=true pt_sap=true >> $LOG 2>&1
ev R3_v3nets6_720 $E/v3nets6.pth 720 100;   cmp O_v3_720 R3_v3nets6_720
ev R3_all24v3_720 $E/all24v3.pth 720 100;   cmp O_v3_720 R3_all24v3_720
ev R3_v3_2620 $E/all18_v3.pth 2620 200
ev R3_v3nets6_2620 $E/v3nets6.pth 2620 200; cmp R3_v3_2620 R3_v3nets6_2620
ev R3_all24v3_2620 $E/all24v3.pth 2620 200; cmp R3_v3_2620 R3_all24v3_2620
log "Ende"
