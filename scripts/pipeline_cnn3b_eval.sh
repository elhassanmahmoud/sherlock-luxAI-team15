#!/bin/bash
# 22.10.2026: PPO cnn3b nach docs/superpowers/plans/2026-10-21-threat-features.md (Nachtrag 03:40).
# Staende 50/100/150 auf 503 220-503 419 gegen V3 (T21_v3_3220.csv); bester nach Solution_92 nur bei
# >= +3 pp und default >= 99 % in die frische Bestaetigung 504 820-505 019 (+ direkt 505 020-505 219).
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_cnn3b.log
PY=.venv/bin/python
D=experiments/compare/regeln
P=experiments/ppo/cnn3b
W=${WORKERS:-9}
log() { echo "[$(date +%H:%M)] $*" >> $LOG; }
log "Start PPO-Auswertung cnn3b"
for it in 0050 0100 0150; do
    [ -f $D/T21_cnn3b_${it}_3220.csv ] || $PY -m scripts.par_eval --weights $P/ppo_$it.pth --first 3220 --n 200 \
        --workers $W --out $D/T21_cnn3b_${it}_3220.csv 2>&1 | grep -v geladen >> $LOG
    $PY -m scripts.compare_report --ref $D/T21_v3_3220.csv $D/T21_cnn3b_${it}_3220.csv 2>&1 | grep -E "default |solution92" >> $LOG
done
BEST=$($PY - <<'PY'
import pandas as pd
r = {it: pd.read_csv(f"experiments/compare/regeln/T21_cnn3b_{it}_3220.csv") for it in ("0050", "0100", "0150")}
wr = {it: d[d.opponent == "solution92"].result.mean() for it, d in r.items()}
print(max(wr, key=lambda k: (wr[k], -int(k))))
PY
)
log "bester Stand nach Solution_92: $BEST"
if ! $PY scripts/v5_gates.py selection $D/T21_v3_3220.csv $D/T21_cnn3b_${BEST}_3220.csv >> $LOG; then
    log "Auswahlhuerde verfehlt -> Ende, frische Bloecke unberuehrt"; exit 0
fi
log "Auswahlhuerde bestanden -> frische Bestaetigung"
$PY -m scripts.par_eval --weights experiments/ensembles/all18_v3.pth --first 4820 --n 200 --workers $W \
    --out $D/P22_v3_4820.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $P/ppo_$BEST.pth --first 4820 --n 200 --workers $W \
    --out $D/P22_cnn3b_${BEST}_4820.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.par_eval --weights $P/ppo_$BEST.pth --first 5020 --n 200 --workers $W \
    --opponents self:experiments/ensembles/all18_v3.pth --out $D/P22_cnn3b_${BEST}_direct_5020.csv 2>&1 | grep -v geladen >> $LOG
$PY -m scripts.compare_report --ref $D/P22_v3_4820.csv $D/P22_cnn3b_${BEST}_4820.csv 2>&1 | grep -E "default |solution92" >> $LOG
$PY scripts/v5_gates.py confirm $D/P22_v3_4820.csv $D/P22_cnn3b_${BEST}_4820.csv $D/P22_cnn3b_${BEST}_direct_5020.csv >> $LOG
log "Ende PPO cnn3b"
