# Passive V3-Verlustdiagnose: keine Kollisions-Veto-Regel ableiten

Read-only-Auswertung vom 21.10.2026 der abgeschlossenen, ergebnisgeschichteten 20 Spiele auf zehn Karten. Keine Modelle/Agenten/Engine importiert, keine Spiele, Gegenfaktik oder Trainingsjobs gestartet, keine Repositorydateien geändert. Exakte Zählung mit Python-Stdlib; keine Prävalenz- oder Stärkeschätzung und keine Konfidenzintervalle aus Unit-Schritten.

## Entscheidung und Hauptbefunde

**Kein Agenten-/Regelpatch. Den bereits separat geplanten Curriculumvergleich mit unveränderter V3-Logik fortsetzen; diese Diagnose ist kein neuer Wirksamkeitsnachweis dafür.** Keine Wiederholung oder Kombination der negativen Reserve-, safe_moves-, sap_geometry-, active_targets- oder V4-Versuche.

- **H1 wird zurückgenommen:** Die eingefrorene Engine verwendet bei Kollisionen Energie nach Bewegung, aber vor Sap. Eigene Sapkosten ändern daher die unmittelbare Kollisionsentscheidung nicht. Die frühere gegenteilige Interpretation war falsch. Root hat die Korrektur auch mit einem engen synthetischen Engine-Test bestätigt.
- **Tracebefund dazu:** 18.020 strenge bekannte Punkt-Singletons → 17.610 post-rule STAY → 1.674 erzwungene SAPs → 104 sichtbare Nachbarkontexte → 13 enge Kostenindikatoren. In fünf davon zieht der Gegner tatsächlich auf das Feld; alle fünf behalten unmittelbar die produktive Besetzung. Kostenindikator ist kein Kollisionskipppunkt.
- **Wann Spiele verloren werden:** Matchsiege 16/20 in M1, 6/20 in M2, 3/20 in M3. Alle 13 verlorenen Spiele verlieren M2 und M3. Ein einziges Match endet punktgleich: 510858/player_1, M1, 364:364; Energietiebreak 576:1.478 gegen Sherlock.
- **Späte Belegung trotz Wissen:** Bei den 13 verlorenen Spielen sind M2/t75 im Mittel 80,1% der echten aktiven Punktfelder bekannt, aber 4,00 eigene gegenüber 7,62 gegnerischen Feldern produktiv besetzt. M3/t100: 88,6% bekannt, 4,62 gegenüber 9,08 besetzt. Das zeigt einen Belegungsrückstand, trennt jedoch Anreise, Zuweisung, Energie und Gegnerdruck noch nicht als Ursachen.
- **Energiebeobachtung ohne Kausalbehauptung:** 123/1.653 auswertbare strenge forced-SAP-Übergänge enden mit einem maskierten negativen eigenen Slot, 130 mit Verlust der bisherigen produktiven Feldbesetzung. Unterschiedliche Ausgangszustände und simultane Effekte verhindern eine daraus abgeleitete Reserve-Regel. Slots werden nicht als Lebenszyklen/Todesfälle gezählt.

Die 20 Spiele auf zehn Karten sind ergebnisgeschichtet ausgewählt (7 Siege/13 Niederlagen). Alle Zahlen sind Diagnosezählungen, keine Prävalenz-, Stärke- oder Patchwirkungsschätzung. Einzelspiele, Kartennenner, 240 Snapshots und ±5-Schritt-Sequenzen folgen im Anhang; vollständige Rohableitungen stehen im JSON.

## Anhang: Datenabhängigkeit und Rücknahme von H1

Die tatsächlich eingefrorene Engine speichert `original_unit_energy = state.units.energy` **nach der Bewegung und vor Sap** (`env.py:293`). Die Kollisions-Energiesummen werden anschließend ausdrücklich aus `original_unit_energy` berechnet (`env.py:462`), nicht aus den nach Sap veränderten Energien. Der Vergleich steht bei 486–499. Die zeitliche Reihenfolge Bewegung → Sap → Kollision reicht deshalb nicht, um auf eine Sap-bedingte Änderung der Kollisionsstärke zu schließen. Der frühere Solution_92-Bericht und sein isoliertes Rechenbeispiel verwendeten hier das falsche Energiestadium.

Folge: Eigene Sapkosten oder gleichzeitig eingehender Sap ändern in dieser Engine den **gleichen Kollisionsvergleich dieses Schritts nicht**. Sie können den anschließenden Energie-/Punktstatus und spätere Situationen beeinflussen; daraus folgt ohne separate Ursacheprüfung keine konkrete Patchwirkung. Die archivierten `cost_only_margin_stay/sap` bleiben beschreibende Kostenindikatoren, sind aber keine tatsächliche Kollisionsreserve. Kein archivierter Replay-Schritt wurde kontrafaktisch simuliert. Root hat die Datenabhängigkeit inzwischen zusätzlich mit einem getrennten synthetischen Engine-Test bestätigt: `/tmp/sherlock-sap-collision-correction-20261021.md`; identische gesamte Masken in STAY/SAP, eigene Restenergien102/62. Dieser Test ist nicht Teil der20 beobachteten Spiele.

Das Rohmaterial passt zu dieser Korrektur: 13 eng definierte Kostenindikatoren, davon fünf tatsächlich eintretende Gegneraktionen; **alle fünf behalten im unmittelbaren Folgezustand das produktiv besetzte Feld**. Ein sofortiger durch Sapkosten gekippter Kollisionsausgang ist weder durch die Engine noch durch diese fünf Ereignisse gestützt.

