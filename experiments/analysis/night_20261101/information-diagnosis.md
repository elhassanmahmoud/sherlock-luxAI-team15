# Informationsdiagnose Sherlock, 01.11.2026

Lesestand: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15`, HEAD `93a2ddd`. Nur Dateien gelesen und diesen Bericht geschrieben. Keine Tests, Spiele, Trainings, Seedreservierungen oder Änderungen am Projekt. Fremde unversionierte Dateien (`config 2.py`, `reward 2.py`, `.DS_Store`, Awake-State) unangetastet.

## Empfehlung

Vor dem Battle zuerst **exakte Schlüsse aus teilweise überlappenden Punktegleichungen** als kleinen, standardmäßig ausgeschalteten Belief-Versuch untersuchen. Der aktuelle Code lässt einen algebraisch klar belegbaren Fall offen. Ob dieser Fall in den Restniederlagen oft genug vorkommt, ist noch NICHT gemessen; das muss ein kurzer Beobachtungstrace auf verbrauchten Karten entscheiden, bevor frische Karten oder Training investiert werden.

Ein zweiter, nachrangiger Ansatz ist **lokaler Lernbonus für tatsächlich geklärte Kandidaten, einschließlich Nullbeweisen** bei unverändertem 79er-Eingabeformat. Das adressiert ein belegtes Defizit des Trainingssignals, kostet aber mehr Zeit und braucht einen frischen Replay Buffer. Keine weitere breite Nachtrainingsrunde mit identischem Signal und keine Wiederholung von `cand_post`/`spawn_proof`.

## Was der aktuelle Befund wirklich trägt

- Aktive Abgabe ist V14 `v14_rescue`, 36 Netze, `cand_rescue=true`, `rescue_after=30`. Frisch gegen Solution_92 95,44 %, Übernahme per ausdrücklicher Teamentscheidung trotz knapp verfehltem Gate: `docs/ARBEITSSTAND.md:29–46`, `docs/EXPERIMENT_PROTOKOLL.md:3`, Manifest `experiments/releases/20261101_v14_rescue.json`.
- Engster belegter Informationsengpass ist **das frühe Erschließen bekannter Relic-Zonen**, besonders bei Sichtweite 1. Orakel auf den 72 Dev-A-Karten mit Sicht 1: Solution_92 85,4 % normal, 90,3 % nur Relics, 94,4 % nur wahre Punkte/Nullfelder um bereits bekannte Relics, 96,5 % beides. Am Ende 15,6 statt 17,0 bekannte Punktefelder: überwiegend Verzögerung statt dauerhaft fehlendem Endwissen. `docs/ARBEITSSTAND.md:149–155`, `docs/EXPERIMENT_PROTOKOLL.md:17–19`.
- Die Diagnose meldet 30–40 Schritte zur Klärung einer neuen Zone, etwa ein getestetes Kandidatenfeld je Schritt, Beispiel 800048. Das erste Relic bzw. der erste eigene Punkt ist im Mittel nicht später als bei Solution_92. `docs/EXPERIMENT_PROTOKOLL.md:16`, Battleplan `docs/superpowers/plans/2026-10-29-battle-push.md:568–576`.
- Die Orakelwirkung ist eine obere Diagnosegrenze, kein umsetzbarer Gewinn. Das Werkzeug liest explizit `env.state` und verbietet seine Verwendung für Training/Abgabe: `scripts/oracle_probe.py:6–10,25–31,39–56`. Alle unten vorgeschlagenen produktiven Schlüsse verwenden ausschließlich bestehende Beobachtungen.
- Das alles ist hauptsächlich Dev-A-Diagnose. Es beweist weder, dass jede V14-Niederlage an Information liegt, noch einen zu erwartenden frischen Gewinn von neun Prozentpunkten.

## Warum `cand_post`/`spawn_proof` abgeschlossen sind

Der gewählte `v19cr` kombinierte `cand_post=15`, `spawn_proof` und `cand_rescue` auf V13. Entwicklung, Gewichtswahl und Auswahl des besten von vier Kandidaten nutzten dieselben Dev-A-Karten. Dort +1,81 pp, frisch auf 800 Karten dagegen −0,35 pp [−1,30; +0,59], Solution_92 −0,50, V3 −2,00, `league_nets6` −1,62. Quellen: `docs/EXPERIMENT_PROTOKOLL.md:4–9`, `docs/ARBEITSSTAND.md:48–57`, Battleplan `:619–633`.

Das ist keine frische isolierte Ablation gegen V14: `v19cr` wurde gegen V13 bestätigt; `cand_rescue` allein wurde auf einem anderen frischen Block gemessen. Deshalb lässt sich der Schaden der einzelnen neuen Schalter dort nicht exakt separieren. Es gibt aber keinen belastbaren Grund für eine erneute Bestätigung desselben Pakets. `spawn_proof` allein war sogar schon im Screen −0,28 pp, mit Rescue +0,22 pp; beide nicht zugelassen.

Die Codepfade erklären, was verändert wurde:

- `cand_probs` nimmt das Maximum aus einem anhand kompletter Karten geschätzten Zonenprior und `rest/n` offener Gleichungen; das ist keine gemeinsam konsistente Posteriorverteilung: `agents/sherlock/features.py:158–191`.
- Der Bonus zieht bis zu `15*p` Wegkosten von Kandidaten ab, also können weitere Kandidaten bevorzugt und Wege verlängert werden: `features.py:348–371`. Der alte Befund war bereits laufwegbegrenzt. Eine neue Priorgewichtung wäre damit im Wesentlichen eine Wiederholung derselben, frisch nicht bestätigten Idee.
- `spawn_proof` setzt nur ein Bool, das `_stable` vor Schritt 50 öffnet: `belief.py:508–537`. Es verbessert weder die eigentliche Algebra noch die Wegwahl. `window_infer_all` wurde ebenfalls bereits ohne Gewinn geprüft (`docs/EXPERIMENT_PROTOKOLL.md:234`; `docs/ARBEITSSTAND.md:947,954`). Diese Varianten nicht als neue Versuche ausgeben.

## Ansatz 1: exakte Überlappungsschranken im bestehenden Belief

**Konkreter fehlender Schluss.** `belief.py:569–590` speichert Beobachtungen als `sum(U)=rest`. `_add_differences` überspringt gleiche Mengengrößen sofort und verarbeitet ansonsten nur echte Teilmengen (`belief.py:605–621`). `_propagate` klärt anschließend nur Summen mit null oder maximal vielen positiven Feldern (`:719–741`).

Beispiel zweier gültiger Beobachtungen im selben stabilen Matchabschnitt:

```text
a + b + c = 2
    b + c + d = 1
