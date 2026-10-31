#!/bin/bash
# 31.10.2026: V13-Pruefung nach Plan-Nachtrag 31.10., 18:50 (docs/superpowers/plans/2026-10-29-battle-push.md).
# Referenz V12 = experiments/ensembles/battle_v12.pth (bytegleich mit der Abgabe vom 31.10., 17:07).
#   bash scripts/battle_v13.sh admit NAME1 [NAME2 ...]
#       Dev-A-Screen 800000-800299 gegen die 6 Gegner (V12-Basis einmalig, Dateien D_v12*), je Kandidat
#       experiments/ensembles/battle_NAME.pth dieselben Spiele und direkt gegen V12 (600 Spiele). Zulassung:
#       Mittel ueber 6 Gegner >= +0,5 pp ueber V12, direkt >= 50 %, Solution_92 >= -1,0 pp (Punktschaetzungen);
#       bei mehreren der mit dem hoechsten Mittel. Log experiments/battle_dev.log, Ausgabe: Name oder "keine".
#   bash scripts/battle_v13.sh confirm NAME
#       Battle-Bestaetigung genau eines Kandidaten: V12 und Kandidat auf 812000-812799 gegen die 6 Gegner und
#       default, direkt gegen V12 auf 812800-813199 (800 Spiele). Huerden scripts/league_gates.py battle.
#       Log experiments/pipeline_battle_gate.log. Die Abgabe aendert dieses Skript nicht.
# WORKERS (Default 12) Prozesse je Lauf.
cd "$(dirname "$0")/.."
MODE=$1; shift
PY=.venv/bin/python
D=experiments/compare/battle
E=experiments/ensembles
R=experiments/releases
V12=$E/battle_v12.pth
LOG=experiments/battle_dev.log
GLOG=experiments/pipeline_battle_gate.log
W=${WORKERS:-12}
RL="self:$R/20261022_all18_v3/agent_p0.pth,self:$R/20261022_v7_Bsnpd/agent_p0.pth"
HOLD="self:$E/league_nets6.pth,self:$E/threat6.pth"
[ "$(shasum -a 256 $V12 | cut -c1-16)" = b258dc9927a7094f ] || { echo "V12-Referenz $V12 ist veraendert"; exit 1; }

run() {  # run GEWICHTE FIRST N GEGNER AUSGABE LOG
    [ -f "$5" ] && return 0
    $PY -m scripts.par_eval --weights "$1" --first $2 --n $3 --workers $W --opponents "$4" --out "$5" \
        2>&1 | grep -v geladen | tail -1 >> "$6"
}
screen() {  # screen NAME GEWICHTE: Dateinamen wie scripts/battle_screen.sh, damit scripts/screen_table.screen passt
    run $2 300000 300 "solution92,sol92_sq" $D/D_$1.csv $LOG
    run $2 300000 300 "$RL" $D/D_$1_rl.csv $LOG
    run $2 300000 300 "$HOLD" $D/D_$1_hold.csv $LOG
}

if [ "$MODE" = admit ]; then
    [ $# -ge 1 ] || { echo "mindestens ein Kandidat"; exit 1; }
    for n in "$@"; do [ -f $E/battle_$n.pth ] || { echo "fehlt: $E/battle_$n.pth"; exit 1; }; done
    echo "[$(date '+%d.%m. %H:%M')] V13-Zulassung: Start $* (Referenz V12, Code $(git rev-parse --short HEAD))" >> $LOG
    screen v12 $V12
    for n in "$@"; do
        screen $n $E/battle_$n.pth
        run $E/battle_$n.pth 300000 300 "self:$V12" $D/D_${n}_directv12.csv $LOG
    done
    chosen=$($PY - "$@" <<'EOF' 2>> $LOG
import sys
import pandas as pd
from scripts.compare_report import compare_results
from scripts.league_gates import direct_result, panel_delta
from scripts.screen_table import SIX, screen
V12 = "self:experiments/ensembles/battle_v12.pth"
base = screen("v12")
best = None
with open("experiments/battle_dev.log", "a") as log:
    for n in sys.argv[1:]:
        c = screen(n)
        log.write(f"    Screen {n}, Dev A, gepaart gegen V12:\n")
        sol = None
        for r in compare_results(c, base):
            log.write(f"      {SIX[r['opponent']]:8s} {r['winrate']:.4f} (V12 {r['ref_winrate']:.4f}, "
                      f"Δ {r['delta'] * 100:+.2f} [{r['low'] * 100:+.2f}; {r['high'] * 100:+.2f}])\n")
            if r["opponent"] == "solution92":
                sol = r["delta"]
        p = panel_delta(c, base, panel=tuple(SIX))
        d = direct_result(pd.read_csv(f"experiments/compare/battle/D_{n}_directv12.csv"), V12)
        ok = p["delta"] >= 0.005 and d["winrate"] >= 0.50 and sol >= -0.01
        log.write(f"    Zulassung: {n} Mittel 6 {p['winrate']:.4f} vs V12 {p['ref_winrate']:.4f} "
                  f"(Δ {p['delta'] * 100:+.2f} [{p['low'] * 100:+.2f}; {p['high'] * 100:+.2f}], {p['maps']} Karten), "
                  f"Solution_92 Δ {sol * 100:+.2f}, direkt gegen V12 {d['winrate']:.4f} "
                  f"[{d['low']:.4f}; {d['high']:.4f}] aus {d['games']} Spielen -> "
                  f"{'zugelassen' if ok else 'nicht zugelassen'}\n")
        if ok and (best is None or p["delta"] > best[0]):
            best = (p["delta"], n)
print(best[1] if best else "keine")
EOF
)
    echo "[$(date '+%d.%m. %H:%M')] V13-Zulassung: ${chosen:-keine}" >> $LOG
    echo "${chosen:-keine}"
    exit 0
fi

if [ "$MODE" = confirm ]; then
    NAME=$1
    CAND=$E/battle_$NAME.pth
    [ -n "$NAME" ] && [ -f $CAND ] || { echo "fehlt: $CAND"; exit 1; }
    other=$(ls $D/GD_*_conf.csv 2>/dev/null | grep -v "/GD_V12_conf.csv" | grep -v "/GD_${NAME}_conf.csv")
    [ -n "$other" ] && { echo "Der Block hat schon eine Battle-Bestaetigung: $other"; exit 1; }
    OPP="solution92,sol92_sq,$RL,$HOLD,default"
    echo "[$(date '+%d.%m. %H:%M')] Battle-Bestaetigung: Start $NAME ($CAND, SHA-256 $(shasum -a 256 $CAND | cut -c1-16))," \
        "Referenz V12, Karten ab 812000, direkt ab 812800, Code $(git rev-parse --short HEAD)" >> $GLOG
    run $V12 312000 800 "$OPP" $D/GD_V12_conf.csv $GLOG
    run $CAND 312000 800 "$OPP" $D/GD_${NAME}_conf.csv $GLOG
    run $CAND 312800 400 "self:$V12" $D/GD_${NAME}_confdir.csv $GLOG
    $PY -m scripts.league_gates battle $D/GD_V12_conf.csv $D/GD_${NAME}_conf.csv $D/GD_${NAME}_confdir.csv \
        --direct-opponent "self:$V12" >> $GLOG 2>&1
    echo "[$(date '+%d.%m. %H:%M')] Battle-Bestaetigung $NAME fertig" >> $GLOG
    tail -14 $GLOG
    exit 0
fi
echo "Aufruf: bash scripts/battle_v13.sh admit NAME... | confirm NAME"
exit 1
