# Sampled-Target-Pilot

**Stand 08.11.2026: Vier Technikspiele und alle 800 Vorlauf-/Lernausführungen vollständig akzeptiert; 96.000 Updates, noch kein Leistungsresultat.**

[Trainingsbericht, Rohbelege und Grenzen](TRAININGSERGEBNIS.md). Ältere Vorbereitungsnachweise unten sind historisch; die Quellensperre des Trainings wurde erst nach der vollständigen Abnahme aufgehoben. V14 und die Abgabe-ZIP bleiben unverändert. Der vorangegangene [Artillerievergleich](../artillery_comparison_20261108/ERGEBNIS.md) ist abgeschlossen und wird nicht verlängert.

Der Pilot vergleicht das vorhandene Double-DQN-Lernziel mit dem Wert der tatsächlich an die Engine übergebenen Folgeaktion. Beide Arme verwenden dieselbe verzögerte Replayfreigabe. Das ist SARSA-artiges Lernen aus historischen Replayaktionen, kein streng on-policy SARSA. Die normale Aktionswahl, Regeln, Rewards und der produktive Core bleiben erhalten. Nur die kurze experimentlokale Lernmethode entscheidet zwischen den beiden Targets.

## Tatsächlich geprüft

- [Technischen Startfehler vor dem ersten Spiel reproduziert und korrigiert](operations/launcher-fix.md): Mac-Framework-Interpretername; danach125 gemeinsame Tests PASS in3,42s. Fehlgeschlagene Stufe vollständig erhalten, null Spiele/Updates; neue Aufnahme separat und weiterhin vor jeder Frischstudie.
- [Gemeinsamer Abschlusslauf: 123 Tests bestanden](operations/task3-implementation.md), 3,19 Sekunden: bestehende 53 Agenttests und 70 Studien-/Supervisorprüfungen. Feste Spielpläne, vollständige Folgeaktionsbelege, atomare Vorlauf-Freigabe, strikte Aufnahme und kontrolliertes Beenden eigener Prozesse. Nur synthetische Daten; keine echte Lux-Laufzeit oder Spielstärke aus diesem Ergebnis ableiten.
- [Unabhängiger abschließender Code-Review](operations/task3-review.md): PASS_STATIC, keine konkreten Blocker. Root hat Worker und Supervisor zusätzlich vollständig gelesen und die tatsächlichen Datei-/Schutzhashes abgeglichen.
- [53 synthetische Tests bestanden](operations/task12-tests.json), 2,71 Sekunden: bestätigte Folgeaktionslabels, Terminal-/Matchgrenzen, Maskenfälle, Ring-/Bundle-Speicherung und numerische Gleichheit des Kontroll-Lernschritts mit dem Core auf demselben fertigen Batch.
- [Unabhängiger statischer Fixreview](operations/task12-review-fix1.md). Historische UNRUN-Berichte dokumentieren die frühere reine Textvorbereitung; der Root-Testbeleg ist jünger.
- [Methodenreview](operations/method-review.md); vier alte Statusformulierungen anschließend präzisiert, technische Initialisierung auf run_seed45 festgelegt. Keine Aufnahmefreigabe für den noch ungeprüften Studienrunner.
- [Kartenprüfung](operations/seed-audit.md) über acht während des Scans stabile Arbeitskopien. Keine beobachtete Kartennutzung oder Reservierung. Zwölf Treffer in vollständigen SHA256-Feldern sind Zahlenfolgen innerhalb von Hashes, keine Karten. [Root-Entscheidung und Grenzen](operations/seed-audit-acceptance.json), [verlustfreier Rohbericht](operations/seed-audit.raw.json.gz).

[Unabhängige Aufnahmeprüfung](operations/admission-review.md): PASS für Methoden-/Kohorten-/Hashbindungen und installierten Task1/2-Stand. Studienwerkzeuge und reale Läufe bleiben gesondert abzunehmen.

## Vorab begrenzter Umfang

[Feste Methode](../../../docs/superpowers/specs/2026-11-08-sampled-target.md), [Umsetzungsplan](../../../docs/superpowers/plans/2026-11-08-sampled-target.md).

1. Vier technische Spiele auf bekannter Karte4242, beide Modi und Seiten gegen default, keine Gradienten. Vollständig akzeptiert.
2. Zwei Starts45/46, jeweils Kontrolle und Sampled: 40 Vorlauf- und160 Lernspiele je Arm, insgesamt800 Ausführungen und96000 Lernupdates. Vor Gradienten muss je Startpaar vollständige Vorlaufgleichheit und ein tatsächlicher Targetunterschied nachgewiesen sein.
3. Genau400 Leistungsprüfungen der vier finalen Einzelnetze gegen Solution92/sol92_sq und paarweise direkt. Keine V14-Promotion oder automatische Ensemble-/Nachschlagsstudie aus diesem Pilot.

Der feste Maximalumfang beträgt1204 Spielausführungen, getrennt nach Technik, Vorlauf/Lernen und Leistung. Die sechs Kartenlisten und alle Aufnahmebedingungen stehen in der Methode. Fehler/fehlende Labels werden nicht durch STAY, Argmax oder ausgeschlossene Zeilen ersetzt. Der Core definiert Terminalgrenzen; die geerbte nahe Respawn-Heuristik wird dadurch nicht zu einem sicheren Identitätsnachweis. „Ausgeführt“ bedeutet an die Engine übergeben, nicht garantierte physische Wirkung.

Technik und Training sind abgeschlossen; die vier neuen Netze bleiben experimentell. Die feste 400er-Leistungsprüfung folgt nach eigener Werkzeug- und Datenaufnahme. Aktueller Laufstatus im gemeinsamen Arbeitsstand; noch kein bestätigter Stärkegewinn.
