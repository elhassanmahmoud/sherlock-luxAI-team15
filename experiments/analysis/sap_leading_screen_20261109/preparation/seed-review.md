# Gezielter lokaler Kartenfrischecheck für den SAP-Vorhaltescreen

09.11.2026. **Kein beobachteter lokaler Nutzungs- oder Reservierungskonflikt im geprüften Umfang.** Zielbereiche jeweils vollständig und inklusiv: Panel9940000–9940019, Direkt9940100–9940119; insgesamt40 verschiedene Karten. Das ist keine Spielstartfreigabe und kein Beweis einer weltweit nie erfolgten Nutzung.

## Tatsächlich ausgeführte Prüfung

Vorhandenes Werkzeug `experiments/analysis/sampled_target_20261108/operations/seed-audit.py` wiederverwendet, Ursprung-SHA `f29a816897c411c8e7c133847b5f3793ca85e037a7a549fd8093ff0b64da6b4d`. Externe enge Adaption: neue zwei Bereiche/Profil, keine behauptete Quellenruhe und bewusst keine Roh-JSONL-Vollanalyse. Seed-/Intervall-/CSV-/Textlogik unverändert; keine neue allgemeine Audit-Infrastruktur.

Tatsächlicher Aufruf mit dem vorhandenen Projektinterpreter: `python -B /tmp/sap-leading-seeds/seed-audit.py --targeted-readonly-scan`. Exit0; Rohzeitfenster04:10:35–04:10:56 UTC, intern20,71s. Nur Dateilesen/Hashen, Standardbibliothek und Git-Leseaufrufe; null Modelle, Tensorloads, Tests oder Spiele. Keine Repositoryänderungen durch den Reviewer.

| Abdeckung | Tatsächlicher Umfang |
|---|---:|
| Registrierte Arbeitskopien |8|
| JSON-/CSV-Dateipfade einschließlich gzip |14530|
| Unterschiedliche JSON-Inhalte nach Byte-Deduplikation |1513|
| Unterschiedliche CSV-Inhalte |1695|
| Gelesene CSV-Zeilen |1647885|
| Numerische CSV-Seedwerte |1643224|
| Numerische JSON-Seedwerte |117796|
| Konservative JSON-Intervallkandidaten |718|
| Ergänzende Textpfade / unterschiedliche Textinhalte |9149 /1826|
| Absichtlich nicht geparste Roh-JSONL-Pfade |1224|

Strukturierter Bereich: `experiments`, `logs`, `replays`, JSON/CSV einschließlich `.gz`. Ergänzend Wurzel sowie `docs/scripts/experiments/logs/replays`, Dateitypen `.md/.py/.sh/.txt/.log`, numerische Literale und explizite Intervalle. Vollständige Pfadinventare, SHA256, Dateistats, Schemafelder und Abdeckungslücken stehen im Rohbericht.

**Treffer:**0 CSV-Nutzungsüberschneidungen,0 JSON-Seed-/numerische Nennungen,0 überlappende JSON-Intervalle,0 JSON-Stringnennungen und0 Textnennungen der Zielbereiche. Damit auch keine bloßen SHA-Zahlenteilstrings als Scheintreffer. Eine Nennung im neuen uncommitteten oder externen Plan würde separat als aktuelle Planung behandelt; die Prüfung fand keine ältere solche Reservierung. Externe `/tmp`-Planentwürfe wurden nicht als historische Kartennutzung ausgegeben.

## Quellenwechsel während der Prüfung

Der unveränderte Rohstatus lautet **`REVIEW_REQUIRED`**, ausschließlich wegen drei Mutationsmeldungen bei Roots paralleler technischer Integration: neue primäre `admission.json`, geänderte Worktree-HEAD-Zeile und derselbe primäre HEAD-Wechsel. Keine Parse-/Lese-/Textfehler, keine Textdekodierungslücken und keine Änderung bereits inventarisierter strukturierter Dateibytes beobachtet.

