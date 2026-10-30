#!/bin/bash
# 30.10.2026: Zulassung nach den Plan-Nachtraegen 30.10., 14:21 und 18:31 (docs/superpowers/plans/2026-10-29-battle-push.md).
# Fuer jeden Kandidaten experiments/ensembles/battle_NAME.pth: Dev-A-Screen gegen die 6 Gegner (scripts/battle_screen.sh)
# und Direktduell gegen V11 auf Dev A, gepaart gegen V11 (= mix36c_as) auf denselben Karten. Zugelassen ist, wer im
# Mittel ueber die 6 Gegner mindestens +1,0 pp ueber V11 liegt und direkt mindestens 52 % gewinnt (Punktschaetzungen);
# bei mehreren der mit dem hoechsten Mittel. Log experiments/battle_dev.log ("Zulassung: ...").
# Mit ROUND=3 oder ROUND=4 startet danach fuer den zugelassenen Kandidaten die Runde gegen V11
# (scripts/pipeline_battle_round.sh, Referenz V11, Bloecke aus scripts/pipeline_battle_gate.sh).
#   bash scripts/battle_admit.sh NAME1 [NAME2 ...]        (WORKERS je Screen, Default 8; Screens nacheinander)
cd "$(dirname "$0")/.."
LOG=experiments/battle_dev.log
PY=.venv/bin/python
E=experiments/ensembles
D=experiments/compare/battle
V11=experiments/releases/20261030_v11_baseline/agent_p0.pth
W=${WORKERS:-8}
[ $# -ge 1 ] || { echo "mindestens ein Kandidat"; exit 1; }
for n in "$@"; do [ -f $E/battle_$n.pth ] || { echo "fehlt: $E/battle_$n.pth"; exit 1; }; done
echo "[$(date '+%d.%m. %H:%M')] Zulassung: Start Screens $* (Referenz V11)" >> $LOG
for n in "$@"; do
    WORKERS=$W bash scripts/battle_screen.sh $n $E/battle_$n.pth > /dev/null
    [ -f $D/D_${n}_directv11.csv ] || $PY -m scripts.par_eval --weights $E/battle_$n.pth --first 300000 --n 300 \
        --workers $W --opponents "self:$V11" --out $D/D_${n}_directv11.csv 2>&1 | grep -v geladen | tail -1 >> $LOG
done
chosen=$($PY - "$@" <<'EOF' 2>> experiments/battle_dev.log
import sys
import pandas as pd
from scripts.league_gates import direct_result
from scripts.screen_table import screen
V11 = "self:experiments/releases/20261030_v11_baseline/agent_p0.pth"
base = screen("mix36c_as")
best = None
with open("experiments/battle_dev.log", "a") as log:
    for n in sys.argv[1:]:
        c = screen(n)
        j = c.merge(base, on=["seed", "side", "opponent"], suffixes=("", "_v11"))
        delta = j["result"].mean() - j["result_v11"].mean()
        d = direct_result(pd.read_csv(f"experiments/compare/battle/D_{n}_directv11.csv"), V11)["winrate"]
        ok = delta >= 0.01 and d >= 0.52
        log.write(f"    Zulassung: {n} Mittel 6 {j['result'].mean():.4f} vs V11 {j['result_v11'].mean():.4f} "
                  f"(Δ {delta * 100:+.2f} pp, {len(j)} Spiele), direkt gegen V11 {d:.4f} -> "
                  f"{'zugelassen' if ok else 'nicht zugelassen'}\n")
        if ok and (best is None or delta > best[0]):
            best = (delta, n)
print(best[1] if best else "keine")
EOF
)
echo "[$(date '+%d.%m. %H:%M')] Zulassung: ${chosen:-keine}" >> $LOG
echo "${chosen:-keine}"
if [ -n "$ROUND" ] && [ -n "$chosen" ] && [ "$chosen" != "keine" ]; then
    REF=$V11 REFNAME=V11 WORKERS=${GATE_WORKERS:-12} bash scripts/pipeline_battle_round.sh $ROUND $chosen
fi
