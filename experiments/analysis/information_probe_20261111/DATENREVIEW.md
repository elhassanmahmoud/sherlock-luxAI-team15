# Unabhängige Prüfung der tatsächlichen Offlineauswertung

11.11.2026, Reviewer `information_input_audit`, getrennt vom Implementierer. Nur öffentliche Originaltraces und Artefakte gelesen; eigenes leichtgewichtiges Python zur Rekonstruktion, kein Import von `scripts/information_probe.py`, kein Modell, keine Engine und keine Test-Suite.

**Ergebnis: PASS für die technische Auswertung, Gate A nicht erfüllt.** Vier von zwölf Schlüsseln auf vier Karten; Verlust- und Kontrollgruppe vertreten. Mindestens sechs Schlüssel waren erforderlich. Keine Aufnahme von Phase B.

Der Reviewer meldete 129.805 erfolgreiche Einzelprüfungen in seiner separaten Rekonstruktion:

- Alle 302 tatsächlich untersuchten chronologischen Präfixe, 39 Eingabe-/Source-Bindungen sowie Werkzeughash aktuell und aus Commit `c2fa026` geprüft.
- Punktdifferenz und aktuelle verschiedene besetzte Felder mit nichtnegativer Energie, gespeicherte Q-Werte/maskiertes Argmax und Originalmasken abgeglichen.
- Öffentliche Nullfeldableitung, Bewegungssicherheit, Kandidatenreihenfolge, Belegungsentwürfe, erste Gelegenheit und Auswertungshürden unabhängig nachgerechnet.
- Alle vier Vorschläge exakt bestätigt: 831006/p1 Schritt58, 831042/p0 Schritt65, 831000/p1 Schritt70, 831002/p1 Schritt57; Zielkoordinaten, geänderte Aktionen und verwendete Nullfelder stimmen.

**Grenze:** In allen vier Fällen normalisiert sich die alte Gleichung auf `0=0`; die neue geplante Belegung enthält ein unbekanntes Feld. Die Auswertung belegt nur die Möglichkeit eines öffentlichen Feldtests. Weder ausgeführte Alternativaktionen noch frühere Information oder stärkere Spielleistung sind nachgewiesen.

Root hat zusätzlich sämtliche serialisierten Entscheidungen mit dem unveränderten Originalwerkzeug und sämtliche Eingabebindungen reproduziert: [Root-Abnahme](ROOT_ABNAHME.json). Diese Root-Reproduktion ist keine zweite unabhängige Methode. [Ergebnis](ERGEBNIS.md), [Rohbericht](offline/audit.json).
