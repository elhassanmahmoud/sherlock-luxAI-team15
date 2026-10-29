#!/bin/bash
# 29.10.2026: dritte Nachtrainingsrunde (Plan docs/superpowers/plans/2026-10-29-battle-push.md, Arbeitsweg 2).
# Grund: Die Trainingskurven der Runden 1-2 steigen weiter (Einzelnetz gegen Solution_92 61 % -> 71 %,
# gegen sol92_sq 48 % -> 54-56 %). Weiter ab experiments/runs/20261029_ft2_v10_s<seed> (Gewichte + Buffer),
# neue Trainingskarten (--map-offset 2000). Einzige Aenderung zum Mix: der Pool enthaelt zusaetzlich die
# bisher beste Mischung battle_mix36 (V10 + ft18), damit die Netze auch gegen einen starken RL-Gegner lernen.
# Danach Ensemble battle_ft3_18 mit V10-Config.
#   bash scripts/pipeline_battle_ft3.sh        (GAMES=2000 PAR=6 per Umgebung aenderbar)
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_battle_ft3.log
PY=.venv/bin/python
V10=experiments/releases/20261022_v10_baseline/agent_p0.pth
OLD3=experiments/releases/20261020_old3_sym3/agent_p0.pth
MIX36=experiments/ensembles/battle_mix36.pth
GAMES=${GAMES:-2000}
PAR=${PAR:-6}
MIX="solution92=0.35,sol92_sq=0.25,sol92_weak=0.10,pool=0.20,rush=0.05,default=0.05"
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }
log "Start Runde 3: 18 Netze, $GAMES Spiele, $PAR parallel, Karten-Offset 2000, Pool V10 + old3 + mix36"
run_three() {
    seed=$1
    init=experiments/runs/20261029_ft2_v10_s$seed
    name=20261029_ft3_v10_s$seed
    until grep -q '"status": "done"' $init/manifest.json 2>/dev/null; do sleep 60; done
    if grep -q '"status": "done"' experiments/runs/$name/manifest.json 2>/dev/null; then return 0; fi
    nice -n 5 $PY -m scripts.finetune --init $init --name $name --games $GAMES --seed $seed --map-offset 2000 \
        --variant full_rules_v10 --keep-final --val-every 500 --n-val 8 --no-test --prefill-games 0 \
        --mix "$MIX" --pool $V10 $OLD3 $MIX36 > experiments/batch_20261029_ft3_$seed.log 2>&1
    echo "[$(date '+%d.%m. %H:%M')] s$seed fertig (exit $?): $(tail -1 experiments/batch_20261029_ft3_$seed.log)" >> $LOG
}
export -f run_three
export PY GAMES MIX V10 OLD3 MIX36 LOG
seq 10 27 | xargs -P $PAR -I{} bash -c 'run_three {}'
W=""
for seed in $(seq 10 27); do
    f=experiments/runs/20261029_ft3_v10_s$seed/weights/agent.pth
    [ -f $f ] && W="$W $f"
done
$PY -m scripts.build_ensemble --cfg-from $V10 --out experiments/ensembles/battle_ft3_18.pth $W >> $LOG 2>&1
log "Ende Runde 3: $(shasum -a 256 experiments/ensembles/battle_ft3_18.pth | cut -c1-16)"
