#!/bin/bash
# 29.10.2026: weitere Nachtrainingsrunde N (Plan docs/superpowers/plans/2026-10-29-battle-push.md, Arbeitsweg 2),
# allgemein fuer Runde 4 und spaeter. Jedes Netz startet ab dem Endstand seiner Vorrunde (Gewichte + Buffer),
# sobald diese fertig ist, auf neuen Trainingskarten (Kartenversatz 1000 * (N - 1)). Danach Ensemble
# battle_ft<N>_18 mit V10-Config.
#   bash scripts/pipeline_battle_ftn.sh N VORRUNDE_PRAEFIX NAME_PRAEFIX
#   z. B. bash scripts/pipeline_battle_ftn.sh 4 20261029_ft3_v10_s 20261030_ft4_v10_s
# Umgebung: GAMES (2000), PAR (6), MIX (wie Runde 1-3), POOL (V10, old3, battle_mix36)
cd "$(dirname "$0")/.."
ROUND=$1; PREV=$2; NAMEP=$3
[ -n "$NAMEP" ] || { echo "N VORRUNDE_PRAEFIX NAME_PRAEFIX"; exit 1; }
LOG=experiments/pipeline_battle_ft$ROUND.log
PY=.venv/bin/python
V10=experiments/releases/20261022_v10_baseline/agent_p0.pth
OLD3=experiments/releases/20261020_old3_sym3/agent_p0.pth
GAMES=${GAMES:-2000}
PAR=${PAR:-6}
MIX=${MIX:-"solution92=0.35,sol92_sq=0.25,sol92_weak=0.10,pool=0.20,rush=0.05,default=0.05"}
POOL=${POOL:-"$V10 $OLD3 experiments/ensembles/battle_mix36.pth"}
OFFSET=$(( 1000 * (ROUND - 1) ))
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }
log "Start Runde $ROUND: 18 Netze ab $PREV*, $GAMES Spiele, $PAR parallel, Kartenversatz $OFFSET, Mix $MIX, Pool $POOL"
run_n() {
    seed=$1
    init=experiments/runs/$PREV$seed
    name=$NAMEP$seed
    until grep -q '"status": "done"' $init/manifest.json 2>/dev/null; do sleep 60; done
    if grep -q '"status": "done"' experiments/runs/$name/manifest.json 2>/dev/null; then return 0; fi
    nice -n 5 $PY -m scripts.finetune --init $init --name $name --games $GAMES --seed $seed --map-offset $OFFSET \
        --variant full_rules_v10 --keep-final --val-every 500 --n-val 8 --no-test --prefill-games 0 \
        --mix "$MIX" --pool $POOL > experiments/batch_${NAMEP}$seed.log 2>&1
    echo "[$(date '+%d.%m. %H:%M')] s$seed fertig (exit $?): $(tail -1 experiments/batch_${NAMEP}$seed.log)" >> $LOG
}
export -f run_n
export PY GAMES MIX POOL OFFSET PREV NAMEP LOG
seq 10 27 | xargs -P $PAR -I{} bash -c 'run_n {}'
W=""
for seed in $(seq 10 27); do
    f=experiments/runs/$NAMEP$seed/weights/agent.pth
    [ -f $f ] && W="$W $f"
done
$PY -m scripts.build_ensemble --cfg-from $V10 --out experiments/ensembles/battle_ft${ROUND}_18.pth $W >> $LOG 2>&1
log "Ende Runde $ROUND: $(shasum -a 256 experiments/ensembles/battle_ft${ROUND}_18.pth | cut -c1-16)"
