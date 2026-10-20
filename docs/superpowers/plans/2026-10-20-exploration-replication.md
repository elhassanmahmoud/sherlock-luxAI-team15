# Gepaarter Vergleich längerer Exploration

> Umsetzung innerhalb des ausdrücklich freigegebenen autonomen Nachtauftrags; getrennte Implementierung und unabhängige Prüfung durch Subagents, Zulassung und Zusammenführung durch Root.

**Ziel:** Prüfen, ob längere Exploration während des bestehenden 3.000-Spiele-Curriculums bessere gelernte Netze ergibt. Keine Änderung der Belohnung oder der Abgabe allein aufgrund einer Hypothese.

**Befund:** `eps_decay_steps=60000` erreicht bei 303 Schritten pro Spiel im 199. Spiel den Floor 0,05. Das bestehende 3.000er-Curriculum beginnt die gemischte Gegnerphase erst nach 750 Default-Spielen. Die beiden 400er-Reward-Piloten hatten identische Exploration und erklären diesen Unterschied deshalb nicht; die Terminalkorrektur war dort deutlich schlechter und bleibt aus.

**Begrenztes Design:** Neue Registry-Variante `full_rules_v3_slowexplore`, eigene Kopie der vorhandenen `full_rules_v3`-Overrides, einziger Config-Unterschied `eps_decay_steps=454500` (1.500 vollständige Spiele). Bestehende Agentenimplementierung, Rewards, Guided-Anteil und Curriculum unverändert. Baseline 60000. Bei Spiel 750 steht der neue Epsilon-Verlauf bei 0,525, nach 1500 bei 0,05; die zweite Hälfte trainiert am gleichen Floor. Dies ist eine einzelne vorab gewählte Variante, keine Suche über mehrere Decays.

## Fester Versuch

- Drei frische gepaarte Starts 47, 48, 49; je 3.000 Spiele pro Arm, 18.000 insgesamt. Keine Wiederverwendung des verworfenen Reward-Piloten und kein Resume.
- Vor jedem Paar identische tatsächliche Q-/Target-Anfangstensoren, Agent-RNG, Karten und Gegnerfolge prüfen. Einziger Unterschied `eps_decay_steps`; `terminal_death_potential=False`, `active_targets=False`, `sap_geometry=False` in beiden Armen.
- Train-Karten: 470000–471499, 480000–481499, 490000–491499. Remote vor Start auf Kollision prüfen. 750 Default-Warm-up-Spiele, danach deterministischer Solution92-Anteil 0,7, kein Pool. `--no-test --val-every 0`.
- Keine Zwischencheckpoint-Auswahl oder Ergebnis-basierte Verlängerung. Alle finalen Einzelnetze auf 500720–500779, beiden Seiten/default/Solution92, jeweils 240 Spielen auswerten.
- Ein Trainer oder maximal zwei Evaluationsworker, keine schweren Paralleltests. Alle Quellen/HEAD/Gewichte pro Paar einfrieren; Quellen müssen für alle drei Paare fachlich identisch bleiben. Kein nachträgliches Ändern des Epsilonverlaufs.
- Zulassung aller drei Paare nur mit gemessener Laufzeit und mindestens einer Stunde Abschlussreserve. Pilot gemessen ca. 6,6–6,8 min für 400 Spiele; linear etwa 5,1 Stunden für 18.000 Spiele plus ca. 15 Minuten Auswertung. Veränderte Exploration kann die Laufzeit verändern. Vor weiteren Paaren Restzeit kontrollieren. Bei Zeit-/Technikabbruch als unvollständig dokumentieren; kein Methodenurteil aus ausgewählten fertigen Starts.

## Auswertung und Entscheidung

Alle drei Startdifferenzen berichten; Kartenbootstrap erfasst keine Trainingsstart-Streuung. Entwicklungsregel: mittlere Solution92-Differenz mindestens +3 Prozentpunkte, mindestens zwei von drei Starts positiv, mittlerer Default-Verlust höchstens 2 Prozentpunkte. Keine nachträgliche Auswahl des besten Einzelnetzes. Wenn die Regel nicht erfüllt ist, keine Übernahme dieser Trainingsrichtung behaupten.

