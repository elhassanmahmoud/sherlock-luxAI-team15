# Unabhängige Gauß-Datenabnahme · 02.11.2026

**Datenabnahme ACCEPTED; technische Admission bestanden; praktische Routinghürde NICHT bestanden.** 1.318.342 unabhängige Prüfungen,0 Fehler. Keine Stärken-, Merge- oder Abgabefreigabe. V14 bleibt durch diesen Befund unverändert.

## Vollständigkeit und Bindung

- Exakt **C8+S160=168** vollständige Spiele: C vier feste verbrauchte Schlüssel×zwei Quellen; S40 Karten840000–840039×beide Seiten×zwei Quellen. Je Spiel303 Rohframes=300 frische Entscheidungen+3 Resets; S-Prototyp damit24.000 frische Shadowentscheidungen. Die gesamte Fortsetzungsperiode hat nach den separat protokollierten26 früheren Trace-/Integrationsspielen194 tatsächliche Spiele; Tests sind darin keine Vollspiele.
- Alle84 Quellenpaare: native Aktionsbytes beider Teams einschließlich Dtype/Shape/Reihenfolge neu dekodiert und vollständig neu gehasht, exakte Hash-/Outcome-/v2-Punkteparität. C reproduziert zusätzlich den gepinnten historischen CSV-Ausgang. V-pre/post- und Truth-Verläufe ebenfalls quellenübergreifend identisch.
- Manifest/Phasenschlüssel, Start-/Endseals, Vollständigkeit der Ergebnis-/Timing-/Rohdateien, Supervisorabschluss/Exit0 und unveränderte Eingaben geprüft. Referenz tatsächlich384dad2, Prototyp969cc31; alle gepinnten Runtimebytes gegen tatsächlichen Git-HEAD und feste Basen3a7e782/307b1ed geprüft. V14 SHA98a07350…d3d8 unverändert.
- Vier Ladebelege über C/S und beide Quellen: jeweils identische36 Tensorhashes,79 Features/6 Aktionen, Evaluation/epsilon0/Autosaveaus, handelnde Overlap-/Gaußflags aus. Gewöhnliche direkt geladene Module stammen aus der jeweils ausgewählten Wurzel, Engineimporte aus dem gepinnten Paket. Kein Modell erneut geladen.
- C-Envelope38,2s; S-Envelope638,5s (13:25:34,982–13:36:13,465UTC). Der innere S-Phasentimer beträgt625,1s und liegt unter1800s; der Envelope umfasst zusätzlich die vorausgehende C-/Quellenprüfung. Die C-basierte Vollblockreserve ist eingehalten.

## Tatsächliche Neuheit und Vorlauf

**Genau4 strikte neue Fakten gegenüber V∪A:2 positive und2 Nullfelder.** Alle im selben Frame: Karte840011,player_0,erstes Match,Beobachtung80. Positive Weltkoordinaten(2,14),(9,21); Nullfelder(1,14),(9,22). Alle vier waren vor der aktuellen V-Inferenz unbekannt und nach derselben V-/A-Inferenz weiterhin unbekannt. V und A holen sämtliche vier bei Beobachtung81 nach: **jeweils ein beobachteter Schritt Vorsprung**.

Damit1/80 Spiele=1,25%,1/40 Karten=2,5%,ein Erwerbsframe unter24.000 Entscheidungen. Für jede der4 Fakten wurden V und A getrennt verfolgt:4/4 beobachtete V-Vorläufe und4/4 beobachtete A-Vorläufe,jeweils1;0 zensierte Fälle. Das Audit weist offene Enden andernfalls je Rolle separat administrativ oder nach Nullwissen-Regimewechsel/Verlust aus. Es wird kein nur unter nachgeholten Fällen berechneter Mittelwert als allgemeiner Vorsprung ausgegeben.

G hatte gegenüber V29 zusätzliche positive und26 zusätzliche Null-Fakt-Schritte. Gegenüber A waren es nur2/2; A hatte umgekehrt86 positive/168 Null-Fakt-Schritte, die G fehlten. Es besteht keine Obermengenannahme. Die für das Routing maßgebliche positive G-Überlegenheit über **V∪A beträgt2 physische Feld-Schritte**, einschließlich persistierender Vorteile je Entscheidungsframe; nicht29 und nicht die vielen gleichzeitigen normalen G-/V-Schlüsse.

