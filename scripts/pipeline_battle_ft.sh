#!/bin/bash
# 29.10.2026: Nachtraining der 18 V3-Netze unter allen V10-Regeln gegen eine gemischte Liga
# (docs/superpowers/plans/2026-10-29-battle-push.md, Arbeitsweg 2). Je Netz ein eigener Lauf
# experiments/runs/20261029_ft_v10_s<seed>, danach Ensemble ft18 mit exakt der V10-Config.
#   bash scripts/pipeline_battle_ft.sh            (GAMES=1500 PAR=6 per Umgebung aenderbar)
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_battle_ft.log
PY=.venv/bin/python
V10=experiments/releases/20261022_v10_baseline/agent_p0.pth
OLD3=experiments/releases/20261020_old3_sym3/agent_p0.pth
GAMES=${GAMES:-1500}
PAR=${PAR:-6}
MIX="solution92=0.35,sol92_sq=0.25,sol92_weak=0.10,pool=0.20,rush=0.05,default=0.05"
log() { echo "[$(date '+%d.%m. %H:%M')] $*" >> $LOG; }

# Quellnetze in der Reihenfolge des V10-Ensembles, Seed 10 + Index
SOURCES=$($PY -c "
import torch
ck = torch.load('$V10', map_location='cpu', weights_only=True)
for i, s in enumerate(ck['ensemble_sources']):
    print(10 + i, s.rsplit('/weights/', 1)[0])
")
log "Start Nachtraining: $(echo "$SOURCES" | wc -l | tr -d ' ') Netze, $GAMES Spiele, $PAR parallel, Mix $MIX"

run_one() {
    seed=$1; init=$2
    name=20261029_ft_v10_s$seed
    if [ -f experiments/runs/$name/manifest.json ] && grep -q '"status": "done"' experiments/runs/$name/manifest.json; then
        return 0
    fi
    nice -n 5 $PY -m scripts.finetune --init "$init" --name $name --games $GAMES --seed $seed \
        --variant full_rules_v10 --keep-final --val-every 500 --n-val 8 --no-test --prefill-games 0 \
        --mix "$MIX" --pool $V10 $OLD3 > experiments/batch_20261029_ft_$seed.log 2>&1
    echo "[$(date '+%d.%m. %H:%M')] s$seed fertig (exit $?): $(tail -1 experiments/batch_20261029_ft_$seed.log)" >> $LOG
}
export -f run_one
export PY GAMES MIX V10 OLD3 LOG
echo "$SOURCES" | xargs -P $PAR -L 1 bash -c 'run_one "$0" "$1"'

W=""
for seed in $(echo "$SOURCES" | cut -d' ' -f1); do
    f=experiments/runs/20261029_ft_v10_s$seed/weights/agent.pth
    [ -f $f ] && W="$W $f"
done
mkdir -p experiments/ensembles
$PY -m scripts.build_ensemble --out experiments/ensembles/battle_ft18_raw.pth $W >> $LOG 2>&1
$PY -c "
import torch
v10 = torch.load('$V10', map_location='cpu', weights_only=True)
ck = torch.load('experiments/ensembles/battle_ft18_raw.pth', map_location='cpu', weights_only=False)
ck['cfg'] = dict(v10['cfg'])
torch.save(ck, 'experiments/ensembles/battle_ft18.pth')
print('ft18:', 1 + len(ck['ensemble']), 'Netze, V10-Config')
" >> $LOG 2>&1
log "Ende Nachtraining: $(shasum -a 256 experiments/ensembles/battle_ft18.pth | cut -c1-16)"
