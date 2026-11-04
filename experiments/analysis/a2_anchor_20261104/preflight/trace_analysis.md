# A2: unabhängige Prüfung der bekannten Niederlagenfälle

**Integrität bestanden:** zwölf Fälle, je ein normaler und ein beobachteter Lauf, zusammen 24 Ausführungen. 48,218 Prüfungen: je 303 tatsächlich ausgeführte Schritte und drei Matches; vollständige Aktionsarrays beider Spieler, unabhängig rekonstruierte Schritt-/Gesamtdigests, Ergebnisse und Matchdaten zwischen normal/beobachtet exakt. Sechs Ergebnisfelder direkt gegen die ursprünglichen CSV-Zeilen geprüft. Alle 52 Quellen-/Eingabe-/Abgabe-/Interpreter-Pins mit den tatsächlichen Dateien abgeglichen und unverändert. Keine neuen Spiele, Modelle, Trainings oder Tests.

Punkte stehen jeweils aus Sicht der untersuchten Rolle. Zeiten sind nullbasierte `env_step`; Koordinaten und Richtungen in Beispielen sind kanonisch. Match 2 beginnt bei 101, Match 3 bei 202.

| Fall | Match 1 | Match 2 | Match 3 | Matches gewonnen | Erste bekannte Punkte / erstes Punkten (env) |
|---|---:|---:|---:|---:|---:|
| A2 866000 0 | 182:125 | 21:616 | 650:48 | 2:1 | 37 / 36 |
| A2 866000 1 | 56:269 | 10:598 | 100:323 | 0:3 | 35 / 34 |
| A2 866008 0 | 341:135 | 427:342 | 338:383 | 2:1 | 38 / 33 |
| A2 866008 1 | 364:102 | 348:385 | 300:460 | 1:2 | 36 / 35 |
| V14 866000 0 | 149:105 | 36:537 | 735:42 | 2:1 | 35 / 34 |
| V14 866000 1 | 275:75 | 71:445 | 132:210 | 1:2 | 42 / 41 |
| V14 866008 0 | 366:135 | 394:413 | 344:360 | 1:2 | 35 / 32 |
| V14 866008 1 | 316:142 | 389:377 | 288:370 | 2:1 | 36 / 35 |
| A2 866101 0 | 348:379 | 496:496 | 475:480 | 0:3 | 21 / 20 |
| A2 866101 1 | 348:379 | 496:496 | 475:480 | 0:3 | 21 / 20 |
| A2 866102 0 | 68:194 | 374:210 | 705:799 | 1:2 | 45 / 44 |
| A2 866102 1 | 68:194 | 374:210 | 705:799 | 1:2 | 45 / 44 |

## Konkrete Beobachtungen

**Frühe Präferenzdifferenz wird zunächst übersteuert.** 866000 auf beiden Seiten: erste Netzabweichung env4, aber erste finale Aktionsabweichung erst env27. UID1 an env4 auf identischen Merkmalen/Masken: A2 DOWN, V14 RIGHT; beide final RIGHT. An env27 UID3 in (5,12), Energie46, kein zugewiesenes Ziel: A2 STAY, V14 LEFT; beide ohne beobachteten Override. 866008/player1 divergiert final env26 (UID8 DOWN vs RIGHT).

**866000/player1: Entdeckung gelingt, anschließend bricht das Halten ein.** A2 sieht erste bekannte Punkte env35 statt V14 env42 und erzielt erste Punkte env34 statt env41. Dennoch Match 1 56:269 statt V14 275:75. A2 env65 noch44:22 und zwei besetzte bekannte Punkte; env75 54:55 und null, env85 56:113 und null, env95 56:213 und null. Match 2 nur10:598 (V14 71:445); Wissen12 statt16 bekannte Punkte am Ende. Keine reine Entdeckungsverzögerung.

**Konkretes Netzverhalten plus Energieverlust, keine identifizierte Regelursache.** A2/866000/player1 env35: UID2 allein am bekannten zugewiesenen Punkt(19,5), Energie34, Netz und final LEFT ohne Override; env36(18,5), positive Energie35 und keine bekannte Punktbelegung. env53 halten UID2/4 die bekannten Punkte(18,4)/(19,5) mit Energie0; env54 beide−10, nicht mehr nichtnegativ wertbar. Damit sind Verlassen und anschließender Energieverlust konkret sichtbar; genaue Schadensquelle und Beitrag zum Spielausgang sind nicht kausal isoliert.

