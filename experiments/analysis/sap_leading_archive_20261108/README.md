# SAP-Vorhalten: erste öffentliche Archivdiagnose

**Kein neuer Agent und kein Spielstärkenachweis.** Einmalige, rein lesende Analyse von zwölf alten V14-Spielen gegen Solution: sechs ausgewählte Niederlagen auf vier Karten und sechs qualitative Gewinnkontrollen auf drei anderen Karten. Die Geometrie gibt einen Anlass für eine kleine getrennte Einflussprobe; sie belegt weder bessere Schüsse im tatsächlichen Spiel noch mehr Siege.

## Ergebnis

| Auswahlstufe | Schussereignisse |
|---|---:|
| Alle finalen SAP-Befehle | 1.343 |
| Eindeutig sichtbarer Gegner am bisherigen Zentrum | 965 |
| Derselbe sichtbare Gegner direkt im vorherigen Schritt | 620 |
| Genau eine kardinale Bewegung beobachtet | 494 |
| Energiebedingungen erfüllt | 490 |
| Neues Zentrum öffentlich sichtbar, passierbar und in Reichweite | 426 |

Mehrere eigene Einheiten können gleichzeitig auf denselben Gegner schießen. Deshalb entsprechen die 426 Ereignisse **286 eindeutigen Gegner/Schritt-Fällen**. In248 davon ist die nächste Position sichtbar:118 laufen geradeaus weiter,49 bleiben stehen,81 machen einen anderen kardinalen Schritt (einschließlich Umkehr), keine größeren Sprünge.38 Folgepositionen bleiben unbekannt und werden nicht als Stehenbleiben oder Tod gewertet.

Hypothetischer Vergleich nur dieses einzelnen Ziels bei den248 beobachteten Fällen: direktes Zentrum hat Gewicht1, ein Nachbarfeld Gewichtf, sonst0. Bisheriges/neues Zentrum insgesamt: f=0,25:98,75/150,25; f=0,5:148,5/182,5; f=1:248/247. **Das sind aufsummierte geometrische Gewichte, keine Schadenspunkte oder Gewinnraten.** Faktor0 ist nur ein zusätzliches geometrisches Szenario, kein behaupteter Kursparameter. Der öffentliche Streufaktorposterior ist in diesen Archiven nicht gespeichert.

Der Befund ist in den alten Verlustspielen kleiner als in den Gewinnkontrollen: Bei f=0,5 beträgt die geometrische Summe für109 beobachtete eindeutige Fälle69→78, bei139 Kontrollfällen79,5→104,5. Die Gruppen sind nicht repräsentativ oder kausal vergleichbar. Sichtbarkeitsausfälle und Auswahl überlebender/sichtbarer Gegner begrenzen die Prognose; gleiche UID ist kein sicherer Lebensidentitätsnachweis. Sichtbare negative Folgeenergie wird mitgezählt und separat berichtet, nicht nachträglich ausgefiltert. Andere Gegner im Trefferbereich, gegenseitige Reaktionen, gekappter Schaden und spätere Punkte sind hier nicht berücksichtigt.

## Tatsächlich geprüft

- [Plan vor Vollzählung](../../../docs/superpowers/plans/2026-11-08-sap-leading-archive.md), [Datenverfügbarkeit](availability.md), [unabhängiger vollständiger Codereview](code-review.md).
- 27 synthetische Checks durch den Implementierer bestanden, Root hat den gesamten unveränderten Code gelesen. [Ausführungsbeleg und dessen Grenzen](execution.json).
- Root führte die vollständige Zählung genau einmal aus: Exit0, alle12 manifestgebundenen Dateihashes geprüft, pro Trace303 Frames. Null neue Spiele, Tensorloads oder Lernupdates, keine Produktionsänderung.
- [Unabhängige Nachrechnung](result-review.md): alle 15 Zusammenfassungen und Geometriewerte aus den Ereignissen exakt bestätigt, tatsächlicher Exit0. Keine zweite Rohtracezählung.
- [Vollständige Ereignistabelle und alle Nenner](result.json), SHA256 `3f46764a597f13749a146977e5a7fee9611bed89bbb234ca9f93e6cad073016b`.

## Reproduktion und nächster Schritt

Mit dem vorhandenen Projektinterpreter: `python -B scripts/sap_leading_archive.py --root /absoluter/pfad/zum/repo --out /tmp/neue-sap-diagnose.json`. Ausgabe muss neu sein. Das versionierte Werkzeug ist bytegleich zum tatsächlich ausgeführten externen Skript. Selbstprüfung ohne Archive: `--self-test`.

Als nächstes kommt allenfalls eine kleine gepaarte Fortsetzung desselben Spielzustands mit genau einem geänderten SAP-Zentrum infrage. Dabei müssen alle anderen anfänglichen Befehle gleich bleiben und die Erinnerung zum tatsächlich gesendeten Schuss passen. Erst unterschiedliche tatsächliche Folgezustände und Punkte könnten einen Nutzen belegen. Kein weiteres großes Training und keine Änderung an V14 aus dieser Archivdiagnose.
