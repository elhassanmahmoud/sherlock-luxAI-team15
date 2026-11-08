# Statischer Review: Sampled-Target-Agent, Task 1/2

**CHANGES REQUESTED – zwei konkrete Korrekturen vor technischer Abnahme.** Die zentrale Folgeaktions-/Replay-Methode ist statisch schlüssig. Kein Python, Import, Syntaxcompile, Test, Modell oder Spiel wurde ausgeführt; sämtliche Laufzeitnachweise bleiben **UNRUN**. Keine Repo- oder Implementierungsdatei geändert, keine laufenden Auswahlresultate gelesen. Dieser Bericht ist keine Start- oder Laufzeitfreigabe.

Geprüfte, während des Reviews unveränderte Fassung:

- `/tmp/sampled-target-staging/scripts/sampled_target_agent.py`: `fd0e94a695f4e06b4fedfe43c27d37e91b31a97e9b2458405958fd9427217391`.
- `/tmp/sampled-target-staging/tests/test_sampled_target_agent.py`: `52014754a8f3ab50566c26af7502ffc6ae18dbcebe03b56065b150a7c6133f89`.
- Maßstab: korrigierte `/tmp/sampled-target-pilot-spec-draft.md`, `/tmp/sampled-target-pilot-plan-draft.md` und enge externe Vorbereitungsfreigabe. Produktionsquellen nur gelesen.

## P2 – Spiegelungsfixture verwendet die falsche geometrische Abbildung

**Datei:** `tests/test_sampled_target_agent.py:242` (Testkörper 243–254).

Die beiden positiven Fälle `(True, 1, 3)` und `(True, 2, 4)` erwarten eine 180°-Drehung. Der tatsächliche Core spiegelt an der Antidiagonalen: `agents/sherlock/geometry.py:30` definiert `MIRROR_DIR = [0, 2, 1, 4, 3]`; deshalb gilt 1→2 und 2→1. Die Agentprüfung in `sampled_target_agent.py:388–389` ruft den richtigen Corehelper auf und wird diese beiden Fixtures abweisen. Das ist aus den Konstanten statisch ableitbar, kein beobachtetes Testergebnis.

**Enge Korrektur:** erwartete native Richtungen auf die tatsächliche Antidiagonalspiegelung ändern; optional die übrigen Richtungen in denselben parametrisierten Test aufnehmen. Den richtigen Agentcode nicht an die falsche Fixture anpassen. Vorhandener SAP-Test 301–311 prüft einen eingereichten SAP außerhalb der Netzmaske, aber keinen gespiegelten SAP-Vektor; seine Aussage entsprechend begrenzt lassen oder den bereits geplanten Mirror-SAP-Fall gezielt ergänzen.

## P2 – Bundle-Preflight akzeptiert unvollständigen Adam-Zustand trotz Lernupdates

**Datei:** `scripts/sampled_target_agent.py:553–564`, vor der Live-Mutation 566–570.

Der temporäre Optimizer-Load, Endlichkeitsprüfung und die erlaubte Schlüsselteilmenge reichen nicht für die zugesicherte strikte Persistenz. Ein Checkpoint mit `learn_steps > 0`, passender Parameterguppenstruktur, aber leerem `opt['state']` passiert diese Schleifen vollständig. Ebenso passiert pro Parameter ein Zustand mit lediglich `step`, aber ohne `exp_avg`/`exp_avg_sq`: `set(values) <= {...}` erlaubt gerade das Weglassen der Pflichtfelder, und die Momentprüfungen sind nur `if name in values`.

Das Verhalten ist zusätzlich lesend im installierten Torch nachvollzogen: `torch/optim/optimizer.py:1018–1042` installiert die gelieferten Stateeinträge; `torch/optim/adam.py:115–138` ergänzt keine fehlenden Momente und lässt leere States zu. Ein äußerer SHA bindet die gelieferten Bytes, beweist aber nicht ihre Vollständigkeit. Damit kann dieser Load ein unvollständiges Lernartefakt akzeptieren und anschließend den frischen Agent mutieren. Wegen der Inspektionssperre wird daraus kein unerlaubter Resume; es verletzt dennoch den beanspruchten Abschluss-/Reloadnachweis.

**Enge Korrektur:** vor jeglicher Live-Mutation für den festen Pilot-Adam bei `learn_steps > 0` vollständige Zustände für die gebundenen Parameter und die Pflichtfelder `step`, `exp_avg`, `exp_avg_sq` verlangen; den skalaren, endlichen, nichtnegativen und zum gespeicherten Lernfortschritt passenden Step prüfen. Für `learn_steps == 0` den tatsächlich frischen Zustand zulassen. Vorhandene Shape-/Dtype-/Finiteheitsprüfungen behalten. Ein gezielter Bundle-Negativtest sollte fehlenden Gesamtstate, fehlendes Moment und falschen Step nach gültig neu gebundenen äußeren Dateihashes vor Mutation abweisen; die bisherigen Tests 441–459 decken nur Arm/Mode/Dateihash ab und erreichen diese semantische Prüfung nicht.

