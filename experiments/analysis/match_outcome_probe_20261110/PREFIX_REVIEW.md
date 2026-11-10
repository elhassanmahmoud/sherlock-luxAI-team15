# Prüfung der einmaligen Prefix-Reparatur vor Start

10.11.2026. Neuer Sammler vollständig von Root gelesen; der Implementierer ließ zusätzlich eine eng begrenzte unabhängige Prüfung durchführen, ohne gemeldeten offenen Befund. Root führte59 gezielte Tests selbst aus, alle bestanden (4,93s). Neue8Tests umfassen den vollständigen zweiphasigen Controller mit synthetischer Umgebung; keine dieser Prüfungen lud Abgabegewichte oder führte echte Spiele aus.

- Frische ursprüngliche Spielhistorie für jede Alternative/Wiederholung; kein Snapshot und keine Änderung am Gegner. `make_opponent` setzt Solution-Globals zurück, anschließend Spiel-/NumPy-/Torch-RNG fest. Ganzer Präfix wird mit verifizierter Baseline verglichen.
- Stockreferenz und Sammler über alle303Frames identisch; Gegenfaktenschnitt erst nach öffentlicher Auswahl, normale Regelkette folgt. Andere Gegneraktion im Eingriffsschritt wird abgewiesen.
- Tatsächlich berechneter Abweichungsframe und beide Vergleichswerte werden vor einem Abbruch gespeichert.
- Jeder Start und jeder Engineaufruf wird vor Ausführung gegen feste Grenzen gezählt. Rückkehr/Archivierung separat;303Schritte eines dritten-Match-Alternativlaufs sind zusätzlich ein vollständiges Spiel, keine verschwiegenen Teilpartien.
- Technische Aufnahme bindet beide Schlüssel, jede Rohdatei, echte Root-Abnahme und unveränderte Quelle. Kein Fortsetzen existierender Outputverzeichnisse oder automatischer Phasenübergang.
- Synthetischer Gesamtdurchlauf:32 Referenz-/Sammelläufe,48Alternativen,8Wiederholungen,20.200Schritte bei Wiederholung des ersten Matches;48vollständige/40kurze Läufe. Das ist ausschließlich ein Zähl-/Controllerbeispiel, kein tatsächliches Agentenergebnis. Feste echte Obergrenze bleibt21.816Schritte.

Noch keine tatsächlichen Prefixspiele zum Zeitpunkt dieses Dokuments. Erst Fehlerkarte11011007/p0 und Kontrolle11011017/p0, danach tatsächliche Abnahme vor Rest. V14/ZIP unverändert.
