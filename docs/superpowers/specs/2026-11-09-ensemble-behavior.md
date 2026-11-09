# Ensemble-Verhalten während des Einzelnetztrainings

## Frage und Entscheidung

Die geschlossene MATCH38-Bestätigung (Quelle 98f2b02, Ergebnis e1b8f8e) liefert keinen Nachfolger: direkt 58/120, Solution beide 38/40. Keine Wiederholung oder weitere Gewichtung dieses Kandidaten. Der Nutzer beauftragt kontinuierliche autonome Verbesserung und hat Entscheidungs-/Freigaberunden ausdrücklich an Codex delegiert. Die folgende Methodenwahl trifft Codex, nicht eine behauptete Nutzerpräferenz im Detail.

Bisher trainieren die untersuchten Komponenten mit eigener Q-Auswahl; im späteren Agenten werden 36 beziehungsweise 38 Q-Ausgaben gemittelt. Die neue Hypothese betrifft die dadurch unterschiedlichen erfahrenen Situationen: Ein einzelnes Mitglied lernt weiter mit eigenem DDQN, wählt während seiner Trainingshandlungen aber gemeinsam mit 35 eingefrorenen ursprünglichen Mitgliedern. Das ist ein gezielter Verhaltensvergleich, keine bewiesene Ursache bisheriger Misserfolge.

Alternativen: erneutes höheres Matchreward oder größere Mischung wären Wiederholungen ohne neue Ursache; passiver vollständiger Eval-Actor mit separatem Terminal-Replaysammler ist aufwendiger und verändert zusätzlich Trainingsregeln. Gewählt wird der enge temporäre Q-Hook im regulären Trainingspfad. Reward, Exploration, Regeln, Replay und DDQN bleiben unverändert. Der Actor ist damit ausdrücklich keine eingefrorene vollständige V14-Evalpolitik.

## Eingriff und Invarianten

- Eigenes Lernmitglied ist V14-Komponente 18 (nullbasiert), unveränderte 79 Eingaben, sechs Aktionen, hidden=256, Dueling. Ursprüngliche V14-Datei SHA98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8.
- Ausschließlich innerhalb der normalen `_act_est`-Handlung wird der schon berechnete Output des Lernnetzes an Position 18 mit den 35 anderen originalen Netzausgaben in Originalreihenfolge gemittelt. Genau ein Forward je Mitglied pro Handlung; keine zusätzliche Kopie von Originalmitglied 18, keine Rekursion. Legale Maske und nachgelagerte Regeln greifen unverändert.
- Die 35 Netze gehören in einen separaten instanzlokalen Adapter, nicht in `agent.extra_q`. Ihr Aufbau erhält Python-/NumPy-/Torch-RNG; Tensoren, Dtypes und Mitgliedsreihenfolge bleiben identisch, `requires_grad=False`. Keine eingefrorenen Parameter in Adam und keine Aliase zu Lerntensoren.
- Hook nur im Handlungsbereich aktiv, nach Rückkehr oder Ausnahme garantiert entfernt. Während `_learn` ausschließlich eigenes Q, eigenes Target und eigene Gradienten, unverändertes DDQN-Target. Keine globalen Modulpatches, keine Core-/Abgabeänderung. OFF umgeht den Adapter ohne zusätzliche Forwards oder RNGverbrauch.

## Feste Lernrezeptur und historische Kontrolle

Zwei neue ON-Arme, Starts **48 und 49**, frisch aus demselben Originalmitglied 18. Je **40 Vorlauf + 400 Lernspiele**, ausschließlich Endgewichte, **60.000 Updates** je Arm. Frischer Adam/Replay, Target=q, `env_steps=60000`, `learn_steps=0`, lr=0,00005, epsilon=0,05. **w_match=2**; exakt die alte Kontrollkonfiguration und geordnete `match_weight_study.rollout_plan(start)` verwenden. Keine bisherigen Match20-Endgewichte als Lernstart. Trainingskarten werden bewusst wiederverwendet, nicht als frische Leistungskarten bezeichnet.

