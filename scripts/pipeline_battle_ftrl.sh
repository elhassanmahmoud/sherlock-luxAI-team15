#!/bin/bash
# 29.10.2026, 21:00: zweite Nachtrainings-Linie der 18 V3-Netze, "RL-Liga" (Plan-Nachtrag 29.10., 21:00 in
# docs/superpowers/plans/2026-10-29-battle-push.md). Gleiche Quellnetze und Einstellungen wie Runde 1
# (pipeline_battle_ft.sh), aber die Haelfte der Spiele gegen eigene RL-Abgaben, damit das Ensemble gegen
# Agenten anderer Teams (Netze + Regeln) robuster wird. Grund: mix36 gewinnt gegen V3/V7 +3,5/+6,5 pp und
# direkt 58 % gegen V10, gegen die Solution_92-Familie nur +0 bis +1,7; Runde 2 brachte denselben 6 Netzen
# auf Dev A nichts (ft2_6 gegen ft6: sol92_sq -2,3 [-5,8; +1,0], Solution_92 -0,2).
# Neue Trainingskarten (Kartenversatz 4000; 0-2999 Runden 1-3, 3000-3999 Runde 4), Laeufe experiments/runs/20261029_ftrl_v10_s<seed>,
# danach Ensemble battle_ftrl18 mit V10-Config.
#   bash scripts/pipeline_battle_ftrl.sh          (GAMES=1500 PAR=6 per Umgebung aenderbar)
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_battle_ftrl.log
PY=.venv/bin/python
R=experiments/releases
V10=$R/20261022_v10_baseline/agent_p0.pth
GAMES=${GAMES:-1500}
PAR=${PAR:-6}
MIX="solution92=0.20,sol92_sq=0.20,sol92_weak=0.05,pool=0.50,default=0.05"
POOL="$V10 $R/20261020_old3_sym3/agent_p0.pth experiments/ensembles/battle_mix36.pth $R/20261022_all18_v3/agent_p0.pth $R/20261022_v7_Bsnpd/agent_p0.pth"
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }
# Quellnetze in der Reihenfolge des V10-Ensembles, Seed 10 + Index (wie Runde 1)
SOURCES=$($PY -c "
import torch
ck = torch.load('$V10', map_location='cpu', weights_only=True)
for i, s in enumerate(ck['ensemble_sources']):
    print(10 + i, s.rsplit('/weights/', 1)[0])
")
log "Start RL-Liga: $(echo "$SOURCES" | wc -l | tr -d ' ') Netze, $GAMES Spiele, $PAR parallel, Kartenversatz 4000, Mix $MIX, Pool $POOL"
run_rl() {
    seed=$1; init=$2
    name=20261029_ftrl_v10_s$seed
    if grep -q '"status": "done"' experiments/runs/$name/manifest.json 2>/dev/null; then return 0; fi
    nice -n 5 $PY -m scripts.finetune --init "$init" --name $name --games $GAMES --seed $seed --map-offset 4000 \
        --variant full_rules_v10 --keep-final --val-every 500 --n-val 8 --no-test --prefill-games 0 \
        --mix "$MIX" --pool $POOL > experiments/batch_20261029_ftrl_$seed.log 2>&1
    echo "[$(date '+%d.%m. %H:%M')] s$seed fertig (exit $?): $(tail -1 experiments/batch_20261029_ftrl_$seed.log)" >> $LOG
}
export -f run_rl
export PY GAMES MIX POOL LOG
echo "$SOURCES" | xargs -P $PAR -L 1 bash -c 'run_rl "$0" "$1"'
W=""
for seed in $(echo "$SOURCES" | cut -d' ' -f1); do
    f=experiments/runs/20261029_ftrl_v10_s$seed/weights/agent.pth
    [ -f $f ] && W="$W $f"
done
$PY -m scripts.build_ensemble --cfg-from $V10 --out experiments/ensembles/battle_ftrl18.pth $W >> $LOG 2>&1
log "Ende RL-Liga: $(shasum -a 256 experiments/ensembles/battle_ftrl18.pth | cut -c1-16)"
