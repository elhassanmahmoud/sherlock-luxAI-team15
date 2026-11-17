# Auftrag für Codex (ab 16.11.2026, abends)

Geschrieben von Claude Code auf Mahmouds Wunsch („du kannst ihm immer neue Aufgaben geben“). **Starten nur durch
Moayed.** Der Nachtauftrag vom 15.11. ist vollständig erledigt, danke. Dieser Auftrag ergänzt Mahmouds eigene Läufe
auf dem M5 und doppelt nichts.

## Ausgangslage (16.11., 22:36)

- **Abgabe ist R3** (Moayed, 16.11.): Solution 788/800, Kaggle 12/800 auf 7158000–7158399
  ([Freigabe](../experiments/releases/20261116_r3_finale/README.md)). Daran ändert dieser Auftrag nichts.
- Mahmouds Rechner (Claude Code) arbeitet bis 17.11., 09:00 am **Schüler**: DAgger-Runde 3 (600 Spiele) → v5, danach
  eine neue Eingabe „letzte eigene Bewegung je Einheit“ (v6). Ziel ist die Kaggle-Lücke: Alle drei Finalisten
  gewinnen dort nur 12/800.
- Neu im Repo: `scripts/par_eval.py` versteht `r3zip:PFAD` als Spieler oder Gegner (`scripts/r3_package.py`).
  Damit spielen Messungen das unveränderte R3-Paket. Sechs gespeicherte R3-Spiele gegen Solution wurden exakt
  nachgespielt.

## Rahmen

- **Nicht ändern:** `agents/sherlock/weights/*`, `experiments/releases/20261116_r3_finale/*`, `dist/agent.zip`,
  `Gruppe15.zip`. Keine neue Abgabe ohne ausdrückliches Ja von Mahmoud und Moayed.
- **Heute nicht ändern** (Mahmouds Lauf baut darauf auf): `scripts/imitate.py`, `agents/sherlock/imitation_agent.py`,
  `agents/sherlock/imitation_net.py`, `agents/sherlock/hybrid_agent.py`. Befunde dazu bitte als Datei, nicht als
  Codeänderung.
- **Karten:** Codex nutzt nur **7165000–7165999** und **7173000–7173399**. Reserviert für Mahmoud: Dev C
  7164000–7164099, DAgger ab 7253000, **frische Bestätigung 7159000–7159399** (bis zur Bestätigung von niemandem
  benutzen). Dev A/B und 7158000–7158399 sind für Auswahl/Bestätigung verbraucht.
- M3/8 GB: höchstens so viele Spielprozesse, wie die Durchsatzmessung erlaubt (in der Regel 2–4), kein großes Training.
- Vor jedem Push `git pull --rebase`; Ergebnisse getrennt von Code committen; Einträge im Arbeitsstand ergänzen.

## Aufgaben (in dieser Reihenfolge)

0. **Moayed, bitte zuerst:** das Archiv `experiments/imitation/k3_v4_extra_7172000_400.tar.gz` (59.745.300 Bytes,
   SHA-256 `e1411e3e6d8c155dd2978c40f80f786e336ea881053e1ab7461d0598d4e9f7a7`) per AirDrop oder Drive an Mahmoud
   schicken. Es ist DAgger-Runde-3-Material; Mahmoud trainiert damit den nächsten Schüler. Nicht ins Repo.
1. **R3 gegen weitere Spielweisen (wichtigste Aufgabe).** R3 ist die Abgabe, wurde aber bisher nur gegen Solution,
   Kaggle und V14 gemessen. Bitte R3 (`r3zip:`) auf genau denselben Karten und Gegnern wie die V15/V14-Studien spielen:
   `sol92_sq`, `rush`, `dqn` auf 7170040–7170063 und FT18 sowie Zufall auf den Karten aus
   `experiments/analysis/umbau_20261115/robustness_ft18_random/`, beide Sitze. Frage: Verliert R3 irgendwo Spiele, die
   V15 gewinnt? V14 verlor gegen die quadratische Solution 7/48 und gegen FT18 10/24, V15 keines. Gepaart mit den
   vorhandenen V14-/V15-Tabellen auswerten, Ergebnis nach `experiments/analysis/r3_robustheit_20261116/`.
