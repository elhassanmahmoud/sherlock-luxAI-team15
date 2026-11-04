# Einzelnetz und größeres Ensemble – Fortsetzung bis 04.11., 16 Uhr

> **For agentic workers:** Use superpowers:subagent-driven-development. Moayed explicitly reauthorized autonomous continuation, single-network and larger-ensemble experiments on 04 November after the previous study closed. No renewed design permission is required.

**Goal:** Zwei neue, begründete Varianten prüfen und nur einen unabhängig bestätigten, technisch geeigneten Nachfolger veröffentlichen.
**Architecture:** Vorhandene DQN-Tensoren unter identischer V14-Spielkonfiguration; kleines vorab festgelegtes Auswahlexperiment und höchstens eine neue unabhängige Bestätigung. Keine Änderung der aktiven Agentenlogik.
**Tech Stack:** Bestehende Python3.13/Torch/Kursengine, je ein BLAS/Torch-Thread, zwei Evaluationsworker. Python3.10 für etwaige Paketabnahme.
**Spec:** Nutzerauftrag04.11.: weiter bis16Uhr, sehr gutes Einzelnetz und mehr Netze versuchen. Bestandsschutz bis nachgewiesener Verbesserung, alte Sicherungen, autonome Commits und Dokumentation für Mahmoud gelten weiter. Die Studie03./04.11. ist abgeschlossen; ihre Ergebnisse werden nicht umgedeutet oder erneut bestätigt.

## Entscheidungen vor neuen Ergebnissen

- Ausgang main6393859; V14 beide Rohdateien98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8, bestehende ZIP88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6.
- Inventur: vollständige FT5/FTRL/League-Familien nicht lokal verfügbar. V14+FT3 würde Mitglieder duplizieren. FO6 ist lokal verfügbar und eigenständig trainiert. Kein Nachladen zufälliger Ersatznetze.
- Genau zwei Kandidaten: **SOLO28**, ausschließlich V14-Mitglied28 (nullbasiert in `[q,*ensemble]`, FT3-Start20); **FO42**, V14-Mitglieder0–35 gefolgt von `experiments/candidates/all24fo.pth` Mitgliedern18–23. Alle42 Tensorzustände müssen unterschiedlich sein. Gleiche V14-Inferenzkonfiguration, 79 Features, sechs Aktionen, hidden256. Kein erneutes Training in dieser Studie.
- SOLO28 wurde ausschließlich anhand historischer FT3-Endvalidierung nominiert:16/16 gegen Solution und default auf acht bekannten Karten. Das ist keine neue Stärkemessung. FO42 ergänzt sechs Netze aus FO-Starts30–35, die mit `far_opp=10` trainiert wurden: Entfernte Punkteziele der Gegnerhälfte wurden beim lernenden Agenten nachrangig zugeteilt. Ein Vorteil ist offen.
- Die alten Kandidaten FT18/Z36/PAIR/R/C werden nicht nachnominiert. Andere Netzkombinationen sind nicht Teil dieser Studie. Neue Untersuchungen benötigen ein eigenes, vor Ergebnissen festgelegtes Protokoll.

## Zeitkorrektur vor frischen Ergebnissen (04.11., 08:18 Berlin)

Der einmalige technische Pilot am Quellstand3598bb8 beendete alle44 bekannten Spiele mit Exit0 und unveränderten Quellen/Gewichten. Die beobachtete maximale Direkt-Wandzeit4,50655s/Spiel hebt nach der vorab festgelegten Regel beide Zeitklassen an. Die ursprünglichen5720 Leistungsspiele würden einschließlich Reserven erst15:10Berlin enden; zulässig ist14:30. Der ursprüngliche Umfang ist damit **nicht zum Start zugelassen**. Noch keine frischen Leistungsspiele, kein Freeze und keine Ergebnisnominierung wurden gestartet.

Vor jeglichen frischen Ergebnissen wird deshalb ausschließlich die Panel/default-Präzision der Bestätigung von120 auf80 Karten reduziert. Die zusätzlichen Solution-Karten steigen entsprechend von280 auf320, sodass deren400 Karten/800 Spiele je Modell erhalten bleiben. Auswahl20 Karten, Direkt160 Karten, Kandidaten, sieben Gates, Resampling, Konfiguration, Zeit- und Kontingentgrenzen bleiben identisch. Neue Maximalzahl4760 Leistungsspiele plus44 technische. Breitere Panel/default-Unsicherheit wird ausdrücklich berichtet. Originalplan/Code3598bb8, Originalzulassungsfehler und Pilot bleiben erhalten; aktualisierte Schedule-Tests und unabhängiger Auswerter werden vor Ergebnissen neu geprüft und gepinnt. Der Pilot wird weder wiederholt noch zeitlich nach unten korrigiert; sein Agenten-/Modellcode bleibt identisch.

## Globale Grenzen

