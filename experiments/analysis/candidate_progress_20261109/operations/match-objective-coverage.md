# Matchziel und vorhandene Reward-Versuche — Quellencheck

**Ein isolierter Lernversuch mit stärker gewichtetem Matchsieg gegenüber unveränderten dichten Rewards ist in den geprüften Quellen nicht als ausgeführt oder geschlossen belegt.** Matchsiege fehlen dem heutigen Reward allerdings nicht: sie liefern bereits einmalig±2 pro Einheit. Die bekannten negativen Reward-Studien prüften andere Änderungen. Vier verlorene Partien mit höheren Gesamtpunkten sind daher ein Anlass zur Prüfung der Gewichtung, kein Nachweis ihrer Ursache.

## Tatsächlicher aktueller Reward

Für eine vorher vorhandene Einheit `u`, `n=max(1, Anzahl vorheriger eigener Einheiten)` und `ΔW=Δeigene Matchsiege−Δgegnerische Matchsiege` gilt bei `use_shaping=True`:

```
B = [w_explore·min(neu_erkundet/20, 1)
     + w_discovery·neu_bewiesene_Punkte
     − w_opp_points·gegnerischer_Punktzuwachs] / n

r_u = B + w_match·ΔW
      + falls überlebt:
          w_point·I[Eigentümer eines bekannten Punktfelds im Folgezustand]
          − w_stack·I[redundant auf bekanntem Punktfeld]
          + w_energy·(E'−E)/400
          + w_shape·(γ·φ'−φ)
        sonst:
          −w_death [zusätzlich −w_shape·φ nur bei terminal_death_potential]
      + falls finale Aktion SAP:
          w_sap_hit·(+1 bei hits>0, sonst−1)·max(1,hits)
```

`φ=−10·Manhattanabstand zum zugewiesenen Ziel/(W+H)`. Mit `reward_fix=True` liefern negative Energien keinen Punktebonus, erkannter Tod/Respawn beendet die Einheit und am Matchende wird `φ'=0`. Der optionale Fog-Neutral-Schalter unterdrückt nur den letzten SAP-Term bei dokumentiert unbekanntem Trefferstatus. Quellen: [reward.py:89](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/reward.py:89), [Hauptformel:106](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/reward.py:106).

Aktuelle Standardgewichte: Punkt1, Match2, Zielpotential0,5, Erkundung0,3, Entdeckung0,5, Energie0,1, Tod0,5, Stack0,3, SAP0,3; Gegnerpunkte0, γ0,99 ([Config](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/config.py:496)). Ein Halter kann somit **jeden Schritt+1** bekommen, der Matchausgang nur **einmal±2**; der Matchterm wird nicht durch `n` geteilt. Ein SAP-Kostenabzug38 trägt im Energieanteil lediglich−0,0095 bei; der geschätzte einzelne Treffer trägt+0,3 bei. Das sind Termgrößen, keine gemessene Ursache einer Entscheidung. Die Punktebelohnung verwendet bekannte produktive Feldbelegung, nicht unmittelbar die gesamte Spielpunktzahl oder deren Gewinnmarge.

**Kein zusätzlicher Spielgewinnbonus:** Der an `update` übergebene Engine-Reward wird nicht als weiteres Lernsignal verwendet. Tod, Matchgrenze und Spielende setzen `done=True`; `y=r+(1−done)γQ_target`. Dadurch wird ein zusätzlicher Bonus erst am ganzen Spielende nicht automatisch durch frühere Matchgrenzen zurückpropagiert ([main.py:1583](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/main.py:1583)). Das bestehende Signal bewertet einzelne Matchausgänge, nicht gesondert die Mehrheit der drei Matches.

**Kein Punktevorsprung-Potential und kein allgemeines Reward-Clipping:** Das Potential ist Zielentfernung. Nur der Erkundungsanteil ist gedeckelt; Huber-Loss und Gradientennorm-Clipping sind keine Reward-Begrenzung. Das Merkmal `point_diff=tanh((own_points−opp_points)/20)` sowie gedeckelte eigene Punkte sind Eingabemerkmale, kein Reward-Potential ([features.py:742](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/features.py:742)). `use_shaping=False` behält Punkt+Match unverändert bei und ist daher kein reines Matchziel.

## Was wirklich geprüft wurde

