# Wann der Grafikchip des M3 hilft

Bei einem einzelnen Spielzug war die gemeinsam berechnete CPU-Auswertung der 36 Netze rund doppelt so schnell wie der Grafikchip. Sobald 64 bereits beobachtete Spielstellungen gemeinsam ausgewertet wurden, erreichte der Grafikchip das 2,93-Fache des CPU-Durchsatzes. Das betrifft die Vorwärtsrechnung mit denselben Gewichten; weitere Züge eines laufenden Spiels hängen von der vorherigen Entscheidung ab. Für Archivanalysen können dagegen viele unabhängige Stellungen gleichzeitig vorliegen.

| Zusammengefasste Stellungen | CPU | Metal-GPU | GPU-Durchsatz relativ zur CPU |
|---:|---:|---:|---:|
| 1 | 0,473 s | 0,944 s | 0,50× |
| 16 | 0,207 s | 0,192 s | 1,08× |
| 64 | 0,233 s | 0,080 s | 2,93× |

Jede Tabellenzeile verarbeitet dieselben 450 aufgezeichneten Spielstellungen in vier Messwiederholungen je Gerät. Der Median schließt die Übertragung der Merkmale zur GPU und der sechs Bewertungen zurück zur CPU ein. Die CPU verwendete einen Torch-Thread, auf beiden Geräten wurden die 36 Netze schichtweise gebündelt. Einheiten desselben Zuges wurden gemeinsam ausgewertet.

Auf allen 1.800 archivierten Stellungen und 19.230 Einheitsentscheidungen stimmte die beste zulässige GPU-Aktion mit dem ursprünglichen V14 überein. Der maximale Betrag der Q-Wert-Abweichung betrug 0,00001145. Für die Ausführung einer kompletten Partie auf dem Grafikchip wurde keine Parität gemessen. [Messungen, Version und Hashes](mps.json) · [Messprogramm](mps_probe.py) · [Ausgangsvergleich für die CPU](ERGEBNIS.md)