**866008/player1: Gesamtpunkte verbergen die verlorenen Matches.** A2 1012:947 Gesamtpunkte, aber1:2 Matches; V14 993:889 und2:1. A2 Match 2 348:385, V14 389:377. Beide kennen10 Punkte und starten in Match 2 bei Schritt7, Match 3 bei Schritt5 mit dem Punkten. A2 env185 301:334 bei nur einem bekannten besetzten Punkt; V14 297:336 bei fünf. Bis env200 steht A2 344:377 mit zwei besetzten Punkten, V14 380:370 mit fünf. Match 2 zeigt eine bessere späte Besetzung/Rückkehr bei V14, keine spätere erste Entdeckung bei A2. Match 3 verlieren beide.

**Kein universeller A2-Nachteil auf derselben Karte.** 866008/player0: A2 gewinnt2:1 (341:135,427:342,338:383), V14 verliert1:2 (366:135,394:413,344:360). A2 gewinnt hier gerade das zweite Match, das V14 verliert. Diese Gegenbeobachtung verhindert eine pauschale Kausalbehauptung über A2.

**Direktduelle: schmale Verluste und Match-Tiebreak statt allgemeiner Kollaps.** 866101 auf beiden Seiten:348:379,496:496,475:480, Gesamt0:3. Match 3 nur−5, Match 2 punktgleich und laut aufgezeichneten Wins V14 zugesprochen. Engine nutzt bei Punktgleichstand Gesamtenergie, danach Zufall; die konkrete terminale Energie beider Teams ist nicht vollständig erfasst, daher keine Wahl zwischen diesen beiden Gründen. 866102:68:194,374:210,705:799, Gesamt1:2; Match 1 erste Punkte für beide Schritt44, A2 nur sechs bekannte Punkte am Ende, Match 3 schon23. Beide Seiten liefern hier gleiche kanonische Zahlen, keine zusätzlichen unabhängigen Karten.

## Reichweite und Grenzen

Die erste tatsächliche Aktionsdifferenz auf identischen Features/Masken zeigt, wo sich die beiden Politiken erstmals auseinanderbewegen; sie beweist nicht, dass genau diese Aktion den späteren Verlust verursacht. Spätere Zustände, Zielzuweisungen und gegnerische Reaktionen unterscheiden sich. Finale Abweichungen vom Netz wurden vollständig geprüft; kein bestimmter Regelname wurde nachträglich als Ursache erfunden. Der Aktionspfad enthält mehrere mögliche Eingriffe.

Besetzung zählt vor der Aktion verschiedene **bereits bekannte** Punktkoordinaten mit mindestens einer eigenen Einheit bei Energie≥0. Das sind weder sämtliche wahren Punktfelder noch exakte Punktebeiträge. Negative Energie und aktive→abwesende Ereignisse sind separat im JSON erfasst; Match-Resets ausgeschlossen. Wiederverwendete IDs und möglicher Tod/Respawn im selben Übergang erlauben keine verlässliche Gesamtzahl von Toten oder eine eindeutige Schadensursache. Bei Direktduellen ist nur A2 intern instrumentiert; V14s vollständiger Wissens-/Energiezustand fehlt.

Die Fälle stützen eine Diagnose von Besetzungs-/Halteproblemen, Energieeinbrüchen und teils sehr knappen Matchverlusten. Sie widerlegen eine alleinige Erklärung durch spätes Entdecken und rechtfertigen keine allgemeine Gewinnquotenaussage. Reduzierte Lehrerübereinstimmung im separaten Retentionsaudit bleibt eine beobachtete Präferenzänderung; ob der feste schwache Lehreranker Spielstärke verbessert, muss der vorab festgelegte gepaarte Lernvergleich zeigen.

Reproduzierbare Auswertung: `analyze_traces.py`, anschließend `summarize_trace_analysis.py`; vollständige Zahlen, Beispiele und Prüfnachweise in `trace_analysis.json`.
