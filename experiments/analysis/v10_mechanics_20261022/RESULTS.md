# V10-Mechanikkorrekturen: Ergebnisse und Übergabe

## Status

**Abgeschlossen: kein qualifizierter V10-Nachfolger.** Insgesamt 8.800
Vergleichsspiele sind vollständig ausgewertet: 2.400 zur Auswahl und 6.400 zur
unabhängigen Bestätigung. Die Energie-Korrektur bestätigt ihren kleinen
Auswahlvorsprung nicht. V10 bleibt mit unveränderten Gewichten aktiv; beide
neuen Schalter bleiben aus.

Moayed hat am 22.10. um 16:24 Berlin den Abschluss vor der nächsten Review
beauftragt. Deshalb wird nur die bereits laufende Bestätigung beendet. Es folgen
keine neuen Versuchsreihen und kein Versionswechsel. Diese Begrenzung wurde in
[closing_scope_20261022.json](closing_scope_20261022.json) festgehalten, bevor
die Ergebnisse des Bestätigungskandidaten vorlagen.

## Umsetzung

Die Änderungen betreffen Regeln bei der Aktionswahl und das Kartengedächtnis,
nicht das Training oder die 18 Netze. Beide neuen Schalter sind standardmäßig aus.

| Schalter | Fehler und enge Korrektur | Verbleibende Grenze |
|---|---|---|
| `sap_overkill_recovery` | Bei der Absage weiterer Saps mögliche Energie-Erholung des Gegners berücksichtigen. Die Engine kann einen durch Sap zunächst negativen Gegner durch Feldenergie retten. | Konservative Obergrenze (normalerweise 20) kann zusätzliche unnötige Schüsse verursachen; die bestehende Annahme über die Zielposition wurde nicht geändert. |
| `nebula_infer_drift_safe` | Bei erkannter Terrain-Drift keine alten, verdeckten Nebelpositionen aus der zeitlich älteren Sichtmaske als aktuelles Terrain übernehmen. | Nur erkannte Drift; der vorhandene Drift-Detektor wurde nicht verbessert. Nützliche Inferenz kann auf diesem Schritt ebenfalls entfallen. |

Umsetzung in getrennten Commits `75e71c0` und `9e5206b`; unabhängiges
[Code-Review](code-review.md). Die technische Korrektheit allein beweist keine
höhere Siegquote: Beide Eingriffe verändern auch die strategischen Abwägungen.

## Auswahl: 200 Karten, beide Startseiten

Seeds 610100–610299, jeweils 400 Spiele gegen Solution_92, drei Matches je Spiel.
Keine Gleichstände. Diese Daten dienten der Auswahl, nicht der unabhängigen Bestätigung.

| Variante | Siege / Remis / Niederlagen | Quote | Unterschied zu V10 | Gepaarter 95-%-Bereich |
|---|---:|---:|---:|---:|
| V10 | 363 / 0 / 37 | 90,75 % | — | — |
| Energie-Korrektur | 367 / 0 / 33 | 91,75 % | +1,00 pp | −0,75 bis +3,00 pp |
| Karten-Korrektur | 359 / 0 / 41 | 89,75 % | −1,00 pp | −2,50 bis +0,25 pp |
| Beide Korrekturen | 362 / 0 / 38 | 90,50 % | −0,25 pp | −2,50 bis +2,00 pp |

Nur die Energie-Korrektur erfüllt die vorab festgelegte Auswahlhürde von mindestens
+1 pp. Gegenüber V10 kippen zehn Spiele zugunsten des Kandidaten und sechs gegen
ihn; 384 bleiben beim gleichen Ergebnis. Der Kandidat wurde vor den weiteren
Spielen verbindlich ausgewählt. Gegen default gewinnen anschließend V10 und der
Kandidat jeweils **400/400** auf demselben Auswahlblock. Es gab kein Nachrücken
oder Nachjustieren anderer Varianten.

Belege: [Auswahl](selection_summary.json), [Default-Prüfung](selection_default_summary.json),
[unabhängige Auswahlprüfung](selection-data-review.md),
[unabhängige Freigabe der Bestätigung](default-admission-review.md).

## Unabhängige Bestätigung

800 neue Karten 611000–611799, beide Startseiten, jeweils 1.600 Spiele pro
Variante und Gegner. Zusammen 6.400 Spiele; keine Gleichstände.

| Gegner | V10: Siege / Remis / Niederlagen | Energie-Korrektur: Siege / Remis / Niederlagen | Quoten V10 → Korrektur | Δ und gepaarter 95-%-Bereich |
|---|---:|---:|---:|---:|
| Solution_92 | 1.448 / 0 / 152 | 1.437 / 0 / 163 | 90,50 % → 89,8125 % | −0,6875 pp [−1,50; +0,125] |
| default | 1.599 / 0 / 1 | 1.599 / 0 / 1 | 99,9375 % → 99,9375 % | 0,00 pp [0,00; 0,00] |

**Die Solution-Bedingung ist nicht erfüllt:** Der Vorsprung erreicht weder die
geforderten +2 pp noch eine untere 95-%-Grenze über null. Gegen default sind beide
Bedingungen erfüllt. Der Punktschätzer gegen Solution ist niedriger, das Intervall
umfasst aber null; deshalb nicht als statistisch gesicherte Verschlechterung
bezeichnen. Ein belastbarer Gewinn ist ebenfalls nicht nachgewiesen.

