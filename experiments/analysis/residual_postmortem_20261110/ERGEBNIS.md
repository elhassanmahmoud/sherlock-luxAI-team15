# Warum die letzten Kandidaten V14 nicht schlagen

Stand: 10.11.2026. **Nur Nachanalyse und Planung: null neue Spiele, null Lernupdates, keine geänderten Gewichte.** Bezugsquelle `3c1ba9f`. Alle früheren Studien bleiben geschlossen. Der nächste Versuch ist vorgeschlagen, nicht gestartet.

## Ergebnis und Reichweite

| Fester Vergleich | V14 | R61 | R62 |
|---|---:|---:|---:|
| Gegen Solution, 20 Karten × beide Seiten | 40/40 | 35/40 | 38/40 |
| Direkt gegen V14, 20 andere Karten × beide Seiten | – | 14/40 | 10/40 |

Das sind die bereits geprüften Auswahlspiele des [Residualpilots](../residual_ensemble_20261110/ERGEBNIS.md), keine zusätzlichen Tests. Beide Kandidaten scheitern. 40/40 auf diesem Kartensatz ist keine allgemeine 100-Prozent-Quote. Auch die Direktintervalle bleiben breit; aus diesen Zahlen folgt keine universelle Unfähigkeit der Methode.

## Was wir tatsächlich feststellen können

1. **Kein belegter Lade-, Speicher- oder Nullinitialisierungsfehler.** Acht Nullkorrekturkontrollen reproduzierten V14 exakt; Training, Tensoren, Speicherung und Auswertung wurden unabhängig geprüft. Zwei neue Korrekturen wurden tatsächlich gelernt. Technische Korrektheit beweist jedoch keine optimale Lernmethode und schließt nicht jeden denkbaren Fehler aus.
2. **Die Korrektur greift breit in knappe Entscheidungen ein.** Je 8.192 nichtterminale Folgezustände aus vier vorhandenen Replaydateien, jeweils mit beiden Endnetzen bewertet: 11,3–13,1 % andere maskierte Vorschläge. Bei geänderten Vorschlägen liegt der Median des ursprünglichen Abstandes zwischen den besten zwei legalen V14-Werten je Stichprobe bei 0,0295–0,0444. Die Korrektur erhöht in diesen Stichproben die Zahl der STAY-Vorschläge und senkt die Zahl der RIGHT-Vorschläge in kanonischen Koordinaten. Das belegt eine Richtungsänderung, nicht deren Ursache oder Schädlichkeit.
3. **Vorschlag ist nicht ausgeführte Aktion.** Die Stichprobe misst M gegenüber M+R vor den nachgelagerten Regeln. Sie beweist nicht, dass jede solche Änderung am Ende ausgeführt wird. Der Sammler speichert tatsächlich ausgeführte Aktionen; das DDQN-Folgeziel wählt weiterhin aus maskierten Rohbewertungen. Diese Abweichung ist eine plausible methodische Schwierigkeit, aber durch diesen Befund nicht als Verlustursache bewiesen. Ein früherer Folgeaktions-Pilot hat bereits eine andere Targetvariante ohne belegten Erfolg geprüft.
4. **Unsere Optimierungs- und Hilfsgrößen treffen das Spielziel nur teilweise.** Das Training verwendet geformte Einheitenbelohnungen mit Punkt-, Energie-, Bewegungs- und Kampfanteilen sowie bereits einem Matchterm. Es ist also falsch zu sagen, Matches würden gar nicht belohnt. Dennoch sind Team-Matchgewinne und geformte lokale Belohnung verschiedene Ziele. Einfach den Matchreward zu erhöhen wurde bereits geprüft; MATCH38 scheiterte in der frischen Bestätigung.
5. **Es gibt konkrete Fälle, in denen Punktemargen das Ergebnis falsch beschreiben.** R62 verliert auf `11011001/player_1` trotz 1.057:840 Gesamtpunkten. R61 verliert auf `11011002/player_0` trotz 1.496:1.433. Auf `11011017/player_0` haben V14, R61 und R62 jeweils 0:0 Gesamtpunkte; V14 gewinnt dennoch 3:0 Matches, beide Kandidaten verlieren 1:2. Die installierte Engine entscheidet einen Matchgleichstand erst nach gesamter verbleibender Teamenergie, dann gegebenenfalls zufällig. Die archivierten Summen enthalten keine terminalen Energieverteilungen: **Welche dieser beiden Stufen die einzelnen Matches entschieden hat, ist noch nicht nachgewiesen.**

### Was die Summen zusätzlich zeigen

Über dieselben 40 Solution-Spiele hat R61 im Mittel 26,275 eigene Punkte weniger und 13,975 Gegnerpunkte mehr. R62 hat 13,5 eigene und 12,475 Gegnerpunkte weniger. Die STAY-Anteile steigen um etwa 0,95 beziehungsweise 1,49 Prozentpunkte, die Stapelanteile um 0,37 beziehungsweise 0,82 Prozentpunkte. Endgültig bekannte Punktefelder unterscheiden sich im Mittel nur um −0,075/−0,025; daraus folgt **nicht**, dass sie gleich früh gefunden wurden. Beide Kandidaten haben hier keine protokollierten ungültigen Aktionen oder Belief-Widersprüche.