- Wiederverwendung des vorhandenen Worktrees `sherlock-november-followup` auf neuer Branch `improvement/network-breadth-20261104`, erst nach vollständig geschlossenem vorherigem Lauf. Alte Daten/Manifeste bleiben unverändert; alte Quelle7c906e1 bleibt im Git verfügbar. Native Erstellung einer zusätzlichen Arbeitskopie wurde wegen der Repository-Unterordnergrenze des App-Werkzeugs abgewiesen; keine weitere Kopie erforderlich.
- Maximal zwei schwere Prozesse insgesamt, je ein Rechenthread. Neue Studie friert gesamten Quellstand, Interpreter/Engine, alle Kandidaten/Gegner und diesen Plan von Auswahlbeginn bis Bestätigungsende ein. Remote-Updates währenddessen nur im Hauptcheckout prüfen; keine Integration in laufende Quellen.
- Mindestens30% Kontingent übrig. Ab65% Verbrauch keine neue Phase; ab70% keine Entwicklung. Tatsächlicher Kontingentstand in `/tmp/sherlock-breadth-20261104/watch/usage.json` höchstens15Minuten alt vor Phasenstart; unbekannt/veraltet blockiert Start. Keine Resets. Unter35% Akku keine neue Phase, bei25% kontrollierter Stopp.
- Neue Laufdaten ausschließlich `experiments/analysis/network_breadth_20261104/`, Modelle `experiments/ensembles/network_breadth_20261104/`. Niemals vorhandene Ausgaben überschreiben oder Studie doppelt starten. STOP-Datei `/tmp/sherlock-breadth-20261104/STOP`.
- Leistungsspiele enden spätestens04.11.14:30Berlin (13:30UTC), Abschluss/Paket bis16:00Berlin. Mindestens90Minuten Paket-/Abschlussreserve nach Leistungsspielen. Bei jeder Phase alle verbleibenden Spiele rechnen, zusätzlich20% Zeitreserve und20Minuten Übergänge. Ursprüngliche konservative Wandzeitraten **2,6s/Panelspiel und3,5s/Direktspiel** gelten bereits für zwei Worker, niemals nochmals halbieren. Mit bekannten Pilotspielen und abgeschlossenen Blöcken nur nach oben korrigieren. Vollständiger Maximalumfang4760Spiele:4360Panelklasse,400direkt. Nach dem einmaligen Pilot gelten mindestens3,34772213s/Panelspiel und4,50654902s/Direktspiel (gemeinsamer Verlangsamungsfaktor1,28758543); damit19678,43s plus1200s Übergang, also rund5h48min bis Leistungsende. Auch diese Raten dürfen anschließend nur steigen. Reicht die verbleibende Zeit nicht, keine neue Phase. Kein Verkleinern nach Resultaten.

## Vorbereitung und technischer Pilot

- Neuer Builder liest nur vertrauenswürdige lokale Gewichte, prüft Typen/Formen/Play-Feature-Semantik und eindeutige Tensoridentität. SOLO zählt1, FO42 zählt42; `target_q=q`, leere/entsprechende Ensemble-Liste, keine übernommenen Optimierer/Replay-Zustände. Counters sind normalisierte Inferenzmetadaten, keine erfundene Trainingshistorie. Konfiguration exakt V14, keine neuen Regeländerungen. Quellen-/Mitgliederhashes, Reihenfolge, Dateihashes dokumentieren und nach erneutem Laden prüfen.
- Vor frischen Karten technische Pilotspiele nur auf verbrauchten500720/500721: V14, SOLO28, FO42 jeweils beide Seiten gegen Solution, V13 und default =36Spiele; SOLO28/FO42 zusätzlich gegen V14 =8Spiele. Insgesamt44 technische Spiele, keine Stärkeauswahl anhand dieser Quoten. Zeiten,303Schritte, gültige Aktionen und erhaltene Gewichte prüfen. Einmalige Aufnahme; keine Wiederholung zur Zeitoptimierung.
- Seed-Verbrauch einschließlich aller lokalen Worktrees/CSV/JSONL/Manifeste prüfen; neue Bereiche dürfen nicht bereits verbraucht sein. Protokollreservierungen sind keine gespielten Karten. Vollständige Quellen- und Modellabnahme vor Auswahl, keine Zulassung nur anhand von Flags.

## Feste Leistungsspiele

Panel: Solution_92, sol92_sq, V3(`20261022_all18_v3`), V7(`20261022_v7_Bsnpd`), V10(`20261022_v10_baseline`), V13(`20261101_v13_neb`). default separat. Direktgegner unveränderte V14-Sicherung.

