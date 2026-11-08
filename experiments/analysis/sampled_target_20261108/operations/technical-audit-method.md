# Unabhängiger Prüfer der vier Sampled-Target-Technikspiele

**PREPARED / UNRUN.** Der Prüfer wurde ausschließlich als Text außerhalb des Repositorys vorbereitet. Kein Import, Compile, Test, Modell, Spiel oder Auditlauf wurde in diesem Auftrag ausgeführt. Receipt-/Transcript-/Supervisoranbindung ist gegen die unten gebundenen stabilen Schnittstellen ausgearbeitet. Das ist noch keine Syntax- oder Funktionsabnahme dieses Auditors. Root prüft den Code und autorisiert eine Ausführung erst, nachdem alle vier technischen Jobs beendet sind.

## Enger Prüfgegenstand

Genau `technical_control_p0`, `technical_sampled_p0`, `technical_control_p1`, `technical_sampled_p1`: Karte 4242 gegen default, Initialisierungsanker 45, jeweils frische Einzelagentinstanz ab Komponente 18, 303 tatsächliche Schritte, `learn_enabled=False`, null Updates. Kein Trainings-, Vorlaufgate-, Leistungs- oder Promotionsaudit. Keine Wiederholung oder zusätzliche Partie bei einem Befund.

Die implementierende Stelle benennt folgende geplante Runpfade:

`experiments/runs/20261108_sampled_target_technical_{control|sampled}_p{0|1}/`

Darin `technical_receipt.json`, das genau neun Artefakte bindet: `manifest.json`, `rollouts.jsonl`, `technical_proof.json`, `initial_agent.pth`, `technical_agent.pth` sowie `prefill/{bundle.json,replay.npz,provenance.jsonl.gz,trajectory.jsonl.gz}`. Die Vorbereitung liegt getrennt und enthält `manifest.json`, die initialen Komponentendateien und `supervisor_launch.json`.

Der abgeschlossene Supervisorzustand ist `stage="technical"`, `status="done"`, `active=[]`, `queue=[]`, `paired_prefill={}`, vier exakte `jobs` und `receipts`; `technical_pairs` hat genau `player_0`/`player_1`. `receipts[job]` ist `{absoluter_Receiptpfad: SHA256}`. Alle Worker-Returncodes sind null; auch das eigene Wachhalten hat einen protokollierten Endcode. Der zweite Seitenvergleich darf erst nach beiden Exits des ersten beginnen.

## Gebundene Schnittstellen und spätere Ausführung

Die unabhängigen Momentaufnahmen bleiben außerhalb des Repositorys erhalten:

- `/tmp/sampled-target-technical-worker-interface-40d18c9.py`: stabil installierter Worker, SHA-256 `40d18c9a8ad8c3ef9b497ce260b533a93e2581a6c7c158a06712d89537aee224`.
- `/tmp/sampled-target-technical-supervisor-interface-snapshot.py`: stabil installierter Supervisor, SHA-256 `df85b767962cffc9c903da86b4ac4f539143ef7b0b0faa24f21e017c2687d07d`.
- `/tmp/sampled-target-technical-audit.py`: vorbereiteter unabhängiger Auditor, SHA-256 `384a0467a64e5b23a8e81cb5134321c79c0cad78c39a55e5411b3b324c14a408`.

Der frühere Worker-Snapshot `/tmp/sampled-target-technical-interface-snapshot.py` mit SHA-256 `ab10837d2d945fd51bd3f6978f5ca9cea0fd46851d00eaf9f8eb9c062ef18fa6` bleibt als historische Vorbereitung erhalten. Der Adapter berücksichtigt die Änderungen zur stabilen Fassung: atomare Publikation, strengere Ereignistypen, erforderliches Seed-Auditinventar und mindestens ein nichtterminales Folgelabel. Diese Referenzhashes beschreiben den Entwurfsmaßstab; die später tatsächlich verwendete Quelle wird vollständig aus den realen eingefrorenen Laufbelegen gebunden. Bei einer späteren Schemaänderung muss Root den Adapter vor Ausführung erneut abgleichen.

Der spätere Aufruf hat ausschließlich drei erforderliche Argumente:

```text
<gebundener Python-Interpreter> -B /tmp/sampled-target-technical-audit.py
  --state <absoluter Pfad zum beendeten technischen state.json>
  --state-sha256 <extern nach Ende aller Jobs festgestellter SHA256>
  --out <neue JSON-Datei in einem bereits bestehenden Ausgabeordner>
```

Dies ist eine Aufrufbeschreibung, kein ausgeführter Befehl. Keine automatischen Start-, Wiederholungs- oder Warteaktionen. Der Root-gebundene Endstate ist der einzige Einstieg; fehlende/unfertige/falsche Belege führen zu Exit 1 und `AUDIT BLOCKED` auf stderr. Ein PASS-JSON entsteht erst nach allen Gegenprüfungen und einer erneuten Byteprüfung sämtlicher verwendeter Dateien. Bestehende Ausgaben werden nicht überschrieben. Das JSON enthält ausdrücklich `eligible=False`, die vollständige Eingabehashliste, Originalbefehle, vier Receiptreferenzen, je Seite alle überprüften Nenner und die Aussagegrenzen. Es ersetzt keine Root-Startentscheidung.

## Unabhängige Datenstrategie

