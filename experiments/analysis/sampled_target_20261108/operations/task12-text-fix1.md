# Enger Fix nach statischem Task-1/2-Review

08.11.2026. Ausschließlich externe Textänderungen gemäß Root-Auftrag während der laufenden 600er-Bestätigung. Grundlage: `/tmp/sampled-target-implementation-review.md`. Die ursprüngliche `IMPLEMENTATION.md` bleibt als historischer Stand erhalten; aktuelle Reviewfassung ist diese Fixfassung.

**Drei gezielte Änderungen:**

- Test Zeile 242 erwartet jetzt die tatsächliche Antidiagonalspiegelung 1→2 und 2→1. Agent-/Core-Geometrie unverändert.
- Bundle-Load Zeilen 556–581 verlangt nach mindestens einem Lernupdate einen vollständigen Adam-State für sämtliche gebundenen Parameter mit `step`, `exp_avg` und `exp_avg_sq`. `step` muss skalar, endlich, nichtnegativ und exakt gleich `learn_steps` sein. Fehlende Pflichtfelder werden schon vor dem temporären Optimizer-Load abgefangen; fehlende/zusätzliche Parameterzustände danach, weiterhin vor jeder Mutation des Zielagenten. Moment-Tensor-, Shape-, Dtype- und Endlichkeitsprüfungen bleiben erhalten. Bei null Updates wird nur der frische leere Adam-State zugelassen.
- Learner Zeilen 461–462 zählt positive und negative nichtterminale `sampled_y-control_y`-Differenzen getrennt. Bestehende Summen, Targets, Batch, Sampling, Forward-Aufrufe und Lernreihenfolge unverändert.

**Tests zuerst als Text ergänzt:** neun beschädigte Adam-Varianten mit neu korrekt gebundenen äußeren Dateihashes; Prüfung unveränderter Q-/Target-/Optimizer-/Replay-/Zählerzustände bei Ablehnung; positiver Inspektionsreload sowohl vor als auch nach einem Update. Der neue Telemetrietest enthält positive, negative, Null- und Terminalfälle in einem festen Batch und erwartet trotz sich aufhebender Summe je einen positiven/negativen Fall.

**Tatsächliche Prüfung:** ausschließlich Quellen-/Textsichtung, Zeilenzählung und Dateihashes. Kein Python, Import, Compile, NumPy/Torch-Aufruf, pytest, Modell, Forward oder Spiel ausgeführt. Sämtliche Tests bleiben **UNRUN**, RED/GREEN unbeobachtet. Keine Funktionsbehauptung und keine Freigabe für Studie/Training. Keine Repo-, HEAD-, Gewichts-, Seed-, Runner- oder Supervisoränderung.

Für die unabhängige Nachprüfung eingefroren:

- `/tmp/sampled-target-staging/scripts/sampled_target_agent.py` — 590 Zeilen; SHA-256 `c767ee07a6fcf9566e762e105eec36a3b51e44664cb1b4b77e82d93ddd414bf9`.
- `/tmp/sampled-target-staging/tests/test_sampled_target_agent.py` — 548 Zeilen; SHA-256 `020819bc80df0b1ff81d4c390110bf8ca13fbff84ee74f54636d3625252657eb`.

Geänderte Bereiche: Agent 461–462 und 556–581; Tests 242, 426–450 sowie 489–548. Die weitergehenden Task-3/4-Arbeiten bleiben ausdrücklich außerhalb dieser Vorbereitung.
