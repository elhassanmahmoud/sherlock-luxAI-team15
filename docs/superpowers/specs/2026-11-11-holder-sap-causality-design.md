# Produktive Halter schützen: zuerst den Nutzen eines Schussverzichts nachweisen

**Status: Umsetzung vom Nutzer nach Planprüfung ausdrücklich freigegeben.** Moayed beauftragt am 11.11. einen nächsten sinnvollen Plan aus den bisherigen Ergebnissen. Mindestens 5 % Kontingent erhalten; ab 92 % Verbrauch keine neue Phase, spätestens bei 95 % kontrolliert stoppen. V14 und ZIP bleiben bis zu einem belegten besseren vollständigen Agenten unverändert. Dieser Vorschlag ist Codex' Empfehlung, keine bereits bestätigte Verlustursache.

## Warum dieser nächste Schritt?

Mehr Netze, Rewardvarianten, Nachahmung und additive Korrekturen lieferten bisher keinen bestätigten Nachfolger. Der letzte Matchausgang-Pilot veränderte 43/48 Aktionen, aber nur einmal den Matchausgang positiv und einmal negativ. Alle Eingriffe erfolgten bei Matchschritt 40. Eine knappe Q-Bewertung erwies sich dort nicht als ausreichend ergiebiger Weg zu entscheidenden Situationen. [Ergebnis](../../../experiments/analysis/match_outcome_probe_20261110/ERGEBNIS.md).

Eine konkrete andere Spur ist belegt: Auf `9946007/player_0` wählen zwei alleinige Punktehalter bei Schritt 138 Netz-STAY, führen nach Regeln aber SAP aus. Energie fällt 50→8 beziehungsweise 53→23; danach folgen Abgänge, negative Energie und zwischen Aktionen 143–152 eigene 0 gegen 46 gegnerische Punkte. **Nicht bewiesen:** dass Schussverzicht diesen Verlauf verbessert. Gegnerangriffe, Nebel, eigene Schusskosten und die verlorene Wirkung eines unterlassenen Schusses müssen auseinandergehalten werden. [Originalbefund E3](../../../experiments/analysis/holder_oscillation_20261109/analysis/REPORT.md).

Die nächste Frage lautet deshalb: **Verbessert es tatsächliche Match- und Spielausgänge, einzelne von Regeln erzwungene Schüsse produktiver Halter auszulassen?** Die Ursache wird mit einer realen Gegenrechnung geprüft, bevor daraus eine Regel oder ein Lerner entsteht.

## Abgewogene Ansätze

1. **Empfohlen: eng begrenzte Kausalprobe eines finalen SAP-Vetos.** Konkreter protokollierter Anlass; vorhandene Originalpräfix-Messung wiederverwendbar. Risiko: Schüsse können wichtige Verteidigung sein, daher nicht pauschal ausschalten.
2. **Andere strategische Zielsets über mehrere Schritte.** Potenziell größerer Hebel, aber aktuell keine klare neue Zielentscheidung belegt. Alte V4-Piloten hatten keine wirksamen Fälle, der spätere Paar-Tausch wurde tatsächlich geprüft und scheiterte in der Bestätigung. Nicht als neues Hungarian-/HOLD-Projekt neu etikettieren.
3. **Teamlernen über Matchgrenzen.** Echte strukturelle Frage: `main.py:_update` beendet Einheitenübergänge beim Matchwechsel; spätere Informationsvorteile propagieren nicht über dieses TD-Ziel. Entdeckungsbelohnungen bestehen bereits. Ein neuer Teamkritiker wäre ein größerer Umbau ohne aktuellen kausalen Vorteilsbeleg; zunächst zurückstellen.