=> a - d = 1
=> a = 1, d = 0
```

Beide Gleichungen sind einzeln nicht extrem. Keine ist Teilmenge der anderen. Der aktuelle Code überspringt den Vergleich aufgrund gleicher Größe und kann diese beiden Felder aus diesen Beobachtungen nicht klären. Der Schluss ist reine Algebra binärer Punktefelder; kein Wissen über Erzeuger, Seed, Relic-Masken oder Unsichtbares erforderlich.

**Minimalumsetzung, falls die Häufigkeitsdiagnose lohnt:** neuer Belief-Schalter `overlap_infer=false`; im bestehenden Vergleich der neuen Gleichung mit alten, bereits normalisierten offenen Records zusätzlich `L=A\B`, `R=B\A`, `delta=rA-rB` berechnen. Wenn `delta == len(L)`, gilt exakt: alle L positiv, alle R null. Wenn `delta == -len(R)`, gilt das Umgekehrte. Als kleine abgeleitete Gleichungen an die vorhandene Propagation geben. Alte Teilmengenlogik und stabiler Inferenzzeitpunkt bleiben erhalten. Keine globale SAT-Suche, kein neues Netz, keine Wahrscheinlichkeitstabelle, keine vollständige All-Pairs-Schleife.

**Notwendige Invarianten:** vor dem Vergleich aus beiden Gleichungen aktuelle bewiesene Punkte abziehen und entschiedene Felder entfernen; nur zulässige Restwerte akzeptieren. Neue Schlussregel ausschließlich dort aufrufen, wo bisher überhaupt gültige Records entstehen. Bei Widerspruch keine positiven Schlüsse erzwingen; bestehende Recovery respektieren. Match-Reset und neu gefundene Relics behalten ihre bisherigen Gültigkeitsregeln. Standard aus muss bestehende Aktionen exakt erhalten.

**Erster entscheidender Minimalversuch (Vorschlag, hier nicht ausgeführt):** auf einer vorab festen Auswahl bereits verbrauchter Sicht-1-Karten (einschließlich 800048, zusätzlich gewonnene und verlorene Fälle) rein im Schatten zählen, wie oft die neue Regel mehr positive/Nullfelder vor dem nächsten direkten Besuch beweisen könnte; Zeitgewinn der ersten eigenen Punktefelder und zusätzlicher Schlüsse bis Schritt 25/40/60 berichten. Der Agent handelt zunächst unverändert. Wenn fast nie etwas zusätzlich ableitbar ist, sofort verwerfen. Bei realer Wirkung erst schaltbaren Kandidaten auf V14, dann eigener bisher unbenutzter Entwicklungsblock, unverändertes Battle-Gate. Maximal zwei Worker, keine Verwendung der Orakelwerte als Input; etwaige Wahrheit nur offline als Prüforakel.

**Risiken:** Gleichungen könnten selten teilweise überlappen oder der Flaschenhals könnte primär ein fehlender Besuch sein; dann kein Nutzen. Bestehende falsche Nullannahmen durch `keep_dead_fast` können stärkere Schlüsse schneller falsch machen. `MAX_RECORDS=400` (`belief.py:73`), daher zusätzliche Arbeit nur neuer Record gegen alte, keine 400²-Abschlusssuche. Mehr exaktes Wissen kann die Zielzuweisung verändern und muss trotzdem spielerisch bestätigt werden. Das ist ein belegter Code-Gap, bislang kein belegter Leistungsgewinn. Die gelesenen Protokolle/Tests enthalten Teilmengen-Inferenz, aber keinen dokumentierten Versuch dieser Überlappungsschranken.

## Ansatz 2: Kandidatenklärung lokal belohnen, Nullbeweise einschließen

**Belegter Signal-Gap:** `reward.py:115–121` gibt allen lebenden Ausgangs-Units denselben Bonus für `newly_proven` und `newly_explored`. Eine neue positive Entdeckung mit Symmetrie wird in `_mark_point` für beide Kartenhälften gezählt (`belief.py:747–763`), während `_mark_dead` keinen Entdeckungszähler erhöht (`:765–774`). Ein korrekt negativ getestetes Feld erhält somit keinen eigenen Discovery-Bonus; ein untätiger entfernter Halter erhält den gleichen Discovery-Teamanteil wie der Tester. Bewegung zu wechselnd zugewiesenen Zielen wird zusätzlich über Potential belohnt (`reward.py:42–51,139–140`).

Die 79 Merkmale enthalten Zielvektor, nächstes Kandidatenfeld, lokale Kandidatenbits, Belegungen, Sichtweite und Matchphase (`features.py:24–47,747–780`). Sie enthalten keinen Status „dieser Kandidat wurde soeben erfolglos getestet, aber noch nicht logisch aufgelöst“ und keine Gleichungsunsicherheit. Daraus folgt kein Beweis, dass eine neue Eingabearchitektur erforderlich ist. Für einen kleinen Pilotversuch reicht zunächst dasselbe Format mit gezielterem Signal; neue Eingabekanäle würden alle vorhandenen Gewichte/Buffer inkompatibel machen (`main.py:93–104`, `replay_buffer.py:66–74`).

**Minimaler Trainingsversuch:** unverändertes V14-Verhalten und 79 Merkmale, genau eine neue standardmäßig null gesetzte Gewichtung `w_probe`. Einmaliger lokaler Zusatzbonus, wenn eine im Ausgangszustand offene Kandidatenposition nach der nächsten Beobachtung tatsächlich als positiv ODER null bewiesen ist und eine überlebende eigene Unit nun dort steht; bei mehreren Units auf demselben Feld nur einen eindeutigen Besitzer belohnen. Nur tatsächliches neues Wissen, kein Bonus nur fürs Betreten und kein mehrfacher Bonus für gespiegelt dieselbe Information. Keine Orakelziele und keine neue Priorverteilung. Vorab feste kleine Gewichtung statt Koeffizientensuche. Beide Arme aus denselben Einzelnetz-Startgewichten, gleicher Gegner-/Kartenplan und gleiches Budget, ein Kontrolllauf mit `w_probe=0` und ein Versuch, maximal zwei Prozesse. Zuerst Mechanismus (eigene Kandidatenklärungen pro Schritt / Zeit bis mehrere eigene Punktefelder), dann WR prüfen; keine automatische Aufnahme der zwei Netze ins 36er-Ensemble.

**Wichtige technische Stolperstellen:**

1. `make_context` speichert `point_tiles`, `candidate`, `belief` als Referenzen (`features.py:688–701`). `main._update` mutiert den Belief vor dem Reward (`main.py:1475–1488`). Für „vorher offen → nachher geklärt“ muss die alte Kandidatenmenge ausdrücklich als kleine Kopie/set vor dem Update gesichert werden; ein späteres `prev_ctx['candidate']` ist kein verlässlicher Snapshot.
2. Gespeicherte Replay Rewards sind fertige Zahlen (`replay_buffer.py:31–39,63–74`). `finetune.py:115–117` kopiert alte Buffer. Bei neuem Reward darf man alte und neue Bedeutungen nicht blind mischen: frischen Buffer getrennt füllen oder korrekt neu bewerten. Der alte Buffer enthält keine Rohbeobachtungen für diesen lokalen Bonus. Ein sofort leerer Lernstart war historisch schädlich (`finetune.py:9–13`); neue Transitionen zuerst ohne Lernen sammeln.
3. V14-Rescue ist im Training ausdrücklich abgeschaltet (`main.py:377–379,397–398,466–468`), selbst wenn `rules_in_training_all` wahr ist. Ein Trainingspilot darf das nicht unbemerkt als „voller V14-Regelstand“ bezeichnen. Entweder beide Arme bewusst mit identischem bisherigen Trainingsverhalten führen oder dieses Mismatch als separate Änderung festlegen; nicht zugleich Reward und Rescue-Pfad als eine Ablation vermischen.
4. Bonus erzeugt einen möglichen Anreiz, zu lange zu erkunden statt zu punkten. Nur neuen Informationsgewinn zahlen, klein halten, lokale einmalige Vergabe; keine pauschale Erkundungsquote. `cand_quota`, `cand_boost`, `explore_quota`, `sticky` sind ältere erfolglose Spuren und kein Ersatz dafür (`docs/EXPERIMENT_PROTOKOLL.md:225,234`).

Der Reward-Gap ist anhand des Codes belegt. Ein darauf isolierter lokaler Nullbeweis-/Probe-Bonus ist in den gelesenen Protokollen und Tests nicht dokumentiert. Seine Wirkung ist unbewiesen. Die letzte breite Runde mit zwölf nachtrainierten Netzen hatte auf Karten ohne Nebelabzug 25 −0,07 pp und brachte nichts Messbares (`docs/ARBEITSSTAND.md:138–141`; `docs/EXPERIMENT_PROTOKOLL.md:20–22`); das rechtfertigt nur einen klar isolierten Pilot, keine weitere große Runde.

## Entscheidung vor dem Battle

Reihenfolge: (1) vorhandene Beobachtungen auf zusätzliche exakte Überlappungsschlüsse untersuchen; (2) nur bei ausreichender Häufigkeit winzigen Belief-Kandidaten verifizieren; (3) lokalen Reward-Pilot nur bei genügend Restzeit und eigenem vorab festgelegtem Vergleich. Bei ausbleibender Mechanismuswirkung V14 lassen. Frische Entwicklungsdaten und Bestätigung strikt trennen. Dieser Bericht reserviert dafür keine Karten und behauptet keine ausgeführte Verifikation.

## Präzises Minimaldesign und Soundnessbeweis für Ansatz 1

Für zwei gleichzeitig gültige, bereits um bewiesene positive/Nullfelder bereinigte Gleichungen gilt:

```text
sum(A) = a, sum(B) = b, jedes Feld p(t) in {0,1}
I = A ∩ B, L = A \ B, R = B \ A
x = sum(L), y = sum(R), z = sum(I)
x + z = a, y + z = b
0 <= x <= |L|, 0 <= y <= |R|, 0 <= z <= |I|

