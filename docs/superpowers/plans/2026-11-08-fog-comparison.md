# Fog-Kandidaten begrenzt vergleichen

Spec: [fester Vergleich](../specs/2026-11-08-fog-comparison.md). Vor Ergebnissen unabhängig methodisch geprüft. Training aktuell in anderer Arbeitskopie eingefroren; jetzt keine Python-Dateien/Tests dort ändern.

## Task 1: Schmaler Vergleichsadapter

Nach vollständig akzeptierten vierTrainings: neue `scripts/fog_reward_compare.py` und bei sinnvollerTrennung `scripts/fog_reward_eval.py`, gezielte `tests/test_fog_reward_compare.py`. Bestehende Profile/Trainer nichtändern. HistorischeTrainingsabnahme nachprüfen, genaue38-Netz-Artefakte exklusiv bauen undreloadprüfen. Neue festeRollen/Karten/Gates/Rangfolge derSpec. Bestehende par_eval-Worker, CSV-Validierung, Kartenbootstrap undbewährteSource-/Quota-/OwnedProcess-Helfer weiterverwenden. Keine allgemeine neueFrameworkschicht, kein Überschreiben vorhandenerOutputs.

TDDsynthetisch für exakteMembership/config/hash,unvollständigeoderveränderteArtefakte,440/1200-Planmatrix,Halbsieg-Schwellen/DeterministischeRangfolge,Nur-ein-Nominierter,FailohneNachrücker,vollständigegepaarteCSV,unveränderte7+3Bestätigungsgates,source-/quota-/AC-/STOP-/max2-Prozessguard. Root stelltAudits/Modelle/Protokolle bereit. Keine neuenModellspiele beiImplementation/Tests. KeinPushdurchImplementer; Rootintegriert.

## Task 2: Review und fester Lauf

UnabhängigerCode-/Methodenreview, gezielteTests; Input-/Seed-AuditundQuellcommit vorLauf. Erst440Vorauswahl vollständig, unabhängigprüfen, genaueinenNominierten ausfestenGates/Rangfolge. Wennkeiner:Wellebeenden. Sonstfrische1200Bestätigung,allebestehendenGatesundRohdatenunabhängigprüfen. Höchstens1640Leistungsspiele, keineVerlängerung/Pooling. V14/ZIP bis belegtembesseremKandidatenbytegleich.

## Task 3: Übergabe

TatsächlicheModelle/Spiele/Lernen/Gegner/SiegquotenmitUnsicherheit dokumentieren, keine100%-Garantie. Nomination istkeineFreigabe. NurqualifiziertenNachfolger nachKursprüfung/ReproduktionundSicherung ersetzen. GeprüfteÄnderungen sinnvollpushen undprimärenCheckoutaktuellhalten. VorangegangeneStudienundfremdeDateienerhalten.
