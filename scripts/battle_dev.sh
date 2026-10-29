#!/bin/bash
# 29.10.2026: Entwicklungsmessung auf Dev A 800000-800299 (Plan docs/superpowers/plans/2026-10-29-battle-push.md).
#   bash scripts/battle_dev.sh NAME [GEWICHTE] [--set k=v ...]
# OPP (Umgebung): Gegnerliste, Default "solution92,sol92_sq" (schneller Vorab-Test); PANEL=1 = ganzes Panel.
# DEVB=1: Gegenprobe auf Dev B 801000-801299 gegen B_V10_devB.csv (Ausgabe DB_<NAME>.csv).
# Ergebnis experiments/compare/battle/D_<NAME>.csv, Zusammenfassung mit gepaartem Vergleich gegen die
# V10-Basis (B_V10_dev800.csv, gleiche Karten) in experiments/battle_dev.log.
cd "$(dirname "$0")/.."
NAME=$1; shift
W=experiments/releases/20261022_v10_baseline/agent_p0.pth
if [ -n "$1" ] && [ "${1#--}" = "$1" ]; then W=$1; shift; fi
OLD3=self:experiments/releases/20261020_old3_sym3/agent_p0.pth
if [ -n "$PANEL" ]; then OPP="solution92,sol92_sq,sol92_weak,$OLD3,default"; fi
OPP=${OPP:-solution92,sol92_sq}
FIRST=300000; BASE=experiments/compare/battle/B_V10_dev800.csv; OUT=experiments/compare/battle/D_${NAME}.csv
if [ -n "$DEVB" ]; then FIRST=301000; BASE=experiments/compare/battle/B_V10_devB.csv; OUT=experiments/compare/battle/DB_${NAME}.csv; fi
LOG=experiments/battle_dev.log
PY=.venv/bin/python
[ -f $OUT ] && { echo "$OUT existiert schon"; exit 1; }
$PY -m scripts.par_eval --weights $W "$@" --first $FIRST --n 300 --workers ${WORKERS:-8} \
    --opponents "$OPP" --out $OUT 2>&1 | grep -v geladen | tail -1 > /dev/null
{
    echo "[$(date '+%d.%m. %H:%M')] $NAME${DEVB:+ (Dev B)} ($W $*)"
    $PY - "$OUT" "$BASE" <<'EOF'
import sys
import pandas as pd
from scripts.compare_report import compare_results
cand = pd.read_csv(sys.argv[1])
ref = pd.read_csv(sys.argv[2])
ref = ref[ref["opponent"].isin(set(cand["opponent"]))]
for r in compare_results(cand, ref):
    print(f"    {r['opponent'][:28]:28s} {r['winrate']:.4f} (V10 {r['ref_winrate']:.4f}, "
          f"Δ {r['delta'] * 100:+.2f} [{r['low'] * 100:+.2f}; {r['high'] * 100:+.2f}])")
EOF
} >> $LOG 2>&1
tail -4 $LOG