## Basis, Zeitachsen und Grenzen

Archiv: `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/experiments/analysis/continuous_20261021/loss_observation`. Freeze-HEAD `525060f01c5b7e7507e63982db5fd6742f6273f6`. Manifest SHA-256 `b866c89d65cc26479ad71b1ebfcf4958b47385160af1544a9ab98659412f5f58`. 6.060 Übergänge, 60 Matches, 240 feste Snapshots, 7 gewonnene/13 verlorene Spiele; alle 20 Spiele sind dieselben zuvor ergebnisgeschichtet ausgewählten Diagnosefälle. Ausgabedateihashes wurden aus dem bereits von Root geprüften Manifest übernommen; keine zweite vollständige Integritätsprüfung.

`step_t` ist der globale Zustand vor der Aktion (0–302), `match_step_t` der lokale Zustand (0–100). Punkte in den Matchtabellen sind vollständig nach dem letzten Übergang/v2; überall Sherlock zuerst. Der „dauerhafte Rückstand ab“ bezeichnet den ersten **Nach-Übergangsindex 1–101**, ab dem der Punktabstand bis zum Matchende durchgehend negativ bleibt; dies ist rückblickend beschrieben und kein Zeitpunkt mathematischer Uneinholbarkeit. Kenntnis stammt aus `act(obs_t)`, Belegung/echte aktive Felder aus demselben externen Zustand t. Reset-Folgezustände werden aus kurzfristigen Ereignisquoten ausgeschlossen.

Eine verschwundene Maske, ein negativer Energiezustand, ein versetzter Slot und der Verlust produktiver Feldbelegung sind verschiedene Ergebnisse. Derselbe Slot kann schon im nächsten Übergang wieder am Spawn erscheinen. Deshalb weder Todeszahlen aus IDs ableiten noch maskierte oder versetzte Slots als dieselbe durchgehend beobachtete Einheit behandeln. Nichtmaskierte Energie-Restwerte sind nicht interpretierbar. Die JSON-Beispiele enthalten reine Zustandswerte, keine Lebenszyklusbehauptung.

## Exakte Matchausgänge und Zeitpunkt der Verluste

| Karte | Seite | Spiel | Match 1 | Match 2 | Match 3 | Dauerhafter Rückstand M1/M2/M3 |
| --- | --- | --- | --- | --- | --- | --- |
| 510862 | 0 | L | 171:125 W | 522:622 L | 623:638 L | –/73/99 |
| 510862 | 1 | L | 219:85 W | 481:587 L | 595:604 L | –/73/100 |
| 510847 | 0 | L | 181:74 W | 183:266 L | 277:540 L | –/19/16 |
| 510847 | 1 | L | 221:45 W | 257:303 L | 287:548 L | –/67/16 |
| 510930 | 0 | L | 110:137 L | 246:440 L | 342:425 L | 47/36/43 |
| 510930 | 1 | L | 165:198 L | 230:503 L | 306:462 L | 33/38/43 |
| 510956 | 0 | L | 164:71 W | 358:374 L | 267:437 L | –/25/68 |
| 510956 | 1 | W | 148:89 W | 342:308 W | 264:274 L | –/–/96 |
| 510950 | 0 | W | 123:9 W | 245:385 L | 315:292 W | –/63/– |
| 510950 | 1 | L | 114:14 W | 158:374 L | 258:297 L | –/49/43 |
| 510972 | 0 | W | 191:122 W | 643:552 W | 485:747 L | –/–/47 |
| 510972 | 1 | L | 154:259 L | 520:664 L | 472:732 L | 36/72/47 |
| 510819 | 0 | L | 460:40 W | 324:532 L | 254:339 L | –/17/58 |
| 510819 | 1 | L | 377:67 W | 380:550 L | 204:338 L | –/17/47 |
| 510858 | 0 | L | 374:275 W | 465:728 L | 751:810 L | –/58/89 |
| 510858 | 1 | L | 364:364 L (E) | 431:756 L | 690:789 L | E/64/80 |
| 510911 | 0 | W | 288:72 W | 558:473 W | 500:590 L | –/–/32 |
| 510911 | 1 | W | 286:110 W | 519:501 W | 521:631 L | –/–/32 |
| 510839 | 0 | W | 81:61 W | 410:202 W | 564:434 W | –/–/– |
| 510839 | 1 | W | 103:35 W | 433:200 W | 550:423 W | –/–/– |

Matchsiege: **16/20 in M1, 6/20 in M2, 3/20 in M3**. Alle 13 verlorenen Spiele verlieren M2 und M3: neun W–L–L, vier L–L–L. Die vier L–L–L-Spiele sind nach Match 2 entschieden; die anderen neun Verluste erst nach Match 3. 59/60 Matches werden über Punkte, eines über Energie und keines per Zufall entschieden. Die 35 verlorenen Matches umfassen 34 Punktverluste und einen Energietiebreak.

Der Energietiebreak ist **510858/player_1, M1: 364:364 Punkte, Energie 576:1.478**; Sherlock führt in 56/101 Nach-Übergangszuständen, liegt in 17 zurück und ist in 28 gleichauf. Kurz vor Schluss beträgt der Vorsprung noch +10/+6/+3, dann 0. Die Gesamtpunktdifferenz allein unterschlägt diesen Mechanismus.

