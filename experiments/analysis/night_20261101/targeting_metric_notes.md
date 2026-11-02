# Was die 38,1 % ohne Zielzuweisung tatsächlich messen

Reine Quellenprüfung des V14-Diagnosepfads auf Stand `139057f`; Agent, Features und Mechanismusquelle entsprechen weiter diesem Stand. Keine Spiele, Modelle, Tests oder Agentenänderungen. Die separat nachgerechnete Quote **1681 / 4417 = 38,1 %** wird hier definiert, nicht neu als Ursache interpretiert.

**Kurzbefund:** Gezählt werden eigene, im Belief bewiesene Punktefelder ohne eigene oder **sichtbare** gegnerische Unit, deren Koordinate im aktuellen Zielplan nicht vorkommt. „Frei“ bedeutet agentensichtig frei; „zugewiesen“ bedeutet Zielplanung vor Netz-/Regelentscheidung, keine ausgeführte Bewegung. Der Code belegt weder einen veralteten Cache noch eine kausale Zielzuweisungsstörung.

## Zeitpunkt und Nenner

`mechanism_probe.py:250–265` ruft `agent.act(obs_t)` auf, sichert danach den wahren Zustand `s0`, simuliert/führt den Übergang aus und ruft erst danach `classify(agent,s0,...)` auf. Dennoch misst `classify` **den Zustand vor der gerade ausgeführten Aktion**, nicht die neue Belegung nach Bewegung/Tod: Es verlangt `_cache[0] == s0['steps']` und liest genau diesen Kontext (`:143–160`). Reset-Schritte werden ausgelassen (`:262–263`).

`main.py:300–316` aktualisiert zuerst den Belief mit obs_t; `_decide` baut danach Kontext, Zielzuweisung, Features, Sapziele und Masken und speichert sie mit der aktuellen Step-ID (`main.py:237–258`). In dieser Diagnose gibt es zwischen Aktion und Klassifikation keinen weiteren `agent.observe/update`-Aufruf. Damit ist dies kein belegter Nachlauf um einen Beobachtungsschritt. Dass der Diagnoseaufruf nach `env.step` steht, macht den verwendeten Cache nicht zum Nach-Aktionszustand.

Formal für jeden gezählten Schritt t:

```text
F_t = {bekanntes Punktefeld (x,y): x+y<=23,
       keine eigene Unit im Kontext, keine sichtbare gegnerische Unit im Kontext}
U_t = {Feld aus F_t: Feldkoordinate kommt in keinem ctx['assigned'] vor}
Quote = Summe_t |U_t| / Summe_t |F_t| = 1681 / 4417
```

Gezählt wird nur über die zwölf verlorenen Matches der gezielten Diagnose. Es sind **Feld-Schritte**, keine verschiedenen Felder, Units, Aktionen oder verpassten Punkte. `own_half` schließt hier die Diagonale x+y=23 ein (`mechanism_probe.py:153,181–189`); die getrennte Matchbelegungsmessung in `analyze_losses.py:49–50` verwendet eine strikt getrennte Hälfte. Beide Halbzählungen sind deshalb nicht identisch.

## Grenzen von „frei“ und „zugewiesen“

| Begriff | Konkrete Quelle und Bedeutung |
|---|---|
| Eigene Unit vorhanden | `features.py:613–635` nimmt alle eigenen maskierten Units; `mechanism_probe.py:181–184` prüft deren Koordinate ohne Energiebedingung. Auch eine Unit mit negativer Energie verhindert hier das Label „frei“, obwohl sie nicht mehr punktet. |
| Gegner sichtbar | `enemy_coords` enthält nur beobachtete Gegner mit gültiger Position (`features.py:637–640`). `classify` benutzt genau diese Menge, nicht die wahren Gegnerpositionen (`mechanism_probe.py:152,186–189`). Unsichtbare gegnerische Halter können daher im Nenner „freie Felder“ stehen. |
| Bekanntes Punktefeld | Grundlage ist `b.point_tiles` (`mechanism_probe.py:182`), keine erneute Wahrheitsprüfung dieses freien Felds. Die wahre Karte wird in anderen Diagnosefeldern benutzt; die Freifeldschleife filtert nicht mit `pt_true`. Es handelt sich um im Belief bestätigtes Wissen. |
| Ziel vorhanden | Jede nichtleere Koordinate aus `ctx['assigned']` irgendeiner eigenen maskierten Unit zählt (`mechanism_probe.py:155–160`). Die Unit muss dafür weder genügend Energie haben noch einen Schritt auf dieses Ziel ausführen. |
| Genügend Units | Nicht geprüft. `assign_targets` weist höchstens min(Unitanzahl,Zielanzahl) verschiedene Ziele zu und entfernt danach Zeile/Spalte (`features.py:393–402`). Halter, wenige Spawn-Units oder mehr bekannte Felder als verfügbare Units können echte Zielknappheit verursachen. Die Quote weist keinen Leerlauf geeigneter Units nach. |
| Erreichbar / aktuell passierbar | In der Freifeldzählung nicht geprüft. Ein bekanntes Feld unter einem Asteroiden oder hinter einem unpassierbaren Weg bleibt darin. BFS bewertet das Kartengedächtnis; unbekannte Tiles gelten dort zunächst als passierbar (`belief.py:839–842`, `features.py:194–222,348–355`). |
| Energie und sichere Bewegung | Die Zuweisung bekommt vor allem IDs/Positionen, keine unitweise Energiebudgetrechnung (`features.py:659–680`). Energie, sichtbare Gefahren und Kollisionen begrenzen erst die Aktionsmaske (`main.py:1371–1400`); weitere Aktionsregeln können warten, sappen oder ausweichen. Ein zugewiesenes Ziel garantiert deshalb keinen Fortschritt oder eine sichere Ankunft. |

