# Matchvorsprung und Restzüge: begrenzte Bestandsaufnahme

**Befund:** Sherlock sieht Zeit und Punktevorsprung bereits, besitzt aber im geprüften Core keine explizite Prüfung „Match mathematisch gewonnen/verloren“ und keine daran gebundene Erkundungsumschaltung. Verwandte Regeln wurden tatsächlich getestet. Die zwei eng geprüften öffentlichen Verlusttraces enthalten sichere Endphasen, belegen jedoch **keinen neuen wirksamen Hebel**. Keine Planung oder Änderung der laufenden Matchgewichtsstudie; keine Zwischenresultate gelesen.

## Vorhandene Nutzung und geschlossene Versuche

- **Netzeingaben:** `match_step_frac`, `match_idx_frac`, eigene Punkte `min(P/200,1)`, `point_diff=tanh((P−O)/20)` sowie eigene/gegnerische Matchsiege. Zeit und Differenz liegen also gemeinsam vor, aber ohne expliziten Quotienten oder Sicherheitsindikator. Große Differenzen werden stark komprimiert; aus dem Code folgt nicht, ob die Netze eine sinnvolle Risikowahl gelernt haben. Beleg: `agents/sherlock/features.py:28–31,734–745`.
- **Kampf bei Rückstand:** `tactics_when_behind` schaltet `dodge`, Splash-Ausweichen und `art_sap` anhand `opp_points>own_points`; keine Restzeit- oder Ergebnisgarantie (`main.py:381–402,503`). Entwicklungsversuch auf V3 hard150/easy60: `art_sap` nur bei Rückstand 33,0/100 %, dokumentiert als ungefähr +2,6 Prozentpunkte gewichtet; damalige Abgabe unverändert (`docs/ARBEITSSTAND.md:1815–1823`). Kein Beleg für denselben Effekt auf V14.
- **Restenergie:** `end_sap` berücksichtigt Zeit, erreichbare Ziele und Halterreserve, aber keinen Punktabstand (`main.py:697–733`). V12-Screen: end_sap10 direkt 45,7 %; end_sap20 nur +0,14 pp Panel; beide nicht zugelassen (`docs/EXPERIMENT_PROTOKOLL.md:140`). Beide Schalter sind im archivierten originalen V14-Config aus: `experiments/analysis/threat_warmstart_20261109/preparation/source-config.json` (`tactics_when_behind=false`, `end_sap=0`).
- **Erkundung:** `explore_quota`, `relic_search`, `relic_scout` prüfen Matchindex, frühe Zeitfenster, fehlende Relic-Paare und bisheriges Wissen; keine Ergebnisgarantie (`features.py:408–418,537–568`). Allgemeine zusätzliche Suche wurde bereits negativ geprüft: explore_quota −8/−9,5 pp, relic_search ohne Gewinn, relic_scout1 −1,3/−1,0 pp gegen Square/Solution auf V10 (`EXPERIMENT_PROTOKOLL.md:341,348,164`). Das schließt keine hypothetische Garantiebedingung logisch aus, ist aber kein Anlass, die alten Varianten erneut zu starten. Begrenzte Stichwort-/Quellenprüfung fand keinen ausgeführten Versuch genau dieser Bedingung.

## Konservative Grenze aus der tatsächlichen Engine

