#!/bin/bash
# 31.10.2026: Test der Regel end_sap (Restenergie am Matchende) gegen die dann aktuelle Abgabe, nach Plan-Nachtrag
# 31.10., 22:00 (docs/superpowers/plans/2026-10-29-battle-push.md). Wie scripts/battle_v13.sh, aber mit Referenz REF.
#   REF=v13r0 bash scripts/battle_v14.sh admit NAME1 [NAME2 ...]
#       Dev-A-Screen 800000-800299 gegen die 6 Gegner, gepaart gegen die vorhandenen Dateien D_${REF}*.csv
#       (fehlen sie, werden sie erzeugt), direkt gegen REF (600 Spiele). Zulassung wie Nachtrag 18:50:
#       Mittel ueber 6 Gegner >= +0,5 pp, direkt >= 50 %, Solution_92 >= -1,0 pp; bei mehreren das hoechste Mittel.
#   REF=v13r0 bash scripts/battle_v14.sh confirm NAME
#       Battle-Bestaetigung genau eines Kandidaten: REF und Kandidat auf 813200-813999 gegen die 6 Gegner und
#       default, direkt gegen REF auf 814000-814399 (800 Spiele). Huerden scripts/league_gates.py battle.
# Gewichte: experiments/ensembles/battle_${REF}.pth und battle_NAME.pth. WORKERS (Default 12) Prozesse je Lauf.
cd "$(dirname "$0")/.."
MODE=$1; shift
PY=.venv/bin/python
D=experiments/compare/battle
E=experiments/ensembles
R=experiments/releases
REF=${REF:?REF fehlt, z. B. REF=v13r0}
REFW=$E/battle_$REF.pth
LOG=experiments/battle_dev.log
GLOG=experiments/pipeline_battle_gate.log
W=${WORKERS:-12}
RL="self:$R/20261022_all18_v3/agent_p0.pth,self:$R/20261022_v7_Bsnpd/agent_p0.pth"
HOLD="self:$E/league_nets6.pth,self:$E/threat6.pth"
[ -f $REFW ] || { echo "fehlt: $REFW"; exit 1; }

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
    echo "[$(date '+%d.%m. %H:%M')] V14-Zulassung: Start $* (Referenz $REF, SHA-256 $(shasum -a 256 $REFW | cut -c1-16)," \
        "Code $(git rev-parse --short HEAD))" >> $LOG
    screen $REF $REFW
    for n in "$@"; do
        screen $n $E/battle_$n.pth
        run $E/battle_$n.pth 300000 300 "self:$REFW" $D/D_${n}_direct$REF.csv $LOG
    done
    chosen=$($PY - "$REF" "$@" <<'EOF' 2>> $LOG
import sys
import pandas as pd
from scripts.compare_report import compare_results
from scripts.league_gates import direct_result, panel_delta
from scripts.screen_table import SIX, screen
ref = sys.argv[1]
REFP = f"self:experiments/ensembles/battle_{ref}.pth"
base = screen(ref)
best = None
with open("experiments/battle_dev.log", "a") as log:
    for n in sys.argv[2:]:
        c = screen(n)
        log.write(f"    Screen {n}, Dev A, gepaart gegen {ref}:\n")
        sol = None
        for r in compare_results(c, base):
            log.write(f"      {SIX[r['opponent']]:8s} {r['winrate']:.4f} ({ref} {r['ref_winrate']:.4f}, "
                      f"Δ {r['delta'] * 100:+.2f} [{r['low'] * 100:+.2f}; {r['high'] * 100:+.2f}])\n")
            if r["opponent"] == "solution92":
                sol = r["delta"]
        p = panel_delta(c, base, panel=tuple(SIX))
        d = direct_result(pd.read_csv(f"experiments/compare/battle/D_{n}_direct{ref}.csv"), REFP)
        ok = p["delta"] >= 0.005 and d["winrate"] >= 0.50 and sol >= -0.01
        log.write(f"    Zulassung: {n} Mittel 6 {p['winrate']:.4f} vs {ref} {p['ref_winrate']:.4f} "
                  f"(Δ {p['delta'] * 100:+.2f} [{p['low'] * 100:+.2f}; {p['high'] * 100:+.2f}], {p['maps']} Karten), "
                  f"Solution_92 Δ {sol * 100:+.2f}, direkt gegen {ref} {d['winrate']:.4f} "
                  f"[{d['low']:.4f}; {d['high']:.4f}] aus {d['games']} Spielen -> "
                  f"{'zugelassen' if ok else 'nicht zugelassen'}\n")
        if ok and (best is None or p["delta"] > best[0]):
            best = (p["delta"], n)
print(best[1] if best else "keine")
EOF
)
    echo "[$(date '+%d.%m. %H:%M')] V14-Zulassung: ${chosen:-keine}" >> $LOG
    echo "${chosen:-keine}"
    exit 0
fi

if [ "$MODE" = confirm ]; then
    NAME=$1
    CAND=$E/battle_$NAME.pth
    [ -n "$NAME" ] && [ -f $CAND ] || { echo "fehlt: $CAND"; exit 1; }
    other=$(ls $D/GE_*_conf.csv 2>/dev/null | grep -v "/GE_${REF}_conf.csv" | grep -v "/GE_${NAME}_conf.csv")
    [ -n "$other" ] && { echo "Der Block hat schon eine Battle-Bestaetigung: $other"; exit 1; }
    OPP="solution92,sol92_sq,$RL,$HOLD,default"
    echo "[$(date '+%d.%m. %H:%M')] Battle-Bestaetigung: Start $NAME ($CAND, SHA-256 $(shasum -a 256 $CAND | cut -c1-16))," \
        "Referenz $REF ($(shasum -a 256 $REFW | cut -c1-16)), Karten ab 813200, direkt ab 814000," \
        "Code $(git rev-parse --short HEAD)" >> $GLOG
    run $REFW 313200 800 "$OPP" $D/GE_${REF}_conf.csv $GLOG
    run $CAND 313200 800 "$OPP" $D/GE_${NAME}_conf.csv $GLOG
    run $CAND 314000 400 "self:$REFW" $D/GE_${NAME}_confdir.csv $GLOG
    $PY -m scripts.league_gates battle $D/GE_${REF}_conf.csv $D/GE_${NAME}_conf.csv $D/GE_${NAME}_confdir.csv \
        --direct-opponent "self:$REFW" >> $GLOG 2>&1
    echo "[$(date '+%d.%m. %H:%M')] Battle-Bestaetigung $NAME fertig" >> $GLOG
    tail -14 $GLOG
    exit 0
fi
echo "Aufruf: REF=NAME bash scripts/battle_v14.sh admit NAME... | confirm NAME"
exit 1
