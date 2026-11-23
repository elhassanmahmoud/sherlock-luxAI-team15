# Orts- und Flottensuche als isoliertes Forschungspaket

Am 23. November 2026 wurden die ausgewerteten Quellen des gemeinsamen Kundschafters mit zwei unveränderten V16-Netzen als Kurs- und als natives Forschungspaket verpackt. Die Entscheidung über eine Übernahme richtet sich nach dem getrennten allgemeinen Spielvergleich.

## Welche Version im Paket steckt

Der Vergleich auf 48 Sicht-1-Karten und beiden Sitzen enthält 288 ganze Partien. Die V16-Kontrolle gewann 93/96 gegen Solution, der gemeinsame Kundschafter 95/96 und direkt gegen V16 51/96. Der Paketbau prüft den Quellenabdruck dieser Serie und übernimmt den bereits auf separaten Validierungskarten gewählten Wert `prior_index = 2`. Zusätzlich prüft er Ortsprior und Routenberechnung gegen die früher archivierten Quellen. Beide ZIPs enthalten denselben Ortsprior und dieselbe gelernte Vorhersage der restlichen Flotte. Die trainierten Zahlen bleiben beim Verpacken bytegleich. [Spielvergleich](../ortundflotte/duelle.json) · [Quellen und Modellprüfsummen](pakete.json)

| Format | Größe | SHA-256 |
|---|---:|---|
| `Gruppe15.zip`, Klasse `Gruppe15.main.Agent_x` | 9.525.056 Byte | `cbc50a3e5d8c664794ffe4ce6c4e75508c406703b80f282b69937c020c65ab0f` |
| `agent.zip`, Klasse `sherlock.main.Agent_x` | 9.524.963 Byte | `f4b6e62084420461b6c59294930a3a670b8fdbb466c0f0fee88bc89e9c8c3a51` |

Der SHA-256-Wert der enthaltenen V16-Gewichtsdatei ist in beiden Archiven `8ed7412856d6176b81e257360c8eac4a41b844fec935db33aff9e19221d86495`. Jeder Aufbau aus den eingefrorenen Quellen ergab zweimal denselben ZIP-Inhalt bis auf das letzte Byte. Jedes Archiv enthält 38 Dateien. Die relativen Modulimporte, die Pfade der Zusatzmodelle und der äußere Einstiegspunkt ermöglichen das Laden außerhalb des Forschungsbaums. Der reguläre Kurs-Paketcheck prüfte beide Sitz- und Speicherpfade sowohl bei Installation im Projektstamm als auch unter `agents/`. [Paketbau](paket.py)

## Welche Züge verglichen wurden

Die Stichprobe für die Paketprüfung war vor dem Nachspielen bestimmt. Für Spieler 0 gegen Solution und Spieler 1 gegen Original-V16 wurde jeweils die erste Karte nach Seed mit tatsächlich verändertem Befehl aus der neuen 288er-Serie gewählt. Beides führte zu `164050001`. Zwei vollständige neue Umgebungssitzungen reproduzierten sämtliche gemeinsamen Weltbefehle beider Teams, alle drei Matchresultate, den Spielsieger und die Eingriffsliste exakt. Pro Referenz wurden 303 öffentliche Beobachtungen der Kandidatenseite aufgezeichnet. [Kursaufnahme](aufnehmen.py) · [Beleg Spieler 0](referenz_p0.json) · [Beleg Spieler 1](referenz_p1.json)

| Referenz | Ursprüngliche Matchpunkte aus Sicht des Kandidaten | Veränderte Befehle in Weltkoordinaten |
|---|---|---|
| Sicht 1, Spieler 0 gegen Solution | 358–6, 263–2, 614–81 | Einheit 2, Zug 22 von 0 auf 3, Zug 23 von 2 auf 3 |
| Sicht 1, Spieler 1 gegen V16 | 10–261, 62–197, 119–451 | Einheit 2, Zug 22 von 0 auf 4, Zug 23 von 1 auf 4 |
| Sicht 4, beide Sitze gegen Solution, `161050000` | Bereits verifizierte V16-Kontrollaufnahmen | Kein Eingriff in beiden vollständigen Spielen |

Unter Kurs-Python 3.10.15 und 3.13.13 wurde der unveränderte Klassenlader aus `lux.runner` jeweils aus einer isolierten Kopie mit dem entpackten Kurspaket gestartet. Jede Instanz erhielt die tatsächlichen öffentlichen Beobachtungen der gewählten Referenz. Der Prüfer verglich jede ausgegebene Einheit einschließlich beider Zielkoordinaten mit dem archivierten Befehl. Er zeichnete außerdem den tatsächlichen V16-Vorschlag im Inneren des Kandidaten auf und verglich jeden Unterschied mit der archivierten Eingriffsliste. Der offizielle native ZIP-Lader `scripts.r3_package.r3_package_agent` las das zweite Archiv in einem getrennten Prozess und durchlief dieselben beiden aktiven Fälle. [Prüfcode](paritaet.py)

