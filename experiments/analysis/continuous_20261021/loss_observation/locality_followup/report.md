# Begrenzter Folgecheck: Was „bekannt, aber unbesetzt“ lokal bedeutet

**Eine prüfbare Arbeitshypothese bleibt: Wiederbesetzung nach lokalen Energie-/Maskenverlusten kostet relevante Zeit; die Zahl vermeintlicher sofortiger Chancen wird zugleich durch weit entfernte bekannte Felder aufgebläht.** Die vier untersuchten Ausschnitte belegen solche Abläufe konkret, isolieren aber weder ihre gesamte Punktwirkung noch eine korrigierende Policy. Kein Regelpatch, keine neue Variante und keine Änderung des laufenden kontrollierten Curriculumvergleichs. Die falsche Hypothese eines durch Sapkosten gekippten Kollisionsvergleichs desselben Schritts bleibt zurückgenommen.

Nur vorhandene Traces gelesen; keine Modelle/Agenten/Engine importiert, keine Policy aufgerufen, keine Spiele/Trainingsjobs, kein Git-/Repositoryschreiben. Skript, JSON und Bericht liegen unter `/tmp`. Der abgeschlossene Gesamtbericht wurde nicht erneut erstellt oder erweitert.

## Feste Auswahl und messbare Grenzen

Aus allen 40 Snapshots der Matches 2 und 3 bei lokalem `t=75` wurden **vor der Detailinspektion** die vier größten Differenzen „produktive Gegnerfelder minus eigene produktive Felder“ genommen; Gleichstände nach Seed, Seite, Match aufsteigend. Die Auswahl umfasst drei Karten, beide Seiten von 510858 und ausschließlich später verlorene Spiele. Sie ist bewusst auf Extremfälle beschränkt; keine Prävalenz-/Stärke-/Kausalschätzung. Je Fall wird nur das feste Fenster t=65…85 untersucht. Ein globaler Schritt ist `(Match−1)×101+t`.

Die legal aufgezeichneten Entscheidungsdaten enthalten eigene Position/Energie, bekannte Punktfelder, finale Aktion, legale Ein-Schritt-Aktionsmaske und aktuell sichtbare Gegner samt Energie. Sie enthalten **keine Zielzuweisung, keinen BFS-Pfad, keine Feldenergiekarte, keinen vollständigen Terrain-/Sensorsicht-Snapshot eines Zieles und kein Ziel-Beobachtungsalter**. Deshalb bedeutet ein bekanntes Feld ohne sichtbaren Gegner nicht „sicher frei“, ein kurzer Manhattan-Abstand nicht „begehbar“ und die Bewegung auf ein bereits besetztes Feld nicht automatisch eine falsche Zielzuweisung.

Die eigenen/gegnerischen Kartenhälften werden rein geometrisch relativ zum Spawn getrennt: Seite0 hat `x+y<23`, Seite1 `x+y>23`; die Diagonale ist separat. Dies ist keine Besitz- oder Sicherheitsdefinition. Die Schnittmenge mit echten aktiven Feldern und die tatsächliche gegnerische Feldbelegung sind **externe Ground Truth**, keine Agentenkenntnis. Manhattan-Distanz ist nur eine optimistische Untergrenze der erforderlichen Bewegungszahl, ohne Hindernisse und Interaktion. Die zusätzliche Prüfung `E>=Distanz×Bewegungskosten` zählt nur vorhandenes Bewegungsbudget: keine Energiegewinne/-verluste, kein Pfadnachweis und weder notwendige noch hinreichende Erreichbarkeitsbedingung.

## Die vier Ausgangszustände bei t=75

| Fall | Bekannt/aktiv | Besetzt eigen/Gegner | eigene maskierte E≥0 Slots | bekannt unbesetzt | davon eigene Hälfte/Diagonale/Gegnerhälfte | Distanz zur Gegnerhälfte* |
| --- | --- | --- | --- | --- | --- | --- |
| 510858/p1/M2 | 24/24 | 1/11 | 5 | 23 | 11/0/12 | 21–29 |
| 510858/p0/M2 | 24/24 | 3/10 | 9 | 21 | 9/0/12 | 18–26 |
| 510847/p0/M3 | 15/15 | 3/9 | 9 | 12 | 4/1/7 | 8–14 |
| 510930/p1/M2 | 12/12 | 2/8 | 8 | 10 | 4/0/6 | 6–12 |

*Spanne des jeweils nächsten eigenen nichtnegativen Slots zu jedem unbesetzten bekannten Feld in der Gegnerhälfte. Ein bereits punktender Slot darf hier theoretisch umziehen; dies würde sein bisheriges Feld frei lassen. Keine tatsächliche Wegeplanung.