Die methodische Aussage und die Auswahl stärkerer Gewichte getrennt halten. Nach allen drei Paaren zuerst das Ensemble aller drei Kontrollnetze gegen alle drei neuen Netze vergleichen. Anschließend genau zwei vorab bestimmte Abgabekandidaten bilden: feste V3-Netzbasis plus alle drei Kontrollnetze bzw. dieselbe Basis plus alle drei Slowexplore-Netze. Keine Auswahl einzelner Starts, keine Mischung beider neuen Dreiergruppen und keine andere Netzgewichtung. Beide Kandidaten bekommen exakt dieselbe Inferenzconfig wie die dann installierte geprüfte Abgabe. Diese Config vor der ersten Ensembleauswertung dokumentieren und danach einfrieren.

Beide Kandidaten und die installierte Abgabe auf denselben 60 Entwicklungskarten auswerten. Kandidat nur zulässig, wenn sein Solution92-Unterschied zur installierten Abgabe positiv ist und die untere 95%-Kartengrenze >0 liegt, bei höchstens 2 Prozentpunkten Default-Verlust. Wenn beide zulässig: den größeren Solution92-Unterschied wählen; exakter Gleichstand wählt die Kontrollgruppe (einfachere etablierte Trainingsmethode). Genau ein Kandidat erhält den frischen Block. Wenn keiner zulässig, keine frische Übernahmeprüfung. Die zusätzliche Kontrollgruppe darf auch bei nicht erfülltem Slowexplore-Methodengate gewinnen; dann ist das ein Ensemble-/Neutrainingsgewinn, ausdrücklich kein Nachweis für längere Exploration. Auch ein ausgewähltes Slowexplore-Ensemble beweist für sich keine allgemeine Überlegenheit der Trainingsmethode.

Alle hier beschriebenen Entwicklungs-, Bestätigungs- und Direktintervalle verwenden 5.000 Bootstrap-Ziehungen mit Seed 0 auf ganzen Karten samt beiden Seiten. Vor der Ensembleauswertung Hash der festen V3-Basis (aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935) sowie Hash und Config der installierten Vergleichsabgabe erfassen; diese Vergleichsidentität bleibt über Entwicklung, Bestätigung und Direktgate unverändert.

Der direkte Vergleich der beiden gleich großen Ensembles dient zur Zuordnung des beobachteten Unterschieds; Änderungen der Netzanzahl gegenüber V3 sind sonst ein Mitfaktor. Unterschiede der Abstände zwischen legalen Q-Aktionen untersuchen, ohne nachträglich eine Normalisierung einzuführen.

Eine neue Abgabe muss danach auf einem separaten frischen Block gegen die tatsächlich installierte Abgabe bestehen: **510200–510399 reserviert**, 200 Karten × beide Seiten × beide Gegner, gepaarter Kartenbootstrap (5.000, Seed 0). Solution92-Differenz positiv und Untergrenze >0; beobachteter Default-Verlust höchstens 2 Prozentpunkte. Anschließend strikter Direktvergleich gegen installierte Abgabe auf den bekannten 60 Karten: untere 95%-Kartengrenze der mittleren Ergebniswertung >0,5. Technische Kursprüfung, Reproduktion, Sicherung und Hashprüfung vor Promotion. Falls bis 06:00 nicht vollständig geprüft, Kandidat erhalten und Abgabe beibehalten.

510000–510199 bleiben ausschließlich der getrennten Inferenzentscheidung vorbehalten. Keine Nutzung der finalen Testkarten 900000+.

## Umsetzung und Prüfungen

- [x] Registry-Variante und Tests für isolierte Config-Kopie, exakten Ein-Feld-Unterschied und Epsilon-Meilensteine erstellen; zuerst fehlende Variante als erwarteten Fehler nachweisen.
- [x] Separaten Paar-Runner aus dem geprüften Replikationsgerüst ableiten: neue Pfade/Labels, exakter Epsilon-Diff statt Terminalflag-Diff, nur 3.000 Spiele, Seeds 47–49, vollständige Daten-/Tensor-/Quellen-/Fristprüfungen. Stdlib-Fixtures und unabhängiger Review.
- [ ] Nach Ende der laufenden Inferenzrunde Quellen integrieren, gezielte Tests und kurze Lauffähigkeitsprüfung; dokumentieren, committen, pushen.
- [ ] Tatsächliches Training starten und jeden vollständigen Paarlauf samt Rohdaten und Befunden sichern; fachlich identischen Code beibehalten.
- [ ] Gesamtauswertung aller drei Paare, gegebenenfalls die vorab beschriebenen Ensemble-/Freigabestufen. Kein automatischer Austausch aufgrund der Trainingsquote oder des Loss.