Die Berechnung verwendet 5.000 gepaarte Bootstrap-Ziehungen ganzer Karten
(beide Seiten zusammen), NumPy-Zufallsseed 0 und Perzentile 2,5/97,5. Vorher wurden
exakt alle erwarteten Spielschlüssel, Spielabschlüsse, Ergebnisse, Punktezählung
v2 und Datei-Prüfsummen kontrolliert. Für Schwellenentscheidungen wurden exakte
Halbpunkt-Einheiten verwendet, keine gerundeten Prozentzahlen.

Belege: [vollständige Auswertung](confirmation_summary.json),
[V10-Rohdaten](confirmation_baseline.csv), [Kandidaten-Rohdaten](confirmation_recovery.csv),
[Aufrufe und Abschlussjournal](confirmation_state.json),
[unabhängige Abschlussprüfung](confirmation-data-review.md).


Die ursprünglichen Übernahmebedingungen stehen im
[unverändert archivierten Plan](../../../docs/superpowers/plans/2026-10-22-v10-mechanics.md).
Neben mindestens +2 pp gegen Solution mit unterer 95-%-Grenze über null wären
auch die Default-Bedingungen, ein bestandenes Direktduell gegen V10 sowie der
zusätzliche stärkere Gegner erforderlich. **Direktduell und Robustheitsblock
werden wegen des vorab festgehaltenen Abschlussauftrags nicht mehr gestartet.**
Die reservierten Seeds 612000–612399 und 613000–613099 sind in dieser Studie
unbenutzt. Eine spätere Fortsetzung müsste ausdrücklich neu beauftragt werden.

## Technische Prüfungen

- Regressionen zuerst rot, dann grün; fokussierte Prüfung 33 bestanden.
- Vollständige Suite vor den Messungen: **527 Tests plus 14 Untertests bestanden**,
  siehe [Protokoll](full-suite.log).
- Nach Übernahme von Mahmouds Demo-Änderungen: **sieben zusätzliche Integrationstests bestanden**,
  siehe [Protokoll](integration-demo-tests.log).
- Originalcode gegen erweiterten Code mit beiden Schaltern aus: je vier Spiele,
  insgesamt acht; 1.212 Schritte je Fassung. Sämtliche Aktionen beider Spieler
  und alle Spielmetriken außer Laufzeiten identisch. Siehe
  [Kompatibilitätsentscheidung](compatibility_verdict.json).
- Acht zusätzliche technische Spiele mit beiden Schaltern an durch den
  unveränderten Kurs-Runner bestanden; [Prüfbeleg](course_runner_combined.json).
- Temporärer Prüf-Checkpoint: alle **264 Tensoren** und Nicht-Konfigurationsdaten
  identisch zu V10; nur die zwei Schalter gesetzt. [Prüfbeleg](smoke_checkpoint.json).
- Abgabepaket dieses temporären Checkpoints: „Check ok“;
  [Protokoll](package_check.log). Dieser Checkpoint wurde nicht als Abgabe installiert.

## Quellen, Schutz und Zusammenarbeit

Alle Leistungsmessungen der Auswahl und Bestätigung liefen mit festgehaltenem HEAD
`de2e95d451a22643a3f7351636d3348f7770a1aa`, derselben Python-/Engine-Umgebung,
denselben Gewichten und ausschließlich den im jeweiligen Manifest genannten
zwei Boolean-Schaltern. Der [Quellenstand](source_freeze.json) und die Journale
halten die konkreten Dateien, Prüfsummen, Aufrufe und Rückgabewerte fest.
Jeweils höchstens zwei Evaluations-Worker, kein paralleles Training.
[Abschlussprüfung](source_freeze_end.json): alle 128 festgehaltenen Dateien,
Interpreter und vier geschützten Gewichtsdateien unverändert; sämtliche eigenen
Spielprozesse beendet.

Beide aktiven V10-Dateien und ihre versionierten Kopien unter
`experiments/releases/20261022_v10_baseline/` haben SHA-256:

`03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`

Mahmouds Ergebniscommit `bb7e84b` wurde vor dem Freeze berücksichtigt. Seine
späteren Commits bis `11c62f5` bringen Präsentation und Demo-Werkzeuge, ändern aber
weder Agenten, Gewichte, Gegner noch die hier verwendete Auswertungslogik. Bis
`d252a83` wurden sie während der Messung nur in Moayeds Hauptcheckout übernommen;
die getrennte Mess-Arbeitskopie blieb unverändert.
[Prüfbeleg dieses Zwischenstands](remote_check_20261022T1400.json). Nach Abschluss
der Spiele und der unabhängigen Quellenprüfung wurde auch die Mess-Arbeitskopie
auf `11c62f5` vorgezogen. Dieser Integrationsstand ist nicht der Messstand.

Für eine Reproduktion siehe [README](README.md). Historische Manifeste enthalten
absolute Pfade auf Moayeds Mac; für andere Rechner neue Ausgabepfade verwenden.
Die reservierten Auswahl- und Bestätigungskarten sind nach dieser Arbeit
verbraucht und dürfen nicht erneut als unbekannte Testkarten ausgegeben werden.

## Bedeutung für die Review

V10 ist der weiterhin gültige Vorführ- und Abgabestand. Die Fehlerkorrekturen
sind getrennte, technisch geprüfte Versuchsoptionen. Das Ziel 100 % gegen
Solution_92 wurde durch diese Arbeit nicht erreicht. Auch ein perfekter
endlicher Test wäre keine Garantie für alle Karten. Bei einem künftigen weiteren
Schritt bleiben koordinierte Kämpfe eine begründete Hypothese aus Mahmouds
Verlustanalysen; die Eignung des vorhandenen `tactics.py`-Entwurfs ist durch diese
zwei Korrekturen ausdrücklich nicht validiert.
