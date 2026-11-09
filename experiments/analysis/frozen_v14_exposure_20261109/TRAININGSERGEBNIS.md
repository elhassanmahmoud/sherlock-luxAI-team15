# Training gegen eingefrorenen V14 abgeschlossen

**Technisch abgeschlossen; noch kein Stärkenachweis.** Zwei neue Einzelnetze wurden im bisherigen Ensemble-Verhaltensverfahren trainiert. Nur die Gegnerexposition wurde geändert: Die ursprünglichen Solution-Positionen bleiben, andere Gegner werden durch den festen aktuellen V14 ersetzt. Reward, Features, Regeln und eigenes DDQN bleiben gleich. V14 und ZIP wurden nicht verändert.

| Arm | Vorlauf ohne Updates | Lernspiele | Updates | Solution / V14 insgesamt | Gespeicherte finale Replayzeilen |
| --- | ---: | ---: | ---: | ---: | ---: |
| e48 | 40 | 400 | 60000 | 264 / 176 | 300000 |
| e49 | 40 | 400 | 60000 | 252 / 188 | 300000 |

Dazu vier bekannte Technikspiele: beide historischen ON-Solutionverläufe exakt reproduziert, zwei neue Spiele gegen den eingefrorenen V14 technisch geprüft. Insgesamt884 Spielausführungen und120000 Updates, ohne Neustart oder Ersatzrunde. Die880 Vorlauf-/Lernspiele registrierten3050022 Einheitenübergänge; diese sind keine unabhängigen Spiele. Finale Replays sind Ringpuffer und enthalten nur die jüngsten jeweils300000 Zeilen.

## Tatsächliche Prüfungen

87 gezielte synthetische Tests und unabhängiger Codereview bestanden. Der echte Metadatenvorlauf deckte zwei falsche Annahmen über alte Belegformate auf; korrigiert und separat mit Red/Green geprüft. Keine Spiele wurden dadurch wiederholt. Technikaudit670Checks, gemeinsame Vorlaufprüfung1074Checks, Abschlussaudit5783Checks: tatsächliche Tensoren, Adam, Replays, ursprüngliche Karten/Seiten, alle Gegnerbelege, erhaltene Freigabe und Prozessenden unabhängig geprüft. Root hat zusätzlich die Originalvalidatoren unter der eingefrorenen Trainingsquelle ausgeführt.

Beide q/Targets sind gegenüber dem Ausgangsnetz verändert, am finalen Kopierschritt exakt gleich; sämtliche Adamzustände stehen auf60000. Die35 anderen Netze der eigenen Aktionsauswahl sowie jede frische V14-Gegnerinstanz blieben unverändert. Kein Training am Gegner. Beide ursprünglichen Worker, Owner und Wachhalter sind beendet.

## Herkunft und Grenzen

Trainingsquelle `6839ebd3bd3f2a939aeb07c15bb470a73bfc74c4`. [Root-Abschluss](operations/training-completion.json), [unabhängiger Finalaudit](operations/final-audit.json), [Technikabnahme](operations/technical-acceptance.json), [Vorlauffreigabe](training_v1/release.json).

- e48 Enddatei: `ea551bcad26a460d4da4b6315253140d0c275ffb940a53d93b34249a251f9061`.
- e49 Enddatei: `1ca4030a98ddc2f75c26d026cdfc0fe85f32d71630fd2c29d23218d5f538e4b6`.
- Root-Abschluss: `1b3a4ea33661420c6ee1be9dcd691109e6cd829d2b9b5f5d6c17c25fda230236`.

Die Trainingskarten wurden absichtlich aus dem bisherigen kontrollierten Verfahren wiederverwendet. Historische Kontrollen sind keine neuen unabhängigen Trainingsreplikate; alte vollständige Laufzeitarchive fehlen teilweise. Trainingsabschluss, niedrigere Lernfehler oder einzelne Trainingssiege beweisen keine höhere Spielstärke. Noch kein neues Ensemble ausgewählt oder als Abgabe eingesetzt.

Während der Rechenzeit wurden Vergleichsdateien ausschließlich als externer unausgeführter Textentwurf vorbereitet. Diese ausdrücklich dokumentierte Ausnahme änderte weder Quelle/HEAD noch den laufenden Versuch. Integration und echte Tests erst nach tatsächlichem Root-Abschluss; keine vorweggenommene Vergleichsaufnahme.

## Nächster festgelegter Schritt

Original36 plus beide Endnetze ergeben die geplante EXPOSURE38-Variante. Separate tatsächliche Montage-/Loaderabnahme, danach genau200 reservierte Auswahlspiele gegen Solution, V14 und BEHAVIOR38 gemäß unveränderter Spec. Vier Gates unverändert; Erfolg nominiert nur für eine frische Bestätigung. Keine automatischen Nachschläge oder Übernahme. Die algebraische [Mischungsnotiz](operations/averaging-note.md) und [Residual-Machbarkeit](operations/residual-feasibility-unexecuted.md) sind nur Quellenanalysen, kein weiterer Versuch und kein Leistungsnachweis.
