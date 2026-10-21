# Anschlussentscheidung: höchstens ein kleiner Repräsentationscheck

**Vorschlag nach Abschluss der festen Studie: einmalig prüfen, ob die Kompression auf den nächsten sichtbaren Gegner relevante weitere Gegner aus der Netzeingabe verliert. Noch kein Agentenpatch und keine zusätzliche Spiel-/Trainingsstudie.** In den gelesenen Variantenprotokollen ist dieser eng abgegrenzte Prüfpunkt nicht dokumentiert. Der aktuelle Curriculumvergleich bleibt unverändert; laufende Resultate wurden nicht gelesen.

## Konkreter Anlass und Hypothese

Im bereits ausgewählten Fall **510930/player_1, Match 2, lokal t=78 (global 179), eigene UID7** stehen folgende Werte tatsächlich im Trace:

| Beobachtung bei t | Position | Energie | Manhattan-Distanz zur eigenen Unit |
|---|---|---:|---:|
| eigene UID7 | (19,10) | 125 | — |
| sichtbarer Gegner UID4 | (20,9) | 89 | 2 |
| sichtbarer Gegner UID7 | (19,8) | 150 | 2 |

Die eigene Aktion ist hoch, die gegnerische UID7 zieht nach unten: beide erreichen (19,9). Eigene Maske danach aus, gegnerische Maske an. Dies ist der bereits dokumentierte Anreise-/Konvergenzfall, kein neu gesuchtes Beispiel und keine Schadensattribution.

`features.py:455–469` übernimmt nur Position, Abstand und relative Energie **eines** nächsten Gegners. `np.argmin` wählt im Gleichstand den ersten Eintrag; die Gegner entstehen in aufsteigender Slotreihenfolge (`:299–333`). Hier wird deshalb UID4 mit Energie89 dargestellt, nicht der tatsächlich konvergierende Gegner UID7 mit Energie150. Die übrigen beiden Gegnermerkmale zählen Gegner in Sapreichweite bzw. insgesamt, ohne deren individuelle Energien. Die lokalen Richtungskanäle enthalten Gelände, Feldenergie, Punktwissen und eigene Belegung, keine gegnerische Belegung/Energie.

**Prüfbare Hypothese:** Die aktuelle Netzeingabe kann einen sichtbaren zweiten Ankunftsgegner mit anderer Energierelation nicht unterscheiden, obwohl diese Information in der legalen Beobachtung vorhanden ist. Das wäre ein begrenzter Repräsentationsverlust, keine bewiesene Ursache der gewählten Aktion oder des Spielverlusts. Eigenes Sap und die zurückgenommene unmittelbare Sap-/Kollisionshypothese spielen dabei keine Rolle.

## Ein einziger billiger Prüfauftrag, noch nicht ausgeführt

1. **Isoliertes Feature-Fixture ohne Modell/Engine:** Tatsächliche eigene/Gegnerpositionen und -energien dieses Beispiels verwenden; alle übrigen Kontextfelder konstant halten. Nur die Energie des nicht ausgewählten Gegners UID7 einmal150 und einmal50 setzen. Den tatsächlichen Feature-Code isoliert prüfen: Bleibt der ganze Featurevektor identisch? Als Gegenkontrolle die Energie von UID4 ändern: Dann muss sich das relative Energiemerkmal ändern. Das prüft allein Informationsverlust, keinen hypothetischen Kollisionsausgang oder bessere Aktion.
2. **Relevanz im bereits fest begrenzten Material:** Ausschließlich die vier vorhandenen Locality-Fälle, jeweils lokale Schritte65…85: 510858/p1/M2, 510858/p0/M2, 510847/p0/M3, 510930/p1/M2. Nenner sind sämtliche nichtnegativen eigenen Bewegungsentscheidungen in diesen84 Übergängen. Zählen, wann ein bei t sichtbarer Gegner tatsächlich auf denselben Zielort zieht, ob dieser im nächsten-Gegner-Merkmal fehlt, und den aufgezeichneten Folgezustand separat berichten. Keine neuen Karten/Fenster nach dem Ergebnis wählen, keine Energiequelle zurechnen.

**Vorab-Stopp:** Scheitert das Feature-Fixture oder bleibt der konkrete Konvergenzbefund auf die schon bekannte eine Karte beschränkt, diesen Pfad schließen. Ein weiteres Auftreten auf mindestens einer anderen der bereits festen Karten wäre nur ein praktischer Anlass zur späteren Repräsentationsdiskussion, kein statistischer Gate-Erfolg und keine Freigabe für neues Training. Diese Zweikartenregel ist eine Aufwandsschwelle, kein Wirksamkeitsnachweis.

Für diesen Auftrag sind **keine zusätzlichen Replayfelder und keine neuen Spiele nötig**: sichtbare Gegner, eigene Aktionen, nachträglich aufgezeichnete Gegneraktionen und Folgezustände existieren. Der vollständige tatsächliche Featurevektor, zugewiesene Ziele und Zielterrain fehlen im Trace; deshalb wird das vollständige Fixture kontrolliert synthetisch aufgebaut und nicht als Rekonstruktion des ursprünglichen Netzinputs ausgegeben. Kein neuer Observerrahmen.

## Gegenargument, Abgrenzung und Kosten

Der Gegnerzug ist bei t unbekannt. Ein vollständigeres Gegnerbild muss daher keine bessere Entscheidung erlauben; das Netz könnte bereits aus Zählmerkmalen eine sinnvolle statistische Antwort lernen. Ein einzelner ergebnisbedingt ausgewählter Verlust erklärt keinen relevanten Anteil der späten Belegungslücke. Genau deshalb nur der begrenzte Informationscheck, keine neue Featuredimension oder Policy jetzt.

Dies wiederholt weder `safe_moves` (Maske gegen **bereits** auf dem Zielfeld stehende Gegner, negativ getestet) noch `active_targets`, Reserven oder `sap_geometry`. Auch `sticky`, `pt_walk`/`pt_walk_own`, `pt_hold` und `energy_pref` wurden bereits ungünstig geprüft; keine dieser Regeln wird erneut vorgeschlagen. Grundlage: `docs/ARBEITSSTAND.md:100,130,156,182,208,267–274` sowie `main.py:452–479`.

**Kostenobergrenze:** ein lokales Fixture plus höchstens84×16=1.344 vorhandene Unit-Entscheidungen, keine Netz-/Engineauswertung; erwartbar Sekunden Rechenzeit, maximal30 Minuten Umsetzung und Prüfung. Falls das ohne neue Instrumentierung nicht sauber gelingt, stoppen. Diese Notiz startet den Auftrag nicht; Root entscheidet nach der laufenden Studie.

Quellen: `/tmp/sherlock-late-locality-20261021.json` und vorhandene Rohtraces; `agents/sherlock/features.py` SHA-256 `1ac9fa9f2bc7d74d70e72bf23a44c7d532687adbbadb0b8ba2df6f44c4c082e6`; `agents/sherlock/main.py` SHA-256 `4b53d516485649736f049728f88be1e666e0229c54de59f0819ff8fb353da457`. Nur Text/JSON gelesen, keine Repositoryänderung, keine Modelle, keine neuen Spiele, keine laufenden Trainingsresultate. Anschlussvorbereitung beendet.
