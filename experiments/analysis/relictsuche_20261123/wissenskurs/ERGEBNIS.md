# Punktewissen läuft im unveränderten Kursrunner

Das gesonderte Forschungspaket lädt den Spieler als `Gruppe15.main.Agent_x`. Beide Sitzpositionen verwenden dieselbe Datei `Gruppe15/agent.pth` mit den ursprünglichen V16-Gewichten. Die zusätzlich verwendeten Punktegleichungen benötigen nur die öffentlichen Beobachtungen. Der Paketbau wurde mit dem Kurslader sowohl im Projektstamm als auch im Unterordner für Agenten geprüft.

| Umgebung | Ganze Spiele | Geprüfte Einheitenbefehle | Sichere Zusatzfelder auf den vier Sitzen |
|---|---:|---:|---:|
| Python 3.10.15 | 4 | 19.392 | 0, 0, 1, 1 |
| Python 3.13.13 | 4 | 19.392 | 0, 0, 1, 1 |

Der Kursrunner spielte dieselben beiden Normalsicht-Sitze und zwei getrennte aktive Sicht-1-Sitze gegen Solution. Jeder eingereichte Befehl der 16 Schiffe entsprach der zuvor gespeicherten tatsächlichen Partie. Als Player 1 durchlief Sherlock zusätzlich die 303 Kurs-Aufrufe für das Training und den anschließenden Speichervorgang. Alle Gewichtsprüfsummen stimmten auch danach mit V16 überein.

SHA-256 des Forschungspakets: `27154906b12e7a138f9c4e119aca7908881f0b49de502fce8397535b46510518`. Dieses Paket liegt getrennt von der Abgabe. [Paketidentität](paket.json) · [Aktives Spiel auf Python 3.10](kurs310_162640041_player_1.json) · [Aktives Spiel auf Python 3.13](kurs313_162640062_player_0.json)