| Versuch | Tatsächlicher Umfang/Befund und Abgrenzung |
|---|---|
|`no_shaping`,10.10.|Drei Trainingsstarts à3000 Spiele; gegenüber`full` Solution−16,7pp [−28,9;−5,6], default−32,8pp. Entfernt alle zusätzlichen Terme, **behält Punkt1 und Match2**. Kein isolierter Matchgewichtsvergleich. [Ergebnis](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/docs/ERGEBNISSE_20261010.md:43).|
|Gegnerpunkte bestrafen,19./20.10.|DQN`opp6`: `w_opp_points=1` **zusammen mit Gegnerpool**,68% statt74% gegen Solution,−6pp [−14;+2]; Rewardeffekt nicht isoliert. PPO`cnn2c`: nur dieses Rewardgewicht geändert,78/78/75/77% gegenüber80% am Start; kein Gewinn. [DQN](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/docs/ARBEITSSTAND.md:2374), [PPO](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/docs/ARBEITSSTAND.md:2291). Es geht um Gegnerpunktzuwachs, nicht um terminalen Spielsieg.|
|„Terminal“-Pilot,20.10.|Gepaarte frische Netze, je400 Trainings-/240 Auswertungsspiele; `terminal_death_potential=True` verliert gegen Kontrolle bei Solution−23,33pp [−34,17;−13,33]; Stopregel, keine größere Replikation. Das korrigiert `−w_shape·φ` beim **Einheitentod**, keine Erhöhung von`w_match` und keinen Spielbonus. [Bericht](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/autonomous_20261020/reward_pilot_analysis.md:1).|
|Schüler/SAP0,04.11.|S30-Paar und später zwei A2-Paare entfernen ausschließlich den SAP-Treffer-/Fehlschussterm. Kein V14-Nachfolger, kein abgesicherter SAP0-Vorteil; andere Rewardgewichte bleiben gleich. [S30](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/docs/SCHUELERNETZ_REWARD_20261104.md:45), [A2](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/docs/AKTIONSSCHUELER_20261104.md:49).|
|Fog-Neutral,08.11.|Nur unbekannter Fog-SAP-Hit-Term neutral, übrige Rewards unverändert; technisch abgeschlossen, keine erfolgreiche Nominierung. Kein Matchzielvergleich. [Ergebnis](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/fog_comparison_20261108/ERGEBNIS.md:1).|

Die alte Fehlverwendung kumulierter Matchsiege als wiederholter Bonus wurde laut10.10.-Bericht **vor** dem dortigen Batch korrigiert; sie ist keine heutige offene Änderung. Das aktuelle Inferenzconfig beschreibt außerdem nicht automatisch den Trainingsreward aller36 historischen Mitglieder: bereits die ursprünglichen`opp`-Quellnetze wurden mit Gegnerpunktstrafe trainiert ([Herkunftsgrenze](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/docs/NAECHSTER_TRAININGSVERSUCH_20261021.md:36)). Keine Modellarchive wurden für diesen Check geöffnet.

## Genau eine verbliebene, klar getrennte Hypothese

**Die relative Gewichtung des bereits vorhandenen terminalen Matchsignals (`w_match`) isoliert erhöhen, während sämtliche dichten Reward-Terme und Abschlussregeln gleich bleiben.** Dafür fand die begrenzte Suche in aktuellem Agent-/Trainingscode, Experimentprotokoll, Arbeitsstand und archivierten Reward-/Schülerplänen keinen ausgeführten Vergleich. Das wäre eine Gewichtungshypothese, weder ein bewiesener Fehler noch schon „nur auf Matchsiege lernen“. Ein neuer Game-Bonus, Punktevorsprung-Potential, Reward-Clipping oder erneutes Abschalten des gesamten Shapings sind ausdrücklich nicht Teil dieser einen offenen Abgrenzung. Keine Zahl, Versuchsanordnung oder Startfreigabe wird hier festgelegt.

Read-only abgeschlossen unter Quelle`c023b28bd4369ffc1c32b5347fb8574bdd42c472`. Keine aktuellen Vergleichsergebnisse zur Variantenwahl gelesen; keine neuen Pläne, Implementierungen, Tests, Spiele oder Trainings. „Nicht gefunden“ bezieht sich auf die genannten Quellen, nicht auf unbeobachtete externe Arbeit.