Referenzen sind vorab beide vollständigen Kontrollen 48/49 aus der geschlossenen Matchgewicht-v2-Studie, ohne Gewinnerauswahl: Finals SHA931ae709779144d578cdf8134f8ef8bb777c653f3f390426a96e03eb141d2429 und SHA499ff53fd318e507e31036b73920e5792b5c47443a24d91d880e7aa2a111ee01. Bindung über Gesamtabnahme SHA41cb8fa0689bb1a5b98bbd692e147fceb8471b5e72387b661b06e7484c244b94, beide Originalaufnahmen/Receipts, unveränderte alte Runtime-/Interpreter-/Enginebytes und unveränderte tatsächliche Modelle. Historische Admission nicht gegen neuen HEAD aufrufen. Vollständige frühere Binär-/RNG-Snapshots fehlen; deshalb OFF-Reproduktion zwingend und verbleibende Grenze offen nennen.

Technikphase genau **vier bekannte Spiele**, null Gradienten: OFF dann ON jeweils 9946007/player_0 und 831006/player_1 gegen Solution, Start48, jeweils frisch initialisierter Agent, zwei Fälle innerhalb jedes Arms fortlaufend wie historische Technik. OFF muss die akzeptierten ursprünglichen Kontrollfälle vollständig in nativen/öffentlichen Trajektorien, Ergebnis, Initialidentität, Replay-/Reward-/finalen Aktionsnachweisen reproduzieren. ON muss tatsächlich eine andere legale greedy Präferenz und mindestens eine andere finale Aktion zeigen; korrekte originale Reward-/Replaylabels, endliche Werte und unveränderte 35 Netze belegen. Kein ON/OFF-Trajektoriengleichheitsgate. Falls technische Treue/Exposition nicht belegt: stoppen, keine automatische Ersatzkontrolle oder weitere Karten.

Nach Technikabnahme beide ON-Worker gemeinsam bis zu ihren festen 40er-Vorläufen. **Manuelle Root-Barriere vor Gradienten**: tatsächliche Replays/Initialzustände/Optimizer/Rewards/Hooks und gefrorene Tensoren prüfen, getrennte ON-Verläufe ausdrücklich zulässig. Originalworker erst nach gehashtem Root-Beleg freigeben. Danach je 400 Lernspiele ohne Zwischenwahl oder interne Validation. Höchstens 884 neue Spielausführungen und 120.000 Updates inklusive Technik; keine automatischen Wiederholungen.

## Nachfolgende kleine Auswahl

Erst nach vollständiger Trainingabnahme separat aufnehmen. Ursprüngliche 36 plus beide neuen ON-Endnetze = **BEHAVIOR38**; Vergleich mit bereits akzeptierter **CONTROL38** und ursprünglichem **V14**, gleiche unveränderte V14-Inferenzconfig, keine Kalibrierung/Mischwahl. Tatsächliche Montage-/Loaderidentität vorher prüfen.

Feste 200 Auswahlspiele: alle drei Varianten gegen Solution auf9990000–9990019, beide Seiten (120); BEHAVIOR38 direkt gegen V14 auf9990100–9990119 und gegen CONTROL38 auf9990200–9990219 (80). Diese 60 Karten vor Start einmal begrenzt auf dokumentierte Nutzung prüfen. Vier Gates: tatsächliche Solution-Siege mindestens beide Referenzen; direkt mindestens 24 echte Siege von 40 gegen jede Referenz. Remis sind keine Siege. Je Statistik 5.000 PCG64-Seed-0-Ganzkarten-Bootstrapziehungen, 95%-Scoreintervalle, keine Familienkorrektur über frühere Versuche. Historische Kontrollen sind keine neu unabhängig trainierten Replikate.

Fehlschlag schließt den Ansatz ohne Schwellenänderung oder Nachschlag. Bestehen nominiert nur für eine separat vor neuen Daten festgelegte Bestätigung. Keine automatische Promotion; V14/ZIP erst nach belegtem Vorteil, Sicherung, Reproduktion und Kursprüfung ersetzen.

## Betrieb

Profil `ensemble_behavior_20261109`. Maximal zwei Modellworker, keine Tests parallel, Quelle/HEAD und Eingaben während jeder aufgenommenen Phase festhalten. Akku und Restkontingent ausdrücklich erlaubt; tatsächliche frische Quota durch geprüften ISO-Schreiber, bei 100 Prozent kontrollierter Stopp, Resets nur durch Nutzer. Historische Studien nicht erneut starten. Sinnvolle Commits und sichere Hauptkopie-/Remoteabgleiche zwischen Phasen; Fremddateien erhalten.
