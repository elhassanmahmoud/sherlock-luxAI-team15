#!/bin/bash
# 01.11.2026: gezielte Bestaetigung der Nebel-Korrektur (est_censor + neb_cross) gegen V12 auf frischen Karten mit
# Nebelabzug 25 (Plan docs/superpowers/plans/2026-10-29-battle-push.md, Nachtrag 01.11., 04:45). Die Korrektur
# wirkt nur dort (Dev A: 84 von 87 veraenderten Ergebnissen); auf den uebrigen Karten muss sie gleich spielen.
#   WORKERS=12 bash scripts/battle_neb25.sh v15cx
# Karten: experiments/analysis/neb25_20261101/seeds_n25.json (die ersten 300 Karten mit Abzug 25 aus 816000-819999)
# und seeds_rest.json (die ersten 60 uebrigen). Huerden siehe Python-Block unten.
cd "$(dirname "$0")/.."
NAME=${1:?Kandidat fehlt, z. B. v15cx}
PY=.venv/bin/python
D=experiments/compare/battle
E=experiments/ensembles
R=experiments/releases
A=experiments/analysis/neb25_20261101
GLOG=experiments/pipeline_battle_gate.log
W=${WORKERS:-12}
REFW=$E/battle_v12.pth
CAND=$E/battle_$NAME.pth
[ -f $CAND ] || { echo "fehlt: $CAND"; exit 1; }
RL="self:$R/20261022_all18_v3/agent_p0.pth,self:$R/20261022_v7_Bsnpd/agent_p0.pth"
HOLD="self:$E/league_nets6.pth,self:$E/threat6.pth"
SIXO="solution92,sol92_sq,$RL,$HOLD"
run() {  # run GEWICHTE SEEDLISTE GEGNER AUSGABE
    [ -f "$4" ] && return 0
    $PY -m scripts.par_eval --weights "$1" --seed-list "$2" --workers $W --opponents "$3" --out "$4" \
        2>&1 | grep -v geladen | tail -1 >> $GLOG
}
echo "[$(date '+%d.%m. %H:%M')] Nebel-25-Bestaetigung: Start $NAME ($CAND, SHA-256 $(shasum -a 256 $CAND | cut -c1-16))," \
    "Referenz V12 ($(shasum -a 256 $REFW | cut -c1-16)), Karten $A/seeds_n25.json und seeds_rest.json," \
    "Code $(git rev-parse --short HEAD)" >> $GLOG
run $REFW $A/seeds_n25.json "$SIXO,default" $D/GN_V12_n25.csv
run $CAND $A/seeds_n25.json "$SIXO,default" $D/GN_${NAME}_n25.csv
run $CAND $A/seeds_n25.json "self:$REFW" $D/GN_${NAME}_n25dir.csv
run $REFW $A/seeds_rest.json "$SIXO" $D/GN_V12_rest.csv
run $CAND $A/seeds_rest.json "$SIXO" $D/GN_${NAME}_rest.csv
$PY - "$NAME" "$REFW" >> $GLOG 2>&1 <<'EOF'
import sys
import pandas as pd
from scripts.compare_report import compare_results
from scripts.league_gates import direct_result, panel_delta
from scripts.screen_table import SIX
name, refw = sys.argv[1], sys.argv[2]
D = "experiments/compare/battle"
c, b = pd.read_csv(f"{D}/GN_{name}_n25.csv"), pd.read_csv(f"{D}/GN_V12_n25.csv")
p = panel_delta(c, b, panel=tuple(SIX))
by = {r["opponent"]: r for r in compare_results(c, b)}
sol, dflt = by["solution92"], by["default"]
d = direct_result(pd.read_csv(f"{D}/GN_{name}_n25dir.csv"), f"self:{refw}")
cr, br = pd.read_csv(f"{D}/GN_{name}_rest.csv"), pd.read_csv(f"{D}/GN_V12_rest.csv")
m = cr.merge(br, on=["seed", "side", "opponent"], suffixes=("_c", "_r"))
same = float((m["result_c"] == m["result_r"]).mean())
pr = panel_delta(cr, br, panel=tuple(SIX))
print(f"Nebel-25-Bestaetigung {name}: Abzug-25-Karten Mittel 6 {p['winrate']:.4f} vs {p['ref_winrate']:.4f} "
      f"(Δ {p['delta'] * 100:+.2f} pp [{p['low'] * 100:+.2f}; {p['high'] * 100:+.2f}], {p['maps']} Karten); "
      f"Solution_92 Δ {sol['delta'] * 100:+.2f} [{sol['low'] * 100:+.2f}; {sol['high'] * 100:+.2f}]; "
      f"default {dflt['winrate']:.4f}; direkt {d['winrate']:.4f} [{d['low']:.4f}; {d['high']:.4f}] aus {d['games']} Spielen; "
      f"uebrige Karten: gleiches Ergebnis in {same * 100:.1f} % von {len(m)} Spielen, Mittel 6 Δ {pr['delta'] * 100:+.2f} pp")
gates = [
    ("Abzug 25: Mittel 6 Δ >= +1 pp", p["delta"] >= 0.01),
    ("Abzug 25: Mittel 6 untere 95%-Grenze > 0", p["low"] > 0),
    ("Abzug 25: Solution_92 Δ >= -0.5 pp", sol["delta"] >= -0.005),
    ("Abzug 25: default >= 99%", dflt["winrate"] >= 0.99),
    ("Abzug 25: direkt gegen V12 >= 50 %", d["winrate"] >= 0.50),
    ("uebrige Karten: >= 98 % gleiche Ergebnisse", same >= 0.98),
    ("uebrige Karten: Mittel 6 Δ >= -0.5 pp", pr["delta"] >= -0.005),
]
for label, ok in gates:
    print(f"  {'OK  ' if ok else 'FAIL'} {label}")
print("GATE Nebel-25-Bestaetigung: " + ("BESTANDEN" if all(ok for _, ok in gates) else "NICHT BESTANDEN"))
EOF
echo "[$(date '+%d.%m. %H:%M')] Nebel-25-Bestaetigung $NAME fertig" >> $GLOG
tail -12 $GLOG