Keine falschen Zusatzfakten von G oder A in frischen Frames; auch Reset-Zusatzfakten0 falsch.946 vorhandene V-Falsch-Fakt-Schritte sind separat ausgewiesen und werden weder als neue G-Information noch als zusätzliche G-Fehler ausgegeben. Die Wahrheitsprüfung verwendet die gespeicherte nachgelagerte kanonische Truth samt geprüfter Quellbindung; keine zweite versteckte Enginehistorie wurde erzeugt.

## Solver und Zeitbudget

161 echte G-Versuche in240 Matchverläufen; beobachtetes Maximum4/Match unter Cap8. Zwischen tatsächlich aufeinanderfolgenden Versuchen8–54 frische Beobachtungen; alle Counterkontinuitäten/Resetzustände und Mindestabstand8 geprüft. Keine nicht beobachtbaren Abbruchursachen aus dem leeren Solverergebnis erfunden.

Globale Quantile aus **allen24.000 frischen Einzelmessungen**, keine Mittelung von Spielquantilen:

| Messung | Median | P95 | Maximum |
|---|---:|---:|---:|
| G.observe CPU |0,048ms|0,092ms|0,704ms|
| G−V.observe CPU |−0,017ms|−0,010ms|0,616ms|
| G.observe Wall |0,048958ms|0,093375ms|1,321250ms|

CPU-Gates P95≤5ms/Maximum≤15ms und Zusatz-P95≤5ms bestanden. Negative Differenz ist bei fester V/A/G-Reihenfolge und gemeinsamem Warmzustand **kein Beleg für einen schnelleren aktivierten G-Agenten**. Gesamte aktive G-Agentenlatenz/Stärke wurde hier nicht gemessen.

## Vorab festgelegte praktische Route

Die Weltkoordinaten-Entdoppelung und Nenner wurden um **13:34:36UTC** ausdrücklich festgehalten, vor S-Abschluss und bevor Root oder dieses Audit S-Ausgänge/Neuheit gelesen haben. P1 wird per Antidiagonale in echte Weltkoordinaten zurückgeführt; positives physisches Fakt ist `(seed,world_x,world_y,point)`,über Seiten und Erwerbsmatches nur einmal.

| Festes Gate | Tatsächlich | Ergebnis |
|---|---:|---|
| Technische Admission inklusive≥1 strengem sicheren Fakt |4 Fakten,alleGuards|PASS|
|≥20 strikte positive physische Fakten |2 (auch2 per-Spiel-/Erwerbsfakten)|FAIL|
|≥5 erwerbende Spiele |1|FAIL|
|≥3 erwerbende Karten |1|FAIL|
|≥100 positive Vorteil-Feld-Schritte über V∪A |2|FAIL|

**Gauß erfüllt damit die heutige praktische Alternativroute nicht.** Keine Hürde wurde gelockert; kein Siegtest/Intervall wurde aus dieser Diagnose abgeleitet. Ein anderer Pilot braucht den bereits geforderten eigenen festen Nachtrag.

Nachvollziehbar mit `python3 -B /tmp/sherlock-continue-20261102/gauss_independent_audit.py --out NEUE_DATEI.json`; liest ausschließlich geschlossene Evidenz und verwendet keine Repoimporte. Skript/Pin/JSON liegen neben diesem Bericht. Geprüfte Originalauswertung wurde nur zum abschließenden Vergleich gelesen, nicht aufgerufen oder importiert.

Ausschließlich Standardbibliothek und Read-only-Git-/Dateizugriffe; keine Modelle, Spiele,pytest,Subagents oder Repositoryänderungen. Historische Korrektur vermerkt: die frühere CSV-/Manifest-Suche bewies keine frischen Trainings-/Prefillkarten; seed29-Prefill495000–495003 war bereits im Arbeitsstand erfasst. Das berührt keine841+-Holdoutkarten und autorisiert kein Training.

Ergebnis-JSON SHA256: `7ab4a1187c64f572fa8a932988e11d2652013762959b59d72132afde6cda00d1`.
