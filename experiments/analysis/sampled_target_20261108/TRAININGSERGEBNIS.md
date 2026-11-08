# Folgeaktions-Lernvergleich: Training abgeschlossen

**Vier vollständige Lernarme technisch und unabhängig akzeptiert; noch kein Leistungsresultat. V14 und die Abgabe-ZIP bleiben unverändert.**

Wir vergleichen das bisherige Double-DQN-Lernziel mit dem Wert der tatsächlich eingereichten Folgeaktion. Beide Varianten verwenden dieselbe verzögerte Freigabe gespeicherter Erfahrungen. Es handelt sich um SARSA-artiges Lernen aus historischen Replayaktionen, nicht um streng on-policy SARSA. Aktionswahl, Regeln, Rewards und produktiver Agent wurden nicht geändert.

## Tatsächlicher Umfang

| Arm | Vorlauf ohne Lernen | Lernspiele | Updates | Gespeicherte Übergänge insgesamt |
|---|---:|---:|---:|---:|
| control45 | 40 | 160 | 24.000 | 718,884 |
| sampled45 | 40 | 160 | 24.000 | 723,204 |
| control46 | 40 | 160 | 24.000 | 713,114 |
| sampled46 | 40 | 160 | 24.000 | 716,119 |

Insgesamt **800 Spielausführungen = 160 Vorlauf + 640 Lernen**, 96.000 Updates und 242.400 tatsächlich ausgeführte Umgebungsschritte. Endzähler pro Arm: 120.600, einschließlich des vorgegebenen Anfangszählers 60.000. Jeweils nur die letzten 300.000 Replayzeilen bleiben im Ring erhalten; die vollständigen Capture-/Commitbelege aller 2.871.321 Übergänge sind archiviert.

Zusätzlich vier bekannte technische Spiele auf Karte 4242, beide Modi und beide Seiten, null Gradienten. Der frühere macOS-Startfehler endete vor Modellkonstruktion: null Spiele und null Updates; Ursache, Regression und gesonderter Neustartentscheid bleiben separat dokumentiert.

## Vergleichbare Ausgangsbedingungen

Je Start 45/46 waren die kompletten Vorläufe in tatsächlichen Aktionen, Erfahrungen, Trajektorien und aufgezeichneten Zufallszustands-Fingerprints gleich. Anfangsnetze, Targets und frischer Adam blieben währenddessen unverändert. Start 45 hatte 144.531 Vorlaufzeilen, Start 46 hatte 143.955.

Die unabhängige Offline-Nachrechnung bestätigt tatsächlich verschiedene Lernziele auf 16.863 beziehungsweise 17.733 nichtterminalen Vorlaufzeilen. Das belegt die Intervention, **keine bessere Qualität**. Alle vier Endnetze unterscheiden sich von ihren Anfangsnetzen; jeder Adam-Parameter erreicht Schritt 24.000, die finalen Targets sind synchronisiert und die Tensoren endlich.

Anfang: jeweils V14-Komponente 18, einzelnes Netz; Lernrate 0,00005, Batch 256, Gamma 0,99, Epsilon 0,05, Replaykapazität 300.000, Zielnetz-Sync alle 500 Updates. Beide Modi eines Starts erhalten dieselbe vorab gebundene Karten-/Seiten-/Gegnerfolge. Gegnerrezeptur: Solution92 60 %, sol92_sq 20 %, default 10 %, rush 10 %; tatsächliche Folgen stehen in den Manifesten. Karten und vollständige Bedingungen: [feste Methode](../../../docs/superpowers/specs/2026-11-08-sampled-target.md).

## Tatsächlich geprüfte Belege

- Quellenstand durch Technik und Training: `945e1938a1fb1fcc87eeaf10b58138a409266581`. Alle vier Original-Abschlussvalidatoren liefen erfolgreich im eigenen eingefrorenen Supervisor. Root hat deren beendeten, hashgebundenen Ausführungsnachweis übernommen und sie nach dem unabhängigen Vollaudit nicht redundant wiederholt. [Originalnachweis](operations/original_training_validation.json).
- [Unabhängiger vollständiger Trainingsaudit](operations/training_independent_audit.json): tatsächlicher Exit 0 / PASS. Alle 800 Spielpläne, Capture-/Folgeaktions-/Commitverknüpfungen, vollständigen Vorlaufpuffer, finalen Ringe, Tensor-/Adamzustände und 500 Eingabebindungen geprüft. Enthält echte deterministische Offline-Forwardberechnungen auf gespeicherten Anfangstensoren, keine zusätzlichen Spiele oder Updates. [Prüfmethode und Grenzen](operations/training-audit-method.md), [Prüfcode](operations/training-audit.py.txt).
- [Historische Root-Abnahme](operations/historical_training_acceptance.json), SHA-256 `dac732d042b700543aeec8e718771660165e5462abfa60d84a0170689ddac458`: tatsächliche Quelldaten, Endmodelle und Prüfungen versiegelt, bevor HEAD oder Werkzeuge verändert werden durften. Alle eigenen Trainingsworker, Supervisor und Wachhalter im Betriebssystem beendet.
- Technik: [tatsächlicher Vier-Spiel-Audit](operations/technical_v2_audit.json). Vor dem realen Training bestanden bereits 125 gezielte synthetische Tests; deren Belege sind von Spielzahlen getrennt.

## Grenzen und Weitergabe

Belegt sind eingereichte Befehle, nicht deren physische Wirkung. Die unveränderte Core-Heuristik für Unit-Lebensgrenzen bleibt eine Einschränkung. Reset-/Result-Hashes können ohne vollständige Enginezustände nicht unabhängig rekonstruiert werden; eingereichte Aktionshashes dagegen schon. Überschriebene frühere Replay-Featurearrays und historische Zwischen-Gradienten sind nicht archiviert. Keine Aussage über Trainingspopulationen aus zwei festen Starts.

Rohbelege, Manifeste, Endgewichte und Audits werden versioniert. Die großen `.npz`-Replaydateien bleiben lokal und sind über den [Dateiindex](operations/local-replay-files.json) mit Größe und Hash gebunden. Mahmoud braucht diese Dateien zusätzlich, um den vollständigen Lernaudit oder die strikte historische Aufnahme auf einem anderen Rechner erneut auszuführen; ein Git-Pull allein reicht dafür nicht. Die vier Endnetze und späteren Inferenzkopien sind separat verfügbar.

Nächster vorab festgelegter Schritt: genau 400 Vergleichsspiele der vier finalen Einzelnetze, jeweils gegen Solution92/sol92_sq sowie Sampled gegen passende Kontrolle. Kein V14-Ersatz direkt aus diesem Methodenpilot. Noch keine Siegquoten oder bestandenen Leistungsgates behauptet.
