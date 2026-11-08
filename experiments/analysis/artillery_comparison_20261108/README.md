# Artillerie-Ensemblevergleich

08.11.2026: **Werkzeuge und Kandidaten geprüft; in diesem Vorabstand noch keine Leistungsspiele.** Tatsächlicher späterer Laufstatus steht in `selection/state.json` und gegebenenfalls `confirmation/state.json`.

| Rolle | Zusammensetzung | SHA-256 |
|---|---|---|
| V14 | 36 ursprüngliche Netze | `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` |
| CONTROL38 | V14 + control43 + control44 | `d7e882c272a4e526eae360c51ef4be020d40a42d963047659aa2817a0a4dc4e2` |
| ALIGNED38 | V14 + aligned43 + aligned44 | `cd422172a56c711cafe75fb9023bde7e7cb8780bc64ff684e93c00435fda4107` |

Alle Netze erhalten dasselbe Gewicht. Beide Kandidaten verwenden die unveränderte effektive V14-Inferenzkonfiguration; die beiden optionalen Trainingsflags sind aus. Der Zugewinn gegenüber V14 wäre gegebenenfalls eine Wirkung des gesamten neuen Ensembles, nicht automatisch ein isolierter Nachweis erfolgreichen Nachtrainings. Zwei Starts erlauben keine allgemeine Kausalaussage zur Artillerieregel.

## Feste Methode

[Spec](../../../docs/superpowers/specs/2026-11-08-artillery-comparison.md), [Plan](../../../docs/superpowers/plans/2026-11-08-artillery-comparison.md), [vor Trainingsresultaten festgelegte Größenbegrenzung](../artillery_alignment_20261108/operations/comparison-sizing.md).

- Auswahl: 440 vollständige Partien, beide Seiten; Solution_92, sol92_sq, default und direkte V14-Duelle. Höchstens ein Nominierter nach festen Schwellen und Rangregeln.
- Nur bei Qualifikation: einmalig 600 frische Partien, lokales Sechserpanel plus default und direkte V14-Duelle. Alle sieben ursprünglichen und drei zusätzlichen Schutzbedingungen müssen erfüllt sein. Ganze Karten bilden die Bootstrap-Einheiten; 20 Kartencluster können kleine echte Unterschiede übersehen. Unklar heißt V14 behalten.
- Kein Nachschlag, keine weiteren Kandidaten, keine nachträgliche Gewichts- oder Mitgliederauswahl. Quellen/HEAD/Modelle/Gegner und alle vier Kartenlisten bleiben über beide Phasen fest.

## Tatsächliche Zulassung

[123 Tests bestanden](operations/tests.json), [unabhängiger Installationsreview](operations/installed-review.md), [reale Kandidatenmontage und Reload](operations/candidate-verification.json), [Kandidatenbeleg](../../candidates/artillery_alignment_20261108/admission.json), [historische Trainingsabnahme](../artillery_alignment_20261108/operations/historical_training_acceptance.json).

[Zielgerichteter Kartenaudit](operations/seed-audit.md) über acht stabile Arbeitskopien: keine beobachtete Nutzung/Reservierung, keine Fehler oder Dateimutationen. Seedlose/uneindeutige Altdaten und nicht zugängliche externe Läufe begrenzen diese Aussage. Rohreport verlustfrei als [gzip](operations/seed-audit.raw.json.gz) archiviert; [Root-Entscheidung](operations/seed-audit-acceptance.json), [gebundene Listenfreigabe](operations/seed_acceptance.json).

Die vollständige historische Zulassung bindet auch die vier großen lokalen Replaypuffer. Diese werden nicht in Git eingecheckt. In einer anderen Kopie sind sie separat mit den dokumentierten Hashes bereitzustellen; fehlende Belege werden nicht still übergangen. Die eigenständigen Kandidatengewichte liegen im versionierten Kandidatenordner. V14 und bestehende Abgabe-ZIP bleiben bis zu einer belegten und technisch geprüften Verbesserung unverändert.
