# Gefahrmerkmals-Warmstart: Training abgeschlossen

**Beide Lernläufe sind vollständig und technisch geprüft. Eine höhere Spielstärke ist noch nicht belegt.** Die produktive Abgabe bleibt V14. Eingefrorene Trainingsquelle: `af8b2711d37a9fd4509415972345c5849c21db62`.

| Tatsächlicher Umfang | Kontrolle | Gefahrmerkmale |
|---|---:|---:|
| Bekannte technische Ausführungen | 2 | 2 |
| Vorlaufspiele ohne Lernen | 40 | 40 |
| Lernspiele | 400 | 400 |
| Optimizerupdates | 60.000 | 60.000 |
| Gespeicherte finale Replayzeilen | 300.000 | 300.000 |
| Neue Eingabespalten | 22, dauerhaft null | 22, tatsächlich gelernt |

Beide Netze starteten aus demselben V14-Mitglied 18. Die ursprünglichen 79 Spalten und alle übrigen Parameter wurden exakt übernommen, 22 neue Eingabespalten mit null initialisiert. Kontrolle bekommt nur Nullwerte im Zusatzteil, die zweite Variante die bestehenden öffentlichen Gefahrmerkmale. Regeln, Reward, Double-DQN-Lernverfahren, Optimierung, feste Karten und Gegnerpläne sind gleich. Beide Arme hatten einen frischen Optimizer und Replay. Nur der finale Endstand ist vorgesehen; keine Zwischencheckpointwahl.

Trainingskarten 9950000–9950199, jeweils beide Seiten; Vorlauf 9950300–9950319. Vorab festgelegter Gegnergenerator 47, Mischung Solution 60 %, Quadrat-Solution 20 %, default 10 %, rush 10 %. Die tatsächliche begrenzte Mischung steht in den Rohzeilen. Vier bekannte Technikspiele: 831006/player_1 und 831000/player_0 je Arm. Diese Daten sind keine unabhängigen Leistungstests.

## Tatsächlich geprüft

31 synthetische Tests bestanden vor realen Modellen; unabhängiger Code- und Korrekturreview. Alle vier echten Technikspiele bestanden mit identischen nativen Aktionen und Ergebnissen beider 101er-Arme. Nach den zwei Vorläufen je 143.986 tatsächliche Replayzeilen mit identischen ursprünglichen Merkmalen, Aktionen, Belohnungen und Folgemasken. 60.313 aktuelle Zeilen enthalten öffentliche Zusatzinformationen; nur der Merkmalsarm erhielt sie tatsächlich. Root gab die Gradienten danach ausdrücklich frei.

Beide Endstände enthalten 60.000 tatsächliche Adam-Schritte je Parameter, endliche Q-/Target-/Adam-Tensoren und je 400 endliche gemeldete Spielmittelverluste. Kontrollspalten samt Adamzuständen blieben null. Im Merkmalsarm sind neue Spalten und deren Optimizerzustände verändert; alle 60.000 Lernschritte meldeten einen nichtnull Zusatzspaltengradienten. Die finalen gespeicherten Replays bestätigen den Null-/Echtmerkmalskontrast. Beide Q-Netze unterscheiden sich vom Start und voneinander.

[Unabhängiger Vorlaufaudit](operations/prefill-audit-REPORT.md), [unabhängiger Abschlussaudit](operations/final-audit-REPORT.md), [Root-Abschluss vor Quellenfreigabe](operations/closure.json). Der Owner beendete beide Worker mit Exit 0 und prüfte die ursprünglichen Abschlussvalidatoren. Root prüfte zusätzlich ursprüngliche Aufnahme, unveränderte Quellen/Eingaben/Schutzdateien, tatsächliches Prozessende und Belege. Erst anschließend wurde die Quelle für neue Arbeit freigegeben.

Grenzen: Einzelne Batchverluste, Initialtensorarchive und vollständige Rohbeobachtungen wurden nicht archiviert. Entsprechende Laufzeitzähler sind als solche gekennzeichnet. Die finalen Tensoren, Replaydateien, Rohspielzeilen und erhaltenen Replayausschnitte wurden unabhängig nachgerechnet. Eine einzige gepaarte Initialisierung belegt weder allgemeinen Methodennutzen noch bessere Turnierleistung.

## Modelle und gemeinsame Daten

- [Kontrolle](training_v1/control/final.pth), SHA-256 `bcb00242b1b73429c72deb556e5a74fb3386aab288bea02f21f538398af34994`.
- [Gefahrmerkmale](training_v1/threat/final.pth), SHA-256 `2acf88f8dedbb1eb060ff4ebc3a4b365dc022ef2d0bb8ecf41dfe60883819c93`.
- Beide enthalten ein einzelnes 101er-Netz, Target und Optimizer; noch keine neue 36er-Abgabe.
- Alle vier großen Vorlauf-/Endreplays sind verlustfrei als `.npz.gz` unter [archives](archives/manifest.json) erhalten. Insgesamt etwa 58 MB statt 737 MB unkomprimiert. Root hat jede Datei vollständig entpackt und den ursprünglichen SHA-256 nachgerechnet. Die unkomprimierten Originale bleiben lokal, werden aber nicht zusätzlich versioniert.
- Rohlogs und Quellen-/Pfadbindungen stammen vom tatsächlichen Mac-Lauf. Andere Rechner benötigen angepasste Pfadbindungen für neue Aufnahmen; die relativen Archivpfade und Originalhashes erlauben die Wiederherstellung derselben Daten.

Beide V14-Gewichte unverändert SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; ZIP unverändert `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Kein V14-Ersatz oder Leistungsnachschlag aus diesem Bericht. Der nächste getrennte Schritt ist die kleine, vorab festgelegte Prüfung der finalen Mitglieder im 36er-Ensemble gegen V14 und die Kontrolle.
