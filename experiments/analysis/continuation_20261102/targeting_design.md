# V14: Zielplanung, Ausführung und Energie – Diagnose vor Eingriff

02.11.2026 · reine Quellenprüfung · Checkout `/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics`, HEAD `3a7e782`. Keine Agentenänderung, Tests, Modelle oder Spiele ausgeführt. Die angefragte Notiz liegt unter `experiments/analysis/night_20261101/targeting_metric_notes.md`, nicht unter `docs/`. Kein inhaltlicher Blocker.

**Empfehlung:** Zuerst den unveränderten V14 auf dem von Root festgelegten kleinen Satz bereits bekannter Verlust-/Kontrollkarten beobachten. Die bestehenden 1681/4417 freien eigenen Punktefeld-Schritte ohne Ziel und die 40,9 % niedrigen Energiebelegungen rechtfertigen eine Zerlegung, aber noch keinen neuen Heimbonus, Energiereserve- oder Laufbefehl. Zwei konkrete neue Quellhypothesen lassen sich eng prüfen; die zweite bleibt zunächst ausschließlich ein Zuordnungs-Gegenfaktum.

## 1. Was die Kette tatsächlich tut

- `main.py:300–316,237–258`: Belief aus obs_t aktualisieren, dann Kontext/Ziele → Sapziele/Features → Masken, mit exakt dieser Step-ID cachen. Die Diagnose liest denselben Vor-Aktionskontext; kein belegter alter Cache.
- `features.py:291–324,348–402`: globale Greedy-Zuordnung ohne unitweise Energie. Bekannte Punkte starten mit Kosten BFS-Distanz, Kandidaten mit +1000. Nicht erreichbare Distanzen werden 5000; nahe gegnerische Punkte sind gleichrangig, erst Distanz >10 erhält +1500. Jede gewählte Zeile/Spalte wird entfernt. Es gibt höchstens min(Units,Ziele) Zuweisungen. Ein leerer eigener Punkt ist deshalb nicht automatisch ein ignoriertes verfügbares Ziel.
- `features.py:655–680`: V14 nimmt auch negative/immobile Units in die Planung; `active_targets` ist aus und würde ohnehin nur negative Energie entfernen. `build_features:729–780` enthält Energie, Zugunfähigkeit und lokale Feldenergie; das Netz ist also nicht energieblind. Der zugewiesene Zielvektor enthält Manhattan-Distanz, während die Planung BFS verwendet.
- `main.py:324–335`: tatsächliches Q-Ensemble mitteln, zunächst rohes Argmax, dann Masken und maskiertes Argmax. `:1364–1415` sperrt Bewegung wegen Energie < Bewegungskosten, Rand/Asteroid, sichtbarer stärkerer Besetzung oder Kollisionsschutz. STAY bleibt legal. BFS-Erreichbarkeit ist keine Aussage über aktuell erlaubte sichere Schritte oder die Energie einer ganzen Route.
- Danach kommen Regeln: Bewegungspfad/Erkundung (`:389–404`), Halter-/Artillerie-Sap (`:427–449`), Nebelumweg/Warten (`:460–483`), Sap-Stornierung (`:526–531`), endgültige Aktion (`:543–558`). Diese schreiben `ctx['assigned']` nicht um. Die Freifeldquote meint Vor-Netz-Zielplanung, keine tatsächliche Bewegungsabsicht.

**Wichtige Energiephase:** `mechanism_probe.py:63,282–288` zählt lowE auf der Position **nach Bewegung und Bewegungskosten, aber vor eigenem/feindlichem Sap, Void und Feldgewinn** (`sim['orig'] < sap_cost`). Das ist weder „bewegungsunfähig“ noch ein Beweis, dass der gerade ausgeführte eigene Sap die beobachtete Reserve verbraucht hat. Ein Halter kann mit 0 Energie weiter punkten; spätere Schadensanfälligkeit muss über mehrere Schritte verfolgt werden.

## 2. Minimales Beobachtungsschema

Alle Mengen im kanonischen Raum; Key `(seed, side, match_idx, obs_step, match_step)`. Reset separat markieren. Quellen-/Gewichts-/Config-Hashes und vollendete Spiele im Laufbeleg.