Bei 510858/p1 sind **12 der 23 unbesetzten bekannten Felder 21–29 Bewegungen entfernt**. Es existieren nur fünf nichtnegative eigene Slots, während der Gegner elf unterschiedliche Felder besetzt. Selbst eine kostenlose sofortige Verteilung dieser fünf Slots auf fünf verschiedene Punkte könnte höchstens fünf Felder halten: mindestens sechs Felder Abstand lassen sich in diesem Zustand allein durch Umverteilung nicht schließen. Bei p0 sind zwölf der 21 unbesetzten Felder 18–26 Bewegungen entfernt. In 510847/p0/M3 und 510930/p1/M2 liegen sämtliche sieben bzw. sechs unbesetzten bekannten Felder der Gegnerhälfte bereits tatsächlich unter gegnerischer produktiver Besetzung.

| Fall | bekannt unbesetzt | davon Gegner produktiv (extern) | davon Gegner auf Feld sichtbar | lokale Kandidaten ≤5 mit Bewegungsbudget* | eigene E≥0 Slots abseits echter Punkte |
| --- | --- | --- | --- | --- | --- |
| 510858/p1/M2 | 23 | 11 | 1 | 5 | 4 |
| 510858/p0/M2 | 21 | 10 | 2 | 7 | 5 |
| 510847/p0/M3 | 12 | 9 | 1 | 1 | 5 |
| 510930/p1/M2 | 10 | 8 | 0 | 1 | 5 |

*Kandidat: eigene Hälfte/Diagonale, im echten Zustand nicht gegnerisch produktiv besetzt, mindestens ein eigener nichtnegativer Slot abseits echter Punkte in Manhattan-Abstand≤5 und mit aktuell ausreichendem reinem Bewegungsbudget. **Das sind 5/7/1/1 potenzielle lokale Felder, keine erreichbaren oder gefahrlosen Alternativen.** Mehrere Felder können dieselbe Unit benötigen. Negativenergetische Gegner oder Terrainblockaden sind mit diesem Filter nicht ausgeschlossen. Die extern festgestellte gegnerische Besetzung ist häufig nicht sichtbar: beispielsweise bei 510858/p1 elf tatsächlich gegnerisch besetzte unbesetzte bekannte Felder, aber nur auf einem davon ein aktuell sichtbarer nichtnegativer Gegner.

Zwei solche lokalen Chancen werden im nächsten tatsächlichen Schritt genutzt: 510858/p1 UID0 bewegt sich bei t75 von(16,22) nach(15,22), Energie130→132; 510858/p0 UID12 von(3,8) nach(3,9), Energie5→5. „Bekannt und unbesetzt“ zu t75 ist hier also ein Zwischenzustand während realer Anreise und kein ausgelassener Zug. Bei 510847/p0 ist der einzige Kandidat(8,10), zuletzt von einem gerade negativ gewordenen eigenen Slot gehalten; bei 510930/p1 ist es(18,9).

## Energie-/Maskenverläufe und verbleibende Einsatzstärke

| Fall | E≥0 Slots t65→75→85 | produktive Felder t65→75→85 | Übergang E≥0→maskiert negativ | davon Start auf echtem Punkt | E≥0→Maske aus |
| --- | --- | --- | --- | --- | --- |
| 510858/p1/M2 | 13→5→7 | 6→1→2 | 12 | 11 | 1 |
| 510858/p0/M2 | 13→9→7 | 6→3→4 | 11 | 7 | 2 |
| 510847/p0/M3 | 10→9→9 | 4→3→2 | 7 | 6 | 0 |
| 510930/p1/M2 | 14→8→9 | 4→2→2 | 1 | 1 | 10 |

Die letzten drei Spalten zählen Übergänge im festen Fenster t65…85, **keine Tode/individuellen Lebenszyklen**. Ein Slot kann später am Spawn wieder auftreten. Sie quantifizieren keine gegnerische Schadensquelle und keinen Sap-Effekt. Die Fälle unterscheiden sich: In den beiden 510858-Seiten werden zahlreiche Slots negativ; 510930/p1 hat dagegen zehn Übergänge von nichtnegativ zu Maske aus und nur einen zu maskiert negativ. Eine einzige Energiepuffer-Erklärung würde diese Unterschiede verdecken.

## Tatsächliche aufeinanderfolgende Entscheidungen

Tabellen zeigen Zustand t und Resultat nach derselben Aktion. S=STAY, U/R/D/L=kardinale Bewegung, SAP=Sap. „–“ bedeutet kein aufgezeichneter aktiver Entscheidungsslot oder maskierte Energie nicht interpretierbar. Alle Werte sind aus den vorhandenen Übergängen; negative Energie wird nicht als Tod bezeichnet.