lo = max(0, a - |L|, b - |R|)
hi = min(|I|, a, b)
=> lo <= z <= hi
=> a-hi <= x <= a-lo, b-hi <= y <= b-lo
```

Alle Grenzen sind ganzzahlig. `lo <= hi` ist nicht nur notwendig, sondern für dieses Gleichungspaar ausreichend: Jedes ganzzahlige z im Intervall erlaubt x=a-z und y=b-z innerhalb ihrer Kapazitäten; da I,L,R disjunkt sind, lassen sich in jedem Teil genau diese Anzahlen binärer Einsen setzen. Keine Unabhängigkeitsannahme und keine Annahme über Punktwahrscheinlichkeiten nötig.

Die kleinste nützliche Spezialregel folgt durch Subtraktion mit `delta=a-b=x-y`:

- **Oberer Extremfall:** `delta == |L|`. Dann `x-y=|L|`, aber x kann höchstens |L| und y mindestens 0 sein. Also zwingend x=|L| und y=0: jedes Feld in L ist positiv, jedes in R null.
- **Unterer Extremfall:** `delta == -|R|`. Analog zwingend x=0 und y=|R|: jedes Feld in L null, jedes in R positiv.
- **Inverse Orientierung:** Tauscht man A und B, tauschen L/R und das Vorzeichen von delta. Die beiden Regeln gehen exakt ineinander über. Es genügt daher ein Vergleich pro neu/alt-Paar; kein zweiter umgekehrter Aufruf.
- **Leere Exklusivmenge:** Wenn L oder R leer ist, enthält die Aussage nichts über die leere Menge. Das reduziert sich auf die bestehende Teilmengen-Differenz; zur Vermeidung doppelter Arbeit den bestehenden Pfad behalten. A=B mit a=b erzeugt keinen neuen Schluss.
- **Alle übrigen Fälle:** keine einzelne Feldklassifikation aus dieser Spezialregel. Insbesondere nie gerundet, geschätzt oder nach Mehrheit entscheiden.

**Widersprüche sind Vorbedingungen, kein positives Signal:** Zunächst `0 <= a <= |A|` und `0 <= b <= |B|` prüfen. Dann `lo <= hi`. Verletzung oder `delta` außerhalb `[-|R|, |L|]` bedeutet ein ungültiges/inkompatibles Gleichungspaar. Beispiel `A={a,b},sum=0` und `B={b,c},sum=2`: delta=-2 liegt unter -|R|=-1. Aus solchem Paar KEINE extreme Null-/Punktgleichung erzeugen. Bei gleicher Menge und verschiedenem Rest liegt ebenfalls ein Widerspruch vor. Im Minimalversuch Inkonsistenzen zählen und Paar auslassen; keine zusätzliche Recovery-Heuristik mit diesem Fix vermischen. Widersprechende Vorschläge derselben Vergleichsrunde (ein Feld soll sowohl Punkt als auch null sein) ebenfalls nicht an `_propagate` weitergeben. Entscheidend: `_propagate` nutzt derzeit `<=0`/`>=len` und kann nicht als Validator neu erzeugter ungültiger Records dienen (`belief.py:730–738`).

**Normalisierung:** Aus beiden Rohrecords bewiesene positive Felder entfernen und deren Anzahl vom Rest abziehen, bewiesene Nullfelder nur entfernen. Mengen müssen eindeutige flache Feldindizes enthalten. Keine Symmetrie-Deduplizierung der besetzten Felder einführen: ein Feld und sein Spiegelfeld sind zwei potenziell gleichzeitig punktende Belegungen, selbst wenn ihr binärer Wert gleich ist. Bestehende `_mark_point`/`_mark_dead` übertragen die danach bewiesenen Einzelwerte bereits korrekt aufs Spiegelfeld.

**Gültigkeit in der Zeit:** Die Algebra kann nur gleichzeitige statische Punktfunktionen vergleichen. Deshalb keine Änderung an `_stable`, Spawnfenster, `reset_match`, `_reopen_dead` oder an der Erzeugung der Records. Das neue Flag muss vom Agenten ausdrücklich an den Belief übertragen werden; Default false. Kein `spawn_proof` als versteckte Voraussetzung des Versuchs.

**Harte Arbeitsgrenze:** Nur die eine neue Gleichung gegen die höchstens `MAX_RECORDS=400` vorhandenen Records vergleichen; keine rekursive All-Pairs-Schließung. Bei M Records und höchstens K Feldindizes pro Record kostet das O(M*K) Zeit und O(K) temporären Speicher pro Paar. Für normale Beobachtungsrecords ist K höchstens die Zahl eigener einzigartig besetzter Felder (maximal 16); bestehende abgeleitete Teilmengen sind nicht größer. Zusätzlich positive und negative Schlussfelder in zwei Sets sammeln (höchstens W*H=576 Einträge je Set), danach höchstens zwei neue Extremgleichungen an die vorhandene Propagation geben. So erzeugt der neue Pfad nicht bis zu 800 zusätzliche Records. Bestehendes Abschneiden auf 400 Records beibehalten; danach keine zusätzliche Abschlussrunde. Der ursprüngliche Teilmengenpfad darf unverändert bleiben. Die gesamte bestehende Propagation hat weiterhin ihre bisherige Fixpunktiteration; die neue Vergleichsphase selbst ist strikt begrenzt.

**Verifikation nach einer später autorisierten Umsetzung:** analytisches Vier-Feld-Beispiel in beiden Orientierungen, keine Folgerung im nicht extremen Fall, identische/ungleiche Restwerte bei identischen Mengen, leere Mengen, Inkonsistenzfälle, bereits bewiesene Werte vor der Normalisierung, Matchwechsel/Spawnfenster sowie unveränderte Aktionen bei ausgeschaltetem Flag. Danach vorhandene Tests und begrenzte feste Beobachtungstraces. Dieser Bericht hat keine davon ausgeführt.