Geprüfte installierte Quelle: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/lib/python3.13/site-packages/luxai_s3/`.

`env.py:45–69,695–707` zählt pro Team **verschiedene** von mindestens einer lebenden Einheit mit Energie ≥0 besetzte Punktekacheln. Stapeln und überlappende Relic-Zonen vervielfachen diesen Kachelertrag nicht. Die feste Kapazität beträgt 16 Slots (`params.py:19`, `state.py:229–231`); Spawns nutzen nur einen freien Slot (`env.py:563–575`). Daher 0≤Punktezuwachs≤U=16 je Aktion, selbst mit künftigem Spawn oder heute unsichtbaren Gegnern. Aktuelle sichtbare Gegnerzahl wäre keine sichere Obergrenze.

Entscheidend: **erst punkten, dann Matchende prüfen**, danach Zähler zurücksetzen (`env.py:695–745`). Bei vor-Aktion-Matchschritt m und Maximum H verbleiben einschließlich der jetzigen Aktion **R=H−m+1** Wertungen, also bei H=100 und m=100 noch eine. Für aktive Matchschritte gilt: Vorsprung D>U·R garantiert Punktsieg; D<−U·R garantiert Punktniederlage. Gleichheit genügt nicht: Punktegleichstand entscheidet erst Gesamtenergie, dann Zufall (`env.py:709–731`). Das vorhandene `end_sap` rechnet H−m und ist deshalb keine Vorlage für diese Garantie. Matchschritt0 wird vom Agenten als Reset behandelt; keine Schlussfolgerung über alte sichtbare Einheiten daraus ziehen. Die Grenze ist bewusst grob; sie garantiert weder einen besseren späteren Matchausgang noch verfügbaren Informationsgewinn.

## Bereits vorhandene öffentliche Situationen

Nur zwei bereits untersuchte Verlustfälle, je 300 Entscheidungen, gelesen. Berechnung ausschließlich aus **vor-Aktion** `public` bzw. `context/observation`, H=100 und 16 Slots; keinerlei `posthoc`-Wahrheit verwendet. Tabelle zeigt jeweils den ersten strikt garantierten Schritt, keine Auswahl weiterer Karten.

| Trace / Match | Schritt, Originalzeile | Öffentliche Punkte; Rest | Bedeutung |
|---|---|---|---|
| 9946007/p0, M1 | 99, Z.100 | 75:114; R=2, 39>32 | Nur zwei sichere Verlustaktionen; 8 bekannte Punkte, 11 Kandidaten, 26 aktuelle Erkundungskoordinaten. Ein kleines mögliches Informationsfenster ist vorhanden, Nutzen unbelegt. Bei Schritt98 gilt 44<48 noch **keine** Garantie. |
| derselbe, M2 | 199, Z.200 (m=98) | 189:250; R=3, 61>48 | Bereits 0:1 Matchsiege; mit diesem unvermeidbaren Verlust ist auch das Gesamtspiel entschieden. |
| derselbe, M3 | 290, Z.291 (m=88) | 350:127; R=13, 223>208 | Sicherer Matchsieg, aber öffentlich bereits 0:2 Matches; kein späteres Match. 0 Kandidaten. |
| 866008/p0, M1 | 92, Z.185 | 292:130; R=9, 162>144 | Neun sichere Siegaktionen, aber 10 bekannte Punkte, **0 Kandidaten und 0 Erkundungskoordinaten** in diesem öffentlichen Kontext. |
| derselbe, M2/M3 | 201/Z.403; 302/Z.605 | 389:408 bzw.338:360; jeweils R=1 | Erst letzte Aktion sicher verloren; keine belegte längere risikoarme Erkundungsphase. |

Originale: `experiments/analysis/holder_oscillation_20261109/probe_v1/9946007_player_0.jsonl.gz` (SHA256 `2c577ce5898f7463971cefa15b5996c2331e7f5c94b0d6d68493025c86e42db2`) und `experiments/analysis/a2_anchor_20261104/traces/06_V14_866008_player_0/observed.jsonl.gz` (`e2cdbcc8cec6cc69786ff4f7e732a1d50a649acded369c9ef7c869bc599f9be5`). Beim ersten Trace stimmt der manifestgebundene Enginehash exakt mit der gelesenen Engine überein (`cc1b2657…65a469`); der ältere Trace enthält H/max_units öffentlich, dessen historische Enginebindung wurde in dieser engen Sichtung nicht erneut vollständig auditiert. Seine Einordnung gilt unter der geprüften beschriebenen Wertungssemantik. Frühere Falldiagnosen: `holder_oscillation_20261109/analysis/REPORT.md` und `preparation/historical-REPORT.md`.

**Grenze:** Keine Aussage über Häufigkeit auf allen Karten oder kausalen Nutzen. Die belegten Verlustengpässe liegen früher als die sicheren Verlustfenster; die auffälligen späten Gesamtpunkte allein begründen keine neue Regel. Nur lokale Quelllektüre und Standardbibliothek-Auswertung vorhandener JSONL; keine Modelle, Tests, Spiele, Simulationen oder Repositoryänderungen.
