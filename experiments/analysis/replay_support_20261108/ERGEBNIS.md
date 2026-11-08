# Replay-Abdeckung der gespeicherten Endnetzgewinner

**08.11.2026 – Diagnose abgeschlossen und vollständig unabhängig nachgerechnet. Bei 2.019 von 10.000 Bankzeilen war der Endnetzgewinner unter den passenden Replayaktionen nicht beobachtet. Das ist ein beschreibender Befund, kein Nachweis fehlerhafter TD-Targets.**

Gefragt wurde: Findet sich ein gespeicherter Folgezustand `ns` als bytegleiches aktuelles `s` im zugehörigen ursprünglichen Replay, und wurde die vom eigenen Endnetz unter der gespeicherten Maske bevorzugte Aktionsklasse dort tatsächlich gespeichert?

Verwendet wurden ausschließlich die feste 10.000-Zeilen-Bank und gespeicherten Q-Ausgaben der abgeschlossenen Fog-Einflussdiagnose sowie deren vier ursprüngliche Replaypuffer. Je Arm waren es 2.500 Bankzeilen; betrachtet wurde jeweils nur dessen eigenes finales Netz. Es gab keine neuen Spiele, Modellimporte, Netzberechnungen oder Lernupdates.

| Arm | Gewinner beobachtet | Gewinner nicht beobachtet |
|---|---:|---:|
| control41 | 1.959 | 541 |
| neutral41 | 1.992 | 508 |
| control42 | 2.010 | 490 |
| neutral42 | 2.020 | 480 |
| **Gesamt** | **7.981** | **2.019** |

Alle Bankzeilen hatten mindestens einen passenden aktuellen `s`-Treffer: **0 unbekannte Fälle**. Sämtliche ursprünglichen Bankübergänge waren nichtterminal: **0 terminale Bankzeilen**. Die Abdeckung beruht auf nur ein bis zwei passenden aktuellen `s`-Beobachtungen je Bankzeile. „Nicht beobachtet“ bedeutet somit lediglich: Die bevorzugte Klasse fehlt unter diesen wenigen gespeicherten Aktionen. [Originalergebnis](run_v1/summary.json)

Der unabhängige Audit bestand **41.002 Prüfungen**. Er rekonstruierte alle 10.000 Berichtszeilen und ihre Einzelwerte, streamte dafür erneut sämtliche 1.200.000 aktuellen `s`-Zeilen der vier Puffer und prüfte Originalindizes, `ns`, Masken, Terminalwerte und Hashbindungen. Keine Folgeaktion wurde aus `a[i+1]` abgeleitet. [Datenprüfung](data-audit.json)

**Grenzen:** Gleiche 79 Merkmalsbytes beweisen keinen gleichen vollständigen Belief- oder Regelzustand. Die endlichen, teilweise überschriebenen Replaydaten sind korreliert; die Q-Werte stammen von Endnetzen, nicht von den historischen Online-/Target-Netzen. Der Befund beweist weder unmögliche Aktionen noch falsche Q-Werte, historische TD-Fehler oder Stärkeverlust. Beobachtete Gewinner sind ebenso wenig ein Qualitätsnachweis. Off-policy DQN darf andere Aktionen bewerten als die Verhaltenspolicy ausführt.

**Entscheidung:** Die Diagnose bleibt rein deskriptiv; sie löst keine Trainings-, Aktions- oder Netzauswahl aus. Ein Sampled-Target-Pilot mit neu aufgezeichneten Folgebefehlen ist lediglich ein offener Vorschlag und nicht umgesetzt. V14 bleibt unverändert.
