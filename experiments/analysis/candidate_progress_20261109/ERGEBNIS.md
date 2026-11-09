# Kandidatenrettung nach Stillstand: V14 bleibt

Die neue Regel zeigt einen kleinen positiven Hinweis, aber keinen qualifizierten Nachfolger. Sie aktiviert das bestehende Rescue-Regelbündel früher, wenn zwölf vollständig beobachtete Übergänge keinen öffentlichen Fortschritt bringen. Alle 36 Netze und Gewichte bleiben identisch.

| Fester Vergleich | Siege | Remis | Niederlagen |
|---|---:|---:|---:|
| V14/OFF gegen Solution | 40 | 0 | 0 |
| Frührettung/ON gegen Solution | 40 | 0 | 0 |
| ON direkt gegen OFF | 22 | 0 | 18 |

Solution: 20 Karten 9948000–9948019, beide Seiten. Direkt: andere 20 Karten 9948100–9948119, beide Seiten. 120 vollständige Spiele, jeweils 303 Schritte, Punktewertung v2; keine Lernupdates. Quellenstand `c023b28bd4369ffc1c32b5347fb8574bdd42c472`.

Die vorab festgelegte Solution-Hürde besteht, die Direkt-Hürde von mindestens 24 tatsächlichen Siegen wird mit 22 verfehlt. Keine Nominierung, Verlängerung oder Übernahme. Direktscore 55 %, deskriptives 95%-Ganzkartenintervall 50–62,5 %. Gepaarter Solution-Unterschied 0 Prozentpunkte; das beobachtete Kontrastintervall 0–0 entsteht durch ausschließlich identische Siege und ist keine Garantie gleicher zukünftiger Leistung. Je 40/40 auf 20 Karten belegt keine allgemeine 100%-Quote. Wiederholte Projektauswahl, keine Korrektur für viele Versuche.

Vorher genau vier bekannte Technikspiele: OFF reproduziert beide archivierten V14-Aktionsfolgen und Resultate exakt. Auf der gezielt ausgewählten Niederlage 9946007/player_0 gewinnt ON 3:0 statt OFF 1:2; Punkte 936:352 statt 739:507, drei frühe Hook-Schritte mit 48 UID-Schritt-Abfragen. Das andere bekannte Spiel 831006/player_1 bleibt unverändert. Diese Wirkungsprobe ist keine unabhängige Stärkeprüfung. Eine Abfrage muss keine finale Aktion verändern; die vollständige native Aktionsfolge ändert sich beim ersten Schlüssel tatsächlich.

49 gezielte synthetische Tests, unabhängiger Code-/Methodenreview, reale Technikprüfung und unabhängige Nachrechnung aller drei CSVs bestanden. Die ursprüngliche Analyse stimmt mit der separaten Nachrechnung überein. Root prüfte vor Quellenfreigabe Aufnahme, Eingaben, Quellen, Schutzdateien und tatsächliches Prozessende. Alle eigenen Modelljobs sind beendet. Eine erste Owner-Vorprüfung lehnte den Mac-Symlink /tmp ab; noch vor jedem Worker/Spiel wurde ausschließlich der Aufruf auf /private/tmp korrigiert. Kein Modellspiel wurde wiederholt.

Der neue Schalter `cand_stall_rescue` bleibt standardmäßig ausgeschaltet. V14-Gewichte, Sicherungen und Gruppe15.zip bleiben unverändert. Evalkopien unter technical_v1 sind ausdrücklich experimentell.

[Plan](../../../docs/superpowers/plans/2026-11-09-candidate-progress-rescue.md) · [Originalanalyse](performance_v1/summary.json) · [Unabhängiger Ergebnisreview](operations/result-review.md) · [Technikreview](operations/technical-review.md) · [Root-Abschluss](operations/closure.json)

Nächste getrennte Lernhypothese: relative Gewichtung des bereits vorhandenen Matchsignals isoliert prüfen. [Quellencheck](operations/match-objective-coverage.md). Matchsiege fehlen dem Reward nicht; ein isolierter Gewichtungsvergleich wurde in den geprüften Quellen nicht gefunden. Keine Wiederholung abgeschlossener Reserveschalter oder dieser Frührettungsvariante.
