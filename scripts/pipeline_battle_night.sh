#!/bin/bash
# 29.10.2026: Nachtablauf nach Runde 2 (Plan docs/superpowers/plans/2026-10-29-battle-push.md, Nachtrag 29.10.).
# 1. wartet auf das Ende von Runde 2 (pipeline_battle_ft2.sh) und startet sofort Runde 3 (pipeline_battle_ft3.sh)
# 2. baut mix36b (V10 + ft2_18) und mix54 (V10 + ft18 + ft2_18), beide mit V10-Config
# 3. Auswahl Runde 1 (802000-802399) fuer das vorab festgelegte Buendel mix36, ft2_18, mix36b, mix54;
#    Wahl hoechstens eines Kandidaten nach scripts/league_gates.py
# 4. Bestaetigung Runde 1 (803000-804399) nur fuer den gewaehlten Kandidaten
# Die Abgabe aendert dieses Skript nicht; Uebernahme nach bestandener Bestaetigung von Hand
# (scripts/release_candidate.py: Sicherung, Installation, Kurs-Runner, Bericht).
#   bash scripts/pipeline_battle_night.sh      (WORKERS=8 neben dem Training)
cd "$(dirname "$0")/.."
PY=.venv/bin/python
LOG=experiments/pipeline_battle_gate.log
E=experiments/ensembles
V10=experiments/releases/20261022_v10_baseline/agent_p0.pth
export WORKERS=${WORKERS:-8}
until grep -q "Ende Runde 2" experiments/pipeline_battle_ft2.log 2>/dev/null; do sleep 60; done
nohup caffeinate -i bash scripts/pipeline_battle_ft3.sh > /dev/null 2>&1 &
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mix36b.pth $V10 $E/battle_ft2_18.pth
$PY -m scripts.build_ensemble --cfg-from $V10 --out $E/battle_mix54.pth $V10 $E/battle_ft18.pth $E/battle_ft2_18.pth
CANDS="mix36 ft2_18 mix36b mix54"
for c in $CANDS; do
    bash scripts/pipeline_battle_gate.sh select 1 $c $E/battle_$c.pth
done
bash scripts/pipeline_battle_gate.sh pick 1 $CANDS
chosen=$(grep "AUSWAHL:" $LOG | tail -1 | awk '{print $2}')
if [ -n "$chosen" ] && [ "$chosen" != "keine" ]; then
    bash scripts/pipeline_battle_gate.sh confirm 1 $chosen $E/battle_$chosen.pth
fi
echo "[$(date '+%d.%m. %H:%M')] Nachtablauf fertig (Wahl: ${chosen:-keine})" >> $LOG