| Ebene | Pflichtfelder |
|---|---|
| Öffentlicher Zustand vor Aktion | Eigene IDs/Positionen/Energie, sichtbare Gegner/IDs/Energie, bekannte Punkte/Kandidaten, aktueller Sensor, Gedächtnis-Passierbarkeit/Nebel/Feldenergie, Bewegungs-/Sapkosten, Nebelschätzung, tatsächliches `assigned`, `first_on_tile`, aktive Schalter. |
| Je Unit | Zielklasse/Hälfte, BFS-Distanz zum Istziel, aktueller Halter/Stack, Energieklassen `<0`, `<move`, `<sap`, `>=sap`; tatsächliches Q[6], rohes und maskiertes Argmax, Maske, Gründe je gesperrter Richtung, erste erlaubte BFS-verkürzende Richtungen. |
| Ausführung | Geordnete Wrapper-Ereignisse mit Eingabe/Rückgabe: `_rule_override`, `_path_fix`, `_obey_target`, `_soft_nebula`, `_no_strand`; ergänzend `_fog_sap`, `_artillery_ok`, `_overkill` mit Sapziel und Kopie von `planned_dmg`. Finale kanonische Aktion und tatsächliche Bewegung getrennt. Nicht beobachtbare Inline-Provenienz als „abgeleitet/unklar“ markieren. |
| Je agentensichtig freiem bekannten eigenen Feld | Dauer der Freiphase, zugewiesene Unit oder keine, sichtbarer Gegner, Passierbarkeit, min. BFS lebender Units und beweglicher Nicht-Halter, erlaubter erster Fortschritt, gewählte konkurrierende Ziele und deren Kosten. Auch zugewiesene, aber dauerhaft nicht angelaufene Felder zählen. |
| Nur nachgelagerte Wahrheit | Verdeckter Gegner auf dem Feld, tatsächlicher Asteroid/Blockade, echte Punktkarte; Energie nach Bewegung, Sapzahlung, eingehendem Sap, Void/Kollision und Feld/Nebel; Todes-/Rückkehrzeit. Bei gegnerischen Zielen Besetzung, zugefügter Schaden und gegnerische Besetzungsänderung als beobachtete Störindikatoren, nicht als kausalen Nutzen ausgeben. |

**Beobachter darf Verhalten nicht verändern:** Q-Ausgaben über bestehende Forward-Hooks kopieren (`detach().clone()`), keine zusätzlichen Netzaufrufe; in derselben Unit-/Netzreihenfolge und demselben Datentyp wie `main.py:324–330` mitteln. Unmaskiertes Q vor der In-place-Maskierung sichern. Keine RNG-Nutzung, kein zweites `observe/act`, keine wiederholte `_enemy_stationary`-Abfrage: Letztere verändert `_enemy_prev` (`main.py:1075–1082`). Wrapper rufen das Original genau einmal auf; mutable Argumente sofort kopieren. Tatsächliche Masken aus dem Cache speichern und Sperrgründe rein aus kopierten öffentlichen Daten herleiten; keine neuen Sperren setzen.

`belief.last_seen` ist **kein verlässliches Feldenergiealter**: Symmetrie aktualisiert es auch für die Spiegelsicht, Feldenergie wird nur unter dem realen Sensor kopiert (`belief.py:397–411`). Energiefrische im Beobachter selbst anhand tatsächlicher Sensorsicht führen; Gedächtnisschätzung und beobachteten Wert trennen.

## 3. Zerlegung und engste Hypothesen

Keine einzelne exklusive Ursache erzwingen: Energie, Weg und Konkurrenz können gleichzeitig vorliegen.

1. **Kapazität/Zuordnung:** Wie viele lebende Units halten bereits unterschiedliche Punkte; wie viele bewegliche Nicht-Halter bleiben gegenüber freien erreichbaren Feldern? Fehlende Kapazität, nach Gedächtnis unerreichbar, keine erlaubte erste Richtung und lediglich ein anderes gewähltes Ziel getrennt ausweisen. Ein hypothetischer sicherer erster Schritt beweist keine sichere vollständige Ankunft. Positive-/negative-Energie-Reservierungen zählen, ohne `active_targets` neu vorzuschlagen.
2. **Q versus Ausführung:** Bei zugewiesenem erreichbar bekannten Punkt: wählt schon das maskierte Netz STAY/SAP/Umweg, sperrt die Maske den Fortschritt, oder verändert erst eine Regel die Bewegung? Q-Abstände zwischen tatsächlicher Aktion und legalem Fortschritt sichern; hohe Q-Werte beweisen keinen Nutzen. Zielwechsel und längere Rückwege separat erfassen, kein Sticky-Versuch.
3. **Halterenergie:** Eintrittsenergie sowie die letzten eigenen Saps und Schadens-/Feldbeiträge vor lowE, Freiwerden oder Tod verfolgen. Niedrige Energie ohne Verlust eines Punkts ist eine andere Klasse als ein belegter Halterausfall. Eigener hoher Gesamtschaden und niedrige Energie beweisen noch keinen schädlichen Sap.

