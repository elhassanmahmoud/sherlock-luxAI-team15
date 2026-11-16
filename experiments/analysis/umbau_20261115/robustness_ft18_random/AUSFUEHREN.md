# Aufnahmequelle und Ausführung

Die Registrierung steht im Commit `ed1aee4`. Der Simulator und die beiden Vergleichsagenten verwenden die eingefrorenen Quellen des ersten V15-Robustheitsvergleichs. Für den Gegner FT18 enthält der Abzug zusätzlich das unveränderte Agentenpaket des damaligen FT18-Bestätigungslaufs unter dem Importnamen `ft18_historical`. Die historischen Quellen werden aus Git gelesen; die Gegner- und V15-Checkpoints werden anhand ihrer Datei-SHAs geprüft. [Plan und Spielschlüssel](PLAN.md)

Aus dem Git-Projekt mit dem eingecheckten Studienwerkzeug, mit Python ≥3.12. `FT18` bezeichnet den Originalcheckpoint `experiments/ensembles/final_battle_20261103/FT18.pth` der damaligen Arbeitskopie. `V15` bezeichnet die geprüfte gepackte Kursdatei `experiments/imitation/releases/v15_codex/weights/agent.pth`. In diesem Beispiel werden beide als absolute Pfade übergeben. `OUT` ist das Ergebnisverzeichnis für diese eine Serie.

```sh
REPO="$(git rev-parse --show-toplevel)"
STUDIE="$REPO/experiments/analysis/umbau_20261115/robustness_ft18_random"
PY="$REPO/.venv/bin/python"
FREEZE="$(mktemp -d)/frozen"
"$PY" -B "$STUDIE/rekonstruieren.py" --repo "$REPO" --out "$FREEZE" --ft18 "$FT18" --v15 "$V15"
cd "$FREEZE"
"$PY" -B -m scripts.v15_ft18_random check
/usr/bin/caffeinate -i "$PY" -B -u -m scripts.v15_ft18_random run --out "$OUT"
"$PY" -B -m scripts.v15_ft18_random assess --out "$OUT"
```

`check` und `assess` benötigen keinen Netz- oder Spielstart. `run` verwendet einen einzigen Prozess und eine exklusive Ausgabesperre, arbeitet zuerst die 40 V14-Sitze und danach die 40 V15-Sitze ab und schreibt den Vergleich. Ein Wiederanlauf prüft die bestehende Herkunft und die bisher vollständig geschriebenen Spielzeilen in der festen Reihenfolge. Die Rohdaten pro Arm sind `games.jsonl`. Die beiden Abschlussbelege verknüpfen diese mit den jeweiligen Manifesten. `assessment.json` nennt die Spiel-/Matchsiege, gepaarte Intervalle und jede gewonnene oder verlorene Sitzpaarung getrennt nach Gegner.

Vor der Messung wurden alle 16 historischen Python-Dateien gegen das damalige Quellregister, beide Checkpoints gegen ihre veröffentlichten SHA-256 und der Kursquellstand gegen das erste Robustheitspanel kontrolliert. Ein zweiter, leerer Neuaufbau aus Git reproduzierte den Laufvertrag byteidentisch. Die zusätzliche Laufzeitprüfung liest bei FT18 die tatsächlichen Netze aus dem geladenen Gegnerobjekt. Für den Zufallsgegner prüft sie jeden ausgeführten Weltbefehl gegen den ursprünglichen Generator und legt pro Spiel den Hash der Befehlsfolge ab.
