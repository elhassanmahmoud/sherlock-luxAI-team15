# Artillerieregel im Training: vier feste Lernläufe abgeschlossen

08.11.2026. **Technisch vollständig geprüft; noch kein belegter stärkerer V14-Nachfolger.** Der Versuch gleicht genau eine vorhandene Spielregel an das Training an. Alle vier Arme beginnen mit V14-Komponente 18. Innerhalb jedes Startpaars unterscheidet sich ausschließlich `art_splash_in_training`; Regeln, Belohnung, Architektur, Lernbudget und exogener Spielplan sind sonst gleich. Veränderte Aktionen dürfen unterschiedliche Verläufe erzeugen.

Je Arm wurden 40 Vorlaufspiele ohne Gradienten, 400 Lernspiele und 32 separate Diagnoseausführungen gespielt. Insgesamt sind das **1.888 Ausführungen, davon 1.600 Lernspiele, und 240.000 neue Updates**. Jeder Endcheckpoint enthält 60.000 Updates und den erwarteten Umgebungszähler 193.320. Nur die vier vorab festgelegten Endmodelle werden verwendet.

| Arm | Zusätzliche ausgegebene Artillerie-SAPs im Vorlauf | Im Lernen | Finale Solution-Diagnose | Finale default-Diagnose |
|---|---:|---:|---:|---:|
| control43 | 0 | 0 | 6/8 | 8/8 |
| aligned43 | 171 | 1.853 | 8/8 | 8/8 |
| control44 | 0 | 0 | 7/8 | 8/8 |
| aligned44 | 231 | 1.664 | 5/8 | 8/8 |

Die zusätzlichen Befehle wurden nach den nachgelagerten Regeln und bis ins Replay verfolgt; das ist keine garantierte Trefferwirkung. Im Aligned-Vorlauf wurden weitere 23 beziehungsweise 57 zunächst erlaubte SAPs später verworfen. Vor Gradienten bestätigte die Paarprüfung gleiche Startnetze, Optimierer-/RNG-Zustände und Spielpläne; die Kontrollarme geben keine durch den neuen Schalter zusätzlich erlaubten SAPs aus.

Alle anfänglichen Diagnosen lagen bei 7/8 gegen Solution und 8/8 gegen default. Die Enddiagnose ist gemischt: Vorteil im ersten Start, Nachteil im zweiten. Sie benutzt nur vier getrennte Diagnosekarten mit beiden Seiten, keine vollständigen Ensembles. **Keine allgemeine Kausalwirkung, kein V14-Vergleich und keine 100-%-Aussage** daraus ableiten. Die festgelegte separate Auswahl umfasst maximal 440 Spiele; nur ein qualifizierter Kandidat darf anschließend einmalig in 600 frischen Spielen bestätigt werden.

## Tatsächliche Prüfung

- Während aller Läufe unveränderte Quelle `02ce1b2ce9a5b0780da1ee6462a2368b2226d495`; alle vier Worker und der Supervisor endeten mit Exit 0, eigenes Wachhalten beendet.
- Unabhängiger Datenaudit: 1.388.715 Prüfungen, alle Rohdaten-/Zeitplan-/Receiptbindungen und 415 Dateien geprüft, keine ausstehenden Daten. [Bericht](operations/artillery-training-audit.md)
- Unabhängiger Tensor-/Replayaudit: 1.686 Prüfungen; je Arm alle zwölf Q- und zwölf Target-Tensoren verändert/endlich, 152.967 Parameter, zwölf Adam-Zustände mit jeweils 60.000 Schritten, je 300.000 Replayzeilen auf Schema, endliche Werte und Aktions-/Maskenbereiche geprüft. [Bericht](operations/artillery-training-tensor-audit.md)
- Root führte danach auf der ursprünglichen Quelle alle vier unveränderten `validate_final_receipt`-Validatoren und beide Paarprüfungen aus. Erst nach erfolgreicher [Root-Abnahme](operations/root-final-validation.json) wurde der Freeze aufgehoben. [Historische Abnahme](operations/historical_training_acceptance.json), SHA-256 `34395fb96b8245a7cca7088cdb04acdd881dd1c037f9f7c0b688affb093f7712`.

Die vollständigen Vorlaufereignisse sind erhalten. Während der Lernspiele wurden Zähler und Ereignisdigests gespeichert; daraus lässt sich nicht jede einzelne historische Helper-Eingabe erneut rekonstruieren. Technische Vollständigkeit ist kein Nachweis höherer Spielstärke.

## Artefakte und Übergabe

Endnetze und Rohprotokolle liegen unter `experiments/runs/20261108_artillery_alignment_{control43,aligned43,control44,aligned44}/`. Vorbereitete Manifeste/Startnetze stehen in [prepared_v1](prepared_v1/), abgeschlossene Ablaufbelege in [training_v1](training_v1/). Die neuen Netze bleiben experimentell.

Die vier großen `weights/agent.buffer.npz` bleiben bewusst lokal und werden nicht in Git eingecheckt. Für eine vollständige erneute Rohdatenabnahme in Mahmouds Kopie sind diese Dateien separat und mit den Hashes der Abschlussreceipts zu übertragen. Ein Git-Pull allein enthält sie nicht; die Zulassung verwirft fehlende Belege. Die später gebauten Kandidaten können als eigenständige Gewichtsdateien genutzt werden. Die historischen Originalvalidatoren verlangen ihren ursprünglichen Quellenstand; nach einem HEAD-Wechsel dient die gebundene historische Abnahme als Nachweis.

V14-Dateien weiterhin SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; bestehende ZIP `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Keine Abgabe ersetzt.
