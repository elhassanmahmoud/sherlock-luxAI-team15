# Neuer Verbesserungsversuch bis 03.11., 06:00 Berlin

Gelesener Ausgang: main/performance `3a7e782`, V14-Gewichte `98a07350…d3d8`; getrennter Gauß-Prototyp `307b1ed`. Vorige Studie abgeschlossen: kein Nachrücken und kein qualifizierter V14-Nachfolger. Reine Quellen-/Archivlektüre und Standardbibliotheksprüfung vorhandener Seedtabellen; keine Codeänderung, Modelle, Tests, neuen Spiele oder Trainings. Am Entwurfszeitpunkt02.11.13:06Berlin verbleiben knapp17Stunden. Nutzer-Nachtrag13:17Berlin: Weiterarbeit auf Akku ausdrücklich erlaubt; zuletzt85–86%. Unter35% keine neue lange Phase, bei25% eigene schwere Jobs kontrolliert sichern/beenden; AC hebt diese Akkugrenzen auf. Kein Warten auf Netzteil erforderlich.

## Empfehlung

**Den nächsten Trainingsversuch an eine belegte Änderung der Zielmachbarkeit binden und den Reward unverändert lassen.** Zuerst muss Roots Zielanalyse einen konkret vermeidbaren Planungsfall identifizieren. Anschließend kleine gepaarte Anpassung mit zwei vorab festgelegten V14-Komponenten: Baseline-Planung versus dieselbe neue Planungslogik, die später tatsächlich im Agenten ausgeführt wird. Dadurch wird eine Verteilungsänderung im Zustands-/Aktionspfad untersucht, statt nochmals Belohnungen eines Einzelnetzes zu verstärken und es als37.Netz anzuhängen.

Gauß ist eine sinnvolle **getrennte technische Reserve**. Die mathematische zusätzliche Schlussmöglichkeit ist belegt; die Häufigkeit nützlicher zusätzlicher Fakten auf echten Beobachtungen ist ungeprüft. Die neue heutige Freigabe erlaubt einen eigenen neuen Plan; sie macht den gescheiterten Kontrollkandidaten nicht wieder zulässig und reaktiviert nicht automatisch den alten bedingten Schattenplan.

## Was die bisherigen Daten tragen

Der vorige Pilot hat korrekt gelernt: je600Spiele,120Prefill,96bekannte Validierungen,90000Adamupdates, frischer Optimizer/Replay aus demselben echten V14-Komponentennetz18. Dennoch replizierte das37-Netz-Kontrollensemble seinen Auswahlvorteil nicht: Panel+4,83pp auf50Karten, anschließend−0,167pp [−2,375;+2,000] auf200neuen Karten, direkt50,25% [43,5;57]. Der höhere Entdeckungsreward wurde bereits in der Auswahl abgewiesen. Dies ist weder ein genereller Gegenbeweis gegen Training noch eine Begründung für weitere Rewardstärken/Seedlotterien.

Auch Runde6 trainierte unter den aktuellen Nebel-/Halbstreuungsregeln24000Spiele ohne gesicherten zusätzlichen Ensemblegewinn. Die älteren ft-Einzelcheckpoints/Buffer fehlen lokal weiterhin; beliebige ft-Manifeste ohne Gewichte führen im generischen Loader zum stillen Neustart. Echte Komponentenextraktion aus der vorhandenen V14 ist dagegen möglich und wurde bereits geprüft.

Die zwölf selektiven Verlustmatchdiagnosen zeigen konkurrierende Informationen: unbekannte Punktfeld-Schritte, schwächere späte Belegung, Energie-/Halterverluste und Stacks. Die38,1%-Quote ist agentensichtiges Freifeld-/Planwissen, kein Nachweis ignorierter erreichbarer Felder oder verfügbarer Units. Eine erneute pauschale Heimpriorität wird dadurch nicht begründet.

## Architektur: warum der Lernanreiz zuerst einen ausführbaren Pfad braucht

