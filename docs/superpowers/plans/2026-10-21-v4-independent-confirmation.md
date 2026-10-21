# V4 einmalig unabhängig bestätigen – 21.10.2026

Vor neuen Ergebnissen festgelegt um 07:30 Berlin. Moayed verlängerte die autonome Arbeit bis 09:00; keine neuen Agentenregeln und kein Training in diesem Versuch. Remote geprüft: lokales main und origin/main stehen auf ffcc394. Neue Kartenblöcke unten sind nicht in den bisherigen Reservierungen enthalten.

## Frage und bisherige Evidenz

Mahmouds vorhandenes all18_v4 unterscheidet sich durch gespeicherte Inferenzschalter von V3. Auf seinen 400 neuen Karten lag V4 gegen Solution_92 um 2,375 Prozentpunkte vor V3 (gepaartes Intervall [0,125; 4,625]); der bisherige direkte Vergleich 61/120 gegen V3 war nicht eindeutig. V4 wurde deshalb nicht übernommen. Jetzt einmalig ein größerer unabhängiger direkter Vergleich und ein separater neuer Gegnervergleich. Die alten Daten werden nicht mit den neuen zusammengerechnet. Kein Nachlegen weiterer Karten abhängig vom Ergebnis.

Die vorherige Punktfeld-Diagnose rechtfertigt unter dem engen vorab gesetzten Arbeitsfilter keinen Policy-Patch. Ein Filter nur für aktuell sichtbare, blockierte, unbesetzte eigene Punktefelder bleibt eine separate explorative Idee, die hier nicht getestet oder aktiviert wird.

## Fester Umfang

- V3: `experiments/candidates/all18_v3.pth`, SHA-256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`.
- V4: `experiments/candidates/all18_v4.pth`, SHA-256 `3465225733bbbfbf05adc577f7af5f76cb2d886ff2ed895498434fac979ededd`.
- Gespeicherte Configs laden, keine Overrides, train=False, keine Speicherung in Abgabepfade.
- **Direkt:** Karten 510400–510799, V4 gegen V3, beide Seiten: 800 Spiele.
- **Gegnervergleich:** Karten 510800–510999, jeweils V3 und V4 gegen default und Solution_92, beide Seiten: 800 Spiele je Kandidat, 1600 insgesamt.
- Gesamt **2400 Spiele**. Alle drei Läufe unabhängig von Zwischenergebnissen vollständig durchführen; keine Ergebnisabhängigkeit der Reihenfolge oder Stichprobengröße. Höchstens zwei Evaluationsworker insgesamt, numerische Threads jeweils eins.
- Alte Reservierungen 510000–510399 bleiben unbenutzt. Mahmouds nächster Block 503220+ bleibt frei.

## Prüfung und feste Entscheidung

Quellen, Interpreter, Gewichte und HEAD vor/nachher identisch; exakte eindeutige Spielschlüssel, beide Seiten vollständig, 303 Schritte, Punktezählversion 2 und endliche Kennzahlen prüfen. Bekannte Referenzen und abgeschlossene Kursprüfung gelten weiter; vor etwaiger Installation technische Kandidatenprüfung frisch durchführen.

Auswertung ausschließlich ganzer Kartenpaare, jeweils 5000 Bootstrapziehungen mit Seed 0 und Perzentilen 2,5/97,5. Remis zählen 0,5. Keine Unit-Schritte als unabhängige Stichprobe behandeln.

V4 kommt nur zur Übernahme infrage, wenn **alle** Bedingungen auf den neuen Daten erfüllt sind:

1. Solution_92: mittlere Differenz V4 minus V3 positiv und untere Grenze des gepaarten 95%-Kartenintervalls strikt größer null.
2. Default: beobachteter Rückgang höchstens 2 Prozentpunkte.
3. Direkt: untere Grenze des 95%-Kartenintervalls des V4-Scores strikt größer 50%.
4. Technische Prüfungen, Reproduktion und Sicherung der aktuellen V3 vor Austausch bestanden; alte Sicherung old3_sym3 unverändert erhalten.

Die Übernahme ist eine Konjunktion, kein Herausgreifen des besten Ergebnisses. Frühere nicht bestandene Prüfung bleibt dokumentiert. Wiederholte Untersuchung derselben Hypothese begrenzt die Interpretation nomineller Intervalle; nur diese einmalige unabhängige Bestätigung, keine Serie bis zu einem positiven Ergebnis. Kein allgemeiner Turniersieg- oder Überlegenheitsnachweis gegenüber beliebigen Gegnern.

## Zeitgrenze und Übergabe

Bis 08:40 Berlin müssen die Auswertungen fertig sein; andernfalls kontrolliert abbrechen und als unvollständig dokumentieren, keine Übernahme. Mindestens 20 Minuten Reserve für unabhängige Datenprüfung, technische Kontrolle, Dokumentation und Push. Keine Experimente nach 09:00; Morgenbericht zu tatsächlichen Ergebnissen, Commit-IDs, Abgabe/Sicherung und offenen Punkten. Ein nicht eindeutiges Ergebnis lässt V3 unverändert.
