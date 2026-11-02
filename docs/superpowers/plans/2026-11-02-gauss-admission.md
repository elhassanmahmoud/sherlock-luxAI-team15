# Neuer Gauß-Admissionplan · 02./03.11.2026

**Nur heutiger technischer Auftrag, noch kein Job/Code gestartet.** Kein Wiederaufleben der alten No-nominee-Klausel, kein Nachrücken nach CONTROL und kein Stärken-/Trainings-/Mergeauftrag. Root dispatcht erst nach Toolreview und freiem Worker. Aktuell kein Modelljob dieses Plans: Root reserviert die Rechenkapazität für die Trace-Vollsuite.

## 1. Feste Quelle und Umfang

- Prototyp: `sherlock-november-followup`, Basis `307b1ed2051cb9b1a339f849f4322630f5dca7b9`; stabile Referenz: primärer Checkout `384dad2b5a077f5ab026f63c5c8a2d944bc51776`. Dessen importierter Runtimecode muss bytegleich zu `3a7e7825b614a30bc85c7895a38e6b9fc62efdd5` sein; tatsächlichen HEAD erfassen. Root friert beide während aller168Spiele ein.
- Genau V14: SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`, 36Netze,79Features,6Aktionen, train=False/epsilon0/Autosaveaus. Fehlende/falsche Gewichte hart ablehnen, kein zufälliges Ersatznetz und kein Update.
- Ein Modellworker für diesen Ablauf; Root kann einen zweiten anderweitig vergeben. Akkuarbeit erlaubt: unter35% keine neue lange Phase, bei25% eigene schwere Jobs sichern/beenden; AC hebt diese Grenzen auf. Kein Volltest parallel.
- Solver unverändert:400Records,16physischeTiles/Record, vollständigeKomponente≤24Variablen/40Zeilen,4096Zellupdates,8Versuche/Match mit8Beobachtungen Abstand.256Bit gelten für Eingabe-/gespeicherte Matrixwerte; explizite Fraction-Produkte sind wie im Review nur strukturell begrenzt. Kein adaptives Budget/Wallclocklimit im Solver.

## 2. Tool- und Quellguard vor jedem Engine-Spiel

- `probe_overlap.py` ist Quellenreferenz, kein unverändert neu zu startender Job. Neues externes Admissionwerkzeug: zwei Quellen, getrennte V/A/G-Geschichten, Vorher-Unbekanntheit, komplette Aktionspassivität und nachgelagerte Wahrheit implementieren.
- Je Quelle ein **frischer Subprozess mit genau dieser ausgewählten Modulwurzel**; Skript außerhalb der Checkouts oder in einem neu gepinnten Followup-Analyseordner. Keine Crossimports, niemals beide `agents.*`-Versionen über denselben Modulcache. Importpfade prüfen und die Bytegleichheit sämtlicher Referenz-Agenten-/Spiel-/Gegnerhilfen zu3a belegen; tatsächlichen Ausführungs-HEAD384dad2 nennen. Die Performance-Trace-Implementierung bleibt separat.
- Beide tatsächlichen HEADs, externeTooldatei, Agent/Belief/Exact/Config/Geometry/Features, Gegner/common/scoring, echte Engine/Interpreter/Versionen, Schlüsselmanifest und V14 vorab hashen; nach jeder Phase unverändert prüfen. Integration erst außerhalb des Freeze.
- Beide handelnden Agenten: V14-Inferenzconfig, overlap=False/gauss=False. Nach realem Laden Architektur/geladeneTensoren/36Netze und beide Flags am Agenten **und** Belief prüfen. Keine Orakelkonfiguration.
- Nur neue reine Werkzeugtests: unabhängige mutableBeliefs, Beobachtungsidempotenz/Reset, nativeActions, P1-Spiegelung, Vorher/Nachher-Neuheit, Truthfehlorientierung, Quellenbruch, fehlendesModell. Die37unveränderten Solver-/Belieftests und Mikrobenchmark nicht blind wiederholen.

## 3. StufeC: Default-off real prüfen · acht bekannte Spiele

Fixe verbrauchte Schlüssel: `(831006,P1),(831029,P0),(831042,P0),(831043,P1)`, jeweils einmal Referenz und einmal Prototype-default-off, sequenziell gegen Solution92. **8vollständige Spiele**, keine Kartensuche.

Je Spiel nativeAktionsbytes mit Shape/Dtype und Reihenfolge,303Übergänge,300frischeNichtreset-/3Resetbeobachtungen, Match-/Spielsiege und Punkttotalev2 speichern. Gleiche Engine-/Agentenkonstruktorseeds und Gegnerresetlogik. Aktions-SHA und Ergebnisse müssen exakt zwischen Quellen und zu den bekannten Benchmarkwerten passen; Gaußversuche des handelnden Prototyps=0.

**Fehler→Stop vor840er-Spielen:** jeder Aktions-/Ergebnis-/Stepunterschied, falschesModell, Inputbruch oder unvollständigerBlock. Gleiche Siege allein beweisen keine Passivität.

## 4. StufeS: realer V14 mit drei Beliefs · 160 Diagnose-Spiele

Nur nach bestandenemC:40fixe Diagnosekarten **840000–840039**, beide Seiten, also80eindeutigeSchlüssel, jeweils384dad2-Referenz mit bytegleichem3a-Runtimecode und Prototype-default-off mitShadows. **160vollständige Spiele**, einWorker, proSchlüsselReferenz/Shadow nacheinander; Reihenfolge seedaufsteigend,P0/P1. Kein zusätzlicher Gegner, keine A-/G-Siegquoten.

Alle80Paare müssen nativeAktions-SHA,303/300/3 und Ergebnis/v2Punkte exakt reproduzieren. So wird Passivität für alle Diagnoseschlüssel geprüft, statt sie aus vier Rauchtests zu extrapolieren.

Nach jedem normalen `new_game`, **vor erster Beobachtung und vor Wrapperanbringung**, zwei vollständige unabhängige Kopien des zurückgesetzten V-Beliefs erstellen:

| Geschichte | overlap | gauss | Rolle |
|---|---:|---:|---|
|V|false|false|echt handelnder Originalagent|
|A|true|false|Overlap, eigene Records/Markierungen|
|G|false|true|Gauß, eigene Records/Markierungen/Budgets|

Alle anderen Schalter/Team/Kanonisierung/Sensorradius gleich. Keine gemeinsame Arrays/Records/Caches und keine Klone aus V nach einzelnen Beobachtungen. Matchresets mit bestehenden Regeln an alle weiterreichen; zusätzlicheG-Positive dürfen zwischen Matches regulär erhalten bleiben. Nur Spielreset erzeugt neue Kopien. KeinA+G-Bündel.

## 5. Richtiger Zeitpunkt: vor V sichern, nach fertiger Aktion validieren

Pro frischerBeobachtungt: V/A/G-Punkt-/Nullmengen **vor** jeder Verarbeitung sichern; öffentlicheObs separat fürA/G kopieren. OriginalV.observe exakt einmal im vorhandenen Aufruf ausführen, danach A.observe/G.observe auf ihren eigenen Obs-Kopien. Nachzustände/Attempts sichern. Kein extraact/forward/RNG/_enemy_stationary-Aufruf.

Der reguläre Agent.act muss erst vollständig fertig werden. **Erst danach**, außerhalb Agent/Belief, Wahrheit aus dem noch nicht weitergeschalteten env.state(obs_t) lesen und fertige Fakten prüfen; dann env.step. Nicht Wahrheit ausobs_t+1 verwenden. Ein existierender idempotenter observe-Aufruf ruft nur das Original auf und zählt keine weitere Shadowbeobachtung. Resetframes separat, kein Informationsfortschritt.

Für jeden Typk=point/dead gilt unveränderlich:

```text
newG_k = G_post_k − G_pre_k
unknownV_pre = alleTiles − (V_pre_point ∪ V_pre_dead)
extra_current_k = newG_k ∩ unknownV_pre
strict_increment_k = extra_current_k
                     − (V_post_point ∪ V_post_dead ∪ A_post_point ∪ A_post_dead)