- `features.py:225ff` weist Ziele vor dem Netz zu, hauptsächlich aus Positionen, BFS und Prioritäten. Es erhält gegenwärtig kein unitweises Energiebudget. Ein als Ziel eingetragenes Feld kann mehr Energie/Laufzeit erfordern, als die betreffende Unit sinnvoll aufbringen kann.
- Die79Netzmerkmale enthalten aktuelle Energie, Bewegungs-/Sapkosten, lokale Energie und `assigned_dx/dy/dist/exists`, aber keine vollständige Wegenergiebilanz oder explizite Ankunftszeit. Ein neuer globaler Energie-/Feasibilityreward allein fügt diese Information nicht hinzu.
- Maske, Kollisionsschutz, Sap-/Nebelregeln und weitere Überschreibungen greifen nach Ziel-/Featurebildung. Ein günstigeres Ziel verändert nicht zwangsläufig die ausgeführte Bewegung. Der zu messende Übergang ist daher **Plan → erlaubte/netzgewählte Aktion → endgültige Aktion → Fortschritt**, nicht nur Zahl zugewiesener Felder.
- Eine sichere kleine Planungskorrektur kann innerhalb79Features bleiben: Sie ändert, welches ausführbare Ziel als `assigned_*` erscheint. Eine neue Featuredimension würde dagegen alle alten Ensembles und Replay-Formate betreffen und gehört nicht in diesen engen Versuch.

## Zulassung vor Training

Roots Zielpfad muss zuerst auf bereits bekannten Diagnoseschlüsseln und wenigen vorab fixierten Entwicklungskarten unterscheiden:

1. Tatsächlich kein Gegner auf dem agentensichtig freien Feld versus versteckter Halter; Wahrheit nur nachgelagerte Diagnose.
2. Genügend geeignete, bewegungs-/wartefähige Units versus echte Unitknappheit; legal erreichbare Wege versus Asteroiden/unterbrochene Pfade.
3. Keine Zuweisung trotz geeigneter Unit versus vorhandenes Ziel ohne Fortschritt wegen Energie, Weglänge oder endgültiger Regelaktion.

Ein Planungsfix sollte nur öffentlich verfügbares Wissen verwenden. Ein energiearmes Schiff auf einem positiven Energiefeld kann durch Warten wieder bewegungsfähig werden; „Energie kleiner als gesamte Wegkosten“ ist daher keine universelle Unerreichbarkeit. Unbekannte Energie/Nebelwerte dürfen nicht als perfekte Wegkosten erscheinen. Belegte Gegnerstörung auf deren Hälfte nicht pauschal entfernen.

**Stop:** Wenn die Zielanalyse nur die alte38,1%-Quote bestätigt oder kein tatsächlich beeinflussbarer Fehlerpfad mit veränderter legaler Endaktion auftaucht, diesen Trainingsweg nicht starten. Als mechanische Mindestzulassung vor Implementierungsauswertung bieten sich mindestens8 dokumentierte relevante Plan-/Endaktionsänderungen auf mindestens4 verschiedenen bekannten Karten an, ohne ungültige Aktionen oder belegbar falsche Inputs. Root muss dieses konkrete Kriterium vor der Probe übernehmen/ersetzen; es ist kein heutiges bereits bestandenes Gate.

## Minimaler gepaarter Anpassungsversuch

Wenn der Mechanismus zugelassen ist, eine einzige feste Planungskorrektur `F` einfrieren. Keine gleichzeitige Reward-, Netzarchitektur-, Sapziel- oder Gaußänderung.

| Dimension | Vorab festgelegt |
|---|---|
| Initialisierungen | Komponenten18 und19 der unveränderten V14, keine Auswahl nach ihrer Leistung |
| Arme je Komponente | Kontrolle: bisherige Planung; Treatment: F in Planung/Features und tatsächlichem Trainingsaktionspfad |
| Netz | jeweils ein79-Feature-/6-Aktionen-DQN; identische q/target-Starttensoren pro Paar |
| Optimizer/Replay | neuer Adam,lr1e-4; frischer Replay pro Arm;120eigene Prefillspiele ohne Lernen |
| Horizont | genau600Trainingsspiele, Endstand; interne Val8bekannte Karten nach0/300/600nur Diagnose |
| Reward | unverändert,w_discovery0,5,w_explore0,3; keine zusätzlichen Strafgewichte |
| Gegner | unverändert fest .6Solution/.2Quadrat/.1default/.1rush, kein Pool/Snapshots |
| Parallelität | ein Paar gleichzeitig=2Worker; zweites Paar danach, höchstens2Stunden Gesamtbudget mit beobachteter Zeitzulassung |