| Vergleich | Aufgezeichnete Sitze | Gleiche Einheitenbefehle | Abweichungen von der jeweiligen Referenz |
|---|---:|---:|---:|
| Kurs-Python 3.10.15 | 4 | 19.392 / 19.392 | 0 |
| Kurs-Python 3.13.13 | 4 | 19.392 / 19.392 | 0 |
| Nativer ZIP-Lader, Python 3.13.13 | 2 | 9.696 / 9.696 | 0 |

Die jeweils installierte V16-Gewichtsdatei wurde vor und nach dem Aufruf geprüft. Die beiden Kurs-Einstellungen umfassten auf Spieler 0 Auswertungsmodus und auf Spieler 1 die Standardinitialisierung mit anschließendem kursüblichem Speichern. Der getrennte Paketcheck prüfte `train=True`, `update` und Speichern. Die Beobachtungswiedergabe bewertet technische Gleichheit auf den gewählten Fällen. Die Aussage zur Spielstärke stammt weiterhin aus den eigenständigen Spielserien. [Kurs 3.10](kurs_310.json) · [Kurs 3.13](kurs_313.json) · [Nativer Lader](native.json)

## Beide Forschungsarchive in einer eigenen Arbeitskopie erzeugen

Mit aktivierter Python-Projektumgebung vom Stamm der Arbeitskopie aus ausführen:

```sh
python experiments/analysis/relictsuche_20261123/ortflottenkurs/paket.py
```

Der Standardordner ist `experiments/imitation/relictsuche_20261123/ortflottenkurs/`. Darin stehen anschließend `Gruppe15.zip` für den Kurs und `agent.zip` für den nativen Lader. Mit `--out andere/ausgabe` lässt sich ein anderer relativer Zielordner wählen. Der Bau erzeugt die benötigte V16-Kursvorlage vorübergehend aus dem im Projekt enthaltenen V16-Freigabearchiv. Er prüft das Ergebnis gegen die archivierten SHA-256-Werte in der Tabelle oben und liest das historische Manifest nur zur Kontrolle. [Paketbau](paket.py) · [Referenzmanifest](pakete.json)

Am 23. November wurden beide Aufrufe in einer temporären Projektkopie geprüft. Zu Beginn fehlten dort sowohl `dist/` als auch die Forschungsarchive. Beide Aufrufe erzeugten beide ZIPs bytegleich zu den historischen Originaldateien und bestanden die Kurs-Ladetests unter `agents/` und in der Projektwurzel. Der SHA-256-Wert des Referenzmanifests war vor und nach beiden Aufrufen `dd421b11017e0335615c8ef19538b5cfca0a6b2af9c1ed8e5bc4df83b8ba19b6`.

## Wiederholung der Befehlsvergleiche auf dem ursprünglichen Studienrechner

Verwendet werden die beiden bereits eingerichteten lokalen Interpreter und die bei `aufnehmen.py` angegebenen externen Archivpfade. Die beiden neuen ZIPs und die vier Beobachtungsdateien liegen unter `experiments/imitation/relictsuche_20261123/ortflottenkurs` im Desktop-Arbeitsverzeichnis. Vom Stamm der Arbeitskopie aus lassen sich Quellen, Verpackung und Befehle wie folgt erneut prüfen.

```sh
study=experiments/analysis/relictsuche_20261123/ortflottenkurs
desktop=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15
py313=$desktop/.venv/bin/python
py310=$desktop/experiments/imitation/finalwoche_20261122/kurs310/env/bin/python
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
"$py313" "$study/aufnehmen.py" 0
"$py313" "$study/aufnehmen.py" 1
"$py313" "$study/paket.py" --out "$desktop/experiments/imitation/relictsuche_20261123/ortflottenkurs"
"$py310" -I "$study/paritaet.py" course "$study/kurs_310.json"
"$py313" -I "$study/paritaet.py" course "$study/kurs_313.json"
"$py313" -I "$study/paritaet.py" native "$study/native.json"
```

Auch das reguläre Umverpacken der nativen Forschungs-ZIP mit dem Abgabebauer wurde in einem eigenen Arbeitsverzeichnis geprüft. Alle 37 Laufzeit- und Konfigurationsdateien sind bytegleich zur separat geprüften Kursfassung. Die Begleitdatei nennt beim Standardbau die Quelle des Archivs. Die beiden Standard-Kursprüfungen aus den vorgesehenen Startordnern bestanden auch nach dieser Umverpackung. [Nachweis des Standardbaus](standardbau.json)