### 510858/p1/M2: negativer Punkt-Slot, Wiederauftauchen am Spawn und neun tatsächliche Anreiseschritte

UID0 steht t65 auf bekanntem(14,21) bei Energie0 und STAY; danach−11. Nach dem nächsten Übergang trägt dieser Slot die Spawnposition(23,23), Energie100. Von t67 bis75 folgen neun tatsächlich ausgeführte Bewegungen ohne STAY/SAP, danach ist das bekannte zuvor unbesetzte(15,22) produktiv. Die hohe Feldkenntnis erspart diese beobachtete Reise nicht; keine Aussage, dass derselbe Lebenszyklus fortlebt.

| t | Position | E | Aktion | Position danach | E danach | Maske danach |
| --- | --- | --- | --- | --- | --- | --- |
| 65 | [14, 21] | 0 | S | [14, 21] | -11 | an |
| 66 | [14, 21] | -11 | S | [23, 23] | 100 | an |
| 67 | [23, 23] | 100 | L | [22, 23] | 105 | an |
| 68 | [22, 23] | 105 | L | [21, 23] | 111 | an |
| 69 | [21, 23] | 111 | L | [20, 23] | 117 | an |
| 70 | [20, 23] | 117 | L | [19, 23] | 123 | an |
| 71 | [19, 23] | 123 | L | [18, 23] | 129 | an |
| 72 | [18, 23] | 129 | L | [17, 23] | 134 | an |
| 73 | [17, 23] | 134 | U | [17, 22] | 132 | an |
| 74 | [17, 22] | 132 | L | [16, 22] | 130 | an |
| 75 | [16, 22] | 130 | L | [15, 22] | 132 | an |
| 76 | [15, 22] | 132 | S | [15, 22] | 135 | an |

### 510858/p0/M2: lokale Chance wird besetzt, später geht Produktivität bei STAY verloren

UID12 erreicht(3,9) im Übergang t75→76 und bleibt t76…80 dort mit STAY. Energie5→6→7→8→9, dann−3; im Übergang t81 wird die Maske entfernt. Gegner UID15 wird derweil bei(5,11),(4,11),(3,11),(2,11),(2,10) sichtbar. Dies belegt Ankunft, zeitweilige produktive Haltung und anschließenden Nettoenergieverlust unter beobachtetem Gegnerkontakt. Es trennt Sap, Void und Feldenergie nicht; der Verlustschritt enthält kein eigenes SAP.

| t | Position | E | Aktion | Position danach | E danach | Maske danach |
| --- | --- | --- | --- | --- | --- | --- |
| 74 | [3, 7] | 7 | D | [3, 8] | 5 | an |
| 75 | [3, 8] | 5 | D | [3, 9] | 5 | an |
| 76 | [3, 9] | 5 | S | [3, 9] | 6 | an |
| 77 | [3, 9] | 6 | S | [3, 9] | 7 | an |
| 78 | [3, 9] | 7 | S | [3, 9] | 8 | an |
| 79 | [3, 9] | 8 | S | [3, 9] | 9 | an |
| 80 | [3, 9] | 9 | S | [3, 9] | -3 | an |
| 81 | [3, 9] | -3 | S | [3, 9] | – | aus |

### 510847/p0/M3: ein lokales bekanntes Feld verliert seine Besetzung, der Slot erscheint am Spawn

UID3 hält(8,10) mit STAY und wird bei t74 Energie15→−5. Nach t75 steht derselbe Slot am Spawn; danach folgen nur Bewegungen bis t80 und darüber hinaus. Das frei gewordene(8,10) ist bei t75 vier Manhattan-Schritte vom nächstgelegenen nichtpunktenden lebenden Slot UID1 entfernt, aber dessen tatsächlich ausgegebene Aktion führt von(8,6) nach bereits besetztem(9,6). Ohne dessen zugewiesenes Ziel, Terrain und geplante Wege ist das kein Beleg einer vermeidbaren Fehlzuweisung; die vorhandenen Daten zeigen diese offene Alternative nur geometrisch.

| t | Position | E | Aktion | Position danach | E danach | Maske danach |
| --- | --- | --- | --- | --- | --- | --- |
| 70 | [8, 10] | 19 | S | [8, 10] | 21 | an |
| 71 | [8, 10] | 21 | S | [8, 10] | 23 | an |
| 72 | [8, 10] | 23 | S | [8, 10] | 13 | an |
| 73 | [8, 10] | 13 | S | [8, 10] | 15 | an |
| 74 | [8, 10] | 15 | S | [8, 10] | -5 | an |
| 75 | [8, 10] | -5 | S | [0, 0] | 100 | an |
| 76 | [0, 0] | 100 | D | [0, 1] | 101 | an |
| 77 | [0, 1] | 101 | R | [1, 1] | 103 | an |
| 78 | [1, 1] | 103 | R | [2, 1] | 106 | an |
| 79 | [2, 1] | 106 | R | [3, 1] | 110 | an |
| 80 | [3, 1] | 110 | R | [4, 1] | 114 | an |

