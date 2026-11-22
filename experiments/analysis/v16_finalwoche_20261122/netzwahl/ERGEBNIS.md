# Situative Netzgewichtung bringt weniger als einen halben Prozentpunkt

Beide Netze des V16 wurden unverändert geladen. Wir haben aus 530.487 zulässigen Lehrerentscheidungen das feste und das situationsabhängige Mischgewicht gelernt. Auf 24 getrennten neuen Partien standen 81.792 zulässige Entscheidungen zur Prüfung. Bei 7.617 davon empfahlen die beiden Netze unterschiedliche Aktionen.

| Gewichtung | Treffer bei gegensätzlicher Empfehlung | Lehrerfehler als Kreuzentropie, alle Zeilen |
|---|---:|---:|
| Original, gleiche Gewichte | 3.783 / 7.617 | 0,5330 |
| Ein gelerntes konstantes Gewicht | 3.808 / 7.617 | 0,5309 |
| Gewicht abhängig von der Situation | 3.818 / 7.617 | 0,5301 |

Die situationsabhängige Wahl brachte 35 zusätzliche Treffer bei 7.617 strittigen Entscheidungen, also **+0,46 Prozentpunkte**. Vor dem Training hatten wir mindestens einen Prozentpunkt als Schwelle für einen Spielvergleich festgelegt. 948 der insgesamt 81.792 Aktionen vor den nachgeschalteten Spielregeln änderten sich. Über alle Entscheidungen stimmte die neue Wahl in 68.312 Fällen mit dem Lehrer überein, die ursprüngliche in 68.277. Daraus folgt kein zusätzlicher Sieg. Der Lauf endet nach dem Training und der getrennten Offlineprüfung.

Ein technischer Kontrolllauf mit exakt null Zusatzgewicht ergab auf allen 303 aufeinanderfolgenden öffentlichen Zuständen eines archivierten Spiels identische 4.848 Aktions-Tripel für zwei getrennt geladene V16-Agenten. [Messung je Karte und Parameter](offline.json) · [56 neu gesammelte Lehrpartien und Hashes](lehrpartien.json) · [Vorab festgelegte Kriterien](PLAN.md)