Diese konkrete Änderung wurde anschließend eng nachgeprüft, ohne breiten Scan zu wiederholen: alle14 Dateien des Commits `2ddf64b` in beiden Kopien gelesen, bytegleich und ohne Zielkartennennung. Die hinzugekommene primäre `experiments/analysis/sap_leading_prototype_20261109/admission.json` ist bytegleich zur bereits gescannten Studienkopie: SHA `d6cc3effc187eaa2cc97228ae8ae21064979a6c16e3aa60326b076ffecd3227a`. Sie dokumentiert null neue Spiele/Modelle. Rohmeldungen bleiben erhalten; es wird kein nachträglich durchgehendes Freeze behauptet.

| Registrierte Kopie | HEAD zu Scanbeginn → Scanende |
|---|---|
| `Desktop/KI/sherlock-luxAI-team15` |`a856274fc1cd8eccd551c0792919b842add0e0fe` → `2ddf64b33b12744619fa6e57188b7f2c45ecc8c5`|
| `.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15` |`2ddf64b33b12744619fa6e57188b7f2c45ecc8c5`, unverändert|
| `Desktop/KI/sherlock-counterplay` |`a5d2e61b0e8654bad64e31c29447ada1e439174d`, unverändert|
| `Desktop/KI/sherlock-enemy-tie` |`694eda39ee006cb4644184db73ff2b0a5cbe4383`, unverändert|
| `Desktop/KI/sherlock-ensemble-validation` |`3dcf090b380918175c5d1d01262ddbd7a717d18f`, unverändert|
| `Desktop/KI/sherlock-november-followup` |`bed06df3335caa4d7a79c928132143a9c7e0a8fc`, unverändert|
| `Desktop/KI/sherlock-v10-mechanics` |`03e54e267242ff642c126313fe5f512ed9d959ac`, unverändert|
| `Desktop/KI/sherlock-v4-joint` |`ea8cd339829f398fd27e8f871f654fded2513589`, unverändert|

Alle Pfade unter `/Users/moayedshawesh/`; exakte absolute Pfade im Rohbericht. Die acht registrierten Arbeitskopien selbst blieben dieselben.

## Grenzen und prüfbare Belege

286 unterschiedliche CSVs mit4661 Zeilen haben keine Seedspalte.1476 vom breiten Seedfeldheuristik-Parser beanstandete Werte liegen ausschließlich in JSON, darunter Schemaobjekte, Seeddateipfade, Passivitätsbooleans und Zeitmetriken;0 ungültige CSV-Seedwerte. Diese Rohbefunde bleiben als Schema-/Zuordnungslücken erhalten, nicht als geprüfte Kartennutzung. Roh-JSONL-Traces, Rollouts und Trainingsprovenance wurden bewusst nicht erneut geparst; ausschließlich dort dokumentierte oder seedlose Nutzung bleibt unbekannt. Ebenso unbekannt: andere Rechner, unregistrierte Kopien, undokumentierte Läufe, errechnete Seedformeln, unbekannte Schemas/Binärformate und nicht verfolgte Verzeichnissymlinks. `.git/.venv/venv/node_modules/__pycache__` ausgeschlossen. Neue Textdateien werden vom wiederverwendeten Scanner nicht nochmals vollständig inventarisiert; der konkrete Integrationsdelta wurde daher separat gelesen, eine allgemeine Quellenruhe nicht behauptet.

- [Externer Scanner](/tmp/sap-leading-seeds/seed-audit.py): SHA `fbff0c9963d71f2e09c4002d6fc5579b16eb3a03a6c9fb8d6950a9bbc5da96e1`.
- [Unveränderter vollständiger Rohbericht](/tmp/sap-leading-seeds/seed-audit.json): SHA `2c800a2fcb7b4d42638b916ceee8dc5e8c164abd301439c609fa1ad7814aaff8`.
- [Enger Integrationsdelta-Nachweis](/tmp/sap-leading-seeds/integration-delta.json): SHA `094648697c93574b6b8198f6da6d3d0af48e9edd2681ca25bd35f38aca52f9e7`.

Beide Bereiche können auf Basis dieses begrenzten lokalen Befunds unverändert im getrennten Screenplan verbleiben. Eine tatsächliche Reservierung/Aufnahme bindet Root separat an den endgültigen Plan; hier wurden keine Karten belegt oder Spiele gestartet.
