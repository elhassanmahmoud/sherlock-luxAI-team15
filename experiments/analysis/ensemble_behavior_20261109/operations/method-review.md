# Methodenreview: Ensemble-Verhalten beim Einzelnetztraining

**PASS für die maßgebliche Spec und den Plan; keine offene methodische oder grundsätzliche Implementierungsblockade gefunden.** Das ist eine Vorabprüfung des Vertrags, keine Abnahme noch nicht vorhandener Implementierung, Tests, Modelle oder Laufdaten.

Der Eingriff ist klar begrenzt: eigener DDQN-Lerner und originale Kontrollrewardformel, aber während der tatsächlichen Handlung der geordnete Mittelwert aus 35 unveränderten Originalmitgliedern und dem aktuellen Lernoutput an Position 18. Eigene q/Target/Adam-Identitäten bleiben erhalten. Der Instanzhook lässt sich auf `_act_est` beschränken; im gelesenen Core erfolgt `_learn` separat über `_update`. Das Originaltraining benötigt daher weder Ensembletargets noch einen neuen Replaypfad. Matchstart und fehlende aktive Units dürfen weiterhin ohne Q-Forward bleiben.

Zwei feste ON-Starts 48/49 mit je 40 Vorlauf- und 400 Lernspielen, eine gemeinsame manuelle Barriere, kein neuer Kontrolllauf und vier bekannte technische Spiele ergeben genau **884 neue Ausführungen und 120.000 Updates**. Start 49 erhält nur eine zusätzliche Initialprüfung ohne Spiel. Beide historischen Kontrollfinals sind vorab festgelegt; keine Auswahl des besseren Starts. Die spätere 200er-Auswahl und alle vier tatsächlichen Sieggates sind bereits fest, keine automatische Bestätigung oder Promotion.

## Bindende Punkte für die spätere Implementierungsabnahme

- Exakt 36 geordnete Beiträge je aktiver Handlung: aktuelles q an Index 18, niemals zusätzlich das alte Mitglied 18. Keine Aliase, eingefrorene Gradienten oder Adamzugehörigkeit. Aufbau erhält Python-/NumPy-/Torch-/Agent-RNG, CPU/Gerät/Threads werden explizit gebunden. OFF führt weder zusätzliche Forwards noch RNGverbrauch ein.
- Hook nur im Handlungsaufruf, auch bei Ausnahme entfernt; vorheriger Instanzzustand exakt wiederhergestellt. Auf identischem synthetischem Replay und RNG muss das tatsächliche originale `_learn` mit ruhendem Adapter dieselben q-/Target-/Adamzustände erzeugen. Roh-Q-Belege vor der Core-Numpy-Maskierung kopieren; Masken und UID-Reihenfolge passiv aus dem einzigen tatsächlichen Entscheidungslauf beziehen.
- Historische Kontrollaufnahmen, Abschlüsse, Receipts, Modelle, Kontrollkonfiguration, Startpläne und alte gebundene Runtimebytes prüfen; keine alte Admission gegen neuen HEAD aufrufen. OFF reproduziert die beiden bekannten Fälle in originaler kumulativer Reihenfolge und mit unverändertem Initialisierungs-/Envzeitpunkt. ON belegt auf denselben Fällen eine geänderte legale Präferenz sowie tatsächliche finale Aktionsänderung, korrekte Rewards/Replaylabels und null Updates. Keine ON/OFF-Trajektoriengleichheit verlangen.
- Beide tatsächlichen 40er-Vorläufe müssen vollständig und getrennt korrekt sein: Initialgewichte/Target/frischer Adam, null Lernen, eigene gespeicherte Replays und Kontrollrewards, aktive Hookbelege und unveränderte 35 Tensoren. Erst ein gemeinsamer an beide Vorlaufhashes und Rootreview gebundener manueller Release erlaubt den Originalworkern Gradienten. Keine einzelne vorzeitige Freigabe, Ersatzkontrolle oder Wiederaufnahme.
- Abschluss nur mit je 440 vollständigen Spielen, 193.320 Envschritten, 60.000 tatsächlichen Adamupdates, endlichen Lernbelegen und richtigen finalen Einzelnetz-/Target-/Adam-/Replaydateien. Die 35 Verhaltensnetze gehören nicht als zusätzliche Kandidaten ins Einzelnetzcheckpoint. STOP/Quota/Fehler sichern unvollständig und starten nichts neu.

## Zwei überholte Kontextstellen

Der externe Bauvertrag enthält noch (Abschnitt 2) getrennte `start48`/`start49`-Phasen und Start 49 erst nach Abnahme von 48. Sein Schlussabsatz erwägt bei fehlender Treue ein frisches Kontroll-/ON-Ersatzpaar. **Beides ist durch die endgültige Spec und die ausdrückliche Rootwahl überholt:** eine Trainingphase mit `on48` und `on49`, gemeinsame Barriere; bei fehlender technischer Treue/Exposition stoppen, kein Fallback. Der Plan erklärt den Vorrang der Spec bereits ausdrücklich. Root hat anschließend ausdrücklich bestätigt, dass beide Vorschläge verworfen und im Ledger beziehungsweise Taskbrief-Preamble als überholt abgegrenzt sind. Die originale externe Machbarkeitsdatei bleibt historisch erhalten; Spec, Plan und aktueller Taskbrief sind bindend. Diese Root-Klarstellung schließt den Dokumentationshinweis; keine Methodenänderung und kein offener Blocker. Ledger/Taskbrief wurden hier nicht zusätzlich nachgelesen.

## Grenzen der späteren Aussage

Historische Kontrollen sind vertretbare fest gebundene Referenzen, keine gleichzeitig neu ausgeführten Kontrollreplikate. Zwei bekannte OFF-Reproduktionen und Quellen-/Initialbindungen ersetzen keine fehlenden historischen vollständigen Bibliotheksbinär- oder RNG-Snapshots; diese Grenze bleibt offen. Reproduktionsfehler dürfen nicht als negativer oder positiver Leistungsbefund umgedeutet werden.

Der Actor bleibt ein veränderlicher 36er-Trainingsactor mit Exploration und bisherigen Trainingsregeln. Das spätere 38er-Evalensemble enthält zusätzlich die ursprünglichen 36 und beide neuen Finals; der Eingriff reduziert die vermutete Verhaltensabweichung, beseitigt sie nicht vollständig. Kein behaupteter vollständiger V14-Evalactor und kein vorweggenommener Kausalnachweis für frühere Misserfolge. Der kleine feste Screen nominiert bei Bestehen nur; seine Kartenbootstrapintervalle sind deskriptiv ohne Korrektur über frühere Projektversuche.

Gelesene Bytefassungen, SHA256:

- Spec: `3fbad1bb1f283e9719463e94d438600270e0878809d3d995ce05382ab8a1a7fb`
- Plan: `d2b706abc9701f01498edae84f042d874188381a08ae23cd703625c5d9dd4b9b`
- Externer Bauvertrag: `91c7952818d7743c26e729702d5013d3534cc1468175a9c55fa557b63c669ef1`

Nur Quellen und Unterlagen gelesen und diesen externen Bericht geschrieben. Keine Projektimporte, Codes, Tests, Modelle, Spiele oder Freigabe ausgeführt.