Die Vorabtensoren pro Paar müssen gleich sein, nicht zwangsläufig die Prefilltrajektorien: F verändert absichtlich die handelnde Policy schon im Prefill. Beide Arme teilen Karten und exogenen Gegnerplan; jeder sammelt unter seiner eigenen eingefrorenen Anfangspolicy. Das ist eine bewusste Behandlung, keine Verletzung der Paarung. Q bleibt während Prefill unverändert. Die neue F-Logik muss bei `training=True` tatsächlich gelten; ein ausschließlich eval-wirksamer Schalter beantwortet die Trainingsfrage nicht. Bestehende eval-only-Rescue-Semantik nicht heimlich umschalten.

**Wichtig:** `scripts.night_train_pilot.run_arm` ist fest auf Seed9 und die vorige Studie kodiert und darf nicht unverändert erneut gestartet werden. Der allgemeine `finetune` kann neue Seeds/Varianten, braucht aber einen kleinen neuen kontrollierten Wrapper mit geprüften Anfangsdateien und temporären Varianten. Das ist vorgeschlagene neue Umsetzung, kein bereits vorhandenes neues CLI. Keine Modellextraktion/Jobs wurden hierfür ausgeführt.

Vorgeschlagene generische CLI je Komponente/Arm, erst nach Definition der geprüften temporären Varianten:

```sh
python -m scripts.finetune --init <neuer Init-Ordner für Index18 oder19> \
  --name <einmaliger Studienname/Arm/Index> --variant <baseline_v14 oder v14_plus_F_train> \
  --games 600 --seed <28 oder29> --map-offset 4200 --lr 0.0001 \
  --prefill-games 120 --keep-final --no-test --n-val 8 --val-every 300 \
  --mix 'solution92=0.6,sol92_sq=0.2,default=0.1,rush=0.1'
```

Zwei vorab feste Ensembles für die neue Leistungsstudie, beide **36Netze**:

- **A:** V14+F, alle bisherigen Tensoren unverändert. Das isoliert den direkten Planungsnutzen.
- **B:** A, aber Komponenten18/19 durch die zwei unter F adaptierten Endnetze ersetzt; keine Nettovergrößerung des Ensembles, keine Mischungssuche.

Die zwei unter bisheriger Planung trainierten Kontrollnetze dienen der Entwicklung-/Methodenablation: unter derselben finalen F-Inferenzconfig gegen die adaptierten Pendants beurteilen, damit allgemeines Nachtraining nicht als F-Anpassung ausgegeben wird. Sie bilden keinen nachrückenden Stärkekandidaten. Keine Best-Seed-Auswahl, keine nachträgliche Entfernung des schlechteren der beiden adaptierten Netze. Zwei Starts erlauben weiterhin keinen allgemeinen Methodenbeweis; die Freigabe bewertet das feste zusammengesetzte Agentenartefakt.

**Trainingstop:** Dateifehler/falscher Anfang/NaN/fehlende Updates/Deadline/AC-Verlust stoppen beide aktiven Arme. Bei unvollständigem Paar kein trainierter B-Kandidat. Kein frühes Beenden eines schlechten Arms und Weiterlaufen seines Pendants. Interne kleine Val darf keinen besten Zwischenstand ersetzen.

## Alternative: Gauß technisch zulassen, bevor dafür überhaupt trainiert wird

Der Stand307b1ed hat Main-Wiring, Default-off,37reine Tests, Review und Mikrobenchmark. Gemessene Helpermaxima lagen bei0,218ms(Fünf-Feld),3,604ms(dicht24),4,752ms(400Records); das sind keine aktiven Agenten-/Echtzeitbelege.

