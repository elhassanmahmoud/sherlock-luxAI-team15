# Unabhängiger Builder-Review: Targeting-Prototypen

02.11.2026 · Lesereview auf Performance-HEAD `f2bebfa682580220ae609064af46e2ab1c4464de`.

**Verdict: kein Implementierungsblocker.** Der begrenzte Umfang ist technisch schlüssig und durch die geprüften H1/H2-Beobachtungen motiviert. Umsetzung mit den vorgesehenen roten Tests kann beginnen. Dies ist keine Codeabnahme, Stärkenzulassung oder Leistungsfreigabe.

## Quellenannahmen konkret geprüft

- **H1-Reinheit stimmt:** `agents/sherlock/main.py:1196–1215` liest nur Gegnerenergie, bestehende Schadensplanung, Config/Env-Obergrenze. `_sap_cover` (`1105–1111`) erzeugt neue Vergleichsarrays. Keine Mutation von Kontext/Plan, kein RNG und kein State-Update. Die Prüfung kann daher genau im bestehenden Artilleriezweig (`445–449`) vor dessen SAP-Übernahme stehen.
- **H1-Reihenfolge stimmt:** Soft-Nebel, Stranding und weitere Sicherheitsregeln liegen danach (`460–519`); der bisherige späte Overkillschutz bei `526–531` bleibt für andere SAP-Ursprünge bestehen. Nur aktuelle erlaubte Bewegung1–4 zurückzuhalten schützt ursprüngliche SAP/STAY-Präferenzen. Es wird kein spät übersprungener Bewegungspfad restauriert. Der Zähler darf entsprechend der Spec nur eine vor Artillerie erhaltene Aktion bezeichnen.
- **H2-Maskenannahme stimmt:** `_action_mask` (`1364–1415`) und seine Bewegungshelfer `_enemy_mobile` (`1127–1140`) / `_harmful_nebula` (`781–786`) lesen keine Zielzuweisung. Die einmal vor dem Tausch berechneten Masken bleiben bei unverändertem Sapziel gültig. Der abgeschaltete Zweig kann die bisherige Reihenfolge von `_decide` (`246–258`) exakt behalten.
- **H2-Featurepfad ist korrekt begrenzt:** Die zugewiesenen Zielmerkmale kommen aus `ctx['assigned']` (`features.py:753–760`). Im zugelassenen Pfad `feat_belief is self.belief` ist `fctx is ctx` (`main.py:247–251`); Tausch vor `build_features` und Cacheerstellung erreicht deshalb Merkmale und spätere Zielregeln gemeinsam. Bei Training ist das vorhandene `rules_in_training`-Gate notwendig, wie in der Spec festgelegt.
- **Orientierung/Halter sind richtig spezifiziert:** `Belief.set_team` (`belief.py:148–153`) und die vorhandene Zielhälftenformel (`features.py:332–334`) decken kanonische sowie ungespiegelte Team1-Sicht ab. Der neue Helper soll diese Orientierung verwenden. Niedrigste nichtnegative lebende ID auf einem Punkt verhindert, dass ein negativer Legacyinhaber den echten Halter freigibt; mobile lebende Stacker bleiben zulässig.
- **BFS-Vertrag ist ausreichend:** `bfs_maps` (`features.py:194–222`) setzt auch eine unpassierbare Startzelle auf Distanz0. Die ausdrücklich verlangten Passierbarkeitsprüfungen beider Ursprünge/Ziele dürfen deshalb beim Implementieren nicht durch bloßes `dist>=0` ersetzt werden. Alle vier alten/neuen Wege und maskenerlaubte erste Fortschritte, maximal ein bestes Paar und deterministische IDs entsprechen dem vorliegenden konservativen Gegenfaktum.

## Evidenz, Umfang und Machbarkeit

Der Entwurf übernimmt die geprüften Nenner korrekt: H1 sind16 beobachtete Unit-Schritte, davon3 eigene bekannte Punktfortschritte; H2 sind141 überlappende Paar-Schritt-Gelegenheiten in91 Frames, kein realisierter Gesamtgewinn. Weder dominante Niederlagenursache noch neue Siegchance wird daraus behauptet. Negative frühere pauschale Heim-/Energieansätze werden nicht erneut eingebaut.

Zwei Flags, ein reiner Helper und ein einzelner Tausch bei höchstens120 Paaren sind ein angemessener nächster Eingriff. Höchstens16 relevante Ziele auf24×24 und Wiederverwendung von `bfs_maps` brauchen keine neue Abhängigkeit oder zusätzlichen Netzforward. Ein Aktivpfad kostet zusätzliche BFS-Arbeit; tatsächliche Laufzeit ist erst mit der vorgesehenen technischen Prüfung belegt. Keine Garantie für vollständige Routenenergie oder Netzreaktion folgt aus der ersten legalen Bewegung.

Die12 Default-off-Reproduktionen an den gepinnten alten nativen Streamhashes sowie vorab feste Aktiv-Smokes sind eine sinnvolle technische Trennung von späterer Auswahl. Maximal zwei Kandidaten, bestehende Gates und eine unabhängige Bestätigung bleiben richtig. Der Gauß-Routingfilter20 strikte positive Fakten /5 Spiele /3 Karten /100 positive Fakt-Schritte ist vor Gaußdaten festgelegt und ausdrücklich kein Siegtest; er rechtfertigt selbst keine Übernahme. Ein eventueller Anpassungspilot bleibt ohne eigenen vorab fixierten Nachtrag unfreigegeben.

## Ein nicht blockierender Wortlautpunkt

Spec Zeile82 sagt „maximal zwei Nominees“. Der übergeordnete Fortsetzungsplan verlangt höchstens zwei Kandidaten und **genau höchstens einen Nominee zur Bestätigung** (`2026-11-02-targeting-continuation.md`, Aufgaben4–5). Die Prototypenimplementierung hängt daran nicht; im Leistungsnachtrag muss diese bestehende Ein-Nominee-Regel ausdrücklich gelten. Kein Nachrücken/zweite Bestätigung ist hier zugelassen.

Nur Dateien/Quellen gelesen und diesen externen Bericht geschrieben. Keine Repoänderung, Modellimporte, Tests, Spiele oder Subagents. Noch keine Implementierung zur Abnahme vorgelegt.

Gelesene Entwurfsidentitäten:

- `docs/superpowers/specs/2026-11-02-targeting-prototypes-design.md`: SHA256 `9a8e6b93e3682d3404b0c14a9432378504b9fdd20761dec0dfde995392240800`
- `docs/superpowers/plans/2026-11-02-targeting-prototypes.md`: SHA256 `7ffffe170e4e0bf21079fbd7bb45f812b95d62d791ea7097a567736603f84125`
