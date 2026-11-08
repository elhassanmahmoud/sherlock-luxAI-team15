# Unabhängiger Abschlussaudit: Sampled-Target-Training

**TEXT PREPARATION / UNRUN.** Dieser neue Auditor wurde ausschließlich als Text außerhalb des Repositorys erstellt und statisch gelesen. Kein Python-Import, Syntaxcompile, Test, Tensorladen, Forward, Audit oder Spiel wurde während der Vorbereitung ausgeführt. Die laufenden Trainingsdaten wurden nicht ausgewertet. Root muss die Codeprüfung abschließen und die tatsächliche Ausführung gesondert anordnen, nachdem alle vier Worker, Supervisor und Wachhalter beendet sind.

## Fester Umfang und Versionen

Genau vier Rollen `control45`, `sampled45`, `control46`, `sampled46`; je 40 Vorlauf- und 160 Lernspiele, 200 Ausführungen, 24.000 Updates und Endzähler 120.600. Gesamt 160 Vorlauf- plus 640 Lernspiele, 96.000 Updates, 242.400 tatsächlich ausgeführte Env-Schritte. Keine Leistungsbewertung, Folgestudie, Wiederholung oder V14-Promotion.

Der Maßstab ist die eingefrorene Trainingsquelle `945e1938a1fb1fcc87eeaf10b58138a409266581`. Außerhalb des Repositorys gesicherte Schnittstellen:

- `/tmp/sampled-target-training-worker-interface-945e193.py`: `40d18c9a8ad8c3ef9b497ce260b533a93e2581a6c7c158a06712d89537aee224`.
- `/tmp/sampled-target-training-supervisor-interface-945e193.py`: `e6d5bb238fe0fd4d27f00c103ec4824f04c01ce3b7a5cd51297b877c5a1bb443`.
- Neuer Auditor `/tmp/sampled-target-training-audit.py`: `22dec771a1e970a6c9c0cc11ac8eacd00cba36ad50196e4d94cb6f2a88785428`.
- Wiederverwendete eigene unabhängige Hash-/Bytekodierung `/tmp/sampled-target-technical-audit.py`: `384a0467a64e5b23a8e81cb5134321c79c0cad78c39a55e5411b3b324c14a408`.

Der Support ist der zuvor unabhängig verfasste technische Datenprüfer, kein Studien-/Agenthelper. Sein SHA wird vor jedem Import geprüft; sein `main()` wird nicht aufgerufen. Root hat dessen tatsächlichen Lauf nach den vier Technikspielen als Exit 0/PASS gemeldet, Rohbericht `operations/technical_v2_audit.json`, SHA `d6be0ee133955b7c64309962a8bd629eb1f8ebf695c0bf8ec49737a196274158`. Das ist ein historischer Nachweis des Supports, kein Test dieses neuen Trainingsauditors. Die vier bekannten Technikspiele und der archivierte frühere Launcherfehler mit null Spielen bleiben getrennt von den 800 Studienausführungen.

## Datenprüfung