510819 bestätigt das frühe Überschussmuster genau: Seite 0 gewinnt M1 mit +420, verliert M2/M3 mit −208/−85 und das Spiel trotz +127 Gesamtpunkten. Seite 1 gewinnt M1 mit +310, verliert später −170/−134 und das Spiel trotz +6. Bei 510862 fällt M3 dagegen sehr spät endgültig zurück: nach lokalem Übergang 99 bzw. 100, finale Differenzen −15/−9. Die punktverlorenen Matches haben dauerhaften Rückstand ab Median 36 in M1 (Spanne 33–47, n=3), 53,5 in M2 (17–73,n=14), 47 in M3 (16–100,n=17). Dies rechtfertigt keine einzige globale „früh verloren“-Erklärung.

## Bekannte Felder versus produktive Besetzung

Die folgende Tabelle gewichtet jedes Spiel gleich. K = bekannte **aktive echte** Punktfelder, T = echte aktive Punktfelder, B = eindeutige produktiv besetzte Felder Sherlock/Gegner, U = bekannte aktive Felder ohne eigene produktive Besetzung. Die beiden Seiten einer Karte sind getrennte Verläufe. Ein freies bekanntes Feld ist nicht automatisch erreichbar, verfügbar oder sinnvoll zu besetzen; Zielzuweisung, BFS, direkte Ziel-Sensorsicht und Beobachtungsalter fehlen im Archiv.

| Match | Schritt t | Spiele | davon T>0 | Mittel K/T | Mittel B eigen/Gegner | Mittel U |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 25 | 20 | 6 | 0.00/2.20 | 0.00/0.05 | 0.00 |
| 1 | 50 | 20 | 20 | 2.80/10.00 | 1.50/1.25 | 1.35 |
| 1 | 75 | 20 | 20 | 8.00/10.00 | 4.00/1.95 | 4.00 |
| 1 | 100 | 20 | 20 | 9.50/10.00 | 3.75/3.25 | 5.75 |
| 2 | 25 | 20 | 20 | 9.60/15.90 | 2.15/2.60 | 7.45 |
| 2 | 50 | 20 | 20 | 11.40/19.50 | 4.85/5.00 | 6.55 |
| 2 | 75 | 20 | 20 | 15.45/19.50 | 5.55/6.45 | 9.90 |
| 2 | 100 | 20 | 20 | 16.25/19.50 | 4.05/7.65 | 12.20 |
| 3 | 25 | 20 | 20 | 16.25/20.30 | 2.05/2.30 | 14.20 |
| 3 | 50 | 20 | 20 | 16.85/22.50 | 6.15/6.80 | 10.75 |
| 3 | 75 | 20 | 20 | 19.05/22.50 | 5.95/6.95 | 13.10 |
| 3 | 100 | 20 | 20 | 19.55/22.50 | 5.15/8.10 | 14.40 |

Alle 240 Snapshots haben keine bekannten Felder außerhalb der echten aktiven Feldmenge. Das belegt Snapshot-Konsistenz des Wissens, nicht die Vollständigkeit der Erkundung. Die anfänglich kleinen T-Nenner entstehen auch durch noch nicht gespawnte Relics; Quotienten im JSON schließen T=0 aus und nennen dafür `n_games_active`. Kenntnis aus früheren Matches ist in M2/M3 vorhanden. Direkte Beobachtung versus Symmetriebeweis und individuelle Spawn-/Entdeckungs-Latenz sind im Recorder nicht getrennt, daher hier nicht nachträglich erfunden.

| Spielgruppe | n | Match | t | Mittel K/T je Spiel | Mittel B eigen/Gegner |
| --- | --- | --- | --- | --- | --- |
| Verlust | 13 | 2 | 25 | 78.6% | 2.31/2.77 |
| Verlust | 13 | 2 | 50 | 62.1% | 4.92/5.38 |
| Verlust | 13 | 2 | 75 | 80.1% | 4.00/7.62 |
| Verlust | 13 | 2 | 100 | 84.6% | 3.85/8.54 |
| Verlust | 13 | 3 | 25 | 83.1% | 2.23/2.31 |
| Verlust | 13 | 3 | 50 | 79.7% | 6.31/6.54 |
| Verlust | 13 | 3 | 75 | 86.0% | 5.31/7.46 |
| Verlust | 13 | 3 | 100 | 88.6% | 4.62/9.08 |
| Sieg | 7 | 2 | 25 | 40.9% | 1.86/2.29 |
| Sieg | 7 | 2 | 50 | 54.8% | 4.71/4.29 |
| Sieg | 7 | 2 | 75 | 85.2% | 8.43/4.29 |
| Sieg | 7 | 2 | 100 | 90.1% | 4.43/6.00 |
| Sieg | 7 | 3 | 25 | 90.1% | 1.71/2.29 |
| Sieg | 7 | 3 | 50 | 79.7% | 5.86/7.29 |
| Sieg | 7 | 3 | 75 | 91.7% | 7.14/6.00 |
| Sieg | 7 | 3 | 100 | 94.4% | 6.14/6.29 |

