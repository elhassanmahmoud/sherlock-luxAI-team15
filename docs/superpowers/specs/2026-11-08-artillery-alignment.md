# Artillerie-Streuschaden im Training angleichen

## Ziel und Ausgangslage

Moayed hat die autonome Weiterarbeit und den Austausch von V14 bei nachgewiesenem Vorteil erneut freigegeben. Kein Reset durch Agenten. Die bisherigen Studien bleiben geschlossen. Artillerie-Offline-Diagnose: 1192 historische Aufrufe, 24 Eval-ja/Training-nein auf einer von zwei bekannten Niederlagen. Unabhängiger Datenabschluss zuerst. Diese Exposition ist keine Aussage über Spielstärke.

Gewählte Hypothese: Neue Netze sollen auch beim Lernen die bereits eingesetzte Streuschaden-Artillerieregel erleben. Nur dieser Trainingsunterschied wird verändert. Größere Ensembles ohne gezieltes Lernen und neutraler Fog-Reward haben keinen abgesicherten Nachfolger geliefert; diese Varianten werden nicht wiederholt oder nachträglich umgewichtet.

## Produktionsänderung, standardmäßig ausgeschaltet

`AgentConfig.art_splash_in_training: bool = False`. In `_artillery_ok` gilt die vorhandene `art_splash`-Abzweigung auch bei Training, wenn der neue Schalter wahr ist. Alle Schwellen, Sicherheitsabstände, Reservewerte und Rückgaben bleiben unverändert. `_act_est` muss für diesen Fall die vorhandene Parameterschätzung beobachten und merken, auch ohne `rules_in_training_all`; ohne `art_splash` bewirkt der neue Schalter nichts. Inferenz muss bei beiden Werten exakt gleich bleiben. Keine Änderung an Gewichten, Reward, Merkmalen, Masken, Replayformat oder anderen Regeln.

`art_still` bleibt unverändert. Der feste V14-Ausgang hat art_still, sap_still_all, smart_sap, idle_sap, art_move_guard und siege jeweils False und end_sap=0. Diese Annahmen vor realen Läufen explizit prüfen. Bei anderer Konfiguration keine Aussage über lokale Aktionswirkung aus bloßen Helper-Ergebnissen ableiten.

## Kontrollierter Lernversuch

Vier feste Arme: control43/aligned43/control44/aligned44, jeweils V14-Komponente18 (nullbasiert), gleiche Q-/Target-Kopie, frischer Adam und leerer Replay. Einziger Unterschied im jeweiligen Paar: art_splash_in_training=False/True. Training unverändert lr5e-5, rules_in_training=True, rules_in_training_all=True, rescue_in_training=True, frozen=False, fog_unknown_reward_neutral=False, env_steps=60000, learn_steps=0, epsilon-Untergrenze0,05, train_every2. Gegneranteile60%Solution92/20%sol92_sq/10%default/10%rush.

Pro Arm40 Vorlaufspiele ohne Gradienten und400 Lernspiele. Endcheckpoint allein, keine Suche nach Zwischenständen. Initial/final je4 Diagnosekarten gegen default/Solution92, beide Seiten (32 Ausführungen pro Arm). Insgesamt maximal1888 Ausführungen und240000 Lernupdates. Trainingsbasis9000000 plus RNG-Seed*10000; je200 Karten beideSeiten:9430000–9430199/9440000–9440199. Vorlauf jeweils+5000, also9435000–9435019/9445000–9445019. Diagnose9600000–9600003. Neue Karten vor Start auf beobachtete Nutzung/Reservierung prüfen; bekannte Datenlücken dokumentieren.

Keine gesonderte Lern-Smoke-Reihe. Technischer Default-/Inferenznachweis mit zwei bekannten V14-Spielen und vorhandenen Frame-Digests, jeweils neuer SchalterFalse/True, ohne Lernen: vier Ausführungen. Dafür Quellen nach Code-Review einfrieren. Ein technischer Fehler rechtfertigt eine dokumentierte Reparatur; kein schlechter Leistungsausgang rechtfertigt neue Karten oder einen Neustart.

## Vorlauf als Mechanikprüfung

