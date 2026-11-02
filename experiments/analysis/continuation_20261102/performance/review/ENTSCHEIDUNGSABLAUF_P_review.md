# Unabhängige Prüfung der Ablaufdokumentation

Verdikt: PASS für aktive Inferenzfolge und Modusabgrenzung; keine Important/Critical Findings. Eine kleine sachliche Wortkorrektur vor Weitergabe empfohlen.

Geprüfter Entwurf: `/tmp/sherlock-continue-20261102/ENTSCHEIDUNGSABLAUF_P.md`, SHA256 `3028dea4685adb09b21d9e3c6136e92be8114d1dc1166073d47f079e16898409`. Bezug: eingefrorener Quellstand `03e54e267242ff642c126313fe5f512ed9d959ac` und vorhandener P_actual_load_preflight.json. Nur Quelltext/JSON gelesen, keine Python-Ausführung, Modelle, Torch, Spiele, Tests oder Repositoryänderungen. Laufende Evalworker unberührt; keine Folienänderung.

Bestätigt:
- Parameterschätzung vor Belief; Kontext/Basiszuweisung und sichtbarer SAP-Vorschlag vor Masken/Features. P berechnet Masken vor dem Paar-Tausch und verändert assigned vor dem Featureaufbau. V14 berechnet Masken danach.
- 79 Eingaben; 36 gleich gewichtete Sechs-Q-Ausgaben; Dueling ohne Softmax. Maskierung vor endgültigem Argmax, rohe Bestaktion nur für Diagnose. Q-Werte sind keine Wahrscheinlichkeiten.
- Die sieben gruppierten aktiven Postregelstufen stimmen mit den tatsächlichen Flags und der Reihenfolge. Nicht aktive Zwischenzweige sind zu Recht ausgelassen. Rescue bleibt bedingt; Nebelausgang ist auch außerhalb Rescue möglich.
- art_move_guard bewahrt den stufenaktuellen legalen Move, nicht zwingend den ursprünglichen NN-Move. Nach dem späteren Overkill-Veto gibt es keinen zweiten Argmax/keine neue Zielsuche. Spätere Nebel-/Rescueregeln bleiben wirksam.
- Sichtbare SAP-Zielrangfolge nutzt die feste 0,5-Annahme; Parameterschätzung beeinflusst getrennt Halter-/Artilleriebedingungen. Keine Behauptung tatsächlicher Treffer oder garantierten Gewinns.
- Par_eval verwendet train=False und keinen update-Aufruf; der dokumentierte Vorladecheck setzt zusätzlich learn_enabled=False. Der Entwurf verwechselt diese Zusatzabsicherung nicht mit der normalen Workerinitialisierung. cfg.frozen=False in P ist korrekt von frozen=True beim Battle-Paket und den Trainingsgates abgegrenzt.
- Die gelesenen Quellbereiche/Zeilenziele tragen die zugehörigen Aussagen. Relative Links sind ausdrücklich als repositorywurzelbezogene Referenzen gekennzeichnet; deren endgültige Transport-/Renderbarkeit prüft der Autor separat.

Kleine Korrektur: Im Absatz „Bei Artillerie ... mindestens drei sichtbare Trefferpositionen“ bitte „mindestens drei sichtbare gegnerische Units im direkten/benachbarten Trefferbereich“ verwenden. main.py:1468 zählt direkte plus benachbarte Gegner-Arrayeinträge, nicht unterschiedliche Felder; gestapelte Units zählen mehrfach. Die Absenkung auf zwei ist ebenfalls eine Unitanzahl. Kein Einfluss auf die erklärte Entscheidungsfolge.

Optionale Klarstellung: Im Mermaid-Knoten vor Parameterschätzung.remember „Endaktion in Weltkoordinaten zusammenstellen“ statt „zurückgeben“. Der echte Return aus act erfolgt erst nach remember; Pseudocode und Fließtext zeigen dies bereits richtig.

## Nachprüfung der Präzisierungen

Finaler geprüfter SHA256 `c9a395c3af76e041dd2eb0e9c62a24206a0f667e9b1b813349bca30b52a07fcf`: Die Unit-/Trefferzählung, Diagramm-Reihenfolge und präzise Manhattan-Bezeichnung sind korrigiert und mit dem Quelltext konsistent. **Final PASS**, keine offenen Important/Critical Findings.

Zusätzlich für Root bestätigt: Fog-SAP (main.py:423–429) prüft nicht den NN-Maskeneintrag für SAP. Es kann anhand eigener Voraussetzungen einen unsichtbaren SAP bestimmen, obwohl die NN-Maske SAP mangels sichtbaren Ziels gesperrt hatte. Der Entwurf ist durch die ausdrückliche Beschränkung auf „normale NN-Auswahl“ korrekt; ein zusätzlicher erklärender Satz hierzu wurde dem Autor empfohlen. Keine Behauptung, jede finale Aktion müsse unverändert dieselbe NN-Maske passieren.