`sap_hits` in `scripts/metrics.py` zählt sichtbare Gegner in einem 3×3-Zielbereich, keine bestätigten Engine-Treffer oder Schäden. Mehr davon belegt keine bessere Kampfwirkung. R61 schießt im 0:0-Verlustbeispiel seltener als V14, R62 häufiger; pauschal „zu viele Schüsse verursachen die Verluste“ ist daher nicht belegt.

## Was wir daraus ableiten – und was offen bleibt

Die letzten Kandidaten haben eine bereits starke Policy verändert, ohne dass ihre lokalen Verbesserungen nachweislich die entscheidenden Matchausgänge verbessern. **Welche konkrete Entscheidung welchen Verlust verursacht, kann die vorhandene Protokollierung nicht eindeutig auflösen.** Eine nachträglich erfundene Einzelursache wäre irreführend. Mehr Updates, Netze oder ein weiterer Rewardkoeffizient sind aus diesen Daten nicht begründet.

Frühere Studien stützen diese vorsichtige Richtung:

- Der Aktionsschüler A2 lernte V14 besser nachzuahmen und verbesserte S30 deutlich; direkt gegen V14 blieb er bei 14/40. Nachahmen liefert keine neuen, nachgewiesen besseren Zielentscheidungen.
- Mehr beziehungsweise andere Netze zeigten teilweise kleine Auswahlvorteile, aber keine bestandene Bestätigung. Das widerlegt nicht jedes Ensemble, begründet aber keine erneute blinde Erweiterung.
- Der alte HOLD-Kopf lernte nur einen STAY-Eingriff anhand der nächsten zwölf Schritte. Seine Validierung war zu klein/unsicher; daraus folgt nicht, dass alle Entscheidungen aus simulierten Alternativen nutzlos wären.

## Empfohlener nächster Ansatz

**V14 behalten und nur belegbare bessere Entscheidungen lernen.** In identischen Entwicklungszuständen V14s Vorschlag und eine genau festgelegte Alternative durch die vollständige Regelkette laufen lassen. Beide bis zum aktuellen Matchende fortsetzen. Primäres Label ist die Änderung des tatsächlichen Matchausgangs, einschließlich Gleichstandsauflösung. Punkte nach zwölf Schritten und am Ende sind ergänzende Diagnose.

Zunächst nur ein kleiner Einfluss-/Lernzielpilot mit maximal 32 vollständigen Ausführungen und begrenzten Fortsetzungen, ohne Training. Nur wenn auf mehreren Karten wirklich günstigere Matchausgänge entstehen, einen kleinen öffentlichen Entscheider trainieren, der normalerweise bei V14 bleibt. Eine bessere Alternative im vollständig bekannten Simulator ist zunächst nur eine theoretische Möglichkeit: Das spätere Netz darf ausschließlich zum Entscheidungszeitpunkt verfügbare Informationen erhalten und muss auf getrennten Karten sowie in vollständigen Spielen bestehen.

[Design und Grenzen](../../../docs/superpowers/specs/2026-11-10-match-outcome-selector-design.md) · [Nächster konkreter Plan](../../../docs/superpowers/plans/2026-11-10-match-outcome-selector.md).

Die Idee ist mit dem allgemeinen Prinzip vereinbar, Verbesserungen durch Planung zu finden und anschließend zu lernen; das ist keine Lux-Erfolgsgarantie und keine vollständige Implementierung von [Expert Iteration](https://arxiv.org/abs/1705.08439).

## Reproduktion und Einschränkungen

- `offline_analysis.py.txt` ist die unveränderte tatsächlich ausgeführte Offlineanalyse; `offline_analysis.json` enthält Kennzahlen, Stichprobenindizes als Hash und Eingabehashes. `case_examples.json` enthält Originalzeilen und den gebundenen Engine-Ausschnitt. `METHOD_REVIEW.md` ist eine unabhängige historische Methodenprüfung, keine zusätzliche Datenreplikation.
- Vier Replaydateien × 8.192 Zeilen, beide Korrekturen auf denselben Zeilen: 32.768 gezogene Zeilen bzw. 65.536 Bewertungen. Keine Behauptung unabhängiger Zustände: Vorlauf und Endpuffer können sich überschneiden, Zeilen innerhalb einer Partie sind korreliert und stammen aus Training.
- Die gespeicherte Maske gehört zum Folgezustand. Ausschließlich `ns/base_ns` wurden damit verglichen; kein falsches Maskieren von `s`. Keine Zielqualität aus den Rohvorschlägen abgeleitet.
- Ausgabe des archivierten Skripts ist `/private/tmp/residual-postmortem-20261110.json`. Reproduktion aus der Studienwurzel mit dem vorhandenen Projekt-Python, `PYTHONPATH=.` und einem BLAS-/Torch-Thread; große Replaydateien liegen lokal in beiden Arbeitskopien und sind nicht in Git. Eine Kopie allein aus Git reicht dafür nicht.
- Alle neun gebundenen Eingabedateien nach Ausführung erneut gehasht; Gewichte/Replaybytes unverändert. Keine neue Testsuite für reine Dokumentation gestartet.
