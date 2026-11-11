# Gezielte Feldtests: Offlinephase geschlossen, V14 bleibt

**11.11.2026 – vier geeignete Spielschlüssel statt der vorab geforderten sechs.** Vier verschiedene Karten, zwei Verlust- und zwei Kontrollspiele. Die Karten- und Gruppenbedingungen sind erfüllt, die Mindestmenge nicht. Keine Phase B/C/D, keine neue Spielausführung, kein Modell geladen, kein Lernupdate und kein V14-/ZIP-Tausch.

## Was umgesetzt und tatsächlich ausgeführt wurde

- Öffentliche Punktgleichungen aus zwölf vorhandenen Traces rekonstruieren, ausschließlich ab Schritt 50 im ersten Match. Aktuelle Belegung mit Energie mindestens null, Stapel einmal zählen. Unbekannt ist nicht gleich Nullfeld.
- Maximal vier Nicht-Halter berücksichtigen, maximal zwei STAY-/MOVE-Vorschläge gemeinsam verändern; Sicht, Bewegungskosten, Nebel, sichtbare Gegner und originale Aktionsmasken beachten. Maximal 113 Belegungsentwürfe; keine geänderten Netze, Rewards oder produktiven Agentenquellen.
- Den ersten gültigen Vorschlag pro Spiel im festen Fenster 50–80 aufnehmen. Nur öffentliche Daten verwenden; `posthoc` und zukünftige Frames stehen dem Entscheider nicht zur Verfügung.
- Alle zwölf Traces enthalten je 303 historische Frames. Tatsächlich 302 Entscheidungsframes untersucht; nach erster Gelegenheit wurde die Suche im jeweiligen Spiel beendet. Das sind keine 302 neuen Engine-Schritte. Die vollständigen 372 Fensterframes waren verfügbar.

Quelle des Werkzeugs: Commit `c2fa026`. [Originaler Plan](../../../docs/superpowers/plans/2026-11-11-information-probing.md), [feste Bedingungen](../../../docs/superpowers/specs/2026-11-11-information-probing-design.md), [vollständige Auswertung einschließlich Eingabebindungen](offline/audit.json), [Root-Abnahme](ROOT_ABNAHME.json).

## Die vier ersten Gelegenheiten

Koordinaten und Aktionsnummern sind kanonisch, nicht die Weltkoordinaten von Player 1. 0=STAY, 1=UP, 2=RIGHT, 3=DOWN, 4=LEFT.

| Seed / Seite | Gruppe | Schritt | Zu klärendes Feld | Geänderte Vorschläge |
|---|---|---:|---|---|
| 831006 / player_1 | Verlust | 58 | (16, 2) | UID 8→0; UID 14→3 |
| 831042 / player_0 | Verlust | 65 | (3, 7) | UID 7→0 |
| 831000 / player_1 | Kontrolle | 70 | (16, 3) | UID 9→4; UID 14→1 |
| 831002 / player_1 | Kontrolle | 57 | (11, 0) | UID 4→2 |

In allen vier Fällen bleibt in der geplanten neuen Gleichung genau ein unbekanntes Feld übrig; die zum Vergleich benutzte alte Gleichung normalisiert sich auf keine unbekannten Felder/Rest null. Zwei Vorschläge benötigen eine, zwei benötigen zwei geänderte Einheitenaktionen. Es wurden keine Alternativzüge in der Engine ausgeführt. Ob die nachgelagerten Regeln den Vorschlag erhalten, eine tatsächliche Informationsverbesserung entsteht oder ein Spiel gewonnen wird, ist ausdrücklich **nicht gemessen**.

Acht Schlüssel ohne Gelegenheit: 831029/p0, 831042/p1, 831043/p0 und p1, 831000/p0, 831001/p0 und p1, 831002/p0.

## Warum der begrenzte Ansatz nicht fortgesetzt wird

Die 302 untersuchten Frames verteilen sich nach dem ersten zutreffenden Prüfpfad:

| Klassifikation | Frames |
|---|---:|
| Kein unbekanntes Kandidatenfeld vorhanden | 122 |
| Keine sichere zulässige Alternativaktion im festgelegten Suchraum | 77 |
| Alternativen vorhanden, aber keine zusätzliche eindeutige Feldbestimmung | 99 |
| Erste gültige öffentliche Gelegenheit | 4 |

Diese Zahlen beschreiben den gefilterten Ausschnitt, keine unabhängigen Ursachenanteile oder allgemeine Häufigkeit über Lux-Karten. Keine Widersprüche im tatsächlich geprüften Gleichungsspeicher beobachtet. Der festgelegte Ansatz findet zu selten eine Gelegenheit, um die vorab geplante kleine Prototypprüfung zu rechtfertigen. Das beweist weder, dass aktive Informationsgewinnung grundsätzlich nutzlos ist, noch dass V14 optimal ist. Wir verbreitern nach Sichtung dieses Ergebnisses weder Fenster noch Kartenmenge und senken die Hürde nicht auf vier.

## Prüfungen, Herkunft und Grenzen

- 26 gezielte synthetische Tests bestanden. Vor Implementierung fehlendes Modul/API tatsächlich beobachtet; im unabhängigen Review gefundene gegenseitig widersprüchliche Gleichungen mit zwei fehlschlagenden Regressionstests reproduziert und korrigiert. Paarweise Konsistenzprüfung, kein vollständiger binärer SAT-Solver.
- Eingaben unabhängig geprüft und im Werkzeug gebunden: zwölf Trace-Hashes, 22 historische Repository-Source-Blobs, Engine, beide aktuellen Gewichte, Baseline-CSV und Kartenliste. 156 Vergleiche der historischen instrumentierten/uninstrumentierten Läufe und 84 Vergleiche gegen die tatsächliche historische Baseline stimmen.
- Historische Quelle `0c0dda642e9876141a705c2b8ed807a4f26ed870`. Sieben seitdem ergänzte Config-Felder sind explizit `False`; aktuelle Abweichungen an `config.py`, `main.py`, `reward.py` dokumentiert. Das belegt Herkunft und Schema, nicht aktuelle Laufgleichheit. Eine echte AUS-Reproduktion wäre erst Phase B gewesen und wurde nicht ausgeführt.
- Root hat alle zwölf Scans samt vollständigen Entscheidungen und Eingabebindungen erneut aus den Originalbytes nachvollzogen. Dies ist eine Reproduktionsprüfung derselben Offlineauswertung, kein zusätzlicher Versuch oder unabhängiger Leistungstest. Separate unabhängige Prüfung siehe [Datenreview](DATENREVIEW.md).

## Übergabe für Mahmoud

Werkzeug: `scripts/information_probe.py`, Tests: `tests/test_information_probe.py`. Reproduktion erzeugt ausschließlich einen neuen Auswertungsordner und verweigert Überschreiben; abgeschlossene Studie nicht als neue Trainingsrunde starten. Geplante Live-Unterklasse, Engine-Runner und Leistungsprüfung wurden nach dem festen Gate **nicht implementiert**.

V14 hat weiterhin 36 Netze. Beide Abgabegewichte SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; ZIP SHA256 `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Kein eigener Modell-/Wachhalteprozess gestartet; Remote-Automation bleibt pausiert. Ein anderer Ansatz braucht eine getrennte neue Begründung, keine automatische Fortsetzung dieser Studie.
