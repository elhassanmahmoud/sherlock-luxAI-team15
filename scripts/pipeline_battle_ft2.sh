#!/bin/bash
# 29.10.2026: zweite Nachtrainingsrunde (Plan docs/superpowers/plans/2026-10-29-battle-push.md, Arbeitsweg 2).
# Grund: 6 nachtrainierte Netze schlugen dieselben 6 Netze vorher auf Dev A (sol92_sq +4,7, Solution_92 +3,2 pp),
# die Trainingskurven stiegen nach 1500 Spielen noch. Weiter ab experiments/runs/20261029_ft_v10_s<seed>
# (Gewichte + Buffer), neue Trainingskarten (--map-offset 1000), sonst gleiche Einstellungen.
# Jedes Netz startet erst, wenn seine erste Runde fertig ist. Danach Ensemble battle_ft2_18 mit V10-Config.
#   bash scripts/pipeline_battle_ft2.sh        (GAMES=2000 PAR=6 per Umgebung aenderbar)
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_battle_ft2.log
PY=.venv/bin/python
V10=experiments/releases/20261022_v10_baseline/agent_p0.pth
OLD3=experiments/releases/20261020_old3_sym3/agent_p0.pth
GAMES=${GAMES:-2000}
PAR=${PAR:-6}
MIX="solution92=0.35,sol92_sq=0.25,sol92_weak=0.10,pool=0.20,rush=0.05,default=0.05"
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }
log "Start Runde 2: 18 Netze, $GAMES Spiele, $PAR parallel, Karten-Offset 1000"
run_two() {
    seed=$1
    init=experiments/runs/20261029_ft_v10_s$seed
    name=20261029_ft2_v10_s$seed
    until grep -q '"status": "done"' $init/manifest.json 2>/dev/null; do sleep 60; done
    if grep -q '"status": "done"' experiments/runs/$name/manifest.json 2>/dev/null; then return 0; fi
    nice -n 5 $PY -m scripts.finetune --init $init --name $name --games $GAMES --seed $seed --map-offset 1000 \
        --variant full_rules_v10 --keep-final --val-every 500 --n-val 8 --no-test --prefill-games 0 \
        --mix "$MIX" --pool $V10 $OLD3 > experiments/batch_20261029_ft2_$seed.log 2>&1
    echo "[$(date '+%d.%m. %H:%M')] s$seed fertig (exit $?): $(tail -1 experiments/batch_20261029_ft2_$seed.log)" >> $LOG
}
export -f run_two
export PY GAMES MIX V10 OLD3 LOG
seq 10 27 | xargs -P $PAR -I{} bash -c 'run_two {}'
W=""
for seed in $(seq 10 27); do
    f=experiments/runs/20261029_ft2_v10_s$seed/weights/agent.pth
    [ -f $f ] && W="$W $f"
done
$PY -m scripts.build_ensemble --cfg-from $V10 --out experiments/ensembles/battle_ft2_18.pth $W >> $LOG 2>&1
log "Ende Runde 2: $(shasum -a 256 experiments/ensembles/battle_ft2_18.pth | cut -c1-16)"
