# V3-Niederlageninventar und empfohlene nächste Beobachtung

Read-only am 21.10.2026; Arbeitsstand laut Koordinator `b008252`. Keine Modelle geladen, Spiele gestartet, Gewichte/Repositorydateien geändert oder Gitoperationen ausgeführt. Keine erneute Bootstraprechnung. Ableitung mit Stdlib: `/tmp/sherlock_loss_inventory_20261021.py`; vollständige Kennzahlen, Auswahlregel, Einzelspielwerte und SHA-256 aller hier zentral verwendeten Quellen: `/tmp/sherlock-loss-inventory-20261021.json`.

## Geprüfte Basis

Quelle: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/compare/autonomous_20261020/v4_independent_20261021/fresh_v3.csv`, SHA-256 `71705b366a6012ff56285fd6dfb7964365e6e711439d37f33a6e2875dbdd44e2`.

800 vollständige eindeutige Schlüssel = 200 Karten 510800–510999 × beide Seiten × default/Solution_92, überall 303 Schritte und Punktzählversion 2. Für dieses Inventar ausschließlich die 400 Solution_92-Spiele: 311 Siege, 89 Niederlagen, keine Remis. Die 400 default-Spiele sind kein Bestandteil des Niederlagennenners. Der bisherige frische Bestätigungsblock wird durch die nun erfolgende Verlustauswahl zum bekannten Diagnoseblock; keine neue unabhängige Stärkenachweis-Stichprobe daraus machen.

| Spielseite | 3:0 | 2:1 | 1:2 | 0:3 | Niederlagen |
|---|---:|---:|---:|---:|---:|
| player_0 | 83 | 72 | 38 | 7 | 45/200 |
| player_1 | 98 | 58 | 36 | 8 | 44/200 |
| Gesamt | 181 | 130 | 74 | 15 | 89/400 |

Kartencluster nach beiden Ausgängen (Reihenfolge Seite 0/1): 138 WW, 27 LL, 18 LW, 17 WL. Damit tragen 27 beidseitig verlorene Karten 54/89 Niederlagen; 35 weitere Karten sind seitenspezifisch geteilt. 62/200 Karten enthalten mindestens eine Niederlage. Das ist eine Ergebnisgruppierung, **keine** nachgewiesene Gelände-/Spawn-/Parametergruppe. Fortlaufende Seednummern bedeuten keine räumlich ähnlichen Karten. 45 gegen 44 Verluste liefern hier keinen auffälligen globalen Seiteneffekt; einzelne Karten können dennoch starke Seitenunterschiede besitzen.

74/89 Niederlagen enden nach Matches 1:2, 15/89 mit 0:3. „1:2“ bedeutet nicht, dass die entscheidenden Matches knapp waren; die CSV speichert weder ihre Reihenfolge noch Punkteabstände oder Energie-/Zufalls-Tiebreaks. Gesamtpunktdifferenz bei Niederlagen: Median −142, Bereich −685 bis +371; 12/89 mit absolut höchstens 50. **21/89 Niederlagen haben trotzdem mehr Gesamtpunkte als der Gegner**, während 19/311 Siege eine negative Gesamtpunktdifferenz haben. Deshalb „knapp“/„deutlich“ erst nach Rekonstruktion der einzelnen Matches verwenden, nicht aus aufsummierten Punkten ableiten.

## Warum Endwerte keine Erklärung liefern

Niederlagen haben im Mittel 16,88 bekannte Punktfelder gegenüber 15,40 bei Siegen; mittlere `stack_frac` 17,80 % gegenüber 12,91 %. Daraus folgt weder, dass Wissen schadet, noch dass Stacking die Verluste verursacht. `known_point_tiles` ist Endwissen und hängt von tatsächlich vorhandenen Feldern sowie Erkundungsverlauf ab; die CSV enthält keinen Nenner echter Felder. `stack_frac` ist bereits ein zeitlich gepoolter Unit-Schrittanteil einschließlich maskierter Slots, keine Zahl verlorener Punkte oder unnötiger Doppelbesetzungen. Unterschiede der Kartendichte, Überlebensdauer, Energie und Gegnerdruck sind nicht kontrolliert. Die hier genannten Mittel gewichten jedes Spiel gleich, nicht jede Unit-Gelegenheit.

Auch `wait_frac` ist bei Verlusten niedriger (40,77 % statt 44,19 %); STAY auf einem produktiven Feld ist erwünscht, SAP kann ebenfalls ohne Bewegung punkten. SAP-Versuche/-Treffer sind keine gemessenen Trefferenergien. Finale Relic-/Punktkenntnis zeigt nicht, ob rechtzeitig vor der Matchentscheidung gehandelt wurde. Die Endpunktmuster begründen Fragen, keine unmittelbaren Patches oder Rewardänderungen.

## Fest vorgeschlagene Stichprobe: zehn Karten, beide Seiten, 20 Spiele

Gezielte, geschichtete Diagnoseauswahl zur Mechanismenvielfalt, **nicht proportional repräsentativ** und nicht zur Hochrechnung einer Fehlerhäufigkeit. Für jedes vorab definierte Stratum wird nach Gesamtpunktabstand sortiert und die untere Medianposition gewählt (Seed als Tie-Break); Ausnahmen „kleinster Abstand“ und „beidseitiger Punktevorsprung“ sind ausdrücklich dokumentiert. Schon gewählte Karten werden ausgeschlossen. Vollständige deterministische Auswahl im JSON/Skript. Ein Stratum „Seite 0 verliert 0:3, Seite 1 gewinnt“ existiert nicht; keines erfinden. Als eigenes vorhandenes Stratum wird stattdessen eine beidseitige Verlustkarte mit gemischtem 1:2/0:3 erfasst.

| Karte | Matchausgänge Seite 0 / 1 | Gesamtpunktdifferenzen 0 / 1 | Diagnosezweck |
|---|---|---:|---|
| 510862 | 1:2 / 1:2 | −69 / +19 | Beidseitiger Verlust bei kleinem aggregiertem Abstand |
| 510847 | 1:2 / 1:2 | −239 / −131 | Typische beidseitige 1:2-Verlustkarte nach Medianregel |
| 510930 | 0:3 / 0:3 | −304 / −462 | Beidseitige Matchserie ohne Sieg |
| 510956 | 1:2 / 2:1 | −93 / +83 | Paarvergleich: Seite 0 verliert, Seite 1 gewinnt |
| 510950 | 2:1 / 1:2 | −3 / −155 | Umgekehrter Paarvergleich, Sieg trotz Gesamtpunkteminus |
| 510972 | 2:1 / 0:3 | −102 / −509 | Ausgeprägter Unterschied der Matchausgänge je Seite |
| 510819 | 1:2 / 1:2 | +127 / +6 | Beide Seiten verlieren trotz Gesamtpunktevorsprung |
| 510858 | 1:2 / 0:3 | −223 / −424 | Beidseitiger Verlust mit unterschiedlichen Matchserien |
| 510911 | 2:1 / 2:1 | +211 / +84 | Beidseitiger Sieg als Kontrollverlauf, ebenfalls verlorene Matches |
| 510839 | 3:0 / 3:0 | +358 / +428 | Durchgehender erfolgreicher Kontrollverlauf |

Das sind 13 Niederlagen und 7 Siege auf 10 Karten; die Verlustanreicherung ist gewollt. Gegenüberseiten sind besonders nützliche Kontrollen für dieselbe Zufallskarte, aber keine identischen Behandlungssituationen: Position, Information und Interaktion können sich unterscheiden. Siegkontrollen nicht als kausales Matching verkaufen.

## Exakte Fragen an einen einzigen nächsten passiven Replay-/Zeitverlaufsdurchlauf

1. **Wann werden Matches verloren?** Je Match finales Punktepaar, Sieger und Tiebreakgrund, erste Punkte beider Teams, kumulierter Punkteabstand im Verlauf und Zeit mit Rückstand. Bei 510819 prüfen, ob ein hoher Siegüberschuss zwei knappe Verluste verdeckt oder andere Verteilungen vorliegen. Nicht aus dem Gesamtscore vorwegnehmen.
2. **Entdecken, beweisen oder besetzen?** Pro aktivem Relic/Punktfeld getrennt erfassen: tatsächlicher Spawn, erste direkte Sicht, erste Belief-Kenntnis (direkt/Symmetrie getrennt soweit verfügbar), erster Beweis als Punktefeld, erste tatsächliche produktive Besetzung. Bereits aus früheren Matches bekannte Relics separat behandeln. Zu vorab festen Zeitpunkten 25/50/75/100 echte aktive Felder, bekannte Felder und eindeutige produktiv besetzte Felder beider Teams berichten; keine Endkenntnis als frühes Wissen einsetzen.
3. **Was geschieht nach einem rechtzeitig bekannten freien Ziel?** Lebende zugewiesene Unit, Entfernung/BFS, Bewegungsenergie, finale Aktion, sichtbarer Gegnerdruck, aktuelle direkte Zielsicht und Zeitpunkt der Terrainbeobachtung; gab es gleichzeitig ein anderes bekanntes, freies und aktuell erreichbar erscheinendes Ziel? Unbekannt/veraltet ausdrücklich kennzeichnen. Blockade allein beweist keine bessere Alternative.
4. **Was kostet eine Punktbesetzung?** Bei Verlust produktiver Besetzung Energie/Negativstatus, Positionswechsel und gegnerische Anwesenheit zeitlich erfassen. Tatsächlichen Verlust von Unit-Identität/Lebenszyklus von neu gespawnten oder wiederverwendeten IDs trennen. Stacking nur auf echten Punktfeldern und zeitgleich verfügbaren Alternativen beschreiben; keine globale Stackquote als unmittelbare Fehlentscheidung.

Nur Mechanismen und konkrete Sequenzen beschreiben. Keine neue Stärkeprüfung, keine CI aus Unit-Schritten, keine Regelkombination, kein erneuter alter Negativversuch. Eine spätere Hypothese muss nach dieser Beobachtung eigenständig vorab definiert und auf anderen Karten geprüft werden.

## Vorhandenes wiederverwenden, notwendige Lücken gezielt ergänzen

- `scripts/common.py::play_game` und `scripts/scoring.py::{match_points_after_step,point_tile_map}` liefern deterministische Episode-/Seitenbehandlung und korrekte v2-Endpunkte. `RecordEpisode` aus `scripts/record_replay.py` erlaubt Replay und Diagnose **im selben Durchlauf**; keine zusätzliche zweite Reproduktionsrunde nötig. Die bestehende Replay-CLI überschreibt Namen und bietet kein exklusives Studienverzeichnis: nicht unverändert als sicherer Batchrunner verwenden.
- `scripts/analyze_losses.py` bietet Matchpunkte, eindeutige echte Feldbesetzung, Energie und Todzählung; `scripts/analyze_timing.py` bietet Spawn-/Sicht-/Erstpunkt-/Kenntnis-Meilensteine. Ihre aktuellen Schleifen sind jedoch kein fertiger neuer Observer: Agent-Belief wird durch `act(obs_t)` aktualisiert und anschließend teils mit `env.state(t+1)` verglichen. Für kausale Zeitreihen muss dieselbe Zeitbasis explizit gespeichert werden. `seen_step` bezeichnet irgendein bereits bekanntes aktives Relic, nicht zwingend das neu gespawnte; Todzählung nur über Maskenwechsel erkennt nicht jeden ID-Lebenszyklus. Diese bestehenden Felder nicht ungeprüft als präzise neue Latenzen übernehmen.
- Historische `timing_sol92_*.csv`: 4 Dateien, 240 Matchzeilen = 40 Karten × beide Seiten × 3 Matches, Seeds 500000–500039, **ohne Punktversionsspalte**. `timing_0.log` nennt ein Sechserensemble, nicht V3. Historische `o3s3_sol92_*.csv`: 4 Dateien, 480 Team-Matchzeilen, derselbe Kartenblock, ebenfalls ohne Versionsspalte. `regeln/*_sol92_*.csv`: 22 Dateien, 1.488 Team-Matchzeilen, 42 unterschiedliche Karten 500720–500761, v2, gemischte Stände. Keine dieser Gruppen enthält 510800–510999; alte Ursachenmuster sind kein V3-Niederlagennachweis für den neuen Block.
- Archivierter Point-flow-Observer erfasst eigene bekannte Feldziele, Zuweisung, Masken, Energie, BFS und Pendeln. Nützliche Funktionen können read-only übernommen werden, aber sein enger Match-3/eigene-Hälfte-Fokus und fehlende direkte Zielsicht/Alter sowie Alternativziele beantworten die neuen Matchfragen nicht vollständig. Rohdaten vorhandener 500720–500729-Reihe nicht nochmals spielen oder als breitere Negativhypothese umdeuten.
- Aktionsquellen-Wrapper sind technisch geprüft; für diese erste Verlustprobe reichen finale Aktionen plus Ziel-/Masken-Snapshot. Keine zweite Q-Auswertung und kein erneuter umfassender Netz-/Regelvergleich nötig. Ground Truth bleibt ausschließlich im externen Beobachter, niemals Agenteneingabe.

**Empfehlung:** genau die obigen 20 unveränderten V3-vs-Solution_92-Spiele einmal als Replay plus zeitlich ausgerichtete passive Match-/Feldbeobachtung aufnehmen. Vorher nur die fehlende Instrumentierung mit kleinen Tests prüfen (Reset/letzter Punkt, beide Koordinatenräume, spät gespawnte Relics, ID-Wiederverwendung, unveränderte Referenzaktion/Resultate). Fester V3-Hash `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`, Quellenfreeze, exklusiver Output, kein Training/Autosave, ein Worker; alle 23 nichtzeitlichen Referenzfelder je Spiel gegen genau die vorhandene CSV vergleichen, 303/v2/exakte 20 Schlüssel und vollständige Rohzeilen prüfen. Bei erster Reproduktionsabweichung stoppen. Dieses Inventar startet die Probe nicht.