1. **Historische Aufnahme und Ausführung:** Einstieg ausschließlich über den nach vollständigem Ende extern gepinnten SHA des Studien-`state.json`. Vor dem Import von NumPy/Torch verlangt der Prüfer vier abgeschlossene Jobs und den Endcode des Wachhalters. Anschließend prüft er das gesamte feste Profil, beide Startpaare, genau vier Receipts, originale Befehle/PID-/Gruppen-/Elternbindungen, Rückgabecodes und Zeitintervalle. Paar 46 darf erst nach beiden Exits von Paar 45 begonnen haben. Das ursprüngliche `supervisor_launch.json` bleibt gebunden.
2. **Quellen und Inputs:** vollständige SourceIdentity einschließlich HEAD, neu abgeglichenem Dateiinventar, Interpreter und Enginequellen; tatsächliche Schutzdateien einschließlich beider V14-Dateien und ZIP; ursprüngliche Root-Studienzulassung, Seed-Abnahme samt Rohscanbindung, technische Abnahme und deren Artefakte. Die tatsächlichen Bytes aller Eingaben werden vor Verwendung und nochmals vor Ausgabe geprüft. Der ursprüngliche V14-Checkpoint wird ausschließlich als Tensorcontainer gelesen; Komponente 18 wird direkt gegen sämtliche Anfangsnetze geprüft.
3. **Exogene Pläne:** genau die festen Karten-/Seiten-/Phasenfolgen für Starts 45/46 und 40+160 Spiele; Kontroll- und Sampled-Plan pro Start elementweise gleich. Alle tatsächlichen 200 Rolloutzeilen werden gegen den unveränderlich vorbereiteten Plan geprüft. Gegner müssen aus der festen Viererrezeptur stammen. Der ursprüngliche Zufallszug der Gegnerfolge wird nicht erneut gezogen; seine vorab gebundene vollständige Folge ist der Prüfgegenstand. Keine RNG-Ziehung im Auditor.
4. **Vollständige Provenance:** spielweise Offline-Verknüpfung aller Episode-/Frame-/Capture-/Commit-/Bestätigungsereignisse. Genau 303 Frames und bestätigte Engineübergaben pro Spiel, passende Match-/UID-/Feature-/Masken-/Folgebefehlsidentität, ursprüngliche Commitreihenfolge, korrekter Vorakt-Zähler, Terminalsentinels und keine offenen Captures/Labels. `empty_captures` wird aus den tatsächlichen leeren Frame-Unitlisten neu gezählt. Keine neue Survivalheuristik oder Behauptung biologischer Lebensidentität.
5. **Replay und Ring:** alle zwölf Arrays mit exaktem Schema/Dtype und endlichen Werten. Jede Zeile des vollständigen Vorlaufpuffers sowie jede tatsächlich aufbewahrte Zeile des finalen Rings wird über ihre globale Commitordinalzahl zugeordnet. Die finale NPZ speichert die chronologische Reihenfolge; nach Ringüberschreibung ist der Index `ordinal − (total_committed − retained_size) − 1`. Jede aufbewahrte Zeile wird genau einmal einschließlich Zustand, Folgezustand, Maske, float32-Reward und Labels geprüft. Auch die nicht mehr aufbewahrten Übergänge bleiben vollständig über ihre Provenanceverknüpfungen geprüft; ihre früheren Rohfeaturearrays sind nicht mehr vorhanden.
6. **Engineprotokolle:** pro Spiel exakt 607 Reset/submitted/result-Records; Episode, Schritte, beide nativen Aktionen und gespeicherte Digestwerte vollständig gebunden. Eigene Aktionen müssen zur Agentprovenienz passen. Die submitted-Digests werden unabhängig aus beiden nativen int64-Aktionsarrays rekonstruiert; der komplette Verlaufshash wird erneut gebildet. Die gebundenen vier Gegnerquellen erzeugen hier int64-Arrays. Reset/result-Digests können ohne archivierte Enginearrays nicht erneut aus Zuständen berechnet werden.
7. **Gepaarter Vorlauf:** vollständige Replaybytes, Ereignis- und Trajektoriensequenzen, Spielzeilen außer Laufzeit sowie initiale/finale RNG-Fingerprints müssen pro Start gleich sein. Beide Anfangsnetze, Targets und der frische Adam müssen über den Vorlauf unverändert bleiben. Vorlaufgates binden exakt beide Originalproofs; vorhandene Gate-/Receipt-/Supervisorhashes müssen übereinstimmen.
8. **Unabhängige Vorlauf-Targetrechnung:** Diese Prüfung enthält echte **Offline-Forwardberechnungen** auf den gespeicherten Anfangstensoren. In festen 256er-Blöcken wird die dokumentierte lineare/ReLU-/Dueling-Arithmetik funktional nachgebildet, ohne `Agent_x`, `QNet` oder andere Modellinstanzen. Beide Targetformeln werden aus derselben vollständigen Vorlaufmenge neu berechnet: DDQN mit maskiertem Online-Argmax, Sampled mit bestätigtem historischem Label, terminal exakt Reward. Kein terminales −1-Gather und keine nachträgliche Maskierung eines Sampled-Labels. Alle diskreten Diagnosewerte stimmen exakt; für die aggregierte Targetdifferenz gilt `rel_tol=1e-12`, `abs_tol=1e-9`. Mindestens eine Index- und Targetwertabweichung ist erforderlich. Vor/nach der Offlineberechnung müssen Q, Target, Adam, Replay und die Python-/NumPy-/Torch-RNG-Fingerprints identisch sein. Keine RNG-Ziehung, kein Gradienten- oder Optimizerschritt, keine Änderung persistierter Lernerdaten.
9. **Endnetze und Adam:** ausschließlich `torch.load(weights_only=True, map_location="cpu")`. Exakte benannte Architektur, Formen, float32-Dtypes und endliche Werte aller Q-/Targetparameter; abschließender Targetsync und tatsächliche Änderung gegenüber dem Anfang. Adam hat genau die gebundenen Parametergruppen und für jeden Parameter vollständige endliche Momente passender Form/Dtype, nichtnegative zweite Momente sowie Step 24.000. Alle Rolloutzähler, gespeicherten Agentzähler, ursprünglichen Reloadbelege und Tensorhashes müssen übereinstimmen. Trainingsupdates werden nicht erneut ausgeführt.
10. **Telemetrie:** 24.000 Updates, maximal 6.144.000 gezogene Batchzeilen, konsistente Nichtterminal-/Index-/Target-/Vorzeichen-/Maskenzähler und Labelaltergrenzen. Diese Konsistenzprüfung ist keine unabhängige Wiederholung sämtlicher historischer Trainingsbatches oder Gradienten; deren vollständige Zwischenstände sind nicht archiviert.