- **Auswahl920Spiele:**20neueKarten861000–861019, beide Seiten. V14/SOLO28/FO42 jeweils gegen7Gegner=840; SOLO28 undFO42 zusätzlich je40direktgegenV14=80. Alle fünf Jobs vollständig beenden, erst dann nominieren.
- Auswahlbedingungen wie vorher: PanelΔ≥+0,5pp, SolutionΔ≥0, default≥99%, direkteQuote≥50%. Höchstens ein Nominierter nach höchstemPanelΔ, dannSolutionΔ, dannwenigerNetzen, dannName. Ohne zugelassenen Kandidaten keine Bestätigung.
- **Bestätigung3840Spiele:**V14 und ein Nominierter auf80neuenKarten862000–862079, beide Seiten gegen7Gegner=2240. Zusätzlich320neueKarten862080–862399 ausschließlichgegenSolution, beideSeiten undbeideModelle=1280. Damit exakt800Solution-Spiele proModell auf400Karten. Dazu320Direktspieleauf160separatenKarten863000–863159. Alle fünf Jobs vollständig vor Schlussauswertung.
- Gesamt maximal4760Leistungsspiele, zuzüglich44technischePilotspiele. Panel/default haben80Karten, Solution400 undDirekt160. Geringere Präzision beimPanel/Direktduell als in der abgeschlossenen Studie ausdrücklich darstellen; keine Resultate aus alten Studien dazumischen.
- Ergebniswert Sieg1/Remis0,5/Niederlage0. Panel gleichgewichtet über6Gegner und80Karten; zusätzlicheSolutionkarten ändern die Panelgewichtung NICHT. Solutionanalyse kombiniert beide disjunkten Blöcke genau einmal zu400Karten. Default80Karten, Direkt160. Strikte vollständige erwartete Schlüssel,303Schritte, Punktezählungv2; keine Schnittmenge oder Teilmengenrettung.
- GanzeKarten mitbeidenSeiten undallenPanelgegnern zusammen resampeln;5000Ziehungen,PCG64Seed0, lineare2,5/97,5Perzentile. Separate passendeKartenmengen fürPanel/Solution/Direkt.
- **Alle sieben Freigabebedingungen unverändert:**PanelΔ≥+1pp;Panel-Untergrenze>0;SolutionΔ≥0;Solution-Untergrenze>−1pp;default≥99%;defaultΔ≥−1pp;Direkt-Untergrenze>50%. KeinNachrücken, keineTeam-Ausnahme, keine zweiteBestätigung nachFehlschlag. Keine100%-Garantie ausendlichenTests.

## Umsetzung und Abnahme

- [ ] Neuer kleiner Kandidatenbauer plus passende Tests für falsche Form/duplizierteMitglieder/Quellschutz/Reloadidentität; alte Builder nicht ändern.
- [ ] Neues Studienwerkzeug mit eigenem Plan/Freeze/Reservierungen, gleicher geprüfter Prozess-/Leistungskontrolle. Alte feste Programme unverändert lassen. Keine globale Monkeypatch-Konfiguration ihrer Deadlines/STOP-Pfade. Eigene strikte Zusammenführung der beidenSolution-Blöcke; Tests für verlorene/duplizierte/zusätzlicheSchlüssel und richtigePanelgewichtung, Gates undZeitbudget.
- [ ] Fokussierte Tests und unabhängiger Code-/Protokollreview. Keine erneuteGesamtsuite ohne Veränderung anLaufzeitcode; letzte1075Tests+126Untertests beziehen sich auf unverändertenAgenten.
- [ ] Tatsächlicher Builder-/Pilot-/Quellenreview, neueSeedprüfung, festeAuswahl und gegebenenfalls einzigeBestätigung. Eigenständige Rohdaten-/Statistikabnahme, keine Freigabe nur anhand des eigenen Auswerters.
- [ ] Bei voller Leistungsqualifikation neue ZIP zunächst separat bauen und Python3.13/3.10, beideAblageorte/frozen/trainTrue,303Schritte-Replay und exakteTensoridentität prüfen. AlteGewichte undZIP sichern, erst dann kontrolliert ersetzen. Keine altenP-spezifischenInstaller und kein`--half` ohne eigene Gleichwertigkeitsprüfung.
- [ ] Ergebnisse/Negativbefunde dokumentieren, sinnvolleCommits/push, lokalenmain sicheraktuellhalten, eigeneJobs/Automationen bis16Uhrbeenden. Bei fehlenderQualifikation bleibtV14. KeinMoodle-Upload ohnekonkreteFreigabe.

## Review-Fokus

- Ein Singleton darf keinen versteckten zweitenNetzzustand alsEnsemble laden;42müssen42unterschiedlicheInference-Mitglieder sein.
- Die zusätzlichen320Solutionkarten dürfen wederPanelgewicht erhöhen nochden80erBlock ersetzen oderdoppeltzählen.
- Fehlerhafte/fehlendeKandidatdateien müssen scheitern, niemals zufälligeNetze laden.
- Gleiche Daten/Quellen/Normierung vonAuswahl bisBestätigung, unveränderlicheNominierung und vollständigeErgebnisdaten.
- Zeit-/Akku-/Kontingent-/STOP-Abbruch darf keineTeilmessung alsqualifiziert markieren; nur eigeneProzessgruppen beenden.
