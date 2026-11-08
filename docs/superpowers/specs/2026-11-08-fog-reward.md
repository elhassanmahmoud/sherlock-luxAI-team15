# Unbekannte Fog-SAP-Treffer im Training neutral behandeln

## Auftrag und Hypothese

Moayed autorisiert autonome Weiterarbeit nach dem abgeschlossenen HOLD-Versuch. V14 und ZIP bleiben bis zum unabhängig belegten besseren Kandidaten unverändert. Hier wird kein alter SAP0-Versuch wiederholt: Bekannt positive Treffer behalten ihren Bonus, bekannt geschätzte Fehlschüsse behalten den Abzug. Nur der bisher als0 gespeicherte **unbekannte** Ausgang eines final ausgeführten Fog-Schusses wird optional neutral behandelt.

Belegt ist die Datenkette `_fog_sap → (dx,dy,0) → _sap_hits → negativer Hit-Shaping-Term`. Das beweist eine Vermischung von unbekannt und negativ geschätzt, keinen bereits nachgewiesenen Stärkeverlust. Historische Trainingslogs zeigen tatsächlich zahlreiche nichtpositive Trefferschätzungen; deren genaue Fog-Herkunft wurde damals nicht explizit gespeichert. Neue Läufe müssen die endgültige Herkunft nachweisen.

## Minimale Implementierung

- `AgentConfig.fog_unknown_reward_neutral: bool = False`. Keine Änderung an Aktion, Maske, Zielwahl, Inferenzregel, Architektur, Replay-Aktionsklasse oder numerischem SAP-Tupel. Keine Null-/Negativ-Sentinels in der dritten Tupelkomponente.
- `_sap_unknown` als Menge kanonischer UIDs beim Episodenreset und am Anfang jedes `_act` leeren. Pro Einheit `fog_origin=None`; wenn der vorhandene Fog-Pfad einen SAP-Vorschlag setzt, genau dieses Tupelobjekt merken. Nur beim tatsächlich ausgegebenen SAP und `sap is fog_origin` UID eintragen. Spätere Zielersetzung, anderer Aktionstyp oder SAP-Abbruch dürfen keine unbekannte Endaktion markieren. Gleiches Ziel mit neu berechneter bekannter Trefferzahl zählt als neue Herkunft.
- `unit_rewards` erhält das optionale Keyword `unknown_sap=None`. Nur wenn Flag wahr, endgültige Aktion SAP und UID markiert: den Hit-Shaping-Anteil auslassen. Alle anderen Terme und bekannte Treffer/Miss-Schätzungen exakt erhalten. Fehlendes Flag wie False behandeln. Bei False ruft `_update` weiterhin die alte Fünf-Argument-Signatur auf, damit historische Reward-Auditoren kompatibel bleiben.
- Neue Auditierung liest explizite finale Herkunft. Sie prüft pro Übergang: Reward(True)−Reward(False)=+w_sap_hit nur für finalen unbekannten SAP bei aktivem Shaping, sonst0. Auch Nullgewicht, Tod/Terminal und deaktiviertes Shaping berücksichtigen. Flag-False-Auswertung und die abgegebene V14-Policy bleiben unverändert.

## Ein festes gepaartes Nachtraining

Für unmittelbare V14-Relevanz verwenden wir fest **V14-Komponente18 (nullbasiert)** statt des älteren A2-Schülers. Diese Wahl steht vor Ergebnissen fest. Alle vier Arme starten mit exakt derselben Q-/Target-Kopie, frischem Adam und leerem Replay. RNG-Starts41 und42, jeweils CONTROL(False) und NEUTRAL(True). Nur dieses Flag unterscheidet das jeweilige Paar.

Bestehendes V14-Nachtrainingsrezept: lr5e-5, `rules_in_training=True`, `rules_in_training_all=True`, `rescue_in_training=True`, eingefroren=False. Startzähler env_steps60000, learn_steps0; ursprüngliche Epsilon-Untergrenze0,05, Trainintervall2. SAP-Gewicht bleibt0,3. Gegneranteile60%Solution92,20%sol92_sq,10%default,10%rush. Keine Lehreranker, SAP0, neue Architektur oder Maskenänderung.

Pro Arm40 Vorlaufspiele ohne Gradienten und400 Lernspiele. Nur Endcheckpoint, keine Auswahl nach Zwischenvalidierung. Zu Beginn und Ende je vier feste bekannte Validierungskarten gegen default/Solution, beide Seiten (32 zusätzliche Ausführungen pro Arm). Zusammen maximal1888 Ausführungen:160 Vorlauf,1600 Lernen,128 diagnostische Validierung. Erwartet60000 Updates je vollständigem Arm,240000 insgesamt. Es sind vier Arme eines festen kontrollierten Versuchs, keine Hyperparametersuche.

Neue Karten: Trainingsbasis7000000 mit `seed*10000`, also7410000–7410199 und7420000–7420199; Vorlauf jeweils+5000, also7415000–7415019/7425000–7425019. Diagnostische Validierung7600000–7600003. Beide Seiten alternieren wie vorhandenes finetune. Seed-Audit vor Start. Validierung ist bekannt und nur beschreibend, kein Stärkenachweis/Checkpointselektor.

## Mechaniknachweis und Abnahme

Vor Gradienten muss jeder Arm im Vorlauf explizit unbekannte finale SAPs beobachtet haben und seine Reward-Arithmetik vollständig bestehen. Q, Target und Adam dürfen sich im Vorlauf nicht ändern. Je Paar müssen Karten/Gegner/Aktionen/Punkte/Zustände und Replay-Inhalte ohne Reward gleich sein; Reward-Differenzen müssen genau zu den unbekannten finalen SAPs passen. Die Paarprüfung darf durch den Supervisor erfolgen, sobald beide Vorlaufbelege vorliegen; bis zu ihrer Bestätigung keine Modelle als valide behandeln. Bei Abweichung beide eigenen Arme kontrolliert stoppen, Teilstände nicht nominieren. Kein stiller Neustart.

Nach Training: vollständiger fester Spielplan, endliche/veränderte Q-/Target-/Adam-Werte, erwartete Updates, neue Gewichte reproduzierbar laden, unabhängiger Audit. Originale V14-Rohdateien und ZIP vor/nachher hashen. Keine automatische Übernahme oder Aussage über bessere Siege aus Reward/Loss allein.

Nur wenn die Mechanik und alle vier Trainings vollständig geprüft sind, separat vor frischen Ergebnissen einen kleinen Vergleich festlegen: Kandidaten mit den beiden Kontrollnetzen beziehungsweise den beiden Neutralnetzen zusätzlich zu V14, genau gleicher Aufbau. Vergleich gegen V14 und Solution/Kontrollen, keine alte Datenmischung und kein späteres Mitgliederauswählen. Die Wirkung des neuen Rewards muss von bloßem zusätzlichen Training unterscheidbar bleiben. Erst danach gegebenenfalls feste unabhängige Bestätigung/Portabilität/Backup vor Abgabeaustausch.

## Betrieb

Bestehender isolierter Worktree/Branch, maximal zwei Modellprozesse. Keine Tests parallel zu Training/Evaluation. Quellen/HEAD/Pläne/Startgewichte während der Messung einfrieren. Frische tatsächliche Quotenbelege, AC, STOP, Fremdprozess- und Hashprüfung. Restliches Kontingent autorisiert, keine Resets durch Agenten. Alte Studien und Daten bleiben geschlossen. Dokumentation und sinnvolle Commits/main für Mahmoud, sicherer lokaler Abgleich an Phasengrenzen.
