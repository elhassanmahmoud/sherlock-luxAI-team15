#!/bin/bash
# 30.10.2026: eine Runde nach docs/superpowers/plans/2026-10-29-battle-push.md (Nachtrag 30.10., 04:09):
# Auswahl fuer jeden Kandidaten genau einmal, Wahl hoechstens eines Kandidaten, Bestaetigung nur fuer ihn.
# Kandidaten sind experiments/ensembles/battle_NAME.pth, Referenz ist V10 (pipeline_battle_gate.sh).
# Die Abgabe aendert dieses Skript nicht; Uebernahme nach bestandener Bestaetigung von Hand
# (scripts/release_candidate.py: Sicherung, Installation, Kurs-Runner, Bericht).
#   bash scripts/pipeline_battle_round.sh RUNDE NAME1 [NAME2 NAME3]   (WORKERS=8 neben Training, sonst 12)
cd "$(dirname "$0")/.."
LOG=experiments/pipeline_battle_gate.log
E=experiments/ensembles
ROUND=$1; shift
{ [ $# -ge 1 ] && [ $# -le 3 ]; } || { echo "1 bis 3 Kandidaten"; exit 1; }
for c in "$@"; do [ -f $E/battle_$c.pth ] || { echo "fehlt: $E/battle_$c.pth"; exit 1; }; done
for c in "$@"; do
    bash scripts/pipeline_battle_gate.sh select $ROUND $c $E/battle_$c.pth
done
n=$(wc -l < $LOG)
bash scripts/pipeline_battle_gate.sh pick $ROUND "$@"
chosen=$(tail -n +$((n + 1)) $LOG | grep "AUSWAHL:" | tail -1 | awk '{print $2}')
if [ -n "$chosen" ] && [ "$chosen" != "keine" ]; then
    bash scripts/pipeline_battle_gate.sh confirm $ROUND $chosen $E/battle_$chosen.pth
fi
echo "[$(date '+%d.%m. %H:%M')] Runde $ROUND fertig (Wahl: ${chosen:-keine})" >> $LOG