Beide Seiten jedes Paares haben exakt gleiche Startparameter, Konfiguration bis auf den neuen Schalter, Karten/Seiten/Gegner und Lernbudgets. Anders als beim Fog-Reward-Versuch dürfen und sollen Aktionen, Zustände und Replay zwischen den Armen divergieren. Keine falsche Trajektoriengleichheitsprüfung übernehmen.

Ein ausschließlich im Versuch aktiver Beobachter um `_artillery_ok` berechnet auf denselben Eingaben beide Schalterwerte, restauriert die Config im finally und gibt immer das tatsächlich konfigurierte Verdikt zurück. Helper ist read-only, RNG-/Estimator-/Config-/Kontextzustände unverändert prüfen. Pro tatsächlich berechtigtem Artillerieaufruf zwischen baseline/aligned unterscheiden, UID/SAP-Eingabe und endgültige native Aktion festhalten. Spiegelung berücksichtigen. Neue Erlaubnis, späterer SAP-Abbruch und tatsächlich überlebender zusätzlicher SAP getrennt zählen. SAP-Identität/Koordinaten, `_prev_actions` und tatsächliche Replay-Aktionsklasse prüfen; keine bloßen Trefferzahlen als Herkunft benutzen. Die genannten deaktivierten späteren SAP-Erzeuger sind Voraussetzungen für die lokale Wirkungsinterpretation.

Vor Gradienten: alle40 Vorlaufspiele je Arm vollständig, Q/Target/Adam unverändert, Replay befüllt und Aktionen korrekt. Jeder aligned-Arm muss mindestens einen neu erlaubten und tatsächlich ausgeführten SAP belegen. Sonst Paar stoppen und Daten berichten; nicht Karten nachschieben. Erst nach unabhängiger automatischer Paarprüfung Gradienten freigeben. Gemeinsame Seeds bedeuten nicht gleiche spätere Zustände.

Nach Training: vollständige Kartenfolge, je60000 Updates, endliche/veränderte Q/Target/Adam, erwartete Zähler, tatsächlich erneut geladene Endgewichte und unveränderte V14-/ZIP-Hashes. Validierungen ausschließlich mit ursprünglicher V14-Inferenzkonfiguration, keine Lern-/Replay-/RNG-Mutation.

## Vergleich und Übernahme

Erst nach technischer Abnahme aller vier Arme zwei feste Kandidaten bauen: V14+beideKontrollnetze bzw. V14+beideAlignednetze, uniform38. Keine Mitgliedersuche/Umgewichtung. Vor Trainings- und Leistungsresultaten festgelegte Obergrenze:440 Auswahlspiele, nur bei Nominierung einmalig600 frische Bestätigungsspiele, maximal1040. Der Methodenvermerk experiments/analysis/artillery_alignment_20261108/operations/comparison-sizing.md bindet Paneldefinitionen, unveränderte Auswahl-/Übernahmebedingungen und feste Rangfolge; beide Kandidaten sind nominierbar. Geringere Empfindlichkeit wegen nur20 unabhängigen Kartenclustern ausdrücklich akzeptiert, kein Nachschlag bei Unklarheit. Exakte vier frische Kartenlisten und Werkzeugzulassung vor Leistungsdaten separat binden. Ziel: Vorteile gegen V14 UND Solution, keine wesentliche Regression gegen Kontrollen. Keine Promotion aus Loss, Einzelnetz-Diagnosen oder bekannten Karten. Bei belegtem Vorteil vorher V14 sichern, Kurs-/Lade-/Laufzeitprüfung sowie Reproduktion abschließen und Übergabe für Mahmoud dokumentieren.

## Betrieb

Vorhandene Studienkopie und Branch weiterverwenden; maximal zwei Modellworker, keine Tests parallel. Quellen/HEAD/Startgewichte/Pläne während Läufen unverändert; Remote nur lesen und Integration am sicheren Übergang. Einmalige exklusive Ausgaben, keine stillen Wiederholungen. Bestehende Ressourcen-, AC-, Quota-, STOP- und Eigentumsprüfungen wiederverwenden. Nutzer erlaubt verbleibendes Kontingent; bei tatsächlichen100% kontrollierter Abschluss, Reset nur durch ihn. Updates, sinnvolle Commits und Push aufmain autorisiert; fremde Dateien erhalten.