1. Root bindet den abgeschlossenen historischen Supervisorzustand extern per SHA-256. Der Auditor soll daraus die genau vier erfolgreichen Befehle, deren echte Runverzeichnisse, Receipts und die ursprüngliche Vorbereitung/Startzulassung erschließen. Fehlende oder zusätzliche Jobs, Wiederholungen, unvollständige Endzustände und nicht gebundene Befehle sperren die Abnahme.
2. Alle Receipt-/Bundle-/Provenance-/Replay-/Checkpointdateien, die Vorbereitung, Zulassungsbelege, eingefrorenen Quellen, der Interpreter und die Schutzdateien werden anhand ihrer tatsächlichen gespeicherten Bytes geprüft. Kein Vertrauen allein in `status=done` oder `reload_pass=True`. Der Ergebnisbericht bindet die verwendeten Eingaben erneut und verändert keine historischen Dateien.
3. Der Auditor lädt ausschließlich Tensor-/Optimizerdaten aus den gespeicherten Checkpoints mit `torch.load(..., weights_only=True, map_location='cpu')`. Keine Agentklasse, Netzinstanz, Forwardberechnung, RNG-Ziehung oder Projektfunktion wird importiert/ausgeführt. Q und Target werden nach Namen/Dtype/Shape/Bytes gehasht, Adam als vollständiger typisierter Zustandsbaum. Frischer leerer Adam, unveränderte Parametergruppen, null Lernschritte sowie identische initiale/finale Tensoren werden direkt gegen die Daten geprüft.
4. Alle Provenanceereignisse eines Spiels werden offline indiziert und anschließend vollständig gegeneinander sowie gegen jede NPZ-Zeile verknüpft. Es gibt genau ein Episodeereignis und 303 aufsteigende, bestätigte Frames; jeder Frame erfasst seine vollständige native Ausgabe und geordnete Unitliste. Alle Capture-/Commitidentitäten müssen eindeutig sein und in derselben Originalreihenfolge auftreten. Kein Pendingrest darf übrigbleiben.
5. Für jede nichtterminale Zeile sind Episode/Match/UID, Folgeschritt, verwendete Feature-/Maskenbytes, endgültige Folgeklasse und der vor dem bestätigenden Update gesicherte Env-Zähler nachzuweisen. Die Bestätigung erfolgt im tatsächlichen Nachfolgerframe vor dessen neuen Captures. Terminale Zeilen haben beide Sentinels −1; vollständig terminale Batches werden erst nach vollständiger aktueller Capture committet, gemischte Batches gemeinsam im Folgeupdate. Finale SAPs außerhalb der Netzmaske werden erhalten, nicht nachträglich korrigiert. Kein `a[i+1]` und kein Test biologischer Respawnidentität.
6. Schema, Dtypes, vollständige Reihenfolge und tatsächliche Bytes aller zwölf Replayarrays werden geprüft. Rewards aus den Ereignissen werden gemäß der persistierten float32-Darstellung verglichen. Native Bewegungsrichtungen werden für player_1 unabhängig mit der festen Antidiagonalspiegelung 1↔2 und 3↔4 nachgerechnet; STAY/Bewegungen dürfen keine SAP-Vektoren tragen. Ein SAP-Wirkungsnachweis wird daraus nicht abgeleitet.
7. Das passive Engine-Transcript enthält genau 607 Records: Reset 0, danach jeweils submitted 0/result 1 bis submitted 302/result 303. Jede Zeile trägt Episode 0, Art, Schritt und exakten Digest; submitted zusätzlich beide tatsächlich übergebenen nativen Aktionsarrays. Eigene Aktionen werden mit der Agentprovenienz verknüpft. Der Prüfer rekonstruiert unabhängig auch den Digest jedes submitted-Tupels aus beiden Aktionsarrays; die gebundenen Sherlock-/default-Quellen erzeugen hier native int64-Arrays. Der Verlaufshash wird aus sämtlichen 607 ASCII-Digests neu gebildet. Die ganze Recordsequenz wird zwischen Kontroll- und Sampled-Modus je Seite verglichen. Roh-Enginearrays werden nicht zusätzlich archiviert: die reset/result-Digests können deshalb nicht unabhängig aus Rohzuständen neu berechnet werden. Ihre Paaridentität und Bindung an den eingefrorenen Recorder werden geprüft und die Grenze ausdrücklich berichtet.
8. Initiale/finale RNG-Identitäten, sämtliche erweiterten Replaybytes, Ereignisse, Trajektorien und Spielzeilen außer der ausdrücklich ausgenommenen Laufzeit müssen je Seite gleich sein. Gewinner werden als technische Metadaten erhalten, niemals zur Auswahl oder als Stärkenachweis interpretiert.

## Grenzen

Die Prüfung ist eine Abnahme gespeicherter Daten unter gebundener Laufquelle. Sie reproduziert keine Engineausführung und beweist nicht unabhängig, dass ein aufgezeichneter Befehl die beabsichtigte Bewegung oder SAP-Wirkung hatte. Core-Terminaldefinition und ihre bekannten Lebensidentitätsgrenzen bleiben bestehen. Gespeicherte RNG-Digests sind Identitätsbelege, keine Rekonstruktion eines nicht archivierten vollständigen Zufallszustands. `learn_enabled=False` und die tatsächlichen sauberen Objektgrenzen werden durch die gebundene Laufquelle vor/nach dem Spiel geprüft; der Datenprüfer rekonstruiert null Updates und vollständig geschlossene Frame-/Transitionbelege. Auch ein späteres PASS ist weder Studienstart- noch Abgabefreigabe; Root entscheidet separat anhand der verbleibenden Aufnahmebedingungen.

Der Auditor importiert keine Implementierungshelfer. Die wenigen dokumentierten Dateihash-, Tensor- und typisierten Bytekodierungen sind eigenständig nachgebildet, damit unabhängige Neuberechnung und Abgleich mit historischen Feldern möglich bleiben. Der semantische Prüfweg arbeitet mit vollständigen Offline-Verknüpfungen statt der Laufzeit-Zustandsmaschine des Studienrunners.
