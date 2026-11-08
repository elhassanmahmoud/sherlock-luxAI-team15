# Artillerie im Training: konkreter Unterschied, noch kein Stärkegewinn

Am 08.11.2026 unter Quellenstand `76d01cf08177f85bf0b1fff7c2b007734ca21d3a` vollständig offline ausgeführt. Null neue Spiele, Lernupdates oder Netzberechnungen. V14 und die abgegebene ZIP bleiben unverändert.

| Archivierte Partie | Helper-Aufrufe | Eval nein / Training nein | Eval ja / Training nein | Eval ja / Training ja |
|---|---:|---:|---:|---:|
| 831006, player_1 | 404 | 380 | 24 | 0 |
| 831043, player_0 | 788 | 771 | 0 | 17 |
| Gesamt | 1192 | 1151 | 24 | 17 |

Eval nein / Training ja kam nicht vor. Jeder Aufruf gehört zu einer eigenen Schritt-/Einheit-Kombination. Beide archivierten Partien enthalten je 303 Zeilen, darunter 300 Entscheidungszeilen.

## Was die Diagnose zeigt

Die Spielregel erlaubt in der ersten Partie 24 Artillerieentscheidungen, die derselbe Helper mit `training=True` ablehnt. In der zweiten Partie gibt es keinen Unterschied. Das bestätigt eine konkrete Exposition des bereits bekannten Codeunterschieds: `art_splash` wirkt im Spiel, bleibt im Training aber ausgeschaltet, auch mit `rules_in_training_all=True`. Der Helper selbst liest diesen zweiten Schalter nicht.

Das historische Eval-Verdikt wurde aus dem jeweiligen Event übernommen. Sein damaliger Estimator-Posterior ist nicht gespeichert, deshalb wurde dieses Verdikt ausdrücklich nicht rekonstruiert. Nur die Trainingsvariante wurde auf isoliertem öffentlichem Kontext berechnet; eine Estimator-Abfrage wäre mit Fehler abgebrochen. Ein- und Ausgabedateien sowie unveränderte Zustände wurden geprüft.

## Prüfung und Grenzen

- Root: zwei gezielte Tests bestanden, 2,41 Sekunden. Unabhängiger Code-/Methodenreview PASS.
- Unabhängige Vorprüfung: historischer Helper-Code identisch; gespeicherte Karten/Zuordnungen bleiben während des Zuges stabil; alle 1192 Ereignisse passen zum aufgezeichneten Einheitenkontext.
- Tatsächlicher Lauf beendet mit Status `complete`. Root-Abschlussprüfung bestätigt Quellenstand, Input-/Output-/Gewichtshashes, Zeilenzahlen, vier Verdiktsummen und unveränderte Zustandsfingerprints.
- **Noch offen:** unabhängige Nachberechnung der Trainingsformel über die 1192 Ergebniszeilen. Sie wurde beim tatsächlichen Kontingentende noch vor Beginn gestoppt. Die Vorprüfung und der Code-Review ersetzen diesen Datenabschluss nicht.

Die zwei Spiele sind bekannte, ausgewählte Niederlagen. Diese Häufigkeiten sind keine allgemeine Schätzung. Ein Helper-Verdikt ist keine endgültige Aktion: Aufrufbedingungen und spätere Regeln können die Wirkung verändern. Keine bessere Entscheidung, Belohnung, Lernwirkung oder Siegquote ist damit bewiesen. Keine neuen Gewichte erzeugt oder übernommen.

## Nächster sinnvoller Versuch

Zuerst den offenen kleinen Datenabschluss erledigen. Danach die konkrete Artillerieregel optional auch beim Training anwenden, bei unverändertem Standardverhalten. Vor einem Lernvergleich die gesamte betroffene Aufrufkette prüfen: `art_still` und die übrige Entscheidungslogik unterscheiden sich ebenfalls zwischen Training und Spiel. Nicht pauschal alle Unterschiede gleichzeitig ändern.

Für eine kausal verständliche Prüfung: gleiche Ausgangsnetze, gleiche Trainingskarten und Starts, Kontrolle gegen die eine angeglichene Regel. Erst wenn daraus ein Kandidat entsteht, ein kleiner vorab begrenzter Vergleich gegen V14 und Solution auf anderen Karten. Noch kein solcher Versuch gestartet oder spezifisches Versuchsbudget festgelegt. Mehr Netze oder größere Stimmgewichte allein haben bisher keinen abgesicherten Nachfolger geliefert.
