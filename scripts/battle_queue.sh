#!/bin/bash
# 29.10.2026: Warteschlange fuer Entwicklungsmessungen (Plan docs/superpowers/plans/2026-10-29-battle-push.md).
# Fuehrt die Zeilen aus experiments/battle_queue.txt der Reihe nach aus; neue Zeilen einfach anhaengen.
# Erledigte Zeilen stehen in experiments/battle_queue.done, Ausgaben in experiments/battle_queue.log.
# Beenden: Datei experiments/battle_queue.stop anlegen (wirkt, sobald die Schlange leer ist).
cd "$(dirname "$0")/.."
Q=experiments/battle_queue.txt; DONE=experiments/battle_queue.done; LOG=experiments/battle_queue.log
touch $Q $DONE
while true; do
    n=$(wc -l < $DONE | tr -d ' ')
    line=$(sed -n "$((n + 1))p" $Q)
    if [ -z "$line" ]; then
        [ -f experiments/battle_queue.stop ] && break
        sleep 20
        continue
    fi
    echo "[$(date '+%d.%m. %H:%M')] START $line" >> $LOG
    bash -c "$line" >> $LOG 2>&1
    echo "[$(date '+%d.%m. %H:%M')] ENDE (exit $?) $line" >> $LOG
    echo "$line" >> $DONE
done
