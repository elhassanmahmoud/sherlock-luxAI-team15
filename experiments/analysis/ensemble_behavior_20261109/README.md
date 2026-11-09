# Ensemble-Verhalten im Einzelnetztraining

Neue getrennte Vorbereitung nach geschlossenem MATCH38-Versuch. Noch keine realen Modelle oder Spiele. Zwei ON-Arme mit fester Kontrollrewardformel und gemeinsamer manueller Vorlaufbarriere; die 35 eingefrorenen Netze wirken ausschließlich bei der Trainingshandlung, der eigene DDQN bleibt unverändert.

Methodenreview bestanden; Implementierung und gezielte synthetische Tests laufen separat. Alte Kontrollen werden nur nach tatsächlicher OFF-Reproduktion und Quellenbindung verwendet. Ihre fehlenden vollständigen historischen Bibliotheks-/RNG-Snapshots bleiben eine Beweisgrenze. Keine automatische Ersatzvariante. Der ursprüngliche externe Bauvertrag unter `operations/` ist historisch; seine sequentiellen Starts und sein Fallback sind durch die bindende Spec ausdrücklich verworfen.

[Spec](../../../docs/superpowers/specs/2026-11-09-ensemble-behavior.md), [Plan](../../../docs/superpowers/plans/2026-11-09-ensemble-behavior.md). V14 und Gruppe15.zip unverändert. Kein stärkerer Kandidat behauptet.
