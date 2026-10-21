# V4-Zielpilot: Auswahl liefert keine Alternativen

Am 21.10.2026 nach dem [vorab festgelegten Plan](../../../docs/superpowers/plans/2026-10-21-v4-target-pilot.md) beendet. Der laufende V3-Agent und seine Gewichte wurden nicht verändert. Eingefrorener Quellstand: `1255f005255521d8d4a981147fb80064df3e0de4`.

Vier V3-Kontrollspiele und vier passive Wiederholungen gegen Solution_92 auf Karten **524000–524001**, jeweils beide Seiten: **acht vollständige Spiele**. Bei den Wiederholungen wurden insgesamt 32 feste Situationen in Match 2/3 untersucht. Die komplette gespeicherte Aktionsfolge beider Spieler und sämtliche Beobachtungs-Hashes stimmen jeweils mit dem Kontrollspiel überein; ebenso alle Ergebnisfelder außer Laufzeit.

**Ergebnis:** In keiner der 32 Situationen gab es nach der unveränderten Auswahlregel ein geeignetes alternatives Ziel. Daher **0/32 Situationen mit veränderter Aktion**, erforderliches Gate ≥8 nicht erfüllt. Es wurde keine alternative Zielaktion ausgewertet. Dies zeigt eine leere Auswahl unter diesen Bedingungen; es belegt **nicht**, dass Zielmerkmale die Aktion nicht beeinflussen oder dass eine andere Zielzuweisung nutzlos wäre. Die einzelnen Ursachen der leeren Auswahl lassen sich aus den gespeicherten Daten nicht bestimmen.

Der Pilot endet hier: kein Zielbewerter trainiert, kein Simulations-Ranking, keine nachträgliche Lockerung der Filter, keine Nutzung der reservierten Karten 524002–524007. 24 fokussierte Tests und unabhängiger Code- und Datenreview bestanden. Alle acht geschützten Gewichtskopien unverändert. Technische Isolation ist belegt, Spielstärke wurde mit dieser Machbarkeitsprüfung nicht verglichen.

- [Vollständige Ausführungsdaten und Hashes](execution_state.json)
- [Rohdaten und Ergebnis](run_01/result.json)
- [Unabhängiger Datenreview](data_audit.md)
- [Implementierungsreview](review.md)
- `run_01/` enthält Manifest und alle acht Spielprotokolle, zusammen 6.621.523 Bytes.

Die State-Felder wurden nach dem Audit auf abgeschlossen und null verbleibende Spiele gesetzt; die im Audit genannten alten Statusfelder waren Startmetadaten. Historische Quell-Hashes bleiben an den eingefrorenen Commit gebunden, auch wenn später auf dem Arbeitszweig weitergearbeitet wird.

**Für Mahmoud:** Nach dem negativen Paar-Koordinator (396 neue Spiele einschließlich Diagnosen) sind damit insgesamt 404 neue Spiele dieser V4-Arbeit abgeschlossen. Noch kein nachweislich stärkerer V4 und kein neuer trainierter Kandidat. Die neu bereitgestellten originalen CNN3-Checkpoints sind separat verfügbar und per vollständigem SHA-256 geprüft. Ein begrenzter Fortsetzungsversuch wird getrennt vorab festgelegt; er ist kein Ergebnis dieses Zielpiloten.