Auf den 13 verlorenen Spielen sind in M2 bei t=75 bereits im Mittel 80,1% der echten aktiven Felder bekannt, aber nur 4,00 eigene gegenüber 7,62 gegnerischen Feldern produktiv besetzt. Bei t=100: 84,6% bekannt, 3,85 gegenüber 8,54 besetzt. In M3 bei t=100: 88,6% bekannt, 4,62 gegenüber 9,08. Das dokumentiert einen späten Belegungsrückstand trotz erheblicher Kenntnis. Es trennt noch nicht Anreise, Zuweisung, Energiemangel, Gegnerdruck und Wiederbesetzung als Ursachen; `active_targets` oder pauschale Reserven daraus erneut abzuleiten wäre unbegründet.

Konkrete späte Zustände je Spiel bei t=100; K/T und produktive Besetzung sind exakte Feldzahlen, keine Mittelwerte:

| Karte | Seite | Spiel | M2 K/T | M2 B eigen/Gegner | M2 U | M3 K/T | M3 B eigen/Gegner | M3 U |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 510862 | 0 | L | 18/22 | 8/11 | 10 | 20/22 | 5/10 | 15 |
| 510862 | 1 | L | 16/22 | 6/9 | 10 | 20/22 | 5/11 | 15 |
| 510847 | 0 | L | 13/13 | 5/6 | 8 | 15/15 | 3/9 | 12 |
| 510847 | 1 | L | 13/13 | 5/5 | 8 | 15/15 | 4/7 | 11 |
| 510930 | 0 | L | 12/12 | 0/8 | 12 | 12/12 | 3/6 | 9 |
| 510930 | 1 | L | 12/12 | 0/9 | 12 | 12/12 | 2/8 | 10 |
| 510956 | 0 | L | 16/18 | 9/2 | 7 | 16/18 | 3/6 | 13 |
| 510956 | 1 | W | 16/18 | 6/1 | 10 | 16/18 | 4/5 | 12 |
| 510950 | 0 | W | 14/18 | 3/5 | 11 | 18/18 | 4/2 | 14 |
| 510950 | 1 | L | 12/18 | 1/7 | 11 | 18/18 | 6/4 | 12 |
| 510972 | 0 | W | 20/20 | 6/6 | 14 | 20/20 | 1/14 | 19 |
| 510972 | 1 | L | 20/20 | 5/11 | 15 | 20/20 | 1/12 | 19 |
| 510819 | 0 | L | 12/29 | 0/11 | 12 | 16/37 | 6/8 | 10 |
| 510819 | 1 | L | 14/29 | 1/11 | 13 | 18/37 | 5/8 | 13 |
| 510858 | 0 | L | 24/24 | 6/11 | 18 | 34/36 | 10/14 | 24 |
| 510858 | 1 | L | 24/24 | 4/10 | 20 | 34/36 | 7/15 | 27 |
| 510911 | 0 | W | 20/25 | 4/10 | 16 | 20/25 | 6/6 | 14 |
| 510911 | 1 | W | 21/25 | 6/8 | 15 | 23/25 | 8/7 | 15 |
| 510839 | 0 | W | 14/14 | 4/6 | 10 | 22/22 | 12/4 | 10 |
| 510839 | 1 | W | 14/14 | 2/6 | 12 | 22/22 | 8/6 | 14 |

## H1-Ereignistrichter und tatsächliche Folgezustände

Gezählt werden Unit-Schritte, keine unabhängigen Kämpfe. Der strenge Nenner verlangt außerhalb Matchstart: eigene Maske, Energie≥0, bekanntes Punktefeld und genau einen maskierten eigenen Slot auf dem Feld. Der Recorder meldet zunächst 18.062 Singleton-Kontexte nach nichtnegativen Slots; 42 mit zusätzlich maskiertem negativem Slot werden ausgeschlossen →18.020 strenge Kontexte. `pt_sap` wird nur zugeschrieben, wenn post-rule STAY, finales und aufgezeichnetes SAP, legale SAP-Maske und `first_on_tile==uid`; konkurrierende späte Flags sind im Freeze ausgeschaltet.

Sichtbarer Nachbar: kardinal benachbart, Energie≥Bewegungskosten, aktuelles eigenes Feld direkt als passierbar sichtbar. Enger Kostenindikator: genau ein solcher Nachbar, Sapzentrum dessen aktuelle Position, `E_eigen > E_gegner−move` und `E_eigen−sap <= E_gegner−move`. Dies ignoriert Stacks, simultane Aktionen und deren Energiewirkungen und ist nach der Enginekorrektur ausdrücklich **kein Kollisionskipppunkt**.