2. **Präsentation (zählt 33 % der Note).** In `docs/presentation/finale_2711/`:
   a) eine Fragenliste mit kurzen, ehrlichen Antworten für die Fragerunde. Mögliche Fragen: Was ist DAgger? Warum lernt
   ihr von einem fremden Agenten, und ist das erlaubt? Warum R3 und nicht V15? Warum gewinnt keiner gegen Kaggle?
   Was macht das Netz, was die Regeln?
   b) einen Sprechtext für Mahmouds Folien 4–7 in einfacher Sprache mit Zeitangaben (Ziel 5:05 Minuten). Folien
   selbst nicht umbauen, Vorschläge kennzeichnen. Review-Session ist am 20.11.
3. **Code-Review** von `scripts/r3_package.py` und der `r3zip:`-Erweiterung in `scripts/par_eval.py` (nur lesen).
   Sobald Mahmouds v6-Änderungen gepusht sind (Commit-Titel enthält „previous move“), auch diese prüfen:
   Spiegelung für player_1, Matchwechsel, gestorbene/neue Einheiten, Gleichheit zwischen Training und Spiel. Befunde
   als `experiments/analysis/umbau_20261115/v6/REVIEW_CODEX.md`.
4. **Wo verliert der Schüler gegen Kaggle?** Auf den 400 Spielen aus `k3_v4_extra_7172000` (Lehrer hat dort jede
   Entscheidung des v4-Schülers beschriftet): In Kampflagen (sichtbarer Gegner höchstens 3 Felder entfernt)
   vergleichen, wie oft und wie v4 vom Lehrer abweicht (Bewegung statt Schuss, falsche Richtung, Stehenbleiben), und
   in welchem Match die Einheiten sterben. Nur Analyse, keine Regeln. Ergebnis nach
   `experiments/analysis/umbau_20261115/dagger_zusatz/kampfdiagnose/`.
5. *Optional, sobald Mahmoud `experiments/candidates/umbau_20261116/student_v5.pth` gepusht hat:* DAgger-Daten mit
   v5 (Schalter wie bei v4: `imit_stay_bias=1.5`, `imit_unstack=true`) auf **7173000–7173399** sammeln, gleiches
   Verfahren und Format wie `k3_v4_extra_7172000`. Nur sammeln, nicht trainieren; Archiv mit Prüfsumme wieder an
   Mahmoud.

## Nicht tun

Keine Übernahme oder Änderung der Abgabe, keine Wiederholung abgeschlossener Studien, keine Nutzung der für Mahmoud
reservierten Karten, kein Training mit Millionen Entscheidungen auf dem M3.

## Nachtrag 17.11.2026 morgens (Claude Code nach der Nacht auf dem M5)

**Stand:** R3 bleibt die Abgabe. Kein Schüler war gegen Solution und Kaggle sicher besser als R3, weder auf Dev A noch
auf den neuen Karten Dev C. Das reine Ensemble aus v7 und v7L gewann aber auf Dev C **192/200 direkt gegen R3**.
Nach DAgger-Runde 5 lag der beste Hybrid (Ensemble v8 + v8L) auf Dev C bei +1,75 Prozentpunkten über R3, knapp unter
der vorab festgelegten Schwelle von +2. Alles Weitere steht im [Morgenbericht](MORGENBERICHT_20261117.md). Die Aufgaben 0–4 gelten weiter. Änderungen:

- **Zu 2 (Präsentation):** In die Fragenliste bitte auch diese Frage aufnehmen: „Euer Netz schlägt euren eigenen Agenten
  192 von 200 Mal. Warum gebt ihr es nicht ab?“ Antwort: Gegen Solution und Kaggle war es nicht besser, und dort messen
  wir die Stärke gegen fremde Gegner ([Dev C](../experiments/analysis/umbau_20261115/devC/ERGEBNIS.md)).
- **Zu 3 (Code-Review):** Die v6-Änderung ist gepusht (`8324845`). Zusätzlich bitte die beiden Auswertewerkzeuge
  `experiments/analysis/umbau_20261115/tools/compare_dev.py` und `offline_eval.py` lesen und prüfen. Befunde wie oben als
  Datei.
- **5 entfällt:** Mahmouds M5 sammelt 600 DAgger-Spiele in 10 Minuten. Auf dem M3 lohnt sich das nicht.
- **Karten:** Dev C (7164000–7164099), 7253000–7255599 (DAgger 4/5 und frische Prüfspiele) sind jetzt verbraucht.
  7159000–7159399 bleibt für eine Bestätigung reserviert.
- Ab 17.11., 09:00 laufen auf Mahmouds Rechner keine Prozesse mehr. Die Dateien unter „Heute nicht ändern“ bitte
  trotzdem nur nach Absprache mit Mahmoud ändern.
