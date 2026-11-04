# V14-Netzpräferenz auf zwei fest vorgegebenen A2-Zuständen

Die eingefrorenen 36 V14-Netze wurden ohne Gradienten auf den exakt kopierten A2-Merkmalen und Masken ausgewertet. Modell-, Trace- und Ladequellen-Hashes stimmen vorher/nachher; ein CPU-Thread, keine neuen Spiele.

| Fall 866000/player1 | A2-Netz / finale Aktion | V14-Netz auf genau demselben Input | Einordnung |
|---|---|---|---|
| env27, UID3, (5,12), Energie 46, kein Ziel | STAY / STAY | LEFT; Abstand zur zweitbesten Aktion 0,03873; Lehrerregret von STAY 0,04496 | Konkrete Imitationsabweichung beim ersten ausgeführten Unterschied. |
| env35, UID2, bekannter zugewiesener Punkt (19,5), Energie 34 | LEFT / LEFT | LEFT; Abstand zur zweitbesten Aktion 0,57004; Lehrerregret von LEFT0 | Der beobachtete Abgang vom Punkt ist hier **keine** Abweichung von der Lehrer-Netzpräferenz. |

Das zweite Beispiel verhindert, dieses konkrete Verlassen eines Punktes als Beleg für mangelnde Lehrerimitation zu verwenden. Eine reine Bindung an die Lehrerpräferenz würde diesen Einzelfall nicht in Richtung STAY korrigieren. Das beweist zugleich nicht, dass LEFT grundsätzlich falsch ist oder dass V14 als vollständiger Agent den Punkt verlassen hätte: Wissenszustand, Zielzuweisung, Regeln und spätere Spielentwicklung wurden nicht gegenfaktisch ausgeführt.

Die einmalig geprüfte optionale Stelle 866008/player1/env185 wurde ausgelassen: Der einzige aktuelle Halter eines bekannten Punktes ist UID0 auf (1,4), Energie 37, mit Netz und final STAY; dort liegt kein passendes Abgangsbeispiel vor. Keine Suche nach Ersatzstellen.

Vollständige Inputs, Masken, sechs Q-Werte und Hashes: `teacher_on_trace_rows.json`. Wiederholung: `teacher_on_trace_rows.py`.