Die Provenance wird jeweils nur für ein Spiel im Speicher gehalten. Große finale Replaypuffer werden pro Arm freigegeben; für den direkten Bytevergleich bleiben nur die beiden vollständigen Vorlaufpuffer eines Startpaars gleichzeitig erhalten.

## Aufruf nach gesonderter Root-Anweisung

```text
<gebundener Interpreter> -B /tmp/sampled-target-training-audit.py
  --state <absoluter abgeschlossener Studien-state.json>
  --state-sha256 <extern nach vollständigem Ende festgestellter SHA256>
  --support /tmp/sampled-target-technical-audit.py
  --out <neue JSON-Datei in bestehendem Ausgabeordner>
```

Dies ist eine Beschreibung, kein ausgeführter Befehl. Der Supportpfad kann auf eine bytegleiche archivierte Kopie zeigen; sein fester SHA bleibt verpflichtend. Der Prüfer schreibt nur die neue Ergebnisdatei, startet keine Worker und überschreibt keine bestehende Ausgabe. Bei einem Fehler: Exit 1 und `AUDIT BLOCKED`, kein PASS-JSON. Nach einem Befund keine automatische Wiederholung von Studienläufen.

## Ausgabe für Root und Task 4

Mit `replay_support_review` abgestimmt: Task 4 benötigt mindestens `status="PASS"`, `training_head` und `receipt_sha256` mit genau den vier Rollen. Der Auditor liefert zusätzlich das von Root verlangte vollständige Schema:

```text
schema_version: 1
status: PASS
profile: sampled_target_20261108
training_head: 945e1938a1fb1fcc87eeaf10b58138a409266581
source: <vollständige tatsächliche historische SourceIdentity>
pins: {source: <dieselbe SourceIdentity>, protected: <vollständige Hashmap>}
arms:
  <jede Rolle>: {receipt_path, receipt_sha256, games: 200, updates: 24000,
                env_steps: 120600, checkpoint_path, checkpoint_sha256,
                committed, retained, shared, offline_target_diagnosis, ...}
receipt_sha256: {control45: <SHA>, sampled45: <SHA>, control46: <SHA>, sampled46: <SHA>}
input_sha256: <sämtliche tatsächlich verwendeten und erneut geprüften Dateien>
limitations: <explizite Aussagegrenzen>
eligible: false
```

Die Prüfung liefert keine kausale Stärkeaussage, keine Ergebniswahl und keine Leistungs-/Abgabefreigabe. Root erstellt die historische Gesamtaufnahme für Task 4 separat. Der Prüfer verlangt weiterhin die laufende ursprüngliche Quellenfixierung; ein späterer HEAD-Wechsel ist kein Anlass, einen historischen Originalvalidator als erneut zeitgenössisch ausgeführt darzustellen.