| Karte | S | Spiel | A Singleton | B rule-STAY | C forced SAP | D Nachbar | E eng | F Eintritt aus D | G Eintritt aus E | H Feldverlust aus F |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 510862 | 0 | L | 1131 | 1115 | 66 | 4 | 1 | 1 | 0 | 0 |
| 510862 | 1 | L | 1136 | 1122 | 78 | 6 | 2 | 2 | 1 | 0 |
| 510847 | 0 | L | 555 | 549 | 71 | 2 | 1 | 0 | 0 | 0 |
| 510847 | 1 | L | 655 | 650 | 102 | 8 | 2 | 4 | 1 | 0 |
| 510930 | 0 | L | 573 | 543 | 124 | 14 | 2 | 4 | 0 | 3 |
| 510930 | 1 | L | 582 | 550 | 104 | 15 | 0 | 4 | 0 | 2 |
| 510956 | 0 | L | 684 | 659 | 81 | 1 | 1 | 1 | 1 | 0 |
| 510956 | 1 | W | 670 | 643 | 80 | 2 | 0 | 0 | 0 | 0 |
| 510950 | 0 | W | 632 | 631 | 59 | 5 | 0 | 0 | 0 | 0 |
| 510950 | 1 | L | 455 | 454 | 47 | 3 | 0 | 0 | 0 | 0 |
| 510972 | 0 | W | 1199 | 1157 | 131 | 5 | 0 | 2 | 0 | 2 |
| 510972 | 1 | L | 1035 | 1008 | 136 | 5 | 2 | 2 | 1 | 1 |
| 510819 | 0 | L | 925 | 908 | 51 | 3 | 1 | 1 | 1 | 0 |
| 510819 | 1 | L | 828 | 817 | 50 | 2 | 0 | 1 | 0 | 0 |
| 510858 | 0 | L | 1341 | 1269 | 102 | 6 | 0 | 0 | 0 | 0 |
| 510858 | 1 | L | 1275 | 1216 | 112 | 4 | 0 | 1 | 0 | 1 |
| 510911 | 0 | W | 1232 | 1222 | 75 | 5 | 1 | 2 | 0 | 1 |
| 510911 | 1 | W | 1219 | 1211 | 80 | 4 | 0 | 1 | 0 | 0 |
| 510839 | 0 | W | 939 | 935 | 53 | 5 | 0 | 2 | 0 | 1 |
| 510839 | 1 | W | 954 | 951 | 72 | 5 | 0 | 0 | 0 | 0 |
| Gesamt | – | 7W/13L | 18020 | 17610 | 1674 | 104 | 13 | 28 | 5 | 11 |

C/B = 1.674/17.610; D/C =104/1.674; E/D =13/104; F/D =28/104; G/E=5/13; H/F=11/28. Diese sind deskriptive Brüche derselben selektierten Verläufe, keine Risiko-/Effektschätzung. Alle 104 D-Ereignisse liegen auf echten aktiven Punktfeldern und außerhalb Reset. D kommt in 20/20 Spielen und 10/10 Karten vor; E in 9/20 Spielen auf 7/10 Karten; G in 5/20 Spielen auf 5/10 Karten. Aus G entstehen 0/5 sofortige negative Energien, 0/5 fehlende Masken, 0/5 produktive Feldverluste.

| Karte | Siege/2 | A | B | C | D | E | F | G | H |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 510819 | 0 | 1753 | 1725 | 101 | 5 | 1 | 2 | 1 | 0 |
| 510839 | 2 | 1893 | 1886 | 125 | 10 | 0 | 2 | 0 | 1 |
| 510847 | 0 | 1210 | 1199 | 173 | 10 | 3 | 4 | 1 | 0 |
| 510858 | 0 | 2616 | 2485 | 214 | 10 | 0 | 1 | 0 | 1 |
| 510862 | 0 | 2267 | 2237 | 144 | 10 | 3 | 3 | 1 | 0 |
| 510911 | 2 | 2451 | 2433 | 155 | 9 | 1 | 3 | 0 | 1 |
| 510930 | 0 | 1155 | 1093 | 228 | 29 | 2 | 8 | 0 | 5 |
| 510950 | 1 | 1087 | 1085 | 106 | 8 | 0 | 0 | 0 | 0 |
| 510956 | 1 | 1354 | 1302 | 161 | 3 | 1 | 1 | 1 | 0 |
| 510972 | 1 | 2234 | 2165 | 267 | 10 | 2 | 4 | 1 | 3 |

Verlustspiele: A=11.175, B=10.860, C=1.124, D=73, E=12, F=21, G=5, H=7. Siegspiele: A=6.845, B=6.750, C=550, D=31, E=1, F=7, G=0, H=4. Aufgrund der ergebnisgeschichteten Kartenwahl und unterschiedlicher Energie-/Gegnerkontexte ist kein kausaler Gruppenvergleich zulässig.

Die 28 tatsächlichen Eintrittsvorschläge in D enden mit 11 produktiven Feldverlusten: neunmal eigene Maske im Folgezustand aus, zweimal Slot an anderer Position; keine negative Energie bei verbleibendem Slot. 17 behalten das produktive Feld. Die 76 D-Kontexte ohne tatsächlichen Eintritt haben neun Feldverluste und zehn negative eigene Slots (eine andere eigene Unit kann das Feld weiter besetzen). Der einzige sofortige Feldverlust der 13 engen Kostenindikatoren gehört gerade **nicht** zu einem eintretenden Gegner: 510862/player_0, t=68.

Gegenkontrolle: 263 vergleichbare sichtbare Nachbarkontexte mit finalem STAY, davon 104 tatsächliche Eintrittsvorschläge. Ein Eintrittsfall liegt an einer Resetgrenze (510956/player_1,t=100) und bleibt aus den kurzfristigen Outcomes ausgeschlossen; auswertbar sind103 Eintrittsfälle. Davon85 Feldverluste, 66 fehlende Masken und 19 versetzte Slots. Viele STAY-Kontexte haben SAP gar nicht legal oder sehr geringe eigene Energie; dies ist deshalb kein Behandlungseffektvergleich mit erzwungenem SAP. Beispiel 510847/player_1,t=196 bleibt trotz 13 gegen 15 gegnerischer Energie produktiv, weil die Gegnerbewegung 4 kostet.

## Energie-/Belegungsverlust nach Sap: sichtbar, aber keine neue Ursache behaupten