Kleinster neuer Schritt ist ein neuer heutiger Shadowplan auf80bekannten vollständigen V14-Spielen(830000–830039,beide Seiten), ein handelnder V14 und strikt getrennte V/A/G-Beliefs auf denselben öffentlichen Beobachtungen. Die unveränderten Caps bleiben4096Zellupdates,24Variablen,40Zeilen,8Versuche/Match mit8Beobachtungen Abstand; keine Budgeterhöhung nach einem schönen Ergebnis. Punkt-/Nullfakten gegen Wahrheit erst nach Verarbeitung prüfen. Metrik ist insbesondere `G \\ (V ∪ A)`, nicht lediglich G gegen ein möglicherweise schwächeres A.

**Technischer Stop:** irgendein falscher Zusatzfakt, Aktionsänderung des handelnden V14 durch den Shadow, nicht reproduzierter Ausgang, Inputbruch oder unvollständige Schlüssel verwirft die Probe. Ohne zusätzlichen sicheren G-Mehrwert Ansatz für dieses Fenster verwerfen. Kosten vollständig messen und vorher eine konkrete lokale CPU-/Act-Budgetgrenze festlegen; Helpermikrozeiten allein sind kein Nachweis. Keine zusätzlichen Trainingsstunden nötig, um eine logische Inferenzhypothese zuzulassen.

Erst ein positiver Mechanismusnachweis könnte einen **eigenen** G-Kandidaten rechtfertigen. Nicht ad hoc mit F oder B kombinieren. Wenn Root heute Gauss als Hauptroute wählt, das neue Auswahlset vor dem ersten840/841erLeistungsspiel auf V14/G festlegen und den Anpassungspilot weglassen. Nicht A/B/G gleichzeitig nach günstigen Zwischenständen erweitern. Der alte Nachtplan mit bedingter No-nominee-Klausel ist heute nur Quellenmaterial; die neue Studie braucht eine neue explizite Vorabfestlegung.

## Frische Datenblöcke und feste Übernahmegates

Lesender Audit im aktuellen Performancecheckout:1205seedhaltigeCSV/CSV.gz,1565566Zeilen,275Manifeste einschließlich deklarierter Trainings-/Prefillspannen. **Keine Treffer** in den folgenden Vorschlagsblöcken. Noch nicht reserviert; Root muss sie zentral gegen die anderen heutigen Aufträge und unveröffentlichte Fremdläufe abgleichen und vor Spielbeginn festschreiben.

| Zweck | Vorschlag |
|---|---|
| Training Index18/Paar1 | Runseed28,offset4200:484200–484499 |
| Prefill Paar1 |485000–485059 |
| Training Index19/Paar2 | Runseed29,offset4200:494200–494499 |
| Prefill Paar2 |495000–495059 |
| Entwicklung |840000–840039 |
| Auswahl |841000–841099,100Karten |
| unabhängige Bestätigung |842000–842299,300Karten |
| unabhängiges Direktduell |843000–843299,300Karten |

Die acht alten internen Valkarten500000–500007 bleiben reine Lernkurve. Die alten831/832/833erStudienkarten sind bekannt und werden nicht als neuer Holdout ausgegeben. Trainingskarten bleiben unter500000 und `4200+600/2<=5000`; beide Finetune-Seedprüfungen passen auch für Runseed29.

Panel unverändert für Vergleichbarkeit zum letzten lokalen Versuch: Solution,Quadrat,V3,V7,V10,V13; default nur Sicherheitsgegner. Keine Aussage, dass dieses Panel Mahmouds fehlende Liga-/Threat-Gegner oder unbekannte Kursgegner vollständig repräsentiert.

**Auswahl genau A/B bzw. genau G:** Kandidaten und V14 auf denselben100Karten gegen sechs Gegner+default, Kandidaten zusätzlich direkt gegen V14. Zulassung wie zuletzt: Paneldelta≥0,5pp, Solutiondelta≥0, default≥99%, direkt≥50%. Genau ein Nominee mit höchstem Paneldelta; Gleichstand bevorzugt den einfacheren reinen Planungs-/Inferenzkandidaten A/G vor dem adaptierten B. Nachträgliche Kontrollkandidaten ausgeschlossen.