### 510930/p1/M2: ununterbrochene Anreise endet bei gleichzeitiger gegnerischer Ankunft

UID7 bewegt sich im ganzen gezeigten Abschnitt, erreicht aber keinen produktiven Punkt. Bei t78 ziehen eigene UID7 von(19,10),E125, und aktuell sichtbare gegnerische UID7 von(19,8),E150, beide nach(19,9). Eigene Maske danach aus, gegnerische Maske an. Dies ist eine konkret beobachtete Konvergenz mit stärkerem sichtbarem Gegner, keine Behauptung eines durch Sapkosten gekippten gleichen Schritts. Die vollständige lokale Zielabsicht fehlt.

| t | Position | E | Aktion | Position danach | E danach | Maske danach |
| --- | --- | --- | --- | --- | --- | --- |
| 70 | [22, 15] | 124 | U | [22, 14] | 125 | an |
| 71 | [22, 14] | 125 | U | [22, 13] | 127 | an |
| 72 | [22, 13] | 127 | U | [22, 12] | 130 | an |
| 73 | [22, 12] | 130 | L | [21, 12] | 134 | an |
| 74 | [21, 12] | 134 | L | [20, 12] | 135 | an |
| 75 | [20, 12] | 135 | L | [19, 12] | 132 | an |
| 76 | [19, 12] | 132 | U | [19, 11] | 122 | an |
| 77 | [19, 11] | 122 | U | [19, 10] | 125 | an |
| 78 | [19, 10] | 125 | U | [19, 9] | – | aus |
| 79 | – | – | – | – | – | – |

## Genau eine Hypothese, keine Maßnahme

**H_late:** In diesen Extremfällen trägt die Zeit bis zur Wiederbesetzung nach lokalen Energie-/Maskenverlusten zum späten Punktdefizit bei; der globale bekannte-unbesetzte-Feldzähler überschätzt zugleich sofort nutzbare lokale Chancen. Erwartbare, falsifizierbare Signatur: Belegungsrückgänge treten zeitlich zusammen mit Verlust nichtnegativer lokaler Slots auf; nachfolgende Slots verbringen mehrere Schritte in tatsächlicher Anreise oder erreichen ein lokales Feld nur kurz, bevor dessen Produktivität erneut entfällt. Die obigen vier Sequenzen zeigen Teile genau dieser Signatur.

Die Hypothese wäre als Erklärung geschwächt, wenn vollständig protokollierte Ziel-/Terrain-/Sichtdaten stattdessen lange, sichere, energetisch tragbare freie lokale Ziele neben verfügbaren Units zeigen und das Belegungsdefizit überwiegend aus ausgelassener Zuweisung besteht. Das ist mit diesem Archiv **nicht entscheidbar**. Schon UID1 im dritten Beispiel hält eine solche offene Zuweisungsfrage sichtbar; sie wird nicht unter dem Wiederbesetzungsmuster versteckt. Ebenso ist nicht isoliert, welcher Anteil des Energieverlusts vom Gegner, vom Terrain, von eigenen früheren Saps oder anderen Effekten stammt. Der Bericht entscheidet weder einen Trainingsmechanismus noch einen Reserve-/Target-/Kollisionspatch. Root entscheidet jede weitere Untersuchung; dieser begrenzte Check endet hier.

## Dateien und Prüfbasis

Analyse: `/tmp/sherlock_late_locality_20261021.py`; Ergebnisdaten: `/tmp/sherlock-late-locality-20261021.json`; Bericht: `/tmp/sherlock-late-locality-20261021.md`. Das JSON enthält nur die vier ausgewählten Fälle, sämtliche Feldklassifikationen und deren 4×21 aufeinanderfolgende Zustände. Auswahl und Feld-/Fensterpartition wurden per Assertion geprüft. Hashes der vier gelesenen Rohdateien und Summaries stehen im JSON. Keine erneute Vollprüfung des Archivs.

Manifest SHA-256: `b866c89d65cc26479ad71b1ebfcf4958b47385160af1544a9ab98659412f5f58`. Analyseskript SHA-256: `854ae605850e696ac279675fad0fc9092e62caddb50201b7a5da28eb0f2b2b5a`.