Über **alle** strengen erzwungenen SAP-Kontexte (mit oder ohne benachbarten Gegner) gibt es 1.653 auswertbare Übergänge und 21 Resetgrenzen. In 123/1.653 ist der eigene Slot danach maskiert und negativ, in 9/1.653 fehlt seine Maske, in 3/1.653 ist der maskierte Slot versetzt; 130/1.653 verlieren insgesamt die produktive Belegung des bisherigen Felds. Kategorien sind nicht als Todeszählung addierbar und Feldverlust ist nicht gleich Slotverlust. Bei finalem STAY sind es 15.730 auswertbare Übergänge, 398 negative Slots, 69 fehlende Masken, 19 versetzte Slots und 463 Feldverluste; die Zustands-/Aktionsselektion unterscheidet sich deutlich. Diese Zahlen tragen keinen neuen pauschalen Reserve-Patch.

Fünf Nach-Übergangszustände nach jedem engen Kostenindikator sind im JSON separat gespeichert. 5/13 sehen innerhalb dieses Fensters irgendwann einen Verlust produktiver Belegung am Ausgangsfeld; darunter 2/5 der tatsächlichen Eintrittsfälle. Vier dieser fünf Fenster enthalten einen maskierten negativen Slot, eines eine später fehlende Maske. Beispiel 510956/player_0,t=66: unmittelbare Besetzung bei Energie 1; einen Schritt später −23 und keine produktive Besetzung. Beispiel 510972/player_1,t=72: Energien 55/59/63/23, dann im fünften Nachzustand fehlende Maske. Mehrere weitere Aktionen/Effekte liegen dazwischen; diese Verläufe dürfen nicht als verzögerter kausaler Schaden des ursprünglichen SAP bezeichnet werden.

## Repräsentative Sequenzen, jeweils fünf Schritte davor und danach

Deterministische Auswahl: erster passender Fall in der vorgegebenen Spielreihenfolge, dann globaler Schritt und UID. Positionen/Aktionen sind Weltkoordinaten. A=0 STAY,1 hoch,2 rechts,3 runter,4 links,5 SAP. „E danach“ wird bei fehlender Maske als „–“ ausgegeben; der Rohwert bleibt im JSON. Eigene Feldbelegung und Slotposition sind gesondert im Ereignis-JSON vorhanden. Gegneraktionen sind nachträglich protokolliert und waren kein Policy-Input.

### 510862_player_1, t=148, eigene UID 4

Enger Kostenindikator mit tatsächlichem Eintritt und produktiver Folgebesetzung: eigene Energie93, Gegner78, move2,sap33, Kostenmargen +17/−16. Der Gegner zieht auf das Feld; eigene Energie danach64, eigene Maske bleibt. Genau dieser Fall widerspricht der alten Kosten-Kollisionsinterpretation.

| t | E eigen | A eigen | E danach | Maske danach | Pos danach | E Gegner | A Gegner | Gegnermaske danach | Punkte danach |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 143 | 163 | 0,0,0 | 167 | an | 17,15 | 161 | 2,0,0 | an | 137:133 |
| 144 | 167 | 0,0,0 | 171 | an | 17,15 | 161 | 3,0,0 | an | 143:138 |
| 145 | 171 | 0,0,0 | 175 | an | 17,15 | 159 | 3,0,0 | an | 149:143 |
| 146 | 175 | 0,0,0 | 179 | an | 17,15 | 155 | 2,0,0 | an | 155:149 |
| 147 | 179 | 5,-2,0 | 93 | an | 17,15 | 156 | 2,0,0 | an | 161:155 |
| 148 | 93 | 5,-1,0 | 64 | an | 17,15 | 78 | 2,0,0 | aus | 167:160 |
| 149 | 64 | 0,0,0 | 68 | an | 17,15 | – | 0,0,0 | an | 173:166 |
| 150 | 68 | 0,0,0 | 72 | an | 17,15 | 100 | 3,0,0 | an | 179:172 |
| 151 | 72 | 0,0,0 | 72 | an | 17,15 | 92 | 2,0,0 | an | 185:177 |
| 152 | 72 | 0,0,0 | 72 | an | 17,15 | 91 | 2,0,0 | an | 190:184 |
| 153 | 72 | 5,-2,-2 | 39 | an | 17,15 | 87 | 2,0,0 | an | 196:189 |

### 510930_player_0, t=89, eigene UID 2

Erzwungenes Sap mit Eintritt und Feldverlust: eigene Energie140, Gegner169, move1; schon die relevante Vor-Sap-Relation ist140<168. Kein enger Kostenindikator. Eigene Maske danach aus; das erklärt nicht, ob frühere Aktionen anders hätten sein sollen.

| t | E eigen | A eigen | E danach | Maske danach | Pos danach | E Gegner | A Gegner | Gegnermaske danach | Punkte danach |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 84 | 193 | 1,0,0 | 193 | an | 20,12 | 168 | 1,0,0 | an | 19:129 |
| 85 | 193 | 1,0,0 | 191 | an | 20,11 | 172 | 1,0,0 | an | 23:129 |
| 86 | 191 | 0,0,0 | 190 | an | 20,11 | 175 | 1,0,0 | an | 28:130 |
| 87 | 190 | 5,-6,-6 | 152 | an | 20,11 | 177 | 4,0,0 | an | 33:130 |
| 88 | 152 | 0,0,0 | 140 | an | 20,11 | 178 | 1,0,0 | an | 39:131 |
| 89 | 140 | 5,0,1 | – | aus | 20,11 | 169 | 1,0,0 | an | 45:132 |
| 90 | – | 0,0,0 | – | aus | 20,11 | 140 | 4,0,0 | an | 51:132 |
| 91 | – | 0,0,0 | – | aus | 20,11 | 138 | 4,0,0 | an | 57:132 |
| 92 | – | 0,0,0 | – | aus | 20,11 | 140 | 1,0,0 | an | 63:132 |
| 93 | – | 0,0,0 | 100 | an | 0,0 | 139 | 1,0,0 | an | 69:134 |
| 94 | 100 | 3,0,0 | 108 | an | 0,1 | 111 | 5,0,-1 | aus | 75:134 |