## Kleine verbleibende Spec-Lücke: Richtung der Targetdifferenz

`sampled_target_agent.py:454–461` erfasst Anzahl verschiedener Indizes/Targets, vorzeichenbehaftete Gesamtsumme, Maskenfälle und Altersumme. Die Spec verlangt außerdem eine Zählung der Vorzeichen der Targetdifferenzen. Positive und negative Fälle können sich derzeit in `target_delta_sum` aufheben. Zwei zusätzliche deskriptive Zähler für positive/negative nichtterminale Differenzen im bereits vorhandenen Batch würden die zugesagte Telemetrie vervollständigen, ohne RNG, Forwards oder Methode zu ändern. Das ist kein festgestellter Fehler des TD-Targets und keine neue Studienanforderung.

## Statisch tragfähige Teile und tatsächliche Grenzen

- **Bestätigte Folgeaktionslabels:** `attach_successor` 172–189 prüft Episode/Match/Schritt/UID sowie bytegleiche tatsächlich verwendete Features und Masken; die ganze native Ausgabe wird gesichert. `_update` 411–423 bestätigt ursprüngliche Beobachtung, native Ausgabe und Zähler, bevor der vorherige Batch in Originalreihenfolge freigegeben wird. Im vorhandenen `common.play_game` liegt dieser Aufruf nach erfolgreichem `env.step`. Es wird korrekt nur der eingereichte Befehl belegt, keine Enginewirkung.
- **Verzögerter Commit:** Der alte Batch wird vor genau einem Parent-update committet. Dessen neue Pushes werden nur gesammelt; der Parent-Lernschritt sieht ausschließlich fertige alte Zeilen. Vollständig terminale neue Batches werden erst nach Parent-update committet, gemischte gemeinsam zurückgehalten. Derselbe Ablauf gilt für beide Modi. Terminale `-1`-Labels werden im Sampled-Pfad nie gegathert.
- **No-op/Matchgrenzen:** Bei leeren Aktionen wird `finish_capture(None)` verwendet, ohne alten Cache als Nachfolger auszuwerten. Bei nichtleeren Captures prüft der Abschluss den nächsten Kontextschritt; nichtterminale Zeilen müssen im gleichen Core-Match bleiben. Core-`done` bleibt maßgeblich, keine neue Survivalheuristik. Die bekannte nicht erkannte nahe Respawnidentität wird nicht fälschlich repariert oder garantiert.
- **Zeitbezug:** `env_steps` wird vor dem Folge-act gesichert und erst durch Parent-update erhöht. Das Metadatum wird beim Commit unverändert übernommen; Lernalter wird mit dem aktuellen Zähler ermittelt. Der einfache Test 268–274 prüft die gespeicherten Werte, der echte Parent-Update-Test 277–298 deckt den unmittelbaren Lernzeitpunkt ab; tatsächliche Ergebnisse noch offen.
- **Core/RNG:** `_act`, `_decide`, Reward und der Parent-update-Body bleiben geerbt. `_act_est`/`_update` enthalten je einen Parent-Aufruf. Kein globaler Monkeypatch im Modul und kein zusätzlicher Samplingzug: beide Targetformeln nutzen denselben Batch mit einmaligem `rng.integers`. Produktions-QNet hat keine stochastische Forwardkomponente. Keine statisch sichtbare neue Verhaltensregel.
- **Control-Parität:** Die DDQN-Formel, Huber-Loss, Zero-grad/Backward/Clip/Adam-Reihenfolge, Lernzähler, Lossliste und Targetsync entsprechen dem Core. Geplante Tests 385–405 vergleichen Parameter/Target/Adam/Loss/RNG sowohl normal als auch an der Sync-Grenze; 408–423 vergleichen beide Modi bei gleichem Argmax-Label. Das ist eine passende geplante Nachrechnung, derzeit kein numerischer PASS.
- **Persistenz:** Ring-/Chronologiespeicherung und alle Zusatzarrays sind indexgleich angelegt. Alte/partielle Schemafelder, fehlende nichtterminale Labels, Pending-Save und direkte Legacyloads werden abgewiesen. Das extern gebundene `pilot_state.json` bindet Gewicht und Replay ohne Selbsthashzirkel. Inspektionsreload verhindert neue Episoden/Lernen; RNG-Fingerprints werden nicht fälschlich als Resumezustand ausgegeben. Die oben genannte Adam-Lücke bleibt zu schließen.

Task 3/4 – verbindliche reale Inputhashes, vollständig gestreamter Eventwriter, Paar-Vorlaufgate, Endreceipts und identische Inferenzkopien beider Direktduellseiten – sind bewusst noch nicht implementiert und gehören nicht zu dieser Task-1/2-Abnahme. Auch nach den engen Korrekturen bleiben Syntax-/Importprüfung und die autorisierte tatsächliche synthetische Testausführung vor jeder Studienentscheidung erforderlich. Keine zusätzliche Studie oder Infrastruktur empfohlen.