Die allgemeine Idee, den Beitrag einer Aktion zum Teamergebnis über Gegenfakten zu untersuchen, ist auch Gegenstand von [COMA, Foerster et al.](https://arxiv.org/abs/1705.08926). Hier wird **kein COMA implementiert**; die Arbeit belegt keinen Erfolg dieses konkreten Lux-Vetos.

## Was ausdrücklich anders ist als bisher

- Kein neues `pt_sap_reserve=30/60`, kein anderes `sap_reserve_k` und kein pauschales SAP0: solche breiten Reserve-/Rewardvarianten sind bereits geprüft.
- Alter HOLD: ursprünglicher MOVE wird vor den Regeln in STAY geändert; nachgelagerte Regeln dürfen weiter SAP erzwingen. Hier: ursprünglicher maskierter Netzvorschlag STAY und ein tatsächlich nach allen Regeln geplanter sichtbarer SAP. Der Eingriff sitzt **nach der letzten Zielwahl, vor der Verbuchung geplanten Schadens**.
- Auswahl nach beobachtbarem Ereignis, nicht nach einem festen Schritt oder nach zukünftiger Niederlage. Bekannte Verlustkarten dienen nur zur Diagnose; kein versteckter Seed-/Gegnerzustand darf Auswahlmerkmal werden.
- Endauswertung bis zum **vollständigen Spielende**. Aktueller Matchsieg und Punkte sind zusätzlich sichtbar; spätere Gedächtnisfolgen werden nicht abgeschnitten.

## Fester erster Pilot: maximal 88 ganze Ausführungen, null Gradienten

**Bekannte Karten, beide Startseiten gegen Solution:** `9946007, 2000000, 2000001, 2000009, 2000029, 2000035, 2000045, 2000055`. Die ersten beiden 200000x-Karten sind Siegkontrollen; die anderen fünf enthalten sechs belegte ganze V14-Niederlagen. Zusätzlich die oben beschriebene Diagnosekarte. Keine neue repräsentative Siegquotenstichprobe.

Herkunft der sieben 200000x-Karten: `experiments/analysis/replacement_validation_20261108/validation/V14_panel_0.csv`, SHA-256 `7f95a56e970230968d7d6f661eff814bc7a2b4b0108d8a2699978e7673359aa6`; die Datei enthält V14 194/200 gegen Solution. Für `9946007/player_0` liegt ein exakter 303-Schritte-Trace vor; die andere Seite ist hier noch kein archivierter exakter Referenztrace. Bekannte Ergebnis-/Quellenunterschiede müssen vor Aufnahme aufgeklärt werden, keine stillen Ersatzkarten.

1. Je Schlüssel ein normaler V14-Referenzlauf und ein passiver instrumentierter Lauf: **32 volle Partien**. Die Referenz lädt eine vor der Hookänderung gesicherte vollständige Original-Agentenquelle, Ausgang `021d13e1a7808d67bf8a11c78fbc4beaae3c9956`, mit originalen Gewichten. Nicht beide Seiten des Neutralitätsvergleichs aus derselben bereits geänderten Klasse laden. Alle 303 Frames müssen übereinstimmen. Bereits vorhandene exakte Traces zusätzlich prüfen; CSVs allein erlauben nur Ergebnisabgleich, keinen erfundenen Frameabgleich.
2. Im passiven Lauf pro Match **die erste** geeignete Situation wählen: aktuelle lebende Einheit mit nichtnegativer Energie, alleinige produktive Besetzung eines bestätigten Punktefelds, legaler STAY, ursprüngliches maskiertes Ensemble-Argmax STAY, am Ende der normalen Regelkette sichtbarer SAP mit `fog_origin is None`. Kein Energie-Schwellenraster, kein Zukunftsfilter. Bei mehreren Einheiten kleinste UID. Keine Gelegenheit ist ein gültiger Nullfall, kein Nachrücken zu späteren Ereignissen.
3. Genau diesen einen Schuss in einer frischen Originalwiederholung durch STAY ersetzen. Sonst V14 unverändert; spätere Einheiten im selben Schritt entscheiden mit korrigierter Planung. Alle Frames bis vor dem Eingriff exakt reproduzieren, danach bis Ende von Match 3 spielen. Maximal **48 Alternativpartien**; jede beginnt am echten Spielanfang. Kein Gegner- oder Engine-Deepcopy.
4. Pro Karte die erste vorhandene Alternative einmal vollständig wiederholen: maximal **8 Partien**. Alle Archivframes identisch. Keine wiederholte Schutzpolicy und keine zusätzliche Variantenwahl in dieser Phase.

Gesamt maximal **88 × 303 = 26.664 Engine-Schritte**, keine versteckten Teilfortsetzungen. Erst Technik auf `9946007/player_0` und `2000000/player_0` einschließlich ihrer bereits eingerechneten Alternativen/Wiederholungen; tatsächliche Abnahme vor restlichen Schlüsseln. Ein Modellworker, keine Tests parallel. Technischer Fehler stoppt die Aufnahme; kein automatischer Reparatur-/Wiederholungsstart.

## Technischer Vertrag

Minimaler standardmäßig passiver experimenteller Hook in `Agent_x`, kein Duplikat der ganzen Aktionsschleife. Alle normalen V14- und Trainingspfade bleiben exakt gleich. Der Hook kann ausschließlich den berechtigten SAP dieses Schritts/UIDs zu STAY machen. Er darf keine neue Bewegung, Ziele oder Schüsse erfinden. In der Probe keine allgemeine Produktionsoption aktivieren.

Eingriff nach letzter SAP-Zielwahl und vor `_plan_damage`. Ursprünglichen maskierten Vorschlag vor `_policy_greedy`, Regelherkunft, finalen SAP und korrekte native Spiegelung getrennt archivieren. `_prev_actions`, `_sap_hits`, `_sap_unknown`, gegebenenfalls `_pred_pending` und etwaige Planungsreservierungen müssen zur wirklich ausgeführten Aktion passen. Reservierungen früherer Einheiten erhalten. Korrekturen nur beim tatsächlichen Veto; keine allgemeine Verschiebung der schon vor späteren Regeln gespeicherten `_pred_pending`-Buchhaltung im Standardpfad. Nebelschüsse sind ausdrücklich nicht zulässig; dennoch nachweisen, dass ein verworfener eigener Planungspfad keine fiktive Reservierung hinterlässt. `smart_sap` ist im gebundenen V14 aus; abweichende Config vor Aufnahme zurückweisen, nicht still neue Semantik zulassen.

Öffentliche Beobachtungen, eigenes Gedächtnis und geschätzte Parameter getrennt von externen Enginebelegen speichern. Für die kausale Energiediagnose die tatsächliche Engine-Reihenfolge verifizieren und relevante Zwischenstände instrumentieren; keine Residualrechnung „Energieänderung minus SAPkosten = Gegnerschaden“ als Wahrheit ausgeben. Eine etwaige Passivinstrumentierung muss gegen den unveränderten Engineverlauf geprüft werden. Sind Zwischenstände nicht verfügbar, die fehlende Ursachentrennung ausdrücklich offen lassen; die vollständigen Gegenfakten bleiben das Wirkungsmaß.

## Vorab feste Entscheidung

- **Technik:** alle Originalpräfixe, Referenz-/Sammler-/Wiederholungsläufe, Quellen und tatsächlichen Endlabels korrekt; keine abgefangenen Fehler. Sonst keine fachliche Entscheidung.
- **Ausreichend Wirkung:** mindestens 12 wirksame Paare auf mindestens vier Karten. Dies ist ein Machbarkeitsfilter, kein statistischer Nachweis.
- **Ausreichender Anlass für einen Kandidaten:** mindestens zwei negative ganze Spiele werden auf mindestens zwei verschiedenen Karten zu Siegen; mehr positive als negative ganze Spiel-Flips; Summe der Matchsiegänderungen nicht negativ. Alle Nullfälle und verschlechterten Siegkontrollen berichten. Die Summen sind nur ein Entwicklungsfilter, keine erreichbare Policy-Siegquote.
- Bei Verfehlung schließen: kein automatischer Nachschlag, keine spätere UID, kein fünfschrittiges Veto, kein anderer Energiewert und kein Kopftraining. Der Befund betrifft nur diese eine Ereignis-/Interventionsklasse, nicht jede denkbare Halterverteidigung.

## Erst bei brauchbaren Daten: einen vollständigen Kandidaten bauen

Ein einzelner guter Gegenfakt ist keine ausführbare Entscheidungspolitik. Nach bestandenem Pilot wird in einer **separaten, vor Datenaufnahme festen** Lern-/Validierungsfestlegung entschieden, ob öffentliche Energie-/Bedrohungs-/Punktinformationen positive und negative Fälle trennen. Ein kleiner regulierter Entscheider mit V14 als Rückfall ist der bevorzugte Lernweg; kein großer neuer DQN-/Ensemblelauf und kein Auswählen nur erfolgreicher Beispiele. Architektur, Lernkarten, Gegner, Stoppschwelle und maximaler Eingriffsrhythmus sind vor diesem Folgeversuch festzulegen. Null neue Lernspiele aus dem vorliegenden Plan.

Für genau einen danach eingefrorenen Kandidaten: kompakter Screen auf getrennten frischen Karten, 40 Spiele Kandidat gegen Solution, 40 V14 gegen Solution auf denselben Karten und 40 direkt gegen V14; beide Seiten. Screen nur bei nicht weniger Solution-Siegen, mindestens 24/40 direkten Siegen und null technischen Fehlern nominieren. Ein Gleichstand bei 40/40 soll trotz Direktvorteil nicht künstlich ausgeschlossen werden. Diese 120 Spiele sind eine Vorauswahl, kein Stärkenachweis. Eine einzige vorab begrenzte unabhängige Bestätigung folgt nur bei Nominierung; vor deren Start müssen Spielzahl, Primärmaß, quantitative Stabilitätsgrenzen, Kartencluster-Unsicherheit und Kontrollgegner vollständig feststehen. Unklare Bestätigung bedeutet V14 behalten, nicht bis zum gewünschten Ergebnis verlängern. Nicht hier festgelegte Folgephasen sind **keine gestarteten oder pauschal zugelassenen Jobs**.

Übernahme erst nach belastbar besserem vollständigem Spielverhalten direkt gegen V14 und bestandenen vorab festgelegten Solution-/Kontrollgegner-Stabilitätsbedingungen sowie Laufzeit-/Kursprüfung; vorher Sicherung, Paketprüfung, Hashkontrolle und Übergabe. Ein eigener Verbesserungsanspruch gegen Solution erfordert zusätzlich einen positiven gepaarten Bestätigungseffekt mit entsprechendem Kartenintervall; Gleichstand allein reicht dafür nicht. 100 % auf einem Testsatz bleibt ein ehrgeiziges Stichprobenziel, keine Garantie für alle Karten.

## Zusammenarbeit und Budget

Root implementiert später die zusammenhängende kleine Messung; ein unabhängiger Reviewer prüft die Eingriffsstelle und Daten. Keine vielen parallelen Versuchsarme. Vor jedem Modellstart frische Quota, Prozesse, Source-Freeze und Remote prüfen; tatsächliche Nutzerfreigabe zu selbst überwachten Akkuläufen beachten. Keine Resets, fremde Dateien erhalten. Aktueller Folgeauftrag erlaubt die Umsetzung und den begrenzten Pilot nach technischer Abnahme; weitere Phasen bleiben an die oben festgelegten Gates gebunden.

**Planprüfung 11.11.:** Ein unabhängiger Bestandsreview prüfte die Abgrenzung zu alten Ziel-/HOLD-/Reserveversuchen. Ein frischer Implementierungsreview präzisierte die echte vorab eingefrorene Referenz und ausschließlich vetoabhängige Buchhaltungskorrekturen. Diese Punkte sind eingearbeitet; keine Modell-/Spiel-/Testausführung in der Planprüfung. Spätere Bestätigung weiterhin separat quantitativ festlegen.