### 510862_player_0, t=68, eigene UID 2

Einziger sofortiger Feldverlust unter den 13 engen Kostenindikatoren: eigene Energie45→−21. Gegner UID1 zieht nach oben statt auf das Feld. Im Folgeschritt erscheint derselbe eigene Slot am Spawn. Keine ID-Todeszählung und keine Aufteilung der −66 Nettoenergie in Ursachen.

| t | E eigen | A eigen | E danach | Maske danach | Pos danach | E Gegner | A Gegner | Gegnermaske danach | Punkte danach |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 63 | 144 | 3,0,0 | 141 | an | 21,10 | 121 | 1,0,0 | an | 33:23 |
| 64 | 141 | 3,0,0 | 139 | an | 21,11 | 126 | 1,0,0 | an | 36:24 |
| 65 | 139 | 3,0,0 | 92 | an | 21,12 | 130 | 1,0,0 | an | 39:25 |
| 66 | 92 | 4,0,0 | 62 | an | 20,12 | 82 | 4,0,0 | an | 43:27 |
| 67 | 62 | 3,0,0 | 45 | an | 20,13 | 49 | 4,0,0 | an | 48:28 |
| 68 | 45 | 5,-1,0 | -21 | an | 20,13 | 24 | 1,0,0 | an | 52:30 |
| 69 | -21 | 0,0,0 | 100 | an | 0,0 | 7 | 2,0,0 | an | 56:32 |
| 70 | 100 | 3,0,0 | 92 | an | 0,1 | 7 | 2,0,0 | an | 60:34 |
| 71 | 92 | 3,0,0 | 87 | an | 0,2 | 8 | 3,0,0 | an | 64:36 |
| 72 | 87 | 2,0,0 | 87 | an | 1,2 | 11 | 3,0,0 | an | 68:38 |
| 73 | 87 | 3,0,0 | 94 | an | 1,3 | 15 | 3,0,0 | an | 71:40 |

### 510862_player_0, t=155, eigene UID 10

Finales STAY mit Eintritt: t154 erzwungenes Sap bei Energie94→4; t155 final STAY bei4, Gegner98 zieht auf das Feld. Eigener Slot erscheint sofort am Spawn. Der zeitliche Zusammenhang ist beobachtet; eine SAP→STAY-Änderung bei t154 wurde nicht simuliert, andere gleichzeitige Effekte bleiben unzerlegt.

| t | E eigen | A eigen | E danach | Maske danach | Pos danach | E Gegner | A Gegner | Gegnermaske danach | Punkte danach |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 150 | 108 | 2,0,0 | 107 | an | 13,4 | 154 | 1,0,0 | an | 180:176 |
| 151 | 107 | 2,0,0 | 100 | an | 14,4 | 161 | 4,0,0 | an | 187:181 |
| 152 | 100 | 2,0,0 | 96 | an | 15,4 | 153 | 4,0,0 | an | 195:187 |
| 153 | 96 | 0,0,0 | 94 | an | 15,4 | 149 | 4,0,0 | an | 203:193 |
| 154 | 94 | 5,2,0 | 4 | an | 15,4 | 149 | 4,0,0 | an | 211:199 |
| 155 | 4 | 0,0,0 | 100 | an | 0,0 | 98 | 4,0,0 | an | 217:206 |
| 156 | 100 | 2,0,0 | 99 | an | 1,0 | 74 | 4,0,0 | an | 224:212 |
| 157 | 99 | 2,0,0 | 96 | an | 2,0 | 67 | 4,0,0 | aus | 230:218 |
| 158 | 96 | 3,0,0 | 92 | an | 2,1 | – | 0,0,0 | aus | 237:225 |
| 159 | 92 | 2,0,0 | 86 | an | 3,1 | – | 0,0,0 | aus | 245:231 |
| 160 | 86 | 3,0,0 | 86 | an | 3,2 | – | 0,0,0 | aus | 253:238 |

### 510847_player_1, t=196, eigene UID 4

Finales STAY mit erfolgreicher Folgebesetzung: Energie13 gegen Gegner15 bei move4. SAP ist nicht legal. Gegenkontrolle zeigt das passende Vor-Sap-Energiestadium, ist aber kein randomisierter Vergleich.

