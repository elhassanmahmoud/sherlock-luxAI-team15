# Vorabgleich vor dem ersten Spiel

11.11.2026: Die historische Konfiguration vom 9.11. enthält `cand_stall_rescue` noch nicht. Dieser Schalter kam mit `c023b28`; im eingefrorenen Original aus `021d13e` und im jetzigen V14 ist er False. Nur diese fehlende deaktivierte Option wird beim historischen Schemaabgleich ergänzt. Andere Unterschiede und True bleiben ein Abbruchgrund. Keine historische Datei oder Agentenkonfiguration wird geändert; reale Aktions- und Ergebnisreproduktion bleibt zwingend.

Vor der Aufnahme: Konfigurationsvorprüfung verweigert; außerdem ein CLI-Aufruf mit verkürztem erwarteten Commit vor Anlage des Ausgabeordners verweigert. Beide ohne Spiel-/Engineaufruf, ohne Modellinitialisierung und ohne Ergebnisdateien. Der Erststart erfolgt nach Test und Review mit vollständiger Commit-ID.

Eingriffs-/Runnerreview unabhängig, 150 synthetische/betroffene Tests vor dieser engen Schemaergänzung bestanden. Rohdaten werden erst nach bestandenem finalem Vorabgleich erhoben.
