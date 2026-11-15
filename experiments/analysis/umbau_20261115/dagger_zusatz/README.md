# Zusatzdaten vom reinen v4-Schüler

Mahmoud kann mit diesem Ordner die tatsächlich verwendete Aufnahmequelle auf einem zweiten Rechner wiederherstellen und ein übergebenes Datenpaket prüfen. Der Schüler v4 mit Stay-Bias 1,5 und Entstapeln spielt selbst. Der Kaggle-Drittplatzierte empfiehlt aus derselben öffentlichen Beobachtung einen Zug und erhält nach jedem erfolgreichen Umgebungsschritt den tatsächlich gespielten Weltbefehl zurück. Das entspricht Aufgabe 6 des [Nachtauftrags](../../../../docs/NACHTAUFTRAG_CODEX_20261115.md).

Das vor dem ersten Spiel registrierte Verzeichnis enthält für jede der 400 Karten 7172000–7172399 genau einen Schülersitz. Die Ziehung mit Wahrscheinlichkeiten 60/20/20 für Kaggle/V14/Solution reproduziert die beiden veröffentlichten früheren DAgger-Gegnerverteilungen. Für diese Aufnahme ergeben sich 235/90/75 Spiele und 203/197 Sitze. Die 600 für Mahmouds eigene Runde 3 vorgesehenen Karten ab 7252000 liegen außerhalb des Bereichs. Die 855 zuvor lokal verfügbaren Imitationsarchive enthielten keine der hier reservierten Karten. [Frühere DAgger-Runden](../README.md) · [Vollständiges Originalregister und Laufzeitumgebung](laufprotokoll.json)

## Aufnahmequelle wiederherstellen

Voraussetzungen sind Python ab 3.9 für den Neuaufbau, Git, `patch`, der Projektstand mit Git-Objekt `d609183ea6d0ceb416687418613970a8ca2e53e3` und der lokal installierte Kaggle-Lehrer 0.4.8_fn unter `experiments/opponents/kaggle3_lux3_048fn/`. Auf einem neuen Rechner kann der Lehrer mit der vorhandenen Projektumgebung einmal über `python -m scripts.fetch_kaggle3` bereitgestellt werden. Das Rekonstruktionswerkzeug selbst arbeitet offline, verifiziert die 15 externen Dateien vor dem Kopieren und liest Modellgewichte nur als Bytes.

Aus dem Hauptverzeichnis des Projekts in einer Shell:

```sh
export SHERLOCK_PROJECT="$(git rev-parse --show-toplevel)"
BELEG="$SHERLOCK_PROJECT/experiments/analysis/umbau_20261115/dagger_zusatz"
WERK="$(mktemp -d)/aufnahme"
python3 -B "$BELEG/rekonstruieren.py" --out "$WERK" --check-runtime
```

`--check-runtime` prüft zusätzlich mit `$SHERLOCK_PROJECT/.venv/bin/python` die Python- und Bibliotheksversionen, die Engine-Dateien, die festen Spielschlüssel und den Abschluss des Robustheitsvergleichs. Der Hash der Auswertung für 288 Spiele ist `2283f49e4c9efeb4e0be3e1b5297bca96193ec2570eeaf0f9540d6b1386fe787`. Bei abweichender Umgebung lässt sich der **reine Quellenneuaufbau** durch Weglassen von `--check-runtime` prüfen. Der Produktionslauf verwendete arm64 und Python 3.13.13. [Robustheitsbeleg](../robustness/run1/assessment.json)

Der Neuaufbau liest 276 Dateien direkt aus dem Git-Objekt. Für 275 bleiben die Git-Bytes erhalten. Der [Patch](sammler.patch) ergänzt in `scripts/imitate.py` einen explizit aktivierten Prüfpfad. Dazu kommen der [Sammler mit Validator](optional_v4_dagger.py), der [macOS-Aufruf](run.sh) und 15 Kaggle-Dateien einschließlich der zwei U-Net-Gewichte. Insgesamt sind 293 Aufnahmedateien einzeln gepinnt. Die [synthetische Gegenprobe](verify_fixture.py) hat einen eigenen Hash und gehört zur Übergabe. [Vollständige Prüfsummen](freeze.json)