## 4. Zwei bedingte Minimalansätze, nach Quellbeleg geordnet

**1 – Gegebenenfalls verworfene Bewegung nach stornierter Artillerie wiederherstellen.** Konkreter Pfad: `art_sap` darf eine Bewegung durch SAP ersetzen (`main.py:445–449`); später setzt `_overkill=true` die Aktion pauschal auf STAY (`:526–531`). `_artillery_ok` prüft weder geplanten Schaden noch späteres Overkill (`:687–719`), `_overkill` berücksichtigt bereits geplanten Schaden (`:1196–1218`). V14 hat Artillerie und Overkill an; `art_surplus` ist aus. Damit ist der Pfad quellseitig möglich, seine V14-Häufigkeit ist unbekannt.

Vor jeder Umsetzung zählen: vorher erlaubte Bewegung, tatsächlich erzwungenes Artillerie-Sap, tatsächliche Stornierung, End-STAY, keine spätere andere Regel und Bezug zur Feld-Freiphase. Nur falls diese Kette auftritt, wäre ein enger Versuch glaubwürdig: die gespeicherte erlaubte Bewegung bei genau dieser Stornierung wieder durch die verbleibende normale Bewegungskette führen. Nicht ursprünglich vom Netz gewählte SAPs umwandeln. Risiken: gespeicherte Bewegung hätte nach Artillerie sonst aktive Nebelprüfung übersprungen; Wiederherstellung muss diese Prüfung nachholen, und der unterdrückte Zug kann taktisch sinnvoll gewesen sein. Kein bewiesener Bug oder Stärkezuwachs.

**2 – Nur diagnostisch: Zwei-Eigentümer-Tausch bei exakt denselben gewählten eigenen Punktezielen.** Globales Greedy kann selbst sein bestehendes Distanzziel verfehlen. Hindernisfreie Zeile y=0, Units x=0,3; eigene Punkte x=2,4: Die vorhandene Reihenfolge nimmt beim Distanz-1-Gleichstand Unit3→2 und danach Unit0→4, Summe 5. Tauschen ergibt Unit0→2 und Unit3→4, Summe 3. Das ist ein nachvollziehbares algebraisches Gegenbeispiel, kein gemessener V14-Fall.

Im Trace ausschließlich Paare beweglicher Nicht-Halter mit zwei bereits gewählten eigenen bekannten Punktezielen prüfen: dieselbe Kostenmatrix, dieselben Ziele, ein erlaubter Fortschritt je Unit, beide Ziele nach Gedächtnis erreichbar; nur strikt kleinere Summe notieren. Höchstens 120 Paare bei 16 Units, keine Suche bis zur Konvergenz. Kein Heimatbonus, keine Änderung ausgewählter Gegnerziele und zunächst **keine Policyänderung**. Ausgeben: Ereignisse, eingesparte BFS-Summe und Überlappung mit langen Freiphasen. Selbst bei positiver Summe bleiben unterschiedliche Energie/Wechselwirkung und tatsächliches Q-Verhalten offen; weniger BFS garantiert keine höhere Punktzahl.

## 5. Was ausdrücklich nicht neu abgeleitet wird

Historische Negativbefunde: `home_first` ohne Gewinn (`EXPERIMENT_PROTOKOLL.md:219`), Heimstrafen −3 bis −15 pp (`ARBEITSSTAND.md:1582`); `energy_pref`, Sticky und Reserven negativ (`EXPERIMENT_PROTOKOLL.md:230`); `active_targets`, allgemeines `obey_target`/`pt_walk_own`, `art_surplus` sowie `no_strand` ohne Zulassung (`ARBEITSSTAND.md:779,960,1020,1351,236–241`). Daher keine Wiederholung solcher Schalter aus der 38,1-%-Quote. Insbesondere verhindert `art_surplus` pauschal Artillerie für eigene Punktziele und ist nicht der schmale Stornierungsfall oben.

**Offener Nachweis:** Der kleine feste Diagnoselauf muss erst zeigen, welche Klassen die beobachteten Freiphasen tragen und ob eine der beiden neuen Quellhypothesen tatsächlich vorkommt. Ohne diesen Befund keine produktive Fixwahl. Die zwölf alten Spiele waren gezielt gewählte Verluste; Klassenhäufigkeiten daraus sind keine globale V14-Rate und keine unabhängige Stärkenmessung. Es fehlen neue Traces, kein zusätzlicher externer Sachverhalt; schwere Arbeit wartet auf Roots Ressourcenfreigabe.
