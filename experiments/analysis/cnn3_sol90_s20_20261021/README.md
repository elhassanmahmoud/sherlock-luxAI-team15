# Begrenzte CNN3-Fortsetzung: kein neuer Abgabekandidat

21.10.2026, Codex mit Moayed. Fester [Vorabplan](../../../docs/superpowers/plans/2026-10-21-cnn3-bounded-continuation.md), eingefrorener Quellstand `47388d4c7196d3ef90714e23045164f9c80348bf`. **V3 bleibt unverändert.**

## Ergebnis auf bekannten Entwicklungskarten

60 Karten **500720–500779**, beide Seiten, je 120 Spiele pro Gegner:

| Stand | Solution: Siege / Remis / Niederlagen | default |
|---|---:|---:|
| V3, vorhandene geprüfte Referenz | 102 / 0 / 18 | 120 / 0 / 0 |
| Original-CNN3 PPO60, neu gespielt | 96 / 0 / 24 | 120 / 0 / 0 |
| Einziger finaler Fortsetzungsstand | **89 / 0 / 31** | 120 / 0 / 0 |

Fortsetzung gegenüber PPO60: **−5,83 Prozentpunkte**, gepaartes 95%-Kartenintervall **[−15,83; +3,33]**. Gegenüber V3: **−10,83 pp [−20; −2,5]**. Die bekannten Karten sind Entwicklungsdaten. Es gibt keinen nachgewiesenen Vorteil; der negative Vergleich widerlegt nicht grundsätzlich CNN/PPO oder andere Trainingskonfigurationen.

Vorgegebenes Gate: mindestens 108 Solution-Siege, strikt mehr als PPO60 und 120 default-Siege. Die beiden Solution-Bedingungen sind verfehlt. **Kein Direktvergleich, keine Kurs-Adapterentwicklung, keine frischen Bestätigungsspiele, keine Verlängerung und keine Auswahl eines Zwischenstands.** Der Endstand wird nicht übernommen. Die reservierten Karten 523000–523399 wurden in diesem Versuch nicht verwendet.

## Tatsächlich durchgeführtes Training

- Start vom letzten Original-PPO60, kein ausgewählter PPO50-Stand. Warmstart von Policy/Critic mit frischem Adam; kein exaktes Resume des ursprünglichen Optimizers.
- Zehn vollständige Iterationen × 24 Spiele = **240 Trainingsspiele**, **120 verschiedene Karten** aus Teilblöcken 550024–550251. Fester Seed 20; tatsächlich 211 Solution- und 29 Default-Gegner. Keine Teacher-Spiele.
- **837.246 aufgezeichnete Einheitenschritte**, Prozessdauer **2.330,80 Sekunden / 38:50 Minuten**. Ein Rolloutworker auf Moayeds Mac. Keine parallelen Modelljobs.
- Architektur 79 Merkmale/6 Aktionen, CNN 48 Kanäle/4 Blöcke und effektive Agent-Konfiguration erhalten. `detach_value` war schon im Ausgangsstand aktiv.30 von32 gespeicherten Policy-Tensoren änderten sich; alle sind endlich, die Ladeprüfung reproduziert sämtliche finalen Tensoren exakt.
- Minibatch 256 statt des historischen 4096 und frischer Optimizer verändern die Optimierung. Dieser einzelne Kandidatenvergleich isoliert deshalb weder den Gegner-Mix noch eine einzelne Trainingsentscheidung kausal. Kein weiterer Kontrolltrainer wurde dafür behauptet.

Trainingseinstellungen und genaue Seed/Gegnerfolge: Vorabplan und [training_schedule.csv](training_schedule.csv). Zehn Trainingszeilen samt Herkunftsdatei unter [Laufverzeichnis](../../ppo/cnn3_sol90_s20_20261021/); `.pth`-Rohcheckpoints bleiben gemäß Repo-Regel lokal. Finaler lokaler Pfad: `experiments/ppo/cnn3_sol90_s20_20261021/ppo_0010.pth`.

## Prüfungen und Umfang

**724 neue registrierte Spiele:** 240 Training + 240 Original-PPO60-Referenz + 4 V3-Kontrollen + 240 Endstand-Auswertung. Die 240 historischen V3-Referenzspiele werden nicht erneut als neue Spiele gezählt. Zusätzlich ausgeführte Softwaretests sind keine Benchmarkspiele.

Alle neuen Evaluationszeilen sind vollständig und eindeutig, mit Punktezählversion 2, 303 Schritten, endlichen konsistenten Ergebnissen und `invalid_frac=0`. Vier V3-Kontrollen reproduzieren sämtliche 23 gespeicherten Nichtzeitfelder der passenden historischen Zeilen; das ist kein Nachweis vollständiger Trajektorienidentität. Methodik: echte Siege gegen feste Gegner, Remis separat; 5.000 gepaarte Ziehungen ganzer Karten einschließlich beider Seiten, NumPy-Seed 0, Perzentilintervall.

Der schmale PPO-Zufallsfix vor Beginn wurde mit 8 fokussierten Tests und der damaligen Gesamtsuite 489 Tests plus 14 Untertests geprüft. Ursprünglich sechs neue Tests fehlgeschlagen, danach alle acht bestanden. Die Quellen-/Gewichtskontrolle und Prozessbegrenzung blieben während des gesamten Versuchs aktiv. Kein Paket-/Kurs-Stärketest des unterlegenen Endstands wurde durchgeführt.

Nachweise: [results.json](results.json), [training_check.json](training_check.json), [V3-Reproduktion](v3_reproduction.json), [Root-Nachrechnung](root_reproduction.json), Ausführungszustand und Roh-CSV/Logs. Der [unabhängige Abschlussreview](final_audit.md) bestätigt die CSV-, Hash- und Rechenprüfungen; Tensorprüfungen stammen aus der gesonderten Root-Verifikation. Der Ausführungszustand wurde danach als abgeschlossen markiert. CSV-Dateien behalten durch lokale `.gitattributes` ihre Originalbytes und damit die dokumentierten Hashes.

## Identität und Fortsetzung

- OriginalPPO60: `0efe4d39c8b2c8e56d4877e208b6064fc3766b9c486f83c6f82407cf11fb0bef`.
- Finaler Versuch: `d044fced91a887842cdb39f4540246038796b63fdc41c87bce8f270db4298e28`.
- Beide V3-Abgabegewichte unverändert: `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`.
- Alte Sechser-Sicherung unverändert: `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

Mahmoud hat während dieses Laufs einen getrennten positiven Entwicklungsbefund für `art_sap`, Mindesttreffer 3, veröffentlicht. Ein eigener [Bestätigungsplan](../../../docs/superpowers/plans/2026-10-21-art-sap-confirmation.md) prüft diesen unverändert definierten Kandidaten nach dem sicheren Phasenübergang. Das setzt dieses CNN-Training nicht fort und übernimmt dessen Quellen nicht nachträglich. Mahmouds laufende Gefahr-Merkmale-/PPO-Studien bleiben unabhängig.
