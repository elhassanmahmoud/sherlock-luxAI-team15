# Technische Spielabnahme vor Auswahl und Nachtraining

Vor dem ersten Spiel festgelegt, Code3152fed: unabhängiger Review sauber,
792Tests+14Untertests bestanden. Gewichte ausschließlich unverändertes V14,
SHA98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8.

- Defaultoff: genau die12 bekannten seed/side-Schlüssel aus
  `experiments/analysis/continuation_20261102/diagnostic_keys.json`, einmal je
  Schlüssel. Native Aktions-SHA beider Teams und v2-Punkte/Siege/303Schritte
  müssen dem bereits geprüften alten Rohmanifest exakt entsprechen. Zusätzliche
  neue Configfelder sind ausschließlich beide `false`; kein Verhaltensunterschied.
- Aktiviert: die vier bekannten Schlüssel831006/P1,831029/P0,831042/P0,831043/P1
  je einmal unter `art_move_guard` alleine, `point_pair_swap` alleine und beiden
  Flags gemeinsam. Also12aktive Spiele; zusammen **24** technische Spiele.
- Normale `common.play_game`-Schleife mit bestehenden Scoring-/Metrikhelfern.
  Umhülltes `env.step` erfasst unveränderte native Aktionsbytes vor dem Übergang;
  ruft das Original genau einmal auf. Keine zusätzlichen Policy-/RNG-Aufrufe,
  keine Wahrheit, kein Lernen/Update/Autosave, keine Checkpointausgabe.
- Pro Spiel36exakt geladene Netze,79Features/6Aktionen, epsilon0,0gefangene
  Fehler,303Schritte/v2 und unveränderte Tensoren prüfen. In den Einzelmodi muss
  der entsprechende lokale Zähler mindestens einmal über alle vier Spiele
  auftreten; der gemeinsame Modus muss fehlerfrei sein, nicht jedes seltene
  Ereignis erzwingen. Zähler sind lokale Planungsschritte, keine Punktegewinne.
- Ein Worker, gesamter Block höchstens20min, vollständiger Source-/HEAD-/Plan-/
  Eingabe-/Gewichtsfreeze, Akkugrenzen35/25wie autorisiert. Bestehende Ausgaben
  niemals überschreiben. Jede Abweichung verwirft die technische Abnahme.

Dies sind verbrauchte Diagnosekarten und **keine Stärkenauswahl**. Ergebnisse
wählen weder Konfiguration noch Checkpoint. P bleibt für den bedingten Lernpilot
beide Flags aktiv; neue Leistungskarten841/842/843bleiben unangetastet.
