#!/bin/bash
# 30.10.2026, 05:45: vierte Nachtrainings-Linie "Altnetze" (Plan-Nachtrag 30.10., 05:45 in
# docs/superpowers/plans/2026-10-29-battle-push.md). 12 Quellnetze, nie in einer Abgabe und keine
# zurueckgehaltenen Gegner: 6 x full_rules_v6 (22.10.) und 6 x full_rules_fo (20.10.), unter allen V10-Regeln
# nachtrainiert wie die v8-Linie. Seeds 0-9, 28, 29, Kartenversatz 0, Laeufe
# experiments/runs/20261030_ftold_v10_s<seed>. Danach Ensemble battle_ftold12 mit V10-Config sowie
# mix30old (V10 + ftold12) und Screen mit scripts/battle_screen.sh auf Dev A.
#   bash scripts/pipeline_battle_ftold.sh          (GAMES=1500 PAR=12 per Umgebung aenderbar)
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_battle_ftold.log
PY=.venv/bin/python
R=experiments/releases
E=experiments/ensembles
V10=$R/20261022_v10_baseline/agent_p0.pth
GAMES=${GAMES:-1500}
PAR=${PAR:-12}
MIX="solution92=0.30,sol92_sq=0.25,sol92_weak=0.10,pool=0.25,rush=0.05,default=0.05"
POOL="$V10 $R/20261020_old3_sym3/agent_p0.pth $E/battle_mix36.pth $R/20261022_all18_v3/agent_p0.pth $R/20261022_v7_Bsnpd/agent_p0.pth"
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }
SOURCES="0 experiments/runs/20261022_full_rules_v6_s27_sol70
1 experiments/runs/20261022_full_rules_v6_s28_sol70
2 experiments/runs/20261022_full_rules_v6_s29_sol70
3 experiments/runs/20261022_full_rules_v6_s37_sol70
4 experiments/runs/20261022_full_rules_v6_s38_sol70
5 experiments/runs/20261022_full_rules_v6_s39_sol70
6 experiments/runs/20261020_full_rules_fo_s30_sol70
7 experiments/runs/20261020_full_rules_fo_s31_sol70
8 experiments/runs/20261020_full_rules_fo_s32_sol70
9 experiments/runs/20261020_full_rules_fo_s33_sol70
28 experiments/runs/20261020_full_rules_fo_s34_sol70
29 experiments/runs/20261020_full_rules_fo_s35_sol70"
until grep -q "Ende v8-Linie" experiments/pipeline_battle_ftv8.log 2>/dev/null; do sleep 60; done
log "Start Linie 4 (Altnetze): 12 Netze, $GAMES Spiele, $PAR parallel, Kartenversatz 0, Mix $MIX, Pool $POOL"
run_old() {
    seed=$1; init=$2
    name=20261030_ftold_v10_s$seed
    if grep -q '"status": "done"' experiments/runs/$name/manifest.json 2>/dev/null; then return 0; fi
    nice -n 5 $PY -m scripts.finetune --init "$init" --name $name --games $GAMES --seed $seed --map-offset 0 \
        --variant full_rules_v10 --keep-final --val-every 500 --n-val 8 --no-test --prefill-games 0 \
        --mix "$MIX" --pool $POOL > experiments/batch_20261030_ftold_$seed.log 2>&1
    echo "[$(date '+%d.%m. %H:%M')] s$seed fertig (exit $?): $(tail -1 experiments/batch_20261030_ftold_$seed.log)" >> $LOG
}
export -f run_old
export PY GAMES MIX POOL LOG
echo "$SOURCES" | xargs -P $PAR -L 1 bash -c 'run_old "$0" "$1"'
W=""
for seed in $(echo "$SOURCES" | cut -d' ' -f1); do
    f=experiments/runs/20261030_ftold_v10_s$seed/weights/agent.pth
    [ -f $f ] && W="$W $f"
done
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_ftold12.pth $W >> $LOG 2>&1
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mix30old.pth $V10 $E/battle_ftold12.pth >> $LOG 2>&1
log "Ende Linie 4: ftold12 $(shasum -a 256 $E/battle_ftold12.pth | cut -c1-16)"
WORKERS=6 bash scripts/battle_screen.sh mix30old $E/battle_mix30old.pth > /dev/null
log "Screen Linie 4 fertig"
