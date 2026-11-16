# Spielreihe nachrechnen

Der Lauf verwendet den originalen R3-Bewegungsberater und dieselbe V15-Mischung wie der veröffentlichte Kurskandidat. Vier Kontrollpartien auf Karte 7158000 stellten die Spiel- und Matchsiege sowie beide Punktesummen der großen Referenz für beide Startseiten und beide Eltern wieder her. Die zusätzliche Kontaktroute stammt aus dem vorangegangenen R3/V15-Versuch. Das Kontaktvergleichspanel wurde in einer frisch aus Git rekonstruierten Kopie derselben Laufzeit ausgeführt.

Das [Laufzeitregister](laufzeit.json) hält die verwendeten 412 Projektdateien, die zehn Python-Module der Spielengine, die installierten Paketversionen und die Version der Punktezählung fest. Der Wiederaufbau liest die nativen Dateien als Git-Objekte und erzeugt die privaten R3-Importe aus ihrer ursprünglichen Revision. `PY` ist der Interpreter der Projektumgebung. `LAUFZEIT` und `AUS` sind neue, lokale Verzeichnisse.

```sh
D=experiments/analysis/r3_v15_blend_20261116
"$PY" -B "$D/laufzeit.py" restore "$LAUFZEIT"
for phase in smoke control diagnosis_blend diagnosis_contact candidate contact
do
  "$PY" -B "$D/spiele.py" "$phase" --runtime "$LAUFZEIT" --out "$AUS/$phase" --workers 2 || break
done
```

Jede Rohzeile gehört zu genau einem Agenten, Gegner, Kartenschlüssel und Sitz. Nach jeder vollständig beendeten Reihe wird ihre Aufnahme über SHA-256 und Zeilenzahl bestätigt. Die Original-V15-Spiele gegen Solution stammen aus Mahmouds [Dev-B-Vergleich](../kaggle3_20261115/devB_hyb_v4_mixed.csv). Der ursprüngliche R3 wurde auf denselben Sitzen ausgeführt. Der Sitzwechsel und die beobachtete Historie gehören zur vollständigen Partie.
