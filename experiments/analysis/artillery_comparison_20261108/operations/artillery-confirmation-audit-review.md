# Statischer Review des Bestätigungs-Auditors

**Urteil: PASS_STATIC — kein blockierender Befund.** Der geprüfte Entwurf entspricht der festgelegten einmaligen Bestätigung. Das ist weder eine Ausführungsprüfung noch eine Abnahme zukünftiger Bestätigungsergebnisse. Auditor, Syntaxprüfung, Tests, Modelle und Spiele wurden nicht ausgeführt; ausschließlich Quellen, vorhandene abgeschlossene Auswahlmetadaten und kleine Dateihashes gelesen. Keine Repositoryänderung.

## Geprüfte Fassung

- `/tmp/artillery-confirmation-audit.py`: SHA-256 `bb40f83eb52cea1b4e2bcc0252d3a39b52b8cad7217942f14d73e05ee20817d6`.
- `/tmp/artillery-confirmation-audit-README.md`: SHA-256 `b3cd7cab76b8e0a5a62a526ca2450d0a630fb70d301e478481f93cba9978a904`.
- Vorliegende Root-Pins: SHA-256 `5c4ab2ddef762222576e8f0d2777445b1628cdcb87b253a2c00dff9467755187`; gelesen, nicht neu erzeugt oder freigegeben.

Verglichen mit `docs/superpowers/specs/2026-11-08-artillery-comparison.md`, zugehörigem Plan sowie `scripts/artillery_alignment_compare.py`, `artillery_alignment_eval.py`, `ensemble_diversity_compare.py`, `ensemble_diversity_eval_supervisor.py`, `league_gates.py` und `compare_report.py`.

## Wesentliche Prüfergebnisse

1. **Auswahl und Vertrauensanker:** Auditor Zeilen 36–57 und 108–151 verlangt separat übergebenen Root-Pindateihash, `approved=True`, festen HEAD `70669eb9e1509b1bddff902c22a2b7e394167f97`, genau V14 und den angenommenen Nominierten. Auswahlaudit, Summary, vollständige elf CSVs/Receipts und ihre bestehende Eingabekette bleiben gebunden. Die fünf Auswahlbedingungen und Rangfolge werden aus bereits akzeptierten Ganzzahlzählern erneut geprüft; keine statistische Vermischung mit Bestätigung. Der tatsächlich vorhandene Auswahlaudit ist PASS/440/ALIGNED38. Seine Kopie im Repository hat denselben SHA-256 `8d0d2afe29bf5726509e467606a6f8ac2fffd01c8312f3b2340af65e881edc55` wie `/tmp/artillery-selection-audit.json`. Die Root-Quellenidentität stimmt exakt mit seiner akzeptierten Identität überein.

2. **Keine ungeprüften zukünftigen Werte:** Die 112 aktuellen Root-Dateipins enthalten keine Bestätigungsergebnisdateien und keinen zukünftigen Bestätigungs-Launch. Summary und Plan sind getrennte Vertrauensgegenstände: der vorhandene nach Auswahl erzeugte Bestätigungsplan hat den erwarteten Hash `007fea35e36039510a76d0aa542543badbd6cd3fb4075ab2e166ac300682c6d7`. Spätere State-/Provenance-/CSV-Werte werden gegen die vorab gebundenen Modelle, Quellen, Pläne und Befehle geprüft, bevor Statistik beginnt. Der statische Review hat nicht sämtliche 112 großen Dateien erneut gehasht; das bleibt Prüfung des späteren Auditors.

3. **Exakt 600 Spiele:** Zeilen 153–158, 194–231 erzwingen 14 Paneljobs plus einen Direktjob, jeweils exakt 40 eindeutige Gegner/Karte/Seite-Schlüssel. V14 und ALIGNED38 spielen LOCAL_SIX plus default auf 9801000–9801019; nur ALIGNED38 spielt direkt gegen V14 auf 9801100–9801119. Weder CONTROL38 als dritte Bestätigungsrolle noch zusätzliche CSVs/Receipts sind zulässig. Vollständigkeit, Endzustand, Exit0, Originalbefehle, Hashes und Ergebnisarithmetik werden vor allen Berechnungen geprüft.

4. **Unabhängige zehn Gates und Kartenintervalle:** Zeilen 235–270 berechnen aus CSVs eigene Kartenmittel, Halbsiege, W/D/L, strikte Siege und alle sieben unveränderten Hauptbedingungen plus drei Schutzbedingungen. Kein Import der Projektstatistik. Ganze Karten mit beiden Seiten und sechs Panelgegnern bilden je einen Cluster; 5000 Ziehungen mit explizitem PCG64(0), 95%-Perzentilen, gleiche Grenztoleranz 1e-9. Direktkarten bleiben getrennt. Der zusätzliche Defaultschutz erfordert 40/40 strikte Siege. Struktur und Zahlen werden anschließend vollständig mit der Produktionssummary verglichen.

5. **Abschluss und Ergebnisbedeutung:** Zeilen 161–179 und 277–291 verlangen vollständige Beendigung einschließlich eigener Prozessgruppen, explizites Abschlusssignal, unveränderte Quellen/Eingaben sowie exklusiv neue Ausgaben. `status=PASS` bezeichnet Daten-/Statistikprüfung; `passed` bezeichnet separat alle zehn Leistungsbedingungen. README erhält die Grenzen: nur 20 Kartencluster, unadjustierte Intervalle, zwei Trainingsstarts, kein TD-/Kausalnachweis und keine automatische Promotion.

## Offene Prüfung

Die spätere reale Ausführung bleibt bis vollständigen 600 Daten, beendeten Prozessen und Root-Freigabe gesperrt. Dabei muss Root genau die geprüften Skriptbytes und seinen separat bestätigten Pindateihash verwenden. Ein späterer Laufzeitfehler oder fehlender Beleg ist ein Abbruchgrund, kein Anlass für neue Spiele oder gelockerte Gates. Die unveränderte Sampled-Target-Stagingfassung wurde in diesem Auftrag nicht bearbeitet.
