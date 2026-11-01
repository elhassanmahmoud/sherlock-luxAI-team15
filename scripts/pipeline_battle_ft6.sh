#!/bin/bash
# 01.11.2026, 04:25: Nachtraining unter allen V12-Regeln und den Nebel-Korrekturen (Plan
# docs/superpowers/plans/2026-10-29-battle-push.md, Nachtrag 01.11., 04:25). Weiter ab den V12-Netzen
# experiments/runs/20261029_ft3_v10_s16..s27 (Gewichte + Buffer), je 2.000 Spiele, Variante full_rules_v12,
# Kartenversatz 4000 (fuer s16-s27 unbenutzt). Pool: V10, old3, V11, V12. Danach:
#   battle_ft6_12  (die 12 neuen Netze),
#   battle_v17a    (V12-Netze + 12 neue = 48),
#   battle_v17b    (V10-Netze + ft3 s10-s15 + 12 neue = 36, ersetzt die 12 Vorgaenger),
# beide mit V12-Config + est_censor + neb_cross.
#   bash scripts/pipeline_battle_ft6.sh        (GAMES=2000 PAR=12 per Umgebung aenderbar)
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_battle_ft6.log
PY=.venv/bin/python
E=experiments/ensembles
V10=experiments/releases/20261022_v10_baseline/agent_p0.pth
OLD3=experiments/releases/20261020_old3_sym3/agent_p0.pth
V11=$E/battle_mix36c_as.pth
V12=$E/battle_v12.pth
GAMES=${GAMES:-2000}
PAR=${PAR:-12}
MIX="solution92=0.30,sol92_sq=0.20,sol92_weak=0.10,pool=0.30,rush=0.05,default=0.05"
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }
log "Start Runde 6: 12 Netze (s16-s27), $GAMES Spiele, $PAR parallel, Kartenversatz 4000, Variante full_rules_v12, Pool V10 + old3 + V11 + V12, Code $(git rev-parse --short HEAD)"
run_six() {
    seed=$1
    init=experiments/runs/20261029_ft3_v10_s$seed
    name=20261101_ft6_v12_s$seed
    if grep -q '"status": "done"' experiments/runs/$name/manifest.json 2>/dev/null; then return 0; fi
    nice -n 5 $PY -m scripts.finetune --init $init --name $name --games $GAMES --seed $seed --map-offset 4000 \
        --variant full_rules_v12 --keep-final --val-every 500 --n-val 8 --no-test --prefill-games 0 \
        --mix "$MIX" --pool $V10 $OLD3 $V11 $V12 > experiments/batch_20261101_ft6_$seed.log 2>&1
    echo "[$(date '+%d.%m. %H:%M')] s$seed fertig (exit $?): $(tail -1 experiments/batch_20261101_ft6_$seed.log)" >> $LOG
}
export -f run_six
export PY GAMES MIX V10 OLD3 V11 V12 LOG
seq 16 27 | xargs -P $PAR -I{} bash -c 'run_six {}'
NEW=""
for seed in $(seq 16 27); do
    f=experiments/runs/20261101_ft6_v12_s$seed/weights/agent.pth
    [ -f $f ] && NEW="$NEW $f"
done
OLD6=""
for seed in $(seq 10 15); do OLD6="$OLD6 experiments/runs/20261029_ft3_v10_s$seed/weights/agent.pth"; done
$PY -m scripts.build_ensemble --cfg-from $V12 --out $E/battle_ft6_12.pth $NEW >> $LOG 2>&1
$PY -m scripts.build_ensemble --cfg-from $V12 --out $E/battle_v17a_raw.pth $V12 $E/battle_ft6_12.pth >> $LOG 2>&1
$PY -m scripts.build_ensemble --cfg-from $V12 --out $E/battle_v17b_raw.pth $V10 $OLD6 $E/battle_ft6_12.pth >> $LOG 2>&1
for n in v17a v17b; do
    $PY -m scripts.set_cfg $E/battle_${n}_raw.pth $E/battle_$n.pth est_censor=true neb_cross=true >> $LOG 2>&1
done
log "Ende Runde 6: ft6_12 $(shasum -a 256 $E/battle_ft6_12.pth | cut -c1-16), v17a $(shasum -a 256 $E/battle_v17a.pth | cut -c1-16), v17b $(shasum -a 256 $E/battle_v17b.pth | cut -c1-16)"
