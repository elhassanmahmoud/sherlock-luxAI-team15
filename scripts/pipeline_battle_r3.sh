#!/bin/bash
# 30.10.2026: Zulassung und Runde 3 nach dem Plan-Nachtrag 30.10., 14:21 (docs/superpowers/plans/2026-10-29-battle-push.md).
# Wartet auf das Ende der Runde 4 der Hauptlinie (scripts/pipeline_battle_ft4.sh), screent mix36d_as und mix54d_as
# auf Dev A gegen die 6 Gegner (scripts/battle_screen.sh) und misst je ein Direktduell gegen V11 auf Dev A.
# Zulassung: Mittel ueber die 6 Gegner >= V11 + 1,0 pp (gepaart gegen mix36c_as = V11 auf denselben Karten) und
# direkt gegen V11 >= 52 % (Punktschaetzungen); bei zweien der mit dem hoeheren Mittel. Danach Runde 3
# (scripts/pipeline_battle_round.sh 3, Referenz V11) fuer den zugelassenen Kandidaten.
#   bash scripts/pipeline_battle_r3.sh        (WORKERS=8 je Screen, beide parallel)
cd "$(dirname "$0")/.."
LOG=experiments/battle_dev.log
PY=.venv/bin/python
E=experiments/ensembles
D=experiments/compare/battle
V11=experiments/releases/20261030_v11_baseline/agent_p0.pth
W=${WORKERS:-8}
until grep -q "Ende Runde 4" experiments/pipeline_battle_ft4.log 2>/dev/null; do sleep 60; done
echo "[$(date '+%d.%m. %H:%M')] Runde-3-Zulassung: Start Screens mix36d_as, mix54d_as (Referenz V11)" >> $LOG
screen_one() {
    n=$1
    WORKERS=$W bash scripts/battle_screen.sh $n $E/battle_$n.pth > /dev/null
    [ -f $D/D_${n}_directv11.csv ] || $PY -m scripts.par_eval --weights $E/battle_$n.pth --first 300000 --n 300 \
        --workers $W --opponents "self:$V11" --out $D/D_${n}_directv11.csv 2>&1 | grep -v geladen | tail -1 >> $LOG
}
screen_one mix36d_as &
screen_one mix54d_as &
wait
chosen=$($PY - <<'EOF' 2>> experiments/battle_dev.log
import pandas as pd
from scripts.league_gates import direct_result
from scripts.screen_table import screen
V11 = "self:experiments/releases/20261030_v11_baseline/agent_p0.pth"
base = screen("mix36c_as")
best = None
with open("experiments/battle_dev.log", "a") as log:
    for n in ("mix36d_as", "mix54d_as"):
        c = screen(n)
        j = c.merge(base, on=["seed", "side", "opponent"], suffixes=("", "_v11"))
        delta = j["result"].mean() - j["result_v11"].mean()
        d = direct_result(pd.read_csv(f"experiments/compare/battle/D_{n}_directv11.csv"), V11)["winrate"]
        ok = delta >= 0.01 and d >= 0.52
        log.write(f"    Zulassung Runde 3: {n} Mittel 6 {j['result'].mean():.4f} vs V11 {j['result_v11'].mean():.4f} "
                  f"(Δ {delta * 100:+.2f} pp), direkt gegen V11 {d:.4f} -> {'zugelassen' if ok else 'nicht zugelassen'}\n")
        if ok and (best is None or delta > best[0]):
            best = (delta, n)
print(best[1] if best else "keine")
EOF
)
echo "[$(date '+%d.%m. %H:%M')] Runde-3-Zulassung: ${chosen:-keine}" >> $LOG
if [ -n "$chosen" ] && [ "$chosen" != "keine" ]; then
    REF=$V11 REFNAME=V11 WORKERS=12 bash scripts/pipeline_battle_round.sh 3 $chosen
fi