**Bestätigung nur dieses Artefakt:**300neue Karten, beide Seiten, Panel+default,300getrennte Direktkarten. Unveränderte Gates: Paneldelta≥1pp UND untere95%-Grenze>0; Solutiondelta≥0 UND untereGrenze≥−1pp; default≥99% UND Delta≥−1pp; Direktuntergrenze>50%.5000Kartenbootstrapziehungen,RNG0,2,5/97,5Perzentile; Seiten/Panelgegner einer Karte als Cluster. Keine V14-Teamentscheidungs-Ausnahme, keine Kartenverlängerung nach Ergebnis, kein Nachrücken bei Fehlschlag. Manifest-/Input-/Command-/CSV-/Quell-/Checkpointhashes vorab binden und Daten unabhängig abnehmen.

## Realistisches Zeitbudget statt nomineller „17Stunden Training“

Gemessene Vorgängerstudie auf genau diesem M3/2Workers:

-3100Auswahlspiele:114,35min;6000Bestätigungsspiele:212,09min. Konservativer Planwert **2,22Wandsekunden pro Spiel** bei2Workers. Prozesszeit war im Mittel4,35/4,19sjeSpiel; nicht nochmals durch die Workerzahl teilen.
- Das vorige Paar aus2×816Spielen benötigte40min42s. Vier gleich große Arme in zwei Paarwellen grob82min, mit20%Reserve etwa98min. Neue F-Logik kann die Kosten ändern; anhand vollständig geplanter Pilotzeilen vor jeder Welle neu zulassen.
- Auswahl100Karten mit2Kandidaten:1400Baseline+2×(1400+200direkt)=**4600Spiele**,≈170min,mit20%≈204min.
- Bestätigung300Karten:4200+4200+600=**9000Spiele**,≈333min,mit20%≈400min.

Damit sind Training+Auswahl+Bestätigung schon rund11,7Stunden inklusive20%-Reserve, dazu Mechanismus/Code/Checks und mindestens45–60min Schluss-/Paketreserve. Die vollständige Variante passt in17Stunden, wenn Root den Mechanismus/Codeweg innerhalb etwa3Stunden einfriert und keine zusätzlichen Kandidaten-/Abulationsrunden hinzufügt. Akkuarbeit ist ausdrücklich erlaubt. Der tatsächliche Ladestand und die35/25%-Grenzen begrenzen die Phasenzulassung, nicht das bloße Fehlen eines Netzteils.

**Admission:** vor jeder Phase alle noch erforderlichen Schritte mit dem langsameren tatsächlich gemessenen Durchsatz und Reserve berechnen.300erBestätigung konservativ spätestens02.11.22:30Berlin starten, damit Auswertung/Übernahmeprüfung vor03.11.05:30passt. Ab05:00keine neuen langen Jobs,05:30aktiveModellarbeit beenden,06:00Bericht. Wenn diese vollständige Folge nicht mehr passt, vor Leistungsdaten entweder den Lernteil ganz auslassen und nur A/G untersuchen oder den Versuch als Experiment ohne heutige Übernahme beenden. Numerische Gates nicht reduzieren; keine weitere Stichprobenänderung aus einem günstigen Verlauf heraus.

## Nächste autorisierte Handlung für Root

Dieses Read-only-Memo startet keine Jobs; die autorisierte Arbeit auf Akku darf Root innerhalb der dokumentierten Grenzen fortsetzen. Roots unabhängige Zielanalyse abschließen, eine einzige mechanisch begründete Route wählen und mit neuen Seeds/Zeitfenster/Gates vorab festhalten. Ich empfehle Anpassungstraining nur nach einem nachweisbar ausführbaren geänderten Zielpfad; ansonsten die deutlich billigere, klar falsifizierbare Gauß-Shadow-Zulassung statt eines weiteren Reward-/Einzelnetzversuchs.