Der Zielplan liegt **vor** dem Q-Netz und seinen Aktionsmasken (`main.py:316–335`). Danach können Bewegung, Sap und Warten unter anderem durch Punktfeld-Sap, Artillerie, Nebelmeidung und Kollisionsschutz verändert werden (`main.py:390–445,460–501,526–558`). Die Koordinaten in `ctx['assigned']` werden dadurch nicht zu einem Plan der endgültig ausgeführten Züge umgeschrieben. Umgekehrt bedeutet ein fehlendes Feld im Plan nicht, dass keine Unit durch eine andere Aktion dorthin gelangt.

## Welche aktive Priorität ein eigenes bekanntes Feld zurückstellen kann

Für die tatsächliche V14-Datei mit SHA `98a07350…d3d8` wurden ausschließlich ZIP-/Pickle-Opcodes gelesen, **ohne Unpickling, Torchimport oder Modellausführung**. Relevante explizite Configwerte: `home_first=false`, `home_penalty=0`, `far_opp=10`, `far_cand=true`, `reach_assign=true`. Die übrigen einschlägigen Defaults (unter anderem Quoten/Sticky/Energiebonus/aktive Energieauswahl aus) sind in `config.py:44–53,83–105,299–303,422–431,457–459` festgelegt; das bestehende `from_dict` ergänzt fehlende Schlüssel (`:498–502`).

- **Keine generelle eigene Hälfte zuerst:** Alle bekannten Punktefelder beginnen mit Priorität 0, Kandidaten mit 1; die Kosten sind BFS-Distanz + 1000×Priorität (`features.py:291–297,348–355`). Da der Heimbonus aus ist (`features.py:595–599`), können nahe gegnerische Punktefelder vor weiter entfernten eigenen Punkten gewählt werden. Ein Feld verliert dann im globalen Greedy-Schritt gegen billigere Ziele, wenn die Units ausgeschöpft sind. Das ist eine vorhandene Priorität, kein Nachweis, wie oft sie die 1681 Feld-Schritte erklärt.
- **Gegnerdistanzregel gilt nicht für jedes Gegnerfeld:** Erst gegnerische bekannte Punktefelder mit Distanz >10 werden um 1500 zurückgestellt (`features.py:359–368`). Nahe gegnerische Felder bleiben gleichrangige Konkurrenten. `far_cand` verändert entfernte gegnerische Kandidaten, keine pauschale Vorrangregel für alle eigenen Punktefelder.
- **Nach Gedächtnis unerreichbare Punktefelder sind letzte Wahl:** BFS −1 wird zu Kosten 5000 (`features.py:349–355`). Solche eigenen Felder können bewusst hinter erreichbaren Kandidaten oder Erkundungszielen bleiben. Die Freifeldmetrik prüft diese Kosten nicht.
- **Nicht jede vergebene Unit ist sofort handlungsfähig:** Die aktuelle aktive-Unit-Filterung ist standardmäßig aus; `features.py:655–658` entfernt negative Energie nur bei `active_targets=true`. Auch das macht „ohne Ziel für dieses Feld“ nicht zu „geeignete verfügbare Unit wurde ignoriert“. Hier wird kein erneuter Filterversuch empfohlen.

Eine pauschale Heimpriorität wurde bereits ohne Erfolg untersucht: `home_first` brachte am 11.10. auf 120 Validierungs-Seeds gegen Solution −1,3 pp mit KI [−5,8; +3,3] und blieb aus (`docs/EXPERIMENT_PROTOKOLL.md:214`). Der historische Arbeitsstand meldet für `home_penalty`/`home_last_only` −3 bis −15 pp und nennt die Störwirkung eigener Units auf der Gegnerhälfte als Erklärung (`docs/ARBEITSSTAND.md:1582`). Das sind ältere Stände, kein universeller Kausalnachweis; sie begründen aber ausdrücklich **keine pauschale Wiederholung von home_first/home_penalty** aufgrund dieser Quote.

## Präzisere nächste Messfrage

**Wie viele der agentensichtig freien, im Belief bewiesenen eigenen Feld-Schritte sind nachgelagert tatsächlich ohne Gegner, nach dem damaligen Kartengedächtnis erreichbar und mit einer bewegungsfähigen eigenen Unit versorgbar?** Erst innerhalb dieser Gruppen die Zeitlücke zerlegen: kein Ziel wegen knapper Units/billigerer ausgewählter eigener oder naher gegnerischer Ziele; Ziel vorhanden, aber langer Weg/Rückkehr; Ziel vorhanden, aber Energie-/Halterverlust oder geänderte Endaktion. Bei konkurrierenden Gegnerzielen auch deren tatsächliche Störwirkung und die Kosten einer Rückkehr erfassen, statt automatisch das eigene Feld für wertvoller zu halten. Anfang und Ende jeder Freiphase sowie Vor-Aktionsziel und endgültige Aktion getrennt erfassen. Noch ungeklärte Relic-Zonen bleiben eine eigene Informationsklasse.

Die vorhandene Quote allein beantwortet diese Frage nicht. Aus dieser Quellenprüfung folgt kein Bugnachweis, neuer Regelschalter, Produktionsfix oder Kandidat. [Diagnosebefunde](remaining_solution_losses/findings.md), [Aggregationen und Nenner](remaining_solution_losses/aggregates.json), [Ausgabegrenzen](remaining_solution_losses/validation_summary.json).
