# Residualer V14-Pilot, 10.11.2026

Freigegebene [Spec](../../../docs/superpowers/specs/2026-11-10-residual-ensemble-design.md)
und [Plan](../../../docs/superpowers/plans/2026-11-10-residual-ensemble.md).
**Abgeschlossen, negativ:** Beide Kandidaten scheitern in200 festen Auswahlspielen.
V14/ZIP bleiben unverändert. [Endergebnis](ERGEBNIS.md),
[Trainingsbericht](TRAININGSERGEBNIS.md). Keine weitere Phase starten.

## Methode

Die ursprünglichen 36 Netze bleiben eingefroren. Ein zusätzliches Dueling-Netz
lernt eine **additive** Korrektur ihres Mittelwerts. Initialisiert aus Mitglied
18, ausschließlich beide letzten Ausgabeschichten null. DDQN verwendet in
Vorhersage, Online-Auswahl und Target durchgängig M+R. Adam besitzt nur R.
Kein normaler 37er-Export und keine Skalierung der ursprünglichen Gewichte.

Der Akteur bleibt im Auswertungsmodus mit vollständiger Regelkette. Epsilon
0,05 verändert erlaubte Vorschläge vor den Regeln; Auswertung verwendet 0.
Ein Übergang wird beim nächsten tatsächlichen Aktionsaufruf vervollständigt,
damit Parameterschätzung, Belief und Merkmale exakt dessen Reihenfolge haben.
Lernen erfolgt danach in update(), um keinen laufenden Einheitenzug zu ändern.
Matchgrenzen und Spielende verwenden einen separaten öffentlichen Rewardkontext
mit kopiertem Belief, der keine Ziele im aktiven Akteur überschreibt.

Die 300 nichtleeren Matchschritte pro Spiel ergeben bei train_every=2 genau
150 Updates. Gemeint sind gültige Zeitschritte; ein solcher Schritt kann auch
keine lebende Einheit haben. Nullschritte beim Matchreset zählen nicht.
Terminale Folgezustände werden als Nullmerkmale mit STAY-Maske gespeichert;
ihre echten M(0)-Werte bleiben enthalten, obwohl der Bootstrap durch done entfällt.

Replay und rohe M-Werte teilen einen Ringindex, Schreibgeneration und
SHA256-Bindung einschließlich float32-Merkmalsbytes und finaler Weltaktion.
Physische Reihenfolge wird beim Speichern erhalten. Der Modellhash bindet auch
die Reihenfolge der originalen 36 Mitglieder. Direkte numerische Cacheprüfung:
rtol=1e-5, atol=2e-5; unterschiedliche Batchgrößen können Rundungen verändern.

## Grenzen der Diagnose

Rohvorschlagsänderung, Exploration, Abweichung der finalen kanonischen Aktion
vom Vorschlag und Rückkehr zum rohen Basisvorschlag werden gezählt. Das sind
**keine kausalen Anteile finaler Residualwirkung oder ihrer Aufhebung durch
Regeln**: Dafür wäre eine zweite isolierte Auswertung der ganzen Regelkette
erforderlich. Diese zusätzliche Gegenfaktualsimulation gehört nicht zum Pilot.
Der ursprüngliche Diagnosewunsch wird daher enger und ehrlich ausgewiesen.
SAP-Offsets und tatsächliche finale Aktionen sind dennoch im Replay gebunden.
Die vollständige Null-R-Parität wird anhand beider tatsächlicher Spielverläufe
geprüft. Das DDQN-Target bleibt eine Approximation der nachgelagerten Regeln.

## Feste Phasen und Bedienung

1. `technical`: genau 8 Ausführungen, Stock aus Commit346e013 gegen Null-R mit
   aktivem passivem Sammler, auf zwei bekannten Schlüsseln gegen Solution/V14.
2. `training`: Starts61/62 je40 Vorlauf und80 Lernspiele, exakt12.000 Updates.
   Nach den Vorläufen warten die bestehenden Worker auf eine tatsächliche
   Root-Abnahme der gespeicherten Artefakte; keine automatische Lernfreigabe.
3. `selection`: genau200 Spiele, beide Starts müssen die festen Gates erfüllen.
4. Nur danach `confirmation`: genau600 Spiele für höchstens einen festen Kandidaten.
5. Export/Kursprüfung nur nach erfolgreicher Bestätigung; bisherige Abgabe bleibt.

`python -B -m scripts.residual_ensemble_run launch --phase technical` startet
ausschließlich die angegebene Phase in dieser Studienkopie. Vorher benötigt der
Launcher einen frischen echten Kontingentbeleg unter
`/private/tmp/sherlock-residual-usage.json`, die Originalquelle aus
`git archive 346e013 agents/sherlock` als Paket `original_sherlock` unter
`/private/tmp/residual-v14-original-20261110/`, und die geprüften Kartenbelege.
Alle tatsächlichen Quellen/Eingaben werden im Phasenstatus gehasht. Bestehende
Phasenordner verhindern Neustarts. Maximal zwei eigene Worker, bestehende
Rechensperre und Prozessüberwachung, keine parallelen Tests. `STOP` in diesem
Studienordner beendet die eigene Phase. Eine Folgephase benötigt `accepted.json`
mit dem Hash des tatsächlichen vorherigen `completion.json`.

Ab92% Kontingentverbrauch kontrollierter Abschluss, mindestens5% Reserve;
keine Resets. Akkubetrieb gemäß ausdrücklicher Nutzerfreigabe erlaubt.

## Karten und Übergabe

[Einmaliger Kartencheck](seed_audit.json): keine beobachtete Vornutzung der280
reservierten Karten in den beiden geprüften Checkouts. Seedlose Daten,
untersuchte Dateiformate und ausgelassene JSONL-/externe Historien sind konkret
im Bericht begrenzt; kein Anspruch auf globalen Nichtgebrauch. Historische
abgeschlossene Versuche werden nicht erneut gestartet.

[Erster unabhängiger Kernreview](CORE_REVIEW.md): Lernkern ohne Blocker;
Diagnosebegriffe eingegrenzt und echte synthetische Sammlertests ergänzt.
Neue Werkzeuge sind experimentell. Das Abgabemodell und die ZIP wurden nicht
verändert. Ergebnisse werden erst nach tatsächlichen vollständigen Läufen
mit Unsicherheiten und unveränderten Freigabebedingungen ergänzt.
