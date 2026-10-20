#!/bin/bash
# 20.10.2026: wartet auf 6 x full_rules_fo und PPO cnn2c, baut Ensembles, misst sie
# auf Val 720-819 und frischen Val-Karten 501 820-502 019 gegen all18_fo10.
# Abgabe-Gewichte werden NICHT angefasst. Log: experiments/pipeline_2010.log
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_2010.log
PY=.venv/bin/python
D=experiments/compare/regeln
E=experiments/ensembles
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
done_runs() { grep -l '"status": "done"' experiments/runs/$1/manifest.json 2>/dev/null | wc -l; }
weights() { for d in experiments/runs/$1; do printf "%s " "$d/weights/agent.pth"; done; }
ev() { name=$1; w=$2; first=$3; n=$4; shift 4
    $PY -m scripts.par_eval --weights $w "$@" --first $first --n $n --workers ${WORKERS:-7} \
        --out $D/$name.csv 2>&1 | grep -v geladen >> $LOG; }
cmp() { $PY -m scripts.compare_report --ref $D/$1.csv $D/$2.csv 2>&1 | grep -E "default |solution92" >> $LOG; }

log "Start"
# 1) PPO cnn2c (Strafe fuer Gegnerpunkte)
while pgrep -f "ppo_train ppo --run cnn2c" > /dev/null; do sleep 60; done
log "PPO cnn2c beendet"
for it in 0010 0020 0030 0040; do
    [ -f experiments/ppo/cnn2c/ppo_$it.pth ] || continue
    WORKERS=4 ev P2c_ppo${it}_720 experiments/ppo/cnn2c/ppo_$it.pth 720 100
    cmp P2_ppo0040_720 P2c_ppo${it}_720
done
# 2) 6 Netze full_rules_fo
while [ "$(done_runs '20261020_full_rules_fo_s*_sol70')" -lt 6 ]; do sleep 120; done
log "full_rules_fo fertig"
FO=$(weights "20261020_full_rules_fo_s*_sol70")
ALL18=$(weights "20261019_full_rules_s[0-5]")$(weights "20261019_full_rules_s[6-9]_sol70")$(weights "20261019_full_rules_s1[01]_sol70")$(weights "20261019_full_rules_opp_s*_pool")
$PY -m scripts.build_ensemble --out $E/fo6.pth $FO >> $LOG 2>&1
$PY -m scripts.build_ensemble --out $E/all24fo_raw.pth $ALL18 $FO >> $LOG 2>&1
$PY -m scripts.set_cfg $E/all24fo_raw.pth $E/all24fo.pth keep_dead_fast=true far_opp=10 >> $LOG 2>&1
ev I_fo6_720 $E/fo6.pth 720 100
cmp F_a18_fo10_720 I_fo6_720
ev I_all24fo_720 $E/all24fo.pth 720 100
cmp F_a18_fo10_720 I_all24fo_720
# 3) frische Karten 501 820-502 019 (200 Karten)
ev J_a18fo10_1820 $E/all18_fo10.pth 1820 200
ev J_fo6_1820 $E/fo6.pth 1820 200
cmp J_a18fo10_1820 J_fo6_1820
ev J_all24fo_1820 $E/all24fo.pth 1820 200
cmp J_a18fo10_1820 J_all24fo_1820
log "Ende"