```

Damit zählt kein vor aktuellerV-Inferenz bereits bekanntes Tile als G-Erfindung; gleichzeitigeV/A-Schlüsse sind kein Vorsprung. Gegentypkonflikte separat melden. Persistierende Zusatzfakten geben Fact-Steps, werden nicht jedesMal als neu abgeleitet gezählt. Primär unterschiedliche `(seed,side,acquisition_match,tile,kind)` mit strict_increment zählen, Karten/Spiele getrennt.

Zusätzlich A−V,G−V,G−A und Gegenrichtungen berichten; keine Obermengenannahme. Vorlauf aus tatsächlichen Erstkenntniszeitreihen; ohne Nachholen zensiert. Nullwissen nicht über Regimewechsel verlängern, positiveCarryovers markieren. Kein erfundener Zeitgewinn aus Endständen.

## 6. Wahrheit und unabhängiger Rohbeleg

Nur reine `oracle_probe.truth_maps`-Abbildung, niemals `inject_truth`. Vorab kleine reineFixtures für aktuelleRelicmaske/Punktfeldschwelle und Antidiagonal-P1-Spiegelung. FalscheTruthabbildung→ungültig. Truth erst nachAktionswahl kanonisieren und in separatem Objekt halten; nichts anAgent/Context/Masken/Reward zurückgeben.

Neue wie persistierende G-/A-Zusatzfakten gegen Truth prüfen; vorhandene V-Falschzustände getrennt dokumentieren. **Jeder falscheG-Zusatzfakt verwirft G**, unabhängig von vermuteter Ursache. AlteV-Fehler sind keine neueG-Information.

ProSpiel Gzip-JSONL streamen: Framekey, V/A/G-pre/post-Punkt/Nullmengen, Reset-/Attemptstatus, getrennteTruth undZeitwerte. Für24×24zulässig: packbits-Hex mit festem `x*24+y`, explizitemBitorder und576Bits; Roundtrip/Spiegelung vorher testen. AlleNeuheit/Vorwissen/Truth/Fact-Step-Zahlen müssen aus Rohdaten unabhängig nachzählbar sein, nicht nur Aggregatsummen. NativeAktions-SHAs und303/300/3/v2-Ergebnisse zusätzlich speichern.

## 7. Feste Kosten-, Stop- und Abschlussregeln

- StufeS höchstens30minWandzeit; vollständigen160erBlock mit Reserve vorab zulassen. LetzteDiagnosen kosteten grob5s/Spiel→ca13min plus Shadow/I/O. Bei langsamerer Vorabmessung keinen still verkürzten Block beginnen.
- V/A/G.observe CPU(`process_time_ns`) undWall(`perf_counter_ns`) separat auf300frischenNichtresetframes/Spiel messen; Kopien/Setup/Truth/Serialisierung/act getrennt. FesteV/A/G-Reihenfolge und Scheduling als Messgrenzen nennen.
- TechnischerBudgetvorschlag, vorDispatch fest: G-Observe-CPU P95≤5ms,Max≤15ms; ZusatzCPU(G−V) P95≤5ms. Wallmedian/P95/Max offen ausweisen. Kein behaupteter harterEchtzeitbeweis; Shadow ist keine vollständige aktivierteG-Agentenlatenz.
- TatsächlicheAttemptzuwächse/Abstände/Matchreset nachzählen. `{}` unterscheidet intern keine Budget-/Oversize-/Widerspruchsgründe; ohne geprüfte Instrumentierung keine solchen Abbruchzahlen erfinden.
- Fehler/FalseFact/Mutation/Aktionsabweichung/fehlenderKey/Quellbruch/Deadline/25%-Akku→eigeneJobs kontrolliert sichern/beenden, Block`incomplete/rejected`. Kein Timeout, der innerhalb einerAbleitung nur andereFakten zurückliefert.
- **Technisch verwerfen:** irgendeinSafety-/Daten-/Budgetgate verletzt oder kein strikter sichererG-Mehrwert gegenüber `V ∪ A`. Seeds/Budgets/Definition nicht nachErgebnis lockern.
- **Technisch bestanden, noch kein Stärkekandidat:** vollständige168Spiele(C8+S160), alleGuards bestanden und mindestens ein strikter sichererG-Fakt. Häufigkeit/Point-vsDead/Vorsprung/Gegenrichtungen berichten; Root kann seltenen oder praktisch irrelevanten Mehrwert ohneLeistungsstudie verwerfen.
- Erst danach eigener frischer Leistungsnachtrag, echterG-aktivierter Rauch-/Latenzcheck und technische Freigabe. Kein automatischerMerge/Abgabetausch, keine Kombination mitTargeting/Training und keine Beeinflussung der vergangenenStudie.

UnabhängigeEndabnahme: vollständigeSchlüssel/Actbytes/303/300/3/v2, Rohfaktspuren einschließlich **Unbekanntheit vor aktuellerV-Inferenz**, Truth, Timing-/Attemptnenner und Vorher/Nachherhashes. Heute wurde nur dieserPlan geschrieben; keinTool implementiert, keinModell geladen und keine840erKarte gespielt.


## Operativer Root-Nachtrag vor Implementierung/Spielen

Root autorisiert heute ausschließlich die technische Umsetzung/Prüfung dieses
Plans. Referenz bleibt primary384dad2, bis C und S vollständig geschlossen sind;
Performance-Toolarbeit ist davon getrennt. Tatsächlicher Prototyp-HEAD wird nach
Toolcommit neu gepinnt, statt307b1ed als später ausgeführten HEAD auszugeben.

Effiziente Importisolation: pro Stufe ein eigener Referenz-Kindprozess mit allen
Schlüsseln, danach ein eigener Prototype-Kindprozess mit denselben Schlüsseln.
So entstehen vier getrennte Kindprozesse insgesamt (C4+4, S80+80), keine168
Torch-Neuimporte. Alle Paare/Schlüssel bleiben identisch; Vergleich nach jeder
Stufe vollständig, keine parallelen Modellworker dieses Plans. Dies ersetzt nur
„pro Schlüssel unmittelbar nacheinander“, keine Mess-/Abnahmebedingung.

Die unveränderten37Solverfälle nicht als separate Zusatzrunde wiederholen.
Ein gemeinsamer Volltest nach neuem Werkzeug ist wegen des neuen Codes sinnvoll,
Root koordiniert ihn ohne andere Modelljobs. Fokus auf neue Verhaltenstests.
Sicherheits-/Kostenwerte im Plan sind fest, insbesondere CPU5/15ms und30min fürS.

Import-Nachtrag vor C/S: Der primäre Checkout enthält fremde unversionierte
Python-Dateikopien, die der breite `agents/__init__.py`-Discovery importieren würde.
Beide Kinder dürfen stattdessen eine ausdrücklich geprüfte Namespace mit exakt
dem ausgewählten `agents`-Pfad bootstrappen, ohne den reinen Discovery-Initializer
auszuführen. Alle direkt geladenen Module bleiben gewöhnliche gepinnte Imports;
Namespacepfad und tatsächlich importierte Dateien weiter streng prüfen. Die
fremden Dateien bleiben unangetastet. C muss weiterhin die alten Ergebnisse und
neuen nativen Referenzhashes exakt reproduzieren; keine Lockerung des Quellguards.