| Beleg | SHA-256 |
|---|---|
| Reiner v4-Schüler | `0e8b280cb2173c4efd0d0c94e38119bf2f570dd5af06f52e1b5a7c9743ad7b7f` |
| Originales `scripts/imitate.py` aus Git | `a8480fae862b7f6852d8a24f3848da2b67aee5c9b0baf11598777d338777f617` |
| `scripts/imitate.py` im laufenden Sammler | `e2244dd3a749bbbe779c3623d333edce78d6a7ef7041dbe151fd67a35c371b65` |
| Quellenmanifest der Aufnahme | `adeb0c096fc025f8ced1abbbff55b2f2d651147b48d4161f8708de07b6055521` |
| Tatsächliches Laufprotokoll | `bdbc249aeb9831b8f83eaf2144da3f361ac983e20d6cd16f46b955ec2bd34290` |

## Lokale Daten prüfen und übergeben

`SHERLOCK_PROJECT` zeigt auf das Projekt mit der Umgebung, den Robustheitsdaten und `experiments/imitation/k3_v4_extra_7172000/`. Das Startskript verwendet auf macOS `caffeinate`. Der Planmodus liest nur Quellen und Register. Ein fertig versiegelter 25er-Präfix lässt sich bei freier Sammlungssperre prüfen:

```sh
"$WERK/run.sh" plan
"$WERK/run.sh" validate --through 25
```

Um eine unterbrochene Sammlung bis zur 50. Karte fortzuführen, genügt beispielsweise `"$WERK/run.sh" collect --through 50 --workers 1`. Angegeben wird die **kumulative** Zahl der Karten in 25er-Schritten bis höchstens 400. Die laufende Serie wird durch ihren Betreiber fortgeführt. Der Quellenneuaufbau und beide Prüfaufrufe starten kein Spiel. Auf anderen Betriebssystemen kann `scripts.optional_v4_dagger` aus dem rekonstruierten Verzeichnis direkt mit `--project "$SHERLOCK_PROJECT"` aufgerufen werden. Ein anderer Laufzeitstand erhält eine andere Protokollidentität.

Der Validator gleicht pro Spiel die 303 Lehrerrückmeldungen, die Zeilen aller aktiven und nicht negativ geladenen eigenen Einheiten, die kanonischen Lehrerbefehle beider Sitze, die Masken und Schussziele ab. Er zählt, welche Lehrerbefehle das ursprüngliche Trainingsverfahren zulässt. Für ein vollständiges lokales Audit gehören `protocol.json`, der ausgewählte `index-NNN.json`, `records/`, `data/` und die Sammlungssperre `.collection.lock` zusammen. Die NPZ unter `data/` sind Hardlinks auf dieselben Dateien unter `records/<seed>/`. Ein Transfer für das vollständige Produzentenaudit muss diese Identität erhalten, etwa mit einem hardlink-erhaltenden Tar-Archiv. Der Schülerpfad innerhalb der Spielmetadaten belegt den Ursprungsort. Die normale Imitations-Datenladefunktion öffnet ihre `g*.npz` direkt im übergebenen Ordner; sie lädt aus diesem Herkunftspfad keine Gewichte.

**Durchgeführte Gegenprüfung am 16.11.** In einem leeren temporären Verzeichnis wurden die Quellen allein aus Git, diesem Patch, den beiden Zusatzwerkzeugen und den lokal bereitgestellten Lehrerdateien neu aufgebaut. Alle 293 Dateihashes stimmten. Der rekonstruierte Sammler erzeugte ausschließlich aus Metadaten und den fertigen Robustheitsdateien das ursprüngliche Laufprotokoll byteidentisch. Dabei wurde weder Torch noch die Spielumgebung importiert.

Der erste echte 25er-Präfix ist separat an seinem Index `647a938dcadd276291a34ab9dcd4aaf202d4afa42788215ab894519a806867c8` erkennbar. Für diesen Quellenbeleg wurden die 25 Archivhashes, Sitzschlüssel, Einzelbelege, Hardlinks und Indexsummen lesend abgeglichen. Unter 81.564 Entscheidungen waren 79.780 für den ursprünglichen Trainer zulässig. Alle 2.839 Lehrer-Schusslabels waren legal, sechs zielten auf das eigene Feld. Dieser Präfix dient der Herkunftsprüfung. Die abschließende Datenauswertung erfolgt getrennt.