| t | E eigen | A eigen | E danach | Maske danach | Pos danach | E Gegner | A Gegner | Gegnermaske danach | Punkte danach |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 191 | 33 | 0,0,0 | 38 | an | 15,14 | 104 | 3,0,0 | an | 208:251 |
| 192 | 38 | 0,0,0 | 43 | an | 15,14 | 107 | 2,0,0 | an | 214:256 |
| 193 | 43 | 5,-3,-1 | 12 | an | 15,14 | 108 | 2,0,0 | an | 219:261 |
| 194 | 12 | 0,0,0 | 17 | an | 15,14 | 48 | 3,0,0 | an | 223:267 |
| 195 | 17 | 0,0,0 | 13 | an | 15,14 | 42 | 2,0,0 | an | 227:272 |
| 196 | 13 | 0,0,0 | 18 | an | 15,14 | 15 | 2,0,0 | aus | 232:277 |
| 197 | 18 | 0,0,0 | 23 | an | 15,14 | – | 0,0,0 | an | 237:282 |
| 198 | 23 | 0,0,0 | 28 | an | 15,14 | 100 | 3,0,0 | an | 243:287 |
| 199 | 28 | 0,0,0 | 33 | an | 15,14 | 95 | 3,0,0 | an | 247:292 |
| 200 | 33 | 0,0,0 | 38 | an | 15,14 | 94 | 3,0,0 | an | 252:297 |
| 201 | 38 | 5,-3,-1 | 3 | an | 15,14 | 95 | 2,0,0 | an | 257:303 |

## H2 als optionale Beobachtung, ohne Patchvorschlag

4.591 eigene Unit-Schritte haben legale SAP-Maske und mindestens einen sichtbaren nichtnegativen Gegner im Band `Chebyshev<=R<Manhattan`. Aktionen: 1.118 SAP,450 STAY,3.023 Bewegung;1.311 Kontexte stehen auf bekannten Punktfeldern. 981 der3.023 Bewegungsaktionen führen geometrisch in den Manhattan-Bereich mindestens eines solchen Gegners an dessen Position t;324 davon haben diesen Gegner auch im unmittelbar vorherigen Schritt sichtbar an derselben Position. Das beweist weder dessen nächste Aktion/Stationarität noch sichere Fernposition, Zielwert, vermeidbaren Schaden oder einen Trainingsmangel. Andere Gegner/Splash bleiben möglich. Vollständige Spielnenner stehen unter `h2_counts` im JSON; kein neuer Job und keine Wiederholung von `sap_geometry`.

## Entscheidung: jetzt kein Agentenpatch

**Kein Kollisions-Veto und kein anderer Agentenpatch aus diesem Diagnoseblock.** Die priorisierte H1-Begründung ist durch die eingefrorene Engine widerlegt. Die verbleibenden negativen Energie-/späten Belegungsverläufe sind real beobachtet, aber noch keine hinreichend isolierte Ursache. Frühere negative Reserve-/safe_moves-, `sap_geometry`-, `active_targets`- und V4-Ergebnisse bleiben gültige Grenzen; keine Kombination oder Wiederholung auf Grundlage dieser korrelierten Zählungen.

Der bereits separat festgelegte frühe Curriculumvergleich bei unveränderter V3-Regellogik bleibt ein eigener geplanter Versuch. Diese Beobachtung liefert keinen neuen Wirksamkeitsnachweis dafür und ersetzt ihn nicht durch eine zusätzliche Variante. Für den aktuellen Auftrag ist die minimal gestützte Entscheidung ausdrücklich **kein Agentenpatch**, plus Korrektur des fehlerhaften Mechanismusberichts.

## Reproduzierbarkeit und Quellenhashes

Analyse: `/tmp/sherlock_loss_mechanisms_20261021.py`; maschinenlesbares Ergebnis: `/tmp/sherlock-loss-mechanisms-result-20261021.json`. Das JSON enthält alle20 Spiele/60 Matchverläufe,240 Snapshots,367 relevante forced-/STAY-Nachbarkontexte,13 enge Fünfschritt-Folgeverläufe,Spiel-/Kartennenner,exakte eingefrorene Eingabe-/Ausgabedateihashes und die Prüfresultate. Die Analyse prüft Zählsummen, Ereignis-/Aggregatübereinstimmung, monotonen Trichter,60/240/6060-Struktur und den Hash der fünf tatsächlich gelesenen Quelltexte; alle10 Prüfungen bestehen. Keine erneute vollständige Reproduktions-/Integritätsstudie.

Analyseskript SHA-256: `2690bc6d95746d31c2a6cc14feec192b2a9e11921326265cc781485793705f41`.

- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/agents/sherlock/geometry.py`: `081ffbbfa6b50b8d01b1a2875250ec7c66aa8275a56bb44bc478808df099c9fa` (aktueller gelesener Text identisch zum Freeze).
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/agents/sherlock/main.py`: `4b53d516485649736f049728f88be1e666e0229c54de59f0819ff8fb353da457` (aktueller gelesener Text identisch zum Freeze).
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/scripts/observe_loss_mechanisms.py`: `2fab40331acc220cf0cfac30641ffb55eff8951f1903625390bbc69f9b1d8a06` (aktueller gelesener Text identisch zum Freeze).
- `/Users/moayedshawesh/Desktop/KI/sherlock-counterplay/scripts/scoring.py`: `963ba7785483f1b707e589d3023011f1a869ef65cd4fc064d0b0b44df309aaa0` (aktueller gelesener Text identisch zum Freeze).
- `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/lib/python3.13/site-packages/luxai_s3/env.py`: `cc1b2657e1b56df21ec890bc78eab75539575e16529b8b8e5a1e8d1b4865a469` (aktueller gelesener Text identisch zum Freeze).

- Eingabe `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/agents/sherlock/weights/agent_p0.pth`: `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`.
- Eingabe `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/compare/autonomous_20261020/v4_independent_20261021/fresh_v3.csv`: `71705b366a6012ff56285fd6dfb7964365e6e711439d37f33a6e2875dbdd44e2`.
