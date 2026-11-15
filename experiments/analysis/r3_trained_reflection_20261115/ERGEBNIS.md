# Spiegelung beim Nachtraining verfehlt die Auswahl

Auf den 24 von R3 tatsächlich besuchten Diagnosekarten liefert das mit gespiegelten Beispielen nachtrainierte Netz 436 richtige Lehreraktionsklassen weniger als der ursprüngliche Diagonal-R3. Auf 24 älteren Diagnosekarten sind es 840 weniger. Beide Kartenserien waren vom Training getrennt. Alle drei Netze wurden mit Originalansicht und transponierter Ansicht, gemeinsamer Maske, 70-%-Schwelle und Schutz für V14-Schüsse beurteilt.

| Diagnose | Einheitsentscheidungen | Diagonal-R3 | Unverändert nachtrainierter R8 mit zwei Ansichten | Mit Spiegelung nachtrainiert |
|---|---:|---:|---:|---:|
| R3-Stellungen, 24 Karten auf beiden Sitzen | 160.863 | 109.672 | 110.099 | 109.236 |
| Ältere Stellungen, 24 Karten auf beiden Sitzen | 156.243 | 99.182 | 98.921 | 98.342 |

Gegenüber dem Diagonal-R3 gewinnt der neue Arm auf den R3-Stellungen 1.574 richtige Befehle hinzu und verliert 2.010 vorher richtige. Auf den älteren Stellungen sind es 1.053 gewonnene und 1.893 verlorene Lehrerentscheidungen. An der tatsächlichen Zahl verarbeiteter Beispiele unterscheiden sich die Nachtrainingsarme nicht. Nachgewiesen sind jeweils 1.024 Adam-Schritte, 262.144 identisch gezogene Beispiele einschließlich 225.055 weicher Bewegungsziele und 12.019 Schusszielfelder. Der neue Arm transponierte 512 der 1.024 Minibatches.

Alle vier vorab gesetzten Bedingungen sind verfehlt. Es folgen weder Spielsiegmessungen noch ein Austausch des Kursagenten aus diesem Versuch. Die Übereinstimmung mit dem Lehrer auf gespeicherten Stellungen misst keine Siege gegen Solution oder Kaggle. [Auswahlplan](PLAN.md) · [96 Sitzvergleiche und Nachweise](validation.json)
