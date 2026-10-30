#!/bin/bash
# 30.10.2026, 14:35: vierte Nachtrainingsrunde der Hauptlinie (Plan docs/superpowers/plans/2026-10-29-battle-push.md,
# Nachtrag 30.10., 14:35). Weiter ab experiments/runs/20261029_ft3_v10_s<seed> (Gewichte + Buffer), je 2.000 Spiele,
# Kartenversatz 3000. Gegnermix wie Runden 1-3; der Pool enthaelt statt mix36 jetzt die Abgabe V11
# (battle_mix36c_as.pth, mit art_splash/sap_still_splash), damit die Netze gegen den staerksten RL-Gegner lernen.
# Danach battle_ft4_18 (V10-Config) und die Kandidaten fuer Runde 3 mit eingebranntem Regelsatz R:
# mix36d_as (V10 + ft4_18) und mix54d_as (V10 + ft3_18 + ft4_18).
#   bash scripts/pipeline_battle_ft4.sh        (GAMES=2000 PAR=18 per Umgebung aenderbar)
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_battle_ft4.log
PY=.venv/bin/python
E=experiments/ensembles
V10=experiments/releases/20261022_v10_baseline/agent_p0.pth
OLD3=experiments/releases/20261020_old3_sym3/agent_p0.pth
V11=$E/battle_mix36c_as.pth
GAMES=${GAMES:-2000}
PAR=${PAR:-18}
MIX="solution92=0.35,sol92_sq=0.25,sol92_weak=0.10,pool=0.20,rush=0.05,default=0.05"
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }
log "Start Runde 4: 18 Netze, $GAMES Spiele, $PAR parallel, Kartenversatz 3000, Pool V10 + old3 + V11"
run_four() {
    seed=$1
    init=experiments/runs/20261029_ft3_v10_s$seed
    name=20261030_ft4_v10_s$seed
    if grep -q '"status": "done"' experiments/runs/$name/manifest.json 2>/dev/null; then return 0; fi
    nice -n 5 $PY -m scripts.finetune --init $init --name $name --games $GAMES --seed $seed --map-offset 3000 \
        --variant full_rules_v10 --keep-final --val-every 500 --n-val 8 --no-test --prefill-games 0 \
        --mix "$MIX" --pool $V10 $OLD3 $V11 > experiments/batch_20261030_ft4_$seed.log 2>&1
    echo "[$(date '+%d.%m. %H:%M')] s$seed fertig (exit $?): $(tail -1 experiments/batch_20261030_ft4_$seed.log)" >> $LOG
}
export -f run_four
export PY GAMES MIX V10 OLD3 V11 LOG
seq 10 27 | xargs -P $PAR -I{} bash -c 'run_four {}'
W=""
for seed in $(seq 10 27); do
    f=experiments/runs/20261030_ft4_v10_s$seed/weights/agent.pth
    [ -f $f ] && W="$W $f"
done
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_ft4_18.pth $W >> $LOG 2>&1
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mix36d.pth $V10 $E/battle_ft4_18.pth >> $LOG 2>&1
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mix54d.pth $V10 $E/battle_ft3_18.pth $E/battle_ft4_18.pth >> $LOG 2>&1
for n in mix36d mix54d; do
    $PY -m scripts.set_cfg $E/battle_$n.pth $E/battle_${n}_as.pth art_splash=true sap_still_splash=true >> $LOG 2>&1
done
log "Ende Runde 4: ft4_18 $(shasum -a 256 $E/battle_ft4_18.pth | cut -c1-16), mix36d_as $(shasum -a 256 $E/battle_mix36d_as.pth | cut -c1-16), mix54d_as $(shasum -a 256 $E/battle_mix54d_as.pth | cut -c1-16)"
