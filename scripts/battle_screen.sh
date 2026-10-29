#!/bin/bash
# 29.10.2026: Entwicklungs-Screen eines Ensembles auf Dev A 800000-800299 (Plan docs/superpowers/plans/2026-10-29-battle-push.md,
# Nachtrag 29.10., 23:55). Gegner: Solution_92-Familie (solution92, sol92_sq), fruehere RL-Abgaben (V3, V7),
# zurueckgehaltene RL-Gegner, gegen die nie trainiert wurde (league_nets6 mit V10-Regeln, threat6 mit V3-Regeln),
# und direkt gegen V10. Vergleich gepaart gegen V10 auf denselben Karten (B_V10_dev800, B_V10_rl, B_V10_hold);
# Robustheitsmittel ueber die 6 Gegner ohne Direktduell. Nur Entwicklung, keine Uebernahme.
#   bash scripts/battle_screen.sh NAME GEWICHTE      (WORKERS, Default 6)
#   bash scripts/battle_screen.sh V10                (einmalig: V10-Basis gegen die zurueckgehaltenen Gegner)
cd "$(dirname "$0")/.."
NAME=$1; W=$2
PY=.venv/bin/python
D=experiments/compare/battle
LOG=experiments/battle_dev.log
R=experiments/releases
E=experiments/ensembles
V10=$R/20261022_v10_baseline/agent_p0.pth
RL="self:$R/20261022_all18_v3/agent_p0.pth,self:$R/20261022_v7_Bsnpd/agent_p0.pth"
HOLD="self:$E/league_nets6.pth,self:$E/threat6.pth"
run() {  # run GEWICHTE GEGNER AUSGABE
    [ -f "$3" ] && return 0
    $PY -m scripts.par_eval --weights "$1" --first 300000 --n 300 --workers ${WORKERS:-6} \
        --opponents "$2" --out "$3" 2>&1 | grep -v geladen | tail -1 > /dev/null
}
if [ "$NAME" = V10 ]; then
    run $V10 "$HOLD" $D/B_V10_hold.csv
    echo "[$(date '+%d.%m. %H:%M')] V10-Basis gegen zurueckgehaltene RL-Gegner (league_nets6, threat6), Dev A: $D/B_V10_hold.csv" >> $LOG
    exit 0
fi
[ -f "$W" ] || { echo "Gewichte $W fehlen"; exit 1; }
run $W "solution92,sol92_sq" $D/D_${NAME}.csv
run $W "$RL" $D/D_${NAME}_rl.csv
run $W "$HOLD" $D/D_${NAME}_hold.csv
run $W "self:$V10" $D/D_${NAME}_direct.csv
{
    echo "[$(date '+%d.%m. %H:%M')] Screen $NAME ($W, SHA-256 $(shasum -a 256 $W | cut -c1-16)), Dev A, gepaart gegen V10"
    $PY - $D $NAME <<'EOF'
import sys
import pandas as pd
from scripts.compare_report import compare_results
from scripts.league_gates import direct_result, panel_delta
d, name = sys.argv[1], sys.argv[2]
cand = pd.concat([pd.read_csv(f"{d}/D_{name}{s}.csv") for s in ("", "_rl", "_hold")])
ref = pd.concat([pd.read_csv(f"{d}/{f}.csv") for f in ("B_V10_dev800", "B_V10_rl", "B_V10_hold")])
ref = ref[ref["opponent"].isin(set(cand["opponent"]))]
def label(o):
    return o.split("/")[-2] if o.endswith("agent_p0.pth") else o.split("/")[-1].replace(".pth", "")
for r in compare_results(cand, ref):
    print(f"    {label(r['opponent']):28s} {r['winrate']:.4f} (V10 {r['ref_winrate']:.4f}, "
          f"Δ {r['delta'] * 100:+.2f} [{r['low'] * 100:+.2f}; {r['high'] * 100:+.2f}])")
p = panel_delta(cand, ref, panel=tuple(sorted(set(cand["opponent"]))))
print(f"    Mittel ueber 6 Gegner: {p['winrate']:.4f} (V10 {p['ref_winrate']:.4f}, "
      f"Δ {p['delta'] * 100:+.2f} [{p['low'] * 100:+.2f}; {p['high'] * 100:+.2f}], {p['maps']} Karten)")
r = direct_result(pd.read_csv(f"{d}/D_{name}_direct.csv"))
print(f"    direkt gegen V10: {r['winrate']:.4f} [{r['low']:.4f}; {r['high']:.4f}] aus {r['games']} Spielen")
EOF
} >> $LOG 2>&1
tail -9 $LOG
