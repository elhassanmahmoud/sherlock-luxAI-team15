#!/bin/bash
# 30.10.2026, 02:10: dritte Nachtrainings-Linie "v8-Linie" (Plan-Nachtrag 30.10., 02:10 in
# docs/superpowers/plans/2026-10-29-battle-push.md). Die 12 Netze full_rules_v8 vom 22.10. (Quellen von
# v10nets12; nie in einer Abgabe und keine zurueckgehaltenen Gegner) unter allen V10-Regeln nachtrainieren,
# mit dem Gegnermix der gestrichenen Runde 4. Grund: Die Gewinne kamen bisher aus der Mischung unterschiedlich
# trainierter Netze (mix36/mix36b/mix54 besser als ft18 allein); die v8-Netze sind eine eigene Linie mit
# eigener Initialisierung.
# Kartenbereich der gestrichenen Runde 4 (Kartenversatz 3000, nie benutzt), Seeds 10-21, Laeufe
# experiments/runs/20261030_ftv8_v10_s<seed>. Danach Ensemble battle_ftv8_12 mit V10-Config sowie
# mix30v8 (V10 + ftv8_12) und mix48 (V10 + ft2_18 + ftv8_12), Screen mit scripts/battle_screen.sh auf Dev A.
# Parallel dazu Screen von mix36b (Wahl der Auswahl Runde 1) als Vergleich.
#   bash scripts/pipeline_battle_ftv8.sh          (GAMES=1500 PAR=12 per Umgebung aenderbar)
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_battle_ftv8.log
PY=.venv/bin/python
R=experiments/releases
E=experiments/ensembles
V10=$R/20261022_v10_baseline/agent_p0.pth
GAMES=${GAMES:-1500}
PAR=${PAR:-12}
MIX="solution92=0.30,sol92_sq=0.25,sol92_weak=0.10,pool=0.25,rush=0.05,default=0.05"
POOL="$V10 $R/20261020_old3_sym3/agent_p0.pth $E/battle_mix36.pth $R/20261022_all18_v3/agent_p0.pth $R/20261022_v7_Bsnpd/agent_p0.pth"
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }
# Screens brauchen die V10-Basis gegen die zurueckgehaltenen Gegner (pipeline_battle_morning.sh)
wait_hold() { until grep -q "V10-Basis gegen zurueckgehaltene" experiments/battle_dev.log 2>/dev/null; do sleep 60; done; }
# Quellnetze in der Reihenfolge von v10nets12, Seed 10 + Index
SOURCES=$($PY -c "
import torch
ck = torch.load('$E/v10nets12.pth', map_location='cpu', weights_only=True)
for i, s in enumerate(ck['ensemble_sources']):
    print(10 + i, s.rsplit('/weights/', 1)[0])
")
until grep -q "Ende Runde 3" experiments/pipeline_battle_ft3.log 2>/dev/null; do sleep 60; done
log "Start v8-Linie: $(echo "$SOURCES" | wc -l | tr -d ' ') Netze, $GAMES Spiele, $PAR parallel, Kartenversatz 3000, Mix $MIX, Pool $POOL"
( wait_hold; WORKERS=6 bash scripts/battle_screen.sh mix36b $E/battle_mix36b.pth > /dev/null ) &
run_v8() {
    seed=$1; init=$2
    name=20261030_ftv8_v10_s$seed
    if grep -q '"status": "done"' experiments/runs/$name/manifest.json 2>/dev/null; then return 0; fi
    nice -n 5 $PY -m scripts.finetune --init "$init" --name $name --games $GAMES --seed $seed --map-offset 3000 \
        --variant full_rules_v10 --keep-final --val-every 500 --n-val 8 --no-test --prefill-games 0 \
        --mix "$MIX" --pool $POOL > experiments/batch_20261030_ftv8_$seed.log 2>&1
    echo "[$(date '+%d.%m. %H:%M')] s$seed fertig (exit $?): $(tail -1 experiments/batch_20261030_ftv8_$seed.log)" >> $LOG
}
export -f run_v8
export PY GAMES MIX POOL LOG
echo "$SOURCES" | xargs -P $PAR -L 1 bash -c 'run_v8 "$0" "$1"'
W=""
for seed in $(echo "$SOURCES" | cut -d' ' -f1); do
    f=experiments/runs/20261030_ftv8_v10_s$seed/weights/agent.pth
    [ -f $f ] && W="$W $f"
done
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_ftv8_12.pth $W >> $LOG 2>&1
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mix30v8.pth $V10 $E/battle_ftv8_12.pth >> $LOG 2>&1
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mix48.pth $V10 $E/battle_ft2_18.pth $E/battle_ftv8_12.pth >> $LOG 2>&1
log "Ende v8-Linie: ftv8_12 $(shasum -a 256 $E/battle_ftv8_12.pth | cut -c1-16)"
wait_hold
WORKERS=6 bash scripts/battle_screen.sh mix30v8 $E/battle_mix30v8.pth > /dev/null
WORKERS=6 bash scripts/battle_screen.sh mix48 $E/battle_mix48.pth > /dev/null
wait
log "v8-Screens fertig"
