#!/bin/bash
# 30.10.2026, 18:31: fuenfte Nachtrainingsrunde der Hauptlinie (Plan docs/superpowers/plans/2026-10-29-battle-push.md,
# Nachtrag 30.10., 18:31). Weiter ab experiments/runs/20261030_ft4_v10_s<seed> (Gewichte + Buffer), je 2.000 Spiele,
# Kartenversatz 4000 (letzter freier Block je Seed). Gegnermix und Pool wie Runde 4 (V10 + old3 + V11).
# PAR=6 statt 18, damit daneben Entwicklungsmessungen laufen koennen.
# Danach battle_ft5_18 (V10-Config) und die Kandidaten mit eingebranntem Regelsatz R:
# mix36e_as (V10 + ft5_18) und mix54e_as (V10 + ft3_18 + ft5_18).
#   bash scripts/pipeline_battle_ft5.sh        (GAMES=2000 PAR=6 per Umgebung aenderbar)
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_battle_ft5.log
PY=.venv/bin/python
E=experiments/ensembles
V10=experiments/releases/20261022_v10_baseline/agent_p0.pth
OLD3=experiments/releases/20261020_old3_sym3/agent_p0.pth
V11=$E/battle_mix36c_as.pth  # bytegleich mit der Abgabe V11 (wie in Runde 4)
GAMES=${GAMES:-2000}
PAR=${PAR:-6}
MIX="solution92=0.35,sol92_sq=0.25,sol92_weak=0.10,pool=0.20,rush=0.05,default=0.05"
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }
log "Start Runde 5: 18 Netze, $GAMES Spiele, $PAR parallel, Kartenversatz 4000, Pool V10 + old3 + V11"
run_five() {
    seed=$1
    init=experiments/runs/20261030_ft4_v10_s$seed
    name=20261030_ft5_v10_s$seed
    if grep -q '"status": "done"' experiments/runs/$name/manifest.json 2>/dev/null; then return 0; fi
    nice -n 5 $PY -m scripts.finetune --init $init --name $name --games $GAMES --seed $seed --map-offset 4000 \
        --variant full_rules_v10 --keep-final --val-every 500 --n-val 8 --no-test --prefill-games 0 \
        --mix "$MIX" --pool $V10 $OLD3 $V11 > experiments/batch_20261030_ft5_$seed.log 2>&1
    echo "[$(date '+%d.%m. %H:%M')] s$seed fertig (exit $?): $(tail -1 experiments/batch_20261030_ft5_$seed.log)" >> $LOG
}
export -f run_five
export PY GAMES MIX V10 OLD3 V11 LOG
seq 10 27 | xargs -P $PAR -I{} bash -c 'run_five {}'
W=""
for seed in $(seq 10 27); do
    f=experiments/runs/20261030_ft5_v10_s$seed/weights/agent.pth
    [ -f $f ] && W="$W $f"
done
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_ft5_18.pth $W >> $LOG 2>&1
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mix36e.pth $V10 $E/battle_ft5_18.pth >> $LOG 2>&1
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mix54e.pth $V10 $E/battle_ft3_18.pth $E/battle_ft5_18.pth >> $LOG 2>&1
for n in mix36e mix54e; do
    $PY -m scripts.set_cfg $E/battle_$n.pth $E/battle_${n}_as.pth art_splash=true sap_still_splash=true >> $LOG 2>&1
done
log "Ende Runde 5: ft5_18 $(shasum -a 256 $E/battle_ft5_18.pth | cut -c1-16), mix36e_as $(shasum -a 256 $E/battle_mix36e_as.pth | cut -c1-16), mix54e_as $(shasum -a 256 $E/battle_mix54e_as.pth | cut -c1-16)"
